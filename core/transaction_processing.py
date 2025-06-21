import sys
import os
from decimal import Decimal # Ensure Decimal is imported

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import get_db_connection, execute_query
from core.account_management import get_account_by_id as get_account_details_ext # Renamed to avoid conflict
from core.account_management import AccountNotFoundError, SUPPORTED_ACCOUNT_TYPES
# Note: core.audit_service is imported locally in functions to avoid circular dependencies at load time

# --- Custom Exceptions ---
class TransactionError(Exception):
    """Base exception for transaction processing errors."""
    pass

class InsufficientFundsError(TransactionError):
    """Raised when an account has insufficient funds for a transaction."""
    pass

class InvalidTransactionTypeError(TransactionError):
    """Raised when a transaction type name is not found."""
    pass

class AccountNotActiveOrFrozenError(TransactionError):
    """Raised when an account is not in a valid state for a transaction."""
    pass

class InvalidAmountError(TransactionError):
    """Raised when a transaction amount is invalid (e.g., not positive)."""
    pass


# --- Helper Functions ---

def get_transaction_type_id(type_name, conn_or_cursor=None):
    query = "SELECT transaction_type_id FROM transaction_types WHERE type_name = %s;"

    if conn_or_cursor:
        if hasattr(conn_or_cursor, 'cursor'):
            cursor = conn_or_cursor.cursor()
            try:
                cursor.execute(query, (type_name,))
                result = cursor.fetchone()
            finally:
                cursor.close()
        else:
            cursor = conn_or_cursor
            cursor.execute(query, (type_name,))
            result = cursor.fetchone()
    else:
        result = execute_query(query, (type_name,), fetch_one=True)

    if result:
        return result[0]
    else:
        raise InvalidTransactionTypeError(f"Transaction type '{type_name}' not found.")


def _record_transaction(cursor, account_id, transaction_type_id, amount, description=None, related_account_id=None):
    query = """
        INSERT INTO transactions (account_id, transaction_type_id, amount, description, related_account_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING transaction_id;
    """
    params = (account_id, transaction_type_id, Decimal(str(amount)), description, related_account_id) # Ensure amount is Decimal
    cursor.execute(query, params)
    transaction_id = cursor.fetchone()[0]
    return transaction_id


def _update_account_balance(cursor, account_id, amount_change):
    query = """
        UPDATE accounts
        SET balance = balance + %s, updated_at = CURRENT_TIMESTAMP
        WHERE account_id = %s;
    """
    cursor.execute(query, (Decimal(str(amount_change)), account_id)) # Ensure amount_change is Decimal
    if cursor.rowcount == 0:
        raise AccountNotFoundError(f"Account with ID {account_id} not found during balance update.")


# --- Main Transaction Processing Functions ---

def deposit(account_id, amount, description="Deposit"):
    amount = Decimal(str(amount)) # Ensure amount is Decimal
    if amount <= 0:
        raise InvalidAmountError("Deposit amount must be positive.")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Fetch account details using internal query to ensure it's part of the transaction context if needed for status
            cur.execute("SELECT status_id FROM accounts WHERE account_id = %s;", (account_id,))
            acc_res = cur.fetchone()
            if not acc_res:
                raise AccountNotFoundError(f"Account {account_id} not found for deposit.")

            status_id = acc_res[0]
            cur.execute("SELECT status_name FROM account_status_types WHERE status_id = %s;", (status_id,))
            status_name = cur.fetchone()[0]

            if status_name != 'active':
                raise AccountNotActiveOrFrozenError(f"Account {account_id} is not active. Current status: {status_name}.")

            _update_account_balance(cur, account_id, amount)
            deposit_type_id = get_transaction_type_id('deposit', cur)
            transaction_id = _record_transaction(cur, account_id, deposit_type_id, amount, description)

            conn.commit()
            print(f"Deposit of {amount} to account {account_id} successful. Transaction ID: {transaction_id}")
            return transaction_id

    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InvalidAmountError, InvalidTransactionTypeError) as e:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error during deposit to account {account_id}: {e}")
        raise TransactionError(f"Deposit failed: {e}")
    finally:
        if conn: conn.close()


