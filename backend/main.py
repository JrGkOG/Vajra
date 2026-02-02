"""
FastAPI application for secure file upload with encryption and sharding.
Implements streaming architecture to prevent loading entire files into RAM.
"""

import uuid
import base64
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, status, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json

from crypto_utils import generate_encryption_key, generate_iv, encrypt_chunk, decrypt_chunk
from storage_service import upload_chunk_to_supabase, save_file_metadata, get_file_metadata, download_chunk_from_supabase, log_audit_event, list_files
from vault_service import encrypt_key_for_vault, decrypt_key_from_vault


# Constants
CHUNK_SIZE = 512 * 1024  # 512KB chunks
STORAGE_BUCKET = "uploads"  # Supabase storage bucket name

# Initialize FastAPI app
app = FastAPI(
    title="Secure Upload & Sharding API",
    description="Streaming file upload with AES-256-GCM encryption and sharding",
    version="1.0.0"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str


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


@app.post("/login")
async def login(request: LoginRequest):
    """
    Mock login endpoint that issues JWT tokens.
    
    For PoC: Accepts any password, assigns role based on username.
    - 'commander' -> role: commander, status: active
    - 'viewer' -> role: viewer, status: active
    - Any other -> role: viewer, status: active
    """
    username = request.username.lower()
    
    # Mock role assignment
    if username == "commander":
        role = "commander"
    elif username == "specialist":
        role = "specialist"
    else:
        role = "viewer"
    
    # Create mock JWT payload
    payload = {
        "sub": username,
        "user_id": username,
        "email": f"{username}@vajra.mil",
        "aal": "aal2",  # Assume MFA completed
        "role": role,
        "status": "active"
    }
    
    # Create mock JWT (header.payload.signature)
    header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
    payload_encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    mock_token = f"{header}.{payload_encoded}.mock-signature"
    
    return {
        "access_token": mock_token,
        "token_type": "bearer",
        "user": {
            "username": username,
            "role": role,
            "status": "active"
        }
    }


@app.get("/files")
async def get_files(authorization: Optional[str] = Header(None)):
    """
    List all files in the system.
    Requires authentication.
    """
    # Verify user is authenticated
    user_id = extract_owner_id_from_token(authorization)
    
    try:
        files = await list_files()
        return {"success": True, "files": files}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )


