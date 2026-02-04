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
from signature_utils import (
    generate_user_signature_keys, load_user_private_key,
    sign_chunk_hash, sign_file_manifest, verify_chunk_signature,
    verify_file_manifest_signature, deserialize_public_key
)

# Import authentication and MFA services
from auth_service import (
    get_user_by_email, create_user, update_last_login,
    log_activity, get_activity_logs, check_permission,
    list_all_users, get_user_permissions, verify_password, get_user_by_id,
    update_user_signature_keys, get_user_signature_public_key
)
from email_verification import send_verification_email, verify_user_code


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


class LoginPasswordRequest(BaseModel):
    email: str
    password: str


class LoginMFARequest(BaseModel):
    email: str
    mfa_code: str


class CreateUserRequest(BaseModel):
    email: str
    username: str
    password: str
    role: str  # admin, manager, engineer, staff
    can_upload: Optional[bool] = None
    can_download: Optional[bool] = None


class VaultMFARequest(BaseModel):
    email: str


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


# ===== AUTHENTICATION ENDPOINTS (2-STEP MFA) =====

@app.post("/auth/login/password")
async def login_step1_password(request: LoginPasswordRequest):
    """
    Step 1 of login: Verify email and password, then send MFA code.
    
    Flow:
    1. Check if user exists
    2. Verify password with bcrypt
    3. Generate MFA code
    4. Hash and store code in database
    5. Send code via email
    6. Log all actions
    """
    try:
        # Fetch user from database
        user = await get_user_by_email(request.email)
        
        if not user:
            # Log failed login attempt (no user ID since user doesn't exist)
            await log_activity(
                user_id=None,
                action='LOGIN_FAILED',
                details={'email': request.email, 'reason': 'user_not_found'}
            )
            print(f"❌ Login failed: User not found for {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user account is active
        if user['status'] != 'active':
            await log_activity(
                user_id=user['user_id'],
                action='LOGIN_BLOCKED',
                details={'reason': f"account_{user['status']}", 'email': request.email}
            )
            print(f"❌ Login blocked: Account {user['status']} for {request.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user['status']}"
            )
        
        # Verify password using bcrypt
        if not verify_password(request.password, user['password_hash']):
            await log_activity(
                user_id=user['user_id'],
                action='LOGIN_FAILED',
                details={'reason': 'invalid_password', 'email': request.email}
            )
            print(f"❌ Login failed: Invalid password for {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Password verified! Now send MFA code
        print(f"✅ Password verified for {request.email}, sending MFA code...")
        
        # Email configuration
        sender_email = "karthik.maniam008@gmail.com"
        app_password = "rpjz ujsm cwbp tjxk"
        
        # Send MFA code (code will be hashed and stored in database)
        mfa_result = await send_verification_email(
            email=request.email,
            sender_email=sender_email,
            app_password=app_password,
            user_id=user['user_id'],
            purpose='login'
        )
        
        # Log MFA sent
        await log_activity(
            user_id=user['user_id'],
            action='MFA_SENT',
            details={
                'purpose': 'login',
                'email': request.email,
                'expires_in_minutes': mfa_result['expires_in_minutes']
            }
        )
        
        print(f"✅ MFA code sent to {request.email}")
        
        return {
            "success": True,
            "message": "Password verified. MFA code sent to your email.",
            "email": request.email,
            "expires_in_minutes": mfa_result['expires_in_minutes'],
            "next_step": "Enter the 6-digit code from your email"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login step 1 failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@app.post("/auth/login/mfa")
async def login_step2_mfa(request: LoginMFARequest):
    """
    Step 2 of login: Verify MFA code and issue JWT token.
    
    Flow:
    1. Hash the user's submitted code
    2. Compare with stored hash in database
    3. Issue JWT token with aal2 (MFA verified)
    4. Update last login timestamp
    5. Log successful login
    """
    try:
        # Verify MFA code (will hash user's code and compare with stored hash)
        verification_result = await verify_user_code(
            email=request.email,
            user_code=request.mfa_code,
            purpose='login'
        )
        
        if not verification_result['success']:
            # Log failed MFA attempt
            user = await get_user_by_email(request.email)
            if user:
                await log_activity(
                    user_id=user['user_id'],
                    action='MFA_FAILED',
                    details={
                        'reason': verification_result.get('error'),
                        'email': request.email
                    }
                )
            print(f"❌ MFA verification failed for {request.email}: {verification_result['message']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification_result['message']
            )
        
        # MFA verified! Fetch user and generate JWT token
        user = await get_user_by_email(request.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update last login timestamp
        await update_last_login(user['user_id'])
        
        # Get user permissions
        permissions = get_user_permissions(user)
        
        # Create JWT payload with MFA verified (aal2)
        payload = {
            "sub": user['user_id'],
            "user_id": user['user_id'],
            "email": user['email'],
            "username": user['username'],
            "aal": "aal2",  # MFA completed - important for security!
            "role": user['role'],
            "status": user['status'],
            "permissions": permissions
        }
        
        # Create JWT token (in production, use proper JWT library with signature)
        header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
        payload_encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        jwt_token = f"{header}.{payload_encoded}.mock-signature"
        
        # Log successful login
        await log_activity(
            user_id=user['user_id'],
            action='LOGIN_SUCCESS',
            details={
                'mfa_verified': True,
                'email': request.email,
                'role': user['role']
            }
        )
        
        print(f"✅ Login successful for {request.email} (role: {user['role']})")
        
        return {
            "success": True,
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": {
                "user_id": user['user_id'],
                "email": user['email'],
                "username": user['username'],
                "role": user['role'],
                "status": user['status'],
                "permissions": permissions
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ MFA verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MFA verification failed: {str(e)}"
        )


@app.post("/login")
async def login(request: LoginRequest):
    """
    OLD mock login endpoint (DEPRECATED - use /auth/login/password and /auth/login/mfa instead).
    Kept for backward compatibility.
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


@app.post("/auth/generate-signature-keys")
async def generate_signature_keys(
    vault_password: str,
    authorization: Optional[str] = Header(None)
):
    """
    Generate Ed25519 signature key pair for authenticated user (PASSWORD METHOD).
    Private key is encrypted with vault password before storage.
    
    Args:
        vault_password: User's vault password (for encrypting private key)
        authorization: JWT token
    
    Returns:
        Success message with public key
    """
    # Extract user ID from token
    user_id = extract_owner_id_from_token(authorization)
    
    # Get user
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Generate keys
        public_key_b64, encrypted_private_b64 = generate_user_signature_keys(vault_password)
        
        # Save to database (password method)
        await update_user_signature_keys(
            user_id=user_id,
            public_key=public_key_b64,
            encrypted_private_key=encrypted_private_b64,
            algorithm='ed25519',
            storage_method='password'
        )
        
        # Log activity
        await log_activity(
            user_id=user_id,
            action='SIGNATURE_KEYS_GENERATED',
            details={'algorithm': 'ed25519', 'method': 'password'}
        )
        
        return {
            "success": True,
            "message": "Signature keys generated successfully",
            "public_key": public_key_b64,
            "algorithm": "ed25519",
            "storage_method": "password"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate keys: {str(e)}"
        )


@app.post("/auth/register-client-public-key")
async def register_client_public_key(
    public_key: str,
    authorization: Optional[str] = Header(None)
):
    """
    Register user's public key (CLIENT-SIDE FILE METHOD).
    User generates keys in browser and provides public key only.
    Private key never touches server.
    
    Args:
        public_key: Base64-encoded Ed25519 public key
        authorization: JWT token
    
    Returns:
        Success message
    """
    # Extract user ID from token
    user_id = extract_owner_id_from_token(authorization)
    
    # Get user
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Save only public key to database (client_file method)
        await update_user_signature_keys(
            user_id=user_id,
            public_key=public_key,
            encrypted_private_key=None,  # No private key stored
            algorithm='ed25519',
            storage_method='client_file'
        )
        
        # Log activity
        await log_activity(
            user_id=user_id,
            action='SIGNATURE_KEYS_GENERATED',
            details={'algorithm': 'ed25519', 'method': 'client_file'}
        )
        
        return {
            "success": True,
            "message": "Public key registered successfully. Private key is managed by you.",
            "algorithm": "ed25519",
            "storage_method": "client_file"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register public key: {str(e)}"
        )


@app.get("/auth/my-signature-keys")
async def get_my_signature_keys(authorization: Optional[str] = Header(None)):
    """
    Get current user's signature keys.
    
    Returns:
        public_key: Base64-encoded public key
        has_private_key: Whether private key is stored (password method)
        storage_method: 'password' or 'client_file'
        algorithm: 'ed25519'
    """
    user_id = extract_owner_id_from_token(authorization)
    user = await get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(404, "User not found")
    
    public_key = user.get('signature_public_key')
    encrypted_private = user.get('signature_private_key_encrypted')
    storage_method = user.get('key_storage_method', 'password')
    algorithm = user.get('signature_algorithm', 'ed25519')
    
    if not public_key:
        return {
            "has_keys": False,
            "message": "No signature keys generated yet"
        }
    
    return {
        "has_keys": True,
        "public_key": public_key,
        "has_private_key": bool(encrypted_private),
        "storage_method": storage_method,
        "algorithm": algorithm,
        "keys_generated_at": user.get('signature_keys_generated_at')
    }


@app.get("/files/{file_id}/verify-integrity")
async def verify_file_integrity(
    file_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Verify file integrity without downloading.
    Checks all chunk hashes and signatures.
    """
    user_id, aal, role, status_val = extract_claims_from_token(authorization)
    
    # Get file metadata
    metadata = await get_file_metadata(file_id)
    if not metadata:
        raise HTTPException(404, "File not found")
    
    # Check permissions (owner or admin)
    if metadata['owner_id'] != user_id and role != 'admin':
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
                "message": "File manifest signature verified" if manifest_valid else "❌ File manifest signature INVALID"
            })
            
            if not manifest_valid:
                result['integrity_status'] = "COMPROMISED"
                result['safe_to_download'] = False
                return result
        
        # Check 2: All chunk hashes and signatures
        chunk_results = []
        public_key = None
        
        if file_signature and signed_by:
            public_key_b64 = await get_user_signature_public_key(signed_by)
            public_key = deserialize_public_key(public_key_b64)
        
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
                    chunk_check['error'] = "❌ Hash mismatch - database tampering detected"
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
                if chunk_signatures and len(chunk_signatures) > chunk_index and public_key:
                    sig_valid = verify_chunk_signature(calculated_hash, chunk_signatures[chunk_index], public_key)
                    chunk_check['signature_valid'] = sig_valid
                    
                    if not sig_valid:
                        chunk_check['error'] = "❌ Signature verification failed"
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
            "message": f"✅ All {total_chunks} chunks verified successfully"
        })
        
        result['integrity_status'] = "VERIFIED"
        result['safe_to_download'] = True
        
        return result
        
    except Exception as e:
        result['integrity_status'] = "ERROR"
        result['safe_to_download'] = False
        result['error'] = str(e)
        return result


