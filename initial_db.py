import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

def get_db_connection_direct():
    """Establishes a direct database connection using environment variables."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set.")
    return psycopg2.connect(db_url)

def execute_sql_from_file(conn, filepath):
    """Executes SQL commands from a given file."""
    print(f"Executing SQL from {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    # Split script into individual statements if necessary,
    # but psycopg2 can often handle multi-statement strings directly.
    # However, some complex DDL or plpgsql blocks might require careful splitting or execution.
    # For simplicity, assuming direct execution works for these schema files.
    # If issues arise, splitting by ';' (while respecting string literals and comments) might be needed.
    try:
        with conn.cursor() as cur:
            cur.execute(sql_script)
        conn.commit()
        print(f"Successfully executed {filepath}")
    except Exception as e:
        conn.rollback()
        print(f"Error executing {filepath}: {e}")
        raise

def main():
    load_dotenv() # Load .env file for DATABASE_URL

    schema_files = [
        "schema.sql",
        "auth_schema.sql", # Contains roles, users, permissions - should run after main schema if it has FKs to it, or define base types first.
                           # For this project, auth_schema is mostly independent or defines its own tables.
        "schema_updates.sql", # Contains overdraft_limit, fee_types etc.
        "schema_audit.sql"    # Contains audit_log table
    ]

    conn = None
    try:
        conn = get_db_connection_direct()
        print("Successfully connected to the database.")

        for sql_file in schema_files:
            if not os.path.exists(sql_file):
                print(f"Warning: SQL schema file {sql_file} not found. Skipping.")
                continue
            execute_sql_from_file(conn, sql_file)

        print("\nDatabase initialization complete.")
        print("NOTE: This script creates tables and pre-populates essential lookup data.")
        print("It does not handle migrations for existing data. Run with caution on existing databases.")

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except psycopg2.Error as dbe:
        print(f"Database Connection Error: {dbe}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
```
