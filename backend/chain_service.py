"""
Bridge between the FastAPI backend and the VajraRegistry smart contract.

Design rules:
  * Only 32-byte commitments ever leave the server — never files, keys,
    filenames, classifications or user ids (file ids are hashed first).
  * The chain is an *additional* witness. If it is unreachable, uploads still
    succeed and are marked "unanchored"; verification then reports that the
    on-chain check could not be performed instead of silently passing.
  * web3.py is synchronous, so every call is pushed to a worker thread.

Configuration (all optional for local development):
    CHAIN_RPC_URL       default http://127.0.0.1:8545  (npx hardhat node)
    CHAIN_PRIVATE_KEY   signer key for a public testnet. Unset on localhost:
                        the node's unlocked account #0 is used instead.
    CHAIN_DEPLOYMENT    path to the deploy script's JSON (default next to this file)
    ORACLE_PRIVATE_KEY  signer key for the oracle on a public testnet. Unset on
                        localhost: the node's account #1 is used, a different
                        wallet from the anchoring one.
"""

import asyncio
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from web3 import Web3
from web3.exceptions import ContractLogicError

import ledger

VERDICTS = {0: "NOT_ANCHORED", 1: "MATCH", 2: "MISMATCH", 3: "REVOKED", 4: "COMPROMISED"}
HEALTH = {0: "UNCHECKED", 1: "HEALTHY", 2: "COMPROMISED"}

# Must equal VajraRegistry.version(). A mismatch means a stale deployment from
# before the ABI changed, which the bootstrap replaces automatically.
EXPECTED_CONTRACT_VERSION = 2

_DEFAULT_DEPLOYMENT = Path(__file__).with_name("chain_deployment.json")


def _strip0x(h: str) -> str:
    return h[2:] if h.startswith("0x") else h


class ChainUnavailable(Exception):
    """Raised when the RPC node or the deployed contract cannot be reached."""


def _to_bytes32(hex_str: str) -> bytes:
    raw = bytes.fromhex(hex_str[2:] if hex_str.startswith("0x") else hex_str)
    if len(raw) != 32:
        raise ValueError("expected 32 bytes")
    return raw


