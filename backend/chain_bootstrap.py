"""
Zero-touch blockchain startup, run from inside the FastAPI backend.

When the backend starts it will:
  1. start a local Hardhat node (unless one is already listening),
  2. deploy VajraRegistry if the recorded contract is not on that node,
  3. replay chain_journal.jsonl so every earlier anchor is back on-chain,
  4. report whether the database has drifted from what was anchored.

It only ever auto-starts a node for a *local* RPC URL. Pointing CHAIN_RPC_URL at
a public testnet disables the node start-up and the deploy step entirely.

Environment:
    CHAIN_AUTOSTART=0   turn the whole thing off (use your own node)
    CHAIN_RPC_URL       default http://127.0.0.1:8545
"""

import asyncio
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from web3 import Web3

import chain_journal
import chain_oracle
import ledger
from chain_service import chain, EXPECTED_CONTRACT_VERSION

BACKEND_DIR = Path(__file__).resolve().parent
BLOCKCHAIN_DIR = BACKEND_DIR.parent / "blockchain"
NODE_LOG = Path(os.getenv("CHAIN_NODE_LOG", str(BACKEND_DIR / "chain_node.log")))
_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}

_proc: Optional[subprocess.Popen] = None
_ready = asyncio.Event()

state: Dict[str, Any] = {
    "phase": "idle",          # idle|disabled|starting_node|deploying|replaying|ready|failed
    "message": "",
    "node_started_by_backend": False,
    "replay": None,
    "drift": [],
    "drift_checked": False,
}


def snapshot() -> Dict[str, Any]:
    return dict(state)


def _set(phase: str, message: str = "") -> None:
    state["phase"], state["message"] = phase, message
    print(f"⛓️  chain bootstrap [{phase}] {message}".rstrip())
    if phase in ("ready", "failed", "disabled"):
        _ready.set()


async def wait_ready(timeout: float = 25) -> None:
    """Return once bootstrap finished (or immediately if it never ran)."""
    if state["phase"] in ("idle", "ready", "failed", "disabled"):
        return
    try:
        await asyncio.wait_for(_ready.wait(), timeout)
    except asyncio.TimeoutError:
        pass


# ───────────────────────────── helpers ─────────────────────────────

def _rpc_parts():
    u = urlparse(chain.rpc_url)
    return u.hostname or "127.0.0.1", u.port or 8545


def _node_up() -> bool:
    try:
        return Web3(Web3.HTTPProvider(chain.rpc_url, request_kwargs={"timeout": 2})).is_connected()
    except Exception:
        return False


def _contract_alive() -> bool:
    """Is the recorded deployment actually present on the connected node?"""
    try:
        import json
        dep = json.loads(chain.deployment_path.read_text())
        w3 = Web3(Web3.HTTPProvider(chain.rpc_url, request_kwargs={"timeout": 4}))
        address = Web3.to_checksum_address(dep["address"])
        if not w3.eth.get_code(address):
            return False
        # A contract left over from an older ABI is as good as missing.
        probe = w3.eth.contract(address=address, abi=dep["abi"])
        return int(probe.functions.version().call()) == EXPECTED_CONTRACT_VERSION
    except Exception:
        return False


def _start_node() -> None:
    global _proc
    host, port = _rpc_parts()
    npx = shutil.which("npx")
    if not npx:
        raise RuntimeError("npx not found — install Node.js to auto-start the local chain")
    if not (BLOCKCHAIN_DIR / "node_modules" / "hardhat").exists():
        _set("starting_node", "installing blockchain dependencies (first run only)…")
        subprocess.run([shutil.which("npm") or "npm", "install", "--no-audit", "--no-fund"],
                       cwd=BLOCKCHAIN_DIR, check=True, capture_output=True, timeout=600)

    log = open(NODE_LOG, "wb")      # fresh log per start: the account list is at the top, and it cannot grow forever
    # Same process group as the backend on purpose: Ctrl-C stops both.
    _proc = subprocess.Popen(
        [npx, "hardhat", "node", "--hostname", host, "--port", str(port)],
        cwd=BLOCKCHAIN_DIR, stdout=log, stderr=subprocess.STDOUT,
    )
    state["node_started_by_backend"] = True

    deadline = time.time() + 60
    while time.time() < deadline:
        if _proc.poll() is not None:
            raise RuntimeError(f"Hardhat node exited early (see {NODE_LOG.name})")
        if _node_up():
            return
        time.sleep(0.5)
    raise RuntimeError(f"Hardhat node did not become ready within 60s (see {NODE_LOG.name})")


