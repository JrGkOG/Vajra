import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class CryptoManager:
    """
    Handles low-level cryptographic operations for the Vajra system.
    Uses AES-256-GCM for encryption (providing confidentiality and integrity)
    and SHA-256 for hashing (shard chaining).
    """

    @staticmethod
    def generate_key() -> bytes:
        """
        Generates a random 256-bit (32-byte) AES key.
        This key is unique per shard in the Vajra architecture.
        """
        return AESGCM.generate_key(bit_length=256)

    @staticmethod
    def encrypt_data(data: bytes, key: bytes) -> dict:
        """
        Encrypts data using AES-256-GCM.
        
        Args:
            data: The plain bytes to encrypt (e.g., a 4KB file shard).
            key: A 32-byte AES key.
            
        Returns:
            dict: {
                'ciphertext': bytes (includes the auth tag appended),
                'nonce': bytes (required for decryption)
            }
        """
        aesgcm = AESGCM(key)
        # NIST recommends 12 bytes for GCM nonce
        nonce = os.urandom(12)
        # encrypt() returns ciphertext + auth_tag
        ciphertext = aesgcm.encrypt(nonce, data, associated_data=None)
        
        return {
            "ciphertext": ciphertext,
            "nonce": nonce
        }

    @staticmethod
    def decrypt_data(encrypted_data: bytes, key: bytes, nonce: bytes) -> bytes:
        """
        Decrypts data using AES-256-GCM.
        
        Args:
            encrypted_data: Ciphertext bytes (including appended auth tag).
            key: The 32-byte AES key used for encryption.
            nonce: The 12-byte nonce used for encryption.
            
        Returns:
            bytes: The original plaintext data.
            
        Raises:
            cryptography.exceptions.InvalidTag: If the data or key is incorrect/tampered.
        """
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, encrypted_data, associated_data=None)

    @staticmethod
    def compute_hash(data: bytes) -> str:
        """
        Computes the SHA-256 hash of the given data.
        Used for the 'Blockchain Logic' to link shards together.
        """
        return hashlib.sha256(data).hexdigest()