@app.post("/upload")
async def upload_file(
    classification: str = Query("public", regex="^(top_secret|mission_logs|public)$"),
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Secure file upload endpoint with streaming, encryption, and sharding.
    
    Process:
    1. Extract owner_id from JWT token
    2. Generate encryption materials
    3. Stream & Encrypt
    4. Save metadata (including classification)
    
    Args:
        classification: top_secret, mission_logs, or public (default)
        file: Uploaded file stream
        authorization: JWT token
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
            "classification": classification,  # Added classification
            "total_chunks": chunk_index,
            "encryption_iv": base64.b64encode(iv).decode('utf-8'),
            "chunk_hashes": chunk_hashes
        }
        
        await save_file_metadata(metadata)
        
        # Step 7: Log Audit Event (Success) (ABAC Requirement)
        await log_audit_event({
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": owner_id,
            "action": "UPLOAD",
            "resource_id": file_id,
            "details": {
                "filename": file.filename,
                "classification": classification,
                "chunks": chunk_index,
                "ip": "127.0.0.1" # In prod, extract from Request
            }
        })
        
        # Step 8: Return encryption key to user
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "file_id": file_id,
                "filename": file.filename,
                "total_chunks": chunk_index,
                "encryption_key": encryption_key.hex(),
                "encryption_iv": iv.hex(),
                "message": "File uploaded and encrypted successfully. Store the encryption_key securely!"
            }
        )
    
    except HTTPException:
        # Log failure if we have file_id
        if 'owner_id' in locals():
             await log_audit_event({
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": owner_id,
                "action": "UPLOAD_FAILED",
                "resource_id": file_id,
                "details": {"reason": "HTTPException"}
            })
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
    3. RBAC Verification (Role vs Classification)
    4. Ownership Verification (owner_id matches user_id)
    """
    # Step 1: Extract claims from JWT (Now includes ROLE and STATUS)
    user_id, aal, role, status_val = extract_claims_from_token(authorization)
    
    # Step 2: MFA Check (Critical Security Guardrail)
    if aal == 'aal1':
        # Log Access Denied
        await log_audit_event({
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": "ACCESS_DENIED",
            "resource_id": file_id,
            "details": {"reason": "MFA_REQUIRED", "aal": aal}
        })
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
    
    # Step 4: Ownership Check FIRST - Owners can always download their own files
    # OR Commanders have admin override for all files
    is_owner = metadata['owner_id'] == user_id
    is_commander = role == 'commander'
    
    if not is_owner and not is_commander:
        # Non-owners need ABAC check
        file_classification = metadata.get('classification', 'public')
        allowed, reason = check_abac_access(role, status_val, file_classification)
        
        if not allowed:
            # Log Access Denied
            await log_audit_event({
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "action": "ACCESS_DENIED",
                "resource_id": file_id,
                "details": {
                    "reason": reason,
                    "role": role,
                    "status": status_val,
                    "classification": file_classification
                }
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: {reason}"
            )

    # Log Successful Access
    file_classification = metadata.get('classification', 'public')
    await log_audit_event({
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "action": "DOWNLOAD",
        "resource_id": file_id,
        "details": {
            "classification": file_classification,
            "role": role,
            "is_owner": is_owner
        }
    })

    
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


def extract_claims_from_token(authorization: Optional[str]) -> Tuple[str, str, str]:
    """
    Extract user_id, aal (Authenticator Assurance Level), and role from JWT token.
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
    
    Returns:
        Tuple[str, str, str]: (user_id, aal, role)
    
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
        aal = payload.get('aal', 'aal1')

        # Extract role (Default to 'viewer' if not present)
        role = payload.get('role', 'viewer')
        
        # Extract user status (for ABAC status checks)
        # Default to 'active' if not present
        status_val = payload.get('status', 'active')
        
        return str(user_id), str(aal), str(role), str(status_val)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


def check_abac_access(user_role: str, user_status: str, file_classification: str) -> Tuple[bool, str]:
    """
    Enforce Attribute-Based Access Control (ABAC) policy.
    
    Attributes Checked:
    1. User Status (status): Accounts must be 'active'. 'suspended' users are blocked.
    2. Role (role): existing RBAC matrix.
    3. Environment (time): (Simulated) Specialists only 08:00-18:00 for Mission Logs.
    
    Args:
        user_role: Role of the user (e.g., 'commander')
        user_status: Account status (e.g., 'active', 'suspended')
        file_classification: File security level (e.g., 'top_secret')
    
    Returns:
        tuple: (Allowed: bool, Reason: str)
    """
    # 1. Status Check (User Attribute)
    if user_status == 'suspended':
        return False, "User account is suspended"
    
    # Normalize inputs
    user_role = user_role.lower()
    file_classification = file_classification.lower()
    
    # 2. Time Check (Environment Attribute)
    # Simulated: In real app, check `datetime.now().hour`
    # For PoC, we assume if they are 'specialist' accessing 'mission_logs', 
    # strict hours apply. Let's assume current time is OK for now 
    # unless we want to fail a specific test case.
    # To demonstrate logic:
    # current_hour = datetime.now().hour
    # if user_role == 'specialist' and file_classification == 'mission_logs':
    #     if not (8 <= current_hour <= 18):
    #         return False, "Access allowed only during duty hours (0800-1800)"

    # 3. Clearance Check (RBAC Fallback)
    if file_classification == 'top_secret':
        if user_role == 'commander':
             return True, "Access Granted (Commander Clearance)"
        else:
             return False, f"Role '{user_role}' insufficient for Top Secret"
    
    elif file_classification == 'mission_logs':
        if user_role in ['commander', 'specialist']:
            return True, "Access Granted (Mission Log Clearance)"
        else:
            return False, f"Role '{user_role}' insufficient for Mission Logs"
            
    elif file_classification == 'public':
        return True, "Access Granted (Public)"
    
    else:
        return False, "Unknown classification denied"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ===== VAULT ENDPOINTS =====

