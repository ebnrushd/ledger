import pytest
from fastapi.testclient import TestClient
from fastapi import status
from decimal import Decimal

from api.models import FeeRequest, FeeApplicationResponse # Assuming models are accessible

# Fixture to set up account for fee testing via API
@pytest.fixture
def fee_api_test_account(test_client: TestClient):
    """Sets up a customer and an account for fee API testing."""
    # Customer
    c_payload = {"first_name": "FeeAPI", "last_name": "User", "email": "fee.api.user@example.com"}
    c_resp = test_client.post("/customers/", json=c_payload)
    assert c_resp.status_code == status.HTTP_201_CREATED
    c_id = c_resp.json()["customer_id"]

    # Account with initial balance and overdraft limit
    acc_payload = {"customer_id": c_id, "account_type": "checking", "initial_balance": "200.00"}
    acc_resp = test_client.post("/accounts/", json=acc_payload)
    assert acc_resp.status_code == status.HTTP_201_CREATED
    acc_id = acc_resp.json()["account_id"]
    test_client.post(f"/accounts/{acc_id}/overdraft_limit", json={"limit": "50.00"})

    # Ensure fee types exist (from schema_updates.sql) - e.g., 'monthly_maintenance_fee' (5.00)
    # and 'overdraft_usage_fee' (25.00)
    return acc_id

# --- Tests for Fee API Endpoints ---

def test_apply_fee_default_amount_success(test_client: TestClient, fee_api_test_account):
    """Test applying a fee using its default amount successfully."""
    account_id = fee_api_test_account

    # Get initial balance
    acc_details_before = test_client.get(f"/accounts/{account_id}").json()
    initial_balance = Decimal(acc_details_before["balance"])

    fee_payload = {
        "account_id": account_id,
        "fee_type_name": "monthly_maintenance_fee" # Assumes default amount is 5.00
    }
    response = test_client.post("/fees/apply", json=fee_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["account_id"] == account_id
    assert data["fee_type_name"] == "monthly_maintenance_fee"
    assert Decimal(data["applied_fee_amount"]) == Decimal("5.00") # Check against known default

    acc_details_after = test_client.get(f"/accounts/{account_id}").json()
    assert Decimal(acc_details_after["balance"]) == initial_balance - Decimal("5.00")

def test_apply_fee_custom_amount_success(test_client: TestClient, fee_api_test_account):
    """Test applying a fee with a custom amount."""
    account_id = fee_api_test_account
    initial_balance = Decimal(test_client.get(f"/accounts/{account_id}").json()["balance"])
    custom_fee = Decimal("12.34")

    fee_payload = {
        "account_id": account_id,
        "fee_type_name": "wire_transfer_fee_outgoing", # Using a fee type, but overriding amount
        "fee_amount": str(custom_fee) # Send as string, Pydantic converts
    }
    response = test_client.post("/fees/apply", json=fee_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert Decimal(data["applied_fee_amount"]) == custom_fee
    acc_details_after = test_client.get(f"/accounts/{account_id}").json()
    assert Decimal(acc_details_after["balance"]) == initial_balance - custom_fee

def test_apply_fee_into_overdraft_success(test_client: TestClient, fee_api_test_account):
    """Test applying a fee that pushes the account into overdraft."""
    account_id = fee_api_test_account # Bal 200, OD 50
    initial_balance = Decimal(test_client.get(f"/accounts/{account_id}").json()["balance"]) # 200

    # Fee of 220 will push into overdraft by 20 (200 - 220 = -20)
    fee_amount_overdraft = Decimal("220.00")
    fee_payload = {
        "account_id": account_id,
        "fee_type_name": "overdraft_usage_fee", # Using a relevant fee type name
        "fee_amount": str(fee_amount_overdraft)
    }
    response = test_client.post("/fees/apply", json=fee_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert Decimal(data["applied_fee_amount"]) == fee_amount_overdraft

    acc_details_after = test_client.get(f"/accounts/{account_id}").json()
    assert Decimal(acc_details_after["balance"]) == initial_balance - fee_amount_overdraft # Expected -20

def test_apply_fee_exceeding_overdraft_fail(test_client: TestClient, fee_api_test_account):
    """Test applying a fee that exceeds the account's overdraft limit."""
    account_id = fee_api_test_account # Bal 200, OD 50. Max drawable = 250.

    # Fee of 250.01 should fail
    fee_amount_exceed = Decimal("250.01")
    fee_payload = {
        "account_id": account_id,
        "fee_type_name": "overdraft_usage_fee",
        "fee_amount": str(fee_amount_exceed)
    }
    response = test_client.post("/fees/apply", json=fee_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insufficient funds" in response.json()["detail"]


def test_apply_fee_type_not_found_fail(test_client: TestClient, fee_api_test_account):
    """Test applying a fee where the fee_type_name does not exist."""
    account_id = fee_api_test_account
    fee_payload = {"account_id": account_id, "fee_type_name": "non_existent_special_fee"}
    response = test_client.post("/fees/apply", json=fee_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Fee type 'non_existent_special_fee' not found" in response.json()["detail"]

def test_apply_fee_invalid_custom_amount_fail(test_client: TestClient, fee_api_test_account):
    """Test applying a fee with an invalid custom amount (e.g., negative)."""
    account_id = fee_api_test_account
    fee_payload = {
        "account_id": account_id,
        "fee_type_name": "monthly_maintenance_fee",
        "fee_amount": "-5.00" # Invalid: Pydantic model has gt=0
    }
    response = test_client.post("/fees/apply", json=fee_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # Pydantic validation error
```
