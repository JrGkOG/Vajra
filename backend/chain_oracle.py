"""
Vajra's integrity oracle — the off-chain half of the request/callback pattern.

A smart contract cannot read Supabase. This node watches the chain for
`IntegrityCheckRequested`, looks at the real stored data, recomputes the Merkle
root, and answers with `fulfillIntegrityCheck` from a *separate* oracle wallet.

It reports an observation; it never decides. The contract compares the
observation with the anchor and records Healthy / Compromised itself.

What it observes (so the answer reflects reality, not one database column):
    • the bytes of every chunk actually sitting in Supabase Storage
    • the chunk hashes recorded in the database row
and it reports whichever source contradicts the anchor (else the matching root).

Honesty rule: "I could not look" is NOT "I saw tampering". If the database or
storage is unreachable the oracle stays silent and retries — a network blip must
never raise a false alarm. A file/chunk that is positively *gone* is tampering.

Environment:
    ORACLE_POLL_SECONDS    how often to look for requests         (default 2)
    ORACLE_SWEEP_SECONDS   proactive re-check of every file; 0=off (default 60)
"""

import asyncio
import base64
import hashlib
import os
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

import chain_journal
import ledger
from chain_service import chain

STORAGE_BUCKET = "uploads"                 # same bucket main.py uploads into
MISSING_SENTINEL = "00" * 31 + "01"        # reported when data is positively gone

Observer = Callable[[str, str], Awaitable[Optional[str]]]


class _Unavailable(Exception):
    """We could not observe — distinct from observing tampering."""


def _looks_missing(exc: Exception) -> bool:
    text = str(exc).lower()
    return "not found" in text or "404" in text or "does not exist" in text


