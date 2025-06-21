import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List

# Assuming uvicorn runs from project root
from ....dependencies import get_db, get_current_admin_user, require_role
from ....models import ( # Import JSON API specific models
    HttpError, CustomerDetails, AccountDetails, # Reusing existing detail models
    AdminCustomerListResponse, UserSchema # UserSchema for current_admin type hint
)

# Services
from core import customer_management, account_management # account_management for fetching customer's accounts
from core.customer_management import CustomerNotFoundError
from core.account_management import AccountError as CoreAccountError # Alias to avoid conflict

router = APIRouter(
    prefix="/api/admin/customers",
    tags=["Admin API - Customer Management"],
    dependencies=[Depends(require_role(['admin', 'teller', 'auditor']))]
)

class CustomerDetailWithAccountsResponse(CustomerDetails):
    """Extends CustomerDetails to include a list of associated accounts for admin API."""
    accounts: List[AccountDetails] = []


@router.get("/", response_model=AdminCustomerListResponse)
async def list_customers_api(
    current_admin: UserSchema = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=5, le=100),
    search_query: Optional[str] = Query(None, description="Search by name, email, or ID"),
    db_conn = Depends(get_db)
):
    """Retrieve a paginated list of customers with optional search."""
    try:
        customers_data_dict = customer_management.list_customers(
            page=page, per_page=per_page, search_query=search_query, conn=db_conn
        )
        # Convert customer dicts to CustomerDetails model if needed (list_customers returns dicts)
        return AdminCustomerListResponse(
            customers=[CustomerDetails(**cust) for cust in customers_data_dict.get("customers", [])],
            total_items=customers_data_dict.get("total_customers", 0),
            total_pages=(customers_data_dict.get("total_customers", 0) + per_page - 1) // per_page,
            page=page,
            per_page=per_page
        )
    except RuntimeError as e: # list_customers raises RuntimeError for general DB errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e_unhandled:
        print(f"Unhandled error in list_customers_api: {e_unhandled}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching customers.")


@router.get("/{customer_id}", response_model=CustomerDetailWithAccountsResponse)
async def get_customer_detail_api(
    customer_id: int,
    current_admin: UserSchema = Depends(get_current_admin_user),
    db_conn = Depends(get_db)
):
    """Retrieve details for a specific customer, including their accounts."""
    try:
        customer_dict = customer_management.get_customer_by_id(customer_id, conn=db_conn)
        # customer = CustomerDetails(**customer_dict) # Validate/cast to Pydantic model

        customer_accounts_list = []
        try:
            # Fetch associated accounts for this customer
            accounts_data = account_management.list_accounts(
                customer_id_filter=customer_id,
                per_page=200, # Assuming a customer won't have more than 200 accounts for this detail view
                page=1,
                conn=db_conn
            )
            customer_accounts_list = [AccountDetails(**acc) for acc in accounts_data.get("accounts", [])]
        except CoreAccountError as e_acc:
            # Log this error, but still return customer details if fetched
            print(f"Error fetching accounts for customer {customer_id} in admin API detail: {e_acc}")
            # Optionally, include this error information in the response if needed

        # Combine customer details with accounts
        response_data = {**customer_dict, "accounts": customer_accounts_list}
        return CustomerDetailWithAccountsResponse(**response_data)

    except CustomerNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    except Exception as e: # Catch other unexpected errors
        print(f"Error fetching customer detail API for {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

# Note: Admin API for creating/updating customers is not implemented in this iteration.
# These actions would typically be done via more controlled processes or specific internal tools,
# or through the /api/v1/auth/register (for create) and /api/v1/customers/me (for user self-update) endpoints.
# If direct admin manipulation of customer records via API is needed, POST/PUT/DELETE endpoints would be added here.
```
