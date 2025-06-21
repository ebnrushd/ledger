import pytest
from decimal import Decimal, ROUND_HALF_UP

# Import functions and exceptions to be tested
from core.currency_service import (
    get_exchange_rate,
    convert_currency,
    ExchangeRateNotFoundError,
    CurrencyServiceError
)
from database import execute_query # For adding test rates if needed

# --- Helper to manage test exchange rates ---
def setup_test_rates(db_conn):
    """Inserts specific rates for testing, cleans up first."""
    with db_conn.cursor() as cur:
        # Clean any specific test rates first to avoid conflicts if re-running
        cur.execute("DELETE FROM exchange_rates WHERE source = 'PyTestRates';")

        # Insert known rates for tests
        test_rates = [
            ('USD', 'EUR', Decimal('0.92500000'), 'PyTestRates'), # More precise
            ('EUR', 'USD', Decimal('1.08108108'), 'PyTestRates'), # Approx 1/0.925
            ('USD', 'GBP', Decimal('0.80000000'), 'PyTestRates'),
            ('GBP', 'USD', Decimal('1.25000000'), 'PyTestRates'),
            # Add a rate with a different effective_timestamp to test latest selection
            ('USD', 'EUR', Decimal('0.92000000'), 'PyTestRatesOld'), # Older rate
        ]
        # Update timestamp for the older rate to be in the past
        from datetime import datetime, timedelta
        older_timestamp = datetime.now() - timedelta(days=1)

        for from_c, to_c, rate_val, source_val in test_rates:
            ts = older_timestamp if source_val == 'PyTestRatesOld' else datetime.now()
            cur.execute(
                "INSERT INTO exchange_rates (from_currency, to_currency, rate, effective_timestamp, source) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (from_currency, to_currency, effective_timestamp) DO NOTHING;",
                (from_c, to_c, rate_val, ts, source_val if source_val != 'PyTestRatesOld' else 'PyTestRates') # Ensure source is consistent for cleanup
            )
        db_conn.commit()

@pytest.fixture(scope="module", autouse=True) # auto-use for all tests in this module
def manage_exchange_rates_for_module(db_conn): # db_conn here is session-scoped from conftest
    """Sets up test rates once for the module and cleans them up."""
    # Need a function-scoped connection for setup if db_conn itself is function-scoped
    # For now, assuming db_conn can be used or we get a new one.
    # Let's use the passed db_conn which should be function-scoped and clean.
    # If db_conn is module-scoped, this setup is fine.
    # From conftest, db_conn is function-scoped, so this fixture also becomes effectively function-scoped if it uses db_conn directly.
    # To make this module-scoped for setup/teardown of rates, we'd need a separate conn.
    # For simplicity, let's assume the main schema_updates.sql has some rates,
    # and these tests primarily use those or add very specific ones if needed.
    # The `autouse=True` with `db_conn` (function scope) means `setup_test_rates` runs before each test.
    setup_test_rates(db_conn)
    yield
    # Cleanup is implicitly handled by db_conn fixture clearing tables if rates were part of general tables.
    # However, exchange_rates might not be cleared by default clear_tables logic if not listed.
    # Let's ensure it's cleaned. If clear_tables in conftest handles it, this is redundant.
    # For now, we assume conftest.clear_tables includes exchange_rates or we add specific cleanup.
    # The `setup_test_rates` already cleans up its own 'PyTestRates' source records.


# --- Tests for get_exchange_rate ---
def test_get_exchange_rate_success(db_conn):
    """Test fetching an existing exchange rate."""
    # This relies on rates from setup_test_rates or schema_updates.sql
    rate = get_exchange_rate('USD', 'EUR') # Should get the latest (0.925)
    assert rate == Decimal('0.92500000')

    rate_gbp = get_exchange_rate('USD', 'GBP')
    assert rate_gbp == Decimal('0.80000000')

def test_get_exchange_rate_reverse(db_conn):
    """Test fetching a rate that might be stored in reverse or needs calculation (not supported directly)."""
    # Our get_exchange_rate fetches specific from->to.
    # If EUR to USD is 1.08108108, it should fetch that.
    rate = get_exchange_rate('EUR', 'USD')
    assert rate == Decimal('1.08108108')

def test_get_exchange_rate_same_currency(db_conn):
    """Test fetching rate for the same currency (should be 1.0)."""
    rate = get_exchange_rate('USD', 'USD')
    assert rate == Decimal('1.0')

def test_get_exchange_rate_not_found(db_conn):
    """Test fetching a rate for a non-existent currency pair."""
    with pytest.raises(ExchangeRateNotFoundError, match="Exchange rate not found for USD to XYZ"):
        get_exchange_rate('USD', 'XYZ')

def test_get_exchange_rate_uses_latest(db_conn):
    """Test that the function fetches the most recent rate."""
    # setup_test_rates inserts two USD to EUR rates, one older.
    # The get_exchange_rate should pick the one with current timestamp (0.925)
    rate = get_exchange_rate('USD', 'EUR')
    assert rate == Decimal('0.92500000')


# --- Tests for convert_currency ---
def test_convert_currency_success(db_conn):
    """Test successful currency conversion."""
    amount = Decimal("100.00")
    # USD to EUR: 100 * 0.92500000 = 92.50000000
    converted = convert_currency(amount, 'USD', 'EUR')
    expected = (amount * Decimal('0.92500000')).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    assert converted == expected

    # EUR to USD: 100 * 1.08108108 = 108.10810800
    converted_usd = convert_currency(amount, 'EUR', 'USD')
    expected_usd = (amount * Decimal('1.08108108')).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    assert converted_usd == expected_usd

def test_convert_currency_same_currency(db_conn):
    """Test conversion for the same currency."""
    amount = Decimal("123.45")
    converted = convert_currency(amount, 'JPY', 'JPY')
    assert converted == amount

def test_convert_currency_rate_not_found(db_conn):
    """Test conversion when the exchange rate is not available."""
    with pytest.raises(ExchangeRateNotFoundError):
        convert_currency(Decimal("100.00"), 'USD', 'XYZNONEXISTENT')

def test_convert_currency_various_precisions(db_conn):
    """Test conversion with amounts of various precisions."""
    # Amount with more precision
    amount_precise = Decimal("123.456789")
    # USD to EUR: 123.456789 * 0.92500000
    converted_precise = convert_currency(amount_precise, 'USD', 'EUR')
    expected_precise = (amount_precise * Decimal('0.92500000')).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    assert converted_precise == expected_precise

    # Small amount
    amount_small = Decimal("0.01")
    # USD to EUR: 0.01 * 0.92500000
    converted_small = convert_currency(amount_small, 'USD', 'EUR')
    expected_small = (amount_small * Decimal('0.92500000')).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    assert converted_small == expected_small

# Note: The conftest.py `clear_tables` fixture should include `exchange_rates` table
# in its list of tables to clear to ensure test isolation if rates are added directly by tests
# that don't use the module-scoped fixture's cleanup.
# The current module-scoped fixture `manage_exchange_rates_for_module` with `autouse=True`
# means `setup_test_rates` runs before each test in this file, providing fresh rates.
```
