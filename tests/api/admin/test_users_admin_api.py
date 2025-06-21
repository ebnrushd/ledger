import pytest
from fastapi.testclient import TestClient
from fastapi import status
import psycopg2.extras # For fetching roles if needed for assertions

# Uses admin_client and teller_client fixtures from conftest.py

def test_list_users_as_admin(admin_client: TestClient, create_admin_user, create_teller_user, db_conn):
    """Admin should see a list of users, including newly created ones."""
    # Fixtures create_admin_user and create_teller_user ensure these users exist.
    # db_conn.commit() might be needed if create_user fixtures don't commit and TestClient runs in separate transaction.
    # The create_user fixtures in conftest.py now commit.

    response = admin_client.get("/admin/users/")
    assert response.status_code == status.HTTP_200_OK
    assert "User Management" in response.text
    assert create_admin_user["username"] in response.text # test_admin_user
    assert create_teller_user["username"] in response.text # test_teller_user

def test_list_users_search_as_admin(admin_client: TestClient, create_admin_user):
    """Test searching for a specific user."""
    admin_username = create_admin_user["username"]
    response = admin_client.get(f"/admin/users/?search_query={admin_username}")
    assert response.status_code == status.HTTP_200_OK
    assert admin_username in response.text
    assert "test_teller_user" not in response.text # Assuming teller username is different enough

def test_get_new_user_form_as_admin(admin_client: TestClient):
    """Admin should be able to access the new user form."""
    response = admin_client.get("/admin/users/new")
    assert response.status_code == status.HTTP_200_OK
    assert "Create New User" in response.text
    assert 'name="username"' in response.text # Check for a form field

def test_create_new_user_success_as_admin(admin_client: TestClient, db_conn):
    """Admin successfully creates a new user."""
    new_user_data = {
        "username": "new_api_user",
        "email": "new.api.user@example.com",
        "password": "NewPassword123!",
        "role_id": "2", # Teller role from default roles in auth_schema.sql
        "is_active": "on" # HTML form checkbox
    }
    response = admin_client.post("/admin/users/new", data=new_user_data)
    assert response.status_code == status.HTTP_303_SEE_OTHER # Redirect on success
    assert "/admin/users" in response.headers["location"]
    assert "success_message=User created successfully" in response.headers["location"]

    # Verify user exists in DB (or by trying to list/get them via API)
    response_list = admin_client.get("/admin/users/?search_query=new_api_user")
    assert "new_api_user" in response_list.text

    # Verify audit log (conceptual - requires querying DB)
    # with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
    #     cur.execute("SELECT * FROM audit_log WHERE action_type = 'ADMIN_USER_CREATED' AND target_entity = 'users' ORDER BY timestamp DESC LIMIT 1;")
    #     log_entry = cur.fetchone()
    #     assert log_entry is not None
    #     assert log_entry['details_json']['username'] == "new_api_user"
    #     # assert log_entry['user_id'] == admin_user_id_from_session (hard to get here easily)

def test_create_new_user_validation_error_as_admin(admin_client: TestClient):
    """Admin attempts to create user with invalid data (e.g., short password)."""
    invalid_user_data = {
        "username": "shortpass_user",
        "email": "short.pass@example.com",
        "password": "123", # Too short
        "role_id": "1"
    }
    response = admin_client.post("/admin/users/new", data=invalid_user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST # Re-renders form with error
    assert "Password must be at least 8 characters long" in response.text
    assert 'value="shortpass_user"' in response.text # Form re-population

def test_create_new_user_duplicate_username_as_admin(admin_client: TestClient, create_admin_user):
    """Admin attempts to create user with an existing username."""
    admin = create_admin_user
    duplicate_user_data = {
        "username": admin["username"], # Existing username
        "email": "unique.email@example.com",
        "password": "Password123!",
        "role_id": "2"
    }
    response = admin_client.post("/admin/users/new", data=duplicate_user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert f"User with username '{admin['username']}' already exists" in response.text


def test_view_user_detail_as_admin(admin_client: TestClient, create_teller_user):
    """Admin views details of an existing user."""
    teller = create_teller_user
    response = admin_client.get(f"/admin/users/{teller['user_id']}")
    assert response.status_code == status.HTTP_200_OK
    assert f"User Profile: {teller['username']}" in response.text
    assert teller["username"] in response.text
    assert "teller@example.com" in response.text # Teller's email

def test_get_edit_user_form_as_admin(admin_client: TestClient, create_teller_user):
    """Admin accesses the edit form for a user."""
    teller = create_teller_user
    response = admin_client.get(f"/admin/users/{teller['user_id']}/edit")
    assert response.status_code == status.HTTP_200_OK
    assert f"Edit User: {teller['username']}" in response.text
    assert f'value="{teller["username"]}"' in response.text # Check form pre-population

def test_edit_user_success_as_admin(admin_client: TestClient, create_teller_user, db_conn):
    """Admin successfully edits a user's details (e.g., role and active status)."""
    teller = create_teller_user

    # Get admin role_id (assuming it's 3 from auth_schema)
    admin_role_id = 3
    with db_conn.cursor() as cur: # Ensure admin role exists or get its ID
        cur.execute("SELECT role_id FROM roles WHERE role_name = 'admin';")
        res = cur.fetchone()
        if res: admin_role_id = res[0]
        else: pytest.fail("Admin role not found in DB for test setup")

    edit_user_data = {
        "username": teller["username"], # Keep username same
        "email": "teller.updated@example.com",
        "role_id": str(admin_role_id), # Change role to admin
        "is_active": "" # Uncheck 'is_active'
        # Password field is optional, leave blank to not change
    }
    response = admin_client.post(f"/admin/users/{teller['user_id']}/edit", data=edit_user_data)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert "success_message=User updated successfully" in response.headers["location"]

    # Verify changes
    updated_user_resp = admin_client.get(f"/admin/users/{teller['user_id']}")
    assert "teller.updated@example.com" in updated_user_resp.text
    assert '<span class="badge bg-danger">Inactive</span>' in updated_user_resp.text # is_active is False
    assert "admin" in updated_user_resp.text # Role name updated

    # Verify audit log (conceptual)
    # ... query audit_log table for ADMIN_USER_UPDATED ...

def test_edit_user_change_password_as_admin(admin_client: TestClient, create_teller_user):
    """Admin changes a user's password."""
    teller = create_teller_user
    new_password = "NewSecurePassword321!"
    edit_data_password = {
        "username": teller["username"],
        "email": "teller@example.com", # Original email
        "role_id": "2", # Original role
        "password": new_password,
        "is_active": "on"
    }
    response = admin_client.post(f"/admin/users/{teller['user_id']}/edit", data=edit_data_password)
    assert response.status_code == status.HTTP_303_SEE_OTHER

    # Verify login with new password (requires direct call to user_service.authenticate_user or API login)
    # This is simpler to test at service layer. For API, we'd have to log out admin_client,
    # then try to log in as the teller user with the new password.
    # For now, trust the service layer test for password verification.
    # One could also check the audit log for "password_changed": true.
```
