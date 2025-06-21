import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional

# Adjust sys.path to include project root to find 'core' and 'database'
# This assumes 'api' is a subdirectory of the project root.
# This method of path adjustment is common for structuring larger projects.
# Better approach: run uvicorn from project root, e.g. `uvicorn api.main:app --reload`
# then imports like `from core import ...` work naturally if project root is in PYTHONPATH.
# For this file, assuming PYTHONPATH is set up correctly by the runner.

from ..dependencies import get_db, get_current_user_placeholder
from ..models import (
    CustomerCreate, CustomerUpdate, CustomerDetails,
    HttpError, StatusResponse
)

# Assuming core modules are importable. This requires 'sql-ledger/' to be in PYTHONPATH.
# This is typically handled by running uvicorn from the 'sql-ledger/' directory.
# Or, if 'sql-ledger' is an installable package.
try:
    from core import customer_management
    from core.customer_management import CustomerNotFoundError
except ImportError:
    # Fallback for environments where 'core' is not directly in PYTHONPATH but one level up
    # (e.g., if PWD is 'api' directory and 'core' is sibling to 'api')
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from core import customer_management
    from core.customer_management import CustomerNotFoundError


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
    responses={404: {"description": "Not found", "model": HttpError}},
)

# Placeholder for current user - replace with actual auth
CurrentUser = Depends(get_current_user_placeholder)

@router.post("/", response_model=CustomerDetails, status_code=status.HTTP_201_CREATED,
             summary="Create a new customer",
             responses={
                 400: {"description": "Invalid input data", "model": HttpError},
                 409: {"description": "Customer with this email already exists", "model": HttpError},
                 500: {"description": "Internal server error", "model": HttpError}
             })
async def create_customer(
    customer: CustomerCreate,
    db_conn: customer_management.psycopg2.extensions.connection = Depends(get_db),
    # current_user: dict = CurrentUser # TODO: Uncomment and use for authorization
):
    """
    Create a new customer profile.
    - **first_name**: Customer's first name (required)
    - **last_name**: Customer's last name (required)
    - **email**: Customer's unique email address (required)
    - **phone_number**: Optional phone number
    - **address**: Optional physical address
    """
    # TODO: Add authorization check - e.g., only admins or tellers can create customers.
    # if current_user['role'] not in ['admin', 'teller']:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create customers")

    try:
        # The core function `add_customer` uses `execute_query` which handles its own connection.
        # For consistency with FastAPI's per-request connection, `add_customer` could be refactored
        # to accept a connection/cursor. For now, we'll use it as is.
        # If `add_customer` were refactored:
        # customer_id = customer_management.add_customer(db_conn, customer.first_name, ...)

        customer_id = customer_management.add_customer(
            first_name=customer.first_name,
            last_name=customer.last_name,
            email=customer.email,
            phone_number=customer.phone_number,
            address=customer.address
        )
        if customer_id is None: # Should not happen if no exception, but as a safeguard
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create customer, no ID returned.")

        # Fetch the created customer to return details
        # `get_customer_by_id` also uses `execute_query`.
        created_customer_details = customer_management.get_customer_by_id(customer_id)
        return CustomerDetails(**created_customer_details)

    except ValueError as ve: # Handles duplicate email from add_customer
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.get("/{customer_id}", response_model=CustomerDetails,
            summary="Get customer details by ID",
            responses={
                403: {"description": "Not authorized", "model": HttpError},
                500: {"description": "Internal server error", "model": HttpError}
            })
async def get_customer(
    customer_id: int,
    db_conn: customer_management.psycopg2.extensions.connection = Depends(get_db),
    # current_user: dict = CurrentUser # TODO: Auth
):
    """
    Retrieve details for a specific customer by their `customer_id`.
    """
    # TODO: Authorization:
    # User might need to be an admin, teller, or the customer themselves.
    # if current_user['role'] not in ['admin', 'teller'] and current_user.get('customer_id') != customer_id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this customer")
    try:
        customer_details = customer_management.get_customer_by_id(customer_id)
        return CustomerDetails(**customer_details)
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.put("/{customer_id}", response_model=CustomerDetails,
            summary="Update customer details",
            responses={
                400: {"description": "Invalid input", "model": HttpError},
                403: {"description": "Not authorized", "model": HttpError},
                409: {"description": "Email already exists for another customer", "model": HttpError},
                500: {"description": "Internal server error", "model": HttpError}
            })
async def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    db_conn: customer_management.psycopg2.extensions.connection = Depends(get_db),
    # current_user: dict = CurrentUser # TODO: Auth
):
    """
    Update information for an existing customer.
    Only provided fields will be updated.
    """
    # TODO: Authorization:
    # User might need to be an admin, or the customer themselves for certain fields.
    # if current_user['role'] != 'admin' and current_user.get('customer_id') != customer_id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this customer")

    # Convert Pydantic model to dict, excluding unset values to only update provided fields
    update_data = customer_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update.")

    try:
        # `update_customer_info` uses `execute_query`.
        # It also internally calls `get_customer_by_id` first.
        success = customer_management.update_customer_info(customer_id, **update_data)

        if not success: # Should be caught by exceptions within update_customer_info generally
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                 detail="Customer update failed for an unknown reason (no specific error raised by core function but no success).")

        updated_customer_details = customer_management.get_customer_by_id(customer_id)

        # Log the update using audit_service
        # Note: `update_customer_info` doesn't return old values easily.
        # A more robust audit would fetch customer before update, then log diff.
        # For now, just logging that an update happened.
        try:
            from core.audit_service import log_customer_update # Assuming log_customer_update exists
            # This is simplified; a real audit log would capture old and new values more precisely.
            # The current `log_customer_update` in `audit_service.py` needs `changed_fields` and `old_values`.
            # This would require fetching the customer state before the update.
            # For this API subtask, we'll skip precise old/new value logging here to avoid overcomplicating the router.
            # Ideally, the core `update_customer_info` function would return old/new values or handle auditing.
            # A simpler audit log entry:
            from core.audit_service import log_event
            log_event(
                action_type='CUSTOMER_API_UPDATE',
                target_entity='customers',
                target_id=str(customer_id),
                details={"updated_fields": list(update_data.keys())},
                # user_id=current_user.get('user_id') # TODO: Use actual user ID
            )
        except Exception as audit_e:
            # Log this failure to log, but don't fail the main operation
            print(f"Warning: Failed to log customer update event for customer {customer_id}: {audit_e}")

        return CustomerDetails(**updated_customer_details)

    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as ve: # Handles duplicate email from update_customer_info
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

# Example of how to get customer by email (if needed, though REST typically uses ID for specific resources)
# @router.get("/by-email/", response_model=CustomerDetails, summary="Get customer by email")
# async def get_customer_by_email_endpoint(email: EmailStr, db_conn = Depends(get_db)):
#     try:
#         customer = customer_management.get_customer_by_email(email)
#         return CustomerDetails(**customer)
#     except CustomerNotFoundError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

```
