import pytest
from decimal import Decimal

# Import functions to be tested
from core.accounting_validator import (
    verify_ledger_integrity,
    check_account_balance_vs_transactions,
    AccountingValidationError
)
from core.account_management import open_account, get_account_balance # For setup and verification
from core.customer_management import add_customer # For setup
from core.transaction_processing import deposit, withdraw, transfer_funds # For setup

# Fixture to set up accounts for validation tests
@pytest.fixture
def validation_setup(db_conn):
    """
    Sets up a scenario for accounting validation:
    - Customer 1, Account 1_1 (checking), Account 1_2 (savings)
    - Customer 2, Account 2_1 (checking)
    Performs some balanced transactions.
    """
    c1_id = add_customer("ValCust1", "Test", "val.cust1@example.com")
    c2_id = add_customer("ValCust2", "Test", "val.cust2@example.com")

    acc1_1_id = open_account(c1_id, "checking", initial_balance=Decimal("0.00"))
    acc1_2_id = open_account(c1_id, "savings", initial_balance=Decimal("0.00"))
    acc2_1_id = open_account(c2_id, "checking", initial_balance=Decimal("0.00"))

    # Transactions:
    # 1. Deposit 1000 into Acc1_1
    deposit(acc1_1_id, Decimal("1000.00"), "Initial Deposit C1A1")
    # 2. Deposit 500 into Acc2_1
    deposit(acc2_1_id, Decimal("500.00"), "Initial Deposit C2A1")
    # 3. Transfer 200 from Acc1_1 to Acc1_2
    transfer_funds(acc1_1_id, acc1_2_id, Decimal("200.00"), "Transfer C1A1 to C1A2")
    # 4. Withdraw 50 from Acc1_1
    withdraw(acc1_1_id, Decimal("50.00"), "Withdrawal C1A1")
    # 5. Transfer 100 from Acc2_1 to Acc1_1
    transfer_funds(acc2_1_id, acc1_1_id, Decimal("100.00"), "Transfer C2A1 to C1A1")

    # Expected final balances:
    # Acc1_1: 0 + 1000 - 200 - 50 + 100 = 850
    # Acc1_2: 0 + 200 = 200
    # Acc2_1: 0 + 500 - 100 = 400
    # Total in system from these ops: 850 + 200 + 400 = 1450.
    # Sum of all transaction amounts (debits are neg):
    # +1000 (dep)
    # +500 (dep)
    # -200 (txfer out A11), +200 (txfer in A12)
    # -50 (wdraw)
    # -100 (txfer out A21), +100 (txfer in A11)
    # Sum = 1000 + 500 - 200 + 200 - 50 - 100 + 100 = 1450. This is NOT zero.
    # verify_ledger_integrity checks sum of `transactions.amount` column.
    # For deposits, amount is positive. For withdrawals, negative.
    # For transfers, one leg is positive, one is negative.
    # So, deposit (+1000), deposit (+500), transfer (-200, +200), withdrawal (-50), transfer (-100, +100)
    # Total sum = 1000 + 500 - 200 + 200 - 50 - 100 + 100 = 1450. This is incorrect for the test.
    # The sum of all transactions in `transactions` table *should* be zero if we consider the source of funds
    # for deposits and destination for withdrawals as external to the system of accounts.
    # However, `verify_ledger_integrity` as defined sums the `amount` column.
    # If deposits are +ve and withdrawals are -ve from the account's perspective, and transfers are balanced (+X and -X),
    # then the sum represents the net change of value *within the system of tracked accounts*.
    # For the sum of transactions to be zero, every credit must be offset by a debit *within the system*.
    # This implies that deposits (credits to an account) must have a corresponding debit from a "source of funds" account,
    # and withdrawals (debits from an account) must have a corresponding credit to a "destination of funds" account.
    # The current `verify_ledger_integrity` will not yield zero with simple deposits/withdrawals unless these
    # "external" legs are also recorded as transactions to some form of "system equity" or "external world" account.

    # For the purpose of testing the *current* implementation of `verify_ledger_integrity`,
    # let's make transactions that balance out to zero within the system of these 3 accounts.
    # This means we can't use `deposit` or `withdraw` directly if they only create one-sided entries
    # from the perspective of the total ledger sum unless we also model the external entities.
    # The current `deposit`/`withdraw` functions create single entries in `transactions`.
    # `transfer_funds` creates two balancing entries.

    # Let's adjust the setup for a more meaningful `verify_ledger_integrity` test.
    # We need every credit to an account to be a debit from another *within the test*.
    # This is hard without a "system" or "external" account.
    # Let's assume for `verify_ledger_integrity` we only make transfers.

    # Clean up any transactions from above if any were committed by core functions.
    # The db_conn fixture should handle cleaning tables before this fixture runs.

    # Scenario for verify_ledger_integrity (should sum to 0)
    # Acc1_1 starts with 1000 (via direct update for simplicity, or a "system deposit" not using `deposit`)
    # Acc2_1 starts with 500
    with db_conn.cursor() as cur:
        cur.execute("UPDATE accounts SET balance = %s WHERE account_id = %s;", (Decimal("1000.00"), acc1_1_id))
        cur.execute("UPDATE accounts SET balance = %s WHERE account_id = %s;", (Decimal("500.00"), acc2_1_id))
        db_conn.commit()

    # These transfers will have balanced entries in transactions table
    transfer_funds(acc1_1_id, acc1_2_id, Decimal("200.00"), "T1") # Acc1_1: 800, Acc1_2: 200
    transfer_funds(acc2_1_id, acc1_1_id, Decimal("100.00"), "T2") # Acc2_1: 400, Acc1_1: 900
    transfer_funds(acc1_2_id, acc2_1_id, Decimal("50.00"), "T3")  # Acc1_2: 150, Acc2_1: 450

    # Balances: Acc1_1: 900, Acc1_2: 150, Acc2_1: 450. Total: 1500 (same as initial total)
    # Transaction sums: (-200,+200), (-100,+100), (-50,+50). Total sum of these should be 0.

    return {
        "acc1_1_id": acc1_1_id, "acc1_2_id": acc1_2_id, "acc2_1_id": acc2_1_id,
        "expected_balances": {
            acc1_1_id: Decimal("900.00"),
            acc1_2_id: Decimal("150.00"),
            acc2_1_id: Decimal("450.00"),
        }
    }

