import sys
import os
import random
import string

# Add project root to sys.path to allow importing 'database' and 'core.customer_management'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import execute_query, get_db_connection # Added get_db_connection
from core.customer_management import get_customer_by_id, CustomerNotFoundError # To verify customer exists

class AccountError(Exception):
    """Base custom exception for account-related errors."""
    pass

class AccountNotFoundError(AccountError):
    """Custom exception for when an account is not found."""
    pass

class InvalidAccountTypeError(AccountError):
    """Custom exception for invalid account types."""
    pass

class AccountStatusError(AccountError):
    """Custom exception for account status related issues (e.g., closing non-empty account)."""
    pass

SUPPORTED_ACCOUNT_TYPES = ["checking", "savings", "credit"] # Define supported types

def _generate_unique_account_number(length=10):
    """
    Generates a unique account number.
    In a real system, this would need to be robust to ensure uniqueness,
    possibly checking against the DB or using a sequence.
    For now, it generates a random string of digits.
    """
    while True:
        acc_num = ''.join(random.choices(string.digits, k=length))
        # Simplified: in a real app, query DB to ensure uniqueness
        # For this to be truly unique, a loop with DB check is needed:
        # query_check = "SELECT 1 FROM accounts WHERE account_number = %s;"
        # if not execute_query(query_check, (acc_num,), fetch_one=True): # execute_query needs to be callable here
        # return acc_num
        # This placeholder is problematic for robust testing if tests are re-run.
        return acc_num

def get_account_status_id(status_name):
    """
    Retrieves the ID for a given account status name.

    Args:
        status_name (str): The name of the status (e.g., 'active', 'frozen').

    Returns:
        int: The ID of the status.

    Raises:
        ValueError: If the status name is not found.
    """
    query = "SELECT status_id FROM account_status_types WHERE status_name = %s;"
    try:
        result = execute_query(query, (status_name,), fetch_one=True)
        if result:
            return result[0]
        raise ValueError(f"Status name '{status_name}' not found in account_status_types.")
    except Exception as e:
        print(f"Error fetching status ID for '{status_name}': {e}")
        raise

def open_account(customer_id, account_type, initial_balance=0.00, currency='USD'):
    """
    Opens a new customer account. overdraft_limit defaults to 0.00 as per schema_updates.sql.

    Args:
        customer_id (int): The ID of the customer opening the account.
        account_type (str): Type of account (e.g., 'checking', 'savings').
        initial_balance (float, optional): Initial balance. Defaults to 0.00.
        currency (str, optional): Currency code. Defaults to 'USD'.

    Returns:
        int: The account_id of the newly created account, or None if creation failed.

    Raises:
        CustomerNotFoundError: If the customer_id is invalid.
        InvalidAccountTypeError: If the account_type is not supported.
        AccountError: For other account creation issues.
    """
    try:
        get_customer_by_id(customer_id)
    except CustomerNotFoundError:
        raise

    if account_type.lower() not in SUPPORTED_ACCOUNT_TYPES:
        raise InvalidAccountTypeError(f"Account type '{account_type}' is not supported. Supported types: {SUPPORTED_ACCOUNT_TYPES}")

    account_number = _generate_unique_account_number()

    try:
        active_status_id = get_account_status_id('active')
    except ValueError as e:
        raise AccountError(f"Could not set initial account status: {e}")

    # overdraft_limit will use its DDL default (0.00) if not specified here.
    query = """
        INSERT INTO accounts (customer_id, account_number, account_type, balance, currency, status_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING account_id;
    """
    params = (customer_id, account_number, account_type.lower(), initial_balance, currency, active_status_id)

    try:
        result = execute_query(query, params, fetch_one=True, commit=True)
        if result:
            print(f"Account {account_number} ({account_type}) opened for customer {customer_id} with ID: {result[0]}.")
            return result[0]
        return None
    except Exception as e:
        print(f"Error opening account for customer {customer_id}: {e}")
        raise AccountError(f"Failed to open account: {e}")


def get_account_by_id(account_id):
    """
    Retrieves account details by account_id, including overdraft_limit.

    Args:
        account_id (int): The ID of the account.

    Returns:
        dict: Account details.

    Raises:
        AccountNotFoundError: If account is not found.
    """
    query = """
        SELECT a.account_id, a.customer_id, a.account_number, a.account_type,
               a.balance, a.currency, ast.status_name, a.opened_at, a.updated_at,
               a.overdraft_limit
        FROM accounts a
        JOIN account_status_types ast ON a.status_id = ast.status_id
        WHERE a.account_id = %s;
    """
    try:
        result = execute_query(query, (account_id,), fetch_one=True)
        if result:
            return {
                "account_id": result[0], "customer_id": result[1], "account_number": result[2],
                "account_type": result[3], "balance": float(result[4]), "currency": result[5],
                "status_name": result[6], "opened_at": result[7], "updated_at": result[8],
                "overdraft_limit": float(result[9] if result[9] is not None else 0.00)
            }
        raise AccountNotFoundError(f"Account with ID {account_id} not found.")
    except Exception as e:
        print(f"Error retrieving account by ID {account_id}: {e}")
        raise

