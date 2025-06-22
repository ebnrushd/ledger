import sys
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from pydantic import ValidationError # For validating token data model

# Add project root to sys.path to allow importing 'api.config'
# This assumes 'core' and 'api' are sibling directories under the project root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from api.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_DELTA
    from api.models import TokenData # For type hinting and validation
except ImportError as e:
    print(f"Error importing from api.config or api.models in core/security.py: {e}")
    print("Ensure that the project root is in PYTHONPATH or adjust import paths.")
    # Fallback for direct execution or if PYTHONPATH isn't perfectly set for this structure
    # This indicates a potential issue with how modules are structured or called.
    # For robust solution, project should be runnable with PYTHONPATH covering the root.
    # For now, provide placeholder values if import fails to allow file creation.
    if 'JWT_SECRET_KEY' not in globals():
        JWT_SECRET_KEY = "fallback_secret_for_security_module"
        JWT_ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_DELTA = timedelta(minutes=30)
        print("Warning: Using fallback JWT settings in security.py due to import error.")
    if 'TokenData' not in globals():
        class TokenData: # type: ignore # Placeholder class
            username: Optional[str] = None


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token.

    Args:
        data (dict): Data to be encoded in the token (e.g., {"sub": username}).
        expires_delta (Optional[timedelta]): Custom expiration delta.
                                             Defaults to ACCESS_TOKEN_EXPIRE_DELTA from config.

    Returns:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + ACCESS_TOKEN_EXPIRE_DELTA

    to_encode.update({"exp": expire})
    # Standard claims: 'sub' (subject), 'exp' (expiration time), 'iat' (issued at), 'nbf' (not before)
    # We are primarily using 'sub' for username and 'exp'.
    # 'iat': datetime.utcnow() could be added if needed.

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str, credentials_exception: Exception) -> Optional[TokenData]:
    """
    Decodes and validates a JWT access token.

    Args:
        token (str): The JWT token to decode.
        credentials_exception (Exception): The exception to raise if token is invalid
                                          (e.g., HTTPException(status.HTTP_401_UNAUTHORIZED, ...)).

    Returns:
        Optional[TokenData]: The validated token data (payload as TokenData model) or None if validation fails
                             and an exception is not preferred directly from here.
                             Typically, this function should raise `credentials_exception` on failure.

    Raises:
        credentials_exception: If token is invalid, expired, or claims are malformed.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        username: Optional[str] = payload.get("sub")
        if username is None: # 'sub' claim is standard for subject (username)
            raise credentials_exception

        # Validate payload against TokenData model
        # This ensures that the data we expect in the token is present and valid.
        token_data = TokenData(username=username) # Add other fields if they are in TokenData & token
        return token_data

    except JWTError as e: # Covers expired signature, invalid signature, etc.
        print(f"JWTError during token decode: {e}")
        raise credentials_exception
    except ValidationError as e_val: # If payload doesn't match TokenData model
        print(f"TokenData ValidationError: {e_val}")
        raise credentials_exception # Or a different exception for malformed payload


if __name__ == '__main__':
    # Example Usage & Test
    print("--- Testing JWT Creation & Decoding ---")

    # Sample data for token
    user_data = {"sub": "testuser@example.com", "user_id": 123, "custom_claim": "some_value"}

    # Create a token
    access_token = create_access_token(data=user_data.copy()) # Pass a copy
    print(f"Generated Access Token: {access_token}")

    # Define a dummy credentials exception for testing decode
    class DummyCredentialsException(Exception):
        pass

    creds_exception_instance = DummyCredentialsException("Invalid token or credentials.")

    # Decode the token
    try:
        decoded_payload = decode_access_token(access_token, creds_exception_instance)
        if decoded_payload:
            print(f"Decoded Token Payload (as TokenData): username='{decoded_payload.username}'")
            assert decoded_payload.username == user_data["sub"]
        else:
            print("Token decoding returned None (should have raised or returned data).")
            assert False, "Decoding failed unexpectedly"
    except DummyCredentialsException as e:
        print(f"Error decoding token: {e}")
        assert False, f"Token decoding failed: {e}"

    print("\n--- Testing Expired Token ---")
    expired_token = create_access_token(data={"sub": "expireduser"}, expires_delta=timedelta(seconds=-10))
    try:
        decode_access_token(expired_token, creds_exception_instance)
        assert False, "Expired token was somehow validated."
    except JWTError: # This is caught inside decode_access_token which then raises creds_exception_instance
        print("Caught JWTError as expected internally (not directly here).") # Should not reach here if decode raises
    except DummyCredentialsException:
        print("Successfully failed to validate expired token (raised credentials_exception).")

    print("\n--- Testing Invalid Token (bad signature/content) ---")
    invalid_token = access_token[:-5] + "xxxxx" # Tamper with the token
    try:
        decode_access_token(invalid_token, creds_exception_instance)
        assert False, "Invalid token was somehow validated."
    except DummyCredentialsException:
        print("Successfully failed to validate invalid token.")

    print("\n--- Testing Token with missing 'sub' ---")
    token_no_sub = create_access_token(data={"user_id": 456}) # No 'sub'
    try:
        decode_access_token(token_no_sub, creds_exception_instance)
        assert False, "Token with no 'sub' was validated."
    except DummyCredentialsException:
        print("Successfully failed to validate token with missing 'sub'.")

    print("\nsecurity.py self-test completed.")

```
