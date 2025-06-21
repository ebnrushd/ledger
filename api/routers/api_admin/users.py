import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Optional, List

# Assuming uvicorn runs from project root
from ....dependencies import get_db, get_current_admin_user, require_role
from ....models import ( # Import JSON API specific models
    HttpError, UserSchema,
    AdminUserListResponse, AdminUserCreateRequest, AdminUserUpdateRequest, StatusResponse
)
from core import user_service, audit_service # For audit logging
from core.user_service import UserNotFoundError, UserAlreadyExistsError, UserServiceError

router = APIRouter(
    prefix="/api/admin/users",
    tags=["Admin API - User Management"],
    dependencies=[Depends(require_role(["admin"]))] # Only 'admin' role
)

@router.get("/", response_model=AdminUserListResponse)
async def list_users_api(
    current_admin: dict = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=5, le=100),
    search_query: Optional[str] = Query(None),
    db_conn = Depends(get_db)
):
    """Retrieve a paginated list of users with optional search."""
    try:
        users_data_dict = user_service.list_users(
            page=page, per_page=per_page, search_query=search_query, conn=db_conn
        )
        # Convert user dicts to UserSchema if list_users doesn't already return Pydantic models
        # Assuming list_users returns dicts that are compatible with UserSchema
        return AdminUserListResponse(
            users=[UserSchema(**user) for user in users_data_dict.get("users", [])],
            total_items=users_data_dict.get("total_users", 0),
            total_pages=(users_data_dict.get("total_users", 0) + per_page - 1) // per_page,
            page=page,
            per_page=per_page
        )
    except UserServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e_unhandled:
        print(f"Unhandled error in list_users_api: {e_unhandled}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching users.")

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user_api(
    user_in: AdminUserCreateRequest, # Use Pydantic model for request body
    current_admin: dict = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    """Create a new user."""
    admin_id_for_audit = current_admin.get('user_id')
    try:
        user_id = user_service.create_user(
            username=user_in.username,
            password=user_in.password,
            email=user_in.email,
            role_id=user_in.role_id,
            customer_id=user_in.customer_id,
            is_active=user_in.is_active,
            conn=db_conn
        )

        audit_service.log_event(
            action_type='ADMIN_API_USER_CREATED', target_entity='users', target_id=str(user_id),
            details=user_in.dict(), user_id=admin_id_for_audit, conn=db_conn
        )
        db_conn.commit()

        created_user_data = user_service.get_user_by_id(user_id, conn=db_conn)
        return UserSchema(**created_user_data)

    except UserAlreadyExistsError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (UserServiceError, Exception) as e: # Catch other service errors or unexpected
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        print(f"Error creating user via API: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create user: {e}")


@router.get("/{user_id}", response_model=UserSchema)
async def get_user_api(
    user_id: int,
    current_admin: dict = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    """Retrieve details for a specific user."""
    try:
        user_data = user_service.get_user_by_id(user_id, conn=db_conn)
        return UserSchema(**user_data)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except UserServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{user_id}", response_model=UserSchema)
async def update_user_api(
    user_id: int,
    user_in: AdminUserUpdateRequest, # Pydantic model for request body
    current_admin: dict = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    """Update an existing user's details."""
    admin_id_for_audit = current_admin.get('user_id')
    update_data_dict = user_in.dict(exclude_unset=True)

    if not update_data_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update.")

    # Password validation if present
    if "password" in update_data_dict and update_data_dict["password"] and len(update_data_dict["password"]) < 8 :
         raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 8 characters long if provided.")

    try:
        # `update_user` service function already fetches current state for audit diff if needed
        # and returns True/False.
        success = user_service.update_user(
            user_id=user_id,
            update_data=update_data_dict,
            admin_user_id=admin_id_for_audit, # For potential internal use by service, though audit is done here
            conn=db_conn
        )

        if success:
            # Audit log for the update
            # For JSON API, it's good practice for update_user to return the changed fields for audit details
            # The current user_service.update_user builds an audit diff but doesn't return it.
            # For now, logging the payload that was sent for update.
            audit_details = {k: v for k, v in update_data_dict.items() if k != "password"}
            if "password" in update_data_dict and update_data_dict["password"]:
                audit_details["password_changed"] = True

            audit_service.log_event(
                action_type='ADMIN_API_USER_UPDATED', target_entity='users', target_id=str(user_id),
                details=audit_details, user_id=admin_id_for_audit, conn=db_conn
            )
            db_conn.commit()
        elif not update_data_dict : # If exclude_unset made it empty, or service determined no change
             # This case should be caught by the check above. If service returns False, means no data changed.
             # No need to commit or log audit if no change.
             pass


        updated_user_data = user_service.get_user_by_id(user_id, conn=db_conn)
        return UserSchema(**updated_user_data)

    except UserNotFoundError:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found for update.")
    except UserAlreadyExistsError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (UserServiceError, Exception) as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        print(f"Error updating user via API: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update user: {e}")

# No DELETE endpoint for users for now, usually involves soft delete (is_active=False)
# which is handled by PUT /admin/api/users/{user_id} with AdminUserUpdateRequest.
```
