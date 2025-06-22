import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional


from ..dependencies import get_db, get_current_active_user_from_token
from ..models import (
    CustomerCreate, CustomerUpdate, CustomerDetails,
    HttpError, UserSchema
)

try:
    from core import customer_management, audit_service
    from core.customer_management import CustomerNotFoundError
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from core import customer_management, audit_service
    from core.customer_management import CustomerNotFoundError


router = APIRouter(
    prefix="/customers",
    tags=["Customers (v1)"],
    responses={404: {"description": "Not found", "model": HttpError}},
)

# The POST /customers/ endpoint for general customer creation is removed from /api/v1.
# Customer creation is now primarily handled by the /api/v1/auth/register endpoint,
# which creates a user and a linked customer profile together.
# If an admin needs to create customers directly without users, that would be an admin panel function.


@router.get("/me", response_model=CustomerDetails, summary="Get current user's customer profile")
async def get_my_customer_profile(
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    """
    Retrieve the customer profile linked to the currently authenticated user.
    """
    if not current_user.customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No customer profile linked to this user account."
        )
    try:
        # Pass conn to core function
        customer_details = customer_management.get_customer_by_id(current_user.customer_id, conn=db_conn)
        return CustomerDetails(**customer_details)
    except CustomerNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked customer profile not found.")
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred retrieving profile: {e}")


def _data_actually_changed(update_data: dict, current_data_dict: dict) -> bool:
    """Helper to check if any value in update_data is different from current_data."""
    for key, value in update_data.items():
        if key not in current_data_dict or current_data_dict[key] != value:
            return True
    return False

@router.put("/me", response_model=CustomerDetails, summary="Update current user's customer profile")
async def update_my_customer_profile(
    customer_update: CustomerUpdate,
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    """
    Update the customer profile information for the currently authenticated user.
    Only provided fields will be updated.
    """
    if not current_user.customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # 403 because user is auth'd but no profile to update
            detail="No customer profile linked to this user account to update."
        )

    update_data = customer_update.dict(exclude_unset=True)
    if not update_data: # No actual fields sent for update
        # Return current profile or an informative message
        current_customer_details = customer_management.get_customer_by_id(current_user.customer_id, conn=db_conn)
        return CustomerDetails(**current_customer_details)


    try:
        old_customer_details_dict = customer_management.get_customer_by_id(current_user.customer_id, conn=db_conn)

        if not _data_actually_changed(update_data, old_customer_details_dict):
            # No effective change, return current data
            return CustomerDetails(**old_customer_details_dict)

        success = customer_management.update_customer_info(
            customer_id=current_user.customer_id,
            conn=db_conn,
            **update_data # Pass validated and filtered update_data
        )

        # `update_customer_info` raises error on failure or returns True.
        # If it returned False (e.g. no fields changed, though we checked above), handle it.
        # This part might be redundant if _data_actually_changed is comprehensive.
        if not success :
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                 detail="Customer update failed or no actual changes were made by the service.")

        updated_customer_details_dict = customer_management.get_customer_by_id(current_user.customer_id, conn=db_conn)

        # Audit Log: Capture what changed
        actual_changed_fields = {}
        old_values_for_audit = {}
        for key, new_value in update_data.items(): # Use update_data which has only sent fields
            old_value = old_customer_details_dict.get(key)
            # Ensure comparison handles type differences if any (e.g. Decimal vs float)
            # For Pydantic models, data should be consistent.
            if old_value != new_value:
                actual_changed_fields[key] = new_value
                old_values_for_audit[key] = old_value

        if actual_changed_fields: # Only log if there were actual value changes
            audit_service.log_event(
                action_type='CUSTOMER_SELF_PROFILE_UPDATED', # More specific action type
                target_entity='customers',
                target_id=str(current_user.customer_id),
                details={"changed_fields": actual_changed_fields, "old_values": old_values_for_audit},
                user_id=current_user.user_id,
                conn=db_conn
            )

        db_conn.commit() # Commit customer update and audit log together
        return CustomerDetails(**updated_customer_details_dict)

    except CustomerNotFoundError:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found.")
    except ValueError as ve: # Handles duplicate email
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
    except Exception as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        # Log e server-side
        print(f"Error during /customers/me PUT: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred processing your profile update.")


# General /customers/{customer_id} GET and PUT endpoints are removed for v1 user-facing API.
# Admin panel should be used for administrative access to arbitrary customer records.
# If specific cross-user access is needed (e.g. a service accessing another user's customer data),
# it would require its own specific authorization logic beyond user's own /me.
```
