import pytest
from fastapi.testclient import TestClient
from fastapi import status
from decimal import Decimal

from api.models import ( # Assuming models are accessible via api.models
    DepositRequest, WithdrawalRequest, TransferRequest,
    ACHTransactionRequest, WireTransactionRequest,
    TransactionDetails, TransferResponse
)

# Fixture to set up accounts for transaction testing
@pytest.fixture
def setup_api_accounts(test_client: TestClient):
    """Sets up two customers and one account for each via API calls."""
    # Customer 1 and Account 1
    c1_payload = {"first_name": "TxAPI_C1", "last_name": "User", "email": "txapi.c1@example.com"}
    c1_resp = test_client.post("/customers/", json=c1_payload)
    assert c1_resp.status_code == status.HTTP_201_CREATED
    c1_id = c1_resp.json()["customer_id"]

    acc1_payload = {"customer_id": c1_id, "account_type": "checking", "initial_balance": "1000.00"}
    acc1_resp = test_client.post("/accounts/", json=acc1_payload)
    assert acc1_resp.status_code == status.HTTP_201_CREATED
    acc1_id = acc1_resp.json()["account_id"]
    test_client.post(f"/accounts/{acc1_id}/overdraft_limit", json={"limit": "100.00"}) # Overdraft limit of 100

    # Customer 2 and Account 2
    c2_payload = {"first_name": "TxAPI_C2", "last_name": "User", "email": "txapi.c2@example.com"}
    c2_resp = test_client.post("/customers/", json=c2_payload)
    c2_id = c2_resp.json()["customer_id"]

    acc2_payload = {"customer_id": c2_id, "account_type": "savings", "initial_balance": "500.00"}
    acc2_resp = test_client.post("/accounts/", json=acc2_payload)
    acc2_id = acc2_resp.json()["account_id"]

    return acc1_id, acc2_id

# --- Tests for Transaction API Endpoints ---