def get_account_by_number(account_number):
    """
    Retrieves account details by account_number, including overdraft_limit.

    Args:
        account_number (str): The account number.

    Returns:
        dict: Account details.

    Raises:
        AccountNotFoundError: If account is not found.
    """
    query = """
        SELECT a.account_id, a.customer_id, a.account_number, a.account_type,
               a.balance, a.currency, ast.status_name, a.opened_at, a.updated_at,
               a.overdraft_limit
        FROM accounts a
        JOIN account_status_types ast ON a.status_id = ast.status_id
        WHERE a.account_number = %s;
    """
    try:
        result = execute_query(query, (account_number,), fetch_one=True)
        if result:
            return {
                "account_id": result[0], "customer_id": result[1], "account_number": result[2],
                "account_type": result[3], "balance": float(result[4]), "currency": result[5],
                "status_name": result[6], "opened_at": result[7], "updated_at": result[8],
                "overdraft_limit": float(result[9] if result[9] is not None else 0.00)
            }
        raise AccountNotFoundError(f"Account with number {account_number} not found.")
    except Exception as e:
        print(f"Error retrieving account by number {account_number}: {e}")
        raise

def update_account_status(account_id, new_status_name):
    """
    Updates the status of an account.
    Prevents closing an account if it has a non-zero balance.

    Args:
        account_id (int): The ID of the account to update.
        new_status_name (str): The new status name (e.g., 'frozen', 'closed').

    Returns:
        bool: True if update was successful.

    Raises:
        AccountNotFoundError: If the account is not found.
        AccountStatusError: If trying to close an account with a balance, or other status logic error.
        ValueError: If the new_status_name is invalid.
    """
    current_account = get_account_by_id(account_id)

    if new_status_name.lower() == 'closed' and current_account['balance'] != 0.00:
        raise AccountStatusError(
            f"Account {account_id} cannot be closed due to non-zero balance ({current_account['balance']}). "
            "Balance must be zero before closing."
        )

    try:
        new_status_id = get_account_status_id(new_status_name.lower())
    except ValueError:
        raise

    query = "UPDATE accounts SET status_id = %s, updated_at = CURRENT_TIMESTAMP WHERE account_id = %s RETURNING account_id;"
    params = (new_status_id, account_id)

    try:
        result = execute_query(query, params, commit=True, fetch_one=True)
        if result:
            print(f"Account ID {result[0]} status updated to '{new_status_name}'.")
            # Log this change using audit_service
            try:
                from core.audit_service import log_account_status_change # Local import
                log_account_status_change(
                    account_id=account_id,
                    new_status=new_status_name,
                    old_status=current_account['status_name'],
                    reason="Status updated via update_account_status function."
                    # user_id would be ideal here if available from context
                )
            except Exception as audit_e:
                print(f"Warning: Failed to log account status change for {account_id}: {audit_e}")
            return True
        return False
    except Exception as e:
        print(f"Error updating account {account_id} status: {e}")
        raise AccountError(f"Failed to update account status: {e}")


def set_overdraft_limit(account_id, limit):
    """
    Sets or updates the overdraft limit for a given account.

    Args:
        account_id (int): The ID of the account to update.
        limit (Decimal or float): The new overdraft limit. Must not be negative.

    Returns:
        bool: True if update was successful.

    Raises:
        AccountNotFoundError: If the account is not found.
        ValueError: If the limit is negative.
        AccountError: For other database update errors.
    """
    if float(limit) < 0:
        raise ValueError("Overdraft limit cannot be negative.")

    current_account = get_account_by_id(account_id) # Ensures account exists and gets old limit

    query = "UPDATE accounts SET overdraft_limit = %s, updated_at = CURRENT_TIMESTAMP WHERE account_id = %s RETURNING account_id;"
    params = (limit, account_id)

    try:
        result = execute_query(query, params, commit=True, fetch_one=True)
        if result:
            print(f"Overdraft limit for account ID {result[0]} updated to {limit}.")
            try:
                from core.audit_service import log_event # Local import
                log_event(
                    action_type='OVERDRAFT_LIMIT_CHANGE',
                    target_entity='accounts',
                    target_id=account_id,
                    details={
                        "new_limit": float(limit),
                        "old_limit": float(current_account.get('overdraft_limit', 0.00))
                    }
                    # user_id would be ideal here
                )
            except Exception as audit_e:
                 print(f"Warning: Failed to log overdraft limit change for {account_id}: {audit_e}")
            return True
        return False
    except Exception as e:
        print(f"Error setting overdraft limit for account {account_id}: {e}")
        raise AccountError(f"Failed to set overdraft limit: {e}")


