import sys
import os
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import EmailStr, BaseModel
from typing import Optional, List


# Assuming uvicorn runs from project root making 'api' and 'core' top-level.
from ....dependencies import get_db, get_current_admin_user, require_role # Added require_role
from ....models import HttpError

# Services
from core import user_service
from core.user_service import UserNotFoundError, UserAlreadyExistsError, UserServiceError
import psycopg2.extras

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin - User Management"],
    dependencies=[Depends(require_role(["admin"]))] # Ensures only 'admin' role can access user management
)

@router.get("/", response_class=HTMLResponse, name="admin_list_users")
async def list_all_users(
    request: Request,
    current_admin: dict = Depends(get_current_admin_user), # get_current_admin_user is still needed to get user info
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=5, le=100),
    search_query: Optional[str] = Query(None),
    db_conn = Depends(get_db)
):
    """Display list of users with pagination and search."""
    try:
        users_data = user_service.list_users(page=page, per_page=per_page, search_query=search_query, conn=db_conn)
    except UserServiceError as e:
        return request.state.templates.TemplateResponse("admin/users_list.html", {
            "request": request, "page_title": "Manage Users", "users": [], "total_users": 0,
            "current_page": 1, "total_pages": 1, "error": str(e), "search_query": search_query,
            "current_admin_username": current_admin.get('username')
        })

    total_users = users_data["total_users"]
    total_pages = (total_users + per_page - 1) // per_page

    return request.state.templates.TemplateResponse("admin/users_list.html", {
        "request": request, "page_title": "Manage Users",
        "users": users_data["users"],
        "total_users": total_users, "current_page": page, "per_page": per_page, "total_pages": total_pages,
        "search_query": search_query,
        "current_admin_username": current_admin.get('username')
    })

@router.get("/new", response_class=HTMLResponse, name="admin_new_user_form")
async def new_user_form(request: Request, current_admin: dict = Depends(get_current_admin_user), db_conn = Depends(get_db)):
    available_roles = []
    try:
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT role_id, role_name FROM roles ORDER BY role_name;")
            available_roles = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching roles for user form: {e}")

    return request.state.templates.TemplateResponse("admin/user_form.html", {
        "request": request, "page_title": "Create New User", "user": None, "errors": [],
        "form_action_url": router.url_path_for("admin_create_new_user"),
        "available_roles": available_roles,
        "current_admin_username": current_admin.get('username')
    })

@router.post("/new", response_class=HTMLResponse, name="admin_create_new_user")
async def create_new_user(
    request: Request,
    db_conn = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user),
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    role_id: int = Form(...),
    customer_id: Optional[int] = Form(None),
):
    form_data_received = await request.form()
    is_active_val = True if form_data_received.get("is_active") == "on" else False

    errors = []
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    available_roles = []
    try:
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT role_id, role_name FROM roles ORDER BY role_name;")
            available_roles = [dict(row) for row in cur.fetchall()]
    except Exception as e_roles: print(f"Error re-fetching roles: {e_roles}")

    if errors:
        return request.state.templates.TemplateResponse("admin/user_form.html", {
            "request": request, "page_title": "Create New User", "user": None,
            "form_data": form_data_received, "errors": errors,
            "form_action_url": router.url_path_for("admin_create_new_user"),
            "available_roles": available_roles,
            "current_admin_username": current_admin.get('username')
        }, status_code=status.HTTP_400_BAD_REQUEST)

    try:
        admin_id_for_audit = current_admin.get('user_id')

        user_id = user_service.create_user(
            username, password, email, role_id,
            customer_id=customer_id, is_active=is_active_val, conn=db_conn
        )

        from core.audit_service import log_event
        log_event(
            action_type='ADMIN_USER_CREATED', target_entity='users', target_id=str(user_id),
            details={'username': username, 'email': email, 'role_id': role_id, 'is_active': is_active_val, 'customer_id': customer_id},
            user_id=admin_id_for_audit, conn=db_conn
        )
        db_conn.commit()

        return RedirectResponse(url=router.url_path_for("admin_list_users") + "?success_message=User created successfully.",
                                status_code=status.HTTP_303_SEE_OTHER)
    except UserAlreadyExistsError as e: errors.append(str(e))
    except UserServiceError as e: errors.append(f"Failed to create user: {e}")
    except Exception as e: errors.append(f"An unexpected error occurred: {e}")

    if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()

    return request.state.templates.TemplateResponse("admin/user_form.html", {
        "request": request, "page_title": "Create New User", "user": None,
        "form_data": form_data_received, "errors": errors,
        "form_action_url": router.url_path_for("admin_create_new_user"),
        "available_roles": available_roles,
        "current_admin_username": current_admin.get('username')
    }, status_code=status.HTTP_400_BAD_REQUEST)


@router.get("/{user_id}", response_class=HTMLResponse, name="admin_view_user")
async def view_user_detail(request: Request, user_id: int, current_admin: dict = Depends(get_current_admin_user), db_conn = Depends(get_db)):
    try:
        user = user_service.get_user_by_id(user_id, conn=db_conn)
        return request.state.templates.TemplateResponse("admin/user_detail.html", {
            "request": request, "page_title": f"User: {user['username']}", "user": user,
            "current_admin_username": current_admin.get('username')
        })
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except UserServiceError as e:
         return request.state.templates.TemplateResponse("admin/user_detail.html", {
            "request": request, "page_title": "Error", "user": None, "error": str(e),
            "current_admin_username": current_admin.get('username')
        })

