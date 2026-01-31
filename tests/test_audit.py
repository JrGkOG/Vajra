import pytest
import sqlite3
import os
from backend.core import VajraCore
from backend.storage import Vault
from backend.admin import AdminTools

@pytest.fixture
def admin_setup(tmp_path):
    vault = Vault(str(tmp_path / "reg.db"), str(tmp_path / "shards"))
    core = VajraCore(vault)
    return core, vault

def test_audit_healthy(admin_setup):
    """Test full healthy audit."""
    core, vault = admin_setup
    
    # Create 2 healthy files
    core.shatter_file(b"%PDF-1", "file1.pdf", "Director")
    core.shatter_file(b"%PDF-2", "file2.pdf", "Director")
    
    report = AdminTools.integrity_audit(core)
    
    assert report["total_files"] == 2
    assert len(report["healthy_files"]) == 2
    assert len(report["corrupted_files"]) == 0

def test_audit_detects_corruption(admin_setup):
    """Test audit finds missing shards."""
    core, vault = admin_setup
    
    # Create file
    file_id = core.shatter_file(b"%PDF-Test", "file.pdf", "Director")
    
    # Sabotage: Delete a shard from disk
    meta = vault.get_file_metadata(file_id)
    shard_id = meta['manifest']['shards'][0]['shard_id']
    shard_path = vault.storage_root / f"{shard_id}.bin"
    os.remove(shard_path)
    
    report = AdminTools.integrity_audit(core)
    
    assert len(report["corrupted_files"]) == 1
    assert report["corrupted_files"][0]['filename'] == "file.pdf"
    assert "Shard" in report["corrupted_files"][0]['error']
    assert "not found" in report["corrupted_files"][0]['error']

def test_kill_switch_nukes_data(admin_setup):
    """Test that kill switch destroys access."""
    core, vault = admin_setup
    
    # 1. Create Data
    file_id = core.shatter_file(b"%PDF-Secret", "secret.pdf", "Director")
    
    # 2. Verify Access Works
    assert core.reconstruct_file(file_id, "DIRECTOR") == b"%PDF-Secret"
    
    # 3. ACTIVATE KILL SWITCH
    AdminTools.kill_switch(vault)
    
    # 4. Verify Access Fails
    # The get_file_metadata query should fail or return None, 
    # but likely it will throw OperationalError because table is gone.
    
    with pytest.raises(sqlite3.OperationalError, match="no such table"):
        core.reconstruct_file(file_id, "DIRECTOR")
