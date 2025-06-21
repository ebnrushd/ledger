import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status
from decimal import Decimal

from ..dependencies import get_db, get_current_user_placeholder
from ..models import (
    DepositRequest, WithdrawalRequest, TransferRequest,
    ACHTransactionRequest, WireTransactionRequest,
    TransactionDetails, TransferResponse, HttpError, StatusResponse
)

# Assuming core modules are importable (PYTHONPATH includes project root)
from core import transaction_processing as tp
from core.transaction_processing import (
    AccountNotFoundError, InsufficientFundsError, InvalidAmountError,
    AccountNotActiveOrFrozenError, TransactionError, InvalidTransactionTypeError
)
# `get_account_by_id` might be needed for additional validation or fetching details post-transaction if not returned by core functions
from core.account_management import get_account_by_id

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    responses={
        400: {"description": "Invalid request data or business rule violation", "model": HttpError},
        404: {"description": "Account not found", "model": HttpError},
        500: {"description": "Internal server error", "model": HttpError}
    },
)

# Placeholder for current user
CurrentUser = Depends(get_current_user_placeholder)

@router.post("/deposit", response_model=TransactionDetails, status_code=status.HTTP_201_CREATED,
             summary="Deposit funds into an account")
async def deposit_funds(
    request: DepositRequest,
    db_conn = Depends(get_db), # Core functions currently manage their own connections
    # current_user: dict = CurrentUser # TODO: Auth (e.g., customer for own account, tellers)
):
    """
    Process a deposit into a specified account.
    - **account_id**: Target account ID.
    - **amount**: Positive amount to deposit.
    - **description**: Optional transaction description.
    """
    # TODO: Authorization: e.g., customer can deposit to own account, teller can deposit to any.
    try:
        # `tp.deposit` uses its own connection management internally via `get_db_connection()`.
        # It also handles audit logging for overdrafts (though not typical for deposit).
        tx_id = tp.deposit(
            account_id=request.account_id,
            amount=request.amount,
            description=request.description
        )
        # Fetch the transaction details to return
        # This requires a get_transaction_by_id function, which is not explicitly in the plan.
        # For now, we'll construct a simplified response or assume core function returns enough.
        # Let's assume we need to fetch it. A `get_transaction_by_id` would be useful in `transaction_processing.py`.
        # As a temporary measure, we might return a simpler response or the ID only.
        # However, the response_model is TransactionDetails.
        # Let's assume the core `deposit` function (and others) are modified to return enough details,
        # or we add a `get_transaction_details(tx_id)` function.
        # For this subtask, let's assume we can construct it if core returns tx_id and we know other details.
        # A better way: core functions should return the full transaction object or detailed dict.

        # Simplified: fetch account to get some details for constructing response.
        # This is not ideal. Ideally, transaction_processing.deposit would return full details.
        acc_details = get_account_by_id(request.account_id) # from account_management

        # Find the transaction type name for 'deposit'
        deposit_type_id = tp.get_transaction_type_id('deposit') # Uses its own connection or can take one

        return TransactionDetails(
            transaction_id=tx_id,
            account_id=request.account_id,
            type_name='deposit', # Assuming this type name
            amount=request.amount, # For deposit, amount is positive
            transaction_timestamp=datetime.utcnow(), # Approximate, real value is in DB
            description=request.description
        )

    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InvalidAmountError, InvalidTransactionTypeError) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except TransactionError as e: # Catch other specific transaction errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.post("/withdraw", response_model=TransactionDetails, status_code=status.HTTP_201_CREATED,
             summary="Withdraw funds from an account")
async def withdraw_funds(
    request: WithdrawalRequest,
    db_conn = Depends(get_db),
    # current_user: dict = CurrentUser # TODO: Auth
):
    """
    Process a withdrawal from a specified account.
    - **account_id**: Target account ID.
    - **amount**: Positive amount to withdraw.
    - **description**: Optional transaction description.
    """
    # TODO: Auth
    try:
        tx_id = tp.withdraw(
            account_id=request.account_id,
            amount=request.amount,
            description=request.description
        )
        # Similar to deposit, constructing response. Amount for withdrawal is stored negative in DB.
        return TransactionDetails(
            transaction_id=tx_id,
            account_id=request.account_id,
            type_name='withdrawal',
            amount=-request.amount, # Representing the debit
            transaction_timestamp=datetime.utcnow(), # Approximate
            description=request.description
        )
    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, InvalidTransactionTypeError) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        if isinstance(e, InsufficientFundsError): status_code = status.HTTP_400_BAD_REQUEST # Or 409 Conflict / 422 Unprocessable
        raise HTTPException(status_code=status_code, detail=str(e))
    except TransactionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.post("/transfer", response_model=TransferResponse, status_code=status.HTTP_201_CREATED, # TransferResponse needs to be defined
             summary="Transfer funds between two accounts")
