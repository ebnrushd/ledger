import argparse
import os
import sys
from dotenv import load_dotenv

# Ensure core modules can be imported
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import get_db_connection # For services that use it
from core.user_service import create_user, UserAlreadyExistsError, UserServiceError, get_role_by_name
from core.auth_utils import hash_password # Though create_user should handle hashing

def main():
    load_dotenv() # Load .env for database connection if services need it

    parser = argparse.ArgumentParser(description="Create an initial admin user for the SQL Ledger application.")
    parser.add_argument("--username", required=True, help="Username for the admin (typically an email address).")
    parser.add_argument("--password", required=True, help="Password for the admin user.")
    parser.add_argument("--email", required=True, help="Contact email for the admin user.")

    args = parser.parse_args()

    conn = None
    try:
        conn = get_db_connection()
        conn.autocommit = False # Manage transaction

        admin_role = get_role_by_name("admin", conn)
        if not admin_role:
            print(f"Error: 'admin' role not found in the database. Please ensure roles are initialized (e.g., via initial_db.py).")
            if conn: conn.rollback() # Ensure rollback if role not found
            return

        print(f"Creating admin user '{args.username}' with email '{args.email}'...")

        # create_user handles password hashing internally
        user_id = create_user(
            username=args.username,
            password=args.password, # Pass raw password
            email=args.email,
            role_id=admin_role['role_id'],
            is_active=True, # Admins should be active by default
            conn=conn
        )

        conn.commit() # Commit if all successful
        print(f"Admin user '{args.username}' created successfully with User ID: {user_id}.")
        print("You can now use these credentials to log into the admin panel.")

    except UserAlreadyExistsError:
        print(f"Error: User with username '{args.username}' or email '{args.email}' already exists.")
        if conn: conn.rollback()
    except UserServiceError as use:
        print(f"User service error: {use}")
        if conn: conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn: conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
```
