import sys
import os
import hashlib # For password hashing placeholder - DO NOT USE MD5/SHA for real passwords
from datetime import datetime

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import execute_query, get_db_connection
# For PII and audit, could use audit_service if logging user creations/updates
# from core.audit_service import log_event

class UserServiceError(Exception):
    """Base exception for User service errors."""
    pass

class UserNotFoundError(UserServiceError):
    """Raised when a user is not found."""
    pass

class UserAlreadyExistsError(UserServiceError):
    """Raised when trying to create a user that already exists (e.g. username/email)."""
    pass

def _hash_password_placeholder(password: str) -> str:
    """
    Placeholder for password hashing.
    IMPORTANT: Replace with a strong hashing algorithm like bcrypt, scrypt, or Argon2.
    DO NOT USE MD5 or SHA variants directly for passwords in production.
    """
    print("WARNING: Using placeholder password hashing. Replace with bcrypt/scrypt/argon2 for production.")
    return hashlib.sha256(password.encode()).hexdigest() # Example, NOT FOR PRODUCTION

# --- Import new auth utils ---
from .auth_utils import hash_password, verify_password


def create_user(username, password, email, role_id, customer_id=None, is_active=True, conn=None):
    """
    Creates a new user in the 'users' table.
    """
    hashed_password = hash_password(password) # Use the new hashing function
    query_check_exists = "SELECT user_id FROM users WHERE username = %s OR email = %s;"
    query_insert = """
        INSERT INTO users (username, password_hash, email, role_id, customer_id, is_active, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        RETURNING user_id;
    """
    params_insert = (username, hashed_password, email, role_id, customer_id, is_active)

    _conn_managed_internally = False
    if not conn:
        conn = get_db_connection()
        _conn_managed_internally = True

    try:
        with conn.cursor() as cur:
            cur.execute(query_check_exists, (username, email))
            existing_user = cur.fetchone()
            if existing_user:
                # Check which one conflicted for a better message, if desired
                cur.execute("SELECT username FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    raise UserAlreadyExistsError(f"User with username '{username}' already exists.")
                cur.execute("SELECT email FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    raise UserAlreadyExistsError(f"User with email '{email}' already exists.")
                # Fallback if logic is complex (e.g. race condition)
                raise UserAlreadyExistsError(f"User with username '{username}' or email '{email}' already exists (conflict detected).")

            cur.execute(query_insert, params_insert)
            user_id = cur.fetchone()[0]
            conn.commit() # Commit if successful

            # Audit logging should be called from the router, passing the admin_user_id
            # Example: log_event('USER_CREATED', 'users', user_id,
            #                    {'username': username, 'role_id': role_id, 'email': email},
            #                    admin_user_id_performing_action, conn=conn) # Pass conn if part of larger tx

            return user_id
    except UserAlreadyExistsError:
        if conn and not conn.closed and not conn.autocommit: conn.rollback()
        raise
    except Exception as e:
        if conn and not conn.closed and not conn.autocommit: conn.rollback()
        raise UserServiceError(f"Error creating user '{username}': {e}")
    finally:
        if _conn_managed_internally and conn and not conn.closed:
            conn.close()

def get_user_by_id(user_id, conn=None):
    """Retrieves a user by their user_id, joining with roles table for role_name."""
    query = """
        SELECT u.user_id, u.username, u.email, u.role_id, r.role_name,
               u.customer_id, u.is_active, u.created_at, u.last_login, u.password_hash
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        WHERE u.user_id = %s;
    """
    # This uses execute_query, which manages its own connection if conn is None
    # If conn is provided, it should ideally use that connection.
    # For now, execute_query doesn't accept an existing conn.
    # Let's use direct cursor execution if conn is provided.

    _conn_managed_internally = False
    if not conn:
        conn = get_db_connection()
        _conn_managed_internally = True

    try:
        with conn.cursor() as cur:
            cur.execute(query, (user_id,))
            record = cur.fetchone()

        if not record:
            raise UserNotFoundError(f"User with ID {user_id} not found.")

        return {
            "user_id": record[0], "username": record[1], "email": record[2],
            "role_id": record[3], "role_name": record[4], "customer_id": record[5],
            "is_active": record[6], "created_at": record[7], "last_login": record[8],
            "password_hash": record[9] # Be careful about exposing this, even if hashed
        }
    except UserNotFoundError:
        raise
    except Exception as e:
        raise UserServiceError(f"Error fetching user ID {user_id}: {e}")
    finally:
        if _conn_managed_internally and conn:
            conn.close()


def list_users(page=1, per_page=20, search_query=None, conn=None):
    """Lists users with pagination and optional search, joining with roles."""
    offset = (page - 1) * per_page
    base_query = """
        SELECT u.user_id, u.username, u.email, u.role_id, r.role_name,
               u.customer_id, u.is_active, u.created_at, u.last_login
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
    """
    count_query = "SELECT COUNT(*) FROM users u JOIN roles r ON u.role_id = r.role_id"

    conditions = []
    params = []

    if search_query:
        search_term = f"%{search_query}%"
        conditions.append("(u.username ILIKE %s OR u.email ILIKE %s OR r.role_name ILIKE %s)")
        params.extend([search_term, search_term, search_term])

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
        count_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY u.user_id LIMIT %s OFFSET %s;"
    params.extend([per_page, offset])

    _conn_managed_internally = False
    if not conn:
        conn = get_db_connection()
        _conn_managed_internally = True

    users_list = []
    total_users = 0
    try:
        with conn.cursor() as cur:
            cur.execute(count_query, tuple(params[:-2])) # Params for count query (without limit/offset)
            total_users = cur.fetchone()[0]

            cur.execute(base_query, tuple(params))
            records = cur.fetchall()
            for r in records:
                users_list.append({
                    "user_id": r[0], "username": r[1], "email": r[2],
                    "role_id": r[3], "role_name": r[4], "customer_id": r[5],
                    "is_active": r[6], "created_at": r[7], "last_login": r[8]
                })
        return {"users": users_list, "total_users": total_users, "page": page, "per_page": per_page}
    except Exception as e:
        raise UserServiceError(f"Error listing users: {e}")
    finally:
        if _conn_managed_internally and conn:
            conn.close()


def update_user(user_id, update_data: dict, admin_user_id=None, conn=None):
    """
    Updates user information. `update_data` is a dict of fields to update.
    Password update should be handled separately or require current password if not admin.
    For password changes, a new hash should be generated.
    `admin_user_id` is for audit logging purposes.
    """
    # Fetch current user details for audit logging comparison and for selective updates
    try:
        current_user_data = get_user_by_id(user_id, conn=conn) # Use existing conn if available
    except UserNotFoundError:
        raise # User must exist to be updated

    fields_to_update = []
    params = []
    changed_details_for_audit = {"old_values": {}, "new_values": {}}

    for key, new_value in update_data.items():
        # Skip if new value is same as current, unless it's password
        if key != "password" and key in current_user_data and current_user_data[key] == new_value:
            continue

        if key == "password" and new_value:
            fields_to_update.append("password_hash = %s")
            params.append(hash_password(new_value)) # Use new hashing function
            # Do not log password hashes or new password itself in audit
            changed_details_for_audit["old_values"]["password_changed_at"] = current_user_data.get("password_hash_updated_at", "never") # Fictional field
            changed_details_for_audit["new_values"]["password_changed_at"] = datetime.now().isoformat()
        elif key == "username":
            fields_to_update.append("username = %s")
            params.append(new_value)
            changed_details_for_audit["old_values"]["username"] = current_user_data["username"]
            changed_details_for_audit["new_values"]["username"] = new_value
        elif key == "email":
            fields_to_update.append("email = %s")
            params.append(new_value)
            changed_details_for_audit["old_values"]["email"] = current_user_data["email"]
            changed_details_for_audit["new_values"]["email"] = new_value
        elif key == "role_id":
            fields_to_update.append("role_id = %s")
            params.append(new_value)
            changed_details_for_audit["old_values"]["role_id"] = current_user_data["role_id"]
            changed_details_for_audit["new_values"]["role_id"] = new_value
        elif key == "customer_id":
            fields_to_update.append("customer_id = %s")
            params.append(new_value if new_value is not None else None) # Ensure None is passed for NULL
            changed_details_for_audit["old_values"]["customer_id"] = current_user_data["customer_id"]
            changed_details_for_audit["new_values"]["customer_id"] = new_value
        elif key == "is_active":
            fields_to_update.append("is_active = %s")
            params.append(new_value)
            changed_details_for_audit["old_values"]["is_active"] = current_user_data["is_active"]
            changed_details_for_audit["new_values"]["is_active"] = new_value

    if not fields_to_update:
        return False # No actual changes to update

    query = f"UPDATE users SET {', '.join(fields_to_update)} WHERE user_id = %s RETURNING user_id;"
    params.append(user_id)

    _conn_managed_internally = False
    if not conn:
        conn = get_db_connection()
        _conn_managed_internally = True

    try:
        # Check for potential username/email conflicts if they are being changed
        if "username" in update_data and update_data["username"] != current_user_data["username"] or \
           "email" in update_data and update_data["email"] != current_user_data["email"]:

            conflict_check_parts = []
            conflict_params = []
            if "username" in update_data and update_data["username"] != current_user_data["username"]:
                conflict_check_parts.append("username = %s")
                conflict_params.append(update_data["username"])
            if "email" in update_data and update_data["email"] != current_user_data["email"]:
                conflict_check_parts.append("email = %s")
                conflict_params.append(update_data["email"])

            if conflict_check_parts: # Only run if there's actually something to check for conflict
                conflict_query = f"SELECT user_id, username, email FROM users WHERE ({' OR '.join(conflict_check_parts)}) AND user_id != %s;"
                conflict_params.append(user_id)

                with conn.cursor() as cur_check:
                    cur_check.execute(conflict_query, tuple(conflict_params))
                    conflicting_user = cur_check.fetchone()
                    if conflicting_user:
                        if "username" in update_data and conflicting_user[1] == update_data["username"]:
                             raise UserAlreadyExistsError(f"Username '{update_data['username']}' already exists for another user.")
                        if "email" in update_data and conflicting_user[2] == update_data["email"]:
                             raise UserAlreadyExistsError(f"Email '{update_data['email']}' already exists for another user.")
                        # Fallback
                        raise UserAlreadyExistsError("Username or email already exists for another user (conflict detected).")


        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            updated_id_tuple = cur.fetchone()
            if not updated_id_tuple: # Should not happen if get_user_by_id above succeeded
                raise UserNotFoundError(f"User with ID {user_id} not found during update execution (unexpected).")

            updated_id = updated_id_tuple[0]
            conn.commit()

            # Audit logging should be called from the router, passing the admin_user_id
            # Example: log_event('USER_UPDATED', 'users', updated_id, changed_details_for_audit,
            #                    admin_user_id_performing_action, conn=conn)
            return True

    except (UserNotFoundError, UserAlreadyExistsError):
        if conn and not conn.closed and not conn.autocommit: conn.rollback()
        raise
    except Exception as e:
        if conn and not conn.closed and not conn.autocommit: conn.rollback()
        raise UserServiceError(f"Error updating user ID {user_id}: {e}")
    finally:
        if _conn_managed_internally and conn and not conn.closed:
            conn.close()


if __name__ == '__main__':
    print("Testing user_service.py functions...")
    # These tests assume the database is up and schemas (auth_schema.sql) are applied.
    # `conftest.py` and `pytest` would normally handle test DB setup and teardown.
    # For direct run, manual DB setup might be needed.
    # Ensure roles like 'customer' (role_id 1 from auth_schema.sql) exist.

    test_username = "test_usr_svc_user"
    test_email = "test.usr.svc@example.com"
    test_user_id = None

    # Cleanup before test (if run multiple times)
    # In pytest, db_conn fixture handles this.
    try:
        conn_clean = get_db_connection()
        with conn_clean.cursor() as cur_clean:
            cur_clean.execute("DELETE FROM users WHERE username = %s OR email = %s;", (test_username, test_email))
            conn_clean.commit()
    except Exception as e_clean:
        print(f"Pre-test cleanup error (ignoring): {e_clean}")
    finally:
        if 'conn_clean' in locals() and conn_clean: conn_clean.close()

    try:
        print(f"\n1. Creating user '{test_username}'...")
        # Assuming role_id 1 ('customer') exists from auth_schema.sql default inserts
        # Ensure role_id 3 ('admin') also exists for authenticate_user test later
        with get_db_connection() as conn_roles: # Temp conn to ensure roles
            with conn_roles.cursor() as cur_roles:
                cur_roles.execute("INSERT INTO roles (role_id, role_name) VALUES (1, 'customer') ON CONFLICT (role_id) DO NOTHING;")
                cur_roles.execute("INSERT INTO roles (role_id, role_name) VALUES (3, 'admin') ON CONFLICT (role_id) DO NOTHING;")
            conn_roles.commit()


        test_user_id = create_user(test_username, "password123", test_email, role_id=3) # Create as admin for auth test
        assert test_user_id is not None
        print(f"   User created with ID: {test_user_id}")

        print(f"\n2. Getting user by ID ({test_user_id})...")
        user = get_user_by_id(test_user_id)
        assert user is not None
        assert user["username"] == test_username
        assert user["email"] == test_email
        assert user["role_name"] == "admin"
        print(f"   User details: {user['username']}, Role: {user['role_name']}")

        print("\n2a. Authenticating user...")
        authenticated_user = authenticate_user(test_username, "password123")
        assert authenticated_user is not None
        assert authenticated_user["username"] == test_username
        assert authenticated_user["role_name"] == "admin"
        print(f"   User '{test_username}' authenticated successfully.")

        print("\n2b. Failing authentication (wrong password)...")
        failed_auth_user = authenticate_user(test_username, "wrongpassword")
        assert failed_auth_user is None
        print("   Authentication with wrong password failed as expected.")

        print("\n2c. Failing authentication (non-existent user)...")
        non_existent_user_auth = authenticate_user("nosuchuser", "anypassword")
        assert non_existent_user_auth is None
        print("   Authentication for non-existent user failed as expected.")


        print("\n3. Listing users (expecting at least the created user)...")
        users_page = list_users(page=1, per_page=5, search_query=test_username)
        assert users_page["total_users"] >= 1
        assert any(u["user_id"] == test_user_id for u in users_page["users"])
        print(f"   Found {users_page['total_users']} user(s) matching search. Page content: {len(users_page['users'])}")

        print("\n4. Updating user (email and password)...")
        updated_email = "updated.usr.svc@example.com"
        new_password = "newStrongPassword123!"
        update_success = update_user(test_user_id, {"email": updated_email, "is_active": False, "password": new_password})
        assert update_success is True
        updated_user = get_user_by_id(test_user_id)
        assert updated_user["email"] == updated_email
        assert updated_user["is_active"] is False
        print(f"   User updated. New email: {updated_user['email']}, Active: {updated_user['is_active']}")

        # Verify new password
        re_authenticated_user = authenticate_user(test_username, new_password)
        assert re_authenticated_user is not None
        print(f"   User '{test_username}' re-authenticated successfully with new password.")

        # Verify old password no longer works
        failed_re_auth = authenticate_user(test_username, "password123") # old password
        assert failed_re_auth is None
        print("   Authentication with old password failed as expected after password change.")


        print("\n5. Attempting to create user with conflicting email (should fail)...")
        try:
            create_user("anotheruser", "newpass", updated_email, role_id=1)
            raise AssertionError("Conflicting email user creation did not fail.")
        except UserAlreadyExistsError:
            print("   Successfully caught UserAlreadyExistsError for email conflict.")


    except (UserServiceError, UserNotFoundError, UserAlreadyExistsError) as e:
        print(f"User service test error: {e}")
    except Exception as e_main_test:
        print(f"An unexpected error occurred in user_service tests: {e_main_test}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup after test
        if test_user_id: # Ensure test_user_id was set
            try:
                conn_cleanup_after = get_db_connection()
                with conn_cleanup_after.cursor() as cur_final_clean:
                    cur_final_clean.execute("DELETE FROM users WHERE user_id = %s;", (test_user_id,))
                    conn_cleanup_after.commit()
                print(f"   User {test_user_id} cleaned up.")
            except Exception as e_final_clean:
                print(f"Post-test cleanup error: {e_final_clean}")
            finally:
                if 'conn_cleanup_after' in locals() and conn_cleanup_after and not conn_cleanup_after.closed:
                    conn_cleanup_after.close()

    print("\nuser_service.py tests finished.")


def authenticate_user(username: str, password: str, conn=None) -> Optional[dict]:
    """
    Authenticates a user by username and password.

    Args:
        username (str): The username.
        password (str): The plain text password.
        conn (psycopg2.connection, optional): Existing database connection.

    Returns:
        Optional[dict]: User details (including user_id, username, role_name, email, is_active)
                        if authentication is successful, otherwise None.
                        Does not return password_hash.
    """
    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection()
        _conn_needs_managing = True

    user_data_for_auth = None
    try:
        # Fetch user by username first, including the hash and role for verification
        # Re-using get_user_by_id logic is tricky because it doesn't primarily fetch by username.
        # Direct query here:
        query = """
            SELECT u.user_id, u.username, u.password_hash, u.email, u.role_id, r.role_name, u.is_active
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.username = %s;
        """
        with conn.cursor() as cur:
            cur.execute(query, (username,))
            record = cur.fetchone()

        if not record:
            return None # User not found by username

        user_id, db_username, db_password_hash, db_email, db_role_id, db_role_name, db_is_active = record

        if not db_is_active:
            print(f"Authentication attempt for inactive user: {username}")
            return None # Do not authenticate inactive users

        if verify_password(password, db_password_hash):
            # Password matches
            user_data_for_auth = {
                "user_id": user_id,
                "username": db_username,
                "email": db_email,
                "role_id": db_role_id,
                "role_name": db_role_name,
                "is_active": db_is_active
                # Customer_id could be added if needed for session
            }
            # Optionally, update last_login timestamp here
            with conn.cursor() as cur_update_login:
                cur_update_login.execute("UPDATE users SET last_login = NOW() WHERE user_id = %s;", (user_id,))
            if _conn_needs_managing: conn.commit() # Commit last_login update if we manage connection
            # If conn is passed, caller should commit. This is tricky for a read-like auth func.
            # For now, if passed conn, last_login update might not be committed by this func.
            # A better pattern: auth returns user, router updates last_login. Or this func always uses new conn for auth.
            # For simplicity with current structure: if conn is passed, assume it's part of a larger tx that will commit.
    # However, if conn is managed internally, commit is already done.
    # If conn is passed, it's better if the caller commits after this (read + potential update) function.
    # Let's ensure commit happens only if connection is internally managed for the last_login update.

            return user_data_for_auth
        else:
            # Password does not match
            return None

    except Exception as e:
        print(f"Error during authentication for user {username}: {e}")
        # Do not expose detailed errors, just fail authentication
        # Rollback if we managed connection and an error occurred before commit
        if _conn_needs_managing and conn and not conn.closed and not getattr(conn, 'autocommit', True):
            conn.rollback()
        return None
    finally:
        if _conn_needs_managing and conn and not conn.closed:
            conn.close()

def get_user_by_username(username: str, conn=None) -> Optional[dict]:
    """
    Retrieves a user by their username, joining with roles table for role_name.
    This is similar to get_user_by_id but fetches by username.
    Returns user details including hashed_password for internal use or None if not found.
    """
    query = """
        SELECT u.user_id, u.username, u.email, u.role_id, r.role_name,
               u.customer_id, u.is_active, u.created_at, u.last_login, u.password_hash
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        WHERE u.username = %s;
    """ # Assuming username is unique, otherwise add LIMIT 1 or handle multiple results

    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection()
        _conn_needs_managing = True

    try:
        with conn.cursor() as cur:
            cur.execute(query, (username,))
            record = cur.fetchone()

        if not record:
            # Not raising UserNotFoundError here, just returning None as per Optional[dict]
            return None

        return {
            "user_id": record[0], "username": record[1], "email": record[2],
            "role_id": record[3], "role_name": record[4], "customer_id": record[5],
            "is_active": record[6], "created_at": record[7], "last_login": record[8],
            "password_hash": record[9]
        }
    except Exception as e:
        # Log this error
        print(f"Error fetching user by username '{username}': {e}")
        raise UserServiceError(f"Database error fetching user by username '{username}'.")
    finally:
        if _conn_needs_managing and conn and not conn.closed:
            conn.close()

```