@router.get("/{user_id}/edit", response_class=HTMLResponse, name="admin_edit_user_form")
async def edit_user_form(request: Request, user_id: int, current_admin: dict = Depends(get_current_admin_user), db_conn = Depends(get_db)):
    try:
        user = user_service.get_user_by_id(user_id, conn=db_conn)
        available_roles = []
        try:
            with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT role_id, role_name FROM roles ORDER BY role_name;")
                available_roles = [dict(row) for row in cur.fetchall()]
        except Exception as e_roles: print(f"Error fetching roles for user edit form: {e_roles}")

        return request.state.templates.TemplateResponse("admin/user_form.html", {
            "request": request, "page_title": f"Edit User: {user['username']}", "user": user,
            "form_data": user, "errors": [], "available_roles": available_roles,
            "form_action_url": router.url_path_for("admin_update_existing_user", user_id=user_id),
            "current_admin_username": current_admin.get('username')
        })
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except UserServiceError as e:
         return request.state.templates.TemplateResponse("admin/user_form.html", {
            "request": request, "page_title": "Edit User Error", "user": None, "error": str(e),
            "current_admin_username": current_admin.get('username')
        })

@router.post("/{user_id}/edit", response_class=HTMLResponse, name="admin_update_existing_user")
async def update_existing_user(
    request: Request, user_id: int, db_conn = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user),
    username: str = Form(...), email: EmailStr = Form(...),
    password: Optional[str] = Form(None), role_id: int = Form(...),
    customer_id: Optional[int] = Form(None),
):
    form_data_received = await request.form()
    is_active_val = True if form_data_received.get("is_active") == "on" else False

    update_payload = {
        "username": username, "email": email, "role_id": role_id,
        "customer_id": customer_id if customer_id else None,
        "is_active": is_active_val
    }
    if password:
        update_payload["password"] = password

    errors = []
    if password and len(password) < 8:
        errors.append("If changing password, it must be at least 8 characters long.")

    user_for_form_on_error = None
    available_roles_err = []

    try:
        user_for_form_on_error = user_service.get_user_by_id(user_id, conn=db_conn)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found for update.")
    except UserServiceError as e_fetch:
        errors.append(f"Could not verify current user details: {e_fetch}")

    try:
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur_err:
            cur_err.execute("SELECT role_id, role_name FROM roles ORDER BY role_name;")
            available_roles_err = [dict(row) for row in cur_err.fetchall()]
    except Exception as e_roles_err: print(f"Error re-fetching roles on error: {e_roles_err}")

    if errors:
        return request.state.templates.TemplateResponse("admin/user_form.html", {
            "request": request, "page_title": f"Edit User: {user_for_form_on_error['username'] if user_for_form_on_error else ''}",
            "user": user_for_form_on_error, "form_data": form_data_received, "errors": errors,
            "available_roles": available_roles_err,
            "form_action_url": router.url_path_for("admin_update_existing_user", user_id=user_id),
            "current_admin_username": current_admin.get('username')
        }, status_code=status.HTTP_400_BAD_REQUEST)

    try:
        admin_id_for_audit = current_admin.get('user_id')

        success_updated = user_service.update_user(user_id, update_payload, admin_user_id=admin_id_for_audit, conn=db_conn)

        if success_updated:
            from core.audit_service import log_event
            log_payload = {k: v for k,v in update_payload.items() if k != "password"}
            if update_payload.get("password"): log_payload["password_changed"] = True

            log_event(
                action_type='ADMIN_USER_UPDATED', target_entity='users', target_id=str(user_id),
                details={"updated_fields": log_payload},
                user_id=admin_id_for_audit, conn=db_conn
            )
            db_conn.commit()

            return RedirectResponse(url=router.url_path_for("admin_list_users") + "?success_message=User updated successfully.",
                                    status_code=status.HTTP_303_SEE_OTHER)
        else:
            return RedirectResponse(url=router.url_path_for("admin_view_user", user_id=user_id) + "?info_message=No changes detected in user data.",
                                    status_code=status.HTTP_303_SEE_OTHER)

    except UserAlreadyExistsError as e: errors.append(str(e))
    except UserServiceError as e: errors.append(f"Failed to update user: {e}")
    except Exception as e: errors.append(f"An unexpected error occurred: {str(e)}")

    if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()

    return request.state.templates.TemplateResponse("admin/user_form.html", {
        "request": request, "page_title": f"Edit User: {user_for_form_on_error['username'] if user_for_form_on_error else ''}",
        "user": user_for_form_on_error, "form_data": form_data_received, "errors": errors,
        "available_roles": available_roles_err,
        "form_action_url": router.url_path_for("admin_update_existing_user", user_id=user_id),
        "current_admin_username": current_admin.get('username')
    }, status_code=status.HTTP_400_BAD_REQUEST)

```
