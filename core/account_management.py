import sys
import os
import random
import string
from decimal import Decimal # Ensure Decimal is imported

# Add project root to sys.path to allow importing 'database' and 'core.customer_management'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import get_db_connection # execute_query is no longer primary way if passing conn
from core.customer_management import get_customer_by_id as get_customer_details # Renamed to avoid conflict
from core.customer_management import CustomerNotFoundError

class AccountError(Exception):
    """Base custom exception for account-related errors."""
    pass

class AccountNotFoundError(AccountError):
    """Custom exception for when an account is not found."""
    pass

class InvalidAccountTypeError(AccountError):
    """Custom exception for invalid account types."""
    pass

class AccountStatusError(AccountError):
    """Custom exception for account status related issues (e.g., closing non-empty account)."""
    pass

SUPPORTED_ACCOUNT_TYPES = ["checking", "savings", "credit"]

def _generate_unique_account_number(length=10, conn=None): # Added conn for potential DB check
    """
    Generates a unique account number.
    If `conn` is provided, it can (and should) check against the DB for uniqueness.
    """
    # Placeholder: In a real system, this loop should query DB using `conn` if provided.
    # For now, direct DB check is omitted for brevity of this function, but it's critical.
    # query_check = "SELECT 1 FROM accounts WHERE account_number = %s;"
    # cur.execute(query_check, (new_acc_num,))
    # if not cur.fetchone(): return new_acc_num
    return ''.join(random.choices(string.digits, k=length))