class ChainService:
    def __init__(self) -> None:
        self.rpc_url = os.getenv("CHAIN_RPC_URL", "http://127.0.0.1:8545")
        self.private_key = os.getenv("CHAIN_PRIVATE_KEY") or None
        self.deployment_path = Path(os.getenv("CHAIN_DEPLOYMENT", str(_DEFAULT_DEPLOYMENT)))
        self._w3: Optional[Web3] = None
        self._contract = None
        self._deployment: Optional[Dict[str, Any]] = None
        self._tx_lock = threading.Lock()   # serialise nonce use

    # ───────────────────────── connection ─────────────────────────

    def _connect(self):
        if self._contract is not None and self._w3 is not None and self._w3.is_connected():
            return self._w3, self._contract

        if not self.deployment_path.exists():
            raise ChainUnavailable(
                f"No deployment file at {self.deployment_path.name}. "
                "Run: cd blockchain && npm run deploy:local"
            )
        self._deployment = json.loads(self.deployment_path.read_text())

        w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 8}))
        if not w3.is_connected():
            raise ChainUnavailable(f"Cannot reach chain node at {self.rpc_url}")

        address = Web3.to_checksum_address(self._deployment["address"])
        if not w3.eth.get_code(address):
            raise ChainUnavailable(
                "No contract at the recorded address — the node was probably "
                "restarted. Re-run: cd blockchain && npm run deploy:local"
            )

        contract = w3.eth.contract(address=address, abi=self._deployment["abi"])
        try:
            version = int(contract.functions.version().call())
        except Exception:
            version = 0
        if version != EXPECTED_CONTRACT_VERSION:
            raise ChainUnavailable(
                f"Deployed contract is version {version}, backend expects "
                f"{EXPECTED_CONTRACT_VERSION} — it will be redeployed on the next bootstrap"
            )

        self._w3 = w3
        self._contract = contract
        return self._w3, self._contract

    def _sender(self, w3: Web3, role: str = "anchorer"):
        if role == "oracle":
            key = os.getenv("ORACLE_PRIVATE_KEY")
            if key:
                return w3.eth.account.from_key(key).address
            accounts = w3.eth.accounts
            return accounts[1] if len(accounts) > 1 else accounts[0]
        if self.private_key:
            return w3.eth.account.from_key(self.private_key).address
        return w3.eth.accounts[0]            # unlocked dev-node account

    def _transact(self, fn, role: str = "anchorer", keep_receipt: bool = False) -> Dict[str, Any]:
        """Send a state-changing call and wait for it to be mined."""
        w3, _ = self._connect()
        key = os.getenv("ORACLE_PRIVATE_KEY") if role == "oracle" else self.private_key
        with self._tx_lock:
            sender = self._sender(w3, role)
            try:
                if key:
                    tx = fn.build_transaction({
                        "from": sender,
                        "nonce": w3.eth.get_transaction_count(sender, "pending"),
                        "chainId": w3.eth.chain_id,
                    })
                    signed = w3.eth.account.sign_transaction(tx, key)
                    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                else:
                    tx_hash = fn.transact({"from": sender})
            except ContractLogicError as exc:
                raise ChainUnavailable(f"Contract rejected the transaction: {exc}") from exc
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        if receipt.status != 1:
            raise ChainUnavailable("Transaction reverted on-chain")
        out = {
            "tx_hash": tx_hash.hex() if tx_hash.hex().startswith("0x") else "0x" + tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
        }
        if keep_receipt:
            out["_receipt"] = receipt
        return out

    # ─────────────────────────── queries ──────────────────────────

    def _status_sync(self) -> Dict[str, Any]:
        w3, c = self._connect()
        return {
            "connected": True,
            "rpc_url": self.rpc_url,
            "network": self._deployment.get("network"),
            "chain_id": w3.eth.chain_id,
            "block_number": w3.eth.block_number,
            "contract_address": c.address,
            "owner": c.functions.owner().call(),
            "signer": self._sender(w3),
            "total_files_anchored": c.functions.totalFiles().call(),
            "checkpoint_count": c.functions.checkpointCount().call(),
            "deployed_at_block": self._deployment.get("blockNumber"),
            "contract_version": EXPECTED_CONTRACT_VERSION,
            "oracle": self._sender(w3, "oracle"),
            "oracle_authorised": c.functions.isOracle(self._sender(w3, "oracle")).call(),
        }

    def reset(self) -> None:
        """Forget the cached connection (after the node or contract was replaced)."""
        self._w3 = None
        self._contract = None
        self._deployment = None

    def _is_anchored_sync(self, file_id: str) -> bool:
        _, c = self._connect()
        return bool(c.functions.isAnchored(ledger.file_key(file_id)).call())

    def _anchor_file_sync(self, file_id: str, root: str, manifest: str, total_chunks: int,
                          journal: bool = True):
        _, c = self._connect()
        key = ledger.file_key(file_id)
        if c.functions.isAnchored(key).call():
            raise ChainUnavailable("File is already anchored (write-once)")
        tx = self._transact(c.functions.anchorFile(
            key, _to_bytes32(root), _to_bytes32(manifest), total_chunks))
        if journal:
            self._journal({"type": "file", "file_id": file_id, "merkle_root": _strip0x(root),
                           "manifest_hash": _strip0x(manifest), "total_chunks": total_chunks,
                           "tx_hash": tx["tx_hash"], "block_number": tx["block_number"]})
        return tx

    @staticmethod
    def _journal(record: Dict[str, Any]) -> None:
        """Best effort: a journaling problem must never fail an anchored upload."""
        try:
            import chain_journal
            chain_journal.append(record)
        except Exception as exc:
            print(f"⚠️  Could not journal anchor: {exc}")

    def _get_anchor_sync(self, file_id: str) -> Optional[Dict[str, Any]]:
        w3, c = self._connect()
        key = ledger.file_key(file_id)
        if not c.functions.isAnchored(key).call():
            return None
        a = c.functions.getAnchor(key).call()
        # struct order: merkleRoot, manifestHash, anchoredBy, totalChunks,
        #               anchoredAt, blockNumber, revoked
        out = {
            "merkle_root": a[0].hex(),
            "manifest_hash": a[1].hex(),
            "anchored_by": a[2],
            "total_chunks": a[3],
            "anchored_at": a[4],
            "block_number": a[5],
            "revoked": a[6],
            "contract_address": c.address,
            "chain_id": w3.eth.chain_id,
            "tx_hash": None,
        }
        # The tx hash is recoverable from the (indexed) event — nothing extra to store.
        try:
            logs = c.events.FileAnchored().get_logs(
                from_block=out["block_number"], to_block=out["block_number"],
                argument_filters={"fileId": key})
            if logs:
                h = logs[0]["transactionHash"].hex()
                out["tx_hash"] = h if h.startswith("0x") else "0x" + h
        except Exception:
            pass
        return out

    def _verify_file_sync(self, file_id: str, root: str) -> str:
        _, c = self._connect()
        v = c.functions.verifyFile(ledger.file_key(file_id), _to_bytes32(root)).call()
        return VERDICTS[int(v)]

    # ───────────────────────── oracle plumbing ─────────────────────────

    def _request_integrity_sync(self, file_id: str) -> Dict[str, Any]:
        _, c = self._connect()
        tx = self._transact(c.functions.requestIntegrityCheck(ledger.file_key(file_id)),
                            keep_receipt=True)
        receipt = tx.pop("_receipt")
        events = c.events.IntegrityCheckRequested().process_receipt(receipt)
        tx["request_id"] = int(events[0]["args"]["requestId"]) if events else None
        return tx

    def _pending_requests_sync(self, from_block: int):
        """
        Unfulfilled IntegrityCheckRequested events in [from_block, latest].
        Returns (pending, latest, from_used). `from_used` is 0 when the node was
        replaced (chain shorter than expected) and the scan restarted from genesis.
        """
        w3, c = self._connect()
        latest = w3.eth.block_number
        if latest < from_block - 1:             # node restarted: the chain is shorter
            from_block = 0
        pending = []
        if from_block <= latest:                # nothing new since the last look
            logs = c.events.IntegrityCheckRequested().get_logs(
                from_block=from_block, to_block=latest)
            for log in logs:
                rid = int(log["args"]["requestId"])
                req = c.functions.getRequest(rid).call()   # (fileId, requester, requestedAt, fulfilled)
                if not req[3]:
                    pending.append({"request_id": rid, "file_key": log["args"]["fileId"].hex(),
                                    "block": log["blockNumber"]})
        return pending, latest, from_block

    def _fulfill_sync(self, request_id: int, observed_root: str) -> Dict[str, Any]:
        _, c = self._connect()
        return self._transact(
            c.functions.fulfillIntegrityCheck(request_id, _to_bytes32(observed_root)),
            role="oracle")

    def _integrity_report_sync(self, file_id: str) -> Dict[str, Any]:
        _, c = self._connect()
        r = c.functions.getIntegrityReport(ledger.file_key(file_id)).call()
        # struct order: observedRoot, oracle, checks, reportedAt, blockNumber, status
        return {
            "status": HEALTH[int(r[5])],
            "observed_root": r[0].hex(),
            "oracle": r[1],
            "checks": int(r[2]),
            "reported_at": int(r[3]),
            "block_number": int(r[4]),
        }

    def _oracle_events_sync(self, limit: int = 30) -> list:
        w3, c = self._connect()
        start = max(0, w3.eth.block_number - 5000)
        rows = []
        for name in ("IntegrityCheckRequested", "IntegrityReported", "TamperAlarm"):
            for log in getattr(c.events, name)().get_logs(from_block=start):
                a = log["args"]
                row = {"type": name, "block": log["blockNumber"], "index": log["logIndex"],
                       "file_key": a["fileId"].hex()}
                if "requestId" in a:
                    row["request_id"] = int(a["requestId"])
                if name == "IntegrityReported":
                    row["status"] = HEALTH[int(a["status"])]
                    row["observed_root"] = a["observedRoot"].hex()
                if name == "TamperAlarm":
                    row["anchored_root"] = a["anchoredRoot"].hex()
                    row["observed_root"] = a["observedRoot"].hex()
                rows.append(row)
        rows.sort(key=lambda r: (r["block"], r["index"]), reverse=True)
        return rows[:limit]

    def _verify_chunk_sync(self, file_id: str, chunk_hash: str, index: int, proof) -> bool:
        _, c = self._connect()
        return bool(c.functions.verifyChunk(
            ledger.file_key(file_id), _to_bytes32(chunk_hash), index,
            [_to_bytes32(p) for p in proof]).call())

    def _anchor_checkpoint_sync(self, head: str, seq: int, journal: bool = True):
        _, c = self._connect()
        tx = self._transact(c.functions.anchorCheckpoint(_to_bytes32(head), seq))
        if journal:
            self._journal({"type": "checkpoint", "ledger_head": _strip0x(head), "seq": seq,
                           "tx_hash": tx["tx_hash"], "block_number": tx["block_number"]})
        return tx

    def _latest_checkpoint_sync(self) -> Optional[Dict[str, Any]]:
        _, c = self._connect()
        if c.functions.checkpointCount().call() == 0:
            return None
        cp = c.functions.latestCheckpoint().call()
        # struct order: ledgerHead, anchoredBy, seq, anchoredAt, blockNumber
        return {
            "ledger_head": cp[0].hex(),
            "anchored_by": cp[1],
            "seq": cp[2],
            "anchored_at": cp[3],
            "block_number": cp[4],
        }

    # ───────────────────── async public surface ───────────────────

    @staticmethod
    async def _ready() -> None:
        """Let a request that arrives mid-startup wait for the node to come up."""
        try:
            import chain_bootstrap
            await chain_bootstrap.wait_ready(timeout=25)
        except Exception:
            pass

    @staticmethod
    def _bootstrap_info() -> Optional[Dict[str, Any]]:
        try:
            import chain_bootstrap
            return chain_bootstrap.snapshot()
        except Exception:
            return None

    async def status(self) -> Dict[str, Any]:
        try:
            out = await asyncio.to_thread(self._status_sync)
        except Exception as exc:  # unreachable node, missing deployment, RPC error
            out = {"connected": False, "rpc_url": self.rpc_url, "reason": str(exc)}
        out["bootstrap"] = self._bootstrap_info()
        return out

    async def anchor_file(self, file_id: str, root: str, manifest: str, total_chunks: int):
        await self._ready()
        return await asyncio.to_thread(self._anchor_file_sync, file_id, root, manifest, total_chunks)

    async def get_anchor(self, file_id: str):
        await self._ready()
        return await asyncio.to_thread(self._get_anchor_sync, file_id)

    async def verify_file(self, file_id: str, root: str) -> str:
        await self._ready()
        return await asyncio.to_thread(self._verify_file_sync, file_id, root)

    async def request_integrity(self, file_id: str):
        await self._ready()
        return await asyncio.to_thread(self._request_integrity_sync, file_id)

    async def integrity_report(self, file_id: str):
        await self._ready()
        return await asyncio.to_thread(self._integrity_report_sync, file_id)

    async def oracle_events(self, limit: int = 30):
        await self._ready()
        return await asyncio.to_thread(self._oracle_events_sync, limit)

    async def verify_chunk(self, file_id: str, chunk_hash: str, index: int, proof) -> bool:
        return await asyncio.to_thread(self._verify_chunk_sync, file_id, chunk_hash, index, proof)

    async def anchor_checkpoint(self, head: str, seq: int):
        return await asyncio.to_thread(self._anchor_checkpoint_sync, head, seq)

    async def latest_checkpoint(self):
        return await asyncio.to_thread(self._latest_checkpoint_sync)


chain = ChainService()
