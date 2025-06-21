import sys
import os
import json

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import execute_query, get_db_connection

class AuditServiceError(Exception):
    """Base exception for AuditService errors."""
    pass

def log_event(action_type, target_entity, target_id, details, user_id=None, conn=None):
    """
    Logs an event to the audit_log table.

    Args:
        action_type (str): Type of action performed (e.g., 'CUSTOMER_UPDATE').
        target_entity (str): The entity that was affected (e.g., 'customers').
        target_id (str or int): The ID of the affected entity.
        details (dict): A dictionary containing details of the change.
                        This will be stored as JSONB.
                        Example: {"old_values": {"email": "a@b.com"}, "new_values": {"email": "c@d.com"}}
        user_id (int, optional): The ID of the user performing the action. Defaults to None.
        conn (psycopg2.connection, optional): An existing database connection.
                                             If None, a new one is created.

    Returns:
        int: The log_id of the newly created audit entry, or None if failed.

    Raises:
        AuditServiceError: If logging fails.
    """
    query = """
        INSERT INTO audit_log (user_id, action_type, target_entity, target_id, details_json)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING log_id;
    """
    # Convert details dict to JSON string for storing in JSONB column
    details_json_str = json.dumps(details)
    params = (user_id, action_type, target_entity, str(target_id), details_json_str)

    # print(f"Logging event: User {user_id}, Action {action_type}, Entity {target_entity}, ID {target_id}, Details {details_json_str}")

    _conn = conn
    try:
        if not _conn: # If no connection passed, manage one internally
            _conn = get_db_connection()

        # If using execute_query, it handles its own cursor and commit for simple cases.
        # But for audit logging, we might want it to be part of a larger transaction.
        # The current execute_query is not designed to take an existing connection.
        # Let's adapt to use cursor directly if conn is provided.

        if conn: # Use the provided connection
            with conn.cursor() as cur:
                cur.execute(query, params)
                log_id = cur.fetchone()[0]
                # The caller of log_event (if providing a conn) is responsible for commit/rollback
            return log_id
        else: # Use execute_query for standalone logging (auto-commit)
            result = execute_query(query, params, fetch_one=True, commit=True)
            if result:
                return result[0]
            return None

    except Exception as e:
        # print(f"Error logging audit event: {e}")
        # In a real app, consider more specific error handling or logging to a fallback.
        raise AuditServiceError(f"Failed to log audit event for {target_entity} ID {target_id}: {e}")
    finally:
        if not conn and _conn and not _conn.closed: # If we created a connection, we close it.
            _conn.close()