def withdraw(account_id, amount, description="Withdrawal"):
    amount = Decimal(str(amount)) # Ensure amount is Decimal
    if amount <= 0:
        raise InvalidAmountError("Withdrawal amount must be positive.")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT balance, status_id, overdraft_limit FROM accounts WHERE account_id = %s FOR UPDATE;", (account_id,))
            account_data = cur.fetchone()
            if not account_data:
                raise AccountNotFoundError(f"Account {account_id} not found.")

            balance, status_id, overdraft_limit = Decimal(str(account_data[0])), account_data[1], Decimal(str(account_data[2] or 0.00))

            cur.execute("SELECT status_name FROM account_status_types WHERE status_id = %s;", (status_id,))
            status_name = cur.fetchone()[0]

            if status_name != 'active':
                raise AccountNotActiveOrFrozenError(f"Account {account_id} is not active or is frozen. Current status: {status_name}.")

            if balance - amount < -overdraft_limit:
                raise InsufficientFundsError(f"Insufficient funds in account {account_id}. Balance: {balance}, Overdraft Limit: {overdraft_limit}, Required: {amount}.")

            used_overdraft_before = balance < 0
            _update_account_balance(cur, account_id, -amount)
            new_balance_after_tx = balance - amount

            if new_balance_after_tx < 0 and (not used_overdraft_before or new_balance_after_tx < balance):
                try:
                    from core.audit_service import log_event
                    log_event(action_type='OVERDRAFT_USED', target_entity='accounts', target_id=account_id,
                              details={"old_balance": float(balance), "new_balance": float(new_balance_after_tx),
                                       "overdraft_limit": float(overdraft_limit), "withdrawal_amount": float(amount),
                                       "description": "Account balance went into overdraft or overdraft increased."},
                              conn=conn) # Pass conn to ensure audit is part of same transaction
                    print(f"Overdraft event logged for account {account_id}.")
                except Exception as audit_e:
                    print(f"Warning: Failed to log overdraft event for account {account_id}: {audit_e}")

            withdrawal_type_id = get_transaction_type_id('withdrawal', cur)
            transaction_id = _record_transaction(cur, account_id, withdrawal_type_id, -amount, description)

            conn.commit()
            print(f"Withdrawal of {amount} from account {account_id} successful. Transaction ID: {transaction_id}")
            return transaction_id

    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, InvalidTransactionTypeError) as e:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error during withdrawal from account {account_id}: {e}")
        raise TransactionError(f"Withdrawal failed: {e}")
    finally:
        if conn: conn.close()


