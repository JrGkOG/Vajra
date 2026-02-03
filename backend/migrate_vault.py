"""
Migrate old vault keys to use new user UUIDs.
This fixes the issue where old vault keys can't be accessed with new authentication.
"""

import requests

BASE_URL = "http://localhost:8000"

# First, login to get admin token
email = "karthik.maniam008@gmail.com"
password = "admin123"

print("=" * 60)
print("VAULT KEYS MIGRATION")
print("=" * 60)

# Step 1: Login
print("\n1. Logging in as admin...")
login1 = requests.post(
    f"{BASE_URL}/auth/login/password",
    json={"email": email, "password": password}
)

if login1.status_code != 200:
    print(f"❌ Login failed: {login1.text}")
    exit(1)

print("   Password verified, MFA code sent")
mfa_code = input("\n   Enter MFA code from email: ").strip()

# Step 2: Verify MFA
login2 = requests.post(
    f"{BASE_URL}/auth/login/mfa",
    json={"email": email, "mfa_code": mfa_code}
)

if login2.status_code != 200:
    print(f"❌ MFA failed: {login2.text}")
    exit(1)

data = login2.json()
token = data['access_token']
print(f"✅ Logged in as {data['user']['email']}")

# Step 3: Run migration
print("\n2. Running vault migration...")
response = requests.post(
    f"{BASE_URL}/admin/vault/migrate",
    headers={"Authorization": f"Bearer {token}"}
)

if response.status_code == 200:
    result = response.json()
    print(f"\n✅ Migration completed!")
    print(f"   Total vault entries: {result['total_vaults']}")
    print(f"   Migrated: {result['migrated']}")
    print(f"   Skipped (already migrated): {result['skipped']}")
    
    if result['mappings']:
        print(f"\n   User Mappings:")
        for old_id, new_id in result['mappings'].items():
            print(f"   {old_id} -> {new_id[:20]}...")
else:
    print(f"❌ Migration failed: {response.text}")
    exit(1)

# Step 4: Verify - list vault keys
print("\n3. Verifying - listing vault keys...")
list_response = requests.get(
    f"{BASE_URL}/vault/list",
    headers={"Authorization": f"Bearer {token}"}
)

if list_response.status_code == 200:
    vault_data = list_response.json()
    print(f"✅ Found {len(vault_data['keys'])} vault keys")
    for key in vault_data['keys'][:5]:  # Show first 5
        print(f"   - {key['key_label']}")
else:
    print(f"⚠️  List failed: {list_response.text}")

print("\n" + "=" * 60)
print("MIGRATION COMPLETE!")
print("Now refresh your browser and your vault keys should appear.")
print("=" * 60)
