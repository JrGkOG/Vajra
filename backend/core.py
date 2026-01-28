from backend.crypto import CryptoManager
from backend.storage import Vault

class VajraCore:
    """
    The Central Logic Unit.
    Orchestrates the 'Shatter' (Ingestion) and 'Reconstruct' (Retrieval) processes.
    """
    
    CHUNK_SIZE = 4096 # 4KB as per spec
    GENESIS_HASH = b'\x00' * 32 # 32 bytes of zeros

    def __init__(self, vault: Vault):
        self.vault = vault

    def shatter_file(self, file_content: bytes, filename: str, owner: str) -> int:
        """
        Ingests a file, shatters it into encrypted shards, and stores it in the Vault.
        
        Args:
            file_content: Raw bytes of the file.
            filename: Original filename.
            owner: User/Role owning the file.
            
        Returns:
            int: The file_id in the registry.
        """
        # 1. Validation (Basic size check)
        if not file_content:
            raise ValueError("File content cannot be empty.")
            
        manifest = []
        previous_hash = self.GENESIS_HASH
        
        # 2. Chunking Loop
        for i in range(0, len(file_content), self.CHUNK_SIZE):
            chunk_data = file_content[i : i + self.CHUNK_SIZE]
            
            # 3. Ephemeral Encryption Key (Unique per shard)
            key = CryptoManager.generate_key()
            
            # 4. Chain Hashing (The "Blockchain Logic")
            # We embed the hash of the PREVIOUS link into this link.
            # Payload = [Previous Hash (32 bytes)] + [Actual Data (4KB)]
            payload = previous_hash + chunk_data
            
            # 5. Encrypt
            enc_result = CryptoManager.encrypt_data(payload, key)
            ciphertext = enc_result['ciphertext']
            nonce = enc_result['nonce']
            
            # 6. Dispersal (Store to Disk)
            shard_uuid = self.vault.write_blob(ciphertext)
            
            # 7. Compute Hash for the NEXT link
            # We hash the *Payload* (PrevHash + Data), representing the state of the chain at this point.
            current_hash_hex = CryptoManager.compute_hash(payload)
            previous_hash = bytes.fromhex(current_hash_hex)
            
            # 8. Update Manifest
            # Store keys/nonces here. In a real system, 'key' would be wrapped by Kyber.
            manifest.append({
                "index": i // self.CHUNK_SIZE,
                "shard_id": shard_uuid,
                "key": key.hex(),
                "nonce": nonce.hex(),
                "hash": current_hash_hex
            })
            
        # 9. Commit to Database
        return self.vault.register_file(filename, owner, manifest)
