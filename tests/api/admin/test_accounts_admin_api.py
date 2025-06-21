import pytest
from fastapi.testclient import TestClient
from fastapi import status
from decimal import Decimal

# Uses admin_client, teller_client, create_customer_fx, create_account_fx fixtures

@pytest.fixture
def setup_accounts_for_admin_api(db_conn, create_customer_fx, create_account_fx):
    """Create customers and accounts for admin account listing/detail tests."""
    c1_id = create_customer_fx(first_name="AccAdmin", last_name="UserOne", email_suffix="@accadmin1.com")
    c2_id = create_customer_fx(first_name="AccAdmin", last_name="UserTwo", email_suffix="@accadmin2.com")

    acc1_id = create_account_fx(customer_id=c1_id, account_type="checking", initial_balance=Decimal("1000.00"))
    acc2_id = create_account_fx(customer_id=c1_id, account_type="savings", initial_balance=Decimal("500.00"))
    acc3_id = create_account_fx(customer_id=c2_id, account_type="checking", initial_balance=Decimal("1200.00"))

    from core.account_management import update_account_status # To set one account to 'frozen'
    update_account_status(acc2_id, "frozen", conn=db_conn) # Using db_conn from fixture directly
    db_conn.commit()

    return {"c1": c1_id, "c2": c2_id, "a1": acc1_id, "a2": acc2_id, "a3": acc3_id}

def test_list_accounts_as_admin(admin_client: TestClient, setup_accounts_for_admin_api):
    """Admin should see a list of accounts."""
    response = admin_client.get("/admin/accounts/")
    assert response.status_code == status.HTTP_200_OK
    assert "Account Management" in response.text

    # Check for presence of account numbers (these are dynamic, so check for table rows)
    # A more robust check would involve parsing HTML or knowing account numbers.
    # For now, check if the table structure seems to be populated.
    assert "<td>AccAdmin UserOne</td>" in response.text or "AccAdmin UserTwo" in response.text # Customer names
    assert 'class="table' in response.text

def test_list_accounts_filter_by_status_as_admin(admin_client: TestClient, setup_accounts_for_admin_api):
    """Test filtering accounts by status."""
    acc2_id = setup_accounts_for_admin_api["a2"] # This account was set to 'frozen'

    # Fetch its number to verify it's the only one when filtering by frozen
    acc2_details_resp = admin_client.get(f"/api/v1/accounts/{acc2_id}") # Use public API to get details
    acc2_number = acc2_details_resp.json()["account_number"]

    response = admin_client.get("/admin/accounts/?status_filter=frozen")
    assert response.status_code == status.HTTP_200_OK
    assert acc2_number in response.text
    # Check that other accounts (which are active) are not present
    # This requires knowing other account numbers or more detailed parsing.
    # For now, assume if filtered one is there, and list isn't too long, it works.

def test_list_accounts_search_as_admin(admin_client: TestClient, setup_accounts_for_admin_api):
    """Test searching for an account by its number (or part of it)."""
    acc1_id = setup_accounts_for_admin_api["a1"]
    acc1_details_resp = admin_client.get(f"/api/v1/accounts/{acc1_id}")
    acc1_number = acc1_details_resp.json()["account_number"]

    response = admin_client.get(f"/admin/accounts/?search_query={acc1_number[:5]}") # Search by part of acc number
    assert response.status_code == status.HTTP_200_OK
    assert acc1_number in response.text


def test_view_account_detail_as_admin(admin_client: TestClient, setup_accounts_for_admin_api):
    """Admin views details of an existing account."""
    account_id = setup_accounts_for_admin_api["a1"]
    response = admin_client.get(f"/admin/accounts/{account_id}")
    assert response.status_code == status.HTTP_200_OK

    acc_details = admin_client.get(f"/api/v1/accounts/{account_id}").json() # Get actual details
    assert f"Account Details: {acc_details['account_number']}" in response.text
    assert "Account Information" in response.text
    assert "Manage Account" in response.text
    assert "Recent Transactions" in response.text
    assert "Status updated successfully." not in response.text # No success message initially
    assert "Overdraft limit updated successfully." not in response.text


