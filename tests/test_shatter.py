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
    # Create valid dummy content larger than 4KB
    # 4096 * 2 + 100 bytes = 3 chunks
    content = b"a" * 4096 + b"b" * 4096 + b"c" * 100
    
    file_id = temp_core.shatter_file(content, "test.txt", "Admin")
    
    # Check DB
    meta = temp_core.vault.get_file_metadata(file_id)
    manifest = meta['manifest']
    
    assert len(manifest) == 3
    assert manifest[0]['index'] == 0
    assert manifest[1]['index'] == 1
    assert manifest[2]['index'] == 2

    # Check physical existence
    for item in manifest:
        shard_uuid = item['shard_id']
        assert (tmp_path / "shards" / f"{shard_uuid}.bin").exists()

def test_chain_hashing_logic(temp_core):
    """
    Verify that the hash of shard N is indeed computed from (Hash(N-1) + Data).
    This confirms the 'Blockchain' linking.
    """
    content = b"1" * 4096 + b"2" * 4096
    file_id = temp_core.shatter_file(content, "chain.txt", "Admin")
    
    meta = temp_core.vault.get_file_metadata(file_id)
    manifest = meta['manifest']
    
    # Re-compute to verify
    
    # Chunk 0
    # Payload = Genesis (32x00) + Data (4096x'1')
    genesis = b'\x00' * 32
    chunk0_payload = genesis + (b"1" * 4096)
    expected_hash0 = CryptoManager.compute_hash(chunk0_payload)
    
    assert manifest[0]['hash'] == expected_hash0
    
    # Chunk 1
    # Payload = Hash0 (bytes) + Data (4096x'2')
    hash0_bytes = bytes.fromhex(manifest[0]['hash'])
    chunk1_payload = hash0_bytes + (b"2" * 4096)
    expected_hash1 = CryptoManager.compute_hash(chunk1_payload)
    
    assert manifest[1]['hash'] == expected_hash1

def test_unique_keys(temp_core):
    """Ensure every shard gets a unique key."""
    content = b"x" * 10000
    file_id = temp_core.shatter_file(content, "keys.txt", "Admin")
    manifest = temp_core.vault.get_file_metadata(file_id)['manifest']
    
    keys = [item['key'] for item in manifest]
    assert len(keys) == len(set(keys)) # All must be unique
