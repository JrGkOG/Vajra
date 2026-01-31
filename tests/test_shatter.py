import pytest
from backend.core import VajraCore
from backend.storage import Vault
from backend.crypto import CryptoManager

@pytest.fixture
def temp_core(tmp_path):
    vault = Vault(str(tmp_path / "reg.db"), str(tmp_path / "shards"))
    return VajraCore(vault)

def test_shatter_creates_shards(temp_core, tmp_path):
    """Test that a file is split into multiple shards."""
    # Create valid dummy PDF larger than 4KB
    # Header + 4096 + 4096 + 100
    content = b"%PDF-1.4" + b"a" * 8200
    
    file_id = temp_core.shatter_file(content, "test.pdf", "Admin")
    
    # Check DB
    meta = temp_core.vault.get_file_metadata(file_id)
    manifest_wrapper = meta['manifest']
    shards = manifest_wrapper['shards']
    
    # 8200 + 8 (header) = 8208 bytes. 
    # 8208 / 4096 = 2 chunks (0..4096, 4096..8192) + remainder (8192..8208).
    # Total 3 chunks.
    assert len(shards) == 3
    assert shards[0]['index'] == 0
    assert shards[1]['index'] == 1
    assert shards[2]['index'] == 2

    # Check physical existence
    for item in shards:
        shard_uuid = item['shard_id']
        assert (tmp_path / "shards" / f"{shard_uuid}.bin").exists()

def test_chain_hashing_logic(temp_core):
    """
    Verify that the hash of shard N is indeed computed from (Hash(N-1) + Data).
    """
    # 2 chunks
    content = b"%PDF-1.4" + b"1" * 8000
    file_id = temp_core.shatter_file(content, "chain.pdf", "Admin")
    
    meta = temp_core.vault.get_file_metadata(file_id)
    shards = meta['manifest']['shards']
    
    # Chunk 0
    # Payload = Genesis (32x00) + Data (first 4KB of content)
    genesis = b'\x00' * 32
    chunk0_data = content[0:4096]
    chunk0_payload = genesis + chunk0_data
    expected_hash0 = CryptoManager.compute_hash(chunk0_payload)
    
    assert shards[0]['hash'] == expected_hash0
    
    # Chunk 1
    # Payload = Hash0 (bytes) + Data (next 4KB)
    hash0_bytes = bytes.fromhex(shards[0]['hash'])
    chunk1_data = content[4096:8192]
    chunk1_payload = hash0_bytes + chunk1_data
    expected_hash1 = CryptoManager.compute_hash(chunk1_payload)
    
    assert shards[1]['hash'] == expected_hash1

def test_unique_keys(temp_core):
    """Ensure every shard gets a unique key."""
    content = b"%PDF" + b"x" * 10000
    file_id = temp_core.shatter_file(content, "keys.pdf", "Admin")
    shards = temp_core.vault.get_file_metadata(file_id)['manifest']['shards']
    
    keys = [item['enc_key'] for item in shards]
    assert len(keys) == len(set(keys)) # All must be unique