def transfer_funds(from_account_id, to_account_id, amount, description="Transfer"):
    amount = Decimal(str(amount)) # Ensure amount is Decimal
    if amount <= 0:
        raise InvalidAmountError("Transfer amount must be positive.")
    if from_account_id == to_account_id:
        raise TransactionError("Cannot transfer funds to the same account.")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # --- Currency Conversion Conceptual Notes for Transfers ---
            # If this were an international transfer where from_account and to_account could have different currencies:
            # 1. Fetch both account details, including their currencies.
            #    from_acc_details = get_account_details_ext(from_account_id, cur) # Assuming get_account_details_ext can take a cursor
            #    to_acc_details = get_account_details_ext(to_account_id, cur)
            # 2. If from_acc_details['currency'] != to_acc_details['currency']:
            #    a. The `amount` parameter would need to be clearly defined (e.g., is it in from_currency or to_currency?).
            #       Assume `amount` is in `from_currency`.
            #    b. Use `core.currency_service.convert_currency(amount, from_acc_details['currency'], to_acc_details['currency'])`
            #       to get `converted_amount_for_to_account`.
            #    c. The debit from `from_account_id` would be `amount`.
            #    d. The credit to `to_account_id` would be `converted_amount_for_to_account`.
            #    e. The `transactions` table would need to store amounts in the account's native currency.
            #       It might also benefit from columns like `original_amount_foreign_currency` and `foreign_currency_code`
            #       if a single transaction leg needs to show both perspectives, or if there are FX fees.
            #    f. Exchange rate variations and transaction fees for currency conversion would also need handling.
            # For now, this function assumes both accounts are in the same currency implicitly,
            # and all amounts are directly transferable. The `accounts.currency` field exists but is not used here for conversion.
            # A dedicated `international_transfer_funds` function would be more appropriate for multi-currency logic.
            # --- End Currency Conversion Notes ---

            acc_id_1, acc_id_2 = min(from_account_id, to_account_id), max(from_account_id, to_account_id)

            cur.execute("SELECT account_id, balance, status_id, overdraft_limit FROM accounts WHERE account_id = %s FOR UPDATE;", (acc_id_1,))
            res_acc1 = cur.fetchone()
            cur.execute("SELECT account_id, balance, status_id, overdraft_limit FROM accounts WHERE account_id = %s FOR UPDATE;", (acc_id_2,))
            res_acc2 = cur.fetchone()

            if not res_acc1 or not res_acc2:
                raise AccountNotFoundError("One or both accounts not found for transfer.")

            from_acc_data = res_acc1 if res_acc1[0] == from_account_id else res_acc2
            to_acc_data = res_acc1 if res_acc1[0] == to_account_id else res_acc2

            from_balance, from_status_id, from_overdraft_limit = Decimal(str(from_acc_data[1])), from_acc_data[2], Decimal(str(from_acc_data[3] or 0.00))
            to_status_id = to_acc_data[2] # to_balance, to_overdraft_limit not directly needed for these checks

            cur.execute("SELECT status_name FROM account_status_types WHERE status_id = %s;", (from_status_id,))
            from_status_name = cur.fetchone()[0]
            cur.execute("SELECT status_name FROM account_status_types WHERE status_id = %s;", (to_status_id,))
            to_status_name = cur.fetchone()[0]

            if from_status_name != 'active':
                raise AccountNotActiveOrFrozenError(f"Origin account {from_account_id} is not active or is frozen. Status: {from_status_name}.")
            if to_status_name != 'active':
                raise AccountNotActiveOrFrozenError(f"Destination account {to_account_id} is not active. Status: {to_status_name}.")

            if from_balance - amount < -from_overdraft_limit:
                raise InsufficientFundsError(f"Insufficient funds in account {from_account_id}. Available: {from_balance + from_overdraft_limit}, Required: {amount}.")

            used_overdraft_before = from_balance < 0
            _update_account_balance(cur, from_account_id, -amount)
            new_from_balance_after_tx = from_balance - amount

            if new_from_balance_after_tx < 0 and (not used_overdraft_before or new_from_balance_after_tx < from_balance):
                try:
                    from core.audit_service import log_event
                    log_event(action_type='OVERDRAFT_USED', target_entity='accounts', target_id=from_account_id,
                              details={"old_balance": float(from_balance), "new_balance": float(new_from_balance_after_tx),
                                       "overdraft_limit": float(from_overdraft_limit), "transfer_amount": float(amount),
                                       "description": "Overdraft from transfer to account " + str(to_account_id)},
                              conn=conn)
                    print(f"Overdraft event logged for account {from_account_id} due to transfer.")
                except Exception as audit_e:
                    print(f"Warning: Failed to log overdraft event for transfer: {audit_e}")

            _update_account_balance(cur, to_account_id, amount)

            transfer_type_id = get_transaction_type_id('transfer', cur)
            debit_tx_id = _record_transaction(cur, from_account_id, transfer_type_id, -amount, f"{description} to account {to_account_id}", related_account_id=to_account_id)
            credit_tx_id = _record_transaction(cur, to_account_id, transfer_type_id, amount, f"{description} from account {from_account_id}", related_account_id=from_account_id)

            conn.commit()
            print(f"Transfer of {amount} from account {from_account_id} to {to_account_id} successful. Debit TxID: {debit_tx_id}, Credit TxID: {credit_tx_id}")
            return debit_tx_id, credit_tx_id

    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, InvalidTransactionTypeError) as e:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error during transfer from {from_account_id} to {to_account_id}: {e}")
        raise TransactionError(f"Transfer failed: {e}")
    finally:
        if conn: conn.close()