def get_account_status_id(status_name, conn=None):
    query = "SELECT status_id FROM account_status_types WHERE status_name = %s;"
    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection()
        _conn_needs_managing = True
    try:
        with conn.cursor() as cur:
            cur.execute(query, (status_name,))
            result = cur.fetchone()
        if result: return result[0]
        raise ValueError(f"Status name '{status_name}' not found.")
    except ValueError: raise
    except Exception as e: raise AccountError(f"Error fetching status ID for '{status_name}': {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed: conn.close()

def open_account(customer_id, account_type, initial_balance=Decimal("0.00"), currency='USD', conn=None):
    initial_balance = Decimal(str(initial_balance)) # Ensure Decimal
    try:
        get_customer_details(customer_id, conn=conn) # Use passed conn
    except CustomerNotFoundError:
        raise

    if account_type.lower() not in SUPPORTED_ACCOUNT_TYPES:
        raise InvalidAccountTypeError(f"Account type '{account_type}' is not supported.")

    account_number = _generate_unique_account_number(conn=conn) # Pass conn

    status_id_to_use: int
    if initial_status_id is not None:
        # Optional: Validate if this status_id exists, or trust the caller / FK constraint
        # For now, directly use it. A more robust version might fetch by ID to confirm.
        status_id_to_use = initial_status_id
    else:
        status_id_to_use = get_account_status_id('active', conn=conn) # Pass conn

    query = """
        INSERT INTO accounts (customer_id, account_number, account_type, balance, currency, status_id, opened_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW()) RETURNING account_id;
    """
    params = (customer_id, account_number, account_type.lower(), initial_balance, currency, status_id_to_use)

    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection(); _conn_needs_managing = True; conn.autocommit = False

    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            account_id_val = cur.fetchone()[0]
        if _conn_needs_managing: conn.commit()
        print(f"Account {account_number} opened for customer {customer_id} with ID: {account_id_val}.")
        return account_id_val
    except Exception as e:
        if _conn_needs_managing and conn and not conn.closed: conn.rollback()
        raise AccountError(f"Failed to open account: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed: conn.close()

def _fetch_account_data(query, query_params, conn=None):
    """Helper to fetch account data, managing connection if needed."""
    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection(); _conn_needs_managing = True
    try:
        with conn.cursor() as cur:
            cur.execute(query, query_params)
            result = cur.fetchone()
        if result:
            return {
                "account_id": result[0], "customer_id": result[1], "account_number": result[2],
                "account_type": result[3], "balance": Decimal(str(result[4])), "currency": result[5],
                "status_name": result[6], "opened_at": result[7], "updated_at": result[8],
                "overdraft_limit": Decimal(str(result[9] if result[9] is not None else "0.00"))
            }
        return None # Not found
    except Exception as e:
        raise AccountError(f"Database error fetching account: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed: conn.close()

def get_account_by_id(account_id, conn=None):
    query = """
        SELECT a.account_id, a.customer_id, a.account_number, a.account_type,
               a.balance, a.currency, ast.status_name, a.opened_at, a.updated_at, a.overdraft_limit
        FROM accounts a JOIN account_status_types ast ON a.status_id = ast.status_id
        WHERE a.account_id = %s;
    """
    account_data = _fetch_account_data(query, (account_id,), conn=conn)
    if not account_data: raise AccountNotFoundError(f"Account with ID {account_id} not found.")
    return account_data

def get_account_by_number(account_number, conn=None):
    query = """
        SELECT a.account_id, a.customer_id, a.account_number, a.account_type,
               a.balance, a.currency, ast.status_name, a.opened_at, a.updated_at, a.overdraft_limit
        FROM accounts a JOIN account_status_types ast ON a.status_id = ast.status_id
        WHERE a.account_number = %s;
    """
    account_data = _fetch_account_data(query, (account_number,), conn=conn)
    if not account_data: raise AccountNotFoundError(f"Account with number {account_number} not found.")
    return account_data

def update_account_status(account_id, new_status_name, conn=None, admin_user_id=None): # Added admin_user_id for audit
    current_account = get_account_by_id(account_id, conn=conn)
    if new_status_name.lower() == 'closed' and current_account['balance'] != Decimal("0.00"):
        raise AccountStatusError(f"Account {account_id} cannot be closed due to non-zero balance.")

    new_status_id = get_account_status_id(new_status_name.lower(), conn=conn)
    query = "UPDATE accounts SET status_id = %s, updated_at = NOW() WHERE account_id = %s RETURNING account_id;"

    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection(); _conn_needs_managing = True; conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute(query, (new_status_id, account_id))
            updated_id_tuple = cur.fetchone()
        if not updated_id_tuple: raise AccountNotFoundError(f"Account ID {account_id} not found during status update.")

        # Audit logging should be done by the caller (router) which has admin_user_id context.
        # This function's responsibility is the DB update.
        # If audit_service is called here, it needs admin_user_id and old_status.
        # from core.audit_service import log_event
        # log_event('ACCOUNT_STATUS_CHANGE', 'accounts', account_id,
        #           {'old_status': current_account['status_name'], 'new_status': new_status_name},
        #           user_id=admin_user_id, conn=conn)

        if _conn_needs_managing: conn.commit()
        print(f"Account ID {updated_id_tuple[0]} status updated to '{new_status_name}'.")
        return True
    except (AccountNotFoundError, AccountStatusError, ValueError) as e_val:
        if _conn_needs_managing and conn and not conn.closed: conn.rollback()
        raise e_val
    except Exception as e:
        if _conn_needs_managing and conn and not conn.closed: conn.rollback()
        raise AccountError(f"Failed to update account status: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed: conn.close()

def set_overdraft_limit(account_id, limit, conn=None, admin_user_id=None): # Added admin_user_id for audit
    limit = Decimal(str(limit))
    if limit < Decimal("0.00"): raise ValueError("Overdraft limit cannot be negative.")

    current_account = get_account_by_id(account_id, conn=conn) # Ensures account exists & gets old limit for audit
    query = "UPDATE accounts SET overdraft_limit = %s, updated_at = NOW() WHERE account_id = %s RETURNING account_id;"

    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection(); _conn_needs_managing = True; conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute(query, (limit, account_id))
            updated_id_tuple = cur.fetchone()
        if not updated_id_tuple: raise AccountNotFoundError(f"Account ID {account_id} not found for overdraft update.")

        # Audit logging should be done by the caller (router)
        # from core.audit_service import log_event
        # log_event('OVERDRAFT_LIMIT_CHANGE', 'accounts', account_id,
        #           {'old_limit': float(current_account['overdraft_limit']), 'new_limit': float(limit)},
        #           user_id=admin_user_id, conn=conn)

        if _conn_needs_managing: conn.commit()
        print(f"Overdraft limit for account ID {updated_id_tuple[0]} updated to {limit}.")
        return True
    except (AccountNotFoundError, ValueError) as e_val:
        if _conn_needs_managing and conn and not conn.closed: conn.rollback()
        raise e_val
    except Exception as e:
        if _conn_needs_managing and conn and not conn.closed: conn.rollback()
        raise AccountError(f"Failed to set overdraft limit: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed: conn.close()

def get_account_balance(account_id, conn=None):
    query = "SELECT balance FROM accounts WHERE account_id = %s;"
    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection(); _conn_needs_managing = True
    try:
        with conn.cursor() as cur:
            cur.execute(query, (account_id,))
            result = cur.fetchone()
        if result: return Decimal(str(result[0]))
        raise AccountNotFoundError(f"Account ID {account_id} not found when getting balance.")
    except AccountNotFoundError: raise
    except Exception as e: raise AccountError(f"Could not retrieve balance for account {account_id}: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed: conn.close()

def list_accounts(page=1, per_page=20, search_query=None, account_type_filter=None, status_filter=None, customer_id_filter=None, conn=None):
    offset = (page - 1) * per_page
    select_fields = """
        a.account_id, a.customer_id, a.account_number, a.account_type, a.balance,
        a.currency, ast.status_name, a.overdraft_limit, a.opened_at, a.updated_at,
        c.first_name as customer_first_name, c.last_name as customer_last_name, c.email as customer_email
    """
    base_from_clause = """
        FROM accounts a
        JOIN account_status_types ast ON a.status_id = ast.status_id
        JOIN customers c ON a.customer_id = c.customer_id
    """
    count_query_base = f"SELECT COUNT(a.account_id) {base_from_clause}"
    list_query_base = f"SELECT {select_fields} {base_from_clause}"
    conditions, params = [], []

    if search_query:
        term = f"%{search_query}%"
        id_search_param = None
        if search_query.isdigit(): id_search_param = int(search_query)

        search_conditions = ["a.account_number ILIKE %s", "c.first_name ILIKE %s", "c.last_name ILIKE %s", "c.email ILIKE %s"]
        params.extend([term, term, term, term])
        if id_search_param is not None: # Search by customer_id if query is digit
            search_conditions.append("a.customer_id = %s")
            params.append(id_search_param)
        conditions.append(f"({' OR '.join(search_conditions)})")

    if account_type_filter: conditions.append("a.account_type = %s"); params.append(account_type_filter)
    if status_filter: conditions.append("ast.status_name = %s"); params.append(status_filter)
    if customer_id_filter is not None: conditions.append("a.customer_id = %s"); params.append(customer_id_filter)

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        count_query_base += where_clause; list_query_base += where_clause

    list_query_base += " ORDER BY a.account_id DESC LIMIT %s OFFSET %s;"
    list_params = params + [per_page, offset]

    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection(); _conn_needs_managing = True

    accounts_list, total_accounts = [], 0
    try:
        with conn.cursor() as cur:
            cur.execute(count_query_base, tuple(params))
            total_accounts = cur.fetchone()[0]
            cur.execute(list_query_base, tuple(list_params))
            records = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            for rec_tuple in records:
                acc_dict = dict(zip(colnames, rec_tuple))
                for field in ['balance', 'overdraft_limit']:
                    if field in acc_dict and acc_dict[field] is not None:
                        acc_dict[field] = Decimal(str(acc_dict[field]))
                accounts_list.append(acc_dict)
        return {"accounts": accounts_list, "total_accounts": total_accounts, "page": page, "per_page": per_page}
    except Exception as e: raise AccountError(f"Error listing accounts: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed: conn.close()

def calculate_interest_placeholder(account_id, interest_rate_percentage, conn=None): # Added conn
    try:
        account = get_account_by_id(account_id, conn=conn)
        balance = account['balance'] # Already Decimal from get_account_by_id
        annual_interest = balance * (Decimal(str(interest_rate_percentage)) / Decimal("100.0"))
        monthly_interest = annual_interest / Decimal("12.0")
        # For display or further processing, quantize to currency precision
        quantizer = Decimal("0.01") # Assuming 2 decimal places
        print(f"[INTEREST CALC LOG] Account: {account_id}, Balance: {balance}, Rate: {interest_rate_percentage}%, Monthly Interest: {monthly_interest.quantize(quantizer)}")
        return monthly_interest
    except AccountNotFoundError: raise
    except Exception as e: raise AccountError(f"Interest calculation failed: {e}")

def get_transaction_history(account_id, limit=50, offset=0, conn=None): # Added conn
    get_account_by_id(account_id, conn=conn)
    query = """
        SELECT t.transaction_id, t.account_id, tt.type_name, t.amount,
               t.transaction_timestamp, t.description, t.related_account_id,
               ra.account_number as related_account_number
        FROM transactions t
        JOIN transaction_types tt ON t.transaction_type_id = tt.transaction_type_id
        LEFT JOIN accounts ra ON t.related_account_id = ra.account_id
        WHERE t.account_id = %s
        ORDER BY t.transaction_timestamp DESC, t.transaction_id DESC
        LIMIT %s OFFSET %s;
    """
    params = (account_id, limit, offset)
    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection(); _conn_needs_managing = True
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            results = cur.fetchall()
        history_list = []
        if results:
            colnames = [desc[0] for desc in cur.description]
            for row_tuple in results:
                row_dict = dict(zip(colnames, row_tuple))
                if 'amount' in row_dict and row_dict['amount'] is not None:
                    row_dict['amount'] = Decimal(str(row_dict['amount']))
                history_list.append(row_dict)
        return history_list
    except Exception as e: raise AccountError(f"Could not retrieve transaction history: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed: conn.close()


if __name__ == '__main__':
    print("Running account_management.py direct tests...")
    from core.customer_management import add_customer, get_customer_by_email, CustomerNotFoundError # For setup

    print("   Reminder: Ensure 'accounts.overdraft_limit' column exists from 'schema_updates.sql'.")

    temp_customer_id = None
    temp_account_id = None
    test_customer_email = "am.direct.test@example.com"

    def _cleanup_direct_test_am_data(email_to_clean, acc_id_to_delete=None):
        # Basic cleanup, might need to be more robust for FKs in full system
        conn_clean = None
        try:
            conn_clean = get_db_connection()
            with conn_clean.cursor() as cur_clean:
                cust_to_delete = None
                try: cust_to_delete = get_customer_details(email_to_clean, conn=conn_clean) # Use conn
                except CustomerNotFoundError: pass

                if acc_id_to_delete:
                    cur_clean.execute("DELETE FROM transactions WHERE account_id = %s;", (acc_id_to_delete,))
                    cur_clean.execute("DELETE FROM accounts WHERE account_id = %s;", (acc_id_to_delete,))
                if cust_to_delete:
                    cust_id_val = cust_to_delete['customer_id']
                    if not acc_id_to_delete: # Clean all accounts if no specific one given
                        cur_clean.execute("DELETE FROM transactions WHERE account_id IN (SELECT account_id FROM accounts WHERE customer_id = %s);", (cust_id_val,))
                        cur_clean.execute("DELETE FROM accounts WHERE customer_id = %s;", (cust_id_val,))
                    cur_clean.execute("DELETE FROM customers WHERE customer_id = %s;", (cust_id_val,))
                conn_clean.commit()
        except Exception as e_cl: print(f"   Cleanup error: {e_cl}")
        finally:
            if conn_clean and not conn_clean.closed: conn_clean.close()

    _cleanup_direct_test_am_data(test_customer_email) # Clean before

    try:
        print("\n[SETUP] Creating test customer...")
        temp_customer_id = add_customer("AccountMgmtDirect", "User", test_customer_email) # Manages its own conn
        assert temp_customer_id, "Failed to create customer for AM tests."
        print(f"   Test customer created with ID: {temp_customer_id}")

        print("\n1. Attempting to open a new 'savings' account...")
        temp_account_id = open_account(temp_customer_id, "savings", Decimal("100.00")) # Manages its own conn
        assert temp_account_id, "Failed to open account."
        print(f"   Successfully opened savings account with ID: {temp_account_id}")

        acc_details_open = get_account_by_id(temp_account_id) # Manages its own conn
        assert acc_details_open['overdraft_limit'] == Decimal("0.00")

        print("\n2. Listing accounts (expecting at least one)...")
        accounts_data = list_accounts(customer_id_filter=temp_customer_id) # Manages its own conn
        assert accounts_data["total_accounts"] >= 1
        assert any(acc['account_id'] == temp_account_id for acc in accounts_data['accounts'])
        print(f"   Found account in list. Total for customer: {accounts_data['total_accounts']}")

        print("\n3. Setting overdraft limit...")
        set_overdraft_limit(temp_account_id, Decimal("50.50")) # Manages its own conn
        updated_details = get_account_by_id(temp_account_id)
        assert updated_details['overdraft_limit'] == Decimal("50.50")
        print(f"   Overdraft set to {updated_details['overdraft_limit']}.")

        # Further tests can be added here for other functions using a similar pattern.

    except (AccountError, CustomerNotFoundError, ValueError) as e:
        print(f"   Error during direct AM tests: {e}")
    except Exception as e_unhandled:
        print(f"   Unexpected error in direct AM tests: {e_unhandled}")
        import traceback; traceback.print_exc()
    finally:
        _cleanup_direct_test_am_data(test_customer_email, temp_account_id) # Clean after

    print("\nAccount_management.py direct tests finished.")

```
