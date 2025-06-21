import sys
import os
from decimal import Decimal, ROUND_HALF_UP

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import execute_query, get_db_connection
# from core.account_management import get_account_by_id # For fetching current balance if needed by tests

class AccountingValidationError(Exception):
    """Base exception for accounting validation errors."""
    pass

def verify_ledger_integrity(conn=None):
    """
    Verifies the overall ledger integrity by checking if the sum of all
    transactions (debits as negative, credits as positive) is zero.

    Args:
        conn (psycopg2.connection, optional): An existing database connection.
                                             If None, a new one is created.

    Returns:
        bool: True if the ledger is balanced (sum of transactions is zero), False otherwise.
        Decimal: The sum of all transaction amounts.

    Raises:
        AccountingValidationError: If there's an issue executing the query.
    """
    query = "SELECT SUM(amount) FROM transactions;"

    _conn = conn
    try:
        if not _conn:
            _conn = get_db_connection()

        with _conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()

        # No commit needed for SELECT

        if result and result[0] is not None:
            total_sum = Decimal(result[0])
            # It's good practice to quantize to the currency's precision, e.g., 2 decimal places
            # Assuming all transactions are for currencies with 2 decimal places like USD for this check
            quantizer = Decimal("0.01")
            total_sum_quantized = total_sum.quantize(quantizer, rounding=ROUND_HALF_UP)

            if total_sum_quantized == Decimal("0.00"):
                print(f"Ledger integrity check passed. Total sum of transactions: {total_sum_quantized}")
                return True, total_sum_quantized
            else:
                print(f"Ledger integrity check FAILED. Total sum of transactions: {total_sum_quantized}")
                return False, total_sum_quantized
        else:
            # This case means there are no transactions or SUM returned NULL (empty table)
            print("Ledger integrity check: No transactions found or sum is NULL. Considered balanced.")
            return True, Decimal("0.00")

    except Exception as e:
        raise AccountingValidationError(f"Error during ledger integrity verification: {e}")
    finally:
        if not conn and _conn: # If we created a connection, we close it.
            _conn.close()


def check_account_balance_vs_transactions(account_id, conn=None):
    """
    Compares an account's current balance in the `accounts` table against
    the sum of all its transactions in the `transactions` table.

    Args:
        account_id (int): The ID of the account to check.
        conn (psycopg2.connection, optional): An existing database connection.

    Returns:
        bool: True if the balance matches the sum of transactions, False otherwise.
        Decimal: The reported balance from the accounts table.
        Decimal: The sum of transactions for the account.

    Raises:
        AccountingValidationError: If account not found or query execution fails.
    """
    reported_balance_query = "SELECT balance FROM accounts WHERE account_id = %s;"
    transactions_sum_query = "SELECT SUM(amount) FROM transactions WHERE account_id = %s;"

    _conn = conn
    try:
        if not _conn:
            _conn = get_db_connection()

        with _conn.cursor() as cur:
            # Get reported balance
            cur.execute(reported_balance_query, (account_id,))
            balance_result = cur.fetchone()
            if not balance_result:
                raise AccountingValidationError(f"Account with ID {account_id} not found.")
            reported_balance = Decimal(balance_result[0])

            # Get sum of transactions
            cur.execute(transactions_sum_query, (account_id,))
            sum_result = cur.fetchone()
            transactions_sum = Decimal(sum_result[0] if sum_result and sum_result[0] is not None else "0.00")

        # Quantize both to the same precision (e.g., 2 decimal places)
        quantizer = Decimal("0.01") # Assuming 2 decimal places for currency
        reported_balance_q = reported_balance.quantize(quantizer, rounding=ROUND_HALF_UP)
        transactions_sum_q = transactions_sum.quantize(quantizer, rounding=ROUND_HALF_UP)

        if reported_balance_q == transactions_sum_q:
            print(f"Account balance check for account {account_id} PASSED.")
            print(f"  Reported Balance: {reported_balance_q}, Sum of Transactions: {transactions_sum_q}")
            return True, reported_balance_q, transactions_sum_q
        else:
            print(f"Account balance check for account {account_id} FAILED.")
            print(f"  Reported Balance: {reported_balance_q}, Sum of Transactions: {transactions_sum_q}")
            return False, reported_balance_q, transactions_sum_q

    except Exception as e:
        raise AccountingValidationError(f"Error checking account {account_id} balance vs transactions: {e}")
    finally:
        if not conn and _conn:
            _conn.close()


