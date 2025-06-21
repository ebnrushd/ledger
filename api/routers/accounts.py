import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from decimal import Decimal
from datetime import date

# Assuming project root is in PYTHONPATH for these imports
from ..dependencies import get_db, get_current_active_user_from_token
from ..models import (
    AccountCreate, AccountDetails,
    HttpError, AccountStatementResponse, TransactionDetails, UserSchema
)

from core import account_management, customer_management, audit_service
from core.account_management import AccountNotFoundError, InvalidAccountTypeError, AccountStatusError, AccountError, SUPPORTED_ACCOUNT_TYPES
from core.customer_management import CustomerNotFoundError
from reporting import statements

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts (v1)"],
    responses={404: {"description": "Not found", "model": HttpError}},
    dependencies=[Depends(get_current_active_user_from_token)] # Protect all account routes
)

@router.post("/", response_model=AccountDetails, status_code=status.HTTP_201_CREATED,
             summary="Open a new account for the authenticated user's customer profile")
async def open_customer_account(
    account_in: AccountCreate,
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    if not current_user.customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no linked customer profile to open accounts for.")

    if account_in.customer_id != current_user.customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot open account for a different customer.")

    try:
        account_id = account_management.open_account(
            customer_id=account_in.customer_id,
            account_type=account_in.account_type,
            initial_balance=account_in.initial_balance,
            currency=account_in.currency,
            conn=db_conn
        )

        audit_service.log_event(
            action_type='ACCOUNT_OPENED_API', target_entity='accounts', target_id=str(account_id),
            details={'account_type': account_in.account_type, 'initial_balance': float(account_in.initial_balance),
                     'currency': account_in.currency, 'customer_id': account_in.customer_id},
            user_id=current_user.user_id, conn=db_conn
        )
        db_conn.commit()

        account_details = account_management.get_account_by_id(account_id, conn=db_conn)
        return AccountDetails(**account_details)

    except CustomerNotFoundError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidAccountTypeError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AccountError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Account operation failed: {e}")
    except Exception as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.get("/", response_model=List[AccountDetails], summary="List accounts for current user")
async def list_my_accounts(
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    if not current_user.customer_id:
        return []

    try:
        accounts_data = account_management.list_accounts(
            customer_id_filter=current_user.customer_id,
            per_page=1000, # Get all accounts for this customer by default
            conn=db_conn
        )
        return [AccountDetails(**acc) for acc in accounts_data.get("accounts", [])]
    except AccountError as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list accounts: {e}")

@router.get("/{account_id}", response_model=AccountDetails, summary="Get specific account details for current user")
async def get_my_account(
    account_id: int,
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    if not current_user.customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no linked customer profile.")
    try:
        account_details = account_management.get_account_by_id(account_id, conn=db_conn)
        if account_details["customer_id"] != current_user.customer_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this account.")
        return AccountDetails(**account_details)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.get("/{account_id}/statement", response_model=AccountStatementResponse,
            summary="Generate account statement for one of current user's accounts")
async def get_my_account_statement(
    account_id: int,
    start_date: date = Query(..., description="Start date for the statement (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date for the statement (YYYY-MM-DD)"),
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    if not current_user.customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no linked customer profile.")
    try:
        account_details = account_management.get_account_by_id(account_id, conn=db_conn) # Verify ownership first
        if account_details["customer_id"] != current_user.customer_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access statement for this account.")

        # Note: statements.generate_account_statement uses its own connections in its current form.
        # For consistency, it should also be refactored to accept `conn`.
        statement_data = statements.generate_account_statement(
            account_id, start_date.isoformat(), end_date.isoformat()
        )
        return AccountStatementResponse(**statement_data)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e: # Date format errors from isoformat (though Query should catch)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except statements.StatementError as e: # Custom error from statement generation
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Statement generation failed: {e}")
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.get("/{account_id}/transactions", response_model=List[TransactionDetails],
            summary="Get transaction history for one of current user's accounts")
async def get_my_account_transactions(
    account_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    if not current_user.customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no linked customer profile.")
    try:
        account_details = account_management.get_account_by_id(account_id, conn=db_conn) # Verify ownership
        if account_details["customer_id"] != current_user.customer_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access transactions for this account.")

        transactions = account_management.get_transaction_history(account_id, limit=limit, offset=offset, conn=db_conn)
        return [TransactionDetails(**tx) for tx in transactions]
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AccountError as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get transactions: {e}")
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

# Endpoints for updating status or overdraft limit are removed from V1 user-facing API.
# These are considered admin actions and are available in the /admin/accounts/ section.
```
