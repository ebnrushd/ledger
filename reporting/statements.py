import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import get_db_connection
from core.account_management import get_account_by_id, AccountNotFoundError
from core.customer_management import get_customer_by_id, CustomerNotFoundError

class StatementError(Exception):
    """Base exception for statement generation errors."""
    pass

def _calculate_starting_balance(conn, account_id, start_date_dt):
    """
    Calculates the starting balance for an account on a given start_date.
    This is done by summing all transaction amounts for that account prior to the start_date.
    Note: This method assumes the ledger starts from zero or an initial deposit recorded as a transaction.
    A more robust way for accounts with long histories or explicit opening balances not part of summed transactions
    might involve finding the earliest balance snapshot and summing transactions from there.
    For this implementation, we sum all transactions before the start_date.
    """
    query_sum_before_start = """
        SELECT SUM(amount)
        FROM transactions
        WHERE account_id = %s AND transaction_timestamp < %s;
    """
    # Ensure start_date_dt is just the date part for comparison up to the beginning of that day
    start_of_day_start_date = start_date_dt.strftime('%Y-%m-%d %H:%M:%S')

    with conn.cursor() as cur:
        cur.execute(query_sum_before_start, (account_id, start_of_day_start_date))
        result = cur.fetchone()
        if result and result[0] is not None:
            return Decimal(result[0])
        return Decimal("0.00")

def generate_account_statement(account_id, start_date_str, end_date_str):
    """
    Generates a detailed account statement for a given period.

    Args:
        account_id (int): The ID of the account.
        start_date_str (str): Start date in 'YYYY-MM-DD' format.
        end_date_str (str): End date in 'YYYY-MM-DD' format (inclusive).

    Returns:
        dict: A dictionary containing statement details, including:
              - account_info (dict)
              - customer_info (dict)
              - period (dict: start_date, end_date)
              - starting_balance (Decimal)
              - ending_balance (Decimal)
              - transactions (list of dicts, each with transaction details and running_balance)

    Raises:
        StatementError: If any error occurs during statement generation.
        ValueError: If date format is incorrect.
        AccountNotFoundError: If account is not found.
        CustomerNotFoundError: If customer associated with account is not found.
    """
    try:
        start_date_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
        # End of day for end_date_str to include all transactions on that day
        end_date_dt = datetime.strptime(end_date_str + " 23:59:59.999999", '%Y-%m-%d %H:%M:%S.%f')
    except ValueError as e:
        raise ValueError(f"Invalid date format. Please use YYYY-MM-DD. Error: {e}")

    conn = None
    try:
        conn = get_db_connection()

        # 1. Fetch account details
        account_info = get_account_by_id(account_id) # Uses its own connection, but ok for this read
        if not account_info: # Should be caught by get_account_by_id, but double check
            raise AccountNotFoundError(f"Account {account_id} not found for statement.")

        # 2. Fetch customer details
        customer_info = get_customer_by_id(account_info['customer_id']) # Also uses its own connection
        if not customer_info:
            raise CustomerNotFoundError(f"Customer {account_info['customer_id']} for account {account_id} not found.")

        # 3. Calculate Starting Balance
        # The starting balance is the sum of all transactions *before* the start_date_str.
        starting_balance = _calculate_starting_balance(conn, account_id, start_date_dt)

        # 4. Fetch transactions for the period
        query_transactions_period = """
            SELECT
                t.transaction_id,
                t.transaction_timestamp,
                tt.type_name AS transaction_type,
                t.amount,
                t.description,
                ra.account_number AS related_account_number
            FROM
                transactions t
            JOIN
                transaction_types tt ON t.transaction_type_id = tt.transaction_type_id
            LEFT JOIN
                accounts ra ON t.related_account_id = ra.account_id
            WHERE
                t.account_id = %s AND
                t.transaction_timestamp >= %s AND t.transaction_timestamp <= %s
            ORDER BY
                t.transaction_timestamp ASC, t.transaction_id ASC;
        """

        period_transactions_data = []
        current_running_balance = starting_balance

        with conn.cursor() as cur:
            cur.execute(query_transactions_period, (
                account_id,
                start_date_dt.strftime('%Y-%m-%d %H:%M:%S'),
                end_date_dt.strftime('%Y-%m-%d %H:%M:%S.%f')
            ))
            transactions_in_period = cur.fetchall()

            for row in transactions_in_period:
                tx_amount = Decimal(row[3])
                current_running_balance += tx_amount
                period_transactions_data.append({
                    "transaction_id": row[0],
                    "timestamp": row[1].isoformat() if row[1] else None,
                    "type": row[2],
                    "amount": tx_amount, # Positive for credit, negative for debit
                    "debit": -tx_amount if tx_amount < 0 else Decimal("0.00"),
                    "credit": tx_amount if tx_amount > 0 else Decimal("0.00"),
                    "description": row[4],
                    "related_account_number": row[5],
                    "running_balance": current_running_balance
                })

        # 5. Ending Balance is the last running balance
        ending_balance = current_running_balance

        # Verify ending balance against current account balance if end_date is today or in the past
        # For future end_dates, this check isn't meaningful.
        # if end_date_dt.date() <= datetime.today().date():
        #     # Note: account_info['balance'] might have changed if new transactions occurred after we fetched it
        #     # and before this point, if not all operations are in one DB transaction.
        #     # For a statement, this calculated ending_balance is the correct one for the period.
        #     pass

        statement = {
            "account_info": {
                "account_number": account_info["account_number"],
                "account_type": account_info["account_type"],
                "currency": account_info["currency"],
                "overdraft_limit": account_info.get("overdraft_limit", 0.00) # Ensure overdraft_limit is present
            },
            "customer_info": {
                "customer_id": customer_info["customer_id"],
                "name": f"{customer_info['first_name']} {customer_info['last_name']}",
                "email": customer_info["email"],
                "address": customer_info.get("address", "N/A")
            },
            "period": {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "generated_at": datetime.now().isoformat()
            },
            "starting_balance": starting_balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "ending_balance": ending_balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "transactions": period_transactions_data
        }

        return statement

    except (AccountNotFoundError, CustomerNotFoundError, ValueError) as e:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise StatementError(f"Failed to generate account statement for account {account_id}: {e}")
    finally:
        if conn:
            conn.close()

