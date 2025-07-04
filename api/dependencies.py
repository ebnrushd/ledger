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
    # This placeholder is no longer the primary source for get_current_admin_user
    # return {"username": "testuser", "user_id": 0, "role": "admin_placeholder"}
    pass # Keep it if other non-admin auth might use it, or remove if unused.
         # For now, admin auth will rely on session directly.


# Need Request for session, Status for codes, RedirectResponse for redirecting
from fastapi import Request, status
from fastapi.responses import RedirectResponse

# Define allowed roles for general admin panel access
ADMIN_PANEL_ACCESS_ROLES = ["admin", "teller", "auditor"]


async def get_current_admin_user(request: Request, db_conn = Depends(get_db)): # Added db_conn for potential DB validation
    """
    Authenticates user based on session data for admin panel access.
    Redirects to login if not authenticated or not an authorized role.
    """
    user_id = request.session.get("user_id")
    username = request.session.get("username")
    role_name = request.session.get("role_name")

    if not all([user_id is not None, username, role_name]):
        # Not enough session data, redirect to login with an info message
        login_url = request.url_for("admin_login_form")
        return RedirectResponse(url=f"{login_url}?info_message=Please log in to access the admin panel.",
                                status_code=status.HTTP_307_TEMPORARY_REDIRECT) # 307 to preserve method if POSTed to protected initially

    if role_name not in ADMIN_PANEL_ACCESS_ROLES:
        # Role not allowed for admin panel access at all. Clear session and redirect.
        request.session.clear()
        login_url = request.url_for("admin_login_form")
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT, # Redirect to login after raising error
            detail="You do not have permission to access the admin panel.",
            headers={"Location": f"{login_url}?error_message=Access Denied: Insufficient role."} # Custom header for redirect
        )
        # Alternative to HTTPException for redirect:
        # return RedirectResponse(url=f"{login_url}?error_message=Access Denied: Insufficient role.",
        #                         status_code=status.HTTP_307_TEMPORARY_REDIRECT)


    # Optionally, re-verify user against DB here to ensure still active/valid, though might be overkill per request.
    # from core.user_service import get_user_by_id, UserNotFoundError
    # try:
    #     user_db = get_user_by_id(user_id, conn=db_conn)
    #     if not user_db["is_active"] or user_db["role_name"] != role_name:
    #         request.session.clear()
    #         # Handle inconsistent session state, redirect to login
    #         raise HTTPException(...)
    # except UserNotFoundError:
    #     request.session.clear()
    #     # User in session doesn't exist anymore (e.g., deleted from DB after session created)
    #     # This would be caught by the get_user_by_id call below.
    #     request.session.clear() # Clear invalid session
    #     raise credentials_exception # Re-raise as a general credentials issue forcing re-login

    # Fetch full, current user details from DB to ensure data is up-to-date and user is still valid/active
    try:
        user_details_from_db = user_service.get_user_by_id(user_id, conn=db_conn) # Uses the passed db_conn
        if not user_details_from_db["is_active"]:
            request.session.clear() # Clear session for inactive user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
                headers={"Location": request.url_for("admin_login_form") + "?error_message=Account inactive."} # Custom header for redirect
            )

        # Ensure session role matches DB role (consistency check)
        if user_details_from_db["role_name"] != role_name:
            print(f"Warning: Session role '{role_name}' for user '{username}' mismatches DB role '{user_details_from_db['role_name']}'. Updating session.")
            request.session["role_name"] = user_details_from_db["role_name"]
            # This implies UserSchema should be populated from user_details_from_db

        # Return as UserSchema compatible dict. UserSchema needs all these fields.
        return UserSchema(**user_details_from_db) # Convert to UserSchema (or ensure dict is compatible)

    except user_service.UserNotFoundError:
        request.session.clear() # User in session no longer exists in DB
        login_url = request.url_for("admin_login_form")
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            detail="User not found in database, session cleared. Please log in again.",
            headers={"Location": f"{login_url}?error_message=User not found, please log in again."}
        )
    except Exception as e_db: # Catch other DB errors during user fetch
        print(f"Error fetching user details for session validation: {e_db}")
        # Depending on policy, might clear session or just deny access for this request
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, # Or 500
            detail="Error validating user session against database."
        )


