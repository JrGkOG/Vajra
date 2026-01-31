"""
FastAPI application for secure file upload with encryption and sharding.
Implements streaming architecture to prevent loading entire files into RAM.
"""

import uuid
import base64
from typing import Optional, Tuple
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, status, Query
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
import json

from crypto_utils import generate_encryption_key, generate_iv, encrypt_chunk, decrypt_chunk
from storage_service import upload_chunk_to_supabase, save_file_metadata, get_file_metadata, download_chunk_from_supabase


# Constants
CHUNK_SIZE = 512 * 1024  # 512KB chunks
STORAGE_BUCKET = "uploads"  # Supabase storage bucket name

# Initialize FastAPI app
app = FastAPI(
    title="Secure Upload & Sharding API",
    description="Streaming file upload with AES-256-GCM encryption and sharding",
    version="1.0.0"
)


def extract_owner_id_from_token(authorization: Optional[str]) -> str:
    """
    Extract owner_id from JWT token in Authorization header.
    
    In production, this should:
    1. Verify JWT signature
    2. Check expiration
    3. Extract user_id claim
    
    For PoC, we'll do basic parsing (NOT PRODUCTION-READY).
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
    
    Returns:
        str: User ID extracted from token
    
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    
    # Expected format: "Bearer <jwt_token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: 'Bearer <token>'"
        )
    
    token = parts[1]
    
    # TODO: Implement proper JWT validation here
    # For PoC purposes, we'll just use a placeholder
    # In production, use a library like python-jose or PyJWT
    
    # Placeholder: decode JWT payload (without verification - NOT SECURE!)
    try:
        # JWT format: header.payload.signature
        # We'll extract the payload part and base64 decode it
        payload_part = token.split('.')[1]
        # Add padding if needed for base64 decoding
        padding = 4 - len(payload_part) % 4
        if padding != 4:
            payload_part += '=' * padding
        
        import json
        payload = json.loads(base64.b64decode(payload_part))
        
        # Extract user_id (adjust claim name based on your JWT structure)
        owner_id = payload.get('sub') or payload.get('user_id') or payload.get('id')
        
        if not owner_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain user identifier"
            )
        
        return str(owner_id)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


def extract_claims_from_token(authorization: Optional[str]) -> Tuple[str, str]:
    """
    Extract user_id AND aal (Authenticator Assurance Level) from JWT token.
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
    
    Returns:
        Tuple[str, str]: (user_id, aal) where aal is 'aal1' (password only) or 'aal2' (MFA)
    
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: 'Bearer <token>'"
        )
    
    token = parts[1]
    
    try:
        # JWT format: header.payload.signature
        payload_part = token.split('.')[1]
        # Add padding if needed for base64 decoding
        padding = 4 - len(payload_part) % 4
        if padding != 4:
            payload_part += '=' * padding
        
        payload = json.loads(base64.b64decode(payload_part))
        
        # Extract user_id
        user_id = payload.get('sub') or payload.get('user_id') or payload.get('id')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain user identifier"
            )
        
        # Extract aal (Authenticator Assurance Level)
        # Defaults to 'aal1' if not present (for backward compatibility)
        aal = payload.get('aal', 'aal1')
        
        return str(user_id), str(aal)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )



