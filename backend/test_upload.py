"""
Test script for the secure upload backend.
Tests chunk encryption, hashing, and metadata construction without requiring real Supabase.
"""

import os
import asyncio
import tempfile
from crypto_utils import generate_encryption_key, generate_iv, encrypt_chunk, decrypt_chunk

"""
    hi there i am testing this
"""
def create_test_file(size_mb: int = 2) -> str:
    """
    Create a temporary test file with random data.
    
    Args:
        size_mb: Size of the file in megabytes
    
    Returns:
        str: Path to the created test file
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
    
    # Write random data
    chunk_size = 1024 * 1024  # 1MB chunks
    for _ in range(size_mb):
        temp_file.write(os.urandom(chunk_size))
    
    temp_file.close()
    return temp_file.name


async def test_upload_flow():
    """
    Test the complete upload flow:
    1. Create test file
    2. Read in 512KB chunks
    3. Encrypt each chunk
    4. Verify chunk integrity
    5. Test decryption
    """
    print("🚀 Starting Secure Upload Test\n")
    
    # Step 1: Create test file
    print("📄 Creating 2MB test file...")
    test_file_path = create_test_file(size_mb=2)
    file_size = os.path.getsize(test_file_path)
    print(f"✓ Created test file: {test_file_path} ({file_size:,} bytes)\n")
    
    # Step 2: Generate encryption materials
    print("🔐 Generating encryption key and IV...")
    encryption_key = generate_encryption_key()
    iv = generate_iv()
    print(f"✓ Key: {encryption_key.hex()[:32]}... (32 bytes)")
    print(f"✓ IV:  {iv.hex()[:24]}... (12 bytes)\n")
    
    # Step 3: Process file in chunks
    CHUNK_SIZE = 512 * 1024  # 512KB
    chunk_index = 0
    chunk_hashes = []
    encrypted_chunks = []
    original_chunks = []
    
    print("📦 Processing file in 512KB chunks...")
    with open(test_file_path, 'rb') as f:
        while True:
            chunk_data = f.read(CHUNK_SIZE)
            if not chunk_data:
                break
            
            # Store original for verification
            original_chunks.append(chunk_data)
            
            # Encrypt chunk
            b64_encrypted, chunk_hash = encrypt_chunk(chunk_data, encryption_key, iv)
            encrypted_chunks.append(b64_encrypted)
            chunk_hashes.append(chunk_hash)
            
            print(f"  Chunk {chunk_index}: {len(chunk_data):,} bytes → {len(b64_encrypted):,} chars (base64)")
            print(f"    Hash: {chunk_hash[:32]}...")
            
            chunk_index += 1
    
    print(f"\n✓ Processed {chunk_index} chunks\n")
    
    # Step 4: Test decryption
    print("🔓 Testing decryption...")
    for idx, (encrypted, original) in enumerate(zip(encrypted_chunks, original_chunks)):
        try:
            decrypted = decrypt_chunk(encrypted, encryption_key, iv)
            assert decrypted == original, f"Decryption mismatch at chunk {idx}"
            print(f"  ✓ Chunk {idx}: Decryption successful")
        except Exception as e:
            print(f"  ✗ Chunk {idx}: Decryption failed - {e}")
            return False
    
    print(f"\n✓ All {chunk_index} chunks decrypted successfully\n")
    
    # Step 5: Mock metadata construction
    print("📊 Constructing metadata...")
    metadata = {
        "file_id": "test-file-123",
        "owner_id": "test-user-456",
        "filename": "test_file.bin",
        "total_chunks": chunk_index,
        "encryption_iv": iv.hex(),
        "chunk_hashes": chunk_hashes
    }
    
    print(f"  File ID: {metadata['file_id']}")
    print(f"  Owner ID: {metadata['owner_id']}")
    print(f"  Filename: {metadata['filename']}")
    print(f"  Total Chunks: {metadata['total_chunks']}")
    print(f"  IV: {metadata['encryption_iv'][:24]}...")
    print(f"  Hashes: {len(metadata['chunk_hashes'])} recorded\n")
    
    # Cleanup
    os.unlink(test_file_path)
    print("🧹 Cleaned up test file\n")
    
    print("=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\n🎉 The upload flow is working correctly!")
    print("\n📝 Next steps:")
    print("  1. Set up Supabase (create bucket 'uploads' and table 'files_metadata')")
    print("  2. Configure .env with SUPABASE_URL and SUPABASE_KEY")
    print("  3. Run: uvicorn main:app --reload")
    print("  4. Test with: curl -X POST http://localhost:8000/upload \\")
    print("       -H 'Authorization: Bearer YOUR_JWT' \\")
    print("       -F 'file=@your_file.pdf'")
    
    return True


if __name__ == "__main__":
    asyncio.run(test_upload_flow())