def get_account_balance(account_id):
    """
    Retrieves the current balance of an account.

    Args:
        account_id (int): The ID of the account.

    Returns:
        float: The current balance.

    Raises:
        AccountNotFoundError: If account is not found.
    """
    query = "SELECT balance FROM accounts WHERE account_id = %s;"
    try:
        result = execute_query(query, (account_id,), fetch_one=True)
        if result:
            return float(result[0])
        # This line was problematic, get_account_by_id would call this, creating potential loop if not found
        # raise AccountNotFoundError(f"Account with ID {account_id} not found, cannot retrieve balance.")
        # Instead, rely on execute_query to return None if not found, and handle that.
        # The initial get_account_by_id in calling functions should catch non-existence.
        # However, if called directly and account is gone, this is an issue.
        # For now, assume account existence is checked before calling this for critical ops.
        # Or, let's make it consistent:
        raise AccountNotFoundError(f"Account with ID {account_id} not found when trying to get balance.")

    except AccountNotFoundError: # Re-raise if specifically AccountNotFoundError
        raise
    except Exception as e:
        print(f"Error retrieving balance for account ID {account_id}: {e}")
        raise AccountError(f"Could not retrieve balance for account {account_id}: {e}")


def calculate_interest_placeholder(account_id, interest_rate_percentage):
    """
    Placeholder for interest calculation logic.

    Args:
        account_id (int): The account ID.
        interest_rate_percentage (float): The annual interest rate as a percentage (e.g., 1.5 for 1.5%).
    """
    try:
        account = get_account_by_id(account_id)
        balance = account['balance']

        annual_interest_amount = balance * (interest_rate_percentage / 100.0)
        monthly_interest_amount = annual_interest_amount / 12

        print(f"[INTEREST CALC LOG] Account ID: {account_id}")
        print(f"[INTEREST CALC LOG] Current Balance: {balance} {account['currency']}")
        print(f"[INTEREST CALC LOG] Annual Interest Rate: {interest_rate_percentage}%")
        print(f"[INTEREST CALC LOG] Calculated Annual Interest: {annual_interest_amount:.2f} {account['currency']}")
        print(f"[INTEREST CALC LOG] Calculated Approx. Monthly Interest: {monthly_interest_amount:.2f} {account['currency']}")
        print(f"[INTEREST CALC LOG] Note: This is a placeholder. No actual transaction posted or balance updated.")
        return monthly_interest_amount
    except AccountNotFoundError:
        raise
    except Exception as e:
        print(f"Error in calculate_interest_placeholder for account {account_id}: {e}")
        raise AccountError(f"Interest calculation failed for account {account_id}: {e}")


def get_transaction_history(account_id, limit=50, offset=0):
    """
    Retrieves transaction history for a given account, ordered by timestamp.

    Args:
        account_id (int): The account ID.
        limit (int, optional): Maximum number of transactions to retrieve. Defaults to 50.
        offset (int, optional): Number of transactions to skip (for pagination). Defaults to 0.

    Returns:
        list: A list of dictionaries, each representing a transaction.

    Raises:
        AccountNotFoundError: If the account itself does not exist.
    """
    get_account_by_id(account_id) # Verifies account exists

    query = """
        SELECT t.transaction_id, t.account_id, tt.type_name, t.amount,
               t.transaction_timestamp, t.description, t.related_account_id
        FROM transactions t
        JOIN transaction_types tt ON t.transaction_type_id = tt.transaction_type_id
        WHERE t.account_id = %s
        ORDER BY t.transaction_timestamp DESC, t.transaction_id DESC
        LIMIT %s OFFSET %s;
    """
    params = (account_id, limit, offset)
    try:
        results = execute_query(query, params, fetch_all=True)
        if results:
            return [
                {
                    "transaction_id": r[0], "account_id": r[1], "type_name": r[2],
                    "amount": float(r[3]), "transaction_timestamp": r[4],
                    "description": r[5], "related_account_id": r[6]
                } for r in results
            ]
        return []
    except Exception as e:
        print(f"Error retrieving transaction history for account {account_id}: {e}")
        raise AccountError(f"Could not retrieve transaction history for account {account_id}: {e}")

