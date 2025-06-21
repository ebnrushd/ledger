import sys
import os
from fastapi import APIRouter, Depends, Request, Query, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from decimal import Decimal
from typing import Optional

# Assuming uvicorn runs from project root
from ....dependencies import get_db, get_current_admin_user, require_role
from ....models import HttpError

# Services
from core import account_management, customer_management, transaction_processing
from core.account_management import AccountNotFoundError, AccountStatusError, InvalidAccountTypeError, AccountError, SUPPORTED_ACCOUNT_TYPES
from core.customer_management import CustomerNotFoundError
from core.audit_service import log_event

import psycopg2.extras
from datetime import date

router = APIRouter(
    prefix="/admin/accounts",
    tags=["Admin - Account Management"],
    dependencies=[Depends(require_role(['admin', 'teller', 'auditor']))]
)

@router.get("/", response_class=HTMLResponse, name="admin_list_accounts")
async def list_all_accounts_admin(
    request: Request,
    current_admin: dict = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=5, le=100),
    search_query: Optional[str] = Query(None, description="Search Account #, Customer ID, Name, Email"),
    status_filter: Optional[str] = Query(None, description="Filter by account status (active, frozen, closed)"),
    account_type_filter: Optional[str] = Query(None, description="Filter by account type"),
    customer_id_filter: Optional[int] = Query(None),
    db_conn = Depends(get_db)
):
    accounts_data = {}
    error_message = None
    available_statuses = []
    available_account_types = SUPPORTED_ACCOUNT_TYPES

    try:
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur_status:
            cur_status.execute("SELECT status_id, status_name FROM account_status_types ORDER BY status_name;")
            available_statuses = [dict(row) for row in cur_status.fetchall()]

        accounts_data = account_management.list_accounts(
            page=page, per_page=per_page,
            search_query=search_query,
            status_filter=status_filter,
            account_type_filter=account_type_filter,
            customer_id_filter=customer_id_filter,
            conn=db_conn
        )
    except AccountError as e:
        error_message = str(e)
        accounts_data = {"accounts": [], "total_accounts": 0} # Ensure keys exist for template
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        accounts_data = {"accounts": [], "total_accounts": 0}
        print(f"Error in list_all_accounts_admin: {e}")

    total_accounts = accounts_data.get("total_accounts", 0)
    total_pages = (total_accounts + per_page - 1) // per_page

    return request.state.templates.TemplateResponse("admin/accounts_list.html", {
        "request": request, "page_title": "Manage Accounts",
        "accounts": accounts_data.get("accounts", []),
        "total_accounts": total_accounts,
        "current_page": page, "per_page": per_page, "total_pages": total_pages,
        "search_query": search_query, "status_filter": status_filter,
        "account_type_filter": account_type_filter, "customer_id_filter": customer_id_filter,
        "available_statuses": available_statuses,
        "available_account_types": available_account_types,
        "error": error_message,
        "current_admin_username": current_admin.get('username')
    })

@router.get("/{account_id}", response_class=HTMLResponse, name="admin_view_account")
async def view_account_detail_admin(
    request: Request, account_id: int,
    current_admin: dict = Depends(get_current_admin_user),
    success_message: Optional[str] = Query(None),
    info_message: Optional[str] = Query(None),
    db_conn = Depends(get_db)
):
    account_details = None; customer_details = None; recent_transactions = []
    error_message = None; available_statuses = []

    try:
        account_details = account_management.get_account_by_id(account_id, conn=db_conn)
        if account_details:
            customer_details = customer_management.get_customer_by_id(account_details['customer_id'], conn=db_conn)
            recent_transactions = account_management.get_transaction_history(account_id, limit=10, conn=db_conn)

        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur_status:
            cur_status.execute("SELECT status_id, status_name FROM account_status_types ORDER BY status_name;")
            available_statuses = [dict(row) for row in cur_status.fetchall()]

    except AccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    except CustomerNotFoundError:
        error_message = "Customer associated with this account not found." # Show on page, not as HTTP error
    except Exception as e:
        error_message = f"Error fetching account details: {e}"
        print(f"Error in view_account_detail_admin: {e}")

    return request.state.templates.TemplateResponse("admin/account_detail.html", {
        "request": request, "page_title": f"Account: {account_details['account_number'] if account_details else 'N/A'}",
        "account": account_details, "customer": customer_details,
        "transactions": recent_transactions, "available_statuses": available_statuses,
        "error": error_message, "success_message": success_message, "info_message": info_message,
        "current_date": date.today(),
        "current_admin_username": current_admin.get('username')
    })

@router.post("/{account_id}/status", response_class=HTMLResponse, name="admin_update_account_status",
             dependencies=[Depends(require_role(["admin"]))])
