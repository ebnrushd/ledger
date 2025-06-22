import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Optional, List

# Assuming uvicorn runs from project root
from ....dependencies import get_db, get_current_admin_user, require_role
from ....models import (
    HttpError, UserSchema,
    AdminUserListResponse, AdminUserCreateRequest, AdminUserUpdateRequest, StatusResponse
)
from core import user_service, audit_service
from core.user_service import UserNotFoundError, UserAlreadyExistsError, UserServiceError

router = APIRouter(
    prefix="/api/admin/users",
    tags=["Admin API - User Management"],
    dependencies=[Depends(require_role(["admin"]))]
)

@router.get("/me", response_model=UserSchema, summary="Get current authenticated admin user's details", name="get_current_admin_user_me_api")
async def get_current_admin_user_me_api( # Renamed function
    current_admin_user_data: dict = Depends(get_current_admin_user), # This returns basic session data for now
    db_conn = Depends(get_db) # Add db_conn dependency here
):
    """
    Retrieves the complete, up-to-date details for the currently authenticated admin user.
    The `get_current_admin_user` dependency handles basic session validation.
    This endpoint then fetches full details from the database.
    """
    if not current_admin_user_data or "user_id" not in current_admin_user_data:
        # This case should ideally be caught by get_current_admin_user redirecting.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated or user ID missing in session.")

    try:
        # Fetch full, current user details from the database using the user_id from session
        user_details_from_db = user_service.get_user_by_id(current_admin_user_data["user_id"], conn=db_conn)
        # get_user_by_id returns a dict compatible with UserSchema (includes role_name)
        return UserSchema(**user_details_from_db)
    except UserNotFoundError:
        # Should not happen if session user_id is valid, but good to handle (e.g., user deleted after session created)
        # In this case, clear session and force re-login.
        # Forcing re-login from API endpoint is tricky. Client-side interceptor should handle 401.
        # Here, we just signal that the user from session is not found in DB.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User associated with session not found in database. Please re-login.")
    except UserServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching user details: {str(e)}")


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
    user_in: AdminUserCreateRequest,
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
    except (UserServiceError, Exception) as e:
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
    user_in: AdminUserUpdateRequest,
    current_admin: dict = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    """Update an existing user's details."""
    admin_id_for_audit = current_admin.get('user_id')
    update_data_dict = user_in.dict(exclude_unset=True)

    if not update_data_dict:
        # Fetch current data and return if no update fields provided
        try:
            current_user_data = user_service.get_user_by_id(user_id, conn=db_conn)
            return UserSchema(**current_user_data)
        except UserNotFoundError:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if "password" in update_data_dict and update_data_dict["password"] and len(update_data_dict["password"]) < 8 :
         raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 8 characters long if provided.")

    try:
        success = user_service.update_user(
            user_id=user_id,
            update_data=update_data_dict,
            admin_user_id=admin_id_for_audit,
            conn=db_conn
        )

        if success:
            audit_details = {k: v for k, v in update_data_dict.items() if k != "password"}
            if "password" in update_data_dict and update_data_dict["password"]:
                audit_details["password_changed"] = True

            audit_service.log_event(
                action_type='ADMIN_API_USER_UPDATED', target_entity='users', target_id=str(user_id),
                details=audit_details, user_id=admin_id_for_audit, conn=db_conn
            )
            db_conn.commit()
        # If success is False (no actual change), no audit, no commit needed beyond what service did.

        updated_user_data = user_service.get_user_by_id(user_id, conn=db_conn)
        return UserSchema(**updated_user_data)

    except UserNotFoundError: # Raised by update_user if initial fetch fails
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found for update.")
    except UserAlreadyExistsError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (UserServiceError, Exception) as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        print(f"Error updating user via API: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update user.")

```
