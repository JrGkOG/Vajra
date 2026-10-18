"""
Pure blockchain primitives for Vajra — no I/O, no network, no database.

Two structures live here:

1. Merkle tree over a file's encrypted-chunk hashes.
   One 32-byte root commits to every chunk *and its position*. A single chunk
   can later be proven with O(log n) sibling hashes. The byte layout matches
   contracts/VajraRegistry.sol exactly, so a proof built here verifies on-chain.

       leaf = sha256( 0x00 || uint32_be(index) || chunk_hash )
       node = sha256( 0x01 || min(a, b) || max(a, b) )     (sorted pair)

   * 0x00 / 0x01 prefixes separate leaves from nodes (second-preimage defence).
   * An odd node is promoted unchanged — never duplicated — which avoids the
     duplicate-leaf ambiguity Bitcoin's tree has (CVE-2012-2459).

2. Hash-chained audit ledger.
   Every audit entry commits to the previous entry's hash, so editing or
   deleting any historical row breaks every hash after it.

       entry_hash = sha256( prev_hash || canonical_json(entry) )
"""

import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

GENESIS_HASH = "00" * 32
LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"


# ─────────────────────────── primitives ───────────────────────────

def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> bytes:
    """Deterministic encoding — the same bytes Vajra already signs with Ed25519."""
    return json.dumps(obj, sort_keys=True).encode("utf-8")


def _clean(h: str) -> str:
    return h[2:] if h.startswith("0x") else h


def file_key(file_id: str) -> bytes:
    """
    On-chain identifier for a file. Hashed so the public chain never carries
    the database UUID and a bystander cannot enumerate Vajra's file ids.
    """
    return sha256_bytes(file_id.encode("utf-8"))


def manifest_hash(manifest: Dict[str, Any]) -> str:
    """sha256 of the canonical manifest (identical bytes to what gets signed)."""
    return sha256_hex(canonical_json(manifest))


# ─────────────────────────── merkle tree ──────────────────────────

def leaf_hash(index: int, chunk_hash_hex: str) -> bytes:
    chunk = bytes.fromhex(_clean(chunk_hash_hex))
    if len(chunk) != 32:
        raise ValueError(f"chunk hash must be 32 bytes, got {len(chunk)}")
    return sha256_bytes(LEAF_PREFIX + index.to_bytes(4, "big") + chunk)


def node_hash(a: bytes, b: bytes) -> bytes:
    lo, hi = (a, b) if a <= b else (b, a)
    return sha256_bytes(NODE_PREFIX + lo + hi)


def _levels(chunk_hashes: Sequence[str]) -> List[List[bytes]]:
    if not chunk_hashes:
        raise ValueError("cannot build a Merkle tree with no chunks")
    level = [leaf_hash(i, h) for i, h in enumerate(chunk_hashes)]
    levels = [level]
    while len(level) > 1:
        nxt: List[bytes] = []
        for i in range(0, len(level) - 1, 2):
            nxt.append(node_hash(level[i], level[i + 1]))
        if len(level) % 2 == 1:
            nxt.append(level[-1])          # promote the odd node
        levels.append(nxt)
        level = nxt
    return levels


def merkle_root(chunk_hashes: Sequence[str]) -> str:
    """Hex Merkle root of the ordered chunk hashes."""
    return _levels(chunk_hashes)[-1][0].hex()


def merkle_proof(chunk_hashes: Sequence[str], index: int) -> List[str]:
    """Sibling hashes (hex) from the leaf at `index` up to the root."""
    if not 0 <= index < len(chunk_hashes):
        raise IndexError("chunk index out of range")
    proof: List[str] = []
    idx = index
    for level in _levels(chunk_hashes)[:-1]:
        sibling = idx ^ 1
        if sibling < len(level):           # no sibling => promoted, nothing to add
            proof.append(level[sibling].hex())
        idx //= 2
    return proof


def verify_merkle_proof(chunk_hash_hex: str, index: int,
                        proof: Iterable[str], root_hex: str) -> bool:
    node = leaf_hash(index, chunk_hash_hex)
    for sibling in proof:
        node = node_hash(node, bytes.fromhex(_clean(sibling)))
    return node.hex() == _clean(root_hex).lower()


# ─────────────────────── hash-chained ledger ──────────────────────

def chain_entry(prev_hash: str, entry: Dict[str, Any]) -> str:
    """Hash that seals `entry` onto the chain after `prev_hash`."""
    return sha256_hex(bytes.fromhex(_clean(prev_hash)) + canonical_json(entry))


def seal(prev_hash: str, entry: Dict[str, Any], seq: int) -> Dict[str, Any]:
    """Return the `chain` block to store alongside an audit entry."""
    return {
        "seq": seq,
        "prev_hash": prev_hash,
        "entry_hash": chain_entry(prev_hash, entry),
    }


def verify_chain(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verify an ordered (oldest first) list of sealed audit rows.

    Each row is {"entry": <the body that was hashed>, "chain": {seq,prev_hash,entry_hash}}.
    Returns {"valid", "length", "head", "head_seq"} plus, when invalid,
    {"broken_at", "reason"} identifying the first bad link.
    """
    prev = GENESIS_HASH
    expected_seq: Optional[int] = None
    for position, row in enumerate(rows):
        chain = row.get("chain") or {}
        seq = chain.get("seq")

        if expected_seq is not None and seq != expected_seq:
            return _broken(position, seq, f"sequence gap: expected {expected_seq}, found {seq}")
        if chain.get("prev_hash") != prev:
            return _broken(position, seq, "prev_hash does not match the previous entry (row removed or reordered)")
        if chain_entry(prev, row["entry"]) != chain.get("entry_hash"):
            return _broken(position, seq, "entry contents do not match their hash (row edited)")

        prev = chain["entry_hash"]
        expected_seq = seq + 1

    return {
        "valid": True,
        "length": len(rows),
        "head": prev,
        "head_seq": (expected_seq - 1) if expected_seq is not None else 0,
    }


def _broken(position: int, seq: Any, reason: str) -> Dict[str, Any]:
    return {"valid": False, "broken_at": position, "seq": seq, "reason": reason}
