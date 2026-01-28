import sqlite3
import os
import uuid
import json
from pathlib import Path

class Vault:
    """
    The Zero-Knowledge Store.
    Separates metadata (SQLite) from physical data (Encrypted Blobs on Disk).
    """

    def __init__(self, db_path: str, storage_root: str):
        self.db_path = db_path
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Creates the File Registry table if not exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # We store the manifest as a JSON string for simplicity in this prototype.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_registry (
                file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                owner TEXT NOT NULL,
                manifest TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def write_blob(self, encrypted_data: bytes) -> str:
        """
        Writes a raw encrypted shard to the disk with a random UUID name.
        Returns the UUID string.
        """
        shard_uuid = str(uuid.uuid4())
        file_path = self.storage_root / f"{shard_uuid}.bin"
        
        with open(file_path, "wb") as f:
            f.write(encrypted_data)
            
        return shard_uuid

    def read_blob(self, shard_uuid: str) -> bytes:
        """
        Reads a raw encrypted shard from disk given its UUID.
        """
        file_path = self.storage_root / f"{shard_uuid}.bin"
        if not file_path.exists():
            raise FileNotFoundError(f"Shard {shard_uuid} not found on disk.")
            
        with open(file_path, "rb") as f:
            return f.read()

    def register_file(self, filename: str, owner: str, manifest: list) -> int:
        """
        Registers a new file in the metadata/SQL layer.
        'manifest' is a list of dicts describing the shards.
        Returns the new file_id.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        manifest_json = json.dumps(manifest)
        
        cursor.execute("""
            INSERT INTO file_registry (filename, owner, manifest)
            VALUES (?, ?, ?)
        """, (filename, owner, manifest_json))
        
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return file_id

    def get_file_metadata(self, file_id: int) -> dict:
        """
        Retrieves file metadata and manifest by ID.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor() # Keep default row factory for now, can change to Row later
        
        cursor.execute("SELECT filename, owner, manifest, created_at FROM file_registry WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return {
            "file_id": file_id,
            "filename": row[0],
            "owner": row[1],
            "manifest": json.loads(row[2]),
            "created_at": row[3]
        }
