import pytest
from fastapi.testclient import TestClient
from fastapi import status
from decimal import Decimal
from datetime import date, timedelta

# Uses admin_client, teller_client fixtures
# Needs setup for transactions

@pytest.fixture
def setup_transactions_for_admin_api(test_client: TestClient, db_conn):
    """Create customer, accounts, and transactions for admin transaction view tests."""
    # Customer 1, Account 1
    c1_payload = {"first_name": "TxViewAdmin", "last_name": "Cust1", "email": "txview.admin.c1@example.com"}
    c1_resp = test_client.post("/customers/", json=c1_payload)
    c1_id = c1_resp.json()["customer_id"]
    acc1_payload = {"customer_id": c1_id, "account_type": "checking", "initial_balance": "1000.00"}
    acc1_resp = test_client.post("/accounts/", json=acc1_payload)
    acc1_id = acc1_resp.json()["account_id"]
    acc1_num = acc1_resp.json()["account_number"]

    # Customer 2, Account 2
    c2_payload = {"first_name": "TxViewAdmin", "last_name": "Cust2", "email": "txview.admin.c2@example.com"}
    c2_resp = test_client.post("/customers/", json=c2_payload)
    c2_id = c2_resp.json()["customer_id"]
    acc2_payload = {"customer_id": c2_id, "account_type": "savings", "initial_balance": "500.00"}
    acc2_resp = test_client.post("/accounts/", json=acc2_payload)
    acc2_id = acc2_resp.json()["account_id"]
    acc2_num = acc2_resp.json()["account_number"]

    # Transactions
    # For precise date filtering tests, transactions would need to be created with specific past dates via core functions or direct DB.
    # For now, API calls will make them "today".
    tx1_resp = test_client.post("/transactions/deposit", json={"account_id": acc1_id, "amount": "200.00", "description": "AdminView Dep1"})
    tx1_id = tx1_resp.json()["transaction_id"]

    tx2_resp = test_client.post("/transactions/withdraw", json={"account_id": acc1_id, "amount": "50.00", "description": "AdminView Wd1"})
    tx2_id = tx2_resp.json()["transaction_id"]

    tx3_resp = test_client.post("/transactions/transfer", json={"from_account_id": acc1_id, "to_account_id": acc2_id, "amount": "100.00", "description": "AdminView Trf1"})
    # tx3_id_debit = tx3_resp.json()["debit_transaction"]["transaction_id"]
    # tx3_id_credit = tx3_resp.json()["credit_transaction"]["transaction_id"]

    return {"acc1_id": acc1_id, "acc1_num": acc1_num, "acc2_id": acc2_id, "acc2_num": acc2_num,
            "tx1_id": tx1_id, "tx2_id": tx2_id}


def test_list_transactions_as_admin(admin_client: TestClient, setup_transactions_for_admin_api):
    """Admin should see a list of transactions."""
    acc1_num = setup_transactions_for_admin_api["acc1_num"]

    response = admin_client.get("/admin/transactions/")
    assert response.status_code == status.HTTP_200_OK
    assert "Transaction Monitoring" in response.text
    assert acc1_num in response.text # Check if one of the account numbers appears
    assert "AdminView Dep1" in response.text # Check for a transaction description

def test_list_transactions_filter_by_account_id(admin_client: TestClient, setup_transactions_for_admin_api):
    """Test filtering transactions by account ID."""
    acc1_id = setup_transactions_for_admin_api["acc1_id"]
    acc1_num = setup_transactions_for_admin_api["acc1_num"]
    acc2_num = setup_transactions_for_admin_api["acc2_num"] # Should not appear

    response = admin_client.get(f"/admin/transactions/?account_id_filter={acc1_id}")
    assert response.status_code == status.HTTP_200_OK
    assert acc1_num in response.text
    assert acc2_num not in response.text # Assuming acc2_num is distinct enough
    assert "AdminView Dep1" in response.text
    assert "AdminView Wd1" in response.text
    assert "AdminView Trf1" in response.text # Transfer involving acc1

def test_list_transactions_filter_by_type(admin_client: TestClient, setup_transactions_for_admin_api):
    """Test filtering transactions by type."""
    acc1_num = setup_transactions_for_admin_api["acc1_num"]
    response = admin_client.get("/admin/transactions/?transaction_type_filter=deposit")
    assert response.status_code == status.HTTP_200_OK
    assert "AdminView Dep1" in response.text
    assert "AdminView Wd1" not in response.text # Should be filtered out

def test_view_transaction_detail_as_admin(admin_client: TestClient, setup_transactions_for_admin_api):
    """Admin views details of an existing transaction."""
    transaction_id = setup_transactions_for_admin_api["tx1_id"] # Deposit transaction
    acc1_num = setup_transactions_for_admin_api["acc1_num"]

    response = admin_client.get(f"/admin/transactions/{transaction_id}")
    assert response.status_code == status.HTTP_200_OK
    assert f"Transaction Details: ID {transaction_id}" in response.text
    assert "AdminView Dep1" in response.text
    assert acc1_num in response.text # Primary account number

def test_view_transaction_detail_not_found(admin_client: TestClient):
    """Test viewing a non-existent transaction."""
    response = admin_client.get("/admin/transactions/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Transaction not found" in response.json()["detail"] # API returns JSON for direct HTTPExceptions

def test_list_transactions_as_teller(teller_client: TestClient, setup_transactions_for_admin_api):
    """Teller should also be able to view transactions list."""
    response = teller_client.get("/admin/transactions/")
    assert response.status_code == status.HTTP_200_OK
    assert "Transaction Monitoring" in response.text
    assert "AdminView Dep1" in response.text # Check for some transaction data
```
