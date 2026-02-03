"""
Debug script to check user_id mismatch between JWT token and vault entries.
"""

import requests
import base64
import json

BASE_URL = "http://localhost:8000"

# Test login
email = "karthik.maniam008@gmail.com"
password = "admin123"

print("=" * 60)
print("DEBUGGING VAULT USER ID MISMATCH")
print("=" * 60)

# Get token (use old login for now to test)
print("\n1. Login with old endpoint...")
response = requests.post(
    f"{BASE_URL}/login",
    json={"username": "commander", "password": "test"}
)

if response.status_code == 200:
    data = response.json()
    token = data['access_token']
    
    # Decode JWT to see user_id
    parts = token.split('.')
    payload = json.loads(base64.b64decode(parts[1] + '=='))
    
    print(f"\n2. JWT Payload:")
    print(f"   user_id: {payload.get('user_id')}")
    print(f"   email: {payload.get('email')}")
    
    # Try to list vault keys
    print(f"\n3. Fetching vault keys...")
    vault_response = requests.get(
        f"{BASE_URL}/vault/list",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if vault_response.status_code == 200:
        vault_data = vault_response.json()
        print(f"   Found {len(vault_data['keys'])} keys")
        for key in vault_data['keys']:
            print(f"   - {key['key_label']} (vault_id: {key['vault_id'][:20]}...)")
    else:
        print(f"   ❌ Failed: {vault_response.text}")
else:
    print(f"❌ Login failed: {response.text}")

print("\n" + "=" * 60)
print("\nSOLUTION: The vault keys are tied to old user IDs.")
print("You need to either:")
print("1. Upload new files with the new authentication system")
print("2. Or update existing vault entries to use new user UUIDs")
print("=" * 60)
