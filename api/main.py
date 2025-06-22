import sys
import os
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

# Ensure project root is in PYTHONPATH for imports if running from api directory directly
# Better: Run uvicorn from project root (e.g. `uvicorn api.main:app --reload`)

from .models import HttpError # General error model

# Import custom exceptions from core modules to handle them globally
try:
    from core.customer_management import CustomerNotFoundError
    from core.account_management import AccountNotFoundError, AccountStatusError, InvalidAccountTypeError, AccountError
    from core.transaction_processing import (
        InsufficientFundsError, InvalidTransactionTypeError,
        AccountNotActiveOrFrozenError, TransactionError, InvalidAmountError
    )
    from core.fee_engine import FeeTypeNotFoundError, FeeError
    from core.user_service import UserNotFoundError as CoreUserNotFoundError # Alias if name clashes
    from core.user_service import UserAlreadyExistsError as CoreUserAlreadyExistsError
    from core.user_service import UserServiceError as CoreUserServiceError
    from reporting.reports import ReportingError
    from reporting.statements import StatementError
    # from core.security import ExchangeRateNotFoundError # Example
except ImportError as e:
    print(f"Warning: Error importing core/reporting modules in api/main.py: {e}")
    pass


from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

SESSION_SECRET_KEY = "super_secret_key_for_sql_ledger_admin_demo"


app = FastAPI(
    title="SQL Ledger API",
    version="0.1.0",
    description="API for managing customers, accounts, transactions, and reporting for the SQL Ledger system.",
)

# --- Add Middleware ---
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
)


# --- Global Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error['loc'])
        message = error['msg']
        error_messages.append(f"Field '{field}': {message}")
    # For HTML admin pages, could render an error template if path indicates
    if request.url.path.startswith("/admin") and "text/html" in request.headers.get("accept", ""):
        return request.state.templates.TemplateResponse("admin/error_general.html", { # Assuming a general error template
            "request": request, "page_title": "Validation Error",
            "error_summary": "Input validation failed.", "errors_list": error_messages
        }, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": error_messages},
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    # This typically catches errors in response model validation
    print(f"Pydantic response model validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Response Model Validation Error", "errors": exc.errors()},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler_admin_aware(request: Request, exc: HTTPException):
    if request.url.path.startswith(("/admin", "/api/admin")) and "text/html" in request.headers.get("accept", ""):
        template_name = "admin/error_general.html"
        context = {"request": request, "page_title": f"Error {exc.status_code}", "error_summary": exc.detail, "detail": exc.detail}
        if exc.status_code == status.HTTP_403_FORBIDDEN:
            template_name = "admin/error_403.html"
            context["page_title"] = "Access Denied"
        # elif exc.status_code == status.HTTP_404_NOT_FOUND:
            # template_name = "admin/error_404.html" # If you create a specific 404 admin template
            # context["page_title"] = "Resource Not Found"

        # Check if templates are available on request.state, might not be for all error paths
        if hasattr(request.state, "templates"):
            return request.state.templates.TemplateResponse(template_name, context, status_code=exc.status_code)
        else: # Fallback if templates not on state (e.g. middleware error before templates added)
            return HTMLResponse(f"<html><body><h1>Error {exc.status_code}</h1><p>{exc.detail}</p></body></html>", status_code=exc.status_code)

    # Default JSON response for API type HttpExceptions or non-HTML requests
    headers = exc.headers if hasattr(exc, "headers") else None # getattr(exc, "headers", None)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)


# Custom exceptions from the `core` modules
@app.exception_handler(CustomerNotFoundError)
@app.exception_handler(AccountNotFoundError)
@app.exception_handler(FeeTypeNotFoundError)
@app.exception_handler(CoreUserNotFoundError) # Aliased at import
async def resource_not_found_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

@app.exception_handler(AccountStatusError)
@app.exception_handler(InvalidAccountTypeError)
@app.exception_handler(InsufficientFundsError)
@app.exception_handler(InvalidTransactionTypeError)
@app.exception_handler(AccountNotActiveOrFrozenError)
@app.exception_handler(TransactionError)
@app.exception_handler(FeeError)
@app.exception_handler(InvalidAmountError)
@app.exception_handler(CoreUserAlreadyExistsError) # Aliased
async def business_rule_violation_handler(request: Request, exc: Exception):
    status_to_return = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, CoreUserAlreadyExistsError): # Example of specific status for an error type
        status_to_return = status.HTTP_409_CONFLICT
    return JSONResponse(status_code=status_to_return, content={"detail": str(exc)})