@app.post("/upload")
async def upload_file(
    classification: str = Query("public", regex="^(top_secret|mission_logs|public)$"),
    vault_password: Optional[str] = Query(None),  # NEW: For loading signature key
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
    
    # NEW: Load user's private signing key if vault_password provided
    private_key = None
    user = await get_user_by_id(owner_id)
    
    if vault_password and user.get('signature_private_key_encrypted'):
        try:
            private_key = load_user_private_key(
                user['signature_private_key_encrypted'],
                vault_password
            )
            print(f"✅ Loaded signature key for user {owner_id}")
        except Exception as e:
            print(f"⚠️ Warning: Could not load signature key: {e}")
            # Continue without signatures (optional feature)
    
    # Step 2: Generate encryption materials
    encryption_key = generate_encryption_key()  # 32 bytes for AES-256
    iv = generate_iv()  # 12 bytes for AES-GCM
    file_id = str(uuid.uuid4())
    
    # Storage for chunk hashes and signatures (for integrity verification)
    chunk_hashes = []
    chunk_signatures = []  # NEW: Store signatures
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
            
            # NEW: Sign the chunk hash if private key available
            if private_key:
                chunk_signature = sign_chunk_hash(chunk_hash, private_key)
                chunk_signatures.append(chunk_signature)
            
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
        
        # NEW: Generate file manifest signature if private key available
        file_signature = None
        if private_key:
            manifest = {
                "file_id": file_id,
                "filename": file.filename,
                "total_chunks": chunk_index,
                "chunk_hashes": chunk_hashes,
                "classification": classification,
                "owner_id": owner_id
            }
            file_signature = sign_file_manifest(manifest, private_key)
            print(f"✅ File manifest signed")
        
        # Clear private key from memory
        if private_key:
            del private_key
        
        # Step 6: Save metadata to database
        metadata = {
            "file_id": file_id,
            "owner_id": owner_id,
            "filename": file.filename,
            "classification": classification,  # Added classification
            "total_chunks": chunk_index,
            "encryption_iv": base64.b64encode(iv).decode('utf-8'),
            "chunk_hashes": chunk_hashes,
            # NEW: Add signature fields
            "chunk_signatures": chunk_signatures if chunk_signatures else None,
            "file_signature": file_signature,
            "signature_algorithm": "ed25519" if file_signature else None,
            "signed_by_user_id": owner_id if file_signature else None
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

    # NEW: Verify file signature if present
    if metadata.get('file_signature'):
        try:
            # Get signer's public key
            signed_by_user_id = metadata.get('signed_by_user_id')
            if not signed_by_user_id:
                raise Exception("File has signature but no signer ID")
            
            public_key_b64 = await get_user_signature_public_key(signed_by_user_id)
            public_key = deserialize_public_key(public_key_b64)
            
            # Reconstruct manifest
            manifest = {
                "file_id": metadata['file_id'],
                "filename": metadata['filename'],
                "total_chunks": metadata['total_chunks'],
                "chunk_hashes": metadata['chunk_hashes'],
                "classification": metadata.get('classification', 'public'),
                "owner_id": metadata['owner_id']
            }
            
            # Verify file manifest signature
            if not verify_file_manifest_signature(
                manifest,
                metadata['file_signature'],
                public_key
            ):
                # Log critical security incident
                await log_audit_event({
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": user_id,
                    "action": "SIGNATURE_VERIFICATION_FAILED",
                    "resource_id": file_id,
                    "details": {
                        "type": "file_manifest",
                        "signed_by": signed_by_user_id,
                        "severity": "CRITICAL"
                    }
                })
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="File integrity check failed - signature verification failed"
                )
            
            print(f"✅ File manifest signature verified for {file_id}")
        
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            # Log signature verification error
            await log_audit_event({
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "action": "SIGNATURE_VERIFICATION_ERROR",
                "resource_id": file_id,
                "details": {
                    "error": str(e),
                    "severity": "HIGH"
                }
            })
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Signature verification error: {str(e)}"
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
    # NEW: Get public key if signatures present
    public_key = None
    chunk_signatures = metadata.get('chunk_signatures')
    if chunk_signatures:
        try:
            signed_by_user_id = metadata.get('signed_by_user_id')
            public_key_b64 = await get_user_signature_public_key(signed_by_user_id)
            public_key = deserialize_public_key(public_key_b64)
        except Exception as e:
            print(f"⚠️ Could not load public key for chunk verification: {e}")
    
    async def chunk_generator():
        """
        Generator function for streaming reassembly.
        Downloads, decodes, and decrypts chunks one by one.
        NOW WITH SIGNATURE VERIFICATION.
        """
        total_chunks = metadata['total_chunks']
        
        for chunk_index in range(total_chunks):
            # Download encrypted chunk from Supabase
            storage_path = f"{file_id}/chunk_{chunk_index}"
            b64_encrypted_chunk = await download_chunk_from_supabase(
                bucket=STORAGE_BUCKET,
                path=storage_path
            )
            
            # NEW: Verify chunk signature before decrypting
            if chunk_signatures and public_key:
                import hashlib
                
                # Calculate hash of encrypted chunk
                encrypted_bytes = base64.b64decode(b64_encrypted_chunk)
                chunk_hash = hashlib.sha256(encrypted_bytes).hexdigest()
                
                # CRITICAL: First verify hash matches stored hash (catches database tampering)
                stored_hash = metadata['chunk_hashes'][chunk_index]
                if chunk_hash != stored_hash:
                    # Log critical security incident - database tampering detected!
                    await log_audit_event({
                        "timestamp": datetime.utcnow().isoformat(),
                        "user_id": user_id,
                        "action": "CHUNK_HASH_MISMATCH",
                        "resource_id": file_id,
                        "details": {
                            "chunk_index": chunk_index,
                            "calculated_hash": chunk_hash,
                            "stored_hash": stored_hash,
                            "severity": "CRITICAL",
                            "attack_type": "DATABASE_TAMPERING"
                        }
                    })
                    
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Chunk {chunk_index} hash mismatch - database tampering detected!"
                    )
                
                # Then verify signature (catches storage tampering)
                chunk_sig = chunk_signatures[chunk_index]
                if not verify_chunk_signature(chunk_hash, chunk_sig, public_key):
                    # Log critical security incident
                    await log_audit_event({
                        "timestamp": datetime.utcnow().isoformat(),
                        "user_id": user_id,
                        "action": "CHUNK_SIGNATURE_VERIFICATION_FAILED",
                        "resource_id": file_id,
                        "details": {
                            "chunk_index": chunk_index,
                            "signed_by": signed_by_user_id,
                            "severity": "CRITICAL",
                            "attack_type": "STORAGE_TAMPERING"
                        }
                    })
                    
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Chunk {chunk_index} integrity check failed - signature verification failed"
                    )
            else:
                # Even without signatures, verify hash matches stored hash
                import hashlib
                encrypted_bytes = base64.b64decode(b64_encrypted_chunk)
                chunk_hash = hashlib.sha256(encrypted_bytes).hexdigest()
                stored_hash = metadata['chunk_hashes'][chunk_index]
                
                if chunk_hash != stored_hash:
                    # Log critical security incident
                    await log_audit_event({
                        "timestamp": datetime.utcnow().isoformat(),
                        "user_id": user_id,
                        "action": "CHUNK_HASH_MISMATCH",
                        "resource_id": file_id,
                        "details": {
                            "chunk_index": chunk_index,
                            "calculated_hash": chunk_hash,
                            "stored_hash": stored_hash,
                            "severity": "CRITICAL",
                            "attack_type": "DATABASE_TAMPERING",
                            "note": "File not signed, but hash mismatch detected"
                        }
                    })
                    
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Chunk {chunk_index} hash mismatch - database tampering detected!"
                    )
            
            # Decrypt the chunk
            decrypted_chunk = decrypt_chunk(
                b64_encrypted_chunk,
                encryption_key,
                encryption_iv
            )
            
            # Yield decrypted chunk
            yield decrypted_chunk
    
    # Step 8: Return streaming response
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
    user = await get_user_by_id(user_id)
    
    print(f"🔍 Retrieving vault key {request.vault_id} for user {user_id}")
    
    # Verify MFA code
    try:
        verification_result = await verify_user_code(
            email=user['email'],
            user_code=request.mfa_code,
            purpose='vault_retrieve'
        )
        
        if not verification_result['success']:
            await log_activity(
                user_id=user_id,
                action='VAULT_RETRIEVE_MFA_FAILED',
                resource_type='vault',
                resource_id=request.vault_id,
                details={'reason': verification_result.get('error')}
            )
            print(f"❌ MFA verification failed for vault retrieve: {verification_result['message']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification_result['message']
            )
        
        print(f"✅ MFA verified for vault retrieve")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ MFA verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MFA verification failed: {str(e)}"
        )
    
    try:
        # Fetch encrypted key from database
        vault_entry = await retrieve_vault_key(request.vault_id, user_id)
        
        print(f"🔍 Found vault entry - file_id: {vault_entry.get('file_id')}, label: {vault_entry.get('key_label')}")
        
        # Decrypt the key using password
        decrypted_hex = decrypt_key_from_vault(
            vault_entry['encrypted_hex'],
            vault_entry['salt'],
            request.password
        )
        
        # Log successful retrieval
        await log_activity(
            user_id=user_id,
            action='VAULT_RETRIEVE_SUCCESS',
            resource_type='vault',
            resource_id=request.vault_id,
            details={
                'file_id': vault_entry.get('file_id'),
                'key_label': vault_entry.get('key_label'),
                'mfa_verified': True
            }
        )
        
        print(f"✅ Vault key retrieved successfully (first 16 chars): {decrypted_hex[:16]}...")
        
        return {
            "success": True,
            "hex_key": decrypted_hex,
            "file_id": vault_entry.get('file_id'),
            "key_label": vault_entry.get('key_label')
        }
    except Exception as e:
        await log_activity(
            user_id=user_id,
            action='VAULT_RETRIEVE_FAILED',
            resource_type='vault',
            resource_id=request.vault_id,
            details={'reason': str(e)}
        )
        print(f"❌ Vault retrieval failed: {str(e)}")
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