def list_audit_logs(page=1, per_page=20, user_id_filter=None, action_type_filter=None,
                    target_entity_filter=None, target_id_filter=None,
                    start_date_filter=None, end_date_filter=None, conn=None):
    """
    Lists audit log entries with pagination and optional filters.

    Args:
        page (int): Current page number.
        per_page (int): Number of items per page.
        user_id_filter (int, optional): Filter by specific user_id.
        action_type_filter (str, optional): Filter by action type (case-insensitive).
        target_entity_filter (str, optional): Filter by target entity (case-insensitive).
        target_id_filter (str, optional): Filter by target ID.
        start_date_filter (str or date, optional): Filter logs on or after this date.
        end_date_filter (str or date, optional): Filter logs on or before this date.
        conn (psycopg2.connection, optional): Existing database connection.

    Returns:
        dict: Containing 'audit_logs' list, 'total_logs', 'page', 'per_page'.
    """
    offset = (page - 1) * per_page

    select_fields = """
        al.log_id, al.timestamp, al.user_id, u.username as user_username,
        al.action_type, al.target_entity, al.target_id, al.details_json
    """
    base_from_clause = """
        FROM audit_log al
        LEFT JOIN users u ON al.user_id = u.user_id
    """

    count_query_base = f"SELECT COUNT(al.log_id) {base_from_clause}"
    list_query_base = f"SELECT {select_fields} {base_from_clause}"

    conditions = []
    params = []

    if user_id_filter is not None:
        conditions.append("al.user_id = %s")
        params.append(user_id_filter)
    if action_type_filter:
        conditions.append("al.action_type ILIKE %s")
        params.append(f"%{action_type_filter}%")
    if target_entity_filter:
        conditions.append("al.target_entity ILIKE %s")
        params.append(f"%{target_entity_filter}%")
    if target_id_filter: # target_id is VARCHAR in schema
        conditions.append("al.target_id ILIKE %s")
        params.append(f"%{target_id_filter}%")
    if start_date_filter:
        conditions.append("al.timestamp >= %s")
        params.append(start_date_filter)
    if end_date_filter:
        if isinstance(end_date_filter, str) and len(end_date_filter) == 10: # 'YYYY-MM-DD'
             end_date_param = end_date_filter + " 23:59:59.999999"
        else:
            end_date_param = end_date_filter
        conditions.append("al.timestamp <= %s")
        params.append(end_date_param)

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        count_query_base += where_clause
        list_query_base += where_clause

    list_query_base += " ORDER BY al.timestamp DESC, al.log_id DESC LIMIT %s OFFSET %s;"

    list_params = params + [per_page, offset]

    _conn_managed_internally = False
    if not conn:
        conn = get_db_connection()
        _conn_managed_internally = True

    audit_logs_list_of_dicts = []
    total_logs = 0
    try:
        with conn.cursor() as cur:
            cur.execute(count_query_base, tuple(params))
            total_logs = cur.fetchone()[0]

            cur.execute(list_query_base, tuple(list_params))
            records = cur.fetchall()

            colnames = [desc[0] for desc in cur.description]
            for record_tuple in records:
                log_dict = dict(zip(colnames, record_tuple))
                # details_json is already a dict/list due to psycopg2 JSONB handling
                audit_logs_list_of_dicts.append(log_dict)

        return {
            "audit_logs": audit_logs_list_of_dicts,
            "total_logs": total_logs,
            "page": page,
            "per_page": per_page
        }
    except Exception as e:
        raise AuditServiceError(f"Error listing audit logs: {e}")
    finally:
        if _conn_managed_internally and conn and not conn.closed:
            conn.close()


# --- Specific Event Logging Functions (Examples) ---

def log_customer_update(customer_id, changed_fields, old_values, user_id=None, conn=None):
    """
    Logs an event when customer information is updated.

    Args:
        customer_id (int): The ID of the customer.
        changed_fields (dict): New values of the fields that were changed.
        old_values (dict): Original values of the fields that were changed.
        user_id (int, optional): User performing the update.
        conn (psycopg2.connection, optional): Existing database connection.
    """
    details = {
        "new_values": changed_fields,
        "old_values": old_values,
        "description": f"Customer record for ID {customer_id} was updated."
    }
    return log_event(
        action_type='CUSTOMER_UPDATE',
        target_entity='customers',
        target_id=customer_id,
        details=details,
        user_id=user_id,
        conn=conn
    )

def log_account_status_change(account_id, new_status, old_status, reason=None, user_id=None, conn=None):
    """
    Logs an event when an account's status changes.

    Args:
        account_id (int): The ID of the account.
        new_status (str): The new status of the account.
        old_status (str): The previous status of the account.
        reason (str, optional): Reason for the status change.
        user_id (int, optional): User performing the change.
        conn (psycopg2.connection, optional): Existing database connection.
    """
    details = {
        "new_status": new_status,
        "old_status": old_status,
        "reason": reason or "Status updated through standard procedure."
    }
    return log_event(
        action_type='ACCOUNT_STATUS_CHANGE',
        target_entity='accounts',
        target_id=account_id,
        details=details,
        user_id=user_id,
        conn=conn
    )


