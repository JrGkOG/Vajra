"""
Persistent, hash-chained audit ledger.

Both existing log paths (storage_service.log_audit_event and
auth_service.log_activity) mirror each event here. The pure hashing lives in
ledger.py; this module only handles storage, concurrency and the comparison
with the checkpoint pinned on-chain.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import ledger
from storage_service import supabase

TABLE = "ledger_entries"
_PAGE = 1000
_MAX_RETRIES = 5
_append_lock = asyncio.Lock()      # one writer per process; UNIQUE(seq) covers many


def _normalise(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Round-trip through JSON so what we hash is exactly what Postgres returns."""
    import json
    return json.loads(json.dumps(entry, default=str))


async def _head() -> Optional[Dict[str, Any]]:
    res = await asyncio.to_thread(
        lambda: supabase.table(TABLE).select("seq, entry_hash")
        .order("seq", desc=True).limit(1).execute()
    )
    return res.data[0] if res.data else None


async def append_entry(source: str, user_id: Optional[str], action: str,
                       resource_id: Optional[str] = None,
                       details: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Seal one event onto the chain. Never raises: ledger trouble must not break
    a user's upload or login (the same fail-open policy the audit log uses).
    """
    entry = _normalise({
        "source": source,
        "user_id": user_id,
        "action": action,
        "resource_id": resource_id,
        "details": details or {},
        "ts": datetime.now(timezone.utc).isoformat(),
    })

    async with _append_lock:
        for attempt in range(_MAX_RETRIES):
            try:
                head = await _head()
                prev_hash = head["entry_hash"] if head else ledger.GENESIS_HASH
                seq = (head["seq"] + 1) if head else 1
                chain = ledger.seal(prev_hash, entry, seq)
                row = {"seq": seq, "entry": entry,
                       "prev_hash": chain["prev_hash"], "entry_hash": chain["entry_hash"]}
                await asyncio.to_thread(lambda: supabase.table(TABLE).insert(row).execute())
                return row
            except Exception as exc:
                text = str(exc).lower()
                if "duplicate" in text or "unique" in text or "23505" in text:
                    continue                 # another writer took this seq — re-read head
                print(f"⚠️  Ledger append failed: {exc}")
                return None
    print("⚠️  Ledger append gave up after repeated sequence conflicts")
    return None


async def fetch_all() -> List[Dict[str, Any]]:
    """Whole chain, oldest first, in the shape ledger.verify_chain expects."""
    rows: List[Dict[str, Any]] = []
    start = 0
    while True:
        res = await asyncio.to_thread(
            lambda s=start: supabase.table(TABLE).select("*")
            .order("seq").range(s, s + _PAGE - 1).execute()
        )
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < _PAGE:
            break
        start += _PAGE
    return [{
        "entry": r["entry"],
        "chain": {"seq": r["seq"], "prev_hash": r["prev_hash"], "entry_hash": r["entry_hash"]},
        "created_at": r.get("created_at"),
    } for r in rows]


async def recent(limit: int = 25) -> List[Dict[str, Any]]:
    res = await asyncio.to_thread(
        lambda: supabase.table(TABLE).select("*").order("seq", desc=True).limit(limit).execute()
    )
    return res.data or []


async def verify(on_chain_checkpoint: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Two independent questions:
      1. Is the chain internally consistent?       (catches edits / deletions)
      2. Does it still agree with the pinned head? (catches a full recompute)
    """
    rows = await fetch_all()
    result = ledger.verify_chain(rows)
    result["anchor"] = {"checked": False}

    if on_chain_checkpoint is None:
        result["anchor"]["note"] = "No checkpoint has been anchored on-chain yet"
    else:
        cp_seq = int(on_chain_checkpoint["seq"])
        by_seq = {r["chain"]["seq"]: r for r in rows}
        pinned = by_seq.get(cp_seq)
        consistent = bool(pinned and pinned["chain"]["entry_hash"] == on_chain_checkpoint["ledger_head"])
        result["anchor"] = {
            "checked": True,
            "consistent": consistent,
            "checkpoint_seq": cp_seq,
            "checkpoint_head": on_chain_checkpoint["ledger_head"],
            "block_number": on_chain_checkpoint["block_number"],
            "entries_since_checkpoint": max(0, len(rows) - cp_seq),
        }
        if not consistent:
            result["anchor"]["reason"] = (
                f"Ledger entry #{cp_seq} is missing" if pinned is None else
                "Ledger entry at the checkpoint no longer matches the head recorded on-chain "
                "(history was rewritten or rolled back)"
            )
            result["valid"] = False
            result.setdefault("reason", result["anchor"]["reason"])
    result["total_entries"] = len(rows)
    return result