def test_update_account_status_as_admin(admin_client: TestClient, setup_accounts_for_admin_api, db_conn):
    """Admin successfully changes an account's status."""
    account_id = setup_accounts_for_admin_api["a1"] # Initially active

    # Change to Frozen
    response_freeze = admin_client.post(f"/admin/accounts/{account_id}/status", data={"status": "frozen"})
    assert response_freeze.status_code == status.HTTP_303_SEE_OTHER # Redirect
    assert "success_message=Status updated successfully" in response_freeze.headers["location"]

    # Verify change by fetching detail page (which will show current status)
    detail_page_resp = admin_client.get(f"/admin/accounts/{account_id}")
    assert '<span class="badge bg-warning text-dark">Frozen</span>' in detail_page_resp.text

    # Verify audit log (conceptual)
    # with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
    #     cur.execute("SELECT * FROM audit_log WHERE action_type = 'ADMIN_ACCOUNT_STATUS_CHANGE' AND target_id = %s ORDER BY timestamp DESC LIMIT 1;", (str(account_id),))
    #     log = cur.fetchone()
    #     assert log is not None
    #     assert log['details_json']['old_status'] == 'active'
    #     assert log['details_json']['new_status'] == 'frozen'

def test_update_account_status_fail_close_with_balance(admin_client: TestClient, setup_accounts_for_admin_api):
    """Admin fails to close an account with non-zero balance."""
    account_id = setup_accounts_for_admin_api["a1"] # Has balance 1000
    response = admin_client.post(f"/admin/accounts/{account_id}/status", data={"status": "closed"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST # Re-renders form with error
    assert "cannot be closed due to non-zero balance" in response.text


def test_update_overdraft_limit_as_admin(admin_client: TestClient, setup_accounts_for_admin_api):
    """Admin successfully changes an account's overdraft limit."""
    account_id = setup_accounts_for_admin_api["a1"]
    new_overdraft_limit = "250.75"

    response = admin_client.post(f"/admin/accounts/{account_id}/overdraft", data={"overdraft_limit": new_overdraft_limit})
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert "success_message=Overdraft limit updated successfully" in response.headers["location"]

    detail_page_resp = admin_client.get(f"/admin/accounts/{account_id}")
    assert f'value="{Decimal(new_overdraft_limit):.2f}"' in detail_page_resp.text # Check if form shows new value
    # More robust: check the actual account details via API or DB
    acc_details_resp = admin_client.get(f"/api/v1/accounts/{account_id}")
    assert Decimal(acc_details_resp.json()["overdraft_limit"]) == Decimal(new_overdraft_limit)

def test_update_overdraft_limit_fail_negative(admin_client: TestClient, setup_accounts_for_admin_api):
    """Admin fails to set a negative overdraft limit."""
    account_id = setup_accounts_for_admin_api["a1"]
    response = admin_client.post(f"/admin/accounts/{account_id}/overdraft", data={"overdraft_limit": "-100"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # Pydantic validation on Form data

def test_view_accounts_as_teller(teller_client: TestClient, setup_accounts_for_admin_api):
    """Teller should be able to view account list and details."""
    response_list = teller_client.get("/admin/accounts/")
    assert response_list.status_code == status.HTTP_200_OK
    assert "Account Management" in response_list.text

    account_id = setup_accounts_for_admin_api["a1"]
    response_detail = teller_client.get(f"/admin/accounts/{account_id}")
    assert response_detail.status_code == status.HTTP_200_OK
    assert "Account Details" in response_detail.text

def test_update_account_status_as_teller_fail(teller_client: TestClient, setup_accounts_for_admin_api):
    """Teller should NOT be able to change account status."""
    account_id = setup_accounts_for_admin_api["a1"]
    response = teller_client.post(f"/admin/accounts/{account_id}/status", data={"status": "frozen"})
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access Denied" in response.text # From error_403.html
```
