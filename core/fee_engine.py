import sys
import os
from decimal import Decimal

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import execute_query, get_db_connection
from core.transaction_processing import withdraw, deposit, InsufficientFundsError, TransactionError, AccountNotFoundError, AccountNotActiveOrFrozenError
# We might need a specific transaction type for fees, or use a generic one.
# For now, let's assume 'withdrawal' or a specific 'fee' type if it exists.
# Let's check if 'fee' transaction type exists, if not, we can use a general description.

class FeeError(Exception):
    """Base exception for fee processing errors."""
    pass

class FeeTypeNotFoundError(FeeError):
    """Raised when a fee type name is not found."""
    pass

def get_fee_type_details(fee_type_name, conn=None):
    """
    Retrieves fee type details from the fee_types table.

    Args:
        fee_type_name (str): The name of the fee type.
        conn (psycopg2.connection, optional): Existing database connection.

    Returns:
        dict: Contains fee_type_id, fee_name, default_amount.

    Raises:
        FeeTypeNotFoundError: If fee_type_name not found.
    """
    query = "SELECT fee_type_id, fee_name, default_amount FROM fee_types WHERE fee_name = %s;"

    # Use existing connection if provided, otherwise execute_query handles its own
    _conn = conn
    cursor_managed_internally = False
    if not _conn:
        _conn = get_db_connection()
        cur = _conn.cursor()
        cursor_managed_internally = True
    elif hasattr(_conn, 'cursor'): # It's a connection
        cur = _conn.cursor()
    else: # It's already a cursor
        cur = _conn

    try:
        cur.execute(query, (fee_type_name,))
        result = cur.fetchone()
        if not conn and cursor_managed_internally : # If we created connection for this, no commit needed for SELECT
             pass
    finally:
        if hasattr(cur, 'close') and (cursor_managed_internally or conn): # Close cursor if we opened it or if it's from passed conn
            if not (hasattr(_conn, 'cursor') and cur == _conn): # Don't close if _conn was already a cursor
                 cur.close()
        if not conn and _conn and cursor_managed_internally : # Close connection if we created it
            _conn.close()

    if result:
        return {"fee_type_id": result[0], "fee_name": result[1], "default_amount": Decimal(str(result[2]))}
    else:
        raise FeeTypeNotFoundError(f"Fee type '{fee_type_name}' not found.")


def apply_fee(account_id, fee_type_name, fee_amount=None, description=None, user_id_performing_action=None):
    """
    Applies a fee to a specified account.

    This function will debit the account by the fee amount. It uses the
    `core.transaction_processing.withdraw` function internally, which handles
    balance checks (including overdraft) and transaction recording.

    Args:
        account_id (int): The ID of the account to apply the fee to.
        fee_type_name (str): The name of the fee type (must exist in `fee_types` table).
        fee_amount (Decimal, float, optional): The specific amount for this fee.
                                               If None, uses default_amount from `fee_types`.
        description (str, optional): Custom description for the fee transaction.
                                     If None, a default one is generated.
        user_id_performing_action (int, optional): ID of user/system process applying fee for audit.


    Returns:
        int: The transaction_id of the fee transaction.

    Raises:
        FeeTypeNotFoundError: If the fee_type_name is invalid.
        InsufficientFundsError: If the account (after considering overdraft) cannot cover the fee.
        AccountNotFoundError: If the account does not exist.
        AccountNotActiveOrFrozenError: If the account is not in a state to allow debits.
        FeeError: For other fee application issues.
    """
    try:
        fee_details = get_fee_type_details(fee_type_name)
    except FeeTypeNotFoundError:
        raise # Re-raise specific error

    final_fee_amount = Decimal(str(fee_amount)) if fee_amount is not None else fee_details['default_amount']

    if final_fee_amount <= 0:
        raise FeeError("Fee amount must be positive.")

    final_description = description or f"Fee applied: {fee_details['fee_name']}"

    try:
        # Use the 'withdraw' function for applying the fee.
        # This ensures overdraft logic, status checks, and proper transaction recording are handled.
        # The 'amount' for withdraw should be positive, it handles making it a negative transaction.
        print(f"Applying fee '{fee_details['fee_name']}' of {final_fee_amount} to account {account_id}.")

        # We need a specific transaction type for 'fee' if we don't want it to be 'withdrawal'
        # For now, let's assume the description makes it clear.
        # A more robust solution would be to have a generic debit function in transaction_processing
        # or ensure a 'fee' transaction type exists and use it.
        # Let's use withdraw for now and ensure description is clear.

        # The 'withdraw' function records amount as negative.
        # We will use its existing mechanism.
        transaction_id = withdraw(account_id, final_fee_amount, description=final_description)

        print(f"Fee '{fee_details['fee_name']}' applied to account {account_id}. Transaction ID: {transaction_id}")

        # Log fee application to audit_log
        try:
            from core.audit_service import log_event # Local import
            log_event(
                action_type='FEE_APPLIED',
                target_entity='accounts',
                target_id=account_id,
                details={
                    "fee_name": fee_details['fee_name'],
                    "fee_amount": float(final_fee_amount),
                    "transaction_id": transaction_id,
                    "description": final_description
                },
                user_id=user_id_performing_action # Could be a system user ID
            )
        except Exception as audit_e:
            print(f"Warning: Failed to log fee application for account {account_id}: {audit_e}")

        return transaction_id

    except (InsufficientFundsError, AccountNotFoundError, AccountNotActiveOrFrozenError, TransactionError) as e:
        # These are expected errors from the withdraw function
        print(f"Failed to apply fee to account {account_id}: {e}")
        raise FeeError(f"Could not apply fee '{fee_details['fee_name']}': {e}")
    except Exception as e_other:
        print(f"An unexpected error occurred while applying fee to account {account_id}: {e_other}")
        raise FeeError(f"Unexpected error applying fee '{fee_details['fee_name']}': {e_other}")