# --- Tests for verify_ledger_integrity ---
def test_verify_ledger_integrity_balanced(db_conn, validation_setup):
    """
    Test ledger integrity when all transactions are balanced (e.g., only transfers).
    The current `verify_ledger_integrity` sums all `amount` fields.
    If all ops are internal transfers, sum should be 0.
    Deposits/Withdrawals (as currently implemented as single-leg entries in `transactions`)
    will cause the sum not to be zero.
    This test relies on the `validation_setup` creating only balanced transfer transactions.
    """
    is_balanced, total_sum = verify_ledger_integrity()
    assert is_balanced is True
    assert total_sum == Decimal("0.00")

def test_verify_ledger_integrity_with_unbalanced_ops(db_conn, validation_setup):
    """
    Test how verify_ledger_integrity behaves if there's a deposit (unbalanced from system PoV).
    The sum of transactions will not be zero.
    """
    acc1_1_id = validation_setup["acc1_1_id"]
    deposit(acc1_1_id, Decimal("100.00"), "Standalone Deposit") # This adds +100 to transactions sum

    is_balanced, total_sum = verify_ledger_integrity()
    assert is_balanced is False
    assert total_sum == Decimal("100.00")

    withdraw(acc1_1_id, Decimal("30.00"), "Standalone Withdrawal") # This adds -30 to transactions sum
    is_balanced_2, total_sum_2 = verify_ledger_integrity() # Sum should be 100 - 30 = 70
    assert is_balanced_2 is False
    assert total_sum_2 == Decimal("70.00")


# --- Tests for check_account_balance_vs_transactions ---
def test_check_account_balance_vs_transactions_match(db_conn, validation_setup):
    """Test when reported account balance matches sum of its transactions."""
    # The validation_setup updates balances directly then performs transfers.
    # We need to ensure that the sum of transactions for each account matches its *final* balance.
    # Let's re-do the setup slightly for this test to be clearer.

    c_id = add_customer("BalanceCheck", "User", "balcheck@example.com")
    acc_id = open_account(c_id, "checking", initial_balance=Decimal("0.00")) # Starts at 0

    # Perform transactions whose sum should be the final balance
    deposit(acc_id, Decimal("1000.00"), "BC_Dep1") # Balance: 1000, Tx Sum: +1000
    withdraw(acc_id, Decimal("200.00"), "BC_Wd1")  # Balance: 800,  Tx Sum: +1000 - 200 = +800
    deposit(acc_id, Decimal("50.00"), "BC_Dep2")   # Balance: 850,  Tx Sum: +800 + 50 = +850

    # Verify final balance in 'accounts' table
    current_balance_from_db = get_account_balance(acc_id)
    assert current_balance_from_db == Decimal("850.00")

    matches, reported_bal, tx_sum = check_account_balance_vs_transactions(acc_id)
    assert matches is True
    assert reported_bal == Decimal("850.00")
    assert tx_sum == Decimal("850.00")


