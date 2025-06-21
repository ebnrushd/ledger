import sys
import os
from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from fastapi.responses import HTMLResponse

# Assuming uvicorn runs from project root
from ....dependencies import get_db, get_current_admin_user, require_role # Added require_role
from ....models import HttpError

# Services
from core import customer_management
from core.customer_management import CustomerNotFoundError
from core import account_management # To fetch accounts for a customer

router = APIRouter(
    prefix="/admin/customers",
    tags=["Admin - Customer Management"],
    dependencies=[Depends(require_role(['admin', 'teller', 'auditor']))] # Roles allowed to view customer data
)

# AdminUser = Depends(get_current_admin_user) # No longer needed if using current_admin in signature

@router.get("/", response_class=HTMLResponse, name="admin_list_customers")
async def list_all_customers(
    request: Request,
    current_admin: dict = Depends(get_current_admin_user), # Still get user for display
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=5, le=100),
    search_query: Optional[str] = Query(None, description="Search by name or email, ID"),
    db_conn = Depends(get_db) # For service functions
):
    """Display list of customers with pagination and search."""
    # This would ideally use a dedicated service function in customer_management
    # that supports pagination and searching.
    # For now, let's assume a placeholder or adapt.
    # Let's create a simple list all for now, pagination/search to be added to core if complex.

    # Placeholder: Fetching all customers. Real app needs pagination in core.
    # For now, this will fetch all and slice, which is inefficient for large datasets.
    # A proper implementation would pass pagination/search params to a core service function.

    # Simulating fetching all and then manually paginating for the sake of example,
    # but this is NOT how it should be done in production.
    # The core service should support pagination.

    # This is a conceptual placeholder for how customer listing with search might be handled.
    # A real implementation needs `customer_management.list_customers(page, per_page, search_query)`

    # Let's assume a simplified list_customers function for now or fetch all for demo
    # This router will now use `customer_management.list_customers`
    current_admin: dict = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    """Display list of customers with pagination and search."""
    customers_data = {}
    error_message = None
    try:
        # Use the service layer function for listing customers
        customers_data = customer_management.list_customers(
            page=page,
            per_page=per_page,
            search_query=search_query,
            conn=db_conn
        )
    except CustomerNotFoundError as e: # Assuming list_customers might raise this if search yields nothing or on error
        error_message = str(e) # Or pass specific error message like "No customers found"
        customers_data = {"customers": [], "total_customers": 0} # Ensure template has these keys
    except Exception as e:
        error_message = f"Error fetching customers: {e}"
        customers_data = {"customers": [], "total_customers": 0}
        # In production, log this error.

    total_customers = customers_data.get("total_customers", 0)
    total_pages = (total_customers + per_page - 1) // per_page

    return request.state.templates.TemplateResponse("admin/customers_list.html", {
        "request": request, "page_title": "Manage Customers",
        "customers": customers_data.get("customers", []),
        "total_customers": total_customers,
        "current_page": page, "per_page": per_page, "total_pages": total_pages,
        "search_query": search_query, "error": error_message,
        "current_admin_username": current_admin.get('username')
    })


@router.get("/{customer_id}", response_class=HTMLResponse, name="admin_view_customer")
async def view_customer_detail_admin(
    request: Request,
    customer_id: int,
    current_admin: dict = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    """View a specific customer's details, including their accounts."""
    customer = None
    customer_accounts = []
    error_message = None
    error_message_accounts = None
    try:
        # `get_customer_by_id` uses its own connection if db_conn is not passed to it.
        # Refactor core functions to accept conn for consistency if needed.
        # For now, assuming it's okay or it's refactored.
        customer = customer_management.get_customer_by_id(customer_id) # Pass conn=db_conn if refactored

        # Fetch associated accounts for this customer using account_management.list_accounts
        accounts_data = account_management.list_accounts(
            customer_id_filter=customer_id,
            per_page=50, # Show up to 50 accounts on detail page, or implement pagination for accounts here too
            conn=db_conn
        )
        customer_accounts = accounts_data.get("accounts", [])

    except CustomerNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    except AccountError as e_acc: # Catch errors from list_accounts
        error_message_accounts = f"Error fetching accounts for customer: {e_acc}"
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        # Log error e

    return request.state.templates.TemplateResponse("admin/customer_detail.html", {
        "request": request,
        "page_title": f"Customer: {customer['first_name'] if customer else ''} {customer['last_name'] if customer else ''}",
        "customer": customer,
        "accounts": customer_accounts,
        "error": error_message, # General error for the page
        "error_accounts": error_message_accounts, # Specific error for accounts section
        "current_admin_username": current_admin.get('username')
    })

# Need to import psycopg2.extras for DictCursor if used directly in router
import psycopg2.extras
```