def run_periodic_fee_assessment(test_account_id=None, test_fee_type='monthly_maintenance_fee'):
    """
    Placeholder function to demonstrate periodic fee application.
    In a real system, this would iterate through eligible accounts and apply
    fees based on rules (e.g., monthly maintenance, low balance).
    """
    print("\n--- Running Periodic Fee Assessment (Placeholder) ---")
    if not test_account_id:
        print("No test_account_id provided, skipping demonstration.")
        # In a real scenario, you might query for accounts meeting certain criteria.
        # For example: SELECT account_id FROM accounts WHERE status = 'active' AND last_maintenance_fee_date < (NOW() - INTERVAL '1 month');
        return

    print(f"Assessing account {test_account_id} for fee: {test_fee_type}")
    try:
        # Example: Apply a monthly maintenance fee
        apply_fee(test_account_id, test_fee_type, user_id_performing_action=0) # 0 for System User
        print(f"Successfully applied '{test_fee_type}' to account {test_account_id}.")
    except FeeTypeNotFoundError:
        print(f"  ERROR: Fee type '{test_fee_type}' not found. Ensure it's in fee_types table via schema_updates.sql.")
    except FeeError as fe:
        print(f"  Fee assessment failed for account {test_account_id}: {fe}")
    except Exception as e:
        print(f"  Unexpected error during fee assessment for account {test_account_id}: {e}")

    print("--- Periodic Fee Assessment Finished ---")


