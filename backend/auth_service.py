"""
Authentication service with role-based access control and email MFA.
"""

import os
import bcrypt
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    'admin': 4,
    'manager': 3,
    'engineer': 2,
    'staff': 1
}


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


async def get_user_by_email(email: str) -> Optional[Dict]:
    """Fetch user from database by email."""
    try:
        response = supabase.table('users').select('*').eq('email', email).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"❌ Error fetching user: {e}")
        return None


async def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Fetch user from database by user_id."""
    try:
        response = supabase.table('users').select('*').eq('user_id', user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"❌ Error fetching user: {e}")
        return None


async def create_user(email: str, username: str, password: str, role: str, 
                     can_upload: bool = True, can_download: bool = True,
                     created_by_user_id: str = None) -> Dict:
    """
    Create a new user (admin only operation).
    
    Args:
        email: User's email
        username: Username
        password: Plain text password (will be hashed)
        role: User role (admin, manager, engineer, staff)
        can_upload: Upload permission
        can_download: Download permission
        created_by_user_id: User ID of the admin creating this user
    
    Returns:
        Created user data
    """
    # Validate role
    if role not in ROLE_HIERARCHY:
        raise ValueError(f"Invalid role: {role}")
    
    # Hash password
    password_hash = hash_password(password)
    
    # Create user
    user_data = {
        'email': email,
        'username': username,
        'password_hash': password_hash,
        'role': role,
        'can_upload': can_upload,
        'can_download': can_download,
        'status': 'active',
        'created_by': created_by_user_id
    }
    
    try:
        response = supabase.table('users').insert(user_data).execute()
        print(f"✅ User created: {email} with role: {role}")
        return response.data[0]
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        raise Exception(f"Failed to create user: {str(e)}")


async def update_last_login(user_id: str):
    """Update user's last login timestamp."""
    try:
        supabase.table('users').update({
            'last_login': datetime.utcnow().isoformat()
        }).eq('user_id', user_id).execute()
    except Exception as e:
        print(f"⚠️  Warning: Failed to update last login: {e}")


async def log_activity(user_id: str, action: str, resource_type: str = None,
                       resource_id: str = None, details: Dict = None,
                       ip_address: str = None, user_agent: str = None):
    """
    Log user activity for audit trail.
    
    Args:
        user_id: User ID performing the action
        action: Action performed (e.g., 'LOGIN', 'UPLOAD', 'DOWNLOAD', 'CREATE_USER')
        resource_type: Type of resource (e.g., 'file', 'user', 'vault')
        resource_id: ID of the resource
        details: Additional JSON details
        ip_address: User's IP address
        user_agent: User's browser/client info
    """
    try:
        log_data = {
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': details or {},
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        supabase.table('activity_logs').insert(log_data).execute()
        print(f"📝 Activity logged: {action} by user {user_id}")

        # Mirror into the hash-chained ledger (tamper-evident; head anchored on-chain)
        from ledger_service import append_entry
        await append_entry(
            source='activity_logs',
            user_id=user_id,
            action=action,
            resource_id=resource_id,
            details=details,
        )
    except Exception as e:
        print(f"⚠️  Warning: Failed to log activity: {e}")


async def get_activity_logs(user_id: str = None, limit: int = 100, 
                           action_filter: str = None) -> list:
    """
    Retrieve activity logs.
    
    Args:
        user_id: Filter by user ID (None = all users, admin only)
        limit: Maximum number of logs to return
        action_filter: Filter by action type
    
    Returns:
        List of activity log entries
    """
    try:
        query = supabase.table('activity_logs').select('*, users(username, email, role)')
        
        if user_id:
            query = query.eq('user_id', user_id)
        
        if action_filter:
            query = query.eq('action', action_filter)
        
        response = query.order('timestamp', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"❌ Error fetching logs: {e}")
        raise Exception(f"Failed to fetch logs: {str(e)}")


def check_permission(user_role: str, required_role: str) -> bool:
    """
    Check if user's role meets or exceeds the required role.
    
    Args:
        user_role: User's role
        required_role: Minimum required role
    
    Returns:
        True if user has sufficient permissions
    """
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


async def list_all_users(requesting_user_role: str) -> list:
    """
    List all users (admin only).
    
    Args:
        requesting_user_role: Role of the user requesting this list
    
    Returns:
        List of users (without password hashes)
    """
    if requesting_user_role != 'admin':
        raise PermissionError("Only admins can list users")
    
    try:
        response = supabase.table('users').select(
            'user_id, email, username, role, can_upload, can_download, '
            'status, created_at, last_login'
        ).order('created_at', desc=True).execute()
        
        return response.data
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        raise Exception(f"Failed to list users: {str(e)}")


# Default permissions by role
DEFAULT_PERMISSIONS = {
    'admin': {
        'can_upload': True,
        'can_download': True,
        'can_create_users': True,
        'can_view_all_logs': True,
        'can_access_all_files': True
    },
    'manager': {
        'can_upload': True,
        'can_download': True,
        'can_create_users': False,
        'can_view_all_logs': False,
        'can_access_all_files': False
    },
    'engineer': {
        'can_upload': True,
        'can_download': True,
        'can_create_users': False,
        'can_view_all_logs': False,
        'can_access_all_files': False
    },
    'staff': {
        'can_upload': False,
        'can_download': True,
        'can_create_users': False,
        'can_view_all_logs': False,
        'can_access_all_files': False
    }
}


def get_user_permissions(user: Dict) -> Dict:
    """
    Get effective permissions for a user.
    
    Args:
        user: User dict from database
    
    Returns:
        Dict of permissions
    """
    role = user['role']
    base_permissions = DEFAULT_PERMISSIONS.get(role, DEFAULT_PERMISSIONS['staff']).copy()
    
    # Override with user-specific permissions
    base_permissions['can_upload'] = user.get('can_upload', base_permissions['can_upload'])
    base_permissions['can_download'] = user.get('can_download', base_permissions['can_download'])
    
    return base_permissions


async def update_user_signature_keys(user_id: str, public_key: str, 
                                     encrypted_private_key: str = None, 
                                     algorithm: str = 'ed25519',
                                     storage_method: str = 'password'):
    """
    Update user's signature keys in database.
    
    Args:
        user_id: User ID
        public_key: Base64-encoded public key
        encrypted_private_key: Encrypted private key (None for client_file method)
        algorithm: Signature algorithm ('ed25519')
        storage_method: 'password' or 'client_file'
    """
    try:
        from datetime import datetime
        supabase.table('users').update({
            'signature_public_key': public_key,
            'signature_private_key_encrypted': encrypted_private_key,
            'signature_algorithm': algorithm,
            'key_storage_method': storage_method,
            'signature_keys_generated_at': datetime.utcnow().isoformat()
        }).eq('user_id', user_id).execute()
        
        print(f"✅ Signature keys updated for user {user_id}")
    except Exception as e:
        print(f"❌ Error updating signature keys: {e}")
        raise Exception(f"Failed to update signature keys: {str(e)}")


async def get_user_signature_public_key(user_id: str) -> str:
    """
    Get user's public signature key.
    
    Args:
        user_id: User ID
    
    Returns:
        Base64-encoded public key
    
    Raises:
        Exception: If user not found or no keys generated
    """
    try:
        response = supabase.table('users').select('signature_public_key').eq('user_id', user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise Exception(f"User {user_id} not found")
        
        public_key = response.data[0].get('signature_public_key')
        
        if not public_key:
            raise Exception(f"User {user_id} has not generated signature keys yet")
        
        return public_key
    
    except Exception as e:
        print(f"❌ Error fetching public key: {e}")
        raise

