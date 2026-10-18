"""
HTTP surface for the blockchain layer.

Built through a factory so main.py can hand over its own token-claims
extractor (avoids a circular import and reuses the existing auth path).
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, status

import chain_oracle
import ledger
import ledger_service
from chain_service import chain, ChainUnavailable
from storage_service import get_file_metadata

PRIVILEGED = ("admin", "manager")


def _strip(h: Optional[str]) -> str:
    h = (h or "").lower()
    return h[2:] if h.startswith("0x") else h


def build_manifest(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Rebuild the manifest exactly as /upload signed it."""
    return {
        "file_id": metadata["file_id"],
        "filename": metadata["filename"],
        "total_chunks": metadata["total_chunks"],
        "chunk_hashes": metadata["chunk_hashes"],
        "classification": metadata.get("classification", "public"),
        "owner_id": metadata["owner_id"],
    }


async def blockchain_check(file_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare what the database says *now* with what the chain recorded at upload.
    This is the only check an attacker with full database access cannot satisfy
    by recomputing hashes, because the reference value lives outside their reach.
    """
    try:
        anchor = await chain.get_anchor(file_id)
    except Exception as exc:
        return {"type": "blockchain_anchor", "status": "WARN", "available": False,
                "message": f"⚠️ Could not reach the blockchain — on-chain check skipped ({exc})"}

    if anchor is None:
        return {"type": "blockchain_anchor", "status": "WARN", "available": True, "anchored": False,
                "message": "⚠️ File was never anchored on-chain (uploaded before the blockchain layer, "
                           "or the chain was offline)"}

    local_root = ledger.merkle_root(metadata["chunk_hashes"])
    local_manifest = ledger.manifest_hash(build_manifest(metadata))
    root_ok = _strip(anchor["merkle_root"]) == local_root
    manifest_ok = _strip(anchor["manifest_hash"]) == local_manifest

    try:
        oracle_report = await chain.integrity_report(file_id)
    except Exception:
        oracle_report = None

    base = {
        "oracle": oracle_report,
        "type": "blockchain_anchor", "available": True, "anchored": True,
        "tx_hash": anchor.get("tx_hash"), "block_number": anchor["block_number"],
        "anchored_at": anchor["anchored_at"], "contract_address": anchor["contract_address"],
        "chain_id": anchor["chain_id"],
        "on_chain_root": _strip(anchor["merkle_root"]), "local_root": local_root,
        "root_match": root_ok, "manifest_match": manifest_ok,
    }
    if anchor["revoked"]:
        return {**base, "status": "FAIL", "message": "❌ This file was REVOKED on-chain"}
    if not root_ok:
        return {**base, "status": "FAIL",
                "message": "❌ Chunk hashes in the database do not match the Merkle root anchored "
                           "on-chain — database tampering detected"}
    if not manifest_ok:
        return {**base, "status": "FAIL",
                "message": "❌ File metadata (name / owner / classification) differs from what was "
                           "anchored on-chain"}
    if oracle_report and oracle_report["status"] == "COMPROMISED":
        return {**base, "status": "WARN",
                "message": f"⚠️ Matches the anchor now, but the oracle flagged this file in block "
                           f"#{oracle_report['block_number']}. Run an oracle re-check to clear it."}
    return {**base, "status": "PASS",
            "message": f"✅ Matches the Merkle root anchored in block #{anchor['block_number']}"}


def build_router(extract_claims: Callable[[Optional[str]], tuple]) -> APIRouter:
    router = APIRouter(tags=["blockchain"])

    def claims(authorization: Optional[str]):
        user_id, _aal, role, _status = extract_claims(authorization)
        return user_id, role

    def require_admin(authorization: Optional[str]) -> str:
        user_id, role = claims(authorization)
        if role != "admin":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
        return user_id

    async def load_file(file_id: str, user_id: str, role: str) -> Dict[str, Any]:
        try:
            metadata = await get_file_metadata(file_id)
        except Exception:
            raise HTTPException(404, "File not found")
        if metadata["owner_id"] != user_id and role not in PRIVILEGED:
            raise HTTPException(403, "Access denied")
        return metadata

    # ─────────────────────────── chain ────────────────────────────

    @router.get("/chain/status")
    async def chain_status(authorization: Optional[str] = Header(None)):
        claims(authorization)
        return await chain.status()

    @router.get("/chain/files/{file_id}/anchor")
    async def file_anchor(file_id: str, authorization: Optional[str] = Header(None)):
        user_id, role = claims(authorization)
        metadata = await load_file(file_id, user_id, role)
        return await blockchain_check(file_id, metadata)

    @router.post("/chain/files/{file_id}/anchor")
    async def anchor_existing_file(file_id: str, authorization: Optional[str] = Header(None)):
        """
        Back-fill: anchor a file that was uploaded before the chain existed.
        Admin only — anchoring commits to whatever the database says *right now*,
        so it is trust-on-first-anchor and must be done by a privileged user.
        """
        require_admin(authorization)
        try:
            metadata = await get_file_metadata(file_id)
        except Exception:
            raise HTTPException(404, "File not found")
        try:
            tx = await chain.anchor_file(
                file_id,
                ledger.merkle_root(metadata["chunk_hashes"]),
                ledger.manifest_hash(build_manifest(metadata)),
                metadata["total_chunks"],
            )
        except ChainUnavailable as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
        return {"success": True, "file_id": file_id, **tx}

    @router.get("/chain/files/{file_id}/proof/{index}")
    async def chunk_proof(file_id: str, index: int, authorization: Optional[str] = Header(None)):
        """Prove a single chunk belongs to the anchored file using O(log n) hashes."""
        user_id, role = claims(authorization)
        metadata = await load_file(file_id, user_id, role)
        hashes: List[str] = metadata["chunk_hashes"]
        if not 0 <= index < len(hashes):
            raise HTTPException(404, "Chunk index out of range")

        proof = ledger.merkle_proof(hashes, index)
        local_root = ledger.merkle_root(hashes)
        out = {
            "file_id": file_id, "index": index, "total_chunks": len(hashes),
            "chunk_hash": hashes[index], "merkle_root": local_root, "proof": proof,
            "proof_length": len(proof),
            "locally_valid": ledger.verify_merkle_proof(hashes[index], index, proof, local_root),
        }
        try:
            out["on_chain_valid"] = await chain.verify_chunk(file_id, hashes[index], index, proof)
        except Exception as exc:
            out["on_chain_valid"] = None
            out["chain_error"] = str(exc)
        return out

    # ───────────────────────────── oracle ─────────────────────────────

    @router.get("/chain/oracle/status")
    async def oracle_status(authorization: Optional[str] = Header(None)):
        claims(authorization)
        info = await chain.status()
        try:
            events = await chain.oracle_events(30)
        except Exception:
            events = []
        return {
            "oracle_address": info.get("oracle"),
            "authorised": info.get("oracle_authorised"),
            "connected": info.get("connected", False),
            "sweep_seconds": chain_oracle.node.sweep_seconds,
            "stats": chain_oracle.node.stats,
            "events": events,
        }

    @router.post("/chain/files/{file_id}/oracle-check")
    async def oracle_check(file_id: str, authorization: Optional[str] = Header(None)):
        """Request an oracle check and wait (briefly) for the on-chain answer."""
        user_id, role = claims(authorization)
        await load_file(file_id, user_id, role)
        try:
            before = (await chain.integrity_report(file_id))["checks"]
            req = await chain.request_integrity(file_id)
        except ChainUnavailable as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))

        for _ in range(40):                      # ~20 s
            await asyncio.sleep(0.5)
            report = await chain.integrity_report(file_id)
            if report["checks"] > before:
                return {"success": True, "request_id": req.get("request_id"),
                        "request_tx": req["tx_hash"], "report": report}
        return {"success": False, "pending": True, "request_id": req.get("request_id"),
                "message": "Oracle has not answered yet (storage may be unreachable) — it will keep retrying"}

    @router.post("/admin/oracle/sweep")
    async def oracle_sweep(authorization: Optional[str] = Header(None)):
        require_admin(authorization)
        return {"success": True, "requested": await chain_oracle.node.sweep_now()}

    # ─────────────────────── audit ledger ────────────────────────

    @router.get("/admin/ledger/verify")
    async def verify_ledger(authorization: Optional[str] = Header(None)):
        require_admin(authorization)
        try:
            checkpoint = await chain.latest_checkpoint()
            chain_ok = True
        except Exception:
            checkpoint, chain_ok = None, False
        result = await ledger_service.verify(checkpoint)
        result["chain_reachable"] = chain_ok
        return result

    @router.get("/admin/ledger/entries")
    async def ledger_entries(limit: int = 25, authorization: Optional[str] = Header(None)):
        require_admin(authorization)
        return {"entries": await ledger_service.recent(min(max(limit, 1), 200))}

    @router.post("/admin/ledger/checkpoint")
    async def anchor_checkpoint(authorization: Optional[str] = Header(None)):
        """
        Pin the current ledger head on-chain. Refuses to anchor a chain that does
        not verify — otherwise a tampered history would be permanently endorsed.
        """
        require_admin(authorization)
        check = await ledger_service.verify(None)
        if not check["valid"]:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                f"Ledger failed verification, not anchoring: {check.get('reason')}")
        if check["length"] == 0:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ledger is empty — nothing to anchor")
        try:
            tx = await chain.anchor_checkpoint(check["head"], check["head_seq"])
        except ChainUnavailable as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
        return {"success": True, "head": check["head"], "seq": check["head_seq"], **tx}

    return router