if __name__ == '__main__':
    print("Running fee_engine.py direct tests...")
    # Requires DB with schema_updates.sql (for fee_types) and some accounts.
    # Ensure core.transaction_processing and core.audit_service are available.

    import core.account_management as am
    from core.customer_management import add_customer, get_customer_by_email, CustomerNotFoundError
    from decimal import ROUND_HALF_UP

    test_cust_email_fee = "fee.test@example.com"
    test_acc_id_fee = None
    cust_id_fee = None

    # Simplified cleanup
    def cleanup_fee_test_data():
        print("Attempting fee test cleanup...")
        conn_clean_fee = None
        try:
            cust = None
            try: cust = get_customer_by_email(test_cust_email_fee)
            except CustomerNotFoundError: pass

            if cust:
                conn_clean_fee = get_db_connection()
                cur_clean_fee = conn_clean_fee.cursor()
                cur_clean_fee.execute("SELECT account_id FROM accounts WHERE customer_id = %s;", (cust['customer_id'],))
                accs_to_del = cur_clean_fee.fetchall()
                for acc_tuple in accs_to_del:
                    acc_id_val = acc_tuple[0]
                    print(f"  Deleting transactions & audit for account {acc_id_val}")
                    cur_clean_fee.execute("DELETE FROM transactions WHERE account_id = %s;", (acc_id_val,))
                    cur_clean_fee.execute("DELETE FROM audit_log WHERE target_entity='accounts' AND target_id=%s;",(str(acc_id_val),))
                    cur_clean_fee.execute("DELETE FROM accounts WHERE account_id = %s;", (acc_id_val,))
                cur_clean_fee.execute("DELETE FROM customers WHERE customer_id = %s;", (cust['customer_id'],))
                conn_clean_fee.commit()
                print(f"  Customer {test_cust_email_fee} and associated accounts/transactions deleted.")
        except Exception as e:
            if conn_clean_fee: conn_clean_fee.rollback()
            print(f"  Cleanup error: {e}")
        finally:
            if conn_clean_fee: conn_clean_fee.close()

    cleanup_fee_test_data() # Clean before starting

    try:
        print("\n[SETUP] Creating customer and account for fee tests...")
        cust_id_fee = add_customer("FeeTest", "UserFee", test_cust_email_fee)
        test_acc_id_fee = am.open_account(cust_id_fee, "checking", initial_balance=Decimal("100.00"))
        am.set_overdraft_limit(test_acc_id_fee, Decimal("50.00")) # Give some overdraft
        print(f"  Account {test_acc_id_fee} created with balance 100.00, overdraft limit 50.00.")
        print("  Ensure 'fee_types' table is populated from schema_updates.sql (e.g., 'monthly_maintenance_fee').")

        print("\n1. Applying a standard fee ('monthly_maintenance_fee')...")
        initial_bal = am.get_account_balance(test_acc_id_fee)
        fee_details_test = get_fee_type_details('monthly_maintenance_fee') # Assumes this fee exists
        expected_fee_amt = fee_details_test['default_amount']

        apply_fee(test_acc_id_fee, 'monthly_maintenance_fee')
        new_bal = am.get_account_balance(test_acc_id_fee)
        assert new_bal == initial_bal - expected_fee_amt, f"Balance incorrect. Expected {initial_bal - expected_fee_amt}, got {new_bal}"
        print(f"   Fee applied. Balance changed from {initial_bal} to {new_bal}.")

        print("\n2. Applying a fee with a custom amount...")
        initial_bal = am.get_account_balance(test_acc_id_fee)
        custom_fee_amount = Decimal("7.50")
        apply_fee(test_acc_id_fee, 'monthly_maintenance_fee', fee_amount=custom_fee_amount)
        new_bal = am.get_account_balance(test_acc_id_fee)
        assert new_bal == initial_bal - custom_fee_amount
        print(f"   Custom fee applied. Balance changed from {initial_bal} to {new_bal}.")

        print("\n3. Applying a fee that uses overdraft...")
        # Current bal should be 100 - 5 (std fee) - 7.50 (custom fee) = 87.50
        # Apply a large fee, e.g., overdraft_usage_fee which is 25 by default.
        # Let's apply a hypothetical large fee of 100. Bal should go to 87.50 - 100 = -12.50
        initial_bal = am.get_account_balance(test_acc_id_fee) # Should be 87.50
        large_fee_type = 'overdraft_usage_fee' # Default 25.00. Let's use its default.
        fee_details_large = get_fee_type_details(large_fee_type)
        expected_large_fee_amt = fee_details_large['default_amount'] # 25.00

        apply_fee(test_acc_id_fee, large_fee_type)
        new_bal = am.get_account_balance(test_acc_id_fee)
        # Expected: 87.50 - 25.00 = 62.50
        assert new_bal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == (initial_bal - expected_large_fee_amt).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
        print(f"   Fee '{large_fee_type}' ({expected_large_fee_amt}) applied. Balance changed from {initial_bal} to {new_bal}.")


        print("\n4. Attempting to apply fee exceeding overdraft limit...")
        # Current bal = 62.50. Overdraft limit = 50. Max drawable = 62.50 + 50 = 112.50.
        # Try to apply a fee of 120.
        try:
            apply_fee(test_acc_id_fee, 'overdraft_usage_fee', fee_amount=Decimal("120.00"))
            raise AssertionError("Fee exceeding overdraft did not fail as expected.")
        except FeeError as fe: # Expecting InsufficientFundsError wrapped in FeeError
            if "Insufficient funds" in str(fe):
                 print(f"   Successfully caught expected error for fee exceeding overdraft: {fe}")
            else:
                 raise AssertionError(f"Caught FeeError, but not due to insufficient funds: {fe}")

        print("\n5. Testing run_periodic_fee_assessment (placeholder)...")
        run_periodic_fee_assessment(test_account_id=test_acc_id_fee, test_fee_type='monthly_maintenance_fee')
        # This will apply another monthly_maintenance_fee.
        # Current bal 62.50. After 5.00 fee, should be 57.50.
        assert am.get_account_balance(test_acc_id_fee).quantize(Decimal("0.01")) == Decimal("57.50")
        print(f"   Periodic fee assessment ran. Final balance for account {test_acc_id_fee}: {am.get_account_balance(test_acc_id_fee)}")

        print("\n6. Testing non-existent fee type...")
        try:
            apply_fee(test_acc_id_fee, 'non_existent_super_fee')
            raise AssertionError("Applying non-existent fee type did not fail.")
        except FeeTypeNotFoundError as e:
            print(f"   Successfully caught expected error for non-existent fee type: {e}")


    except Exception as e:
        import traceback
        print(f"\nAn error occurred during fee_engine tests: {e}")
        traceback.print_exc()
    finally:
        cleanup_fee_test_data()

    print("\nFee engine tests completed.")

```
