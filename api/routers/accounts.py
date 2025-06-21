import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from decimal import Decimal
from datetime import date

from ..dependencies import get_db, get_current_user_placeholder
from ..models import (
    AccountCreate, AccountDetails, AccountStatusUpdate, OverdraftLimitSet,
    HttpError, StatusResponse, AccountStatementResponse, TransactionDetails
)

# Assuming core modules are importable (PYTHONPATH includes project root)
from core import account_management, customer_management, transaction_processing # transaction_processing for get_transaction_history
from core.account_management import AccountNotFoundError, InvalidAccountTypeError, AccountStatusError, AccountError
from core.customer_management import CustomerNotFoundError
from reporting import statements # For generating statements

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
    responses={404: {"description": "Not found", "model": HttpError}},
)

# Placeholder for current user
CurrentUser = Depends(get_current_user_placeholder)

@router.post("/", response_model=AccountDetails, status_code=status.HTTP_201_CREATED,
             summary="Open a new account for a customer",
             responses={
                 400: {"description": "Invalid input (e.g., invalid account type, non-positive initial balance)", "model": HttpError},
                 404: {"description": "Customer not found", "model": HttpError},
                 500: {"description": "Internal server error", "model": HttpError}
             })
async def open_new_account(
    account_in: AccountCreate,
    db_conn = Depends(get_db), # Core functions currently manage their own connections
    # current_user: dict = CurrentUser # TODO: Auth (e.g., tellers, admins, or customer for themselves)
):
    """
    Open a new bank account for an existing customer.
    - **customer_id**: ID of the customer for whom the account is being opened.
    - **account_type**: Type of account (e.g., "checking", "savings").
    - **initial_balance**: Optional initial deposit amount (defaults to 0.00, must be non-negative).
    - **currency**: 3-letter currency code (defaults to "USD").
    """
    try:
        # `open_account` uses `execute_query` internally.
        account_id = account_management.open_account(
            customer_id=account_in.customer_id,
            account_type=account_in.account_type,
            initial_balance=account_in.initial_balance, # Already validated by Pydantic as Decimal
            currency=account_in.currency
        )
        if account_id is None: # Should be caught by exceptions in open_account
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to open account.")

        # Fetch and return the full account details
        account_details = account_management.get_account_by_id(account_id)
        return AccountDetails(**account_details)

    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidAccountTypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AccountError as e: # Catch other account related errors from core
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Account operation failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.get("/{account_id}", response_model=AccountDetails,
            summary="Get account details by ID",
            responses={
                 403: {"description": "Not authorized", "model": HttpError},
                 500: {"description": "Internal server error", "model": HttpError}
            })
async def get_account(
    account_id: int,
    db_conn = Depends(get_db),
    # current_user: dict = CurrentUser # TODO: Auth (customer for own account, tellers, admins)
):
    """
    Retrieve details for a specific account by its `account_id`.
    Includes balance, status, overdraft limit, etc.
    """
    # TODO: Authorization checks
    try:
        account_details = account_management.get_account_by_id(account_id)
        return AccountDetails(**account_details)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.put("/{account_id}/status", response_model=AccountDetails,
            summary="Update account status",
            responses={
                400: {"description": "Invalid status or business rule violation (e.g., closing account with balance)", "model": HttpError},
                403: {"description": "Not authorized", "model": HttpError},
                500: {"description": "Internal server error", "model": HttpError}
            })
async def update_account_status_endpoint(
    account_id: int,
    status_update: AccountStatusUpdate,
    db_conn = Depends(get_db),
    # current_user: dict = CurrentUser # TODO: Auth (tellers, admins)
):
    """
    Update the status of an account (e.g., to "active", "frozen", "closed").
    - **status**: The new status name.
    """
    # TODO: Authorization checks
    try:
        # `update_account_status` uses `execute_query` and also calls `get_account_by_id`.
        # It also now includes audit logging.
        success = account_management.update_account_status(account_id, status_update.status)
        if not success: # Should be caught by specific exceptions
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update account status.")

        updated_account_details = account_management.get_account_by_id(account_id)
        return AccountDetails(**updated_account_details)

    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (AccountStatusError, ValueError) as e: # ValueError for invalid status name
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AccountError as e: # Other core account errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Account status update failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.post("/{account_id}/overdraft_limit", response_model=AccountDetails,
             summary="Set or update account overdraft limit",
             responses={
                 400: {"description": "Invalid limit (e.g., negative)", "model": HttpError},
                 403: {"description": "Not authorized", "model": HttpError},
                 500: {"description": "Internal server error", "model": HttpError}
             })
async def set_account_overdraft_limit(
    account_id: int,
    overdraft_in: OverdraftLimitSet,
    db_conn = Depends(get_db),
    # current_user: dict = CurrentUser # TODO: Auth (admins, specific roles)
):
    """
    Set or update the overdraft limit for an account.
    - **limit**: The new overdraft limit (must be non-negative).
    """
    # TODO: Authorization checks
    try:
        # `set_overdraft_limit` uses `execute_query` and includes audit logging.
        success = account_management.set_overdraft_limit(account_id, overdraft_in.limit)
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to set overdraft limit.")

        updated_account_details = account_management.get_account_by_id(account_id)
        return AccountDetails(**updated_account_details)

    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e: # For negative limit
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AccountError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Setting overdraft limit failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.get("/{account_id}/statement", response_model=AccountStatementResponse,
            summary="Generate account statement for a period",
            responses={
                 400: {"description": "Invalid date format", "model": HttpError},
                 403: {"description": "Not authorized", "model": HttpError},
                 500: {"description": "Internal server error", "model": HttpError}
            })
async def get_account_statement(
    account_id: int,
    start_date: date = Query(..., description="Start date for the statement (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date for the statement (YYYY-MM-DD)"),
    db_conn = Depends(get_db), # `generate_account_statement` uses its own connections via core functions
    # current_user: dict = CurrentUser # TODO: Auth
):
    """
    Generate an account statement for a given period.
    Provides starting balance, ending balance, and a list of transactions with running balances.
    """
    # TODO: Authorization checks
    try:
        statement_data = statements.generate_account_statement(
            account_id,
            start_date.isoformat(),
            end_date.isoformat()
        )
        return AccountStatementResponse(**statement_data)
    except (AccountNotFoundError, CustomerNotFoundError) as e: # Customer not found is from within generate_statement
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e: # Date format errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except statements.StatementError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Statement generation failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.get("/{account_id}/transactions", response_model=List[TransactionDetails],
            summary="Get transaction history for an account",
            responses={
                 403: {"description": "Not authorized", "model": HttpError},
                 500: {"description": "Internal server error", "model": HttpError}
            })
async def get_account_transactions(
    account_id: int,
    limit: int = Query(50, ge=1, le=200, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db_conn = Depends(get_db),
    # current_user: dict = CurrentUser # TODO: Auth
):
    """
    Retrieve transaction history for a specific account.
    Supports pagination via `limit` and `offset` query parameters.
    """
    # TODO: Authorization checks
    try:
        # `get_transaction_history` from `account_management` is used here.
        transactions = account_management.get_transaction_history(account_id, limit=limit, offset=offset)
        # Convert list of dicts to list of TransactionDetails models
        return [TransactionDetails(**tx) for tx in transactions]
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AccountError as e: # Other core account errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get transactions: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

```
