"""
Digital signature utilities for file integrity verification.
Uses Ed25519 for fast, secure asymmetric signatures.
"""

import base64
import json
from typing import Tuple, Dict
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidSignature
import os


def generate_ed25519_keypair() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    """
    Generate Ed25519 key pair for digital signatures.
    
    Returns:
        Tuple of (private_key, public_key)
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def serialize_public_key(public_key: ed25519.Ed25519PublicKey) -> str:
    """
    Serialize public key to base64 string for storage.
    
    Args:
        public_key: Ed25519 public key
    
    Returns:
        Base64-encoded PEM string
    """
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return base64.b64encode(public_pem).decode('utf-8')


def serialize_private_key(private_key: ed25519.Ed25519PrivateKey) -> bytes:
    """
    Serialize private key to PEM format (unencrypted).
    Will be encrypted separately before storage.
    
    Args:
        private_key: Ed25519 private key
    
    Returns:
        PEM-encoded private key bytes
    """
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return private_pem


def deserialize_public_key(public_key_b64: str) -> ed25519.Ed25519PublicKey:
    """
    Deserialize public key from base64 string.
    
    Args:
        public_key_b64: Base64-encoded PEM string
    
    Returns:
        Ed25519 public key
    """
    public_pem = base64.b64decode(public_key_b64)
    public_key = serialization.load_pem_public_key(public_pem)
    return public_key


def deserialize_private_key(private_pem: bytes) -> ed25519.Ed25519PrivateKey:
    """
    Deserialize private key from PEM bytes.
    
    Args:
        private_pem: PEM-encoded private key
    
    Returns:
        Ed25519 private key
    """
    private_key = serialization.load_pem_private_key(
        private_pem,
        password=None
    )
    return private_key


def encrypt_private_key_with_password(private_pem: bytes, password: str) -> str:
    """
    Encrypt private key using user's vault password.
    Uses PBKDF2 + AES-256-GCM.
    
    Args:
        private_pem: PEM-encoded private key
        password: User's vault password
    
    Returns:
        Base64-encoded encrypted data (salt:nonce:ciphertext)
    """
    # Generate random salt for PBKDF2
    salt = os.urandom(16)
    
    # Derive encryption key from password
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    key = kdf.derive(password.encode('utf-8'))
    
    # Encrypt with AES-GCM
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, private_pem, None)
    
    # Combine salt:nonce:ciphertext
    encrypted_data = salt + nonce + ciphertext
    
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_private_key_with_password(encrypted_b64: str, password: str) -> bytes:
    """
    Decrypt private key using user's vault password.
    
    Args:
        encrypted_b64: Base64-encoded encrypted data
        password: User's vault password
    
    Returns:
        PEM-encoded private key bytes
    
    Raises:
        ValueError: If decryption fails (wrong password)
    """
    try:
        # Decode from base64
        encrypted_data = base64.b64decode(encrypted_b64)
        
        # Extract salt, nonce, ciphertext
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:28]
        ciphertext = encrypted_data[28:]
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = kdf.derive(password.encode('utf-8'))
        
        # Decrypt
        aesgcm = AESGCM(key)
        private_pem = aesgcm.decrypt(nonce, ciphertext, None)
        
        return private_pem
    
    except Exception as e:
        raise ValueError(f"Failed to decrypt private key: {str(e)}")


def sign_data(data: bytes, private_key: ed25519.Ed25519PrivateKey) -> str:
    """
    Sign arbitrary data with Ed25519 private key.
    
    Args:
        data: Data to sign
        private_key: Ed25519 private key
    
    Returns:
        Base64-encoded signature (64 bytes)
    """
    signature = private_key.sign(data)
    return base64.b64encode(signature).decode('utf-8')


def verify_signature(data: bytes, signature_b64: str, 
                     public_key: ed25519.Ed25519PublicKey) -> bool:
    """
    Verify Ed25519 signature.
    
    Args:
        data: Original data that was signed
        signature_b64: Base64-encoded signature
        public_key: Ed25519 public key
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        signature = base64.b64decode(signature_b64)
        public_key.verify(signature, data)
        return True
    except InvalidSignature:
        return False
    except Exception as e:
        print(f"⚠️ Signature verification error: {e}")
        return False


