import sys
import os
from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from fastapi.responses import HTMLResponse
from typing import Optional
from decimal import Decimal
from datetime import date

# Assuming uvicorn runs from project root
from ....dependencies import get_db, get_current_admin_user, require_role
from ....models import HttpError

# Services
from core import transaction_processing
import psycopg2.extras

router = APIRouter(
    prefix="/admin/transactions",
    tags=["Admin - Transaction Monitoring"],
    dependencies=[Depends(require_role(['admin', 'teller', 'auditor']))]
)

@router.get("/", response_class=HTMLResponse, name="admin_list_transactions")
async def list_all_transactions_admin(
    request: Request,
    current_admin: dict = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=5, le=100),
    account_id_filter: Optional[int] = Query(None, description="Filter by primary Account ID"),
    transaction_type_filter: Optional[str] = Query(None),
    start_date_filter: Optional[date] = Query(None),
    end_date_filter: Optional[date] = Query(None),
    db_conn = Depends(get_db)
):
    transactions_data = {}
    error_message = None
    available_transaction_types = []

    try:
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur_types:
            cur_types.execute("SELECT type_name FROM transaction_types ORDER BY type_name;")
            available_transaction_types = [dict(row) for row in cur_types.fetchall()]

        transactions_data = transaction_processing.list_transactions(
            page=page, per_page=per_page,
            account_id_filter=account_id_filter,
            transaction_type_filter=transaction_type_filter,
            start_date_filter=start_date_filter.isoformat() if start_date_filter else None,
            end_date_filter=end_date_filter.isoformat() if end_date_filter else None,
            conn=db_conn
        )
    except transaction_processing.TransactionError as e:
        error_message = str(e)
        transactions_data = {"transactions": [], "total_transactions": 0}
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        transactions_data = {"transactions": [], "total_transactions": 0}
        print(f"Error in list_all_transactions_admin: {e}")

    total_transactions = transactions_data.get("total_transactions", 0)
    total_pages = (total_transactions + per_page - 1) // per_page

    start_date_str = start_date_filter.isoformat() if start_date_filter else ""
    end_date_str = end_date_filter.isoformat() if end_date_filter else ""

    return request.state.templates.TemplateResponse("admin/transactions_list.html", {
        "request": request, "page_title": "Transaction Monitoring",
        "transactions": transactions_data.get("transactions", []),
        "total_transactions": total_transactions,
        "current_page": page, "per_page": per_page, "total_pages": total_pages,
        "account_id_filter": account_id_filter,
        "transaction_type_filter": transaction_type_filter,
        "start_date_filter": start_date_str,
        "end_date_filter": end_date_str,
        "available_transaction_types": available_transaction_types,
        "error": error_message,
        "current_admin_username": current_admin.get('username')
    })

@router.get("/{transaction_id}", response_class=HTMLResponse, name="admin_view_transaction")
async def view_transaction_detail_admin(
    request: Request, transaction_id: int,
    current_admin: dict = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    transaction_details = None
    error_message = None
    try:
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            query = """
                SELECT
                    t.transaction_id, t.transaction_timestamp, t.description, t.amount,
                    t.account_id, acc_pri.account_number as primary_account_number,
                    cust_pri.customer_id as primary_customer_id, cust_pri.first_name as primary_cust_fname, cust_pri.last_name as primary_cust_lname,
                    tt.type_name, acc_pri.currency,
                    t.related_account_id, acc_rel.account_number as related_account_number
                FROM transactions t
                JOIN accounts acc_pri ON t.account_id = acc_pri.account_id
                JOIN customers cust_pri ON acc_pri.customer_id = cust_pri.customer_id
                JOIN transaction_types tt ON t.transaction_type_id = tt.transaction_type_id
                LEFT JOIN accounts acc_rel ON t.related_account_id = acc_rel.account_id
                WHERE t.transaction_id = %s;
            """
            cur.execute(query, (transaction_id,))
            record = cur.fetchone()
            if record:
                transaction_details = dict(record)
                if transaction_details.get('primary_cust_fname') or transaction_details.get('primary_cust_lname'):
                    transaction_details["customer_name"] = f"{transaction_details.get('primary_cust_fname','')} {transaction_details.get('primary_cust_lname','')} ".strip()
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Error fetching transaction details: {e}"
        print(f"Error in view_transaction_detail_admin: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)

    return request.state.templates.TemplateResponse("admin/transaction_detail.html", {
        "request": request,
        "page_title": f"Transaction Details: ID {transaction_id}",
        "transaction": transaction_details,
        "error": error_message,
        "current_admin_username": current_admin.get('username')
    })
```
