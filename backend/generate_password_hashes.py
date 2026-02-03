"""
Generate bcrypt password hashes for test users.
Run this to get the correct hashes for the SQL script.
"""

import bcrypt

users = {
    'admin': 'admin123',
    'manager': 'manager123',
    'engineer': 'engineer123',
    'staff': 'staff123'
}

print("=" * 60)
print("BCRYPT PASSWORD HASHES FOR TEST USERS")
print("=" * 60)

for username, password in users.items():
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    print(f"\n{username.upper()}:")
    print(f"  Password: {password}")
    print(f"  Hash: {hashed.decode('utf-8')}")

print("\n" + "=" * 60)
print("Copy these hashes to create_users_table.sql")
print("=" * 60)
