from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse

# Assuming uvicorn runs from project root
from ....dependencies import get_db # No admin auth needed for login/logout routes themselves
from ....models import HttpError

# Services
from core import user_service
from core.user_service import UserNotFoundError, UserServiceError # For authenticate_user

import psycopg2.extras # If fetching roles or other details directly

router = APIRouter(
    prefix="/admin", # Matching other admin routes for consistency, login will be /admin/login
    tags=["Admin - Authentication"],
    # No global dependency for admin auth here, as these are the auth routes.
)

@router.get("/login", response_class=HTMLResponse, name="admin_login_form")
async def login_form(request: Request):
    # If user is already logged in, maybe redirect to dashboard? Optional.
    if request.session.get("user_id"):
        return RedirectResponse(url=request.url_for("admin_dashboard"), status_code=status.HTTP_303_SEE_OTHER)

    return request.state.templates.TemplateResponse("admin/login.html", {
        "request": request,
        "page_title": "Admin Login"
    })

@router.post("/login", response_class=HTMLResponse, name="admin_login_submit")
async def login_submit(
    request: Request,
    db_conn = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    error_message = None
    try:
        # authenticate_user returns user details dict (id, username, role_name, etc.) or None
        user = user_service.authenticate_user(username, password, conn=db_conn)

        if user:
            if user.get("role_name") not in ["admin", "teller", "auditor"]: # Example roles allowed for admin panel
                error_message = "You do not have permission to access the admin panel."
                # Optionally, log this attempt with audit_service
                from core.audit_service import log_event
                log_event(action_type='ADMIN_LOGIN_PERMISSION_DENIED', target_entity='users', target_id=str(user.get('user_id')),
                          details={'username': username, 'role': user.get('role_name')}, user_id=user.get('user_id'), conn=db_conn)
                db_conn.commit()
            else:
                # Store essential user info in session
                request.session["user_id"] = user["user_id"]
                request.session["username"] = user["username"]
                request.session["role_name"] = user["role_name"]
                # Optionally, update last_login again here if authenticate_user's commit is not guaranteed with passed conn
                # For now, assuming authenticate_user handles last_login update commit when it manages connection.
                # If conn is passed to authenticate_user, it should commit its own last_login update or rely on this one.
                # The current authenticate_user tries to commit if it manages conn.
                # If conn is passed, it assumes caller commits. Here, we commit after successful audit log.

                from core.audit_service import log_event
                log_event(action_type='ADMIN_LOGIN_SUCCESS', target_entity='users', target_id=str(user["user_id"]),
                          details={'username': username}, user_id=user["user_id"], conn=db_conn)
                db_conn.commit() # Commit audit log for login

                return RedirectResponse(url=request.url_for("admin_dashboard"), status_code=status.HTTP_303_SEE_OTHER)
        else:
            error_message = "Invalid username or password."
            # Optionally log failed login attempt (be careful about logging too much info like username if it doesn't exist)
            # Consider if username exists before logging, to avoid username enumeration issues.
            # For now, generic error.

    except UserServiceError as e:
        error_message = f"Authentication service error: {e}"
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(f"Login error: {e}") # Log this unexpected error
        # db_conn.rollback() # Rollback if an unexpected error occurs mid-transaction (though less likely here)

    return request.state.templates.TemplateResponse("admin/login.html", {
        "request": request,
        "page_title": "Admin Login",
        "error": error_message,
        "username": username # Re-populate username field
    }, status_code=status.HTTP_400_BAD_REQUEST if error_message else status.HTTP_200_OK)


@router.get("/logout", response_class=RedirectResponse, name="admin_logout") # Changed to GET for simplicity
async def logout(request: Request, db_conn = Depends(get_db)):
    admin_user_id = request.session.get("user_id")
    username = request.session.get("username")

    request.session.clear() # Clear the session

    if admin_user_id and username: # Log only if there was a session
        try:
            from core.audit_service import log_event
            log_event(action_type='ADMIN_LOGOUT', target_entity='users', target_id=str(admin_user_id),
                      details={'username': username}, user_id=admin_user_id, conn=db_conn)
            db_conn.commit()
        except Exception as e_audit:
            print(f"Error logging logout event: {e_audit}") # Log but don't fail logout
            if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()


    return RedirectResponse(url=request.url_for("admin_login_form"), status_code=status.HTTP_303_SEE_OTHER)

```
