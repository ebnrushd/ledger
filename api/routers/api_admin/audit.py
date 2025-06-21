import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from datetime import date

# Assuming uvicorn runs from project root
from ....dependencies import get_db, get_current_admin_user, require_role
from ....models import ( # Import JSON API specific models
    HttpError, AuditLogEntry, AdminAuditLogListResponse, UserSchema
)

# Services
from core import audit_service
from core.audit_service import AuditServiceError

router = APIRouter(
    prefix="/api/admin/audit_logs",
    tags=["Admin API - Audit Log Viewer"],
    dependencies=[Depends(require_role(['admin', 'auditor']))]
)

@router.get("/", response_model=AdminAuditLogListResponse)
async def list_audit_logs_api_admin( # Renamed
    current_admin: UserSchema = Depends(get_current_admin_user),
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
    """Retrieve a paginated list of audit log entries with optional filters."""
    try:
        audit_logs_data_dict = audit_service.list_audit_logs(
            page=page, per_page=per_page,
            user_id_filter=user_id_filter,
            action_type_filter=action_type_filter,
            target_entity_filter=target_entity_filter,
            target_id_filter=target_id_filter,
            start_date_filter=start_date_filter.isoformat() if start_date_filter else None,
            end_date_filter=end_date_filter.isoformat() if end_date_filter else None,
            conn=db_conn
        )

        # list_audit_logs returns dicts that should be compatible with AuditLogEntry model
        # (details_json is handled correctly by Pydantic if it's already a dict/list)
        return AdminAuditLogListResponse(
            audit_logs=[AuditLogEntry(**log) for log in audit_logs_data_dict.get("audit_logs", [])],
            total_items=audit_logs_data_dict.get("total_logs", 0),
            total_pages=(audit_logs_data_dict.get("total_logs", 0) + per_page - 1) // per_page,
            page=page,
            per_page=per_page
        )
    except AuditServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e_unhandled:
        print(f"Unhandled error in list_audit_logs_api_admin: {e_unhandled}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching audit logs.")

# No detail view for individual audit log entry API for now.
# The list view provides details_json. If a specific GET by log_id is needed, it can be added.
```
