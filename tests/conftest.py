import pytest
import psycopg2
import os
import sys
from fastapi.testclient import TestClient

# Add project root to sys.path to allow importing project modules
# This assumes 'tests/' is at the project root, alongside 'core/', 'api/', etc.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import database connection function and core modules for setup
# This relies on the environment variables set in pytest.ini or actual env
from database import get_db_connection, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# --- Test Database Setup ---
# This is a simplified setup. In a real-world scenario, you might use a library
# like 'testcontainers' to spin up a DB, or have more sophisticated migration handling.

def create_test_database_if_not_exists():
    """Creates the test database if it doesn't already exist."""
    conn = None
    try:
        # Connect to the default 'postgres' database or an existing admin DB to create the test DB
        conn = psycopg2.connect(dbname='postgres', user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {DB_NAME};")
            print(f"\nTest database '{DB_NAME}' created.")
        else:
            # print(f"\nTest database '{DB_NAME}' already exists.")
            pass
        cur.close()
    except Exception as e:
        print(f"\nError creating/checking test database '{DB_NAME}': {e}")
        print("Please ensure PostgreSQL is running and the user specified in pytest.ini (DB_USER) has permissions to create databases, or create the test database manually.")
        # pytest.exit(f"Failed to create or connect to test database: {e}", returncode=1) # Exit if DB setup fails
        raise # Re-raise to make it clear in test output
    finally:
        if conn:
            conn.close()

def apply_schemas(db_conn):
    """Applies all SQL schema files to the connected database."""
    print(f"\nApplying schemas to test database '{DB_NAME}'...")
    cur = db_conn.cursor()
    # Order matters due to foreign key dependencies
    schema_files = [
        "schema.sql", # Defines customers, accounts, transactions, etc.
        "schema_updates.sql", # Defines overdraft_limit, fee_types, exchange_rates, reconciliation tables
        "auth_schema.sql", # Defines users, roles, permissions (audit_log refers to users)
        "schema_audit.sql" # Defines audit_log (FK to users might be tricky if users table is cleared often without cascade)
    ]
    for schema_file in schema_files:
        schema_path = os.path.join(project_root, schema_file)
        if not os.path.exists(schema_path):
            print(f"WARNING: Schema file {schema_path} not found. Skipping.")
            continue
        try:
            print(f"  Applying {schema_file}...")
            with open(schema_path, 'r') as f:
                cur.execute(f.read())
            db_conn.commit()
        except Exception as e:
            db_conn.rollback()
            print(f"  ERROR applying {schema_file}: {e}")
            raise # Stop if schema application fails
    cur.close()
    print("Schemas applied successfully.")

def clear_tables(db_conn):
    """Clears data from all tables in a specific order to respect FK constraints."""
    # print(f"Clearing tables in test database '{DB_NAME}'...")
    cur = db_conn.cursor()
    # Order is important: delete from tables that are referenced by others first,
    # or from tables that reference others last.
    # This is a common order; might need adjustment based on exact FKs.
    tables_to_clear = [
        # Tables referenced by many others, or leaf tables in dependencies
        "transactions",
        "audit_log",
        "role_permissions",
        "external_transactions",
        # Tables that reference the ones above, or are referenced by fewer
        "accounts",
        "users",
        "permissions",
        "fee_types",
        "exchange_rates",
        "external_transaction_sources",
        # Base tables
        "customers",
        "account_status_types", # Usually keep lookup data, but for full clean state, clear and re-populate
        "transaction_types",    # Same as above
        "roles",                # Same as above
    ]
    try:
        for table in tables_to_clear:
            # print(f"  Clearing table {table}...")
            cur.execute(f"DELETE FROM {table};")
            # Note: For tables with SERIAL PKs, DELETE doesn't reset the sequence.
            # If tests rely on specific IDs (e.g., 1, 2, 3), you might need `TRUNCATE table RESTART IDENTITY CASCADE;`
            # However, TRUNCATE is DDL and can have locking issues or require higher privileges.
            # For now, using DELETE. Tests should fetch IDs rather than assuming them.

        # Re-populate lookup tables that are cleared
        lookup_schemas = ["schema.sql", "auth_schema.sql", "schema_updates.sql"] # Files containing INSERTs for lookup tables
        for schema_file in lookup_schemas:
            schema_path = os.path.join(project_root, schema_file)
            if not os.path.exists(schema_path): continue
            with open(schema_path, 'r') as f:
                content = f.read()
                # Execute only INSERT statements for lookup data
                # This is a bit simplistic; a better way is to have dedicated seed scripts or check table content.
                # For now, this re-runs parts of schema that have default inserts.
                if "INSERT INTO account_status_types" in content:
                    cur.execute("INSERT INTO account_status_types (status_name) VALUES ('active'), ('frozen'), ('closed') ON CONFLICT (status_name) DO NOTHING;")
                if "INSERT INTO transaction_types" in content:
                     cur.execute("INSERT INTO transaction_types (type_name) VALUES ('deposit'), ('withdrawal'), ('transfer'), ('ach_credit'), ('ach_debit'), ('wire_transfer') ON CONFLICT (type_name) DO NOTHING;")
                if "INSERT INTO roles" in content: # From auth_schema.sql
                    cur.execute("INSERT INTO roles (role_name) VALUES ('customer'), ('teller'), ('admin'), ('auditor'), ('system_process') ON CONFLICT (role_name) DO NOTHING;")
                # Permissions and role_permissions are more complex to selectively re-insert if cleared.
                # For simplicity, if those are cleared, schema re-application for them might be needed or tests must create them.
                # The current `apply_schemas` runs all files, so this re-population might be redundant if schema is applied every time.
                # However, if schema is applied once per session, this is useful for per-test cleanup.
        db_conn.commit()
    except Exception as e:
        db_conn.rollback()
        print(f"  ERROR clearing tables: {e}. This might be due to FK constraints if order is wrong or data still linked.")
        raise
    finally:
        cur.close()

# --- Pytest Fixtures ---

@pytest.fixture(scope="session", autouse=True)
def manage_test_database_lifecycle():
    """
    Session-scoped fixture to create the test DB and apply schemas once.
    `autouse=True` makes it run automatically for the test session.
    """
    print("\n--- Test Session Setup: Managing Test Database ---")
    original_db_name = os.getenv('DB_NAME_ORIG', DB_NAME) # Allow overriding for test DB

    # Ensure we are using the test DB name from pytest.ini or env
    if DB_NAME == original_db_name and not DB_NAME.startswith("test_"):
        # This is a basic safety check.
        # pytest.exit(f"Safety check: DB_NAME '{DB_NAME}' does not look like a test database name. Aborting.", returncode=1)
        print(f"WARNING: DB_NAME '{DB_NAME}' might not be a dedicated test database.")

    create_test_database_if_not_exists() # Creates DB if not present

    # Connect to the (potentially newly created) test database to apply schemas
    conn = None
    try:
        conn = get_db_connection() # Uses DB_NAME from env (set by pytest.ini)
        apply_schemas(conn)
        conn.close()
    except Exception as e:
        if conn: conn.close()
        pytest.exit(f"Failed to apply schemas to test database '{DB_NAME}': {e}", returncode=1)

    yield # Tests run at this point

    # Teardown (optional, e.g., could drop the test database)
    # print(f"\n--- Test Session Teardown: Optionally drop test database '{DB_NAME}' ---")
    # For now, we leave the test database intact for inspection.
    # To drop: connect to 'postgres', then `DROP DATABASE DB_NAME`. Requires no active connections.


@pytest.fixture(scope="function") # Changed from "module" to "function" for better isolation
def db_conn(manage_test_database_lifecycle): # Depends on session-scoped DB setup
    """
    Provides a fresh database connection for each test function and handles cleanup.
    """
    # print("\n--- Test Function Setup: Getting DB connection and clearing tables ---")
    connection = get_db_connection() # Connects to the test DB
    clear_tables(connection) # Clear tables before each test for isolation

    yield connection # Provide the connection to the test

    # Teardown: close connection after test
    # print("\n--- Test Function Teardown: Closing DB connection ---")
    connection.close()


@pytest.fixture(scope="module")
def test_client(manage_test_database_lifecycle): # Ensures DB is set up before API client is created
    """
    Provides a FastAPI TestClient instance for API testing.
    This client will interact with the API that uses the test database.
    """
    # Need to ensure the FastAPI app uses the test database settings.
    # Since `database.py` reads env vars, and pytest.ini sets them for the test env,
    # the app instance created should automatically use the test DB.
    print("\n--- Module Setup: Creating FastAPI TestClient ---")
    from api.main import app # Import the FastAPI app
    client = TestClient(app)
    yield client
    print("\n--- Module Teardown: TestClient done ---")


# --- Example Utility Fixtures (can be expanded) ---

@pytest.fixture
def create_customer_fx(db_conn):
    """Fixture to create a customer and return their ID. Cleans up afterwards (implicitly by clear_tables)."""
    from core.customer_management import add_customer
    def _create_customer(first_name="Test", last_name="User", email_suffix="@example.com", phone="1234567890", address="123 Test St"):
        # Ensure unique email for each creation within a single test if called multiple times
        # However, clear_tables should handle most isolation needs.
        import uuid
        unique_email = f"{first_name.lower()}.{last_name.lower()}.{uuid.uuid4().hex[:6]}{email_suffix}"
        customer_id = add_customer(first_name, last_name, unique_email, phone, address)
        assert customer_id is not None
        return customer_id
    return _create_customer

@pytest.fixture
def create_account_fx(db_conn, create_customer_fx):
    """Fixture to create an account for a customer. Depends on create_customer_fx."""
    from core.account_management import open_account
    def _create_account(customer_id=None, account_type="savings", initial_balance=1000.00):
        if customer_id is None:
            customer_id = create_customer_fx() # Create a default customer if none provided

        account_id = open_account(customer_id, account_type, initial_balance)
        assert account_id is not None
        return account_id
    return _create_account

# --- Admin User & Auth Fixtures ---

@pytest.fixture(scope="function") # Function scope to ensure clean user for each test if needed
def create_admin_user(db_conn):
    """Fixture to create an 'admin' user. Returns user details dict."""
    from core.user_service import create_user, UserAlreadyExistsError, get_user_by_username_for_auth # Assuming get_user_by_username_for_auth exists or use get_user_by_id
    from core.auth_utils import hash_password # For direct creation if create_user doesn't handle ON CONFLICT well for tests

    # Ensure 'admin' role exists (role_id 3 from auth_schema.sql)
    with db_conn.cursor() as cur:
        cur.execute("INSERT INTO roles (role_id, role_name) VALUES (3, 'admin') ON CONFLICT (role_id) DO NOTHING;")
        db_conn.commit()

    username = "test_admin_user"
    email = "test_admin@example.com"
    password = "AdminPassword123!"

    try:
        # Attempt to fetch first, then create if not exists, to handle potential re-runs more gracefully
        # This is complex with hashed passwords. For tests, simpler to delete and recreate or use ON CONFLICT.
        # The db_conn fixture already clears tables, so this should be fine.
        user_id = create_user(username, password, email, role_id=3, conn=db_conn)
        # `create_user` now commits if it manages its own connection, or expects caller to commit if conn is passed.
        # Since db_conn is function-scoped and manages its own transaction lifecycle (implicitly via psycopg2 or explicitly),
        # and create_user uses the passed conn, the commit should happen at the end of the test or when db_conn commits.
        # However, create_user was modified to commit if it creates its own conn.
        # For clarity and to ensure data is available for login test *within this fixture's scope*,
        # we might need an explicit commit if create_user doesn't do it when conn is passed.
        # Let's assume create_user with a passed conn does not commit itself.
        # The db_conn fixture itself doesn't explicitly start/commit transactions per call, relies on psycopg2 default or autocommit.
        # For safety in fixtures setting up data:
        # db_conn.commit() # Ensure user is committed before trying to log in with them.

        # The create_user function in user_service.py now commits if it creates its own connection,
        # or expects the caller to commit if a connection is passed. The test client login will be a separate request.
        # So, the user needs to be in DB before login attempt.
        # The db_conn fixture already handles clearing tables.
        # create_user should use the passed `db_conn` and the commit should be handled by the test logic or fixture using it.
        # For a fixture setting up data that another part of the test (like TestClient login) will use,
        # it's crucial that the setup data is committed.
        # The `db_conn` fixture in conftest.py does not start a transaction itself, psycopg2 connections
        # are by default in "autocommit off" mode after first command, meaning an explicit commit is needed.
        # Let's add an explicit commit after data creation within fixtures that set up data for subsequent actions.
        db_conn.commit()


    except UserAlreadyExistsError: # If user somehow exists from a failed previous cleanup
        print(f"Admin user {username} already exists, fetching...")
        # This part needs a function like get_user_by_username that returns all needed fields including ID.
        # For simplicity, assume create_user handles it or tests are isolated.
        # For now, if it exists, we assume it's fine.
        # A more robust way: query for ID based on username.
        with db_conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE username = %s;", (username,))
            res = cur.fetchone()
            if res: user_id = res[0]
            else: raise # Should not happen if UserAlreadyExistsError was raised by create_user

    return {"user_id": user_id, "username": username, "password": password, "email": email, "role_id": 3, "role_name": "admin"}

@pytest.fixture(scope="function")
def create_teller_user(db_conn):
    """Fixture to create a 'teller' user."""
    from core.user_service import create_user, UserAlreadyExistsError
    with db_conn.cursor() as cur: # Ensure 'teller' role exists (role_id 2)
        cur.execute("INSERT INTO roles (role_id, role_name) VALUES (2, 'teller') ON CONFLICT (role_id) DO NOTHING;")
        db_conn.commit()
    username = "test_teller_user"
    try:
        user_id = create_user(username, "TellerPassword123!", "teller@example.com", role_id=2, conn=db_conn)
        db_conn.commit() # Commit after creation
    except UserAlreadyExistsError:
        with db_conn.cursor() as cur: # Fetch existing if conflict
            cur.execute("SELECT user_id FROM users WHERE username = %s;", (username,))
            user_id = cur.fetchone()[0]
    return {"user_id": user_id, "username": username, "password": "TellerPassword123!", "role_name": "teller"}


@pytest.fixture(scope="function")
def authenticated_client(test_client: TestClient):
    """
    Returns a function that can log in a user and return an authenticated TestClient.
    The returned client will have session cookies set.
    """
    def _authenticate(username, password):
        # Login to get session cookies
        login_data = {"username": username, "password": password}
        response = test_client.post("/admin/login", data=login_data) # Use data for form posts

        assert response.status_code == status.HTTP_303_SEE_OTHER # Redirect on success
        assert "ledger_admin_session" in test_client.cookies # Check for session cookie
        # print(f"Logged in as {username}, session cookie: {test_client.cookies.get('ledger_admin_session')}")
        return test_client # Return the client instance which now has the cookie
    return _authenticate


@pytest.fixture(scope="function")
def admin_client(authenticated_client, create_admin_user):
    """Provides a TestClient authenticated as an 'admin' user."""
    # create_admin_user fixture ensures the admin user exists in the DB.
    # `authenticated_client` logs them in.
    return authenticated_client(create_admin_user["username"], create_admin_user["password"])

@pytest.fixture(scope="function")
def teller_client(authenticated_client, create_teller_user):
    """Provides a TestClient authenticated as a 'teller' user."""
    return authenticated_client(create_teller_user["username"], create_teller_user["password"])


# Add more fixtures as needed for transactions, fees, etc.
```