# --- JWT / OAuth2 Dependencies for /api/v1 ---
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError # For specific exception type from python-jose
from typing import List # Ensure List is imported for require_role

# Assuming UserSchema and TokenData are defined in api.models
from ..models import UserSchema, TokenData
from core import user_service, security # For fetching user and decoding token
from ..config import JWT_SECRET_KEY, JWT_ALGORITHM # Though decode_access_token uses this from security.py

# This should match the path of your token issuing endpoint (login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_active_user_from_token(
    token: str = Depends(oauth2_scheme),
    db_conn = Depends(get_db) # Reusing get_db for DB connection
) -> UserSchema:
    """
    Dependency to get the current active user from a JWT token.
    Used to protect /api/v1/... endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    malformed_token_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, # Or 401, depending on desired response for bad token structure
        detail="Malformed token or invalid claims.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # decode_access_token expects credentials_exception to be an instance, not a type
        # Let's pass the type and let it raise, or handle it here.
        # The current decode_access_token raises the passed exception instance.
        token_data = security.decode_access_token(token, credentials_exception=credentials_exception)
        if token_data is None or token_data.username is None:
            # This case should ideally be handled by decode_access_token raising the exception.
            raise malformed_token_exception

    except JWTError: # This can be raised by jwt.decode if token is expired or signature invalid
        raise credentials_exception # Re-raise as the specific credentials exception
    except Exception as e: # Catch any other error during token decoding, including Pydantic validation within decode
        print(f"Unexpected error during token processing: {e}") # Log this
        raise malformed_token_exception


    # Fetch user from database based on username (subject of token)
    user_dict = user_service.get_user_by_username(username=token_data.username, conn=db_conn)
    if user_dict is None:
        raise credentials_exception # User in token not found in DB

    if not user_dict.get("is_active"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Convert dict to UserSchema Pydantic model for type safety and API consistency
    # UserSchema does not include password_hash
    try:
        return UserSchema(**user_dict)
    except ValidationError as e:
        print(f"Error converting user dict to UserSchema: {e}") # Log this
        # This indicates a mismatch between DB data and UserSchema, a server error
        raise HTTPException(status_code=500, detail="Error processing user data.")


# --- RBAC Dependency Factory ---
def require_role(required_roles: List[str]):
    """
    Factory for creating a FastAPI dependency that checks if the authenticated user has one of the required roles.
    """
    async def role_checker(request: Request, current_admin_user: dict = Depends(get_current_admin_user)):
        # get_current_admin_user already ensures user is logged in and has a basic admin panel access role.
        # This dependency adds a more granular check.
        user_role = current_admin_user.get("role_name")
        if user_role not in required_roles:
            # Render a 403 error page
            # To do this cleanly, the exception handler for HTTPException needs to be aware
            # of rendering HTML for admin section. Or, we directly return HTMLResponse here.
            # For now, let's raise HTTPException and assume a global handler might catch it
            # or that the client (browser) will show the JSON error.
            # A better way for HTML pages is to return a TemplateResponse for an error page.

            # Check if request expects HTML, otherwise return JSON
            accept_header = request.headers.get("accept", "")
            if "text/html" in accept_header:
                # This is tricky because dependencies can't directly return TemplateResponse easily
                # if they are also meant to work with non-HTML endpoints.
                # A common pattern is to raise HTTPException and have a custom exception handler
                # in main.py that renders an HTML error page for 403 if originating from /admin.
                # For now, we'll raise a standard HTTPException.
                # The global exception handler in main.py would need to be smart about this.
                # Or, we can try to return HTMLResponse directly if templates are accessible.
                # This is generally not how dependencies work if they are not path operations themselves.
                # So, raising HTTPException is standard. The template display is up to the global handler.
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access Denied: Your role ('{user_role}') is not authorized for this specific action. Required roles: {required_roles}."
                ) # This will be JSON by default.
            else: # API client
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {required_roles}."
                )
        return current_admin_user # Return user if authorized
    return role_checker


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