async def transfer_funds_endpoint(
    request: TransferRequest,
    db_conn = Depends(get_db),
    # current_user: dict = CurrentUser # TODO: Auth
):
    """
    Transfer funds from one account to another.
    - **from_account_id**: Source account ID.
    - **to_account_id**: Destination account ID.
    - **amount**: Positive amount to transfer.
    - **description**: Optional transaction description.
    """
    # TODO: Auth
    if request.from_account_id == request.to_account_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot transfer to the same account.")
    try:
        debit_tx_id, credit_tx_id = tp.transfer_funds(
            from_account_id=request.from_account_id,
            to_account_id=request.to_account_id,
            amount=request.amount,
            description=request.description
        )
        # Constructing response. This is complex if core doesn't return full details.
        # For now, creating two TransactionDetails objects.
        # This assumes `transfer` type is used for both legs.
        utc_now = datetime.utcnow() # Approximate timestamp
        debit_tx = TransactionDetails(
            transaction_id=debit_tx_id, account_id=request.from_account_id, type_name='transfer',
            amount=-request.amount, transaction_timestamp=utc_now, description=f"{request.description} to account {request.to_account_id}",
            related_account_id=request.to_account_id
        )
        credit_tx = TransactionDetails(
            transaction_id=credit_tx_id, account_id=request.to_account_id, type_name='transfer',
            amount=request.amount, transaction_timestamp=utc_now, description=f"{request.description} from account {request.from_account_id}",
            related_account_id=request.from_account_id
        )
        return TransferResponse(debit_transaction=debit_tx, credit_transaction=credit_tx)

    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, InvalidTransactionTypeError) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        if isinstance(e, InsufficientFundsError): status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except TransactionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.post("/ach", response_model=TransactionDetails, status_code=status.HTTP_201_CREATED,
             summary="Process an ACH transaction (credit or debit)")
async def process_ach(
    request: ACHTransactionRequest,
    db_conn = Depends(get_db),
    # current_user: dict = CurrentUser # TODO: Auth (system roles, or specific user permissions)
):
    """
    Process an ACH transaction (credit to or debit from an account).
    - **account_id**: Target account ID.
    - **amount**: Positive amount for the ACH transaction.
    - **ach_type**: "credit" (to the account) or "debit" (from the account).
    - **description**: Optional transaction description.
    """
    # TODO: Auth
    try:
        tx_id = tp.process_ach_transaction(
            account_id=request.account_id,
            amount=request.amount,
            description=request.description,
            ach_type=request.ach_type
        )
        tx_amount = request.amount if request.ach_type == 'credit' else -request.amount
        return TransactionDetails(
            transaction_id=tx_id, account_id=request.account_id, type_name=f'ach_{request.ach_type}',
            amount=tx_amount, transaction_timestamp=datetime.utcnow(), description=request.description
        )
    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, InvalidTransactionTypeError, ValueError) as e: # Added ValueError for invalid ach_type
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        if isinstance(e, InsufficientFundsError): status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except TransactionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.post("/wire", response_model=TransactionDetails, status_code=status.HTTP_201_CREATED,
             summary="Process a wire transfer (incoming or outgoing)")
async def process_wire(
    request: WireTransactionRequest,
    db_conn = Depends(get_db),
    # current_user: dict = CurrentUser # TODO: Auth
):
    """
    Process a wire transfer (incoming to or outgoing from an account).
    - **account_id**: Target account ID.
    - **amount**: Positive amount for the wire transfer.
    - **direction**: "incoming" (to the account) or "outgoing" (from the account).
    - **description**: Optional transaction description.
    """
    # TODO: Auth
    try:
        tx_id = tp.process_wire_transfer(
            account_id=request.account_id,
            amount=request.amount,
            description=request.description,
            direction=request.direction
        )
        tx_amount = request.amount if request.direction == 'incoming' else -request.amount
        return TransactionDetails(
            transaction_id=tx_id, account_id=request.account_id, type_name='wire_transfer', # type_name might be more specific in DB
            amount=tx_amount, transaction_timestamp=datetime.utcnow(), description=request.description
        )
    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, InvalidTransactionTypeError, ValueError) as e: # Added ValueError for invalid direction
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        if isinstance(e, InsufficientFundsError): status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except TransactionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

```