if __name__ == '__main__':
    print("Running audit_service.py direct tests...")
    # Note: These tests require:
    # 1. PostgreSQL running & schema.sql + schema_audit.sql applied.
    # 2. DB connection env vars set.
    # 3. A 'users' table is referenced by 'audit_log' foreign key.
    #    For these tests, we'll assume user_id can be NULL or we use a placeholder.
    #    The FK in schema_audit.sql is to a 'users' table which isn't created yet by the main script.
    #    To make this runnable without `users` table, the FK should be deferred or not created yet.
    #    For now, let's assume we can insert NULL for user_id if users table doesn't exist or FK is not enforced yet.
    #    Alternatively, create a dummy users table and user for testing.

    # For testing, we might need to create a dummy 'users' table and a user if FK is active.
    # Or, temporarily remove/disable the FK constraint in schema_audit.sql for isolated testing.
    # Let's assume user_id = None will work for now.

    test_customer_id = 9999
    test_account_id = 8888
    test_user_id = None # Or a dummy user ID if users table exists and FK is enforced.

    print(f"\n[SETUP] For audit tests to fully pass, ensure 'audit_log' table exists from 'schema_audit.sql'.")
    print(f"A 'users' table is also ideally needed for the user_id foreign key in 'audit_log'.")
    print(f"If 'users' table doesn't exist, ensure user_id can be NULL in audit_log or tests might fail on FK constraint.")

    try:
        print("\n1. Logging a generic event (user_id as None)...")
        log_id1 = log_event(
            action_type='TEST_EVENT',
            target_entity='test_entity',
            target_id='test_id_123',
            details={"info": "This is a test event", "value": 100},
            user_id=test_user_id
        )
        if log_id1:
            print(f"   Successfully logged generic event. Log ID: {log_id1}")
        else:
            print("   Failed to log generic event.")

        print("\n2. Logging a customer update event...")
        log_id2 = log_customer_update(
            customer_id=test_customer_id,
            changed_fields={"email": "new.email@example.com", "phone_number": "555-1234"},
            old_values={"email": "old.email@example.com", "phone_number": "555-0000"},
            user_id=test_user_id
        )
        if log_id2:
            print(f"   Successfully logged customer update. Log ID: {log_id2}")
        else:
            print("   Failed to log customer update.")

        print("\n3. Logging an account status change event...")
        log_id3 = log_account_status_change(
            account_id=test_account_id,
            new_status="frozen",
            old_status="active",
            reason="Customer request",
            user_id=test_user_id
        )
        if log_id3:
            print(f"   Successfully logged account status change. Log ID: {log_id3}")
        else:
            print("   Failed to log account status change.")

        print("\n4. Testing logging within a provided connection (simulated)...")
        # This requires a bit more setup to truly test commit/rollback by caller.
        # We'll simulate a call.
        conn = None
        try:
            conn = get_db_connection()
            conn.autocommit = False # Ensure we control transaction

            log_id4 = log_event(
                action_type='TRANSACTION_TEST_EVENT',
                target_entity='test_tx_entity',
                target_id='tx_id_456',
                details={"info": "Event within external transaction"},
                user_id=test_user_id,
                conn=conn
            )
            if log_id4:
                print(f"   Event logged with provided connection (Log ID: {log_id4}). Committing...")
                conn.commit()
                print("   Committed.")
            else:
                print("   Failed to log event with provided connection.")
                conn.rollback()

        except Exception as e_conn_test:
            if conn: conn.rollback()
            print(f"   Error during connection test: {e_conn_test}")
        finally:
            if conn:
                conn.autocommit = True # Reset for safety, though we are closing
                conn.close()

        print("\nAudit service tests completed.")
        print("Verify the 'audit_log' table in your database for these entries.")

    except Exception as e:
        import traceback
        print(f"\nAN ERROR OCCURRED IN AUDIT SERVICE TESTS: {e}")
        traceback.print_exc()
        print("Ensure DB is running, schema applied, and connection details are correct.")
        print("If Foreign Key to 'users' table is active, ensure 'users' table exists and 'user_id' is valid or NULL.")

```
