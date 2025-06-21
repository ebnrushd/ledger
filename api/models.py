from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Union
from decimal import Decimal
from datetime import datetime, date

# --- General Utility Models ---
class HttpError(BaseModel):
    detail: str

class StatusResponse(BaseModel):
    success: bool
    message: Optional[str] = None


# --- Customer Models ---
class CustomerBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)

class CustomerDetails(CustomerBase):
    customer_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# --- Account Models ---
class AccountBase(BaseModel):
    account_type: str = Field(..., description="e.g., checking, savings")
    currency: str = Field("USD", min_length=3, max_length=3)

class AccountCreate(AccountBase):
    customer_id: int
    initial_balance: Optional[Decimal] = Field(Decimal("0.00"), ge=0)

    @validator('initial_balance', pre=True, always=True)
    def validate_initial_balance(cls, v):
        return Decimal(str(v))

class AccountDetails(AccountBase):
    account_id: int
    customer_id: int
    account_number: str
    balance: Decimal
    status_name: str
    overdraft_limit: Decimal
    opened_at: datetime
    updated_at: Optional[datetime] = None

    @validator('balance', 'overdraft_limit', pre=True, always=True)
    def validate_decimal_fields(cls, v):
        return Decimal(str(v))

    class Config:
        orm_mode = True

class AccountStatusUpdate(BaseModel):
    status: str # e.g., "active", "frozen", "closed"

class OverdraftLimitSet(BaseModel):
    limit: Decimal = Field(..., ge=0)

    @validator('limit', pre=True, always=True)
    def validate_limit(cls, v):
        return Decimal(str(v))


# --- Transaction Models ---
class TransactionBase(BaseModel):
    account_id: int
    amount: Decimal = Field(..., gt=0, description="Absolute amount, positive value.")
    description: Optional[str] = Field(None, max_length=255)

class DepositRequest(TransactionBase):
    pass

class WithdrawalRequest(TransactionBase):
    pass

class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=255)

class ACHTransactionRequest(TransactionBase):
    ach_type: str = Field(..., pattern="^(credit|debit)$") # 'credit' or 'debit'

class WireTransactionRequest(TransactionBase):
    direction: str = Field(..., pattern="^(incoming|outgoing)$") # 'incoming' or 'outgoing'

class TransactionDetails(BaseModel):
    transaction_id: int
    account_id: int
    type_name: str
    amount: Decimal # Positive for credit, negative for debit as stored in DB
    transaction_timestamp: datetime
    description: Optional[str] = None
    related_account_id: Optional[int] = None

    @validator('amount', pre=True, always=True)
    def validate_amount(cls, v):
        return Decimal(str(v))

    class Config:
        orm_mode = True

class TransferResponse(BaseModel):
    debit_transaction: TransactionDetails
    credit_transaction: TransactionDetails


# --- Fee Models ---
class FeeRequest(BaseModel):
    account_id: int
    fee_type_name: str
    fee_amount: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = None

class FeeApplicationResponse(BaseModel):
    transaction_id: int
    account_id: int
    fee_type_name: str
    applied_fee_amount: Decimal
    description: str

    @validator('applied_fee_amount', pre=True, always=True)
    def validate_applied_fee_amount(cls, v):
        return Decimal(str(v))


# --- Statement Models ---
class StatementTransaction(BaseModel):
    transaction_id: int
    timestamp: str # ISO format string
    type: str
    amount: Decimal
    debit: Decimal
    credit: Decimal
    description: Optional[str] = None
    related_account_number: Optional[str] = None
    running_balance: Decimal

    @validator('amount', 'debit', 'credit', 'running_balance', pre=True, always=True)
    def validate_statement_decimals(cls, v):
        return Decimal(str(v))

class StatementAccountInfo(BaseModel):
    account_number: str
    account_type: str
    currency: str
    overdraft_limit: Decimal

    @validator('overdraft_limit', pre=True, always=True)
    def validate_overdraft(cls, v):
        return Decimal(str(v))


class StatementCustomerInfo(BaseModel):
    customer_id: int
    name: str
    email: EmailStr
    address: Optional[str]

class StatementPeriod(BaseModel):
    start_date: str
    end_date: str
    generated_at: str # ISO format string

class AccountStatementResponse(BaseModel):
    account_info: StatementAccountInfo
    customer_info: StatementCustomerInfo
    period: StatementPeriod
    starting_balance: Decimal
    ending_balance: Decimal
    transactions: List[StatementTransaction]

    @validator('starting_balance', 'ending_balance', pre=True, always=True)
    def validate_balances(cls, v):
        return Decimal(str(v))

# --- Reporting Models ---
# No specific Pydantic models for CSV export request body needed if using query params.
# Response is FileResponse.

# --- Audit Log Models (Example if needed for API response) ---
class AuditLogEntry(BaseModel):
    log_id: int
    user_id: Optional[int] = None
    action_type: str
    target_entity: str
    target_id: str
    timestamp: datetime
    details_json: Optional[Union[dict, list]] = Field(None, alias="details") # Using alias for potential direct JSON use

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


# --- Accounting Validator Models (Example if needed for API response) ---
class LedgerIntegrityResponse(BaseModel):
    is_balanced: bool
    total_sum_transactions: Decimal

    @validator('total_sum_transactions', pre=True, always=True)
    def validate_total_sum(cls, v):
        return Decimal(str(v))


class AccountBalanceCheckResponse(BaseModel):
    account_id: int
    matches: bool
    reported_balance: Decimal
    transactions_sum: Decimal

    @validator('reported_balance', 'transactions_sum', pre=True, always=True)
    def validate_balances_check(cls, v):
        return Decimal(str(v))

```
