import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status
from decimal import Decimal

from ..dependencies import get_db, get_current_user_placeholder
from ..models import (
    FeeRequest, FeeApplicationResponse, HttpError
)

# Assuming core modules are importable (PYTHONPATH includes project root)
from core import fee_engine
from core.fee_engine import FeeTypeNotFoundError, FeeError
from core.transaction_processing import ( # Errors that can bubble up from apply_fee via withdraw
    AccountNotFoundError, InsufficientFundsError, AccountNotActiveOrFrozenError, TransactionError
)
# For constructing response, if needed
from core.account_management import get_account_by_id
from datetime import datetime


router = APIRouter(
    prefix="/fees",
    tags=["Fees"],
    responses={
        400: {"description": "Invalid request or business rule violation", "model": HttpError},
        404: {"description": "Resource not found (e.g., account or fee type)", "model": HttpError},
        500: {"description": "Internal server error", "model": HttpError}
    },
)

# Placeholder for current user
CurrentUser = Depends(get_current_user_placeholder)

@router.post("/apply", response_model=FeeApplicationResponse, status_code=status.HTTP_201_CREATED,
             summary="Apply a fee to an account")
async def apply_fee_to_account(
    request: FeeRequest,
    db_conn = Depends(get_db), # Core functions manage their own connections
    # current_user: dict = CurrentUser # TODO: Auth (e.g., admins or system processes)
):
    """
    Apply a specified fee to a customer's account.
    - **account_id**: The ID of the account to be debited.
    - **fee_type_name**: The name of the fee type (must exist in `fee_types` table).
    - **fee_amount**: Optional specific amount for this fee. If not provided,
                      the `default_amount` for the `fee_type_name` will be used.
    - **description**: Optional custom description for the fee transaction.
    """
    # TODO: Authorization checks, e.g., only specific system roles or admins.
    # user_id_performing_action = current_user.get('user_id') # Example
    user_id_performing_action = 0 # Placeholder for system user or unauthenticated for now

    try:
        # `apply_fee` internally calls `withdraw` from transaction_processing,
        # which handles DB connection, overdrafts, status checks, and transaction recording.
        # It also includes audit logging for the fee application.
        tx_id = fee_engine.apply_fee(
            account_id=request.account_id,
            fee_type_name=request.fee_type_name,
            fee_amount=request.fee_amount, # Can be None
            description=request.description,
            user_id_performing_action=user_id_performing_action
        )

        # To construct the response, we need the actual applied fee amount if it was default.
        applied_amount = request.fee_amount
        if applied_amount is None:
            fee_details = fee_engine.get_fee_type_details(request.fee_type_name) # Fetches default
            applied_amount = fee_details['default_amount']

        final_description = request.description or f"Fee applied: {request.fee_type_name}"

        return FeeApplicationResponse(
            transaction_id=tx_id,
            account_id=request.account_id,
            fee_type_name=request.fee_type_name,
            applied_fee_amount=applied_amount,
            description=final_description
        )

    except FeeTypeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (AccountNotFoundError, InsufficientFundsError, AccountNotActiveOrFrozenError) as e:
        # Errors propagated from transaction_processing.withdraw via fee_engine.apply_fee
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        if isinstance(e, InsufficientFundsError): status_code = status.HTTP_400_BAD_REQUEST # Or 409/422
        raise HTTPException(status_code=status_code, detail=str(e))
    except (FeeError, TransactionError) as e: # Catch other specific errors from fee_engine or transaction_processing
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

```
