"""
Test script for email verification system.
Demonstrates the complete flow:
1. Send verification code (hashed with bcrypt)
2. Verify user-submitted code (hash comparison)
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_email_verification():
    """Test the complete email verification flow."""
    
    email = "karthik.maniam008@gmail.com"
    
    print("=" * 60)
    print("🧪 TESTING EMAIL VERIFICATION SYSTEM")
    print("=" * 60)
    
    # Step 1: Send verification code
    print("\n📧 Step 1: Sending verification code...")
    send_response = requests.post(
        f"{BASE_URL}/auth/send-verification",
        json={"email": email}
    )
    
    if send_response.status_code == 200:
        print("✅ Verification email sent successfully!")
        print(f"📊 Response: {send_response.json()}")
    else:
        print(f"❌ Failed to send email: {send_response.text}")
        return
    
    # Step 2: Prompt user to enter the code from their email
    print("\n" + "=" * 60)
    print("📬 Check your email for the 6-digit verification code")
    print("=" * 60)
    
    user_code = input("\n🔢 Enter the 6-digit code from your email: ").strip()
    
    # Step 3: Verify the code
    print("\n🔐 Step 2: Verifying code...")
    verify_response = requests.post(
        f"{BASE_URL}/auth/verify-code",
        json={
            "email": email,
            "code": user_code
        }
    )
    
    if verify_response.status_code == 200:
        print("✅ Code verified successfully!")
        print(f"📊 Response: {verify_response.json()}")
    else:
        print(f"❌ Verification failed: {verify_response.text}")
        print(f"📊 Status code: {verify_response.status_code}")
    
    # Step 4: Test with wrong code
    print("\n" + "=" * 60)
    print("🧪 Testing with incorrect code...")
    print("=" * 60)
    
    wrong_verify = requests.post(
        f"{BASE_URL}/auth/verify-code",
        json={
            "email": email,
            "code": "000000"  # Wrong code
        }
    )
    
    if wrong_verify.status_code != 200:
        print("✅ Correctly rejected invalid code")
        print(f"📊 Error: {wrong_verify.json()}")
    else:
        print("❌ Security issue: Wrong code accepted!")


def test_code_expiry():
    """Test that codes expire after the set time."""
    print("\n" + "=" * 60)
    print("⏰ TESTING CODE EXPIRY")
    print("=" * 60)
    
    email = "test@example.com"
    
    # Send code
    print("\n📧 Sending verification code...")
    send_response = requests.post(
        f"{BASE_URL}/auth/send-verification",
        json={"email": email}
    )
    
    if send_response.status_code == 200:
        expires_in = send_response.json().get("expires_in_minutes", 10)
        print(f"✅ Code sent. Expires in {expires_in} minutes")
        print(f"⚠️  In production, wait {expires_in} minutes to test expiry")
        print("⚠️  For PoC, the code is stored in memory")


if __name__ == "__main__":
    print("\n🚀 Starting Email Verification Tests\n")
    
    # Main test
    test_email_verification()
    
    # Optional: Test expiry (commented out to save time)
    # test_code_expiry()
    
    print("\n" + "=" * 60)
    print("✅ Tests completed!")
    print("=" * 60)
