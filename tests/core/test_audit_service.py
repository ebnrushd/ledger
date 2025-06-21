import pytest
import json
from datetime import datetime

# Import functions and exceptions to be tested
from core.audit_service import (
    log_event,
    log_customer_update,
    log_account_status_change,
    AuditServiceError
)
# For creating a dummy user for user_id FK in audit_log
from core.customer_management import add_customer
# No, need user from users table. Let's create a helper or assume user_id can be None or use a system user.
# The auth_schema.sql inserts some roles. We can insert a dummy user for testing.

@pytest.fixture
def test_user(db_conn):
    """Fixture to create a dummy user and return their ID for audit log tests."""
    # Assumes roles table is populated by auth_schema.sql (e.g., role_id 1 = 'customer' or 'admin')
    # Check if role 'system_process' (role_id 5) exists, otherwise use 'admin' (role_id 3)
    role_id_to_use = 3 # Default to admin
    with db_conn.cursor() as cur_roles:
        cur_roles.execute("SELECT role_id FROM roles WHERE role_name = 'system_process';")
        role_res = cur_roles.fetchone()
        if role_res:
            role_id_to_use = role_res[0]
        else: # Fallback if system_process not found, try admin
            cur_roles.execute("SELECT role_id FROM roles WHERE role_name = 'admin';")
            role_admin_res = cur_roles.fetchone()
            if role_admin_res: role_id_to_use = role_admin_res[0]
            # If admin also not found, test might fail or use hardcoded ID if schema is fixed

    with db_conn.cursor() as cur:
        # Use ON CONFLICT DO NOTHING if user might persist due to test setup issues,
        # though db_conn fixture should clear tables.
        cur.execute(
            "INSERT INTO users (username, password_hash, role_id, email, is_active) "
            "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash RETURNING user_id;",
            ("audit_test_user", "some_hash", role_id_to_use, "audit.test@example.com", True)
        )
        user_id = cur.fetchone()[0]
        db_conn.commit()
        return user_id

# --- Tests for log_event ---
def test_log_event_success(db_conn, test_user):
    """Test successfully logging a generic event."""
    action = "TEST_ACTION"
    entity = "test_entities"
    entity_id = "test_id_123"
    details_dict = {"key1": "value1", "info": "some test data"}

    log_id = log_event(
        action_type=action,
        target_entity=entity,
        target_id=entity_id,
        details=details_dict,
        user_id=test_user
    )
    assert log_id is not None

    # Verify by fetching from audit_log table
    with db_conn.cursor() as cur:
        cur.execute("SELECT user_id, action_type, target_entity, target_id, details_json FROM audit_log WHERE log_id = %s;", (log_id,))
        record = cur.fetchone()
        assert record is not None
        assert record[0] == test_user
        assert record[1] == action
        assert record[2] == entity
        assert record[3] == entity_id
        assert record[4] == details_dict # psycopg2 auto-converts dict to JSONB and back

def test_log_event_success_no_user(db_conn):
    """Test logging an event with no user_id (system event)."""
    log_id = log_event("SYSTEM_BOOT", "system", "hostname1", {"status": "OK"})
    assert log_id is not None
    with db_conn.cursor() as cur:
        cur.execute("SELECT user_id, action_type FROM audit_log WHERE log_id = %s;", (log_id,))
        record = cur.fetchone()
        assert record[0] is None
        assert record[1] == "SYSTEM_BOOT"

def test_log_event_within_existing_transaction(db_conn, test_user):
    """Test logging an event using a passed connection (simulating part of larger transaction)."""
    # db_conn fixture already starts a transaction if autocommit is off, or manages one.
    # For this test, we just pass it. The log_event function should use it.
    # The commit/rollback is handled by db_conn fixture's teardown or test function end.
    # For this test, we'll explicitly commit to check.
    try:
        db_conn.autocommit = False # Ensure we are in a transaction block
        log_id = log_event(
            action_type="PART_OF_TX", target_entity="tx_demo", target_id="tx1",
            details={"step": 1}, user_id=test_user, conn=db_conn
        )
        assert log_id is not None
        # We don't commit here; db_conn fixture or test function wrapper would.
        # To verify it's written, we'd need to query within same transaction or commit.
        # Let's commit to verify this specific log entry.
        db_conn.commit()

        with db_conn.cursor() as cur: # New cursor on same connection
            cur.execute("SELECT action_type FROM audit_log WHERE log_id = %s;", (log_id,))
            assert cur.fetchone()[0] == "PART_OF_TX"

    finally:
        db_conn.autocommit = True # Reset if changed (though fixture re-establishes connection)


# --- Tests for specific event loggers ---
def test_log_customer_update_event(db_conn, test_user):
    """Test the specific logger for customer updates."""
    customer_id_test = 10101
    changed = {"email": "new@example.com", "phone": "555000111"}
    old = {"email": "old@example.com", "phone": "555222333"}

    log_id = log_customer_update(customer_id_test, changed, old, user_id=test_user)
    assert log_id is not None

    with db_conn.cursor() as cur:
        cur.execute("SELECT action_type, target_entity, target_id, details_json FROM audit_log WHERE log_id = %s;", (log_id,))
        record = cur.fetchone()
        assert record[0] == "CUSTOMER_UPDATE"
        assert record[1] == "customers"
        assert record[2] == str(customer_id_test)
        assert record[3]["new_values"] == changed
        assert record[3]["old_values"] == old

def test_log_account_status_change_event(db_conn, test_user):
    """Test the specific logger for account status changes."""
    account_id_test = 20202
    new_stat = "frozen"
    old_stat = "active"
    reason_text = "Customer request due to suspicious activity."

    log_id = log_account_status_change(account_id_test, new_stat, old_stat, reason=reason_text, user_id=test_user)
    assert log_id is not None

    with db_conn.cursor() as cur:
        cur.execute("SELECT details_json FROM audit_log WHERE log_id = %s;", (log_id,))
        details = cur.fetchone()[0]
        assert details["new_status"] == new_stat
        assert details["old_status"] == old_stat
        assert details["reason"] == reason_text

# Note: Testing failure of log_event (e.g., DB down) is harder in unit tests
# as it relies on `execute_query` or connection issues. Such tests are more integration-focused.
# Assume `AuditServiceError` would be raised if `execute_query` fails.
```