def process_wire_transfer(account_id, amount, description="Wire Transfer", direction='outgoing'):
    amount = Decimal(str(amount))
    if amount <= 0:
        raise InvalidAmountError("Wire transfer amount must be positive.")
    if direction not in ['incoming', 'outgoing']:
        raise ValueError("Wire transfer direction must be 'incoming' or 'outgoing'.")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT balance, status_id, overdraft_limit FROM accounts WHERE account_id = %s FOR UPDATE;", (account_id,))
            account_data = cur.fetchone()
            if not account_data:
                raise AccountNotFoundError(f"Account {account_id} not found.")

            balance, status_id, overdraft_limit = Decimal(str(account_data[0])), account_data[1], Decimal(str(account_data[2] or 0.00))

            cur.execute("SELECT status_name FROM account_status_types WHERE status_id = %s;", (status_id,))
            status_name = cur.fetchone()[0]

            if status_name != 'active':
                raise AccountNotActiveOrFrozenError(f"Account {account_id} is not active or is frozen. Status: {status_name}.")

            wire_type_id = get_transaction_type_id('wire_transfer', cur)
            tx_amount = amount

            if direction == 'outgoing':
                if balance - amount < -overdraft_limit:
                    raise InsufficientFundsError(f"Insufficient funds for outgoing wire. Available: {balance + overdraft_limit}, Required: {amount}.")

                used_overdraft_before = balance < 0
                _update_account_balance(cur, account_id, -amount)
                new_balance_after_tx = balance - amount
                tx_amount = -amount

                if new_balance_after_tx < 0 and (not used_overdraft_before or new_balance_after_tx < balance):
                    try:
                        from core.audit_service import log_event
                        log_event(action_type='OVERDRAFT_USED', target_entity='accounts', target_id=account_id,
                                  details={"old_balance": float(balance), "new_balance": float(new_balance_after_tx),
                                           "overdraft_limit": float(overdraft_limit), "wire_amount": float(amount), "direction": "outgoing",
                                           "description": "Overdraft from outgoing wire."},
                                  conn=conn)
                        print(f"Overdraft event logged for account {account_id} due to outgoing wire.")
                    except Exception as audit_e:
                        print(f"Warning: Failed to log wire overdraft event: {audit_e}")
            else: # incoming
                _update_account_balance(cur, account_id, amount)

            transaction_id = _record_transaction(cur, account_id, wire_type_id, tx_amount, description)
            conn.commit()
            print(f"{direction.capitalize()} wire transfer of {amount} for account {account_id} successful. TxID: {transaction_id}")
            return transaction_id

    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, InvalidTransactionTypeError) as e:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error processing wire transfer for account {account_id}: {e}")
        raise TransactionError(f"Wire transfer failed: {e}")
    finally:
        if conn: conn.close()