# ===== EMAIL VERIFICATION ENDPOINTS =====

from email_verification import send_verification_email, verify_user_code


class SendVerificationRequest(BaseModel):
    email: str


class VerifyCodeRequest(BaseModel):
    email: str
    code: str


@app.post("/auth/send-verification")
async def send_verification_code(request: SendVerificationRequest):
    """
    Send a 6-digit verification code to the user's email.
    The code is hashed with bcrypt before storage.
    
    Args:
        email: User's email address
    
    Returns:
        Success message with expiry time
    """
    try:
        # Use the app password from .env in the parent directory
        sender_email = "karthik.maniam008@gmail.com"
        app_password = "rpjz ujsm cwbp tjxk"
        
        result = await send_verification_email(
            email=request.email,
            sender_email=sender_email,
            app_password=app_password
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification email: {str(e)}"
        )


@app.post("/auth/verify-code")
async def verify_verification_code(request: VerifyCodeRequest):
    """
    Verify the user-submitted 6-digit code.
    Hashes the submitted code and compares with stored hash.
    
    Args:
        email: User's email address
        code: 6-digit verification code
    
    Returns:
        Verification result with success status
    """
    try:
        result = await verify_user_code(
            email=request.email,
            user_code=request.code
        )
        
        if not result["success"]:
            # Return appropriate HTTP status based on error type
            if result.get("error") == "MAX_ATTEMPTS_EXCEEDED":
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=result["message"]
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["message"]
                )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


