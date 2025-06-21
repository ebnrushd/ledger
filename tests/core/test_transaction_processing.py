import pytest
from decimal import Decimal

# Import functions and exceptions to be tested
from core.transaction_processing import (
    deposit,
    withdraw,
    transfer_funds,
    process_ach_transaction,
    process_wire_transfer,
    AccountNotFoundError,
    InsufficientFundsError,
    InvalidAmountError,
    AccountNotActiveOrFrozenError,
    TransactionError,
    InvalidTransactionTypeError # Though this is mostly for get_transaction_type_id
)
from core.account_management import (
    get_account_balance,
    set_overdraft_limit,
    update_account_status,
    get_transaction_history, # To verify transactions are recorded
    open_account # For test setup
)
from core.customer_management import add_customer # For test setup
from core.audit_service import get_db_connection # To inspect audit log if needed, or use a dedicated audit fetcher

# --- Test Fixtures ---
@pytest.fixture
def setup_accounts(db_conn):
    """Sets up two customers and one account for each for transaction testing."""
    c1_id = add_customer("TP_Cust1", "Test", "tp.cust1@example.com")
    c2_id = add_customer("TP_Cust2", "Test", "tp.cust2@example.com")

    # Account 1: Checking, 1000 initial balance, 100 overdraft limit
    acc1_id = open_account(c1_id, "checking", initial_balance=Decimal("1000.00"))
    set_overdraft_limit(acc1_id, Decimal("100.00"))

    # Account 2: Savings, 500 initial balance, 0 overdraft limit
    acc2_id = open_account(c2_id, "savings", initial_balance=Decimal("500.00"))

    return acc1_id, acc2_id

# --- Tests for deposit ---
def test_deposit_success(db_conn, setup_accounts):
    acc1_id, _ = setup_accounts
    initial_balance = get_account_balance(acc1_id)
    deposit_amount = Decimal("200.50")

    tx_id = deposit(acc1_id, deposit_amount, "Test Deposit")
    assert tx_id is not None

    expected_balance = initial_balance + deposit_amount
    assert get_account_balance(acc1_id) == expected_balance

    # Verify transaction log
    history = get_transaction_history(acc1_id, limit=1)
    assert len(history) == 1
    assert history[0]["amount"] == deposit_amount
    assert history[0]["type_name"] == "deposit"

def test_deposit_invalid_amount(db_conn, setup_accounts):
    acc1_id, _ = setup_accounts
    with pytest.raises(InvalidAmountError):
        deposit(acc1_id, Decimal("-50.00"))
    with pytest.raises(InvalidAmountError):
        deposit(acc1_id, Decimal("0.00"))

def test_deposit_to_inactive_account(db_conn, setup_accounts):
    acc1_id, _ = setup_accounts
    update_account_status(acc1_id, "frozen") # Or 'closed'
    with pytest.raises(AccountNotActiveOrFrozenError):
        deposit(acc1_id, Decimal("100.00"))

def test_deposit_to_non_existent_account(db_conn):
    with pytest.raises(AccountNotFoundError):
        deposit(99999, Decimal("100.00"))


# --- Tests for withdraw ---
def test_withdraw_success(db_conn, setup_accounts):
    acc1_id, _ = setup_accounts # Initial bal 1000, OD limit 100
    initial_balance = get_account_balance(acc1_id)
    withdraw_amount = Decimal("150.75")

    tx_id = withdraw(acc1_id, withdraw_amount, "Test Withdrawal")
    assert tx_id is not None

    expected_balance = initial_balance - withdraw_amount
    assert get_account_balance(acc1_id) == expected_balance

    history = get_transaction_history(acc1_id, limit=1)
    assert len(history) == 1
    assert history[0]["amount"] == -withdraw_amount # Withdrawals are negative
    assert history[0]["type_name"] == "withdrawal"

def test_withdraw_into_overdraft(db_conn, setup_accounts):
    acc1_id, _ = setup_accounts # Bal 1000, OD 100
    # Withdraw 1050, should result in -50 balance
    withdraw_amount = Decimal("1050.00")
    tx_id = withdraw(acc1_id, withdraw_amount, "Overdraft Withdrawal")
    assert tx_id is not None
    assert get_account_balance(acc1_id) == Decimal("-50.00")
    # TODO: Add check for audit log entry for overdraft usage

def test_withdraw_exceeding_overdraft_limit(db_conn, setup_accounts):
    acc1_id, _ = setup_accounts # Bal 1000, OD 100. Max drawable = 1100.
    with pytest.raises(InsufficientFundsError):
        withdraw(acc1_id, Decimal("1100.01"))

def test_withdraw_insufficient_funds_no_overdraft(db_conn, setup_accounts):
    _, acc2_id = setup_accounts # Bal 500, OD 0
    with pytest.raises(InsufficientFundsError):
        withdraw(acc2_id, Decimal("500.01"))

def test_withdraw_from_frozen_account(db_conn, setup_accounts):
    acc1_id, _ = setup_accounts
    update_account_status(acc1_id, "frozen")
    with pytest.raises(AccountNotActiveOrFrozenError):
        withdraw(acc1_id, Decimal("50.00"))