if __name__ == '__main__':
    print("Running accounting_validator.py direct tests...")
    # These tests require a database with the schema applied and potentially some data.
    # For `verify_ledger_integrity`, the sum of all transactions should be 0.
    # For `check_account_balance_vs_transactions`, you need an account and its transactions.

    # It's complex to set up perfect test data here without a full testing framework
    # and control over the database state. These tests will primarily demonstrate usage
    # and might pass/fail based on the current state of your development database.

    # A good test setup would:
    # 1. Create specific customers and accounts.
    # 2. Perform a series of balanced transactions (e.g., deposits matched by transfers/withdrawals).
    # 3. Run the validation functions.
    # 4. Clean up.

    print("\n1. Verifying overall ledger integrity...")
    try:
        is_balanced, total_sum = verify_ledger_integrity()
        print(f"   Ledger balanced: {is_balanced}, Total Sum: {total_sum}")
        # In a controlled test, you'd assert is_balanced == True
    except AccountingValidationError as e:
        print(f"   Error during ledger integrity verification: {e}")
    except Exception as e:
        print(f"   Unexpected error: {e}")


    print("\n2. Checking account balance vs. transactions (example for account ID 1)...")
    # Replace '1' with an actual account_id from your database that has transactions.
    # If your DB is clean or account 1 doesn't exist/has no transactions, this will reflect that.
    test_account_id = 1 # Default account ID to test; change if needed

    # Attempt to get an account ID from existing test accounts if possible
    # This is a very basic way to find an account; real tests need fixtures.
    try:
        conn_main = get_db_connection()
        with conn_main.cursor() as cur_main:
            cur_main.execute("SELECT account_id FROM accounts ORDER BY random() LIMIT 1;") # Get any account
            res = cur_main.fetchone()
            if res:
                test_account_id = res[0]
                print(f"   Dynamically selected account ID {test_account_id} for balance check.")
            else:
                print(f"   No accounts found to test. Using default ID {test_account_id} which might fail.")
    except Exception as e_fetch:
        print(f"   Could not dynamically fetch an account ID: {e_fetch}. Using default ID {test_account_id}.")
    finally:
        if 'conn_main' in locals() and conn_main:
            conn_main.close()

    try:
        matches, reported_bal, tx_sum = check_account_balance_vs_transactions(test_account_id)
        print(f"   Account {test_account_id}: Balance matches transactions: {matches}")
        print(f"     Reported Balance: {reported_bal}, Transactions Sum: {tx_sum}")
        # In a controlled test, you'd assert matches == True
    except AccountingValidationError as e:
        print(f"   Error checking account {test_account_id}: {e}")
        if "Account with ID" in str(e) and "not found" in str(e):
             print(f"   NOTE: Account {test_account_id} does not exist. This is expected if DB is empty or ID is wrong.")
        elif "division by zero" in str(e) or "InvalidOperation" in str(e): # Can happen if balance/sum is None
             print(f"   NOTE: Possible issue with data for account {test_account_id} (e.g. NULLs where Decimals expected).")

    except Exception as e_unexpected:
        import traceback
        print(f"   An unexpected error occurred for account {test_account_id}: {e_unexpected}")
        traceback.print_exc()

    print("\nAccounting validator tests completed.")
    print("Results depend heavily on the state of your database and the test_account_id used.")
```