class OracleNode:
    def __init__(self, observer: Optional[Observer] = None) -> None:
        self.observer: Observer = observer or self._observe_real
        self.poll_seconds = float(os.getenv("ORACLE_POLL_SECONDS", "2"))
        self.sweep_seconds = float(os.getenv("ORACLE_SWEEP_SECONDS", "60"))
        self._task: Optional[asyncio.Task] = None
        self._last_block = 0                  # next block to scan for new requests
        self._pending: Dict[int, Dict[str, Any]] = {}   # request_id -> request, not yet answered
        self._last_sweep = 0.0
        self._index: Dict[str, str] = {}     # sha256(file_id) hex -> file_id
        self._index_at = 0.0
        self.stats: Dict[str, Any] = {
            "running": False, "requests_seen": 0, "reports_sent": 0,
            "unavailable_skips": 0, "sweeps": 0, "last_error": None,
        }

    # ─────────────────────────── file index ───────────────────────────

    async def _refresh_index(self, force: bool = False) -> None:
        """Map on-chain hashed ids back to real file ids (journal first, then DB)."""
        if not force and self._index and time.time() - self._index_at < 30:
            return
        index = {ledger.file_key(r["file_id"]).hex(): r["file_id"]
                 for r in chain_journal.read()[0] if r.get("type") == "file"}
        try:
            from storage_service import list_files
            for row in await list_files():
                index[ledger.file_key(row["file_id"]).hex()] = row["file_id"]
        except Exception:
            pass                              # the journal alone is enough to work
        self._index, self._index_at = index, time.time()

    async def _file_id_for(self, key_hex: str) -> Optional[str]:
        await self._refresh_index()
        if key_hex not in self._index:
            await self._refresh_index(force=True)
        return self._index.get(key_hex)

    # ─────────────────────────── observation ──────────────────────────

    async def _observe_real(self, file_id: str, anchored_root: str) -> Optional[str]:
        """Return the root to report, or None if the data could not be observed."""
        from storage_service import get_file_metadata, download_chunk_from_supabase

        try:
            meta = await get_file_metadata(file_id)
        except Exception as exc:
            if _looks_missing(exc):
                return MISSING_SENTINEL        # the row is gone: that *is* tampering
            raise _Unavailable(str(exc))

        db_root = ledger.merkle_root(meta["chunk_hashes"])

        hashes: List[str] = []
        for i in range(int(meta["total_chunks"])):
            try:
                b64 = await download_chunk_from_supabase(STORAGE_BUCKET, f"{file_id}/chunk_{i}")
            except Exception as exc:
                if _looks_missing(exc):
                    return MISSING_SENTINEL
                raise _Unavailable(str(exc))
            hashes.append(hashlib.sha256(base64.b64decode(b64)).hexdigest())
        storage_root = ledger.merkle_root(hashes)

        # Report the source that contradicts the anchor; otherwise the common root.
        for candidate in (storage_root, db_root):
            if candidate != anchored_root:
                return candidate
        return anchored_root

    async def _observe(self, file_id: str) -> Optional[str]:
        anchor = await asyncio.to_thread(chain._get_anchor_sync, file_id)
        if anchor is None:
            return None
        anchored = anchor["merkle_root"][2:] if anchor["merkle_root"].startswith("0x") \
            else anchor["merkle_root"]
        try:
            return await self.observer(file_id, anchored)
        except _Unavailable:
            return None

    # ───────────────────────────── main loop ──────────────────────────

    async def handle_requests(self) -> int:
        """
        Pick up new requests (only blocks we have not scanned yet), then try to
        answer everything still pending. Unanswerable requests stay in memory and
        are retried — nothing is re-read from the chain history.
        """
        fresh, latest, used = await asyncio.to_thread(chain._pending_requests_sync, self._last_block)
        if used == 0 and self._last_block > 0:       # node was replaced: start over
            self._pending.clear()
            self._index.clear()
        for req in fresh:
            if req["request_id"] not in self._pending:
                self._pending[req["request_id"]] = req
                self.stats["requests_seen"] += 1
        self._last_block = latest + 1

        answered = 0
        for rid, req in list(self._pending.items()):
            file_id = await self._file_id_for(req["file_key"])
            if file_id is None:
                continue                       # not a file this oracle can see
            root = await self._observe(file_id)
            if root is None:
                self.stats["unavailable_skips"] += 1   # stay silent, retry next tick
                continue
            try:
                await asyncio.to_thread(chain._fulfill_sync, rid, root)
            except Exception as exc:
                if "AlreadyFulfilled" not in str(exc):
                    raise
            self._pending.pop(rid, None)
            self.stats["reports_sent"] += 1
            answered += 1
        return answered

    async def sweep_now(self) -> int:
        """Ask for a fresh check of every anchored file we know about."""
        await self._refresh_index(force=True)
        waiting = {p["file_key"] for p in self._pending.values()}
        requested = 0
        for key_hex, file_id in list(self._index.items()):
            if key_hex in waiting:
                continue
            try:
                if not await asyncio.to_thread(chain._is_anchored_sync, file_id):
                    continue
                await asyncio.to_thread(chain._request_integrity_sync, file_id)
                requested += 1
            except Exception as exc:
                self.stats["last_error"] = f"sweep: {exc}"
        self.stats["sweeps"] += 1
        self._last_sweep = time.time()
        return requested

    async def _run(self) -> None:
        self.stats["running"] = True
        print("🔮 Oracle node started")
        while True:
            try:
                await self.handle_requests()
                if self.sweep_seconds > 0 and time.time() - self._last_sweep >= self.sweep_seconds:
                    await self.sweep_now()
                    await self.handle_requests()
                self.stats["last_error"] = None
            except asyncio.CancelledError:
                raise
            except Exception as exc:           # keep the oracle alive through blips
                self.stats["last_error"] = str(exc)
            await asyncio.sleep(self.poll_seconds)

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._last_block, self._last_sweep = 0, time.time()
        self._pending.clear()
        self._task = asyncio.create_task(self._run())

    def stop(self) -> None:
        if self._task:
            self._task.cancel()
        self._task = None
        self.stats["running"] = False


node = OracleNode()