async def update_account_status_admin_form_post( # Renamed to avoid conflict if another func has same name
    request: Request, account_id: int,
    status_name: str = Form(..., alias="status"),
    current_admin: dict = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    admin_user_id = current_admin.get('user_id')
    error_message_form = None
    old_status = "N/A"
    try:
        current_account_details = account_management.get_account_by_id(account_id, conn=db_conn)
        old_status = current_account_details['status_name']

        if old_status == status_name:
             return RedirectResponse(url=router.url_path_for("admin_view_account", account_id=account_id) + "?info_message=No change in status.",
                                status_code=status.HTTP_303_SEE_OTHER)

        # Pass conn to core function
        account_management.update_account_status(account_id, status_name, conn=db_conn, admin_user_id=admin_user_id)

        log_event(
            action_type='ADMIN_ACCOUNT_STATUS_CHANGE', target_entity='accounts', target_id=str(account_id),
            details={'old_status': old_status, 'new_status': status_name},
            user_id=admin_user_id, conn=db_conn
        )
        db_conn.commit()
        success_message = "Status updated successfully."
        return RedirectResponse(url=router.url_path_for("admin_view_account", account_id=account_id) + f"?success_message={success_message}",
                                status_code=status.HTTP_303_SEE_OTHER)

    except (AccountNotFoundError, AccountStatusError, ValueError, AccountError) as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        error_message_form = str(e)
    except Exception as e_unhandled:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        error_message_form = f"An unexpected error occurred: {e_unhandled}"
        print(f"Unhandled error in update_account_status_admin_form_post: {e_unhandled}")

    # If error, re-render detail page with error
    account_details = customer_details = recent_transactions = available_statuses = None # Initialize before try
    try:
        account_details = account_management.get_account_by_id(account_id, conn=db_conn)
        if account_details: customer_details = customer_management.get_customer_by_id(account_details['customer_id'], conn=db_conn)
        recent_transactions = account_management.get_transaction_history(account_id, limit=10, conn=db_conn)
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur_status:
            cur_status.execute("SELECT status_id, status_name FROM account_status_types ORDER BY status_name;")
            available_statuses = [dict(row) for row in cur_status.fetchall()]
    except Exception as fetch_e:
         # If re-fetch fails, it's a bigger issue, but we must try to render something or raise HTTP error
         print(f"Critical error: Failed to re-fetch details for error page display: {fetch_e}")
         # Fallback to simpler error if main data is missing
         if not account_details: # account_details is critical for page title
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing status update and fetching details for error page: {fetch_e}")


    return request.state.templates.TemplateResponse("admin/account_detail.html", {
        "request": request, "page_title": f"Account: {account_details['account_number'] if account_details else 'N/A'}",
        "account": account_details, "customer": customer_details,
        "transactions": recent_transactions, "available_statuses": available_statuses,
        "error_form_status": error_message_form, "current_date": date.today(),
        "current_admin_username": current_admin.get('username')
    }, status_code=status.HTTP_400_BAD_REQUEST if error_message_form else status.HTTP_200_OK)


@router.post("/{account_id}/overdraft", response_class=HTMLResponse, name="admin_update_overdraft_limit",
             dependencies=[Depends(require_role(["admin"]))])
async def update_overdraft_limit_admin_form_post( # Renamed
    request: Request, account_id: int,
    overdraft_limit: Decimal = Form(..., ge=0),
    current_admin: dict = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    admin_user_id = current_admin.get('user_id')
    error_message_form = None

    try:
        current_account_details = account_management.get_account_by_id(account_id, conn=db_conn)
        old_limit = current_account_details['overdraft_limit']

        if old_limit == overdraft_limit:
            return RedirectResponse(url=router.url_path_for("admin_view_account", account_id=account_id) + "?info_message=No change in overdraft limit.",
                                status_code=status.HTTP_303_SEE_OTHER)

        # Pass conn to core function
        account_management.set_overdraft_limit(account_id, overdraft_limit, conn=db_conn, admin_user_id=admin_user_id)

        log_event(
            action_type='ADMIN_OVERDRAFT_LIMIT_CHANGE', target_entity='accounts', target_id=str(account_id),
            details={'old_limit': float(old_limit), 'new_limit': float(overdraft_limit)},
            user_id=admin_user_id, conn=db_conn
        )
        db_conn.commit()
        success_message = "Overdraft limit updated successfully."
        return RedirectResponse(url=router.url_path_for("admin_view_account", account_id=account_id) + f"?success_message={success_message}",
                                status_code=status.HTTP_303_SEE_OTHER)

    except (AccountNotFoundError, ValueError, AccountError) as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        error_message_form = str(e)
    except Exception as e_unhandled:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        error_message_form = f"An unexpected error occurred: {e_unhandled}"
        print(f"Unhandled error in update_overdraft_limit_admin_form_post: {e_unhandled}")

    account_details = customer_details = recent_transactions = available_statuses = None # Initialize
    try:
        account_details = account_management.get_account_by_id(account_id, conn=db_conn)
        if account_details: customer_details = customer_management.get_customer_by_id(account_details['customer_id'], conn=db_conn)
        recent_transactions = account_management.get_transaction_history(account_id, limit=10, conn=db_conn)
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur_status:
            cur_status.execute("SELECT status_id, status_name FROM account_status_types ORDER BY status_name;")
            available_statuses = [dict(row) for row in cur_status.fetchall()]
    except Exception as fetch_e:
         print(f"Critical error: Failed to re-fetch details for error page display: {fetch_e}")
         if not account_details:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing overdraft update and fetching details for error page: {fetch_e}")

    return request.state.templates.TemplateResponse("admin/account_detail.html", {
        "request": request, "page_title": f"Account: {account_details['account_number'] if account_details else 'N/A'}",
        "account": account_details, "customer": customer_details,
        "transactions": recent_transactions, "available_statuses": available_statuses,
        "error_form_overdraft": error_message_form, "current_date": date.today(),
        "current_admin_username": current_admin.get('username')
    }, status_code=status.HTTP_400_BAD_REQUEST if error_message_form else status.HTTP_200_OK)

```
