import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Optional, List
from decimal import Decimal

# Assuming uvicorn runs from project root
from ....dependencies import get_db, get_current_admin_user, require_role
from ....models import ( # Import JSON API specific models
    HttpError, AccountDetails, UserSchema, AdminAccountListResponse,
    AdminAccountStatusUpdateRequest, AdminOverdraftLimitUpdateRequest, StatusResponse
)

# Services
from core import account_management, customer_management, audit_service # transaction_processing for recent tx removed
from core.account_management import AccountNotFoundError, AccountStatusError, AccountError, SUPPORTED_ACCOUNT_TYPES
from core.customer_management import CustomerNotFoundError

import psycopg2.extras # For fetching available statuses if needed
from datetime import date

router = APIRouter(
    prefix="/api/admin/accounts",
    tags=["Admin API - Account Management"],
    dependencies=[Depends(require_role(['admin', 'teller', 'auditor']))]
)

class AdminAccountDetailResponse(AccountDetails): # For detail view, can include more admin-specific info
    customer: Optional[customer_management.CustomerDetails] = None # Example: embed customer details
    # recent_transactions: List[TransactionDetails] = [] # Example: embed recent transactions

@router.get("/", response_model=AdminAccountListResponse)
async def list_accounts_api_admin( # Renamed
    current_admin: UserSchema = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=5, le=100),
    search_query: Optional[str] = Query(None, description="Search Account #, Customer ID, Name, Email"),
    status_filter: Optional[str] = Query(None),
    account_type_filter: Optional[str] = Query(None),
    customer_id_filter: Optional[int] = Query(None),
    db_conn = Depends(get_db)
):
    try:
        accounts_data_dict = account_management.list_accounts(
            page=page, per_page=per_page, search_query=search_query,
            status_filter=status_filter, account_type_filter=account_type_filter,
            customer_id_filter=customer_id_filter, conn=db_conn
        )
        return AdminAccountListResponse(
            accounts=[AccountDetails(**acc) for acc in accounts_data_dict.get("accounts", [])],
            total_items=accounts_data_dict.get("total_accounts", 0),
            total_pages=(accounts_data_dict.get("total_accounts", 0) + per_page - 1) // per_page,
            page=page,
            per_page=per_page
        )
    except AccountError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e_unhandled:
        print(f"Unhandled error in list_accounts_api_admin: {e_unhandled}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching accounts.")


@router.get("/{account_id}", response_model=AdminAccountDetailResponse)
async def get_account_detail_api_admin( # Renamed
    account_id: int,
    current_admin: UserSchema = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    try:
        account_dict = account_management.get_account_by_id(account_id, conn=db_conn)
        response_data = {**account_dict} # Start with account details

        if account_dict.get("customer_id"):
            try:
                customer_dict = customer_management.get_customer_by_id(account_dict["customer_id"], conn=db_conn)
                response_data["customer"] = customer_dict
            except CustomerNotFoundError:
                response_data["customer"] = None # Or some error indicator

        # Fetching recent transactions can be a separate endpoint or part of a more detailed model if always needed.
        # For now, keeping it similar to HTML version's context.
        # recent_tx = account_management.get_transaction_history(account_id, limit=5, conn=db_conn)
        # response_data["recent_transactions"] = [TransactionDetails(**tx) for tx in recent_tx]

        return AdminAccountDetailResponse(**response_data)
    except AccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    except Exception as e:
        print(f"Error in get_account_detail_api_admin for {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.put("/{account_id}/status", response_model=AccountDetails,
            dependencies=[Depends(require_role(["admin"]))]) # Stricter role for modification
async def update_account_status_api_admin( # Renamed
    account_id: int,
    status_update_request: AdminAccountStatusUpdateRequest, # JSON body
    current_admin: UserSchema = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    admin_user_id = current_admin.user_id
    new_status_name = status_update_request.status

    try:
        current_account_details = account_management.get_account_by_id(account_id, conn=db_conn)
        old_status = current_account_details['status_name']

        if old_status == new_status_name:
            # No change, just return current details or a 304 Not Modified (though 304 is tricky with FastAPI response models)
            return AccountDetails(**current_account_details)

        account_management.update_account_status(account_id, new_status_name, conn=db_conn, admin_user_id=admin_user_id)

        audit_service.log_event(
            action_type='ADMIN_API_ACCOUNT_STATUS_CHANGE', target_entity='accounts', target_id=str(account_id),
            details={'old_status': old_status, 'new_status': new_status_name},
            user_id=admin_user_id, conn=db_conn
        )
        db_conn.commit()

        updated_account_details = account_management.get_account_by_id(account_id, conn=db_conn)
        return AccountDetails(**updated_account_details)

    except (AccountNotFoundError, AccountStatusError, ValueError, AccountError) as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e_unhandled:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        print(f"Unhandled error in update_account_status_api_admin: {e_unhandled}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e_unhandled}")


@router.put("/{account_id}/overdraft_limit", response_model=AccountDetails,
            dependencies=[Depends(require_role(["admin"]))]) # Stricter role
async def update_overdraft_limit_api_admin( # Renamed
    account_id: int,
    overdraft_update_request: AdminOverdraftLimitUpdateRequest, # JSON body
    current_admin: UserSchema = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    admin_user_id = current_admin.user_id
    new_overdraft_limit = overdraft_update_request.limit

    try:
        current_account_details = account_management.get_account_by_id(account_id, conn=db_conn)
        old_limit = current_account_details['overdraft_limit']

        if old_limit == new_overdraft_limit:
            return AccountDetails(**current_account_details) # No change

        account_management.set_overdraft_limit(account_id, new_overdraft_limit, conn=db_conn, admin_user_id=admin_user_id)

        audit_service.log_event(
            action_type='ADMIN_API_OVERDRAFT_LIMIT_CHANGE', target_entity='accounts', target_id=str(account_id),
            details={'old_limit': float(old_limit), 'new_limit': float(new_overdraft_limit)},
            user_id=admin_user_id, conn=db_conn
        )
        db_conn.commit()

        updated_account_details = account_management.get_account_by_id(account_id, conn=db_conn)
        return AccountDetails(**updated_account_details)

    except (AccountNotFoundError, ValueError, AccountError) as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e_unhandled:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        print(f"Unhandled error in update_overdraft_limit_api_admin: {e_unhandled}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e_unhandled}")

```
