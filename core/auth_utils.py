from passlib.context import CryptContext

# Setup CryptContext for password hashing. bcrypt is a good default.
# Deprecated schemes can be listed if migrating old hashes, e.g., deprecated="md5_crypt"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashes a plain text password using the configured context (bcrypt)."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a stored hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Handle potential errors during verification, e.g., if the hash format is unknown
        # or not compatible (though verify should handle this gracefully by returning False)
        # For security, generally just return False on any error.
        return False

if __name__ == '__main__':
    # Example Usage & Test
    plain_pw = "S3cr3tP@sswOrd!"

    print(f"Plain password: {plain_pw}")

    hashed_pw = hash_password(plain_pw)
    print(f"Hashed password (bcrypt): {hashed_pw}")
    print(f"Length of hash: {len(hashed_pw)}") # bcrypt hashes are typically 60 chars

    is_correct = verify_password(plain_pw, hashed_pw)
    print(f"Verification with correct password ('{plain_pw}'): {is_correct}")
    assert is_correct

    is_incorrect = verify_password("WrongPassword!", hashed_pw)
    print(f"Verification with incorrect password ('WrongPassword!'): {is_incorrect}")
    assert not is_incorrect

    # Test with a potentially malformed hash (should not raise error, just return False)
    malformed_hash = "this_is_not_a_bcrypt_hash"
    is_malformed_verified = verify_password(plain_pw, malformed_hash)
    print(f"Verification with malformed hash: {is_malformed_verified}")
    assert not is_malformed_verified

    print("\nauth_utils.py self-test completed.")

```
