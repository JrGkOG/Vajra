import pytest
import os
from cryptography.exceptions import InvalidTag
from backend.crypto import CryptoManager

def test_generate_key():
    """Test that keys are 32 bytes and random (unique)."""
    key1 = CryptoManager.generate_key()
    key2 = CryptoManager.generate_key()
    assert len(key1) == 32
    assert len(key2) == 32
    assert key1 != key2

def test_encrypt_decrypt_flow():
    """Test the full encrypt -> decrypt lifecycle."""
    data = b"This is a secret message specific to Vajra."
    key = CryptoManager.generate_key()
    
    # Encrypt
    result = CryptoManager.encrypt_data(data, key)
    ciphertext = result['ciphertext']
    nonce = result['nonce']
    
    assert ciphertext != data
    assert len(nonce) == 12
    
    # Decrypt
    decrypted = CryptoManager.decrypt_data(ciphertext, key, nonce)
    assert decrypted == data

def test_integrity_check():
    """Test that tampering with ciphertext causes decryption failure (Zero-Trust)."""
    data = b"Sensitive Telemetry Data"
    key = CryptoManager.generate_key()
    result = CryptoManager.encrypt_data(data, key)
    
    ciphertext = bytearray(result['ciphertext'])
    nonce = result['nonce']
    
    # Tamper with the last byte
    ciphertext[-1] ^= 0xFF
    
    with pytest.raises(InvalidTag):
        CryptoManager.decrypt_data(bytes(ciphertext), key, nonce)

def test_wrong_key_fails():
    """Test that the wrong key cannot decrypt the data."""
    data = b"Top Secret"
    key1 = CryptoManager.generate_key()
    key2 = CryptoManager.generate_key()
    
    result = CryptoManager.encrypt_data(data, key1)
    
    with pytest.raises(InvalidTag):
        CryptoManager.decrypt_data(result['ciphertext'], key2, result['nonce'])

def test_hashing():
    """Test SHA-256 hashing consistency."""
    data = b"Shard Link Block 1"
    hash1 = CryptoManager.compute_hash(data)
    hash2 = CryptoManager.compute_hash(data)
    
    assert len(hash1) == 64 # SHA-256 is 64 hex chars
    assert hash1 == hash2
    
    data_modified = b"Shard Link Block 2"
    hash3 = CryptoManager.compute_hash(data_modified)
    assert hash1 != hash3
