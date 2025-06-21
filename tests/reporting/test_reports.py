import pytest
import os
import csv
from datetime import datetime, date

# Import function to be tested
from reporting.reports import export_transactions_to_csv, ReportingError

# Import core functions for test setup
from core.account_management import open_account
from core.customer_management import add_customer
from core.transaction_processing import deposit, withdraw

# --- Test Fixtures ---
@pytest.fixture(scope="function") # Function scope to get fresh accounts for each test if needed
def setup_transactions_for_csv_export(db_conn):
    """Sets up a customer, account, and some transactions for CSV export tests."""
    customer_id = add_customer("CsvExp", "User", "csvexp.user@example.com")
    account_id = open_account(customer_id, "checking", initial_balance=200.00) # Initial balance not a transaction

    # Transactions within a known date range
    # To control timestamps precisely, we'd need to modify transaction recording or mock datetime.now().
    # For now, assume they occur "now" for testing logic, and filter by dates around "today".
    deposit(account_id, 100.00, "CSV Deposit 1") # Effective bal 300
    withdraw(account_id, 20.00, "CSV Withdraw 1") # Effective bal 280
    deposit(account_id, 50.00, "CSV Deposit 2")  # Effective bal 330

    return account_id

@pytest.fixture
def temp_csv_file_path():
    """Provides a temporary file path for CSV output and ensures cleanup."""
    # Using pytest's tmp_path fixture is often preferred for temp files in tests.
    # However, NamedTemporaryFile can also work if handled carefully.
    # Let's use a simple named approach for this example.
    folder = "temp_test_reports"
    if not os.path.exists(folder):
        os.makedirs(folder)

    file_path = os.path.join(folder, f"test_report_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.csv")
    yield file_path # Provide the path to the test
    # Cleanup: remove the file after the test
    if os.path.exists(file_path):
        os.remove(file_path)

# --- Tests for export_transactions_to_csv ---

def test_export_transactions_to_csv_all_for_account(db_conn, setup_transactions_for_csv_export, temp_csv_file_path):
    """Test exporting all transactions for a specific account within a date range."""
    account_id = setup_transactions_for_csv_export

    # Assuming transactions were just created, use today's date for start and end
    today_str = date.today().isoformat()

    export_transactions_to_csv(
        start_date_str=today_str,
        end_date_str=today_str,
        output_filepath=temp_csv_file_path,
        account_id=account_id
    )

    assert os.path.exists(temp_csv_file_path)

    with open(temp_csv_file_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        # Expect 3 transactions created by setup_transactions_for_csv_export
        assert len(rows) == 3

        # Check some data points (order might vary based on exact timestamp, so check presence)
        descriptions = {row["Description"] for row in rows}
        assert "CSV Deposit 1" in descriptions
        assert "CSV Withdraw 1" in descriptions
        assert "CSV Deposit 2" in descriptions

        amounts = {float(row["Amount"]) for row in rows} # Amount from CSV is string
        assert 100.00 in amounts
        assert -20.00 in amounts # Withdrawals are negative in transactions table
        assert 50.00 in amounts

        for row in rows:
            assert row["Account Number"] is not None # Should be populated by JOIN

def test_export_transactions_to_csv_no_transactions_found(db_conn, temp_csv_file_path, create_account_fx):
    """Test export when no transactions match the criteria."""
    account_id = create_account_fx() # Fresh account with no transactions

    export_transactions_to_csv(
        start_date_str="1990-01-01",
        end_date_str="1990-01-31",
        output_filepath=temp_csv_file_path,
        account_id=account_id
    )
    assert os.path.exists(temp_csv_file_path)
    with open(temp_csv_file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
        assert len(rows) == 1 # Only header row
        assert rows[0] == ["Transaction ID", "Timestamp", "Account Number", "Transaction Type", "Amount", "Description", "Related Account Number"]

def test_export_transactions_to_csv_date_range_filter(db_conn, setup_transactions_for_csv_export, temp_csv_file_path):
    """Test filtering by date range (hard to test precisely without controlling transaction timestamps)."""
    account_id = setup_transactions_for_csv_export

    # This test is conceptual for date filtering.
    # Precise testing would require mocking datetime or inserting transactions with specific past/future dates.
    # For now, assume all setup transactions are "today".

    # Export for "yesterday" - should be empty
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    export_transactions_to_csv(yesterday, yesterday, temp_csv_file_path, account_id)
    with open(temp_csv_file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
        assert len(rows) == 1 # Header only

    # Export for "today" - should have the 3 transactions
    today_str = date.today().isoformat()
    export_transactions_to_csv(today_str, today_str, temp_csv_file_path, account_id)
    with open(temp_csv_file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
        assert len(rows) == 3 + 1 # 3 data rows + 1 header

def test_export_transactions_to_csv_invalid_dates(db_conn, temp_csv_file_path):
    """Test export with invalid date format (should be caught by Pydantic/FastAPI in API, direct call here)."""
    # The function itself expects 'YYYY-MM-DD' and converts.
    # datetime.strptime will raise ValueError if format is wrong.
    with pytest.raises(ValueError, match="Invalid date format"):
        export_transactions_to_csv("01/02/2023", "2023-03-01", temp_csv_file_path)
    with pytest.raises(ValueError, match="Invalid date format"):
        export_transactions_to_csv("2023-01-01", "31-12-2023", temp_csv_file_path)

def test_export_transactions_to_csv_non_existent_account(db_conn, temp_csv_file_path):
    """Test export for a non-existent account_id (should produce empty CSV with headers)."""
    # The current implementation of export_transactions_to_csv doesn't explicitly check if account_id exists
    # before querying. If the account_id doesn't exist, the SQL query will simply return no rows.
    # This is acceptable behavior, resulting in an empty report.
    non_existent_account_id = 999888
    today_str = date.today().isoformat()

    export_transactions_to_csv(
        start_date_str=today_str,
        end_date_str=today_str,
        output_filepath=temp_csv_file_path,
        account_id=non_existent_account_id
    )
    assert os.path.exists(temp_csv_file_path)
    with open(temp_csv_file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
        assert len(rows) == 1 # Header only


# Need to import timedelta for test_export_transactions_to_csv_date_range_filter
from datetime import timedelta
```
