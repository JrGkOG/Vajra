"""
Personal Vault Service
Handles password-based encryption and decryption of encryption keys.
Uses PBKDF2 for key derivation and AES-256-GCM for encryption.
"""

import os
import base64
from typing import Tuple
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit key from password using PBKDF2-HMAC-SHA256.
    
    Args:
        password: User's vault password
        salt: Random salt (16 bytes)
    
    Returns:
        32-byte derived key
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits
        salt=salt,
        iterations=100000,  # NIST recommendation
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))


def encrypt_key_for_vault(hex_key: str, password: str) -> dict:
    """
    Encrypt a hex encryption key using password-derived encryption.
    
    Args:
        hex_key: The encryption key to store (hex string)
        password: User's vault password
    
    Returns:
        dict with 'encrypted_hex' (base64) and 'salt' (base64)
    """
    # Generate random salt
    salt = os.urandom(16)
    
    # Derive encryption key from password
    derived_key = derive_key_from_password(password, salt)
    
    # Generate random IV for AES-GCM
    iv = os.urandom(12)
    
    # Encrypt the hex key
    aesgcm = AESGCM(derived_key)
    hex_bytes = hex_key.encode('utf-8')
    ciphertext = aesgcm.encrypt(iv, hex_bytes, None)
    
    # Combine IV + ciphertext
    encrypted_data = iv + ciphertext
    
    return {
        'encrypted_hex': base64.b64encode(encrypted_data).decode('utf-8'),
        'salt': base64.b64encode(salt).decode('utf-8')
    }


def decrypt_key_from_vault(encrypted_hex: str, salt: str, password: str) -> str:
    """
    Decrypt a hex encryption key using password-derived encryption.
    
    Args:
        encrypted_hex: Base64-encoded encrypted data (IV + ciphertext)
        salt: Base64-encoded salt
        password: User's vault password
    
    Returns:
        Decrypted hex key string
    
    Raises:
        Exception: If decryption fails (wrong password, tampered data)
    """
    try:
        # Decode from base64
        encrypted_data = base64.b64decode(encrypted_hex)
        salt_bytes = base64.b64decode(salt)
        
        # Extract IV and ciphertext
        iv = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        
        # Derive decryption key from password
        derived_key = derive_key_from_password(password, salt_bytes)
        
        # Decrypt
        aesgcm = AESGCM(derived_key)
        plaintext = aesgcm.decrypt(iv, ciphertext, None)
        
        return plaintext.decode('utf-8')
    
    except Exception as e:
        raise Exception(f"Failed to decrypt key: Invalid password or corrupted data")