@app.exception_handler(ReportingError)
@app.exception_handler(StatementError)
async def reporting_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": f"A reporting error occurred: {str(exc)}"})

@app.exception_handler(AccountError)
@app.exception_handler(CoreUserServiceError) # Aliased
async def core_general_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": f"An internal service error occurred: {str(exc)}"})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"Generic unhandled exception: {type(exc).__name__} - {str(exc)}")
    # import traceback; traceback.print_exc();
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"An unexpected internal server error occurred."}
    )

# --- Mount static files and templates ---
templates = Jinja2Templates(directory="api/templates")

@app.middleware("http")
async def add_templates_to_request_state(request: Request, call_next):
    request.state.templates = templates
    response = await call_next(request)
    return response

# --- Include Routers ---
# V1 API Routers (JWT authenticated)
from .routers.v1 import auth as v1_auth_router
app.include_router(v1_auth_router.router)

from .routers import customers as v1_customers_router # Alias to distinguish
from .routers import accounts as v1_accounts_router
from .routers import transactions as v1_transactions_router
from .routers import fees as v1_fees_router
from .routers import reports as v1_reports_router

app.include_router(v1_customers_router.router, prefix="/api/v1")
app.include_router(v1_accounts_router.router, prefix="/api/v1")
app.include_router(v1_transactions_router.router, prefix="/api/v1")
app.include_router(v1_fees_router.router, prefix="/api/v1") # Not JWT protected yet, but part of v1
app.include_router(v1_reports_router.router, prefix="/api/v1")

# Admin Routers (HTML serving, session authenticated)
from .routers.admin import auth as admin_auth_router
from .routers.admin import dashboard as admin_dashboard_router
from .routers.admin import users as admin_users_router
from .routers.admin import customers as admin_customers_router
from .routers.admin import accounts as admin_accounts_router
from .routers.admin import transactions as admin_transactions_router
from .routers.admin import audit as admin_audit_router

app.include_router(admin_auth_router.router)
app.include_router(admin_dashboard_router.router)
app.include_router(admin_users_router.router)
app.include_router(admin_customers_router.router)
app.include_router(admin_accounts_router.router)
app.include_router(admin_transactions_router.router)
app.include_router(admin_audit_router.router)

# JSON Admin API Routers (session authenticated, could be JWT if desired)
from .routers.api_admin import dashboard as api_admin_dashboard_router
from .routers.api_admin import users as api_admin_users_router
from .routers.api_admin import customers as api_admin_customers_router
from .routers.api_admin import accounts as api_admin_accounts_router
from .routers.api_admin import transactions as api_admin_transactions_router
from .routers.api_admin import audit as api_admin_audit_router
from .routers.api_admin import lookups as api_admin_lookups_router # New lookups router

app.include_router(api_admin_dashboard_router.router)
app.include_router(api_admin_users_router.router)
app.include_router(api_admin_customers_router.router)
app.include_router(api_admin_accounts_router.router)
app.include_router(api_admin_transactions_router.router)
app.include_router(api_admin_audit_router.router)
app.include_router(api_admin_lookups_router.router) # Add the lookups router


@app.get("/", tags=["Root"], summary="Root path of the API")
async def read_root():
    return {
        "message": "Welcome to the SQL Ledger API",
        "documentation_swagger": "/docs",
        "documentation_redoc": "/redoc",
        "admin_panel_html_login": "/admin/login",
        "api_v1_login_for_jwt": "/api/v1/auth/login"
    }

```
