import pytest
from fastapi.testclient import TestClient
from fastapi import status

# No specific models needed for these auth tests beyond what TestClient handles.

def test_get_login_form(test_client: TestClient):
    """Test that the admin login page loads correctly."""
    response = test_client.get("/admin/login")
    assert response.status_code == status.HTTP_200_OK
    assert "Admin Panel Login" in response.text # Check for a key phrase from login.html

def test_login_success(test_client: TestClient, create_admin_user, db_conn): # Uses create_admin_user to ensure user exists
    """Test successful login with valid admin credentials."""
    admin_user = create_admin_user # User dict from fixture
    db_conn.commit() # Ensure user created by fixture is committed before login attempt

    login_data = {"username": admin_user["username"], "password": admin_user["password"]}
    response = test_client.post("/admin/login", data=login_data)

    assert response.status_code == status.HTTP_303_SEE_OTHER # Redirects to dashboard
    assert response.headers["location"] == "/admin/dashboard" # Check redirect URL (or use request.url_for)
    assert "ledger_admin_session" in test_client.cookies

    # Verify access to a protected route (dashboard)
    dashboard_response = test_client.get("/admin/dashboard")
    assert dashboard_response.status_code == status.HTTP_200_OK
    assert f"Welcome, {admin_user['username']}" in dashboard_response.text

def test_login_failed_wrong_password(test_client: TestClient, create_admin_user, db_conn):
    """Test login failure with incorrect password."""
    admin_user = create_admin_user
    db_conn.commit()

    login_data = {"username": admin_user["username"], "password": "WrongPassword!"}
    response = test_client.post("/admin/login", data=login_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST # Re-renders login form with error
    assert "Invalid username or password" in response.text
    assert "ledger_admin_session" not in response.cookies # No session cookie should be set

def test_login_failed_non_existent_user(test_client: TestClient):
    """Test login failure with a username that does not exist."""
    login_data = {"username": "nosuchuser@example.com", "password": "anypassword"}
    response = test_client.post("/admin/login", data=login_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid username or password" in response.text
    assert "ledger_admin_session" not in response.cookies

def test_logout_success(admin_client: TestClient): # Uses admin_client which is already authenticated
    """Test successful logout."""
    # First, verify we are logged in by accessing a protected route
    dashboard_resp = admin_client.get("/admin/dashboard")
    assert dashboard_resp.status_code == status.HTTP_200_OK

    # Perform logout
    logout_response = admin_client.get("/admin/logout") # Changed to GET to match route
    assert logout_response.status_code == status.HTTP_303_SEE_OTHER
    assert logout_response.headers["location"] == "/admin/login"

    # Session cookie should be cleared or invalidated by the server.
    # TestClient typically manages cookies; after logout, subsequent requests shouldn't be authenticated.
    # We can check if the cookie is explicitly cleared by path=/ and max-age=0, but that's implementation detail.
    # More practically, check if a protected route is no longer accessible.

    dashboard_after_logout = admin_client.get("/admin/dashboard")
    # Expect redirect to login because get_current_admin_user will trigger it
    assert dashboard_after_logout.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert "login" in dashboard_after_logout.headers["location"]


def test_access_protected_route_unauthenticated(test_client: TestClient):
    """Test accessing a protected admin route without authentication."""
    response = test_client.get("/admin/dashboard")
    # Should redirect to login (307 Temporary Redirect)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert "login" in response.headers["location"] # Check if it redirects to login path

# --- RBAC Tests ---
def test_rbac_admin_access_to_user_management(admin_client: TestClient):
    """Admin user should access user management (which requires 'admin' role)."""
    response = admin_client.get("/admin/users/") # User list page
    assert response.status_code == status.HTTP_200_OK
    assert "User Management" in response.text # Check for page title or key content

def test_rbac_teller_denied_user_management(teller_client: TestClient):
    """Teller user should NOT access user management."""
    response = teller_client.get("/admin/users/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    # Check if the custom 403 error page is rendered
    assert "Access Denied" in response.text
    assert "Your role ('teller') is not authorized" in response.text

def test_rbac_teller_access_to_customer_list(teller_client: TestClient):
    """Teller user should access customer list (allowed for 'admin', 'teller', 'auditor')."""
    response = teller_client.get("/admin/customers/")
    assert response.status_code == status.HTTP_200_OK
    assert "Customer Management" in response.text

def test_rbac_teller_denied_audit_logs(teller_client: TestClient):
    """Teller user should NOT access audit logs (allowed for 'admin', 'auditor')."""
    response = teller_client.get("/admin/audit_logs/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access Denied" in response.text
    assert "Your role ('teller') is not authorized" in response.text

def test_rbac_admin_access_to_audit_logs(admin_client: TestClient):
    """Admin user should access audit logs."""
    response = admin_client.get("/admin/audit_logs/")
    assert response.status_code == status.HTTP_200_OK
    assert "System Audit Logs" in response.text

# Test accessing an admin page that doesn't have specific role beyond general admin panel access
def test_rbac_teller_access_to_dashboard(teller_client: TestClient):
    """Teller is in ADMIN_PANEL_ACCESS_ROLES, so should access dashboard."""
    response = teller_client.get("/admin/dashboard")
    assert response.status_code == status.HTTP_200_OK
    assert "Dashboard Overview" in response.text

```