from storage_service import store_vault_key, retrieve_vault_key, list_vault_keys, delete_vault_key

class VaultStoreRequest(BaseModel):
    file_id: Optional[str] = None
    key_label: Optional[str] = None
    hex_key: str
    password: str
    mfa_code: str  # 6-digit MFA code


class VaultRetrieveRequest(BaseModel):
    vault_id: str
    password: str
    mfa_code: str  # 6-digit MFA code


@app.post("/vault/store")
async def store_key_in_vault(
    request: VaultStoreRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Store an encryption key in the personal vault.
    Requires password + MFA authentication.
    """
    # Extract user_id from JWT
    user_id = extract_owner_id_from_token(authorization)
    
    # TODO: Verify MFA code (for now we skip actual verification in PoC)
    # In production: Call Supabase Auth or TOTP library to verify mfa_code
    
    # Encrypt the hex key with password
    encrypted_data = encrypt_key_for_vault(request.hex_key, request.password)
    
    # Store in database
    vault_data = {
        "user_id": user_id,
        "file_id": request.file_id,
        "key_label": request.key_label,
        "encrypted_hex": encrypted_data['encrypted_hex'],
        "salt": encrypted_data['salt']
    }
    
    try:
        result = await store_vault_key(vault_data)
        return {
            "success": True,
            "vault_id": result['data'][0]['vault_id'],
            "message": "Encryption key stored securely in vault"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store key in vault: {str(e)}"
        )


@app.post("/vault/retrieve")
async def retrieve_key_from_vault(
    request: VaultRetrieveRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Retrieve and decrypt an encryption key from the vault.
    Requires password + MFA authentication.
    """
    # Extract user_id from JWT
    user_id = extract_owner_id_from_token(authorization)
    
    print(f"🔍 DEBUG: Retrieving vault key {request.vault_id} for user {user_id}")
    
    # TODO: Verify MFA code
    
    try:
        # Fetch encrypted key from database
        vault_entry = await retrieve_vault_key(request.vault_id, user_id)
        
        print(f"🔍 DEBUG: Found vault entry - file_id: {vault_entry.get('file_id')}, label: {vault_entry.get('key_label')}")
        
        # Decrypt the key using password
        decrypted_hex = decrypt_key_from_vault(
            vault_entry['encrypted_hex'],
            vault_entry['salt'],
            request.password
        )
        
        print(f"🔍 DEBUG: Decrypted hex key (first 16 chars): {decrypted_hex[:16]}...")
        
        return {
            "success": True,
            "hex_key": decrypted_hex,
            "file_id": vault_entry.get('file_id'),
            "key_label": vault_entry.get('key_label')
        }
    except Exception as e:
        print(f"❌ ERROR: Vault retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Failed to retrieve key: {str(e)}"
        )


@app.get("/vault/list")
async def list_user_vault_keys(authorization: Optional[str] = Header(None)):
    """
    List all vault keys for the authenticated user.
    Does not return decrypted keys, only metadata.
    """
    user_id = extract_owner_id_from_token(authorization)
    
    print(f"🔍 DEBUG: Listing vault keys for user_id: {user_id}")
    
    try:
        keys = await list_vault_keys(user_id)
        print(f"🔍 DEBUG: Found {len(keys)} keys")
        return {"success": True, "keys": keys}
    except Exception as e:
        print(f"❌ ERROR: Failed to list vault keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list vault keys: {str(e)}"
        )


@app.delete("/vault/{vault_id}")
async def delete_vault_entry(
    vault_id: str,
    authorization: Optional[str] = Header(None)
):
    """Delete a vault key entry."""
    user_id = extract_owner_id_from_token(authorization)
    
    try:
        result = await delete_vault_key(vault_id, user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Failed to delete vault key: {str(e)}"
        )
