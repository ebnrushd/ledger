import pytest
from decimal import Decimal

# Import functions and exceptions to be tested
from core.account_management import (
    open_account,
    get_account_by_id,
    get_account_by_number,
    update_account_status,
    set_overdraft_limit,
    get_account_balance,
    get_transaction_history, # Assumes transaction_processing is also tested to create transactions
    AccountNotFoundError,
    InvalidAccountTypeError,
    AccountStatusError,
    AccountError,
    SUPPORTED_ACCOUNT_TYPES
)
from core.customer_management import CustomerNotFoundError # For testing open_account with invalid customer
from core.transaction_processing import deposit # To create some transactions for history

# Fixture for a valid customer ID (relies on create_customer_fx from conftest.py)
@pytest.fixture
def existing_customer_id(create_customer_fx):
    return create_customer_fx(first_name="AccTestCust", email_suffix="@account.test")

@pytest.fixture
def another_customer_id(create_customer_fx):
    return create_customer_fx(first_name="AnotherAcc", email_suffix="@anotheraccount.test")

# --- Tests for open_account ---
def test_open_account_success(db_conn, existing_customer_id):
    """Test successfully opening various types of accounts."""
    for acc_type in SUPPORTED_ACCOUNT_TYPES:
        account_id = open_account(
            customer_id=existing_customer_id,
            account_type=acc_type,
            initial_balance=Decimal("50.00")
        )
        assert account_id is not None
        details = get_account_by_id(account_id)
        assert details["customer_id"] == existing_customer_id
        assert details["account_type"] == acc_type
        assert details["balance"] == Decimal("50.00")
        assert details["status_name"] == "active"
        assert details["overdraft_limit"] == Decimal("0.00") # Default

def test_open_account_default_balance(db_conn, existing_customer_id):
    """Test opening account with default initial balance (0)."""
    account_id = open_account(customer_id=existing_customer_id, account_type="savings")
    details = get_account_by_id(account_id)
    assert details["balance"] == Decimal("0.00")

def test_open_account_invalid_customer(db_conn):
    """Test opening account for a non-existent customer."""
    non_existent_cust_id = 999999
    with pytest.raises(CustomerNotFoundError):
        open_account(customer_id=non_existent_cust_id, account_type="checking")

def test_open_account_invalid_type(db_conn, existing_customer_id):
    """Test opening account with an unsupported account type."""
    with pytest.raises(InvalidAccountTypeError):
        open_account(customer_id=existing_customer_id, account_type="investment_plus")

# --- Tests for get_account_by_id and get_account_by_number ---
def test_get_account_details(db_conn, create_account_fx, existing_customer_id):
    """Test fetching account by ID and by number."""
    account_id = create_account_fx(customer_id=existing_customer_id, initial_balance=Decimal("123.45"))

    details_by_id = get_account_by_id(account_id)
    assert details_by_id is not None
    assert details_by_id["account_id"] == account_id
    assert details_by_id["balance"] == Decimal("123.45")

    account_number = details_by_id["account_number"]
    details_by_number = get_account_by_number(account_number)
    assert details_by_number is not None
    assert details_by_number["account_id"] == account_id
    assert details_by_number["account_number"] == account_number

def test_get_account_not_found(db_conn):
    """Test fetching non-existent account by ID and number."""
    with pytest.raises(AccountNotFoundError):
        get_account_by_id(888888)
    with pytest.raises(AccountNotFoundError):
        get_account_by_number("0000000000_non_existent")

# --- Tests for update_account_status ---
def test_update_account_status_success(db_conn, create_account_fx):
    """Test successfully updating an account's status."""
    account_id = create_account_fx()

    # Active to Frozen
    update_account_status(account_id, "frozen")
    details = get_account_by_id(account_id)
    assert details["status_name"] == "frozen"

    # Frozen to Active
    update_account_status(account_id, "active")
    details = get_account_by_id(account_id)
    assert details["status_name"] == "active"

    # Active to Closed (if balance is zero)
    # Ensure balance is zero first by making a withdrawal if needed.
    # For simplicity, assume create_account_fx can create with 0 balance or we adjust.
    zero_bal_account_id = create_account_fx(initial_balance=Decimal("0.00"))
    update_account_status(zero_bal_account_id, "closed")
    details_closed = get_account_by_id(zero_bal_account_id)
    assert details_closed["status_name"] == "closed"