def process_ach_transaction(account_id, amount, description="ACH Transaction", ach_type='credit'):
    amount = Decimal(str(amount))
    if amount <= 0:
        raise InvalidAmountError("ACH transaction amount must be positive.")
    if ach_type not in ['credit', 'debit']:
        raise ValueError("ACH type must be 'credit' or 'debit'.")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT balance, status_id, overdraft_limit FROM accounts WHERE account_id = %s FOR UPDATE;", (account_id,))
            account_data = cur.fetchone()
            if not account_data:
                raise AccountNotFoundError(f"Account {account_id} not found.")

            balance, status_id, overdraft_limit = Decimal(str(account_data[0])), account_data[1], Decimal(str(account_data[2] or 0.00))

            cur.execute("SELECT status_name FROM account_status_types WHERE status_id = %s;", (status_id,))
            status_name = cur.fetchone()[0]

            if status_name != 'active':
                raise AccountNotActiveOrFrozenError(f"Account {account_id} is not active or is frozen. Status: {status_name}.")

            db_tx_amount = amount
            transaction_type_name = ''

            if ach_type == 'debit':
                if balance - amount < -overdraft_limit:
                    raise InsufficientFundsError(f"Insufficient funds for ACH debit. Available: {balance + overdraft_limit}, Required: {amount}.")

                used_overdraft_before = balance < 0
                _update_account_balance(cur, account_id, -amount)
                new_balance_after_tx = balance - amount
                db_tx_amount = -amount
                transaction_type_name = 'ach_debit'

                if new_balance_after_tx < 0 and (not used_overdraft_before or new_balance_after_tx < balance):
                    try:
                        from core.audit_service import log_event
                        log_event(action_type='OVERDRAFT_USED', target_entity='accounts', target_id=account_id,
                                  details={"old_balance": float(balance), "new_balance": float(new_balance_after_tx),
                                           "overdraft_limit": float(overdraft_limit), "ach_amount": float(amount), "type": "debit",
                                           "description": "Overdraft from ACH debit."},
                                  conn=conn)
                        print(f"Overdraft event logged for account {account_id} due to ACH debit.")
                    except Exception as audit_e:
                        print(f"Warning: Failed to log ACH overdraft event: {audit_e}")
            else: # credit
                _update_account_balance(cur, account_id, amount)
                transaction_type_name = 'ach_credit'

            ach_tx_type_id = get_transaction_type_id(transaction_type_name, cur)
            transaction_id = _record_transaction(cur, account_id, ach_tx_type_id, db_tx_amount, description)

            conn.commit()
            print(f"ACH {ach_type} of {amount} for account {account_id} successful. TxID: {transaction_id}")
            return transaction_id

    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, InvalidTransactionTypeError) as e:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error processing ACH {ach_type} for account {account_id}: {e}")
        raise TransactionError(f"ACH {ach_type} failed: {e}")
    finally:
        if conn: conn.close()


def list_transactions(page=1, per_page=20, account_id_filter=None, transaction_type_filter=None,
                      start_date_filter=None, end_date_filter=None, conn=None):
    """
    Lists transactions with pagination and optional filters.

    Args:
        page (int): Current page number.
        per_page (int): Number of items per page.
        account_id_filter (int, optional): Filter by specific account_id.
        transaction_type_filter (str, optional): Filter by transaction type name.
        start_date_filter (str or date, optional): Filter transactions on or after this date.
        end_date_filter (str or date, optional): Filter transactions on or before this date (inclusive of day).
        conn (psycopg2.connection, optional): Existing database connection.

    Returns:
        dict: Containing 'transactions' list, 'total_transactions', 'page', 'per_page'.
    """
    offset = (page - 1) * per_page

    select_fields = """
        t.transaction_id, t.account_id, a.account_number as primary_account_number,
        t.transaction_type_id, tt.type_name, t.amount, t.transaction_timestamp, t.description,
        t.related_account_id, ra.account_number as related_account_number
    """
    base_from_clause = """
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        JOIN transaction_types tt ON t.transaction_type_id = tt.transaction_type_id
        LEFT JOIN accounts ra ON t.related_account_id = ra.account_id
    """

    count_query_base = f"SELECT COUNT(t.transaction_id) {base_from_clause}"
    list_query_base = f"SELECT {select_fields} {base_from_clause}"

    conditions = []
    params = []

    if account_id_filter is not None:
        conditions.append("t.account_id = %s")
        params.append(account_id_filter)

    if transaction_type_filter:
        conditions.append("tt.type_name = %s")
        params.append(transaction_type_filter)

    if start_date_filter:
        conditions.append("t.transaction_timestamp >= %s")
        params.append(start_date_filter) # Ensure this is a date or timestamp string 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'

    if end_date_filter:
        # To include the whole end day, use < (end_date + 1 day) or adjust timestamp
        if isinstance(end_date_filter, str) and len(end_date_filter) == 10: # 'YYYY-MM-DD'
             end_date_param = end_date_filter + " 23:59:59.999999"
        else:
            end_date_param = end_date_filter
        conditions.append("t.transaction_timestamp <= %s")
        params.append(end_date_param)

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        count_query_base += where_clause
        list_query_base += where_clause

    list_query_base += " ORDER BY t.transaction_timestamp DESC, t.transaction_id DESC LIMIT %s OFFSET %s;"

    list_params = params + [per_page, offset]

    _conn_managed_internally = False
    if not conn:
        conn = get_db_connection()
        _conn_managed_internally = True

    transactions_list_of_dicts = []
    total_transactions = 0
    try:
        with conn.cursor() as cur:
            cur.execute(count_query_base, tuple(params))
            total_transactions = cur.fetchone()[0]

            cur.execute(list_query_base, tuple(list_params))
            records = cur.fetchall()

            colnames = [desc[0] for desc in cur.description]
            for record_tuple in records:
                tx_dict = dict(zip(colnames, record_tuple))
                if 'amount' in tx_dict and tx_dict['amount'] is not None:
                    tx_dict['amount'] = Decimal(str(tx_dict['amount']))
                transactions_list_of_dicts.append(tx_dict)

        return {
            "transactions": transactions_list_of_dicts,
            "total_transactions": total_transactions,
            "page": page,
            "per_page": per_page
        }
    except Exception as e:
        raise TransactionError(f"Error listing transactions: {e}")
    finally:
        if _conn_managed_internally and conn and not conn.closed:
            conn.close()