def print_statement_to_console(statement_data):
    """Helper function to print statement data in a readable format."""
    if not statement_data:
        print("No statement data to print.")
        return

    print("\n--- ACCOUNT STATEMENT ---")
    print(f"Statement Date: {statement_data['period']['generated_at']}")
    print("\nCustomer Information:")
    print(f"  Name:    {statement_data['customer_info']['name']}")
    print(f"  Email:   {statement_data['customer_info']['email']}")
    print(f"  Address: {statement_data['customer_info']['address']}")

    print("\nAccount Information:")
    print(f"  Account Number: {statement_data['account_info']['account_number']}")
    print(f"  Account Type:   {statement_data['account_info']['account_type']}")
    print(f"  Currency:       {statement_data['account_info']['currency']}")
    print(f"  Overdraft Limit: {statement_data['account_info']['overdraft_limit']:.2f}")

    print("\nStatement Period:")
    print(f"  From: {statement_data['period']['start_date']} To: {statement_data['period']['end_date']}")
    print(f"\nStarting Balance: {statement_data['starting_balance']:.2f} {statement_data['account_info']['currency']}")

    print("\nTransactions:")
    header = "| {:<19} | {:<25} | {:<10} | {:<10} | {:<12} |".format(
        "Timestamp", "Description", "Debit", "Credit", "Balance"
    )
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    if not statement_data['transactions']:
        print("| {:<85} |".format("No transactions during this period."))
    else:
        for tx in statement_data['transactions']:
            # Ensure amounts are Decimal for formatting
            debit_amount = Decimal(tx.get('debit', 0))
            credit_amount = Decimal(tx.get('credit', 0))
            running_balance = Decimal(tx.get('running_balance', 0))

            print("| {:<19} | {:<25} | {:>10.2f} | {:>10.2f} | {:>12.2f} |".format(
                datetime.fromisoformat(tx['timestamp']).strftime('%Y-%m-%d %H:%M') if tx['timestamp'] else 'N/A',
                tx['description'][:25] if tx['description'] else '', # Truncate description
                debit_amount,
                credit_amount,
                running_balance
            ))
    print("-" * len(header))
    print(f"Ending Balance:   {statement_data['ending_balance']:.2f} {statement_data['account_info']['currency']}")
    print("--- END OF STATEMENT ---")


if __name__ == '__main__':
    print("Running statements.py direct tests...")
    # Requires a database with schema and some data.
    # You will need to know an account_id that has transactions.

    test_account_id = None
    try:
        # Attempt to find an account with some transactions for a more meaningful test
        conn_temp = get_db_connection()
        with conn_temp.cursor() as cur_temp:
            cur_temp.execute("SELECT account_id FROM transactions GROUP BY account_id HAVING COUNT(*) > 0 ORDER BY random() LIMIT 1;")
            res = cur_temp.fetchone()
            if res:
                test_account_id = res[0]
                print(f"Using Account ID {test_account_id} for statement generation.")
            else:
                print("No account with transactions found. Statement test might be less informative.")
                # Fallback: try to get any account ID, even without transactions
                cur_temp.execute("SELECT account_id FROM accounts ORDER BY random() LIMIT 1;")
                res_any_acc = cur_temp.fetchone()
                if res_any_acc:
                    test_account_id = res_any_acc[0]
                    print(f"Found account ID {test_account_id} (may not have transactions).")
                else:
                    print("No accounts found in the database. Cannot run statement test.")
    except Exception as e_fetch:
        print(f"Error fetching test account ID: {e_fetch}")
    finally:
        if 'conn_temp' in locals() and conn_temp: conn_temp.close()

    if test_account_id:
        # Define a date range. For robust testing, this range should ideally cover some transactions.
        # For this example, using a broad range.
        start_date = "2023-01-01"
        end_date = datetime.now().strftime('%Y-%m-%d') # Today

        print(f"\n1. Generating statement for Account ID {test_account_id} from {start_date} to {end_date}")
        try:
            statement = generate_account_statement(test_account_id, start_date, end_date)
            if statement:
                print_statement_to_console(statement)
                # Example: check if ending balance matches the account's current balance (if end_date is today)
                # current_db_balance = get_account_by_id(test_account_id)['balance']
                # print(f"Current DB balance for account {test_account_id}: {current_db_balance}")
                # print(f"Statement ending balance: {statement['ending_balance']}")
                # Note: Small discrepancies might occur due to timing or if not all tx are within statement period.
                # The statement's ending balance is what's correct for the period.
            else:
                print(f"   Failed to generate statement or no data returned.")
        except (StatementError, AccountNotFoundError, CustomerNotFoundError, ValueError) as e:
            print(f"   Error generating statement: {e}")
        except Exception as e_unexp:
            print(f"   Unexpected error during statement generation: {e_unexp}")
            import traceback
            traceback.print_exc()
    else:
        print("Skipping statement generation test as no test_account_id was set.")

    print("\nStatement generation tests completed.")

```
