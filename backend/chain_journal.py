"""
Append-only, hash-chained journal of everything Vajra has anchored on-chain.

Why it exists: the local development chain lives in memory and is empty after a
restart. Real nodes recover by replaying history; this journal is that history.
Each line records the *original* commitment (not "whatever the database says
now"), so replaying it restores the chain's protection instead of endorsing
tampered data.

Line format (JSON, one per line):
    {"type": "file" | "checkpoint", ...fields..., "ts", "prev", "hash"}
    hash = sha256( prev || canonical_json(line without prev/hash) )
Editing or deleting a line breaks every hash after it, and replay stops at the
first bad link.
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ledger

_lock = threading.Lock()


def journal_path() -> Path:
    return Path(os.getenv("CHAIN_JOURNAL", str(Path(__file__).with_name("chain_journal.jsonl"))))


def _body(rec: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in rec.items() if k not in ("prev", "hash")}


def read() -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Return (valid records, error). Stops at the first corrupted line."""
    path = journal_path()
    if not path.exists():
        return [], None

    records: List[Dict[str, Any]] = []
    prev = ledger.GENESIS_HASH
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            return records, f"line {number}: not valid JSON"
        if rec.get("prev") != prev:
            return records, f"line {number}: broken link (a line was removed or reordered)"
        if ledger.chain_entry(prev, _body(rec)) != rec.get("hash"):
            return records, f"line {number}: contents do not match their hash (line edited)"
        records.append(rec)
        prev = rec["hash"]
    return records, None


def append(record: Dict[str, Any]) -> Dict[str, Any]:
    """Seal and append one record. Safe to call from worker threads."""
    with _lock:
        existing, error = read()
        if error:
            # Never extend a corrupted journal — that would launder the damage.
            raise RuntimeError(f"journal is corrupted ({error}); refusing to append")
        prev = existing[-1]["hash"] if existing else ledger.GENESIS_HASH

        rec = {**record, "ts": datetime.now(timezone.utc).isoformat()}
        rec["prev"] = prev
        rec["hash"] = ledger.chain_entry(prev, _body(rec))

        path = journal_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return rec


def replay(svc) -> Dict[str, Any]:
    """
    Re-create on-chain state from the journal. Idempotent: anything already
    on the chain is skipped, so running it repeatedly is harmless.

    `svc` is a ChainService (uses its synchronous methods; call from a thread).
    """
    records, error = read()
    stats: Dict[str, Any] = {
        "journal_entries": len(records),
        "files_replayed": 0, "files_skipped": 0,
        "checkpoints_replayed": 0, "checkpoints_skipped": 0,
        "journal_error": error,
        "errors": [],
    }

    latest = svc._latest_checkpoint_sync()
    latest_seq = int(latest["seq"]) if latest else 0

    for rec in records:
        try:
            if rec["type"] == "file":
                if svc._is_anchored_sync(rec["file_id"]):
                    stats["files_skipped"] += 1
                else:
                    svc._anchor_file_sync(rec["file_id"], rec["merkle_root"],
                                          rec["manifest_hash"], rec["total_chunks"],
                                          journal=False)
                    stats["files_replayed"] += 1
            elif rec["type"] == "checkpoint":
                if int(rec["seq"]) <= latest_seq:
                    stats["checkpoints_skipped"] += 1
                else:
                    svc._anchor_checkpoint_sync(rec["ledger_head"], int(rec["seq"]), journal=False)
                    latest_seq = int(rec["seq"])
                    stats["checkpoints_replayed"] += 1
        except Exception as exc:
            stats["errors"].append(f"{rec.get('type')} {rec.get('file_id') or rec.get('seq')}: {exc}")
    return stats