def test_deposit_success(test_client: TestClient, setup_api_accounts):
    acc1_id, _ = setup_api_accounts
    deposit_payload = {"account_id": acc1_id, "amount": "150.50", "description": "API Deposit"}

    response = test_client.post("/transactions/deposit", json=deposit_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["account_id"] == acc1_id
    assert Decimal(data["amount"]) == Decimal("150.50")
    assert data["description"] == "API Deposit"
    # Verify balance (requires fetching account details)
    acc_resp = test_client.get(f"/accounts/{acc1_id}")
    assert Decimal(acc_resp.json()["balance"]) == Decimal("1000.00") + Decimal("150.50")

def test_deposit_invalid_amount_fail(test_client: TestClient, setup_api_accounts):
    acc1_id, _ = setup_api_accounts
    deposit_payload = {"account_id": acc1_id, "amount": "-50.00"} # Negative amount
    response = test_client.post("/transactions/deposit", json=deposit_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # Pydantic validation (gt=0)

def test_deposit_to_non_existent_account_fail(test_client: TestClient):
    deposit_payload = {"account_id": 999111, "amount": "100.00"}
    response = test_client.post("/transactions/deposit", json=deposit_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_withdraw_success(test_client: TestClient, setup_api_accounts):
    acc1_id, _ = setup_api_accounts # Bal 1000, OD 100
    withdraw_payload = {"account_id": acc1_id, "amount": "200.00", "description": "API Withdrawal"}

    response = test_client.post("/transactions/withdraw", json=withdraw_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["account_id"] == acc1_id
    assert Decimal(data["amount"]) == Decimal("-200.00") # Withdrawals are negative

    acc_resp = test_client.get(f"/accounts/{acc1_id}")
    assert Decimal(acc_resp.json()["balance"]) == Decimal("1000.00") - Decimal("200.00")

def test_withdraw_into_overdraft_success(test_client: TestClient, setup_api_accounts):
    acc1_id, _ = setup_api_accounts # Bal 1000, OD 100
    # Withdraw 1050, should result in -50 balance
    withdraw_payload = {"account_id": acc1_id, "amount": "1050.00", "description": "API Overdraft Withdrawal"}
    response = test_client.post("/transactions/withdraw", json=withdraw_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert Decimal(data["amount"]) == Decimal("-1050.00")

    acc_resp = test_client.get(f"/accounts/{acc1_id}")
    assert Decimal(acc_resp.json()["balance"]) == Decimal("-50.00")

def test_withdraw_insufficient_funds_fail(test_client: TestClient, setup_api_accounts):
    acc1_id, _ = setup_api_accounts # Bal 1000, OD 100. Max drawable = 1100.
    withdraw_payload = {"account_id": acc1_id, "amount": "1100.01"}
    response = test_client.post("/transactions/withdraw", json=withdraw_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insufficient funds" in response.json()["detail"]


def test_transfer_funds_success(test_client: TestClient, setup_api_accounts):
    acc1_id, acc2_id = setup_api_accounts # A1:1000, A2:500
    transfer_payload = {
        "from_account_id": acc1_id,
        "to_account_id": acc2_id,
        "amount": "300.00",
        "description": "API Transfer"
    }
    response = test_client.post("/transactions/transfer", json=transfer_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "debit_transaction" in data
    assert "credit_transaction" in data
    assert Decimal(data["debit_transaction"]["amount"]) == Decimal("-300.00")
    assert Decimal(data["credit_transaction"]["amount"]) == Decimal("300.00")

    acc1_resp = test_client.get(f"/accounts/{acc1_id}")
    assert Decimal(acc1_resp.json()["balance"]) == Decimal("1000.00") - Decimal("300.00")
    acc2_resp = test_client.get(f"/accounts/{acc2_id}")
    assert Decimal(acc2_resp.json()["balance"]) == Decimal("500.00") + Decimal("300.00")

def test_transfer_insufficient_funds_fail(test_client: TestClient, setup_api_accounts):
    acc1_id, acc2_id = setup_api_accounts # A1:1000, OD 100. Max debit = 1100
    transfer_payload = {"from_account_id": acc1_id, "to_account_id": acc2_id, "amount": "1100.01"}
    response = test_client.post("/transactions/transfer", json=transfer_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insufficient funds" in response.json()["detail"]

def test_transfer_to_same_account_fail(test_client: TestClient, setup_api_accounts):
    acc1_id, _ = setup_api_accounts
    transfer_payload = {"from_account_id": acc1_id, "to_account_id": acc1_id, "amount": "50.00"}
    response = test_client.post("/transactions/transfer", json=transfer_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST # Handled by API router logic
    assert "Cannot transfer to the same account" in response.json()["detail"]


@pytest.mark.parametrize("ach_type, amount_sign", [("credit", 1), ("debit", -1)])
def test_ach_transaction_success(test_client: TestClient, setup_api_accounts, ach_type, amount_sign):
    acc_id, _ = setup_api_accounts # Bal 1000
    ach_amount_str = "75.25"
    ach_payload = {
        "account_id": acc_id,
        "amount": ach_amount_str,
        "ach_type": ach_type,
        "description": f"API ACH {ach_type}"
    }
    response = test_client.post("/transactions/ach", json=ach_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert Decimal(data["amount"]) == amount_sign * Decimal(ach_amount_str)

    acc_resp = test_client.get(f"/accounts/{acc_id}")
    expected_balance = Decimal("1000.00") + (amount_sign * Decimal(ach_amount_str))
    assert Decimal(acc_resp.json()["balance"]) == expected_balance


@pytest.mark.parametrize("direction, amount_sign", [("incoming", 1), ("outgoing", -1)])
def test_wire_transaction_success(test_client: TestClient, setup_api_accounts, direction, amount_sign):
    acc_id, _ = setup_api_accounts # Bal 1000
    wire_amount_str = "120.00"
    wire_payload = {
        "account_id": acc_id,
        "amount": wire_amount_str,
        "direction": direction,
        "description": f"API Wire {direction}"
    }
    response = test_client.post("/transactions/wire", json=wire_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert Decimal(data["amount"]) == amount_sign * Decimal(wire_amount_str)

    acc_resp = test_client.get(f"/accounts/{acc_id}")
    expected_balance = Decimal("1000.00") + (amount_sign * Decimal(wire_amount_str))
    assert Decimal(acc_resp.json()["balance"]) == expected_balance

```
