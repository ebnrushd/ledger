from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # For standard login form
from typing import Optional

# Assuming project root is in PYTHONPATH for these imports
from ....dependencies import get_db # Standard DB dependency
from ....models import TokenResponse, UserCreateAPI, UserSchema, HttpError # API Models
from ....config import DEFAULT_CUSTOMER_ROLE_NAME, ACCESS_TOKEN_EXPIRE_DELTA

from core import user_service, customer_management, security, account_management # Core services
from core.user_service import UserAlreadyExistsError, UserServiceError
from core.customer_management import CustomerNotFoundError # Should not happen if creating alongside user
from core.account_management import get_account_status_id as get_status_id_by_name # For initial account status
from core.account_management import open_account as open_initial_account # For initial account
from decimal import Decimal # For initial balance

router = APIRouter(
    prefix="/api/v1/auth", # Prefix for all routes in this router
    tags=["Authentication (API v1)"],
)

@router.post("/login", response_model=TokenResponse, name="api_login_for_access_token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), # Standard form: username & password
    db_conn = Depends(get_db)
):
    """
    Logs in a user and returns an access token.
    Accepts standard OAuth2 form data (username, password).
    """
    user = user_service.authenticate_user(
        username=form_data.username,
        password=form_data.password,
        conn=db_conn
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}, # Standard for bearer token auth
        )
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Or 403 Forbidden
            detail="Inactive user. Please contact support."
        )

    # Data to be encoded in the token
    token_data = {
        "sub": user["username"], # Subject claim: username (or user_id)
        "user_id": user["user_id"],
        "role": user["role_name"],
        # Add other claims as needed, e.g., scopes
    }
    access_token = security.create_access_token(
        data=token_data, expires_delta=ACCESS_TOKEN_EXPIRE_DELTA
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED,
             name="api_register_user",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": HttpError, "description": "Invalid input or role not found"},
                 status.HTTP_409_CONFLICT: {"model": HttpError, "description": "Username or email already exists"}
             })
async def register_user(
    user_in: UserCreateAPI, # Pydantic model for request body
    db_conn = Depends(get_db)
):
    """
    Registers a new user and an associated customer profile.
    Assigns the default 'customer' role to the new user.
    """
    # 1. Get the role_id for the default customer role
    role_id_customer = None
    try:
        with db_conn.cursor() as cur: # Use DictCursor if results are complex
            cur.execute("SELECT role_id FROM roles WHERE role_name = %s;", (DEFAULT_CUSTOMER_ROLE_NAME,))
            role_record = cur.fetchone()
            if role_record:
                role_id_customer = role_record[0]
            else:
                # This is a server configuration issue if default role doesn't exist
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Default role '{DEFAULT_CUSTOMER_ROLE_NAME}' not found in database."
                )
    except Exception as e_role:
        # Log this error
        print(f"Error fetching default customer role ID: {e_role}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not verify user role.")


    # Start a transaction block if not already in one (Depends(get_db) might handle this)
    # For operations spanning multiple service calls that need to be atomic,
    # ensure the connection `db_conn` is used by all and commit/rollback is handled here.
    # The current service functions manage their own commits if conn is not passed or if they create their own.
    # To make user+customer creation atomic, user_service.create_user and customer_management.add_customer
    # should accept `conn` and NOT commit themselves if `conn` is provided.

    # For now, assuming service functions use the passed `conn` and expect this router to commit/rollback.
    # This requires user_service.create_user and customer_management.add_customer to be refactored
    # to not auto-commit when a connection is passed.
    # The overwrite of customer_management.py handled this. user_service.create_user also.

    new_user_id = None
    new_customer_id = None

    try:
        # 2. Create the user first (without customer_id link yet)
        new_user_id = user_service.create_user(
            username=user_in.username,
            password=user_in.password,
            email=user_in.email,
            role_id=role_id_customer,
            is_active=True, # New users are active by default
            conn=db_conn
        )

        # 3. Create the associated customer profile
        new_customer_id = customer_management.add_customer(
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            email=user_in.email, # Can use user's email or a separate one if model allows
            phone_number=user_in.phone_number,
            address=user_in.address,
            conn=db_conn
        )

        # 4. Link the user to the newly created customer_id
        with db_conn.cursor() as cur_link:
            cur_link.execute("UPDATE users SET customer_id = %s WHERE user_id = %s;", (new_customer_id, new_user_id))

        # 5. Create a default 'savings' account in 'pending_approval' state
        try:
            pending_approval_status_id = get_status_id_by_name('pending_approval', conn=db_conn)
            # You might want to make account type, initial balance, currency configurable or based on user_in
            open_initial_account(
                customer_id=new_customer_id,
                account_type='savings', # Default to savings
                initial_balance=Decimal("0.00"), # Default initial balance
                currency='USD', # Default currency
                conn=db_conn,
                initial_status_id=pending_approval_status_id
            )
        except Exception as e_acc:
            # If account opening fails, we should ideally roll back user/customer creation
            if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
            print(f"Failed to open initial account during registration: {e_acc}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating initial account for user.")

        db_conn.commit() # Commit the transaction for user, customer, link, and initial account

    except UserAlreadyExistsError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (UserServiceError, CustomerNotFoundError, Exception) as e: # CustomerNotFoundError is from core.customer_management
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        # Log the error e server-side
        print(f"Registration error: {e}") # Basic logging
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Registration failed: {e}")


    # 5. Fetch the complete user details to return (as UserSchema)
    # get_user_by_id already joins role_name.
    user_details_dict = user_service.get_user_by_id(new_user_id, conn=db_conn)
    if not user_details_dict: # Should not happen if creation succeeded
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve newly created user.")

    return UserSchema(**user_details_dict)

```
