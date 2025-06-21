import sys
import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse # For rendering HTML templates

# Add project root to sys.path if not already configured for sibling imports
# Assuming uvicorn is run from project root, this might not be strictly necessary
# if PYTHONPATH includes the project root.
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))


from ....dependencies import get_db, get_current_admin_user # Relative import for dependencies
# Or, if api is a top-level package recognized by PYTHONPATH: from api.dependencies import ...

# Services
from core import admin_service
from core.admin_service import AdminServiceError


router = APIRouter(
    prefix="/admin", # All routes in this file will be under /admin
    tags=["Admin - Dashboard"],
    dependencies=[Depends(get_current_admin_user)] # Apply admin auth to all routes in this router
)

# Dependency for admin user, can be more specific if needed
# AdminUser = Depends(get_current_admin_user) # This is how it's used in function signatures


@router.get("/dashboard", response_class=HTMLResponse, name="admin_dashboard") # Added name
async def get_admin_dashboard(
    request: Request, # Needed to access request.state.templates
    current_admin: dict = Depends(get_current_admin_user), # Enforce admin authentication and get user
    db_conn = Depends(get_db) # For core services that might take a connection
):
    """
    Admin Dashboard: Displays summary statistics and recent activity.
    Requires admin authentication.
    """
    # current_admin variable now holds the resolved admin user from the dependency
    # print(f"Admin user accessing dashboard: {current_admin.get('username')}")

    summary_data = {}
    error_message = None
    try:
        # Pass db_conn to service function.
        summary_data = admin_service.get_dashboard_summary_data(conn=db_conn)
    except AdminServiceError as e:
        error_message = f"Could not load all dashboard data: {e}"
    except Exception as e_unhandled:
        error_message = f"An unexpected error occurred: {e_unhandled}"
        # Log e_unhandled server-side (e.g. using a proper logger)
        print(f"Unhandled error in dashboard: {e_unhandled}")


    return request.state.templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "page_title": "Admin Dashboard",
            "summary_data": summary_data,
            "error": error_message, # Pass error message to template
            "current_admin_username": current_admin.get('username') if current_admin else "N/A"
        }
    )

```
