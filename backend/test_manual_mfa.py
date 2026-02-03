"""
Test the manual MFA send endpoint.
"""

import requests

BASE_URL = "http://localhost:8000"

# Test with admin user
email = "karthik.maniam008@gmail.com"
password = "admin123"

print("=" * 60)
print("🧪 TESTING MANUAL MFA SEND")
print("=" * 60)

print(f"\n📧 Sending MFA code to: {email}")

response = requests.post(
    f"{BASE_URL}/auth/send-mfa",
    json={
        "email": email,
        "password": password
    }
)

print(f"\n📊 Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"✅ Success!")
    print(f"📬 {data['message']}")
    print(f"⏰ Code expires in {data['expires_in_minutes']} minutes")
    print(f"\n✉️  CHECK YOUR EMAIL: {email}")
else:
    print(f"❌ Failed!")
    print(f"Error: {response.text}")

print("\n" + "=" * 60)