def _deploy() -> None:
    npx = shutil.which("npx")
    env = {**os.environ, "CHAIN_RPC_URL": chain.rpc_url,
           "CHAIN_DEPLOYMENT": str(chain.deployment_path)}
    done = subprocess.run(
        [npx, "hardhat", "run", "scripts/deploy.js", "--network", "localhost"],
        cwd=BLOCKCHAIN_DIR, env=env, capture_output=True, text=True, timeout=240,
    )
    if done.returncode != 0:
        raise RuntimeError(f"contract deploy failed: {(done.stderr or done.stdout)[-400:]}")


async def _check_drift() -> None:
    """Compare journaled commitments with the database. Report only — never rewrite."""
    records, _ = chain_journal.read()
    latest: Dict[str, Dict[str, Any]] = {r["file_id"]: r for r in records if r["type"] == "file"}
    drift = []
    try:
        from storage_service import get_file_metadata
    except Exception as exc:
        state["drift_checked"] = False
        state["drift_note"] = f"skipped: {exc}"
        return

    for file_id, rec in list(latest.items())[:100]:
        try:
            meta = await get_file_metadata(file_id)
        except Exception as exc:
            if "not found" in str(exc).lower():
                drift.append({"file_id": file_id, "reason": "file row no longer exists in the database"})
                continue
            state["drift_checked"] = False
            state["drift_note"] = f"skipped: database unreachable ({exc})"
            return
        if ledger.merkle_root(meta["chunk_hashes"]) != rec["merkle_root"]:
            drift.append({"file_id": file_id,
                          "reason": "chunk hashes in the database differ from what was anchored"})
    state["drift"] = drift
    state["drift_checked"] = True


# ───────────────────────────── entrypoint ──────────────────────────

async def run() -> None:
    """Idempotent. Never raises — a chain problem must not stop the API from serving."""
    try:
        host, _ = _rpc_parts()
        local = host in _LOCAL_HOSTS

        if os.getenv("CHAIN_AUTOSTART", "1") == "0":
            return _set("disabled", "CHAIN_AUTOSTART=0")

        if not await asyncio.to_thread(_node_up):
            if not local:
                return _set("failed", f"chain node {chain.rpc_url} is unreachable")
            _set("starting_node", "launching local Hardhat node…")
            await asyncio.to_thread(_start_node)

        chain.reset()
        if local and not await asyncio.to_thread(_contract_alive):
            _set("deploying", "deploying VajraRegistry…")
            await asyncio.to_thread(_deploy)
            chain.reset()

        _set("replaying", "restoring anchors from journal…")
        state["replay"] = await asyncio.to_thread(chain_journal.replay, chain)
        r = state["replay"]
        if r["journal_error"]:
            print(f"⚠️  journal problem: {r['journal_error']}")

        try:
            await asyncio.wait_for(_check_drift(), timeout=25)
        except Exception as exc:
            state["drift_checked"] = False
            state["drift_note"] = f"skipped: {exc}"

        n = r["files_replayed"] + r["checkpoints_replayed"]
        chain_oracle.node.start()
        _set("ready", f"chain ready — {n} anchor(s) restored, "
                      f"{r['files_skipped'] + r['checkpoints_skipped']} already present")
    except Exception as exc:
        _set("failed", str(exc))


def stop() -> None:
    """Stop the node *only if this backend started it*."""
    global _proc
    chain_oracle.node.stop()
    if _proc and _proc.poll() is None:
        _proc.terminate()
        try:
            _proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _proc.kill()
    _proc = None
