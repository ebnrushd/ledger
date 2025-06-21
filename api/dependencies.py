import sys
import os
from fastapi import HTTPException, status

# Add project root to sys.path to allow importing 'database'
# This assumes the 'api' directory is directly under the project root 'sql-ledger/'
# and 'database.py' is also under 'sql-ledger/'.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Check if 'database.py' can be imported
try:
    from database import get_db_connection, DB_NAME, DB_USER # For testing path
    # print(f"Successfully imported 'database' module from {os.path.join(project_root, 'database.py')}")
    # print(f"DB_NAME: {DB_NAME}, DB_USER: {DB_USER}")
except ImportError as e:
    print(f"Error importing 'database' module in api/dependencies.py: {e}")
    print(f"Project root trying to be added to sys.path: {project_root}")
    print(f"Current sys.path: {sys.path}")
    # If running uvicorn from project root (e.g. `sql-ledger/`), then `database.py` should be directly importable.
    # If uvicorn is run from `sql-ledger/api/`, then `../database.py` is needed.
    # The above path adjustment `os.path.join(os.path.dirname(__file__), '..', '..')` assumes uvicorn is run from `api` directory,
    # and `sql-ledger` is the parent of `api`.
    # If uvicorn is run from `sql-ledger` (project root), `database` should be directly importable without sys.path manipulation here.
    # Let's adjust for running uvicorn from project root:
    # The path adjustment should be for when `api` is a package INSIDE `sql-ledger`.
    # So, `from ..database import get_db_connection` would be if `api` is a package and `database` is a sibling module.
    # However, for uvicorn `api.main:app`, it usually means `PYTHONPATH` includes the project root.
    # Let's assume PYTHONPATH is set up correctly by how uvicorn is run (e.g. from project root)
    # and remove complex sys.path manipulation here. If there are issues, they will show at runtime.
    # The primary way to ensure this works is to run uvicorn from the project root:
    # `uvicorn api.main:app --reload` from the `sql-ledger` directory.

# Corrected import assuming uvicorn is run from project root.
# This means the project root (containing `database.py` and the `api` folder) is in PYTHONPATH.
from database import get_db_connection, DB_NAME, DB_USER, DB_HOST, DB_PASSWORD, DB_PORT
import psycopg2

def get_db():
    """
    FastAPI dependency that provides a database connection/session per request.
    """
    # print(f"Attempting DB connection: User={DB_USER}, DB={DB_NAME}, Host={DB_HOST}, Pwd={'*' * len(DB_PASSWORD)}, Port={DB_PORT}")
    try:
        conn = get_db_connection()
        # print("DB Connection successful in get_db()")
        yield conn
    except psycopg2.OperationalError as e:
        # print(f"DB Connection failed in get_db(): {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {e}"
        )
    except Exception as e_gen: # Catch any other potential errors during connection
        # print(f"Generic DB setup error in get_db(): {e_gen}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred with database setup: {e_gen}"
        )
    finally:
        if 'conn' in locals() and conn:
            # print("Closing DB Connection in get_db()")
            conn.close()

# Placeholder for authentication dependency (to be developed further)
# from fastapi.security import OAuth2PasswordBearer
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Example token URL

async def get_current_user_placeholder(): # DependsOn(oauth2_scheme: str = Depends(oauth2_scheme))
    """
    Placeholder dependency for fetching the current authenticated user.
    In a real application, this would validate the token and return user details.
    For now, it can return a dummy user or None.
    """
    # print("get_current_user_placeholder called")
    # This is where you would integrate with your auth_schema.sql, users table, roles etc.
    # For example, decode a JWT token, look up user_id, fetch user from DB.
    # For this subtask, no actual authentication logic.
    return {"username": "testuser", "user_id": 0, "role": "admin_placeholder"} # Dummy user

if __name__ == '__main__':
    # Test the get_db dependency (basic connection test)
    print("Testing database dependency...")
    try:
        db_gen = get_db()
        conn = next(db_gen)
        print(f"Successfully obtained DB connection: {type(conn)}")
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"PostgreSQL version: {version[0]}")
        cur.close()
    except StopIteration:
        print("StopIteration from get_db() generator, check for exceptions inside.")
    except HTTPException as http_e:
        print(f"HTTPException during test: {http_e.detail}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'conn' in locals() and conn: # conn might not be defined if next(db_gen) failed
            try:
                next(db_gen) # To execute the finally block in get_db
            except StopIteration:
                 print("Connection closed by get_db dependency.")
```
