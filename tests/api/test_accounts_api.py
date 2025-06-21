import pytest
from fastapi.testclient import TestClient
from fastapi import status
from decimal import Decimal
from datetime import date, timedelta

from api.models import AccountDetails, AccountCreate, AccountStatusUpdate, OverdraftLimitSet, AccountStatementResponse, TransactionDetails
# Assuming conftest.py provides test_client and utility fixtures like create_customer_fx
# For API tests, we mostly interact via test_client. Setup might use core functions via fixtures if needed.

# Helper to create a customer and return ID for account tests
@pytest.fixture
def test_customer_id_for_accounts(test_client: TestClient):
    payload = {
        "first_name": "AccAPI_Cust", "last_name": "Test", "email": "acc.api.cust@example.com",
        "phone_number": "555-0200", "address": "789 API Acc St"
    }
    response = test_client.post("/customers/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["customer_id"]

# --- Tests for Account API Endpoints ---

def test_open_account_success(test_client: TestClient, test_customer_id_for_accounts):
    """Test successful account opening."""
    customer_id = test_customer_id_for_accounts
    account_payload = {
        "customer_id": customer_id,
        "account_type": "savings",
        "initial_balance": "100.50", # Pydantic will convert to Decimal
        "currency": "USD"
    }
    response = test_client.post("/accounts/", json=account_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["customer_id"] == customer_id
    assert data["account_type"] == "savings"
    assert Decimal(data["balance"]) == Decimal("100.50")
    assert data["status_name"] == "active"
    assert Decimal(data["overdraft_limit"]) == Decimal("0.00")
    assert "account_id" in data
    assert "account_number" in data

def test_open_account_invalid_customer(test_client: TestClient):
    """Test opening account for a non-existent customer."""
    account_payload = {"customer_id": 99999, "account_type": "checking", "initial_balance": "0"}
    response = test_client.post("/accounts/", json=account_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND # From CustomerNotFoundError
    assert "Customer with ID 99999 not found" in response.json()["detail"]


def test_open_account_invalid_type(test_client: TestClient, test_customer_id_for_accounts):
    """Test opening account with an invalid account type."""
    account_payload = {"customer_id": test_customer_id_for_accounts, "account_type": "super-saver", "initial_balance": "10"}
    response = test_client.post("/accounts/", json=account_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST # From InvalidAccountTypeError
    assert "Account type 'super-saver' is not supported" in response.json()["detail"]


def test_get_account_details_success(test_client: TestClient, test_customer_id_for_accounts):
    """Test fetching details for an existing account."""
    # Create an account first
    acc_payload = {"customer_id": test_customer_id_for_accounts, "account_type": "checking", "initial_balance": "250.00"}
    create_resp = test_client.post("/accounts/", json=acc_payload)
    account_id = create_resp.json()["account_id"]

    response = test_client.get(f"/accounts/{account_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["account_id"] == account_id
    assert Decimal(data["balance"]) == Decimal("250.00")

def test_get_account_details_not_found(test_client: TestClient):
    """Test fetching details for a non-existent account."""
    response = test_client.get("/accounts/999888")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_account_status_success(test_client: TestClient, test_customer_id_for_accounts):
    """Test successfully updating an account's status."""
    acc_payload = {"customer_id": test_customer_id_for_accounts, "account_type": "savings", "initial_balance": "0"} # Zero bal for closing
    create_resp = test_client.post("/accounts/", json=acc_payload)
    account_id = create_resp.json()["account_id"]

    # Active -> Frozen
    status_payload_frozen = {"status": "frozen"}
    response_frozen = test_client.put(f"/accounts/{account_id}/status", json=status_payload_frozen)
    assert response_frozen.status_code == status.HTTP_200_OK
    assert response_frozen.json()["status_name"] == "frozen"

    # Frozen -> Active
    status_payload_active = {"status": "active"}
    response_active = test_client.put(f"/accounts/{account_id}/status", json=status_payload_active)
    assert response_active.status_code == status.HTTP_200_OK
    assert response_active.json()["status_name"] == "active"

    # Active -> Closed (balance is 0)
    status_payload_closed = {"status": "closed"}
    response_closed = test_client.put(f"/accounts/{account_id}/status", json=status_payload_closed)
    assert response_closed.status_code == status.HTTP_200_OK
    assert response_closed.json()["status_name"] == "closed"


def test_update_account_status_close_with_balance_fail(test_client: TestClient, test_customer_id_for_accounts):
    """Test failing to close an account with a non-zero balance."""
    acc_payload = {"customer_id": test_customer_id_for_accounts, "account_type": "checking", "initial_balance": "100.00"}
    create_resp = test_client.post("/accounts/", json=acc_payload)
    account_id = create_resp.json()["account_id"]

    status_payload = {"status": "closed"}
    response = test_client.put(f"/accounts/{account_id}/status", json=status_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot be closed due to non-zero balance" in response.json()["detail"]


def test_set_overdraft_limit_success(test_client: TestClient, test_customer_id_for_accounts):
    """Test setting and updating an account's overdraft limit."""
    acc_payload = {"customer_id": test_customer_id_for_accounts, "account_type": "checking"}
    create_resp = test_client.post("/accounts/", json=acc_payload)
    account_id = create_resp.json()["account_id"]

    limit_payload = {"limit": "150.75"} # Pydantic converts to Decimal
    response = test_client.post(f"/accounts/{account_id}/overdraft_limit", json=limit_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert Decimal(data["overdraft_limit"]) == Decimal("150.75")

def test_set_overdraft_limit_negative_fail(test_client: TestClient, test_customer_id_for_accounts):
    """Test failing to set a negative overdraft limit."""
    acc_payload = {"customer_id": test_customer_id_for_accounts, "account_type": "checking"}
    create_resp = test_client.post("/accounts/", json=acc_payload)
    account_id = create_resp.json()["account_id"]

    limit_payload = {"limit": "-50.00"}
    response = test_client.post(f"/accounts/{account_id}/overdraft_limit", json=limit_payload)
    # This will be caught by Pydantic model validation (ge=0) before core logic
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_account_statement_success(test_client: TestClient, test_customer_id_for_accounts):
    """Test generating an account statement."""
    acc_payload = {"customer_id": test_customer_id_for_accounts, "account_type": "savings", "initial_balance": "0"}
    create_resp = test_client.post("/accounts/", json=acc_payload)
    account_id = create_resp.json()["account_id"]

    # Add some transactions for the statement via API
    test_client.post("/transactions/deposit", json={"account_id": account_id, "amount": "1000", "description": "Dep1"})
    test_client.post("/transactions/withdraw", json={"account_id": account_id, "amount": "200", "description": "Wd1"})

    start_date_str = date.today().isoformat()
    end_date_str = date.today().isoformat()

    response = test_client.get(f"/accounts/{account_id}/statement?start_date={start_date_str}&end_date={end_date_str}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["account_info"]["account_number"] == create_resp.json()["account_number"]
    assert data["period"]["start_date"] == start_date_str
    assert len(data["transactions"]) == 2
    assert Decimal(data["starting_balance"]) == Decimal("0.00") # Assuming transactions are today and SB is before today
    assert Decimal(data["ending_balance"]) == Decimal("800.00") # 1000 - 200

def test_get_account_statement_invalid_date_format(test_client: TestClient, test_customer_id_for_accounts):
    acc_payload = {"customer_id": test_customer_id_for_accounts, "account_type": "savings"}
    create_resp = test_client.post("/accounts/", json=acc_payload)
    account_id = create_resp.json()["account_id"]

    response = test_client.get(f"/accounts/{account_id}/statement?start_date=01-01-2023&end_date=today")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # FastAPI validation of date query params


def test_get_account_transactions_success(test_client: TestClient, test_customer_id_for_accounts):
    """Test fetching transaction history for an account."""
    acc_payload = {"customer_id": test_customer_id_for_accounts, "account_type": "checking"}
    create_resp = test_client.post("/accounts/", json=acc_payload)
    account_id = create_resp.json()["account_id"]

    # Add transactions
    test_client.post("/transactions/deposit", json={"account_id": account_id, "amount": "300", "description": "History Dep1"})
    test_client.post("/transactions/deposit", json={"account_id": account_id, "amount": "150", "description": "History Dep2"})

    response = test_client.get(f"/accounts/{account_id}/transactions?limit=5")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    # Transactions are returned most recent first by core.get_transaction_history
    assert data[0]["description"] == "History Dep2"
    assert Decimal(data[0]["amount"]) == Decimal("150.00")
    assert data[1]["description"] == "History Dep1"
    assert Decimal(data[1]["amount"]) == Decimal("300.00")

```
