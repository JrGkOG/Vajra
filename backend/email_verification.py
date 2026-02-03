"""
Email verification service with secure code hashing.
Generates 6-digit codes, hashes them with bcrypt, stores in database, and validates user input.
"""

import os
import random
import bcrypt
import subprocess
import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuration
MAX_VERIFICATION_ATTEMPTS = 3
CODE_EXPIRY_MINUTES = 10


def generate_verification_code() -> str:
    """Generate a random 6-digit verification code."""
    return str(random.randint(100000, 999999))


def hash_code(code: str) -> str:
    """
    Hash the verification code using bcrypt.
    
    Args:
        code: Plain text verification code
    
    Returns:
        str: Bcrypt hash of the code
    """
    # Convert code to bytes and hash with bcrypt
    code_bytes = code.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(code_bytes, salt)
    return hashed.decode('utf-8')


def verify_code(plain_code: str, hashed_code: str) -> bool:
    """
    Verify a plain text code against a bcrypt hash.
    
    Args:
        plain_code: User-submitted code
        hashed_code: Stored bcrypt hash
    
    Returns:
        bool: True if code matches, False otherwise
    """
    try:
        plain_bytes = plain_code.encode('utf-8')
        hashed_bytes = hashed_code.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception as e:
        print(f"❌ Error verifying code: {e}")
        return False


async def send_verification_email(email: str, sender_email: str, app_password: str, 
                                  user_id: str = None, purpose: str = 'login') -> Dict:
    """
    Generate a verification code, hash it, store in database, and send email.
    
    Args:
        email: Recipient email address
        sender_email: Sender Gmail address
        app_password: Gmail app password
        user_id: Optional user ID for tracking
        purpose: Purpose of MFA (login, vault_store, vault_retrieve)
    
    Returns:
        dict: Success status and message
    """
    # Generate 6-digit code
    code = generate_verification_code()
    
    # Hash the code
    code_hash = hash_code(code)
    
    # Calculate expiry time
    expires_at = datetime.utcnow() + timedelta(minutes=CODE_EXPIRY_MINUTES)
    
    # Clean up any existing codes for this email/purpose
    try:
        supabase.table('mfa_codes').delete().eq('email', email).eq('purpose', purpose).execute()
    except Exception:
        pass  # Ignore if no existing codes
    
    # Store the hash in database
    try:
        mfa_data = {
            'user_id': user_id,
            'email': email,
            'code_hash': code_hash,
            'attempts': 0,
            'purpose': purpose,
            'expires_at': expires_at.isoformat()
        }
        
        supabase.table('mfa_codes').insert(mfa_data).execute()
        print(f"🔐 MFA code hash stored for {email} (purpose: {purpose})")
    except Exception as e:
        raise Exception(f"Failed to store MFA code: {str(e)}")
    
    # Call Node.js script to send email
    try:
        # Pass verification code, email, sender, and app password to Node script
        result = subprocess.run(
            [
                'node',
                '/Users/meenakshiganesan/Karthik/vajra/send-email.js',
                code,  # verification code
                email,  # recipient
                sender_email,  # sender email
                app_password  # app password
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ Verification email sent to {email}")
            return {
                "success": True,
                "message": f"Verification email sent to {email}",
                "expires_in_minutes": CODE_EXPIRY_MINUTES
            }
        else:
            print(f"❌ Email send failed: {result.stderr}")
            raise Exception(f"Email send failed: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        raise Exception("Email send timeout")
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")




async def verify_user_code(email: str, user_code: str, purpose: str = 'login') -> Dict:
    """
    Verify the code submitted by the user.
    
    Args:
        email: User's email address
        user_code: The 6-digit code entered by user
        purpose: Purpose of MFA (must match the purpose when code was sent)
    
    Returns:
        dict: Verification result with success status
    """
    # Fetch MFA code from database
    try:
        response = supabase.table('mfa_codes')\
            .select('*')\
            .eq('email', email)\
            .eq('purpose', purpose)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            return {
                "success": False,
                "error": "NO_CODE_SENT",
                "message": "No verification code found. Please request a new code."
            }
        
        stored_data = response.data[0]
        code_id = stored_data['code_id']
    except Exception as e:
        print(f"❌ Error fetching MFA code: {e}")
        return {
            "success": False,
            "error": "DATABASE_ERROR",
            "message": "Failed to verify code. Please try again."
        }
    
    # Check if code has expired
    expires_at = datetime.fromisoformat(stored_data['expires_at'].replace('Z', '+00:00'))
    if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
        # Clean up expired code
        try:
            supabase.table('mfa_codes').delete().eq('code_id', code_id).execute()
        except Exception:
            pass
        
        return {
            "success": False,
            "error": "CODE_EXPIRED",
            "message": "Verification code has expired. Please request a new code."
        }
    
    # Check attempt limit
    if stored_data['attempts'] >= MAX_VERIFICATION_ATTEMPTS:
        # Lock out after max attempts
        try:
            supabase.table('mfa_codes').delete().eq('code_id', code_id).execute()
        except Exception:
            pass
        
        return {
            "success": False,
            "error": "MAX_ATTEMPTS_EXCEEDED",
            "message": "Too many failed attempts. Please request a new code."
        }
    
    # Increment attempt counter
    new_attempts = stored_data['attempts'] + 1
    try:
        supabase.table('mfa_codes')\
            .update({'attempts': new_attempts})\
            .eq('code_id', code_id)\
            .execute()
    except Exception as e:
        print(f"⚠️  Warning: Failed to update attempts: {e}")
    
    # Verify the code
    is_valid = verify_code(user_code, stored_data['code_hash'])
    
    if is_valid:
        # Success! Clean up the code
        try:
            supabase.table('mfa_codes').delete().eq('code_id', code_id).execute()
        except Exception:
            pass
        
        print(f"✅ Code verified successfully for {email} (purpose: {purpose})")
        return {
            "success": True,
            "message": "Verification successful",
            "user_id": stored_data.get('user_id')
        }
    else:
        remaining_attempts = MAX_VERIFICATION_ATTEMPTS - new_attempts
        print(f"❌ Invalid code for {email}. Attempts remaining: {remaining_attempts}")
        return {
            "success": False,
            "error": "INVALID_CODE",
            "message": f"Invalid verification code. {remaining_attempts} attempts remaining."
        }


def cleanup_expired_codes():
    """Remove expired verification codes from storage."""
    now = datetime.utcnow()
    expired_emails = [
        email for email, data in verification_store.items()
        if now > data["expires_at"]
    ]
    
    for email in expired_emails:
        del verification_store[email]
    
    if expired_emails:
        print(f"🧹 Cleaned up {len(expired_emails)} expired codes")
