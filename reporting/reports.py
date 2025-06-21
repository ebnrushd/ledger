import sys
import os
import csv
from datetime import datetime

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import get_db_connection # Using get_db_connection for self-contained connection management

class ReportingError(Exception):
    """Base exception for reporting errors."""
    pass

def export_transactions_to_csv(start_date_str, end_date_str, output_filepath, account_id=None):
    """
    Fetches transactions within a given date range (and optionally for a specific account)
    and exports them to a CSV file.

    Args:
        start_date_str (str): Start date in 'YYYY-MM-DD' format.
        end_date_str (str): End date in 'YYYY-MM-DD' format (inclusive).
        output_filepath (str): Path to the output CSV file.
        account_id (int, optional): If provided, filter transactions for this account_id.

    Raises:
        ReportingError: If date parsing fails, DB query fails, or CSV writing fails.
        ValueError: If date format is incorrect.
    """
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        # For end_date, include the whole day
        end_date = datetime.strptime(end_date_str + " 23:59:59", '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        raise ValueError(f"Invalid date format. Please use YYYY-MM-DD. Error: {e}")

    base_query = """
        SELECT
            t.transaction_id,
            t.transaction_timestamp,
            a.account_number AS primary_account_number,
            tt.type_name AS transaction_type,
            t.amount,
            t.description,
            ra.account_number AS related_account_number
        FROM
            transactions t
        JOIN
            accounts a ON t.account_id = a.account_id
        JOIN
            transaction_types tt ON t.transaction_type_id = tt.transaction_type_id
        LEFT JOIN
            accounts ra ON t.related_account_id = ra.account_id
        WHERE
            t.transaction_timestamp BETWEEN %s AND %s
    """
    params = [start_date, end_date]

    if account_id is not None:
        base_query += " AND t.account_id = %s"
        params.append(account_id)

    base_query += " ORDER BY t.transaction_timestamp ASC;"

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(base_query, tuple(params))
            results = cur.fetchall()

            if not results:
                print(f"No transactions found for the given criteria (Account ID: {account_id}, Period: {start_date_str} to {end_date_str}).")
                # Create an empty CSV with headers if no results
                with open(output_filepath, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([
                        "Transaction ID", "Timestamp", "Account Number",
                        "Transaction Type", "Amount", "Description", "Related Account Number"
                    ])
                print(f"Empty CSV report with headers generated at: {output_filepath}")
                return

        with open(output_filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow([
                "Transaction ID", "Timestamp", "Account Number",
                "Transaction Type", "Amount", "Description", "Related Account Number"
            ])
            # Write data rows
            for row in results:
                writer.writerow(row)

        print(f"Successfully exported {len(results)} transactions to {output_filepath}")

    except Exception as e:
        raise ReportingError(f"Failed to export transactions to CSV: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    print("Running reports.py direct tests...")
    # These tests will attempt to generate a CSV file.
    # Ensure you have some transactions in your database for the dates specified.

    # Create a temporary directory for reports if it doesn't exist
    temp_report_dir = "temp_reports"
    if not os.path.exists(temp_report_dir):
        os.makedirs(temp_report_dir)

    # Test case 1: All transactions for a date range
    output_file_all = os.path.join(temp_report_dir, "all_transactions_report.csv")
    start_date_all = "2023-01-01" # Adjust if your data is outside this range
    # Use a dynamic end date for broader coverage in tests, e.g., today.
    # For fixed tests, you might use a fixed past date where you know data exists.
    end_date_all = datetime.now().strftime('%Y-%m-%d')

    print(f"\n1. Exporting all transactions from {start_date_all} to {end_date_all} to {output_file_all}")
    try:
        export_transactions_to_csv(start_date_all, end_date_all, output_file_all)
    except ReportingError as e:
        print(f"   Error exporting all transactions: {e}")
    except ValueError as e:
        print(f"   Date error for all transactions: {e}")


    # Test case 2: Transactions for a specific account
    # You'll need to know an account_id that has transactions in your DB.
    # Let's try to fetch one dynamically for testing, similar to accounting_validator
    test_account_id_for_report = None
    try:
        conn_main = get_db_connection()
        with conn_main.cursor() as cur_main:
            # Get an account that has at least one transaction
            cur_main.execute("""
                SELECT DISTINCT t.account_id FROM transactions t
                JOIN accounts a ON t.account_id = a.account_id
                ORDER BY random() LIMIT 1;
            """)
            res = cur_main.fetchone()
            if res:
                test_account_id_for_report = res[0]
                print(f"   Dynamically selected Account ID {test_account_id_for_report} for specific report.")
            else:
                print("   No accounts with transactions found to test specific report. Skipping specific account export.")
    except Exception as e_fetch:
        print(f"   Could not dynamically fetch an account ID for reporting: {e_fetch}. Skipping specific account export.")
    finally:
        if 'conn_main' in locals() and conn_main:
            conn_main.close()

    if test_account_id_for_report:
        output_file_specific = os.path.join(temp_report_dir, f"account_{test_account_id_for_report}_transactions_report.csv")
        start_date_specific = "2023-01-01" # Adjust as needed
        end_date_specific = end_date_all # Use same dynamic end date

        print(f"\n2. Exporting transactions for Account ID {test_account_id_for_report} from {start_date_specific} to {end_date_specific} to {output_file_specific}")
        try:
            export_transactions_to_csv(start_date_specific, end_date_specific, output_file_specific, account_id=test_account_id_for_report)
        except ReportingError as e:
            print(f"   Error exporting specific account transactions: {e}")
        except ValueError as e:
            print(f"   Date error for specific account transactions: {e}")

    # Test case 3: Date format error
    print("\n3. Testing with invalid date format...")
    try:
        export_transactions_to_csv("01/01/2023", "01/02/2023", "dummy.csv")
    except ValueError as e:
        print(f"   Successfully caught date format error: {e}")
    except ReportingError as e: # Should be ValueError first
        print(f"   Caught ReportingError instead of ValueError: {e}")


    # Test case 4: No transactions found
    print("\n4. Testing with a date range likely to have no transactions...")
    output_file_none = os.path.join(temp_report_dir, "no_transactions_found_report.csv")
    start_date_none = "1900-01-01"
    end_date_none = "1900-01-31"
    try:
        export_transactions_to_csv(start_date_none, end_date_none, output_file_none)
        # Check if the file was created and is empty (or just has headers)
        if os.path.exists(output_file_none):
            with open(output_file_none, 'r') as f:
                lines = f.readlines()
                if len(lines) == 1 and "Transaction ID" in lines[0]: # Only header
                    print(f"   Successfully generated an empty report with headers at {output_file_none} as expected.")
                else:
                    print(f"   Report {output_file_none} was generated but content is not as expected for no transactions.")
        else:
            print(f"   Report {output_file_none} was not generated for no transactions (might be an issue).")


    except ReportingError as e:
        print(f"   Error during no-transaction test (this is okay if it's a specific DB error for empty results, but ideally it should just be an empty report): {e}")


    print("\nReporting tests completed.")
    print(f"Please check the '{temp_report_dir}' directory for generated CSV files.")

```
