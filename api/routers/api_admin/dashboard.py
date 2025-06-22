import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status

# Assuming uvicorn runs from project root
from ....dependencies import get_db, get_current_admin_user, require_role
from ....models import HttpError # For error responses
from ....models import AdminDashboardData # Specific response model for this router

# Services
from core import admin_service
from core.admin_service import AdminServiceError


router = APIRouter(
    prefix="/api/admin/dashboard", # New prefix for JSON API
    tags=["Admin API - Dashboard"],
    dependencies=[Depends(require_role(['admin', 'teller', 'auditor']))] # Same roles as HTML version
)

@router.get("/", response_model=AdminDashboardData)
async def get_admin_dashboard_api(
    current_admin: dict = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    """
    Admin Dashboard Data: Provides summary statistics and recent activity as JSON.
    Requires admin, teller, or auditor authentication.
    """
    try:
        # Pass db_conn to service function
        summary_data_dict = admin_service.get_dashboard_summary_data(conn=db_conn)

        # Convert dict to Pydantic model for response validation and serialization
        # The service function already returns a dict that should match AdminDashboardData structure.
        # If there are discrepancies, this Pydantic parsing will catch them.
        return AdminDashboardData(**summary_data_dict)

    except AdminServiceError as e:
        # Log e server-side
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load dashboard data: {e}"
        )
    except Exception as e_unhandled:
        # Log e_unhandled server-side
        print(f"Unhandled error in API admin dashboard: {e_unhandled}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e_unhandled}"
        )

```
