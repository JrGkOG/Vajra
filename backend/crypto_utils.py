"""
Cryptographic utilities for chunk encryption and hashing.
Uses AES-256-GCM for encryption and SHA-256 for integrity hashing.
"""

import base64
import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_encryption_key() -> bytes:
    """
    Generate a random 256-bit (32-byte) encryption key for AES-256.
    
    Returns:
        bytes: 32-byte random key
    """
    return os.urandom(32)


def generate_iv() -> bytes:
    """
    Generate a random 96-bit (12-byte) initialization vector for AES-GCM.
    GCM mode requires a 12-byte nonce for optimal security.
    
    Returns:
        bytes: 12-byte random IV/nonce
    """
    return os.urandom(12)


def encrypt_chunk(data: bytes, key: bytes, iv: bytes) -> tuple[str, str]:
    """
    Encrypt a chunk of data using AES-256-GCM, hash the encrypted result,
    and encode to Base64 for safe transport/storage.
    
    Args:
        data: Raw chunk data to encrypt
        key: 32-byte AES-256 encryption key
        iv: 12-byte initialization vector (nonce)
    
    Returns:
        tuple: (base64_encoded_encrypted_data, sha256_hash_of_encrypted_data)
    
    Raises:
        ValueError: If key or IV lengths are incorrect
    """
    if len(key) != 32:
        raise ValueError("Encryption key must be 32 bytes for AES-256")
    if len(iv) != 12:
        raise ValueError("IV must be 12 bytes for AES-GCM")
    
    # Initialize AES-GCM cipher
    aesgcm = AESGCM(key)
    
    # Encrypt the data
    # AES-GCM produces ciphertext + authentication tag
    encrypted_data = aesgcm.encrypt(iv, data, None)
    
    # Calculate SHA-256 hash of the encrypted data (for integrity verification)
    chunk_hash = hashlib.sha256(encrypted_data).hexdigest()
    
    # Base64 encode the encrypted data for safe transport/storage
    b64_data = base64.b64encode(encrypted_data).decode('utf-8')
    
    return b64_data, chunk_hash


def decrypt_chunk(b64_encrypted_data: str, key: bytes, iv: bytes) -> bytes:
    """
    Decrypt a Base64-encoded encrypted chunk back to original data.
    This is not required for upload but useful for testing/download.
    
    Args:
        b64_encrypted_data: Base64-encoded encrypted chunk
        key: 32-byte AES-256 decryption key
        iv: 12-byte initialization vector used during encryption
    
    Returns:
        bytes: Decrypted original data
    
    Raises:
        ValueError: If key or IV lengths are incorrect
        cryptography.exceptions.InvalidTag: If authentication fails
    """
    if len(key) != 32:
        raise ValueError("Decryption key must be 32 bytes for AES-256")
    if len(iv) != 12:
        raise ValueError("IV must be 12 bytes for AES-GCM")
    
    # Decode from Base64
    encrypted_data = base64.b64decode(b64_encrypted_data)
    
    # Initialize AES-GCM cipher
    aesgcm = AESGCM(key)
    
    # Decrypt the data
    decrypted_data = aesgcm.decrypt(iv, encrypted_data, None)
    
    return decrypted_data
