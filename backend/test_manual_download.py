"""
Simple test to manually download and decrypt chunks.
"""

import asyncio
import base64
from storage_service import get_file_metadata, download_chunk_from_supabase
from crypto_utils import decrypt_chunk

FILE_ID = "1cc28085-a4ba-463f-9344-4582f425c95f"
ENCRYPTION_KEY_HEX = "8ce13706bd856e93a1abaface636e1c88a5dd676212800dff6d07ffd028fb8e2"

async def test_download():
    print("🔍 Testing Manual Download...")
    print("=" * 60)
    
    # Get metadata
    metadata = await get_file_metadata(FILE_ID)
    print(f"✅ Got metadata:")
    print(f"   Filename: {metadata['filename']}")
    print(f"   Total chunks: {metadata['total_chunks']}")
    print(f"   Owner: {metadata['owner_id']}")
    
    # Decode key and IV
    encryption_key = bytes.fromhex(ENCRYPTION_KEY_HEX)
    encryption_iv = base64.b64decode(metadata['encryption_iv'])
    
    print(f"\n🔐 Decryption info:")
    print(f"   Key length: {len(encryption_key)} bytes")
    print(f"   IV length: {len(encryption_iv)} bytes")
    
    # Download and decrypt chunks
    all_data = b""
    for chunk_index in range(metadata['total_chunks']):
        print(f"\n📦 Processing chunk {chunk_index}...")
        
        # Download
        storage_path = f"{FILE_ID}/chunk_{chunk_index}"
        b64_encrypted_chunk = await download_chunk_from_supabase("uploads", storage_path)
        print(f"   Downloaded: {len(b64_encrypted_chunk)} chars (Base64)")
        
        # Decrypt
        decrypted_chunk = decrypt_chunk(b64_encrypted_chunk, encryption_key, encryption_iv)
        print(f"   Decrypted: {len(decrypted_chunk)} bytes")
        
        all_data += decrypted_chunk
    
    print(f"\n📊 Total reassembled size: {len(all_data):,} bytes")
    
    # Save to file
    output_path = "downloads/manual_download.pdf"
    with open(output_path, 'wb') as f:
        f.write(all_data)
    
    print(f"✅ Saved to: {output_path}")
    
    # Compare with original
    import hashlib
    downloaded_hash = hashlib.sha256(all_data).hexdigest()
    print(f"\n🔍 SHA-256: {downloaded_hash}")
    
    # Compare with original file
    original_file = "/Users/meenakshiganesan/Karthik/vajra/Proof_of_concept.pdf"
    import os
    if os.path.exists(original_file):
        with open(original_file, 'rb') as f:
            original_data = f.read()
        original_hash = hashlib.sha256(original_data).hexdigest()
        
        print(f"\n📝 Comparison:")
        print(f"   Original hash:   {original_hash}")
        print(f"   Downloaded hash: {downloaded_hash}")
        
        if original_hash == downloaded_hash:
            print(f"\n🎉 SUCCESS! Files match perfectly!")
        else:
            print(f"\n❌ ERROR: Hashes don't match!")
            print(f"   Original size:   {len(original_data):,} bytes")
            print(f"   Downloaded size: {len(all_data):,} bytes")

if __name__ == "__main__":
    asyncio.run(test_download())
