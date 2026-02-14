#!/usr/bin/env python3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

hash_from_db = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uB0YwBqXs.3e"

# Test common passwords
test_passwords = ["testpass", "secret", "password", "admin", "test", ""]

for pw in test_passwords:
    try:
        result = pwd_context.verify(pw, hash_from_db)
        print(f"Password '{pw}': {result}")
    except Exception as e:
        print(f"Password '{pw}': ERROR - {e}")

# Generate new hash for testpass
print("\n--- Generating new hash for 'testpass' ---")
new_hash = pwd_context.hash("testpass")
print(f"New hash: {new_hash}")
