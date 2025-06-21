import os
from datetime import timedelta

# --- JWT Settings ---
# IMPORTANT: Generate a strong, random secret key for production and load from environment.
# Example for generation: openssl rand -hex 32
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7") # Placeholder
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")) # Default 30 minutes
ACCESS_TOKEN_EXPIRE_DELTA = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

# --- Password Hashing ---
# (auth_utils.py handles this, but settings like salt rounds could be here if needed)

# --- Database ---
# (database.py handles this by reading individual DB_ env vars)

# --- Default User Roles ---
DEFAULT_CUSTOMER_ROLE_NAME = "customer" # Role name for newly registered users

if __name__ == '__main__':
    print("JWT Configuration:")
    print(f"  Secret Key (first 5 chars): {JWT_SECRET_KEY[:5]}...")
    print(f"  Algorithm: {JWT_ALGORITHM}")
    print(f"  Token Expire Minutes: {ACCESS_TOKEN_EXPIRE_MINUTES}")
    print(f"  Default Customer Role: {DEFAULT_CUSTOMER_ROLE_NAME}")

```