def sign_chunk_hash(chunk_hash_hex: str, private_key: ed25519.Ed25519PrivateKey) -> str:
    """
    Sign a chunk hash (SHA-256 hex string).
    
    Args:
        chunk_hash_hex: Hex-encoded SHA-256 hash
        private_key: Ed25519 private key
    
    Returns:
        Base64-encoded signature
    """
    chunk_hash_bytes = bytes.fromhex(chunk_hash_hex)
    return sign_data(chunk_hash_bytes, private_key)


def verify_chunk_signature(chunk_hash_hex: str, signature_b64: str,
                           public_key: ed25519.Ed25519PublicKey) -> bool:
    """
    Verify a chunk hash signature.
    
    Args:
        chunk_hash_hex: Hex-encoded SHA-256 hash
        signature_b64: Base64-encoded signature
        public_key: Ed25519 public key
    
    Returns:
        True if signature is valid, False otherwise
    """
    chunk_hash_bytes = bytes.fromhex(chunk_hash_hex)
    return verify_signature(chunk_hash_bytes, signature_b64, public_key)


def sign_file_manifest(manifest: Dict, private_key: ed25519.Ed25519PrivateKey) -> str:
    """
    Sign file manifest (metadata) to prevent tampering.
    
    Args:
        manifest: Dict containing file_id, filename, chunk_hashes, etc.
        private_key: Ed25519 private key
    
    Returns:
        Base64-encoded signature
    """
    # Create canonical JSON representation (sorted keys for consistency)
    manifest_json = json.dumps(manifest, sort_keys=True)
    return sign_data(manifest_json.encode('utf-8'), private_key)


def verify_file_manifest_signature(manifest: Dict, signature_b64: str,
                                   public_key: ed25519.Ed25519PublicKey) -> bool:
    """
    Verify file manifest signature.
    
    Args:
        manifest: Dict containing file metadata
        signature_b64: Base64-encoded signature
        public_key: Ed25519 public key
    
    Returns:
        True if signature is valid, False otherwise
    """
    manifest_json = json.dumps(manifest, sort_keys=True)
    return verify_signature(manifest_json.encode('utf-8'), signature_b64, public_key)


# Helper function for generating user keys during registration/first upload
def generate_user_signature_keys(vault_password: str) -> Tuple[str, str]:
    """
    Generate Ed25519 key pair for a user and encrypt private key.
    
    Args:
        vault_password: User's vault password (for encrypting private key)
    
    Returns:
        Tuple of (public_key_b64, encrypted_private_key_b64)
    """
    # Generate key pair
    private_key, public_key = generate_ed25519_keypair()
    
    # Serialize keys
    private_pem = serialize_private_key(private_key)
    public_key_b64 = serialize_public_key(public_key)
    
    # Encrypt private key with password
    encrypted_private_b64 = encrypt_private_key_with_password(private_pem, vault_password)
    
    return public_key_b64, encrypted_private_b64


def load_user_private_key(encrypted_private_b64: str, vault_password: str) -> ed25519.Ed25519PrivateKey:
    """
    Load and decrypt user's private signing key.
    
    Args:
        encrypted_private_b64: Encrypted private key from database
        vault_password: User's vault password
    
    Returns:
        Ed25519 private key
    
    Raises:
        ValueError: If decryption fails (wrong password)
    """
    # Decrypt private key
    private_pem = decrypt_private_key_with_password(encrypted_private_b64, vault_password)
    
    # Deserialize to key object
    private_key = deserialize_private_key(private_pem)
    
    return private_key