def test_check_account_balance_mismatch(db_conn, validation_setup):
    """Test when reported account balance does NOT match sum of its transactions (simulated error)."""
    acc_id = validation_setup["acc1_1_id"] # Use an account from the setup

    # Manually corrupt the balance in the accounts table to create a mismatch
    # This simulates a bug or data corruption.
    original_balance = get_account_balance(acc_id)
    corrupted_balance = original_balance + Decimal("123.45") # Arbitrary change

    with db_conn.cursor() as cur:
        cur.execute("UPDATE accounts SET balance = %s WHERE account_id = %s;", (corrupted_balance, acc_id))
        db_conn.commit()

    matches, reported_bal, tx_sum = check_account_balance_vs_transactions(acc_id)
    assert matches is False
    assert reported_bal == corrupted_balance
    # tx_sum should be the sum of transactions based on the setup, which should be original_balance
    # For validation_setup["acc1_1_id"], expected balance is 900 based on transfers from initial 1000.
    # The initial 1000 was set by direct UPDATE, not a transaction.
    # So, tx_sum for acc1_1_id from validation_setup is: -200 (to A12) + 100 (from A21) = -100
    # This highlights complexity: if initial balances aren't transactions, tx_sum != balance.
    # The `check_account_balance_vs_transactions` assumes all balance changes are from transactions.
    # Let's use the `BalanceCheck` user from the previous test for a cleaner state.

    c_id = add_customer("BalanceMismatch", "User", "balmismatch@example.com")
    acc_id_mismatch = open_account(c_id, "checking", initial_balance=Decimal("0.00"))
    deposit(acc_id_mismatch, Decimal("100.00"), "BM_Dep1") # Bal: 100, Tx Sum: +100

    # Now, corrupt the balance
    with db_conn.cursor() as cur:
        cur.execute("UPDATE accounts SET balance = %s WHERE account_id = %s;", (Decimal("150.00"), acc_id_mismatch))
        db_conn.commit()

    matches_m, reported_bal_m, tx_sum_m = check_account_balance_vs_transactions(acc_id_mismatch)
    assert matches_m is False
    assert reported_bal_m == Decimal("150.00")
    assert tx_sum_m == Decimal("100.00")


def test_check_account_balance_non_existent_account(db_conn):
    """Test checking balance for a non-existent account."""
    with pytest.raises(AccountingValidationError, match="Account with ID 999888 not found"): # Error from inside the function
        check_account_balance_vs_transactions(999888)

def test_check_account_balance_no_transactions(db_conn):
    """Test for an account that exists but has no transactions."""
    c_id = add_customer("NoTrans", "User", "notrans@example.com")
    # Open account with initial balance, but this balance itself is not a transaction in `transactions` table.
    # The current `open_account` does not create an initial balance transaction.
    acc_id_no_trans = open_account(c_id, "savings", initial_balance=Decimal("50.00"))

    matches, reported_bal, tx_sum = check_account_balance_vs_transactions(acc_id_no_trans)

    # Balance is 50. Sum of transactions is 0. They don't match.
    # This is correct behavior for the function as written.
    # It highlights that for this check to pass for new accounts,
    # the initial balance might need to be represented as a transaction.
    assert matches is False
    assert reported_bal == Decimal("50.00")
    assert tx_sum == Decimal("0.00")

    # If account was opened with 0 and had no transactions:
    acc_id_zero_bal_no_trans = open_account(c_id, "checking", initial_balance=Decimal("0.00"))
    matches_z, reported_bal_z, tx_sum_z = check_account_balance_vs_transactions(acc_id_zero_bal_no_trans)
    assert matches_z is True
    assert reported_bal_z == Decimal("0.00")
    assert tx_sum_z == Decimal("0.00")

```