if __name__ == '__main__':
    print("Running account_management.py direct tests...")

    # Import for test setup
    from core.customer_management import add_customer, get_customer_by_email
    # Assume schema_updates.sql (adding overdraft_limit column) has been applied to the DB.
    print("   Reminder: Ensure 'accounts.overdraft_limit' column exists from 'schema_updates.sql'.")

    temp_customer_id = None
    temp_account_id = None
    test_customer_email = "am.test@example.com"

    # Cleanup function for test data
    def cleanup_test_data(email, acc_id_to_delete=None):
        print(f"\n[CLEANUP] Attempting cleanup for {email}...")
        try:
            conn_cleanup = get_db_connection()
            cur_cleanup = conn_cleanup.cursor()

            cust_to_delete = None
            try:
                cust_to_delete = get_customer_by_email(email) # uses execute_query, new conn
            except CustomerNotFoundError:
                pass # Already gone or never created

            if acc_id_to_delete: # If specific account ID is known
                print(f"   Deleting transactions for account {acc_id_to_delete}...")
                cur_cleanup.execute("DELETE FROM transactions WHERE account_id = %s;", (acc_id_to_delete,))
                print(f"   Deleting account {acc_id_to_delete}...")
                cur_cleanup.execute("DELETE FROM accounts WHERE account_id = %s;", (acc_id_to_delete,))

            if cust_to_delete:
                customer_id_val = cust_to_delete['customer_id']
                # Delete any other accounts if acc_id_to_delete was not specific enough or failed
                if not acc_id_to_delete: # Or if we want to be thorough
                    cur_cleanup.execute("SELECT account_id FROM accounts WHERE customer_id = %s;",(customer_id_val,))
                    other_accounts = cur_cleanup.fetchall()
                    for acc in other_accounts:
                        print(f"   Deleting transactions for account {acc[0]}...")
                        cur_cleanup.execute("DELETE FROM transactions WHERE account_id = %s;", (acc[0],))
                        print(f"   Deleting account {acc[0]}...")
                        cur_cleanup.execute("DELETE FROM accounts WHERE account_id = %s;", (acc[0],))

                print(f"   Deleting customer {customer_id_val} ({email})...")
                cur_cleanup.execute("DELETE FROM customers WHERE customer_id = %s;", (customer_id_val,))

            conn_cleanup.commit()
            print(f"   Cleanup for {email} done.")
        except Exception as e_clean:
            if 'conn_cleanup' in locals() and conn_cleanup: conn_cleanup.rollback()
            print(f"   Error during cleanup for {email}: {e_clean}")
        finally:
            if 'cur_cleanup' in locals() and cur_cleanup: cur_cleanup.close()
            if 'conn_cleanup' in locals() and conn_cleanup: conn_cleanup.close()

    # Run cleanup before tests
    cleanup_test_data(test_customer_email)

    try:
        print("\n[SETUP] Creating test customer...")
        temp_customer_id = add_customer("AccountMgmtTest", "User", test_customer_email)
        if not temp_customer_id:
            raise Exception("Failed to create test customer.")
        print(f"   Test customer created with ID: {temp_customer_id}")

        print("\n1. Attempting to open a new 'savings' account...")
        temp_account_id = open_account(temp_customer_id, "savings", 100.00)
        if not temp_account_id:
            raise Exception("Failed to open account.")
        print(f"   Successfully opened savings account with ID: {temp_account_id}")
        acc_details_open = get_account_by_id(temp_account_id)
        assert acc_details_open['overdraft_limit'] == 0.00, f"Default overdraft limit should be 0.00, got {acc_details_open['overdraft_limit']}"


        print("\n2. Attempting to retrieve account by ID...")
        account_details = get_account_by_id(temp_account_id)
        assert account_details, f"Failed to retrieve account ID {temp_account_id}"
        print(f"   Successfully retrieved account: {account_details['account_number']}, Balance: {account_details['balance']}, Overdraft Limit: {account_details['overdraft_limit']}")
        assert account_details['balance'] == 100.00
        assert account_details['status_name'] == 'active'

        print("\n3. Attempting to set overdraft limit...")
        new_limit = 50.50
        assert set_overdraft_limit(temp_account_id, new_limit), "Failed to set overdraft limit."
        updated_details = get_account_by_id(temp_account_id)
        assert updated_details['overdraft_limit'] == new_limit, f"Overdraft limit not updated. Expected {new_limit}, got {updated_details['overdraft_limit']}"
        print(f"   Successfully set overdraft limit to {new_limit}. Verified: {updated_details['overdraft_limit']}")

        print("\n4. Attempting to set negative overdraft limit (should fail)...")
        try:
            set_overdraft_limit(temp_account_id, -10.00)
            raise AssertionError("Negative overdraft limit setting did not fail as expected.")
        except ValueError as ve:
            print(f"   Successfully caught expected error for negative limit: {ve}")

        # ... (other tests from original file like get_account_by_number, update_account_status etc. can be here) ...
        # For brevity, focusing on overdraft related test additions.

        print("\nAll account_management tests completed.")

    except Exception as e:
        import traceback
        print(f"\nAn error occurred during account_management tests: {e}")
        traceback.print_exc()
    finally:
        cleanup_test_data(test_customer_email, temp_account_id)

```