# --- Tests for transfer_funds ---
def test_transfer_funds_success(db_conn, setup_accounts):
    acc1_id, acc2_id = setup_accounts # A1:1000, A2:500
    acc1_initial_bal = get_account_balance(acc1_id)
    acc2_initial_bal = get_account_balance(acc2_id)
    transfer_amount = Decimal("300.00")

    debit_tx_id, credit_tx_id = transfer_funds(acc1_id, acc2_id, transfer_amount, "Test Transfer")
    assert debit_tx_id is not None
    assert credit_tx_id is not None

    assert get_account_balance(acc1_id) == acc1_initial_bal - transfer_amount
    assert get_account_balance(acc2_id) == acc2_initial_bal + transfer_amount

    # Verify transaction logs for both
    hist_acc1 = get_transaction_history(acc1_id, limit=1)
    assert hist_acc1[0]["amount"] == -transfer_amount
    assert hist_acc1[0]["type_name"] == "transfer"
    assert hist_acc1[0]["related_account_id"] == acc2_id

    hist_acc2 = get_transaction_history(acc2_id, limit=1)
    assert hist_acc2[0]["amount"] == transfer_amount
    assert hist_acc2[0]["type_name"] == "transfer"
    assert hist_acc2[0]["related_account_id"] == acc1_id

def test_transfer_funds_into_overdraft(db_conn, setup_accounts):
    acc1_id, acc2_id = setup_accounts # A1:1000 OD:100, A2:500
    transfer_amount = Decimal("1050.00") # Will take A1 to -50

    transfer_funds(acc1_id, acc2_id, transfer_amount, "Overdraft Transfer")
    assert get_account_balance(acc1_id) == Decimal("-50.00")
    assert get_account_balance(acc2_id) == Decimal("500.00") + transfer_amount # 1550.00
    # TODO: Check audit log for overdraft on acc1_id

def test_transfer_funds_exceed_overdraft(db_conn, setup_accounts):
    acc1_id, acc2_id = setup_accounts # A1:1000 OD:100. Max debit = 1100
    with pytest.raises(InsufficientFundsError):
        transfer_funds(acc1_id, acc2_id, Decimal("1100.01"), "Exceed OD Transfer")

def test_transfer_funds_from_inactive_account(db_conn, setup_accounts):
    acc1_id, acc2_id = setup_accounts
    update_account_status(acc1_id, "frozen")
    with pytest.raises(AccountNotActiveOrFrozenError):
        transfer_funds(acc1_id, acc2_id, Decimal("50.00"))

def test_transfer_funds_to_inactive_account(db_conn, setup_accounts):
    acc1_id, acc2_id = setup_accounts
    update_account_status(acc2_id, "closed")
    with pytest.raises(AccountNotActiveOrFrozenError):
        transfer_funds(acc1_id, acc2_id, Decimal("50.00"))

def test_transfer_funds_same_account(db_conn, setup_accounts):
    acc1_id, _ = setup_accounts
    with pytest.raises(TransactionError, match="Cannot transfer funds to the same account"):
        transfer_funds(acc1_id, acc1_id, Decimal("10.00"))


# --- Tests for process_ach_transaction ---
@pytest.mark.parametrize("ach_type,initial_change,expected_tx_type", [
    ("credit", Decimal("50.00"), "ach_credit"),
    ("debit", Decimal("-50.00"), "ach_debit")
])
def test_process_ach_transaction_success(db_conn, setup_accounts, ach_type, initial_change, expected_tx_type):
    acc_id, _ = setup_accounts # Bal 1000
    initial_balance = get_account_balance(acc_id)
    ach_amount = abs(initial_change) # Amount for function is positive

    tx_id = process_ach_transaction(acc_id, ach_amount, f"Test ACH {ach_type}", ach_type=ach_type)
    assert tx_id is not None
    assert get_account_balance(acc_id) == initial_balance + initial_change

    history = get_transaction_history(acc_id, limit=1)
    assert history[0]["amount"] == initial_change
    assert history[0]["type_name"] == expected_tx_type

def test_process_ach_debit_insufficient_funds_overdraft(db_conn, setup_accounts):
    acc_id, _ = setup_accounts # Bal 1000, OD 100
    process_ach_transaction(acc_id, Decimal("1080.00"), "ACH Debit into OD", ach_type="debit")
    assert get_account_balance(acc_id) == Decimal("-80.00")

    with pytest.raises(InsufficientFundsError): # Try to debit 30 more (bal -80, OD 100, means 20 left in OD)
        process_ach_transaction(acc_id, Decimal("30.00"), "ACH Debit exceed OD", ach_type="debit")


# --- Tests for process_wire_transfer ---
@pytest.mark.parametrize("direction,initial_change,expected_tx_type", [
    ("incoming", Decimal("75.00"), "wire_transfer"),
    ("outgoing", Decimal("-75.00"), "wire_transfer")
])
def test_process_wire_transfer_success(db_conn, setup_accounts, direction, initial_change, expected_tx_type):
    acc_id, _ = setup_accounts # Bal 1000
    initial_balance = get_account_balance(acc_id)
    wire_amount = abs(initial_change)

    tx_id = process_wire_transfer(acc_id, wire_amount, f"Test Wire {direction}", direction=direction)
    assert tx_id is not None
    assert get_account_balance(acc_id) == initial_balance + initial_change

    history = get_transaction_history(acc_id, limit=1)
    assert history[0]["amount"] == initial_change # Stored as positive for incoming, negative for outgoing
    assert history[0]["type_name"] == expected_tx_type # Generic 'wire_transfer' type used

# TODO: Add more detailed tests for ACH/Wire for inactive accounts, invalid directions/types etc.
# TODO: Add tests for audit logging of overdraft usage (requires fetching from audit_log table).
```
