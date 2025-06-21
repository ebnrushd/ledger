import pytest
from decimal import Decimal

# Import functions and exceptions to be tested
from core.fee_engine import (
    get_fee_type_details,
    apply_fee,
    FeeTypeNotFoundError,
    FeeError
)
from core.transaction_processing import InsufficientFundsError # For testing fee exceeding balance
from core.account_management import (
    get_account_balance,
    set_overdraft_limit,
    open_account # For test setup
)
from core.customer_management import add_customer # For test setup

# Fixture for test account setup
@pytest.fixture
def fee_test_account(db_conn):
    """Sets up a customer and an account for fee testing."""
    customer_id = add_customer("FeePayer", "Test", "feepayer.test@example.com")
    # Initial balance 100, Overdraft limit 50
    account_id = open_account(customer_id, "checking", initial_balance=Decimal("100.00"))
    set_overdraft_limit(account_id, Decimal("50.00"))
    return account_id

# --- Tests for get_fee_type_details ---
def test_get_fee_type_details_success(db_conn):
    """Test fetching details of an existing fee type."""
    # Assumes 'monthly_maintenance_fee' with amount 5.00 exists from schema_updates.sql
    fee_details = get_fee_type_details("monthly_maintenance_fee")
    assert fee_details is not None
    assert fee_details["fee_name"] == "monthly_maintenance_fee"
    assert fee_details["default_amount"] == Decimal("5.00")

def test_get_fee_type_details_not_found(db_conn):
    """Test fetching a non-existent fee type."""
    with pytest.raises(FeeTypeNotFoundError, match="Fee type 'non_existent_fee_abc' not found"):
        get_fee_type_details("non_existent_fee_abc")

# --- Tests for apply_fee ---
def test_apply_fee_default_amount_success(db_conn, fee_test_account):
    """Test applying a fee using its default amount."""
    account_id = fee_test_account
    initial_balance = get_account_balance(account_id) # Should be 100.00

    fee_type_name = "monthly_maintenance_fee" # Default 5.00
    fee_details = get_fee_type_details(fee_type_name) # Get expected amount

    tx_id = apply_fee(account_id, fee_type_name)
    assert tx_id is not None

    expected_balance = initial_balance - fee_details["default_amount"]
    assert get_account_balance(account_id) == expected_balance # 100 - 5 = 95

def test_apply_fee_custom_amount_success(db_conn, fee_test_account):
    """Test applying a fee with a specified custom amount."""
    account_id = fee_test_account # Current balance should be 95 from previous test (if run in sequence without clean context)
                                   # Pytest fixtures ensure `fee_test_account` is fresh or `db_conn` cleans.
                                   # `db_conn` clears tables, so balance is 100.
    initial_balance = get_account_balance(account_id) # Should be 100.00

    fee_type_name = "monthly_maintenance_fee"
    custom_fee_amount = Decimal("7.25")

    tx_id = apply_fee(account_id, fee_type_name, fee_amount=custom_fee_amount)
    assert tx_id is not None

    expected_balance = initial_balance - custom_fee_amount
    assert get_account_balance(account_id) == expected_balance # 100 - 7.25 = 92.75

def test_apply_fee_into_overdraft(db_conn, fee_test_account):
    """Test applying a fee that pushes the account into its overdraft."""
    account_id = fee_test_account # Bal 100, OD 50
    initial_balance = get_account_balance(account_id)

    # A large fee, e.g., using 'wire_transfer_fee_outgoing' (default 15) but with custom amount
    fee_type_name = "wire_transfer_fee_outgoing"
    # To go into overdraft from 100, fee must be > 100. E.g., 120
    # Bal should become 100 - 120 = -20. (OD limit is 50, so this is allowed)
    overdrafting_fee_amount = Decimal("120.00")

    tx_id = apply_fee(account_id, fee_type_name, fee_amount=overdrafting_fee_amount)
    assert tx_id is not None
    assert get_account_balance(account_id) == initial_balance - overdrafting_fee_amount # Expected -20.00

def test_apply_fee_exceeding_overdraft_limit(db_conn, fee_test_account):
    """Test applying a fee that exceeds the overdraft limit."""
    account_id = fee_test_account # Bal 100, OD 50. Max drawable = 150.

    fee_type_name = "wire_transfer_fee_outgoing"
    # Fee of 150.01 should fail
    excessive_fee_amount = Decimal("150.01")

    with pytest.raises(FeeError, match="Insufficient funds"): # FeeError wraps InsufficientFundsError
        apply_fee(account_id, fee_type_name, fee_amount=excessive_fee_amount)

def test_apply_fee_type_not_found(db_conn, fee_test_account):
    """Test applying a fee whose type does not exist."""
    account_id = fee_test_account
    with pytest.raises(FeeTypeNotFoundError):
        apply_fee(account_id, "non_existent_mega_fee")

def test_apply_fee_zero_or_negative_custom_amount(db_conn, fee_test_account):
    """Test applying a fee with zero or negative custom amount."""
    account_id = fee_test_account
    with pytest.raises(FeeError, match="Fee amount must be positive"):
        apply_fee(account_id, "monthly_maintenance_fee", fee_amount=Decimal("0.00"))
    with pytest.raises(FeeError, match="Fee amount must be positive"):
        apply_fee(account_id, "monthly_maintenance_fee", fee_amount=Decimal("-10.00"))

# Note: Tests for `run_periodic_fee_assessment` would be more like integration tests,
# as it involves iterating accounts and applying fees. A simple call can be made
# to ensure it runs without error, but verifying its full logic requires more setup.
def test_run_periodic_fee_assessment_placeholder_runs(db_conn, fee_test_account):
    """Test that the placeholder periodic fee assessment runs without error."""
    from core.fee_engine import run_periodic_fee_assessment # Import here to avoid issues if file is run directly

    initial_balance = get_account_balance(fee_test_account)
    # Uses 'monthly_maintenance_fee' by default in its implementation
    fee_details = get_fee_type_details('monthly_maintenance_fee')

    # This test is basic, just ensures it doesn't crash.
    # Assumes run_periodic_fee_assessment is correctly set up to use a test account.
    # The placeholder function applies 'monthly_maintenance_fee' to the test_account_id.
    try:
        run_periodic_fee_assessment(test_account_id=fee_test_account)
        final_balance = get_account_balance(fee_test_account)
        assert final_balance == initial_balance - fee_details['default_amount']
    except Exception as e:
        pytest.fail(f"run_periodic_fee_assessment raised an unexpected exception: {e}")
```
