import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta

# Import function to be tested
from reporting.statements import generate_account_statement, StatementError

# Import core functions for test setup
from core.account_management import open_account, get_account_by_id
from core.customer_management import add_customer, get_customer_by_id
from core.transaction_processing import deposit, withdraw, transfer_funds

# --- Test Fixtures ---
@pytest.fixture(scope="function")
def setup_account_for_statement(db_conn):
    """
    Sets up a customer, account, and a series of transactions across a few days.
    Returns the account_id.
    Precise timestamp control is difficult without advanced mocking of `datetime.now()`
    within the transaction processing functions. These tests will assume transactions
    are recorded with the current timestamp at the moment of their execution.
    To test date filtering accurately, we'd ideally insert transactions with fixed past timestamps.
    For this fixture, we'll make transactions and then try to generate a statement for "today".
    """
    customer_id = add_customer("StmtTest", "User", "stmt.user@example.com")
    # Open account with an initial balance, but this is NOT a transaction in `transactions` table.
    # The statement's starting_balance calculation relies on sum of transactions *before* start_date.
    # So, for a clean test, let's open with 0 and then deposit.
    account_id = open_account(customer_id, "savings", initial_balance=Decimal("0.00"))

    # Day 1 transactions (conceptual, actual timestamp is "now" for each call)
    # To make this test robust for date ranges, these would need specific, different timestamps.
    # For now, we'll assume they all happen "today" for the purpose of testing statement structure.
    # If we need to test date filtering, we'd need to manually insert transactions with past dates.

    # Let's simulate transactions for a statement period covering "today"
    # All these will have today's date, but different (sequential) timestamps from DB
    deposit(account_id, Decimal("1000.00"), "Initial funding")      # Bal: 1000.00
    withdraw(account_id, Decimal("100.00"), "ATM Withdrawal")       # Bal: 900.00
    transfer_funds(account_id, 99999, Decimal("50.00"), "Mock Transfer Out") # Assuming 99999 is a dummy account not checked here
                                                                        # This will create a debit of 50. Bal: 850.00
                                                                        # Note: transfer_funds creates 2 tx entries; only one for `account_id` is relevant here.
                                                                        # The other leg to 99999 is ignored by statement for `account_id`.
                                                                        # For simplicity, let's use deposit/withdraw which are cleaner one-leggers for statement.
    deposit(account_id, Decimal("200.00"), "Salary deposit")        # Bal: 1050.00 (if previous was 850)
                                                                        # Corrected flow for simpler statement:
                                                                        # 0. Open with 0.
                                                                        # 1. Deposit 1000. Bal 1000. Running Bal 1000.
                                                                        # 2. Withdraw 100. Bal 900. Running Bal 900.
                                                                        # 3. Deposit 200. Bal 1100. Running Bal 1100.
    # For simplicity of this test, let's re-do transactions without the complex transfer
    # The db_conn fixture clears tables, so these are the only transactions for this account_id in this test.
    # Clean slate due to db_conn fixture.
    new_account_id = open_account(customer_id, "savings", initial_balance=Decimal("0.00"))
    deposit(new_account_id, Decimal("1000.00"), "Initial funding")
    withdraw(new_account_id, Decimal("100.00"), "ATM Withdrawal")
    deposit(new_account_id, Decimal("200.00"), "Salary deposit")

    return new_account_id


# --- Tests for generate_account_statement ---

def test_generate_account_statement_success(db_conn, setup_account_for_statement):
    """Test generating a valid account statement for today's transactions."""
    account_id = setup_account_for_statement

    today_str = date.today().isoformat()

    statement_data = generate_account_statement(account_id, today_str, today_str)

    assert statement_data is not None
    acc_info = get_account_by_id(account_id) # Fetch current details for comparison
    cust_info = get_customer_by_id(acc_info["customer_id"])

    # Verify account and customer info
    assert statement_data["account_info"]["account_number"] == acc_info["account_number"]
    assert statement_data["customer_info"]["customer_id"] == cust_info["customer_id"]
    assert statement_data["period"]["start_date"] == today_str
    assert statement_data["period"]["end_date"] == today_str

    # Verify transactions (3 transactions made in setup_account_for_statement)
    assert len(statement_data["transactions"]) == 3

    # Transaction details and running balance:
    # 1. Deposit 1000.00. Running Bal: 1000.00
    # 2. Withdraw 100.00. Running Bal: 900.00
    # 3. Deposit 200.00. Running Bal: 1100.00

    # Starting balance for "today" should be 0 as all transactions are "today"
    # and _calculate_starting_balance sums transactions *before* start_date.
    assert statement_data["starting_balance"] == Decimal("0.00")

    tx1 = statement_data["transactions"][0]
    assert tx1["description"] == "Initial funding"
    assert tx1["amount"] == Decimal("1000.00")
    assert tx1["credit"] == Decimal("1000.00")
    assert tx1["debit"] == Decimal("0.00")
    assert tx1["running_balance"] == Decimal("1000.00")

    tx2 = statement_data["transactions"][1]
    assert tx2["description"] == "ATM Withdrawal"
    assert tx2["amount"] == Decimal("-100.00")
    assert tx2["credit"] == Decimal("0.00")
    assert tx2["debit"] == Decimal("100.00")
    assert tx2["running_balance"] == Decimal("900.00")

    tx3 = statement_data["transactions"][2]
    assert tx3["description"] == "Salary deposit"
    assert tx3["amount"] == Decimal("200.00")
    assert tx3["credit"] == Decimal("200.00")
    assert tx3["debit"] == Decimal("0.00")
    assert tx3["running_balance"] == Decimal("1100.00")

    assert statement_data["ending_balance"] == Decimal("1100.00")
    # Verify this matches the current actual balance in DB
    assert get_account_balance(account_id) == Decimal("1100.00")


