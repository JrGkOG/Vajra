@app.get("/files/{file_id}/verify-integrity")
async def verify_file_integrity(
    file_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Verify file integrity without downloading.
    Checks all chunk hashes and signatures.
    
    Returns detailed integrity status.
    """
    user_id, aal, role, status_val = extract_claims_from_token(authorization)
    
    # Get file metadata
    metadata = await get_file_metadata(file_id)
    if not metadata:
        raise HTTPException(404, "File not found")
    
    # Check permissions
    if not await can_access_file(user_id, metadata):
        raise HTTPException(403, "Access denied")
    
    total_chunks = metadata['total_chunks']
    chunk_hashes_stored = metadata['chunk_hashes']
    chunk_signatures = metadata.get('chunk_signatures', [])
    file_signature = metadata.get('file_signature')
   signed_by = metadata.get('signed_by_user_id')
    
    result = {
        "file_id": file_id,
        "filename": metadata['filename'],
        "total_chunks": total_chunks,
        "is_signed": bool(file_signature and chunk_signatures),
        "signed_by": signed_by,
        "checks": []
    }
    
    try:
        # Check 1: File manifest signature
        if file_signature:
            public_key_b64 = await get_user_signature_public_key(signed_by)
            public_key = deserialize_public_key(public_key_b64)
            
            manifest = {
                "file_id": file_id,
                "filename": metadata['filename'],
                "total_chunks": total_chunks,
                "chunk_hashes": chunk_hashes_stored,
                "classification": metadata.get('classification', 'public'),
                "owner_id": metadata['owner_id']
            }
            
            manifest_valid = verify_file_manifest_signature(manifest, file_signature, public_key)
            result['checks'].append({
                "type": "file_manifest_signature",
                "status": "PASS" if manifest_valid else "FAIL",
                "message": "File manifest signature verified" if manifest_valid else "File manifest signature INVALID"
            })
            
            if not manifest_valid:
                result['integrity_status'] = "COMPROMISED"
                result['safe_to_download'] = False
                return result
        
        # Check 2: All chunk hashes and signatures
        chunk_results = []
        for chunk_index in range(total_chunks):
            try:
                storage_path = f"{file_id}/chunk_{chunk_index}"
                b64_encrypted_chunk = await download_chunk_from_supabase(
                    bucket=STORAGE_BUCKET,
                    path=storage_path
                )
                
                import hashlib
                encrypted_bytes = base64.b64decode(b64_encrypted_chunk)
                calculated_hash = hashlib.sha256(encrypted_bytes).hexdigest()
                stored_hash = chunk_hashes_stored[chunk_index]
                
                hash_match = (calculated_hash == stored_hash)
                
                chunk_check = {
                    "chunk_index": chunk_index,
                    "hash_match": hash_match
                }
                
                if not hash_match:
                    chunk_check['error'] = "Hash mismatch - database tampering detected"
                    chunk_check['status'] = "FAIL"
                    chunk_results.append(chunk_check)
                    result['integrity_status'] = "COMPROMISED"
                    result['safe_to_download'] = False
                    result['checks'].append({
                        "type": "chunk_integrity",
                        "chunks": chunk_results
                    })
                    return result
                
                # Verify signature if available
                if chunk_signatures and len(chunk_signatures) > chunk_index:
                    sig_valid = verify_chunk_signature(calculated_hash, chunk_signatures[chunk_index], public_key)
                    chunk_check['signature_valid'] = sig_valid
                    
                    if not sig_valid:
                        chunk_check['error'] = "Signature verification failed"
                        chunk_check['status'] = "FAIL"
                        chunk_results.append(chunk_check)
                        result['integrity_status'] = "COMPROMISED"
                        result['safe_to_download'] = False
                        result['checks'].append({
                            "type": "chunk_integrity",
                            "chunks": chunk_results
                        })
                        return result
                
                chunk_check['status'] = "PASS"
                chunk_results.append(chunk_check)
                
            except Exception as e:
                chunk_results.append({
                    "chunk_index": chunk_index,
                    "status": "ERROR",
                    "error": str(e)
                })
                result['integrity_status'] = "ERROR"
                result['safe_to_download'] = False
                result['checks'].append({
                    "type": "chunk_integrity",
                    "chunks": chunk_results
                })
                return result
        
        result['checks'].append({
            "type": "chunk_integrity",
            "status": "PASS",
            "message": f"All {total_chunks} chunks verified",
            "chunks": chunk_results
        })
        
        result['integrity_status'] = "VERIFIED"
        result['safe_to_download'] = True
        
        return result
        
    except Exception as e:
        result['integrity_status'] = "ERROR"
        result['safe_to_download'] = False
        result['error'] = str(e)
        return result
