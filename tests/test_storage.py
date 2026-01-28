import pytest
import os
from backend.storage import Vault
import sqlite3
import json

@pytest.fixture
def temp_vault(tmp_path):
    """Fixture to provide a Vault instance with a temporary directory."""
    db_path = tmp_path / "registry.db"
    storage_root = tmp_path / "shards"
    return Vault(str(db_path), str(storage_root))

def test_write_blob_creates_uuid_file(temp_vault, tmp_path):
    """Test that writing a blob creates a file with a UUID name."""
    data = b"some encrypted bytes"
    shard_uuid = temp_vault.write_blob(data)
    
    # Check that the return value looks like a UUID
    assert len(shard_uuid) == 36 # basic length check
    
    # Check that file exists on disk
    expected_path = tmp_path / "shards" / f"{shard_uuid}.bin"
    assert expected_path.exists()
    assert expected_path.read_bytes() == data

def test_read_blob(temp_vault):
    """Test reading back a blob."""
    data = b"secret datastream"
    uuid = temp_vault.write_blob(data)
    
    read_back = temp_vault.read_blob(uuid)
    assert read_back == data

def test_metadata_persistence(temp_vault):
    """Test that file metadata is correctly stored in SQLite."""
    manifest = [
        {"shard_id": "uuid-1", "hash": "abc"},
        {"shard_id": "uuid-2", "hash": "def"}
    ]
    
    file_id = temp_vault.register_file("mission_top_secret.pdf", "Director", manifest)
    assert file_id is not None
    assert isinstance(file_id, int)
    
    # Retrieve
    meta = temp_vault.get_file_metadata(file_id)
    assert meta["filename"] == "mission_top_secret.pdf"
    assert meta["owner"] == "Director"
    assert meta["manifest"] == manifest
    assert len(meta["manifest"]) == 2

def test_missing_blob_raises_error(temp_vault):
    """Test error handling for missing files."""
    with pytest.raises(FileNotFoundError):
        temp_vault.read_blob("non-existent-uuid")
