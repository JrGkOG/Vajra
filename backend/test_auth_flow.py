"""
Test the 2-step MFA login flow with real database users.
"""

import requests
import time

BASE_URL = "http://localhost:8000"

# Test users
USERS = {
    "admin": {"email": "admin@vajra.mil", "password": "admin123"},
    "manager": {"email": "manager@vajra.mil", "password": "manager123"},
    "engineer": {"email": "engineer@vajra.mil", "password": "engineer123"},
    "staff": {"email": "staff@vajra.mil", "password": "staff123"},
}


def test_2step_login(email, password):
    """Test the complete 2-step login flow."""
    
    print("\n" + "=" * 70)
    print(f"🔐 TESTING 2-STEP MFA LOGIN FOR: {email}")
    print("=" * 70)
    
    # Step 1: Send email and password
    print("\n📝 Step 1: Sending email and password...")
    step1_response = requests.post(
        f"{BASE_URL}/auth/login/password",
        json={
            "email": email,
            "password": password
        }
    )
    
    if step1_response.status_code == 200:
        data = step1_response.json()
        print(f"✅ Password verified!")
        print(f"📧 MFA code sent to {data['email']}")
        print(f"⏰ Expires in {data['expires_in_minutes']} minutes")
        print(f"📌 {data['next_step']}")
    else:
        print(f"❌ Step 1 failed: {step1_response.text}")
        return None
    
    # Step 2: Ask user for MFA code
    print("\n" + "=" * 70)
    print("📬 CHECK YOUR EMAIL FOR THE 6-DIGIT CODE")
    print("=" * 70)
    
    mfa_code = input("\n🔢 Enter the 6-digit code from your email: ").strip()
    
    # Step 3: Verify MFA code
    print("\n🔐 Step 2: Verifying MFA code...")
    step2_response = requests.post(
        f"{BASE_URL}/auth/login/mfa",
        json={
            "email": email,
            "mfa_code": mfa_code
        }
    )
    
    if step2_response.status_code == 200:
        data = step2_response.json()
        user = data['user']
        permissions = user['permissions']
        
        print("\n✅ LOGIN SUCCESSFUL!")
        print(f"\n👤 User Information:")
        print(f"   Email: {user['email']}")
        print(f"   Username: {user['username']}")
        print(f"   Role: {user['role']}")
        print(f"   Status: {user['status']}")
        
        print(f"\n🔑 Permissions:")
        print(f"   Can Upload: {'✅' if permissions.get('can_upload') else '❌'}")
        print(f"   Can Download: {'✅' if permissions.get('can_download') else '❌'}")
        print(f"   Can Create Users: {'✅' if permissions.get('can_create_users') else '❌'}")
        print(f"   Can View All Logs: {'✅' if permissions.get('can_view_all_logs') else '❌'}")
        
        print(f"\n🎟️  JWT Token: {data['access_token'][:50]}...")
        
        return data['access_token']
    else:
        print(f"❌ Step 2 failed: {step2_response.text}")
        return None


def test_admin_view_logs(token):
    """Test admin viewing logs."""
    print("\n" + "=" * 70)
    print("📊 TESTING ADMIN LOG VIEWING")
    print("=" * 70)
    
    response = requests.get(
        f"{BASE_URL}/admin/logs",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 10}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Retrieved {data['count']} log entries")
        
        print("\n📜 Recent Activity:")
        for i, log in enumerate(data['logs'][:5], 1):
            print(f"\n{i}. {log['action']}")
            print(f"   User: {log.get('users', {}).get('email', 'N/A')}")
            print(f"   Time: {log['timestamp']}")
            if log.get('details'):
                print(f"   Details: {log['details']}")
    else:
        print(f"❌ Failed to view logs: {response.text}")


def test_admin_create_user(token):
    """Test admin creating a new user."""
    print("\n" + "=" * 70)
    print("👥 TESTING ADMIN USER CREATION")
    print("=" * 70)
    
    new_user = {
        "email": "testuser@vajra.mil",
        "username": "testuser",
        "password": "test123",
        "role": "engineer"
    }
    
    response = requests.post(
        f"{BASE_URL}/admin/users/create",
        headers={"Authorization": f"Bearer {token}"},
        json=new_user
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ User created successfully!")
        print(f"   Email: {data['user']['email']}")
        print(f"   Role: {data['user']['role']}")
        print(f"   Can Upload: {data['user']['can_upload']}")
        print(f"   Can Download: {data['user']['can_download']}")
    else:
        print(f"❌ Failed to create user: {response.text}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("🚀 VAJRA AUTHENTICATION SYSTEM TEST")
    print("=" * 70)
    
    # Test login with admin
    print("\n1️⃣  Testing login with ADMIN user...")
    admin_token = test_2step_login(
        USERS["admin"]["email"],
        USERS["admin"]["password"]
    )
    
    if admin_token:
        # Test admin privileges
        test_admin_view_logs(admin_token)
        # Uncomment to test user creation
        # test_admin_create_user(admin_token)
    
    print("\n" + "=" * 70)
    print("✅ TESTS COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    main()
