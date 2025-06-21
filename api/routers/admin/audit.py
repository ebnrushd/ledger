import sys
import os
from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from fastapi.responses import HTMLResponse
from typing import Optional
from datetime import date

# Assuming uvicorn runs from project root
from ....dependencies import get_db, get_current_admin_user, require_role
from ....models import HttpError

# Services
from core import audit_service
from core.audit_service import AuditServiceError

router = APIRouter(
    prefix="/admin/audit_logs",
    tags=["Admin - Audit Log Viewer"],
    dependencies=[Depends(require_role(['admin', 'auditor']))] # Only admins and auditors
)

@router.get("/", response_class=HTMLResponse, name="admin_list_audit_logs")
async def list_all_audit_logs_admin(
    request: Request,
    current_admin: dict = Depends(get_current_admin_user), # For display
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=5, le=100),
    user_id_filter: Optional[int] = Query(None),
    action_type_filter: Optional[str] = Query(None),
    target_entity_filter: Optional[str] = Query(None),
    target_id_filter: Optional[str] = Query(None),
    start_date_filter: Optional[date] = Query(None),
    end_date_filter: Optional[date] = Query(None),
    db_conn = Depends(get_db)
):
    audit_logs_data = {}
    error_message = None

    try:
        audit_logs_data = audit_service.list_audit_logs(
            page=page, per_page=per_page,
            user_id_filter=user_id_filter,
            action_type_filter=action_type_filter,
            target_entity_filter=target_entity_filter,
            target_id_filter=target_id_filter,
            start_date_filter=start_date_filter.isoformat() if start_date_filter else None,
            end_date_filter=end_date_filter.isoformat() if end_date_filter else None,
            conn=db_conn
        )
    except AuditServiceError as e:
        error_message = str(e)
        audit_logs_data = {"audit_logs": [], "total_logs": 0} # Ensure keys exist for template
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        audit_logs_data = {"audit_logs": [], "total_logs": 0}
        print(f"Error in list_all_audit_logs_admin: {e}")


    total_logs = audit_logs_data.get("total_logs", 0)
    total_pages = (total_logs + per_page - 1) // per_page

    start_date_str_filter = start_date_filter.isoformat() if start_date_filter else ""
    end_date_str_filter = end_date_filter.isoformat() if end_date_filter else ""

    return request.state.templates.TemplateResponse("admin/audit_logs_list.html", {
        "request": request, "page_title": "Audit Logs",
        "audit_logs": audit_logs_data.get("audit_logs", []),
        "total_logs": total_logs,
        "current_page": page, "per_page": per_page, "total_pages": total_pages,
        "user_id_filter": user_id_filter, "action_type_filter": action_type_filter,
        "target_entity_filter": target_entity_filter, "target_id_filter": target_id_filter,
        "start_date_filter": start_date_str_filter, "end_date_filter": end_date_str_filter,
        "error": error_message,
        "current_admin_username": current_admin.get('username')
    })

# No detail view for individual audit log entry for now.
```
