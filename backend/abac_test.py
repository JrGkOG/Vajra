"""
Test script for Attribute-Based Access Control (ABAC) policies.
Verifies User Status checks and Audit Logging triggers.
"""

import requests
import json
import base64
import os

BACKEND_URL = "http://localhost:8000"

# Configuration
# Use a valid file_id from previous uploads (e.g., a Top Secret file)
FILE_ID = "1cc28085-a4ba-463f-9344-4582f425c95f" 
# Use a valid key
ENCRYPTION_KEY = "8ce13706bd856e93a1abaface636e1c88a5dd676212800dff6d07ffd028fb8e2"

def create_mock_jwt(role="commander", status="active", with_mfa=True):
    """Create a mock JWT token with ABAC attributes."""
    payload = {
        "sub": "test-user-123",
        "user_id": "test-user-123",
        "email": "test@example.com",
        "aal": "aal2" if with_mfa else "aal1",
        "role": role,
        "status": status
    }
    
    header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
    payload_encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"{header}.{payload_encoded}.mock-signature"

print("🛡️ ABAC & Audit Log Test")
print("=" * 60)

# Test 1: Active Commander (Should Succeed)
print("\n📋 Test 1: Active Commander (Should Succeed)")
print("-" * 60)
token_active = create_mock_jwt(role="commander", status="active")

response = requests.get(
    f"{BACKEND_URL}/download/{FILE_ID}",
    params={"key": ENCRYPTION_KEY},
    headers={"Authorization": f"Bearer {token_active}"},
    stream=True
)

if response.status_code == 200:
    print("✅ PASS: Active Commander granted access")
else:
    print(f"❌ FAIL: Status: {response.status_code}")
    print(f"   Response: {response.text}")


# Test 2: Suspended Commander (Should Fail)
print("\n📋 Test 2: Suspended Commander (Should FAIL)")
print("-" * 60)
# Even though role is 'commander', status 'suspended' should block access
token_suspended = create_mock_jwt(role="commander", status="suspended")

response = requests.get(
    f"{BACKEND_URL}/download/{FILE_ID}",
    params={"key": ENCRYPTION_KEY},
    headers={"Authorization": f"Bearer {token_suspended}"}
)

if response.status_code == 403 and "suspended" in response.text:
    print("✅ PASS: Suspended Commander denied access")
    print(f"   Response: {response.text}")
else:
    print(f"❌ FAIL: Suspended user was NOT blocked correctly")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")

print("\n" + "=" * 60)
print("Test complete! Check Supabase 'audit_logs' table for entries.")