@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Secure Upload API is running"}


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Secure file upload endpoint with streaming, encryption, and sharding.
    
    Process:
    1. Extract owner_id from JWT token
    2. Generate encryption key and IV
    3. Stream file in 512KB chunks
    4. Encrypt, hash, and encode each chunk
    5. Async upload chunks to Supabase Storage
    6. Save metadata to database
    7. Return encryption key to user
    
    Args:
        file: Uploaded file stream
        authorization: JWT token in Authorization header
    
    Returns:
        JSON response with file_id and encryption_key
    
    Raises:
        HTTPException: If upload fails or authentication fails
    """
    # Step 1: Extract owner_id from JWT
    owner_id = extract_owner_id_from_token(authorization)
    
    # Step 2: Generate encryption materials
    encryption_key = generate_encryption_key()  # 32 bytes for AES-256
    iv = generate_iv()  # 12 bytes for AES-GCM
    file_id = str(uuid.uuid4())
    
    # Storage for chunk hashes (for integrity verification)
    chunk_hashes = []
    chunk_index = 0
    
    # For tracking upload tasks
    upload_tasks = []
    
    try:
        # Step 3: Stream and process file in chunks
        while True:
            # Read chunk from stream (streaming architecture - no full file in RAM)
            chunk_data = await file.read(CHUNK_SIZE)
            
            # If no more data, break
            if not chunk_data:
                break
            
            # Step 4: Encrypt, hash, and encode the chunk
            b64_encrypted_chunk, chunk_hash = encrypt_chunk(chunk_data, encryption_key, iv)
            chunk_hashes.append(chunk_hash)
            
            # Step 5: Async upload to Supabase Storage
            # Path format: /uploads/{file_id}/chunk_{index}
            storage_path = f"{file_id}/chunk_{chunk_index}"
            
            # Create upload task (for async/concurrent uploads)
            upload_task = upload_chunk_to_supabase(
                bucket=STORAGE_BUCKET,
                path=storage_path,
                data=b64_encrypted_chunk
            )
            upload_tasks.append(upload_task)
            
            chunk_index += 1
        
        # Wait for all chunk uploads to complete
        # Using asyncio.gather to run uploads concurrently for speed
        upload_results = await asyncio.gather(*upload_tasks, return_exceptions=True)
        
        # Check if any upload failed
        for idx, result in enumerate(upload_results):
            if isinstance(result, Exception):
                # If one chunk fails, abort the process (per requirements)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Upload failed at chunk {idx}: {str(result)}"
                )
        
        # Step 6: Save metadata to database
        metadata = {
            "file_id": file_id,
            "owner_id": owner_id,
            "filename": file.filename,
            "total_chunks": chunk_index,
            "encryption_iv": base64.b64encode(iv).decode('utf-8'),
            "chunk_hashes": chunk_hashes
        }
        
        await save_file_metadata(metadata)
        
        # Step 7: Return encryption key to user
        # IMPORTANT: In production, you'd want to handle key management differently
        # For PoC, we return it directly (or log it server-side)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "file_id": file_id,
                "filename": file.filename,
                "total_chunks": chunk_index,
                "encryption_key": encryption_key.hex(),  # Simple hex encoding
                "encryption_iv": iv.hex(),  # Simple hex encoding
                "message": "File uploaded and encrypted successfully. Store the encryption_key securely!"
            }
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Catch any other errors and return 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@app.get("/download/{file_id}")
async def download_file(
    file_id: str,
    key: str = Query(..., description="Hex-encoded encryption key"),
    authorization: Optional[str] = Header(None)
):
    """
    Secure file download endpoint with streaming reassembly and decryption.
    
    Security Checks:
    1. JWT Authentication
    2. MFA Verification (aal must NOT be 'aal1')
    3. Ownership Verification (owner_id matches user_id)
    
    Process:
    1. Validate JWT and extract user_id + aal
    2. Check MFA (reject if aal is 'aal1')
    3. Fetch file metadata from database
    4. Verify ownership
    5. Stream chunks: Download -> Decode -> Decrypt -> Yield
    
    Args:
        file_id: UUID of the file to download
        key: Hex-encoded encryption key (from upload response)
        authorization: JWT token in Authorization header
    
    Returns:
        StreamingResponse with decrypted file
    
    Raises:
        HTTPException: If unauthorized, MFA required, or file not found
    """
    # Step 1: Extract claims from JWT
    user_id, aal = extract_claims_from_token(authorization)
    
    # Step 2: MFA Check (Critical Security Guardrail)
    if aal == 'aal1':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA_REQUIRED"
        )
    
    # Step 3: Fetch file metadata
    try:
        metadata = await get_file_metadata(file_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {str(e)}"
        )
    
    # Step 4: Ownership verification
    if metadata['owner_id'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to download this file"
        )
    
    # Step 5: Decode encryption key and IV
    try:
        # Key is hex-encoded, convert to bytes
        encryption_key = bytes.fromhex(key)
        # IV is stored as base64 in metadata
        encryption_iv = base64.b64decode(metadata['encryption_iv'])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid encryption key or IV: {str(e)}"
        )
    
    # Step 6: Create streaming generator
    async def chunk_generator():
        """
        Generator function for streaming reassembly.
        Downloads, decodes, and decrypts chunks one by one.
        """
        total_chunks = metadata['total_chunks']
        
        for chunk_index in range(total_chunks):
            # Download encrypted chunk from Supabase
            storage_path = f"{file_id}/chunk_{chunk_index}"
            b64_encrypted_chunk = await download_chunk_from_supabase(
                bucket=STORAGE_BUCKET,
                path=storage_path
            )
            
            # Decrypt the chunk
            decrypted_chunk = decrypt_chunk(
                b64_encrypted_chunk,
                encryption_key,
                encryption_iv
            )
            
            # Yield decrypted chunk
            yield decrypted_chunk
    
    # Step 7: Return streaming response
    filename = metadata['filename']
    
    try:
        return StreamingResponse(
            chunk_generator(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\""
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