def test_update_account_status_close_with_balance(db_conn, create_account_fx):
    """Test error when trying to close an account with non-zero balance."""
    account_id = create_account_fx(initial_balance=Decimal("100.00"))
    with pytest.raises(AccountStatusError, match="cannot be closed due to non-zero balance"):
        update_account_status(account_id, "closed")

def test_update_account_status_invalid_status(db_conn, create_account_fx):
    """Test updating to an invalid status name."""
    account_id = create_account_fx()
    with pytest.raises(ValueError, match="Status name 'non_existent_status' not found"): # Error from get_account_status_id
        update_account_status(account_id, "non_existent_status")

def test_update_status_non_existent_account(db_conn):
    """Test updating status of a non-existent account."""
    with pytest.raises(AccountNotFoundError):
        update_account_status(777777, "active")


# --- Tests for set_overdraft_limit ---
def test_set_overdraft_limit_success(db_conn, create_account_fx):
    """Test successfully setting and updating overdraft limit."""
    account_id = create_account_fx()

    set_overdraft_limit(account_id, Decimal("100.50"))
    details = get_account_by_id(account_id)
    assert details["overdraft_limit"] == Decimal("100.50")

    set_overdraft_limit(account_id, Decimal("0.00"))
    details = get_account_by_id(account_id)
    assert details["overdraft_limit"] == Decimal("0.00")

def test_set_overdraft_limit_negative(db_conn, create_account_fx):
    """Test error when trying to set a negative overdraft limit."""
    account_id = create_account_fx()
    with pytest.raises(ValueError, match="Overdraft limit cannot be negative"):
        set_overdraft_limit(account_id, Decimal("-50.00"))

def test_set_overdraft_limit_non_existent_account(db_conn):
    """Test setting overdraft limit for a non-existent account."""
    with pytest.raises(AccountNotFoundError):
        set_overdraft_limit(666666, Decimal("100.00"))


# --- Tests for get_account_balance ---
def test_get_account_balance_success(db_conn, create_account_fx):
    """Test fetching account balance."""
    initial_bal = Decimal("789.01")
    account_id = create_account_fx(initial_balance=initial_bal)
    balance = get_account_balance(account_id)
    assert balance == initial_bal

def test_get_account_balance_not_found(db_conn):
    """Test fetching balance for non-existent account."""
    with pytest.raises(AccountNotFoundError): # As per updated get_account_balance
        get_account_balance(555555)

# --- Tests for get_transaction_history ---
def test_get_transaction_history_success(db_conn, create_account_fx):
    """Test fetching transaction history for an account."""
    account_id = create_account_fx(initial_balance=Decimal("200.00"))

    # Add some transactions using transaction_processing.deposit (or withdraw)
    # Note: deposit/withdraw handle their own connections.
    deposit(account_id, Decimal("50.00"), "Dep1")
    deposit(account_id, Decimal("25.00"), "Dep2")

    history = get_transaction_history(account_id, limit=10, offset=0)
    assert len(history) == 2 # Assuming deposit creates one transaction entry.
                            # If open_account also creates one, this would be 3.
                            # Current open_account does not create a transaction.

    # Verify order (most recent first)
    assert history[0]["description"] == "Dep2"
    assert history[0]["amount"] == Decimal("25.00")
    assert history[1]["description"] == "Dep1"
    assert history[1]["amount"] == Decimal("50.00")

    # Test limit and offset
    history_limit1 = get_transaction_history(account_id, limit=1, offset=0)
    assert len(history_limit1) == 1
    assert history_limit1[0]["description"] == "Dep2"

    history_offset1 = get_transaction_history(account_id, limit=1, offset=1)
    assert len(history_offset1) == 1
    assert history_offset1[0]["description"] == "Dep1"


def test_get_transaction_history_no_transactions(db_conn, create_account_fx):
    """Test fetching history for an account with no transactions."""
    account_id = create_account_fx() # No transactions made to this one
    history = get_transaction_history(account_id)
    assert len(history) == 0

def test_get_transaction_history_non_existent_account(db_conn):
    """Test fetching history for a non-existent account."""
    with pytest.raises(AccountNotFoundError):
        get_transaction_history(444444)

```
