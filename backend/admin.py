from backend.core import VajraCore
from backend.storage import Vault
from backend.crypto import CryptoManager
from backend.quantum import QuantumSession
import sqlite3

class AdminTools:
    """
    Administrative capabilities for the Flight Director.
    Includes Auditing and Emergency Data Destruction.
    """

    @staticmethod
    def integrity_audit(core: VajraCore) -> dict:
        """
        Scans ALL files in the registry and verifies their physical integrity.
        Returns a report of healthy vs corrupted files.
        """
        report = {
            "total_files": 0,
            "corrupted_files": [],
            "healthy_files": []
        }
        
        # 1. Fetch all file IDs
        conn = sqlite3.connect(core.vault.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT file_id, filename FROM file_registry")
        files = cursor.fetchall()
        conn.close()
        
        report["total_files"] = len(files)
        
        # 2. Verify each file
        for file_id, filename in files:
            try:
                # We reuse the core reconstruction logic to verify integrity.
                # Since we are Admin (System), we bypass RBAC for the *Audit* process 
                # (or rather, the System checks itself).
                # However, core.reconstruct_file requires a role.
                # We can simulate the 'SATELLITE' system role which has top clearance.
                
                # Note: reconstruct_file returns the bytes, which might be heavy.
                # Optimally we would just verify hashes, but reusing the logic ensures consistency.
                core.reconstruct_file(file_id, "SATELLITE")
                report["healthy_files"].append(filename)
                
            except Exception as e:
                report["corrupted_files"].append({
                    "filename": filename,
                    "error": str(e)
                })
                
        return report

    @staticmethod
    def kill_switch(vault: Vault):
        """
        EMERGENCY: Purge the Central Registry.
        Without the registry (Manifests + Keys + Nonces), the shards on disk
        are mathematically indistinguishable from random noise.
        """
        conn = sqlite3.connect(vault.db_path)
        cursor = conn.cursor()
        
        # DROP the table.
        cursor.execute("DROP TABLE IF EXISTS file_registry")
        conn.commit()
        conn.close()
        
        # In a real system, we would also securely wipe (overwrite) the RAM keys.
