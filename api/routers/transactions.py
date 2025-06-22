import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status
from decimal import Decimal
from datetime import datetime # For constructing response if needed

# Assuming project root is in PYTHONPATH for these imports
from ..dependencies import get_db, get_current_active_user_from_token
from ..models import (
    DepositRequest, WithdrawalRequest, TransferRequest,
    ACHTransactionRequest, WireTransactionRequest,
    TransactionDetails, TransferResponse, HttpError, UserSchema
)

from core import transaction_processing as tp
from core.transaction_processing import (
    AccountNotFoundError, InsufficientFundsError, InvalidAmountError,
    AccountNotActiveOrFrozenError, TransactionError, InvalidTransactionTypeError
)
from core.account_management import get_account_by_id as get_account_details # Renamed for clarity
from core import audit_service # For audit logging

router = APIRouter(
    prefix="/transactions", # Will be part of /api/v1/transactions
    tags=["Transactions (v1)"], # Updated tag
    responses={
        400: {"description": "Invalid request data or business rule violation", "model": HttpError},
        401: {"description": "Not authenticated", "model": HttpError},
        403: {"description": "Not authorized for this action/account", "model": HttpError},
        404: {"description": "Account not found", "model": HttpError},
        500: {"description": "Internal server error", "model": HttpError}
    },
    dependencies=[Depends(get_current_active_user_from_token)] # Protect all transaction routes
)

# Helper to check account ownership and status
async def _verify_account_access_and_status(account_id: int, current_user: UserSchema, db_conn, allow_frozen=False):
    if not current_user.customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no linked customer profile.")
    try:
        account = get_account_details(account_id, conn=db_conn)
    except AccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Account {account_id} not found.")

    if account["customer_id"] != current_user.customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to transact on account {account_id}.")

    if account["status_name"] == 'closed':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Account {account_id} is closed.")
    if not allow_frozen and account["status_name"] == 'frozen':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Account {account_id} is frozen.")
    if account["status_name"] != 'active' and not (allow_frozen and account["status_name"] == 'frozen'):
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Account {account_id} is not active for transactions (status: {account['status_name']}).")
    return account # Return account details if access is fine


@router.post("/deposit", response_model=TransactionDetails, status_code=status.HTTP_201_CREATED)
async def deposit_funds_api( # Renamed
    request_body: DepositRequest, # Changed from 'request' to avoid conflict with FastAPI Request
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    # For deposits, account can be active or frozen (sometimes allowed for frozen to correct issues)
    await _verify_account_access_and_status(request_body.account_id, current_user, db_conn, allow_frozen=True)

    try:
        tx_id = tp.deposit(
            account_id=request_body.account_id, amount=request_body.amount,
            description=request_body.description, conn=db_conn
        )
        # Audit log for deposit
        audit_service.log_event(
            action_type='DEPOSIT_API', target_entity='accounts', target_id=str(request_body.account_id),
            details={'amount': float(request_body.amount), 'description': request_body.description, 'transaction_id': tx_id},
            user_id=current_user.user_id, conn=db_conn
        )
        db_conn.commit()

        # Construct response (ideally core func returns full details)
        return TransactionDetails(
            transaction_id=tx_id, account_id=request_body.account_id, type_name='deposit',
            amount=request_body.amount, transaction_timestamp=datetime.utcnow(), # Approx.
            description=request_body.description
        )
    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InvalidAmountError, InvalidTransactionTypeError) as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except TransactionError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Deposit failed: {e}")


@router.post("/withdraw", response_model=TransactionDetails, status_code=status.HTTP_201_CREATED)
async def withdraw_funds_api( # Renamed
    request_body: WithdrawalRequest,
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    await _verify_account_access_and_status(request_body.account_id, current_user, db_conn, allow_frozen=False)
    try:
        tx_id = tp.withdraw(
            account_id=request_body.account_id, amount=request_body.amount,
            description=request_body.description, conn=db_conn
        )
        # tp.withdraw already handles overdraft audit logging internally with its passed conn.
        # Add general withdrawal audit
        audit_service.log_event(
            action_type='WITHDRAWAL_API', target_entity='accounts', target_id=str(request_body.account_id),
            details={'amount': float(request_body.amount), 'description': request_body.description, 'transaction_id': tx_id},
            user_id=current_user.user_id, conn=db_conn
        )
        db_conn.commit()
        return TransactionDetails(
            transaction_id=tx_id, account_id=request_body.account_id, type_name='withdrawal',
            amount=-request_body.amount, transaction_timestamp=datetime.utcnow(), # Approx.
            description=request_body.description
        )
    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, InvalidTransactionTypeError) as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        if isinstance(e, InsufficientFundsError): status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except TransactionError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Withdrawal failed: {e}")


