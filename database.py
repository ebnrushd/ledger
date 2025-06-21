import psycopg2
import os

# It's good practice to use environment variables for connection details
DB_NAME = os.getenv("DB_NAME", "sql_ledger_db")
DB_USER = os.getenv("DB_USER", "ledger_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "securepassword123") # Replace with a strong password in a real scenario
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        # In a real application, you might want to raise the exception
        # or handle it more gracefully (e.g., retry, log extensively).
        raise

def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Executes a given SQL query with optional parameters.

    Args:
        query (str): The SQL query to execute.
        params (tuple, optional): Parameters to substitute into the query. Defaults to None.
        fetch_one (bool, optional): True to fetch one row. Defaults to False.
        fetch_all (bool, optional): True to fetch all rows. Defaults to False.
        commit (bool, optional): True to commit the transaction. Defaults to False.

    Returns:
        tuple or list of tuples or None: Query result based on fetch_one/fetch_all.
                                        Returns None if no fetch is requested or on error.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, params)

        if commit:
            conn.commit()
            if cur.description: # Check if there's something to fetch (e.g. RETURNING id)
                 if fetch_one:
                    return cur.fetchone()
                 elif fetch_all:
                    return cur.fetchall()
            return None # Or True to indicate commit success

        if fetch_one:
            return cur.fetchone()
        if fetch_all:
            return cur.fetchall()

        return None # Should not happen if one of the flags is true, or implies no return needed.

    except (psycopg2.Error, Exception) as e:
        if conn:
            conn.rollback() # Rollback on error
        print(f"Database query error: {e}")
        # Consider re-raising or specific error handling
        # For now, returning None or raising an error to signal failure
        raise # Re-raise the exception to be handled by the caller
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    # Example usage (optional, for testing connection)
    # Ensure your PostgreSQL server is running and configured
    # and the database/user exist.
    # You might need to run schema.sql first.
    print("Attempting to connect to the database...")
    try:
        conn = get_db_connection()
        print("Connection successful!")
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        print(f"PostgreSQL version: {db_version[0]}")
        cur.close()
        conn.close()

        # Test execute_query (assuming account_status_types table exists and has data)
        print("\nTesting execute_query to fetch account statuses:")
        statuses = execute_query("SELECT status_name FROM account_status_types;", fetch_all=True)
        if statuses:
            for status in statuses:
                print(f"- {status[0]}")
        else:
            print("Could not fetch statuses or table is empty.")

    except Exception as e:
        print(f"Failed to connect or query database during initial test: {e}")
        print("Please ensure your PostgreSQL server is running, the database and user are configured,")
        print(f"and you have run the schema.sql script to create tables (DB: {DB_NAME}, User: {DB_USER}).")
        print("You might also need to set DB_PASSWORD environment variable or update it in database.py.")

    # Note: For the application to run, you'd typically set up the DB and user:
    # sudo -u postgres psql
    # CREATE DATABASE sql_ledger_db;
    # CREATE USER ledger_user WITH PASSWORD 'securepassword123';
    # GRANT ALL PRIVILEGES ON DATABASE sql_ledger_db TO ledger_user;
    # \q
    # psql -U ledger_user -d sql_ledger_db -h localhost < schema.sql
    #
    # And potentially set environment variables:
    # export DB_NAME="sql_ledger_db"
    # export DB_USER="ledger_user"
    # export DB_PASSWORD="securepassword123"
    # export DB_HOST="localhost"
    # export DB_PORT="5432"
