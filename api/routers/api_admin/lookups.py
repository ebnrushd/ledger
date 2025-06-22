from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import psycopg2.extras # For DictCursor

# Assuming project root is in PYTHONPATH
from ....dependencies import get_db, require_role
from ....models import HttpError # General error model

# Define Pydantic model for response
from pydantic import BaseModel

class AccountStatusTypeResponse(BaseModel):
    status_id: int
    status_name: str

class TransactionTypeResponse(BaseModel):
    transaction_type_id: int
    type_name: str

router = APIRouter(
    prefix="/api/admin/lookups",
    tags=["Admin API - Lookups"],
    dependencies=[Depends(require_role(['admin', 'teller', 'auditor']))] # General access for lookups
)

@router.get("/account-status-types", response_model=List[AccountStatusTypeResponse])
async def get_all_account_status_types(db_conn = Depends(get_db)):
    """
    Retrieve all account status types.
    """
    try:
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT status_id, status_name FROM account_status_types ORDER BY status_id;")
            records = cur.fetchall()
            return [AccountStatusTypeResponse(**row) for row in records]
    except Exception as e:
        print(f"Error fetching account status types: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch account status types.")

@router.get("/transaction-types", response_model=List[TransactionTypeResponse])
async def get_all_transaction_types(db_conn = Depends(get_db)):
    """
    Retrieve all transaction types.
    """
    try:
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT transaction_type_id, type_name FROM transaction_types ORDER BY transaction_type_id;")
            records = cur.fetchall()
            return [TransactionTypeResponse(**row) for row in records]
    except Exception as e:
        print(f"Error fetching transaction types: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch transaction types.")

```
