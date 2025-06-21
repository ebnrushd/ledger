import pytest
from fastapi.testclient import TestClient
from fastapi import status

# Uses admin_client and teller_client fixtures

@pytest.fixture
def setup_audit_logs_for_admin_api(admin_client: TestClient, db_conn):
    """
    Perform some actions that generate audit logs.
    Relies on actions in other routers/services that call audit_service.log_event.
    Example: Create a user, update an account status.
    """
    # Create a user (generates ADMIN_USER_CREATED log)
    new_user_data = {
        "username": "auditlogtestuser", "email": "audit.log@example.com",
        "password": "Password123!", "role_id": "1" # Customer role
    }
    response_user = admin_client.post("/admin/users/new", data=new_user_data)
    assert response_user.status_code == status.HTTP_303_SEE_OTHER # Redirect on success

    # Get created user's ID from location header or by fetching (complex)
    # For simplicity, assume it worked and a log was created. We'll search for its action_type.

    # Create a customer and account to change its status
    cust_payload = {"first_name": "AuditCust", "last_name": "LogTest", "email": "audit.cust@example.com"}
    cust_resp = admin_client.post("/api/v1/customers/", json=cust_payload) # Use public API for simplicity
    cust_id = cust_resp.json()["customer_id"]

    acc_payload = {"customer_id": cust_id, "account_type": "savings", "initial_balance": "0"}
    acc_resp = admin_client.post("/api/v1/accounts/", json=acc_payload) # Use public API
    acc_id = acc_resp.json()["account_id"]

    # Update account status (generates ADMIN_ACCOUNT_STATUS_CHANGE log)
    status_update_payload = {"status": "frozen"} # Form data: status=frozen
    response_status = admin_client.post(f"/admin/accounts/{acc_id}/status", data=status_update_payload)
    assert response_status.status_code == status.HTTP_303_SEE_OTHER

    return {"user_action": "ADMIN_USER_CREATED", "account_action": "ADMIN_ACCOUNT_STATUS_CHANGE", "account_id_target": str(acc_id)}


def test_list_audit_logs_as_admin(admin_client: TestClient, setup_audit_logs_for_admin_api):
    """Admin should see a list of audit logs, including generated ones."""
    log_info = setup_audit_logs_for_admin_api

    response = admin_client.get("/admin/audit_logs/")
    assert response.status_code == status.HTTP_200_OK
    assert "System Audit Logs" in response.text

    # Check if known action types from setup appear in the list
    assert log_info["user_action"] in response.text
    assert log_info["account_action"] in response.text
    assert log_info["account_id_target"] in response.text # Check if target_id is visible

def test_list_audit_logs_filter_by_action_type(admin_client: TestClient, setup_audit_logs_for_admin_api):
    """Test filtering audit logs by action type."""
    log_info = setup_audit_logs_for_admin_api
    action_to_filter = log_info["user_action"] # ADMIN_USER_CREATED

    response = admin_client.get(f"/admin/audit_logs/?action_type_filter={action_to_filter}")
    assert response.status_code == status.HTTP_200_OK
    assert action_to_filter in response.text
    # Ensure other action type is not present (if distinct enough)
    assert log_info["account_action"] not in response.text

def test_list_audit_logs_filter_by_target_id(admin_client: TestClient, setup_audit_logs_for_admin_api):
    """Test filtering audit logs by target ID."""
    log_info = setup_audit_logs_for_admin_api
    target_id_to_filter = log_info["account_id_target"]

    response = admin_client.get(f"/admin/audit_logs/?target_id_filter={target_id_to_filter}")
    assert response.status_code == status.HTTP_200_OK
    assert log_info["account_action"] in response.text # This was on account_id_target
    assert target_id_to_filter in response.text
    assert log_info["user_action"] not in response.text # Should be filtered out

def test_list_audit_logs_as_teller_fail(teller_client: TestClient):
    """Teller should NOT be able to view audit logs."""
    response = teller_client.get("/admin/audit_logs/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access Denied" in response.text # From error_403.html
    assert "Your role ('teller') is not authorized" in response.text

# No detail view for audit logs currently implemented via API.
```