@router.post("/transfer", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def transfer_funds_api( # Renamed
    request_body: TransferRequest,
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    if request_body.from_account_id == request_body.to_account_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot transfer to the same account.")

    # Verify user owns and can use the 'from' account
    await _verify_account_access_and_status(request_body.from_account_id, current_user, db_conn, allow_frozen=False)
    # Verify 'to' account exists and is active (or appropriate status for receiving funds)
    # Not checking ownership for 'to_account_id' by current_user, as transfers can be to others.
    try:
        to_account = get_account_details(request_body.to_account_id, conn=db_conn)
        if to_account["status_name"] not in ["active", "frozen"]: # Frozen might receive, closed definitely not
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Destination account {request_body.to_account_id} cannot receive funds (status: {to_account['status_name']}).")
    except AccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Destination account {request_body.to_account_id} not found.")

    try:
        debit_tx_id, credit_tx_id = tp.transfer_funds(
            from_account_id=request_body.from_account_id, to_account_id=request_body.to_account_id,
            amount=request_body.amount, description=request_body.description, conn=db_conn
        )
        # tp.transfer_funds handles overdraft audit for from_account. Add general transfer audit.
        audit_service.log_event(
            action_type='TRANSFER_API', target_entity='accounts', target_id=str(request_body.from_account_id),
            details={'to_account_id': request_body.to_account_id, 'amount': float(request_body.amount), 'description': request_body.description, 'debit_tx_id': debit_tx_id, 'credit_tx_id': credit_tx_id},
            user_id=current_user.user_id, conn=db_conn
        )
        db_conn.commit()

        utc_now = datetime.utcnow() # Approx.
        return TransferResponse(
            debit_transaction=TransactionDetails(
                transaction_id=debit_tx_id, account_id=request_body.from_account_id, type_name='transfer',
                amount=-request_body.amount, transaction_timestamp=utc_now, description=f"{request_body.description} to account {request_body.to_account_id}",
                related_account_id=request_body.to_account_id
            ),
            credit_transaction=TransactionDetails(
                transaction_id=credit_tx_id, account_id=request_body.to_account_id, type_name='transfer',
                amount=request_body.amount, transaction_timestamp=utc_now, description=f"{request_body.description} from account {request_body.from_account_id}",
                related_account_id=request_body.from_account_id
            )
        )
    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, InvalidTransactionTypeError) as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        if isinstance(e, InsufficientFundsError): status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except TransactionError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Transfer failed: {e}")


# ACH and Wire endpoints are more typically initiated by system or specific agreements.
# For user-facing API, these might be restricted or have different validation.
# For now, assume user must own the account for any debiting ACH/Wire.
# For crediting, it could be any valid account.

@router.post("/ach", response_model=TransactionDetails, status_code=status.HTTP_201_CREATED)
async def process_ach_api( # Renamed
    request_body: ACHTransactionRequest,
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    if request_body.ach_type == 'debit':
        await _verify_account_access_and_status(request_body.account_id, current_user, db_conn, allow_frozen=False)
    else: # Credit, ensure account exists and can receive funds
        try:
            acc = get_account_details(request_body.account_id, conn=db_conn)
            if acc['status_name'] not in ['active', 'frozen']: # Can credit to frozen, not closed
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Account {request_body.account_id} cannot receive ACH credit (status: {acc['status_name']}).")
        except AccountNotFoundError:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Account {request_body.account_id} not found for ACH credit.")

    try:
        tx_id = tp.process_ach_transaction(
            account_id=request_body.account_id, amount=request_body.amount,
            description=request_body.description, ach_type=request_body.ach_type, conn=db_conn
        )
        # Audit log
        audit_service.log_event(
            action_type=f'ACH_{request_body.ach_type.upper()}_API', target_entity='accounts', target_id=str(request_body.account_id),
            details={'amount': float(request_body.amount), 'description': request_body.description, 'transaction_id': tx_id},
            user_id=current_user.user_id, conn=db_conn
        )
        db_conn.commit()

        tx_amount = request_body.amount if request_body.ach_type == 'credit' else -request_body.amount
        return TransactionDetails(
            transaction_id=tx_id, account_id=request_body.account_id, type_name=f'ach_{request_body.ach_type}',
            amount=tx_amount, transaction_timestamp=datetime.utcnow(), description=request_body.description
        )
    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, ValueError) as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        if isinstance(e, InsufficientFundsError): status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except TransactionError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"ACH transaction failed: {e}")


@router.post("/wire", response_model=TransactionDetails, status_code=status.HTTP_201_CREATED)
async def process_wire_api( # Renamed
    request_body: WireTransactionRequest,
    current_user: UserSchema = Depends(get_current_active_user_from_token),
    db_conn = Depends(get_db)
):
    if request_body.direction == 'outgoing':
        await _verify_account_access_and_status(request_body.account_id, current_user, db_conn, allow_frozen=False)
    else: # Incoming wire
        try:
            acc = get_account_details(request_body.account_id, conn=db_conn)
            if acc['status_name'] not in ['active', 'frozen']:
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Account {request_body.account_id} cannot receive wire (status: {acc['status_name']}).")
        except AccountNotFoundError:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Account {request_body.account_id} not found for incoming wire.")

    try:
        tx_id = tp.process_wire_transfer(
            account_id=request_body.account_id, amount=request_body.amount,
            description=request_body.description, direction=request_body.direction, conn=db_conn
        )
        audit_service.log_event(
            action_type=f'WIRE_{request_body.direction.upper()}_API', target_entity='accounts', target_id=str(request_body.account_id),
            details={'amount': float(request_body.amount), 'description': request_body.description, 'transaction_id': tx_id},
            user_id=current_user.user_id, conn=db_conn
        )
        db_conn.commit()

        tx_amount = request_body.amount if request_body.direction == 'incoming' else -request_body.amount
        return TransactionDetails(
            transaction_id=tx_id, account_id=request_body.account_id, type_name='wire_transfer',
            amount=tx_amount, transaction_timestamp=datetime.utcnow(), description=request_body.description
        )
    except (AccountNotFoundError, AccountNotActiveOrFrozenError, InsufficientFundsError, InvalidAmountError, ValueError) as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, AccountNotFoundError) else status.HTTP_400_BAD_REQUEST
        if isinstance(e, InsufficientFundsError): status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except TransactionError as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if db_conn and not db_conn.closed and not getattr(db_conn, 'autocommit', True): db_conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Wire transaction failed: {e}")

```
