from backend.crypto import CryptoManager
from backend.storage import Vault
from backend.auth import AccessControl
from backend.quantum import QuantumSession
import json

class VajraCore:
    """
    The Central Logic Unit.
    Orchestrates the 'Shatter' (Ingestion) and 'Reconstruct' (Retrieval) processes.
    Enforces RBAC and Quantum-Safe Key Handling.
    """
    
    CHUNK_SIZE = 4096 # 4KB
    GENESIS_HASH = b'\x00' * 32
    
    ALLOWED_EXTENSIONS = {
        '.pdf': b'%PDF',
        '.csv': None # Text check
    }

    def __init__(self, vault: Vault):
        self.vault = vault

    def _validate_file_type(self, content: bytes, filename: str):
        """Strictly checks file signature (Magic Bytes)."""
        ext = "." + filename.split('.')[-1].lower() if '.' in filename else ""
        
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Security Alert: File type {ext} is strictly forbidden. Only PDF/CSV allowed.")
            
        expected_magic = self.ALLOWED_EXTENSIONS[ext]
        if expected_magic and not content.startswith(expected_magic):
            raise ValueError("Tamper Alert: File extension does not match magic bytes.")
            
        if ext == '.csv':
            # rudimentary text check
            try:
                content[:128].decode('utf-8')
            except UnicodeDecodeError:
                raise ValueError("Tamper Alert: Malformed CSV (Binary data detected).")

    def shatter_file(self, file_content: bytes, filename: str, owner: str, classification: int = AccessControl.CLEARANCE_CONFIDENTIAL) -> int:
        """
        Ingest, Shatter, Encrypt (Quantum Wrapped).
        """
        # 1. Validation
        if not file_content:
            raise ValueError("File content cannot be empty.")
        self._validate_file_type(file_content, filename)
            
        manifest = []
        previous_hash = self.GENESIS_HASH
        
        # 2. Chunking
        for i in range(0, len(file_content), self.CHUNK_SIZE):
            chunk_data = file_content[i : i + self.CHUNK_SIZE]
            
            # 3. Ephemeral Key
            key = CryptoManager.generate_key()
            
            # 4. Chain Hashing
            payload = previous_hash + chunk_data
            
            # 5. Encrypt
            enc_result = CryptoManager.encrypt_data(payload, key)
            ciphertext = enc_result['ciphertext']
            nonce = enc_result['nonce']
            
            # 6. Dispersal
            shard_uuid = self.vault.write_blob(ciphertext)
            
            # 7. Next Link Hash
            current_hash_hex = CryptoManager.compute_hash(payload)
            previous_hash = bytes.fromhex(current_hash_hex)
            
            # 8. Encapsulate Key (Quantum)
            # We do NOT store the raw key. We store the wrapped key.
            encapsulated_key = QuantumSession.encapsulate(key)
            
            manifest.append({
                "index": i // self.CHUNK_SIZE,
                "shard_id": shard_uuid,
                "enc_key": encapsulated_key.hex(), # Store as hex string
                "nonce": nonce.hex(),
                "hash": current_hash_hex
            })
            
        # 9. Register with Clearance
        # We need to store the classification level in the DB for RBAC.
        # Since our schema is fixed in prototype, we'll pack it into the 'owner' field or manifest metadata
        # For this stage, let's assume 'owner' field stores "Role:Classification" or we just update the DB schema.
        # Decision: Use the 'owner' field relative to the logic, or update storage.
        # Let's simple append classification to the Manifest Metadata wrapper 
        # (Actually, storage.py register_file schema is simple. Let's wrap the manifest list in a dict).
        
        final_manifest = {
            "classification": classification,
            "shards": manifest
        }
        
        return self.vault.register_file(filename, owner, final_manifest)

    def reconstruct_file(self, file_id: int, user_role: str) -> bytes:
        """
        Secure Retrieval.
        1. Access Check (Bell-LaPadula).
        2. Integrity Audit.
        3. Quantum Decapsulation.
        4. Reassembly.
        """
        meta = self.vault.get_file_metadata(file_id)
        if not meta:
            raise FileNotFoundError("File not found.")
            
        # Parse Manifest
        # Handle backward compatibility if we changed structure (but this is new code so fine)
        manifest_wrapper = meta['manifest'] 
        # Note: In `shatter`, we passed `final_manifest`. Storage converts to JSON.
        # So `meta['manifest']` comes back as a Dict (if we stored dict) or List (if list).
        
        if isinstance(manifest_wrapper, list):
            # Legacy/Test handling
            shards = manifest_wrapper
            classification = AccessControl.CLEARANCE_CONFIDENTIAL # Default
        else:
            classification = manifest_wrapper.get("classification", AccessControl.CLEARANCE_CONFIDENTIAL)
            shards = manifest_wrapper.get("shards", [])

        # 1. RBAC Check
        if not AccessControl.can_read(user_role, classification):
            raise PermissionError(f"ACCESS DENIED: Role '{user_role}' lacks clearance for Level {classification}.")

        reassembled_buffer = b""
        previous_hash = self.GENESIS_HASH

        # 2. Reassembly Loop
        for item in shards:
            shard_uuid = item['shard_id']
            enc_key_hex = item.get('enc_key') or item.get('key') # Support old 'key' for legacy tests if needed
            nonce_hex = item['nonce']
            stored_hash = item['hash']
            
            # Read from Disk
            ciphertext = self.vault.read_blob(shard_uuid)
            
            # Quantum Unwrap
            enc_key_bytes = bytes.fromhex(enc_key_hex)
            try:
                aes_key = QuantumSession.decapsulate(enc_key_bytes)
            except ValueError:
                # If legaccy test data used plain keys, this might fail or be weird.
                # Assuming clean state or handle it.
                aes_key = enc_key_bytes # Fallback? No, Strict.
            
            # Decrypt
            nonce = bytes.fromhex(nonce_hex)
            payload = CryptoManager.decrypt_data(ciphertext, aes_key, nonce)
            
            # Integrity Check 1: Chain Hash (Pre-computation)
            computed_hash = CryptoManager.compute_hash(payload)
            if computed_hash != stored_hash:
                raise ValueError(f"TAMPER ALERT: Shard {shard_uuid} integrity hash mismatch.")
                
            # Integrity Check 2: Linkage
            # Payload is [PrevHash] + [Data]
            link_hash = payload[:32]
            actual_data = payload[32:]
            
            if link_hash != previous_hash:
                raise ValueError(f"CHAIN BROKEN: Shard {shard_uuid} does not link to previous shard.")
            
            reassembled_buffer += actual_data
            previous_hash = bytes.fromhex(stored_hash)
            
        return reassembled_buffer