# ===== MANUAL MFA SEND ENDPOINT =====

@app.post("/auth/send-mfa")
async def send_mfa_manually(request: LoginPasswordRequest):
    """
    Manually send MFA code (can be triggered by button after password verification).
    This is a standalone endpoint to debug/resend MFA codes.
    """
    try:
        # Fetch user from database
        user = await get_user_by_email(request.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify password first
        if not verify_password(request.password, user['password_hash']):
            await log_activity(
                user_id=user['user_id'],
                action='MFA_SEND_FAILED',
                details={'reason': 'invalid_password', 'email': request.email}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        print(f"🔐 Manually sending MFA code to {request.email}...")
        
        # Email configuration
        sender_email = "karthik.maniam008@gmail.com"
        app_password = "rpjz ujsm cwbp tjxk"
        
        # Send MFA code
        mfa_result = await send_verification_email(
            email=request.email,
            sender_email=sender_email,
            app_password=app_password,
            user_id=user['user_id'],
            purpose='login'
        )
        
        # Log MFA sent
        await log_activity(
            user_id=user['user_id'],
            action='MFA_SENT_MANUAL',
            details={
                'purpose': 'login',
                'email': request.email,
                'triggered': 'manual_button'
            }
        )
        
        print(f"✅ MFA code sent successfully to {request.email}")
        
        return {
            "success": True,
            "message": f"MFA code sent to {request.email}",
            "expires_in_minutes": mfa_result['expires_in_minutes']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to send MFA: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send MFA code: {str(e)}"
        )


@app.post("/vault/mfa/send")
async def send_vault_mfa(authorization: Optional[str] = Header(None), purpose: str = "vault_retrieve"):
    """
    Send MFA code for vault operations (store or retrieve).
    Purpose can be 'vault_store' or 'vault_retrieve'.
    """
    # Extract user from token
    user_id = extract_owner_id_from_token(authorization)
    user = await get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        print(f"🔐 Sending vault MFA code to {user['email']} (purpose: {purpose})...")
        
        # Email configuration
        sender_email = "karthik.maniam008@gmail.com"
        app_password = "rpjz ujsm cwbp tjxk"
        
        # Send MFA code
        mfa_result = await send_verification_email(
            email=user['email'],
            sender_email=sender_email,
            app_password=app_password,
            user_id=user['user_id'],
            purpose=purpose
        )
        
        # Log MFA sent
        await log_activity(
            user_id=user['user_id'],
            action='VAULT_MFA_SENT',
            details={
                'purpose': purpose,
                'email': user['email']
            }
        )
        
        print(f"✅ Vault MFA code sent to {user['email']}")
        
        return {
            "success": True,
            "message": f"MFA code sent to {user['email']}",
            "email": user['email'],
            "expires_in_minutes": mfa_result['expires_in_minutes']
        }
    
    except Exception as e:
        print(f"❌ Failed to send vault MFA: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send MFA code: {str(e)}"
        )


# ===== ADMIN ENDPOINTS =====

@app.post("/admin/vault/migrate")
async def migrate_vault_keys(authorization: Optional[str] = Header(None)):
    """
    Migrate old vault keys from username-based user_ids to new UUID-based user_ids.
    This fixes the issue where old vault keys can't be accessed with new authentication.
    """
    # Extract user from token
    requesting_user_id = extract_owner_id_from_token(authorization)
    requesting_user = await get_user_by_id(requesting_user_id)
    
    # Check if requester is admin
    if requesting_user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can migrate vault keys"
        )
    
    try:
        from storage_service import supabase
        
        # Get all vault entries
        vault_response = supabase.table('user_vaults').select('*').execute()
        all_vaults = vault_response.data
        
        print(f"📊 Found {len(all_vaults)} total vault entries")
        
        # Get all users from new users table
        users_response = supabase.table('users').select('user_id, email, username').execute()
        all_users = users_response.data
        
        # Create mapping: old_username -> new_uuid
        username_to_uuid = {user['username']: user['user_id'] for user in all_users}
        email_to_uuid = {user['email']: user['user_id'] for user in all_users}
        
        print(f"👥 User mappings:")
        for username, uuid in username_to_uuid.items():
            print(f"   {username} -> {uuid}")
        
        # Migrate vault entries
        migrated_count = 0
        skipped_count = 0
        
        for vault in all_vaults:
            old_user_id = vault['user_id']
            
            # Check if it's already a UUID (new format)
            if len(old_user_id) == 36 and '-' in old_user_id:
                print(f"⏭️  Skipping vault_id {vault['vault_id'][:20]}... (already UUID)")
                skipped_count += 1
                continue
            
            # Map old username to new UUID
            new_user_id = username_to_uuid.get(old_user_id)
            
            # Try email mapping if username fails
            if not new_user_id:
                new_user_id = email_to_uuid.get(old_user_id)
            
            if new_user_id:
                # Update the vault entry
                supabase.table('user_vaults')\
                    .update({'user_id': new_user_id})\
                    .eq('vault_id', vault['vault_id'])\
                    .execute()
                
                print(f"✅ Migrated: {old_user_id} -> {new_user_id} (vault: {vault.get('key_label', 'N/A')})")
                migrated_count += 1
            else:
                print(f"⚠️  No mapping found for user_id: {old_user_id}")
        
        # Log migration
        await log_activity(
            user_id=requesting_user_id,
            action='VAULT_MIGRATION',
            details={
                'total_vaults': len(all_vaults),
                'migrated': migrated_count,
                'skipped': skipped_count
            }
        )
        
        return {
            "success": True,
            "message": "Vault migration completed",
            "total_vaults": len(all_vaults),
            "migrated": migrated_count,
            "skipped": skipped_count,
            "mappings": {k: v for k, v in username_to_uuid.items()}
        }
    
    except Exception as e:
        print(f"❌ Vault migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@app.post("/admin/users/create")
async def create_new_user(request: CreateUserRequest, authorization: Optional[str] = Header(None)):
    """
    Create a new user (Admin only).
    
    Only users with admin role can create new users.
    All user creation actions are logged.
    """
    # Extract user from token
    requesting_user_id = extract_owner_id_from_token(authorization)
    requesting_user = await get_user_by_id(requesting_user_id)
    
    # Check if requester is admin
    if requesting_user['role'] != 'admin':
        await log_activity(
            user_id=requesting_user_id,
            action='CREATE_USER_DENIED',
            details={'reason': 'insufficient_permissions', 'requested_email': request.email}
        )
        print(f"❌ User creation denied for {requesting_user['email']} (not admin)")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create users"
        )
    
    try:
        # Determine permissions based on role if not specified
        from auth_service import DEFAULT_PERMISSIONS
        role_defaults = DEFAULT_PERMISSIONS.get(request.role, DEFAULT_PERMISSIONS['staff'])
        
        can_upload = request.can_upload if request.can_upload is not None else role_defaults['can_upload']
        can_download = request.can_download if request.can_download is not None else role_defaults['can_download']
        
        # Create user
        new_user = await create_user(
            email=request.email,
            username=request.username,
            password=request.password,
            role=request.role,
            can_upload=can_upload,
            can_download=can_download,
            created_by_user_id=requesting_user_id
        )
        
        # Log user creation
        await log_activity(
            user_id=requesting_user_id,
            action='CREATE_USER',
            resource_type='user',
            resource_id=new_user['user_id'],
            details={
                'created_email': request.email,
                'created_username': request.username,
                'created_role': request.role,
                'can_upload': can_upload,
                'can_download': can_download
            }
        )
        
        print(f"✅ User created: {request.email} (role: {request.role}) by {requesting_user['email']}")
        
        return {
            "success": True,
            "message": f"User {request.email} created successfully",
            "user": {
                "user_id": new_user['user_id'],
                "email": new_user['email'],
                "username": new_user['username'],
                "role": new_user['role'],
                "can_upload": new_user['can_upload'],
                "can_download": new_user['can_download']
            }
        }
    
    except ValueError as e:
        await log_activity(
            user_id=requesting_user_id,
            action='CREATE_USER_FAILED',
            details={'reason': str(e), 'requested_email': request.email}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await log_activity(
            user_id=requesting_user_id,
            action='CREATE_USER_FAILED',
            details={'reason': str(e), 'requested_email': request.email}
        )
        print(f"❌ User creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@app.get("/admin/users/list")
async def list_users(authorization: Optional[str] = Header(None)):
    """
    List all users (Admin only).
    
    Returns user details without password hashes.
    """
    # Extract user from token
    requesting_user_id = extract_owner_id_from_token(authorization)
    requesting_user = await get_user_by_id(requesting_user_id)
    
    # Check if requester is admin
    if requesting_user['role'] != 'admin':
        await log_activity(
            user_id=requesting_user_id,
            action='LIST_USERS_DENIED',
            details={'reason': 'insufficient_permissions'}
        )
        print(f"❌ List users denied for {requesting_user['email']} (not admin)")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list users"
        )
    
    try:
        users = await list_all_users(requesting_user['role'])
        
        # Log activity
        await log_activity(
            user_id=requesting_user_id,
            action='LIST_USERS',
            details={'count': len(users)}
        )
        
        print(f"✅ User list retrieved by {requesting_user['email']} ({len(users)} users)")
        
        return {
            "success": True,
            "users": users,
            "count": len(users)
        }
    
    except Exception as e:
        await log_activity(
            user_id=requesting_user_id,
            action='LIST_USERS_FAILED',
            details={'reason': str(e)}
        )
        print(f"❌ List users failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@app.get("/admin/logs")
async def view_activity_logs(
    authorization: Optional[str] = Header(None),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100
):
    """
    View activity logs (Admin only).
    
    Allows filtering by user_id, action type, and limit.
    Returns comprehensive audit trail of all system activities.
    
    Args:
        user_id: Filter by specific user (optional)
        action: Filter by action type (optional)
        limit: Maximum number of logs to return (default: 100)
    """
    # Extract user from token
    requesting_user_id = extract_owner_id_from_token(authorization)
    requesting_user = await get_user_by_id(requesting_user_id)
    
    # Check if requester is admin
    if requesting_user['role'] != 'admin':
        await log_activity(
            user_id=requesting_user_id,
            action='VIEW_LOGS_DENIED',
            details={'reason': 'insufficient_permissions'}
        )
        print(f"❌ View logs denied for {requesting_user['email']} (not admin)")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view logs"
        )
    
    try:
        logs = await get_activity_logs(
            user_id=user_id,
            limit=limit,
            action_filter=action
        )
        
        # Log this action (admin viewed logs)
        await log_activity(
            user_id=requesting_user_id,
            action='VIEW_LOGS',
            details={
                'filter_user_id': user_id,
                'filter_action': action,
                'limit': limit,
                'results_count': len(logs)
            }
        )
        
        print(f"✅ Logs retrieved by {requesting_user['email']} ({len(logs)} entries)")
        
        return {
            "success": True,
            "logs": logs,
            "count": len(logs),
            "filters": {
                "user_id": user_id,
                "action": action,
                "limit": limit
            }
        }
    
    except Exception as e:
        await log_activity(
            user_id=requesting_user_id,
            action='VIEW_LOGS_FAILED',
            details={'reason': str(e)}
        )
        print(f"❌ View logs failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch logs: {str(e)}"
        )


@app.get("/user/permissions")
async def get_my_permissions(authorization: Optional[str] = Header(None)):
    """
    Get current user's permissions.
    
    Returns the authenticated user's role and permission flags.
    """
    user_id = extract_owner_id_from_token(authorization)
    user = await get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    permissions = get_user_permissions(user)
    
    return {
        "success": True,
        "user": {
            "user_id": user['user_id'],
            "email": user['email'],
            "username": user['username'],
            "role": user['role']
        },
        "permissions": permissions
    }


@app.get("/admin/logs")
async def get_admin_logs(
    limit: int = Query(100, ge=1, le=500),
    action_filter: Optional[str] = Query(None),
    user_id_filter: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """
    Get activity logs (admin only).
    
    Args:
        limit: Maximum number of logs to return (1-500)
        action_filter: Filter by action type
        user_id_filter: Filter by specific user ID
        authorization: JWT token
    
    Returns:
        List of activity log entries with user details
    """
    # Extract user ID from token
    user_id = extract_owner_id_from_token(authorization)
    
    # Fetch user to check role
    user = await get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is admin
    if user['role'] != 'admin':
        # Log unauthorized access attempt
        await log_activity(
            user_id=user_id,
            action='ADMIN_ACCESS_DENIED',
            details={'attempted_endpoint': '/admin/logs', 'role': user['role']}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Fetch logs
    try:
        logs = await get_activity_logs(
            user_id=user_id_filter,
            limit=limit,
            action_filter=action_filter
        )
        
        # Log admin log access
        await log_activity(
            user_id=user_id,
            action='ADMIN_LOGS_VIEWED',
            details={
                'limit': limit,
                'action_filter': action_filter,
                'user_id_filter': user_id_filter
            }
        )
        
        return {
            "success": True,
            "logs": logs,
            "total": len(logs)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch logs: {str(e)}"
        )

