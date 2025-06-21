import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from decimal import Decimal
from datetime import date

# Assuming uvicorn runs from project root
from ....dependencies import get_db, get_current_admin_user, require_role
from ....models import ( # Import JSON API specific models
    HttpError, TransactionDetails, AdminTransactionListResponse, UserSchema
)

# Services
from core import transaction_processing
from core.transaction_processing import TransactionError # For specific error from service

import psycopg2.extras

router = APIRouter(
    prefix="/api/admin/transactions",
    tags=["Admin API - Transaction Monitoring"],
    dependencies=[Depends(require_role(['admin', 'teller', 'auditor']))]
)

@router.get("/", response_model=AdminTransactionListResponse)
async def list_transactions_api_admin( # Renamed
    current_admin: UserSchema = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=5, le=100),
    account_id_filter: Optional[int] = Query(None),
    transaction_type_filter: Optional[str] = Query(None),
    start_date_filter: Optional[date] = Query(None),
    end_date_filter: Optional[date] = Query(None),
    db_conn = Depends(get_db)
):
    """Retrieve a paginated list of transactions with optional filters."""
    try:
        transactions_data_dict = transaction_processing.list_transactions(
            page=page, per_page=per_page,
            account_id_filter=account_id_filter,
            transaction_type_filter=transaction_type_filter,
            start_date_filter=start_date_filter.isoformat() if start_date_filter else None,
            end_date_filter=end_date_filter.isoformat() if end_date_filter else None,
            conn=db_conn
        )
        # list_transactions already returns dicts compatible with TransactionDetails (amount is Decimal)
        return AdminTransactionListResponse(
            transactions=[TransactionDetails(**tx) for tx in transactions_data_dict.get("transactions", [])],
            total_items=transactions_data_dict.get("total_transactions", 0),
            total_pages=(transactions_data_dict.get("total_transactions", 0) + per_page - 1) // per_page,
            page=page,
            per_page=per_page
        )
    except TransactionError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e_unhandled:
        print(f"Unhandled error in list_transactions_api_admin: {e_unhandled}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching transactions.")


# For the detail view, we need a more detailed Pydantic model if we include customer name, etc.
# For now, reusing TransactionDetails and the router will return what that model defines.
# The direct SQL query in the HTML version fetched more; this Pydantic model is simpler.
# Let's define a specific AdminTransactionDetail model if needed, or adjust TransactionDetails.
# For now, we'll use a direct query like the HTML version to get rich details.

class AdminAPITransactionDetail(TransactionDetails): # Extending base TransactionDetails
    primary_account_number: Optional[str] = None
    primary_customer_id: Optional[int] = None
    primary_cust_fname: Optional[str] = None
    primary_cust_lname: Optional[str] = None
    customer_name: Optional[str] = None # Combined
    currency: Optional[str] = None
    related_account_number_detail: Optional[str] = None # Alias to avoid conflict with TransactionDetails related_account_number if it existed

    class Config:
        orm_mode = True # Enable ORM mode if data comes from ORM objects (not in this direct SQL case)


@router.get("/{transaction_id}", response_model=AdminAPITransactionDetail)
async def get_transaction_detail_api_admin( # Renamed
    transaction_id: int,
    current_admin: UserSchema = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    """Retrieve details for a specific transaction, including related account and customer info."""
    try:
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            query = """
                SELECT
                    t.transaction_id, t.transaction_timestamp, t.description, t.amount,
                    t.account_id, acc_pri.account_number as primary_account_number,
                    cust_pri.customer_id as primary_customer_id, cust_pri.first_name as primary_cust_fname,
                    cust_pri.last_name as primary_cust_lname,
                    tt.type_name, acc_pri.currency,
                    t.related_account_id, acc_rel.account_number as related_account_number_detail
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
                record_dict = dict(record)
                if record_dict.get('primary_cust_fname') or record_dict.get('primary_cust_lname'):
                    record_dict["customer_name"] = f"{record_dict.get('primary_cust_fname','')} {record_dict.get('primary_cust_lname','')} ".strip()

                # Ensure amount is Decimal for Pydantic model
                if 'amount' in record_dict and record_dict['amount'] is not None:
                    record_dict['amount'] = Decimal(str(record_dict['amount']))

                return AdminAPITransactionDetail(**record_dict)
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_transaction_detail_api_admin for {transaction_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

```
