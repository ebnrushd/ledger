import sys
import os
from decimal import Decimal, ROUND_HALF_UP

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import execute_query, get_db_connection

class CurrencyServiceError(Exception):
    """Base exception for currency service errors."""
    pass

class ExchangeRateNotFoundError(CurrencyServiceError):
    """Raised when an exchange rate is not found for the given currency pair."""
    pass

def get_exchange_rate(from_currency, to_currency, conn=None):
    """
    Fetches the latest applicable exchange rate for converting from_currency to to_currency.

    Args:
        from_currency (str): The currency code to convert from (e.g., 'USD').
        to_currency (str): The currency code to convert to (e.g., 'EUR').
        conn (psycopg2.connection, optional): An existing database connection.

    Returns:
        Decimal: The exchange rate (how many units of to_currency for 1 unit of from_currency).

    Raises:
        ExchangeRateNotFoundError: If no rate is found for the pair.
        CurrencyServiceError: For other database errors.
    """
    if from_currency == to_currency:
        return Decimal("1.0")

    query = """
        SELECT rate
        FROM exchange_rates
        WHERE from_currency = %s AND to_currency = %s
        ORDER BY effective_timestamp DESC
        LIMIT 1;
    """
    params = (from_currency, to_currency)

    _conn = conn
    result = None
    try:
        if _conn: # Use provided connection/cursor
            if hasattr(_conn, 'cursor'): # It's a connection
                cur = _conn.cursor()
                try:
                    cur.execute(query, params)
                    result = cur.fetchone()
                finally:
                    cur.close()
            else: # Assume it's a cursor
                cur = _conn
                cur.execute(query, params)
                result = cur.fetchone()
        else: # Manage connection internally via execute_query
            result = execute_query(query, params, fetch_one=True)

        if result and result[0] is not None:
            return Decimal(str(result[0]))
        else:
            raise ExchangeRateNotFoundError(f"Exchange rate not found for {from_currency} to {to_currency}.")

    except ExchangeRateNotFoundError:
        raise
    except Exception as e:
        raise CurrencyServiceError(f"Error fetching exchange rate for {from_currency} to {to_currency}: {e}")


def convert_currency(amount, from_currency, to_currency, conn=None):
    """
    Converts an amount from one currency to another using the latest exchange rate.

    Args:
        amount (Decimal or float or str): The amount to convert.
        from_currency (str): The currency code of the given amount.
        to_currency (str): The currency code to convert the amount to.
        conn (psycopg2.connection, optional): An existing database connection for rate fetching.

    Returns:
        Decimal: The converted amount in the to_currency.
                 The result is typically rounded to a standard number of decimal places
                 (e.g., 2 for most currencies, but this can vary).
                 For this function, we'll use 8 decimal places for intermediate,
                 and expect calling code to quantize appropriately for the target currency.


    Raises:
        ExchangeRateNotFoundError: If no rate is found.
        CurrencyServiceError: For other errors.
    """
    amount_decimal = Decimal(str(amount))
    if from_currency == to_currency:
        return amount_decimal

    try:
        rate = get_exchange_rate(from_currency, to_currency, conn=conn)
        converted_amount = amount_decimal * rate
        # It's good practice to round to a sensible number of decimal places,
        # though final rounding should be based on the target currency's precision.
        # For general calculation, let's use a higher precision.
        return converted_amount.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP) # 8 decimal places for calculation
    except (ExchangeRateNotFoundError, CurrencyServiceError) as e:
        raise # Re-raise the specific error
    except Exception as e_unexpected:
        raise CurrencyServiceError(f"Unexpected error during currency conversion: {e_unexpected}")


