import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import execute_query, get_db_connection
# Import other core services if needed to aggregate data
from core.customer_management import get_customer_by_id # Example if needed
from core.account_management import get_account_by_id # Example

class AdminServiceError(Exception):
    """Base exception for admin service errors."""
    pass

def get_dashboard_summary_data(conn=None):
    """
    Fetches summary data for the admin dashboard.
    - Total number of customers.
    - Total number of accounts.
    - Total value of all account balances (sum of balances, requires careful thought on multi-currency).
    - Number of transactions in the last 24 hours.
    - List of N most recent transactions.

    Args:
        conn (psycopg2.connection, optional): An existing database connection.
                                             If None, a new one will be created and managed.

    Returns:
        dict: Containing dashboard summary data.
    """
    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection()
        _conn_needs_managing = True

    summary = {}
    try:
        # Ensure cursor is created correctly whether conn was passed or obtained.
        # Using 'with conn.cursor()' handles this well if conn is a valid connection object.
        with conn.cursor() as cur:
            # Total Customers
            cur.execute("SELECT COUNT(*) FROM customers;")
            summary["total_customers"] = cur.fetchone()[0]

            # Total Accounts
            cur.execute("SELECT COUNT(*) FROM accounts;")
            summary["total_accounts"] = cur.fetchone()[0]

            # Total value of all accounts (sum of balances)
            # IMPORTANT: This is a naive sum if multiple currencies exist.
            # A proper implementation would convert all balances to a base currency or show per currency.
            # For now, assuming a single currency or just summing as is for placeholder.
            cur.execute("SELECT SUM(balance) FROM accounts WHERE status_id = (SELECT status_id FROM account_status_types WHERE status_name = 'active');")
            total_balance_sum = cur.fetchone()[0]
            summary["total_system_balance_sum"] = Decimal(str(total_balance_sum or "0.00"))
            # Add a note about currency for the template
            summary["total_system_balance_currency_note"] = "USD (naive sum if multi-currency)"


            # Transactions in the last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            cur.execute("SELECT COUNT(*) FROM transactions WHERE transaction_timestamp >= %s;", (yesterday,))
            summary["transactions_last_24h"] = cur.fetchone()[0]

            # Recent N transactions (e.g., last 5)
            # Joining for more details.
            cur.execute("""
                SELECT t.transaction_id, t.transaction_timestamp, a.account_number, tt.type_name, t.amount, t.description
                FROM transactions t
                JOIN accounts a ON t.account_id = a.account_id
                JOIN transaction_types tt ON t.transaction_type_id = tt.transaction_type_id
                ORDER BY t.transaction_timestamp DESC
                LIMIT 5;
            """)
            recent_transactions_raw = cur.fetchall()
            summary["recent_transactions"] = [
                {
                    "id": r[0], "timestamp": r[1].isoformat(), "account_number": r[2],
                    "type": r[3], "amount": Decimal(str(r[4])), "description": r[5]
                } for r in recent_transactions_raw
            ]
        # No commit needed for SELECT queries
    except Exception as e:
        # print(f"Error in get_dashboard_summary_data: {e}")
        # If conn was passed, do not rollback here, let caller manage transaction.
        # If conn was managed internally, rollback could be considered but SELECTs don't alter.
        raise AdminServiceError(f"Failed to fetch dashboard summary data: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed: # Only close if managed internally
            conn.close()

    return summary


# Placeholder for listing functions that might be needed by admin views,
# which could involve joins or specific filtering not in basic core services.
# For example, listing users with their roles, or accounts with customer names.

def get_all_users_with_roles(page=1, per_page=20, search_query=None, conn=None):
    """ Fetches users with their role names. (Placeholder - needs user_service.py) """
    # This function would live in user_service.py once that's created.
    # For now, a placeholder to indicate what admin routers might need.
    print(f"[AdminService-Placeholder] get_all_users_with_roles called with page={page}, per_page={per_page}, search='{search_query}'")
    # Example structure, actual implementation would query DB.
    return {
        "users": [
            {"user_id": 1, "username": "admin_user_example", "email": "admin@example.com", "role_name": "admin", "is_active": True, "customer_id": None, "created_at": datetime.now()},
            {"user_id": 2, "username": "customer_user_example", "email": "cust@example.com", "role_name": "customer", "is_active": True, "customer_id": 101, "created_at": datetime.now()},
        ],
        "total_users": 2,
        "page": page,
        "per_page": per_page
    }
    # raise NotImplementedError("User service for fetching users with roles is not fully implemented here.")


if __name__ == '__main__':
    print("Testing admin_service.py functions...")
    # Requires DB connection and schema applied.
    conn_test = None
    try:
        # Test dashboard summary
        print("\nFetching dashboard summary data...")
        # Need to ensure some data exists for this to be meaningful.
        # The conftest.py setup usually clears tables. For this direct test, data might be absent.
        # A proper test for this would use fixtures to create data.
        summary = get_dashboard_summary_data() # Uses its own connection
        print(f"Dashboard Summary: {summary}")
        assert "total_customers" in summary
        assert "recent_transactions" in summary
        assert len(summary["recent_transactions"]) <= 5

        # Test placeholder for user listing
        print("\nFetching users (placeholder)...")
        users_data = get_all_users_with_roles()
        print(f"Users data: {users_data}")
        assert "users" in users_data

    except AdminServiceError as e:
        print(f"Admin service error: {e}")
    except Exception as e_main:
        print(f"An unexpected error occurred: {e_main}")
        import traceback
        traceback.print_exc()
    finally:
        if conn_test:
            conn_test.close()
    print("\nadmin_service.py tests finished.")

```
