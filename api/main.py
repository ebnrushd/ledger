import sys
import os
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError # For handling Pydantic model validation errors specifically

# Ensure project root is in PYTHONPATH for imports if running from api directory directly
# Better: Run uvicorn from project root (e.g. `uvicorn api.main:app --reload`)
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .routers import customers, accounts, transactions, fees, reports
from .models import HttpError

# Import custom exceptions from core modules to handle them globally
# This requires that the `core` directory is discoverable.
try:
    from core.customer_management import CustomerNotFoundError
    from core.account_management import AccountNotFoundError, AccountStatusError, InvalidAccountTypeError, AccountError
    from core.transaction_processing import (
        InsufficientFundsError, InvalidTransactionTypeError,
        AccountNotActiveOrFrozenError, TransactionError, InvalidAmountError
    )
    from core.fee_engine import FeeTypeNotFoundError, FeeError
    from reporting.reports import ReportingError
    from reporting.statements import StatementError
except ImportError as e:
    print(f"Error importing core/reporting modules in api/main.py: {e}")
    print("Ensure that the application is run from the project root (e.g., 'sql-ledger/' directory)"
          " or that PYTHONPATH is configured correctly.")
    # To make it potentially runnable if `core` is sibling to `api` and PWD is `api`
    # This is a fallback, proper project structure and running from root is preferred.
    # sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..')) # Add project root (parent of api)
    # from core.customer_management import CustomerNotFoundError
    # ... (repeat for all other custom exceptions)
    # This is getting complex, so relying on correct execution environment (PYTHONPATH includes project root)
    # is the cleaner way.
    raise


app = FastAPI(
    title="SQL Ledger API",
    version="0.1.0",
    description="API for managing customers, accounts, transactions, and reporting for the SQL Ledger system.",
    # docs_url="/docs", # Default
    # redoc_url="/redoc" # Default
)

# --- Global Exception Handlers ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log exc.errors() for more details if needed
    error_messages = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error['loc'])
        message = error['msg']
        error_messages.append(f"Field '{field}': {message}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": error_messages},
    )

@app.exception_handler(ValidationError) # Handles Pydantic errors not caught by RequestValidationError (e.g. in response models if not careful)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 422 if it's clear it's client-side input causing response model error
        content={"detail": "Pydantic Model Validation Error (likely in response)", "errors": exc.errors()},
    )

# Custom exceptions from the `core` modules
@app.exception_handler(CustomerNotFoundError)
@app.exception_handler(AccountNotFoundError)
@app.exception_handler(FeeTypeNotFoundError)
# @app.exception_handler(ExchangeRateNotFoundError) # Assuming this is defined in currency_service
async def resource_not_found_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )

@app.exception_handler(AccountStatusError)
@app.exception_handler(InvalidAccountTypeError)
@app.exception_handler(InsufficientFundsError)
@app.exception_handler(InvalidTransactionTypeError)
@app.exception_handler(AccountNotActiveOrFrozenError)
@app.exception_handler(TransactionError) # General transaction error
@app.exception_handler(FeeError)         # General fee error
@app.exception_handler(InvalidAmountError)
async def business_rule_violation_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, # Or 409 Conflict for some
        content={"detail": str(exc)},
    )

@app.exception_handler(ReportingError)
@app.exception_handler(StatementError)
async def reporting_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"A reporting error occurred: {str(exc)}"},
    )

# Catch-all for other AccountErrors or core errors not specifically handled
@app.exception_handler(AccountError) # General account error
async def core_account_error_handler(request: Request, exc: AccountError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"An internal account management error occurred: {str(exc)}"},
    )

# Generic fallback handler for any other unhandled exceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log the exception here for debugging (exc)
    # import traceback; traceback.print_exc(); # For detailed logging during development
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"An unexpected internal server error occurred: {type(exc).__name__} - {str(exc)}"},
    )


# --- Include Routers ---
app.include_router(customers.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(fees.router)
app.include_router(reports.router)


@app.get("/", tags=["Root"], summary="Root path of the API")
async def read_root():
    """
    Welcome message for the SQL Ledger API.
    Provides links to the API documentation.
    """
    return {
        "message": "Welcome to the SQL Ledger API",
        "documentation_swagger": "/docs",
        "documentation_redoc": "/redoc"
    }

# To run (from project root, e.g., sql-ledger/):
# uvicorn api.main:app --reload

# Note on Database Connection Management:
# The `get_db` dependency in `api/dependencies.py` handles per-request DB connections.
# Core service functions currently mostly use `execute_query` which creates its own connection.
# For operations that need to be part of a larger API-controlled transaction,
# core functions would need to be refactored to accept an existing connection/cursor.
# This is a known simplification for this subtask. The current setup ensures each core
# operation is atomic on its own.
```