if __name__ == '__main__':
    print("Running currency_service.py direct tests...")
    # Requires DB with schema_updates.sql (for exchange_rates table and example rates).

    print("\n1. Testing direct rate lookup (USD to EUR)...")
    try:
        rate_usd_eur = get_exchange_rate('USD', 'EUR')
        print(f"   Rate USD to EUR: {rate_usd_eur} (Expected based on sample data, e.g., 0.92)")
        assert rate_usd_eur > 0 # Basic check
    except Exception as e:
        print(f"   Error: {e}")

    print("\n2. Testing conversion (100 USD to EUR)...")
    try:
        converted_eur = convert_currency(Decimal("100.00"), 'USD', 'EUR')
        # If rate is 0.92, expected is 92.00
        print(f"   100 USD is approximately {converted_eur} EUR.")
        # Example check, assuming rate is 0.92000000 from sample data
        # assert converted_eur == Decimal("92.00000000")
        assert converted_eur > 0
    except Exception as e:
        print(f"   Error: {e}")

    print("\n3. Testing conversion (100 EUR to USD)...")
    try:
        converted_usd = convert_currency(Decimal("100.00"), 'EUR', 'USD')
        # If rate is 1.08, expected is 108.00
        print(f"   100 EUR is approximately {converted_usd} USD.")
        # assert converted_usd == Decimal("108.00000000")
        assert converted_usd > 0
    except Exception as e:
        print(f"   Error: {e}")

    print("\n4. Testing conversion for same currency (USD to USD)...")
    try:
        same_currency_val = convert_currency(Decimal("100.00"), 'USD', 'USD')
        print(f"   100 USD to USD: {same_currency_val}")
        assert same_currency_val == Decimal("100.00")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n5. Testing non-existent rate (XYZ to ABC)...")
    try:
        get_exchange_rate('XYZ', 'ABC')
        raise AssertionError("Non-existent rate lookup did not fail as expected.")
    except ExchangeRateNotFoundError as e:
        print(f"   Successfully caught expected error for non-existent rate: {e}")
    except Exception as e:
        print(f"   Unexpected error type for non-existent rate: {e}")

    print("\n6. Testing conversion with non-existent rate...")
    try:
        convert_currency(100, 'XYZ', 'ABC')
        raise AssertionError("Conversion with non-existent rate did not fail as expected.")
    except ExchangeRateNotFoundError as e:
        print(f"   Successfully caught expected error for conversion with non-existent rate: {e}")
    except Exception as e:
        print(f"   Unexpected error type for conversion with non-existent rate: {e}")

    # Example of how one might add a rate for testing if needed (requires DB write privileges)
    # conn_test = None
    # try:
    #     print("\n7. Adding a test rate CAD to USD and fetching it...")
    #     conn_test = get_db_connection()
    #     with conn_test.cursor() as cur:
    #         # Clean up old test rate if it exists from a previous run
    #         cur.execute("DELETE FROM exchange_rates WHERE from_currency = 'CAD' AND to_currency = 'USD' AND source = 'TestEntry';")
    #         cur.execute(
    #             "INSERT INTO exchange_rates (from_currency, to_currency, rate, source) VALUES (%s, %s, %s, %s);",
    #             ('CAD', 'USD', Decimal('0.75123456'), 'TestEntry') # 8 decimal places
    #         )
    #         conn_test.commit()
    #         print("    Test rate CAD to USD inserted.")

    #     rate_cad_usd = get_exchange_rate('CAD', 'USD', conn=conn_test)
    #     print(f"    Fetched test rate CAD to USD: {rate_cad_usd}")
    #     assert rate_cad_usd == Decimal('0.75123456')

    #     converted_cad_to_usd = convert_currency(100, 'CAD', 'USD', conn=conn_test)
    #     print(f"    100 CAD = {converted_cad_to_usd} USD")
    #     assert converted_cad_to_usd == Decimal('75.12345600')


    # finally:
    #     if conn_test:
    #         # Clean up the test rate
    #         with conn_test.cursor() as cur_clean:
    #             cur_clean.execute("DELETE FROM exchange_rates WHERE from_currency = 'CAD' AND to_currency = 'USD' AND source = 'TestEntry';")
    #             conn_test.commit()
    #             print("    Test rate CAD to USD cleaned up.")
    #         conn_test.close()

    print("\nCurrency service tests completed.")
    print("Ensure 'exchange_rates' table exists and has sample data (from schema_updates.sql).")

```
