import pytest
from fastapi.testclient import TestClient
from fastapi import status
import csv
import io
from datetime import date, timedelta

# Assuming conftest.py provides test_client fixture
# No specific Pydantic models needed for request if using query params,
# and response is FileResponse.

@pytest.fixture
def setup_transactions_for_csv_api_report(test_client: TestClient):
    """
    Sets up a customer, account, and some transactions via API calls
    for testing CSV report generation.
    """
    # Customer
    c_payload = {"first_name": "CsvApi", "last_name": "User", "email": "csv.api.user@example.com"}
    c_resp = test_client.post("/customers/", json=c_payload)
    assert c_resp.status_code == status.HTTP_201_CREATED
    c_id = c_resp.json()["customer_id"]

    # Account
    acc_payload = {"customer_id": c_id, "account_type": "checking", "initial_balance": "500.00"}
    acc_resp = test_client.post("/accounts/", json=acc_payload)
    assert acc_resp.status_code == status.HTTP_201_CREATED
    account_id = acc_resp.json()["account_id"]

    # Transactions (ensure these happen "today" for simple date filtering in tests)
    trans1_payload = {"account_id": account_id, "amount": "150.00", "description": "CSV API Deposit 1"}
    resp_t1 = test_client.post("/transactions/deposit", json=trans1_payload)
    assert resp_t1.status_code == status.HTTP_201_CREATED

    trans2_payload = {"account_id": account_id, "amount": "25.50", "description": "CSV API Withdraw 1"}
    resp_t2 = test_client.post("/transactions/withdraw", json=trans2_payload)
    assert resp_t2.status_code == status.HTTP_201_CREATED

    return account_id

# --- Tests for Report API Endpoints ---

def test_export_transactions_csv_success_for_account(test_client: TestClient, setup_transactions_for_csv_api_report):
    """Test successfully exporting transactions to CSV for a specific account."""
    account_id = setup_transactions_for_csv_api_report

    today_str = date.today().isoformat()
    params = {
        "start_date": today_str,
        "end_date": today_str,
        "account_id": account_id
    }
    response = test_client.get("/reports/transactions/csv", params=params)

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=" in response.headers["content-disposition"] # Check for download hint

    # Parse CSV content
    csv_content = response.content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    assert len(rows) == 2 # Two transactions were made for this account today

    descriptions = {row["Description"] for row in rows}
    assert "CSV API Deposit 1" in descriptions
    assert "CSV API Withdraw 1" in descriptions

    amounts = {float(row["Amount"]) for row in rows}
    assert 150.00 in amounts
    assert -25.50 in amounts # Withdrawals are negative

def test_export_transactions_csv_all_accounts_in_range(test_client: TestClient, setup_transactions_for_csv_api_report):
    """Test exporting transactions for all accounts within a date range."""
    # This test assumes setup_transactions_for_csv_api_report created some transactions today.
    # To be more robust, it could create transactions for multiple accounts.
    # For now, it will find transactions for the one account created by the fixture.

    today_str = date.today().isoformat()
    params = {
        "start_date": today_str,
        "end_date": today_str
        # No account_id, so should fetch for all (or at least for the one with txns today)
    }
    response = test_client.get("/reports/transactions/csv", params=params)

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    csv_content = response.content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    # Should find at least the 2 transactions from setup_transactions_for_csv_api_report
    assert len(rows) >= 2
    # Verify some content if possible, e.g. look for known descriptions
    # This becomes more complex if other tests are adding transactions in parallel without full isolation.
    # The conftest.py db_conn fixture (function-scoped) *should* clear tables before each test,
    # so only transactions from the current test's setup fixture should be present.
    descriptions = {row["Description"] for row in rows}
    assert "CSV API Deposit 1" in descriptions
    assert "CSV API Withdraw 1" in descriptions


def test_export_transactions_csv_no_transactions_found(test_client: TestClient):
    """Test CSV export when no transactions match the criteria."""
    # Use a date range where no transactions are expected
    far_past_start = "1980-01-01"
    far_past_end = "1980-01-31"
    params = {"start_date": far_past_start, "end_date": far_past_end}

    response = test_client.get("/reports/transactions/csv", params=params)
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    csv_content = response.content.decode('utf-8')
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    assert len(rows) == 1 # Header row only
    assert rows[0] == ["Transaction ID", "Timestamp", "Account Number", "Transaction Type", "Amount", "Description", "Related Account Number"]

def test_export_transactions_csv_invalid_date_params(test_client: TestClient):
    """Test CSV export with missing or invalid date parameters."""
    # Missing end_date
    response_missing_date = test_client.get("/reports/transactions/csv?start_date=2023-01-01")
    assert response_missing_date.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # FastAPI validation

    # Invalid date format
    response_invalid_format = test_client.get("/reports/transactions/csv?start_date=01/01/2023&end_date=2023-01-31")
    assert response_invalid_format.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
```