if __name__ == '__main__':
    print("Running transaction_processing.py direct tests...")

    import core.account_management as am
    from core.customer_management import add_customer, get_customer_by_email, CustomerNotFoundError
    # from core.audit_service import log_event # Not directly called from here, but implicitly by functions

    cust1_email = "tp.testuser1.ovd@example.com"
    cust2_email = "tp.testuser2.ovd@example.com"
    cust1_id, cust2_id = None, None
    acc1_id, acc2_id = None, None

    # Simplified cleanup for testing
    def cleanup_test_tp_user(email, acc_id=None):
        print(f"Attempting cleanup for {email} and account {acc_id}")
        conn_clean = None
        try:
            conn_clean = get_db_connection()
            cur_clean = conn_clean.cursor()
            cust = None
            try:
                cust = get_customer_by_email(email) # This uses its own connection for read
            except CustomerNotFoundError:
                print(f"Customer {email} not found, may already be cleaned.")

            if acc_id:
                 cur_clean.execute("DELETE FROM transactions WHERE account_id = %s;", (acc_id,))
                 cur_clean.execute("DELETE FROM audit_log WHERE target_entity = 'accounts' AND target_id = %s;", (str(acc_id),))
                 cur_clean.execute("DELETE FROM accounts WHERE account_id = %s;", (acc_id,))

            if cust:
                # Delete other accounts if any (e.g. if acc_id was for acc2 and cust1 had another)
                cur_clean.execute("SELECT account_id from accounts WHERE customer_id = %s;",(cust['customer_id'],))
                other_accs = cur_clean.fetchall()
                for other_a_id_tuple in other_accs:
                    other_a_id = other_a_id_tuple[0]
                    cur_clean.execute("DELETE FROM transactions WHERE account_id = %s;", (other_a_id,))
                    cur_clean.execute("DELETE FROM audit_log WHERE target_entity = 'accounts' AND target_id = %s;", (str(other_a_id),))
                    cur_clean.execute("DELETE FROM accounts WHERE account_id = %s;", (other_a_id,))
                cur_clean.execute("DELETE FROM customers WHERE customer_id = %s;", (cust['customer_id'],))
            conn_clean.commit()
            print(f"Cleanup for {email} potentially completed.")
        except Exception as e_cl:
            if conn_clean: conn_clean.rollback()
            print(f"Error in cleanup: {e_cl}")
        finally:
            if conn_clean: conn_clean.close()

    cleanup_test_tp_user(cust1_email) # Clean before running
    cleanup_test_tp_user(cust2_email)

    try:
        print("\n[SETUP] Creating test customers and accounts for transaction tests...")
        cust1_id = add_customer("TP_OVD_Test1", "User1", cust1_email)
        cust2_id = add_customer("TP_OVD_Test2", "User2", cust2_email)

        acc1_id = am.open_account(cust1_id, "checking", initial_balance=Decimal("1000.00"))
        acc2_id = am.open_account(cust2_id, "savings", initial_balance=Decimal("500.00"))
        print(f"Acc1 ID: {acc1_id} (Bal: 1000), Acc2 ID: {acc2_id} (Bal: 500)")
        print("   Reminder: Ensure 'accounts.overdraft_limit' column exists and audit table is set up.")


        print("\n[TESTING DEPOSIT]")
        deposit(acc1_id, Decimal("200.00"), "Cash deposit")
        assert am.get_account_balance(acc1_id) == Decimal("1200.00")
        print(f"   Deposit successful. Acc1 New balance: {am.get_account_balance(acc1_id)}")

        print("\n[TESTING WITHDRAWAL WITH OVERDRAFT]")
        am.set_overdraft_limit(acc1_id, Decimal("100.00"))
        print(f"   Overdraft limit for Acc1 ({acc1_id}) set to 100.00.")

        # Withdraw 1250 from 1200 (50 into overdraft)
        withdraw(acc1_id, Decimal("1250.00"), "Withdrawal into overdraft")
        assert am.get_account_balance(acc1_id) == Decimal("-50.00")
        print(f"   Withdrawal into overdraft successful. Acc1 New balance: {am.get_account_balance(acc1_id)}")

        # Try to withdraw 100 more (current bal -50, limit 100 allows another 50. This should fail)
        print("   Attempting withdrawal exceeding overdraft limit...")
        try:
            withdraw(acc1_id, Decimal("100.00"))
        except InsufficientFundsError:
            print("   Successfully caught withdrawal exceeding overdraft limit.")
        assert am.get_account_balance(acc1_id) == Decimal("-50.00") # Balance should be unchanged


        print("\n[TESTING TRANSFER WITH OVERDRAFT]")
        # Acc1 bal is -50. Overdraft limit 100. Can go 50 more negative from current balance.
        # Transfer 30 from Acc1 to Acc2. Acc1 new bal should be -80.
        transfer_funds(acc1_id, acc2_id, Decimal("30.00"), "Transfer using overdraft")
        assert am.get_account_balance(acc1_id) == Decimal("-80.00")
        assert am.get_account_balance(acc2_id) == Decimal("530.00") # 500 + 30
        print(f"   Transfer using overdraft successful. Acc1: {am.get_account_balance(acc1_id)}, Acc2: {am.get_account_balance(acc2_id)}")

        # Try to transfer 30 more. Bal -80, limit 100. Max usable overdraft from current bal is 20. This should fail.
        print("   Attempting transfer exceeding remaining overdraft...")
        try:
            transfer_funds(acc1_id, acc2_id, Decimal("30.00"))
        except InsufficientFundsError:
            print("   Successfully caught transfer exceeding remaining overdraft.")
        assert am.get_account_balance(acc1_id) == Decimal("-80.00") # Balance unchanged

        print("\nAll transaction processing tests with overdraft completed.")

    except Exception as e:
        import traceback
        print(f"\nAN ERROR OCCURRED IN TRANSACTION PROCESSING TESTS: {e}")
        traceback.print_exc()
    finally:
        print("\n[CLEANUP] Final cleanup after tests...")
        cleanup_test_tp_user(cust1_email, acc1_id)
        cleanup_test_tp_user(cust2_email, acc2_id)
        print("Transaction processing tests finished.")
```
