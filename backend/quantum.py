import os

class QuantumSession:
    """
    Simulates a Post-Quantum Key Encapsulation Mechanism (KEM).
    Target Algorithm: Kyber-768.
    
    In this prototype, we simulate the 'Encapsulation' by wrapping the 
    AES key with a 'Quantum' marker.
    """
    
    PREFIX = b"KYBER768_ENCAPSULATED::"

    @staticmethod
    def encapsulate(aes_key: bytes) -> bytes:
        """
        Simulates: (shared_secret, ciphertext) = PQ_KEM_Encaps(pub_key).
        We 'hide' the AES key inside a simulated ciphertext container.
        """
        # In real Kyber, we wouldn't just wrap the key. 
        # We would generate a shared secret and use that to encrypt the payload.
        # But for this 'File Sharing' logic, we are treating the AES key AS the secret 
        # that needs to be transported safely to the storage.
        
        return QuantumSession.PREFIX + aes_key

    @staticmethod
    def decapsulate(encapsulated_key: bytes) -> bytes:
        """
        Simulates: shared_secret = PQ_KEM_Decaps(ciphertext, priv_key).
        Unwraps the 'Quantum' container to retrieve the usable AES key.
        """
        if not encapsulated_key.startswith(QuantumSession.PREFIX):
            raise ValueError("Invalid Quantum Ciphertext: Header mismatch")
        
        return encapsulated_key.replace(QuantumSession.PREFIX, b"")
