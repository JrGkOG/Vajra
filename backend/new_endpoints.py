"""
Updated authentication and admin endpoints with email MFA integration.
Add these endpoints to your main.py file.
"""

from pydantic import BaseModel
from fastapi import HTTPException, Header, status
from typing import Optional
import base64
import json

# Import new services
from auth_service import (
    get_user_by_email, create_user, update_last_login, log_activity,
    get_activity_logs, check_permission, list_all_users, get_user_permissions,
    verify_password, get_user_by_id
)
from email_verification import send_verification_email, verify_user_code


# ===== REQUEST/RESPONSE MODELS =====

class LoginStepResponse(BaseModel):
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
    can_upload: Optional[bool] = None  # If None, use role defaults
    can_download: Optional[bool] = None


class VaultMFARequest(BaseModel):
    email: str


# ===== AUTHENTICATION ENDPOINTS =====

@app.post("/auth/login/password")
async def login_step1_password(request: LoginStepResponse):
    """
    Step 1: Verify email and password, then send MFA code.
    
    Args:
        email: User's email
        password: User's password
    
    Returns:
        Success message indicating MFA code was sent
    """
    try:
        # Fetch user from database
        user = await get_user_by_email(request.email)
        
        if not user:
            # Log failed login attempt
            await log_activity(
                user_id=None,
                action='LOGIN_FAILED',
                details={'email': request.email, 'reason': 'user_not_found'}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is suspended
        if user['status'] != 'active':
            await log_activity(
                user_id=user['user_id'],
                action='LOGIN_BLOCKED',
                details={'reason': f'account_{user["status"]}'}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user['status']}"
            )
        
        # Verify password
        if not verify_password(request.password, user['password_hash']):
            await log_activity(
                user_id=user['user_id'],
                action='LOGIN_FAILED',
                details={'reason': 'invalid_password'}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Password verified! Send MFA code
        sender_email = "karthik.maniam008@gmail.com"
        app_password = "rpjz ujsm cwbp tjxk"
        
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
            details={'purpose': 'login'}
        )
        
        return {
            "success": True,
            "message": "Password verified. MFA code sent to your email.",
            "email": request.email,
            "expires_in_minutes": mfa_result['expires_in_minutes']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@app.post("/auth/login/mfa")
async def login_step2_mfa(request: LoginMFARequest):
    """
    Step 2: Verify MFA code and issue JWT token.
    
    Args:
        email: User's email
        mfa_code: 6-digit MFA code from email
    
    Returns:
        JWT token and user information
    """
    try:
        # Verify MFA code
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
                    details={'reason': verification_result.get('error')}
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification_result['message']
            )
        
        # MFA verified! Fetch user and generate token
        user = await get_user_by_email(request.email)
        
        # Update last login
        await update_last_login(user['user_id'])
        
        # Get user permissions
        permissions = get_user_permissions(user)
        
        # Create JWT payload
        payload = {
            "sub": user['user_id'],
            "user_id": user['user_id'],
            "email": user['email'],
            "username": user['username'],
            "aal": "aal2",  # MFA completed
            "role": user['role'],
            "status": user['status'],
            "permissions": permissions
        }
        
        # Create mock JWT (in production, use proper JWT library)
        header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
        payload_encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        mock_token = f"{header}.{payload_encoded}.mock-signature"
        
        # Log successful login
        await log_activity(
            user_id=user['user_id'],
            action='LOGIN_SUCCESS',
            details={'mfa_verified': True}
        )
        
        return {
            "success": True,
            "access_token": mock_token,
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MFA verification failed: {str(e)}"
        )


# ===== ADMIN ENDPOINTS =====

@app.post("/admin/users/create")
async def create_new_user(request: CreateUserRequest, authorization: Optional[str] = Header(None)):
    """
    Create a new user (Admin only).
    
    Requires admin role.
    """
    # Extract user from token
    requesting_user_id = extract_owner_id_from_token(authorization)
    requesting_user = await get_user_by_id(requesting_user_id)
    
    # Check if requester is admin
    if requesting_user['role'] != 'admin':
        await log_activity(
            user_id=requesting_user_id,
            action='CREATE_USER_DENIED',
            details={'reason': 'insufficient_permissions'}
        )
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
                'created_role': request.role
            }
        )
        
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@app.get("/admin/users/list")
async def list_users(authorization: Optional[str] = Header(None)):
    """
    List all users (Admin only).
    """
    # Extract user from token
    requesting_user_id = extract_owner_id_from_token(authorization)
    requesting_user = await get_user_by_id(requesting_user_id)
    
    # Check if requester is admin
    if requesting_user['role'] != 'admin':
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
        
        return {
            "success": True,
            "users": users
        }
    
    except Exception as e:
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
    
    Args:
        user_id: Filter by specific user (optional)
        action: Filter by action type (optional)
        limit: Maximum number of logs to return
    """
    # Extract user from token
    requesting_user_id = extract_owner_id_from_token(authorization)
    requesting_user = await get_user_by_id(requesting_user_id)
    
    # Check if requester is admin
    if requesting_user['role'] != 'admin':
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
        
        return {
            "success": True,
            "logs": logs,
            "count": len(logs)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch logs: {str(e)}"
        )


@app.get("/user/permissions")
async def get_my_permissions(authorization: Optional[str] = Header(None)):
    """
    Get current user's permissions.
    """
    user_id = extract_owner_id_from_token(authorization)
    user = await get_user_by_id(user_id)
    
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


# ===== VAULT ENDPOINTS WITH MFA =====

@app.post("/vault/mfa/send")
async def send_vault_mfa(
    request: VaultMFARequest,
    authorization: Optional[str] = Header(None)
):
    """
    Send MFA code for vault operations.
    """
    user_id = extract_owner_id_from_token(authorization)
    user = await get_user_by_id(user_id)
    
    # Verify email matches user
    if user['email'] != request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email does not match authenticated user"
        )
    
    try:
        sender_email = "karthik.maniam008@gmail.com"
        app_password = "rpjz ujsm cwbp tjxk"
        
        result = await send_verification_email(
            email=request.email,
            sender_email=sender_email,
            app_password=app_password,
            user_id=user_id,
            purpose='vault_store'  # or 'vault_retrieve'
        )
        
        await log_activity(
            user_id=user_id,
            action='VAULT_MFA_SENT',
            details={'email': request.email}
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send MFA code: {str(e)}"
        )
