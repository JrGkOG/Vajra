"""
Test script for downloading and verifying file reassembly.
Tests the secure download endpoint with MFA verification.
"""

import requests
import json
import base64
import os
import hashlib

BACKEND_URL = "http://localhost:8000"

# Test configuration
# These should be from your previous upload
FILE_ID = "1cc28085-a4ba-463f-9344-4582f425c95f"  # Replace with actual file_id from upload
ENCRYPTION_KEY = "8ce13706bd856e93a1abaface636e1c88a5dd676212800dff6d07ffd028fb8e2"  # Replace with actual key
ORIGINAL_FILE = "/Users/meenakshiganesan/Karthik/vajra/Proof_of_concept.pdf"  # Path to original file for comparison

def create_mock_jwt(with_mfa=True, role="commander"):
    """Create a mock JWT token with role support."""
    payload = {
        "sub": "test-user-123",
        "user_id": "test-user-123",
        "email": "test@example.com",
        "aal": "aal2" if with_mfa else "aal1",  # aal2 = MFA enabled
        "role": role  # commander, specialist, viewer
    }
    
    header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
    payload_encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"{header}.{payload_encoded}.mock-signature"

def calculate_file_hash(filepath):
    """Calculate SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

print("🔐 Secure Download Test")
print("=" * 60)

# Test 1: Download without MFA (should fail)
print("\n📋 Test 1: Download without MFA (should be rejected)")
print("-" * 60)
token_without_mfa = create_mock_jwt(with_mfa=False)
response = requests.get(
    f"{BACKEND_URL}/download/{FILE_ID}",
    params={"key": ENCRYPTION_KEY},
    headers={"Authorization": f"Bearer {token_without_mfa}"}
)

if response.status_code == 403 and "MFA_REQUIRED" in response.text:
    print("✅ PASS: MFA check working correctly")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
else:
    print("❌ FAIL: MFA check not working")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")

# Test 3: Viewer trying to access Top Secret (Should Fail)
print("\n📋 Test 3: RBAC Check - Viewer vs Top Secret (Should FAIL)")
print("-" * 60)
token_viewer = create_mock_jwt(with_mfa=True, role="viewer")
# Assuming file was uploaded as Top Secret
response = requests.get(
    f"{BACKEND_URL}/download/{FILE_ID}",
    params={"key": ENCRYPTION_KEY},
    headers={"Authorization": f"Bearer {token_viewer}"}
)

if response.status_code == 403:
    print("✅ PASS: Viewer denied access to Top Secret file")
    print(f"   Response: {response.text}")
else:
    print("⚠️  WARN: Viewer verification check (Make sure file is uploaded as top_secret)")
    print(f"   Status: {response.status_code}")


# Test 4: Commander accessing Top Secret (Should Succeed)
print("\n📋 Test 4: RBAC Check - Commander vs Top Secret (Should SUCCEED)")
print("-" * 60)
token_commander = create_mock_jwt(with_mfa=True, role="commander")

try:
    response = requests.get(
        f"{BACKEND_URL}/download/{FILE_ID}",
        params={"key": ENCRYPTION_KEY},
        headers={"Authorization": f"Bearer {token_commander}"},
        stream=True
    )
    
    if response.status_code == 200:
        # Save downloaded file
        download_path = "downloads/downloaded_file.pdf"
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"✅ Download successful!")
        print(f"   Status: {response.status_code}")

        print(f"   Saved to: {download_path}")
        print(f"   Size: {os.path.getsize(download_path):,} bytes")
        
        # Verify file integrity
        if os.path.exists(ORIGINAL_FILE):
            print(f"\n🔍 Verifying file integrity...")
            original_hash = calculate_file_hash(ORIGINAL_FILE)
            downloaded_hash = calculate_file_hash(download_path)
            
            print(f"   Original hash:   {original_hash}")
            print(f"   Downloaded hash: {downloaded_hash}")
            
            if original_hash == downloaded_hash:
                print(f"\n🎉 SUCCESS: Files match perfectly!")
                print(f"   The file was correctly encrypted, uploaded, downloaded, and decrypted.")
            else:
                print(f"\n❌ ERROR: Files do not match!")
                print(f"   Original size:   {os.path.getsize(ORIGINAL_FILE):,} bytes")
                print(f"   Downloaded size: {os.path.getsize(download_path):,} bytes")
        else:
            print(f"\n⚠️  Original file not found for comparison: {ORIGINAL_FILE}")
            print(f"   You can manually verify the downloaded file at: {download_path}")
    
    else:
        print(f"❌ Download failed!")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")

except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("Test complete!")