def test_generate_account_statement_no_transactions_in_period(db_conn, setup_account_for_statement):
    """Test statement for a period with no transactions."""
    account_id = setup_account_for_statement # This account has transactions today.

    # Choose a date range in the past where no transactions exist for this account
    past_start_date = (date.today() - timedelta(days=10)).isoformat()
    past_end_date = (date.today() - timedelta(days=5)).isoformat()

    statement_data = generate_account_statement(account_id, past_start_date, past_end_date)

    assert statement_data is not None
    assert len(statement_data["transactions"]) == 0
    # Starting balance for a past period for an account created "today" should be 0
    assert statement_data["starting_balance"] == Decimal("0.00")
    assert statement_data["ending_balance"] == Decimal("0.00") # No transactions in period, so SB = EB

def test_generate_account_statement_date_range_spans_transactions(db_conn):
    """
    More complex test for date ranges. This requires inserting transactions with specific past dates.
    This is harder to do without direct DB manipulation or mocking `datetime.now()` in core functions.
    Conceptual:
    - Create account.
    - Manually insert transaction for Day 1.
    - Manually insert transaction for Day 2.
    - Manually insert transaction for Day 3.
    - Generate statement for Day 2 to Day 2. Expected: SB based on Day 1, 1 transaction, EB.
    - Generate statement for Day 1 to Day 3. Expected: SB=0 (if no prior tx), 3 transactions, EB.
    For now, this test will be simplified due to timestamping complexities.
    """
    # This test will be skipped or simplified as it requires more control over timestamps
    # than currently available through the core functions alone for robust testing.
    # We can test if _calculate_starting_balance works conceptually.
    customer_id = add_customer("StmtRange", "User", "stmtrange.user@example.com")
    account_id = open_account(customer_id, "checking", initial_balance=Decimal("0.00"))

    # Manually insert transactions with specific past timestamps
    with db_conn.cursor() as cur:
        ts_day1 = datetime.now() - timedelta(days=2)
        ts_day2 = datetime.now() - timedelta(days=1)

        # Get transaction type IDs
        cur.execute("SELECT transaction_type_id FROM transaction_types WHERE type_name = 'deposit';")
        deposit_type_id = cur.fetchone()[0]

        cur.execute("INSERT INTO transactions (account_id, transaction_type_id, amount, description, transaction_timestamp) VALUES (%s, %s, %s, %s, %s);",
                    (account_id, deposit_type_id, Decimal("100.00"), "Past Dep Day 1", ts_day1))
        cur.execute("INSERT INTO transactions (account_id, transaction_type_id, amount, description, transaction_timestamp) VALUES (%s, %s, %s, %s, %s);",
                    (account_id, deposit_type_id, Decimal("200.00"), "Past Dep Day 2", ts_day2))
        db_conn.commit()
        # Update account balance to reflect these manual insertions for consistency,
        # though generate_account_statement calculates balances from transactions.
        cur.execute("UPDATE accounts SET balance = balance + 300.00 WHERE account_id = %s;", (account_id,))
        db_conn.commit()

    # Statement for Day 2 only
    day2_str = (date.today() - timedelta(days=1)).isoformat()
    statement_day2 = generate_account_statement(account_id, day2_str, day2_str)

    assert statement_day2["starting_balance"] == Decimal("100.00") # From Day 1 deposit
    assert len(statement_day2["transactions"]) == 1
    assert statement_day2["transactions"][0]["description"] == "Past Dep Day 2"
    assert statement_day2["transactions"][0]["amount"] == Decimal("200.00")
    assert statement_day2["ending_balance"] == Decimal("300.00") # 100 (SB) + 200 (Tx)

def test_generate_statement_invalid_dates(db_conn, setup_account_for_statement):
    """Test statement generation with invalid date formats."""
    account_id = setup_account_for_statement
    with pytest.raises(ValueError, match="Invalid date format"):
        generate_account_statement(account_id, "01/01/2023", date.today().isoformat()) # Incorrect start_date format
    with pytest.raises(ValueError, match="Invalid date format"):
        generate_account_statement(account_id, date.today().isoformat(), "12-31-2023") # Incorrect end_date format

def test_generate_statement_non_existent_account(db_conn):
    """Test statement for a non-existent account."""
    with pytest.raises(AccountNotFoundError):
        generate_account_statement(999777, date.today().isoformat(), date.today().isoformat())

# Test print_statement_to_console (basic run, visual check or capture stdout if needed)
def test_print_statement_to_console(capsys, setup_account_for_statement):
    from reporting.statements import print_statement_to_console # Import here
    account_id = setup_account_for_statement
    today_str = date.today().isoformat()
    statement_data = generate_account_statement(account_id, today_str, today_str)

    print_statement_to_console(statement_data)
    captured = capsys.readouterr()
    assert "ACCOUNT STATEMENT" in captured.out
    assert "Initial funding" in captured.out # Check for one of the transactions
    assert "Ending Balance" in captured.out
```
