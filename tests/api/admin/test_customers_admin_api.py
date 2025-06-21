import pytest
from fastapi.testclient import TestClient
from fastapi import status

# Uses admin_client, teller_client fixtures from conftest.py
# Uses create_customer_fx from conftest.py for setting up data via core function

@pytest.fixture
def setup_customers_for_admin_list(db_conn, create_customer_fx):
    """Create a few customers for list testing."""
    cust1_id = create_customer_fx(first_name="AdminList", last_name="CustOne", email_suffix="@adminlist1.com")
    cust2_id = create_customer_fx(first_name="AdminList", last_name="CustTwo", email_suffix="@adminlist2.com")
    cust3_id = create_customer_fx(first_name="Another", last_name="Person", email_suffix="@anotherperson.com")
    db_conn.commit() # Ensure customers are committed
    return {"c1": cust1_id, "c2": cust2_id, "c3": cust3_id,
            "c1_email": "adminlist.custone", "c3_name": "Another"} # Partial details for search

def test_list_customers_as_admin(admin_client: TestClient, setup_customers_for_admin_list):
    """Admin should see a list of customers."""
    response = admin_client.get("/admin/customers/")
    assert response.status_code == status.HTTP_200_OK
    assert "Customer Management" in response.text
    assert "AdminList CustOne" in response.text
    assert "AdminList CustTwo" in response.text
    assert "Another Person" in response.text

def test_list_customers_search_by_name_as_admin(admin_client: TestClient, setup_customers_for_admin_list):
    """Test searching customers by name."""
    search_name = setup_customers_for_admin_list["c3_name"] # "Another"
    response = admin_client.get(f"/admin/customers/?search_query={search_name}")
    assert response.status_code == status.HTTP_200_OK
    assert "Another Person" in response.text
    assert "AdminList CustOne" not in response.text # Should be filtered out

def test_list_customers_search_by_email_as_admin(admin_client: TestClient, setup_customers_for_admin_list):
    """Test searching customers by part of email."""
    search_email_part = setup_customers_for_admin_list["c1_email"] # "adminlist.custone"
    response = admin_client.get(f"/admin/customers/?search_query={search_email_part}")
    assert response.status_code == status.HTTP_200_OK
    assert "AdminList CustOne" in response.text
    assert "Another Person" not in response.text

def test_list_customers_pagination_as_admin(admin_client: TestClient, setup_customers_for_admin_list):
    """Test pagination for customer list."""
    # setup_customers_for_admin_list creates 3 customers
    # Test with per_page = 2, expect 2 pages
    response_page1 = admin_client.get("/admin/customers/?per_page=2&page=1")
    assert response_page1.status_code == status.HTTP_200_OK
    # Based on default ordering (customer_id DESC in service), 'Another Person' (last created) should be on page 1
    assert "Another Person" in response_page1.text
    # Check if pagination controls are present (simplistic check)
    assert "page-link" in response_page1.text
    assert "Page 1 of 2" in response_page1.text # Assuming total 3, per_page 2 = 2 pages

    response_page2 = admin_client.get("/admin/customers/?per_page=2&page=2")
    assert response_page2.status_code == status.HTTP_200_OK
    # 'AdminList CustOne' (first created) should be on page 2
    assert "AdminList CustOne" in response_page2.text
    assert "Page 2 of 2" in response_page2.text


def test_view_customer_detail_as_admin(admin_client: TestClient, setup_customers_for_admin_list, db_conn):
    """Admin views details of an existing customer, including associated accounts."""
    customer_id = setup_customers_for_admin_list["c1"]

    # Create an account for this customer to check if it's displayed
    from core.account_management import open_account
    acc_id = open_account(customer_id, "savings", initial_balance=100.00, conn=db_conn)
    db_conn.commit()
    acc_details = admin_client.get(f"/accounts/{acc_id}").json() # Get account number via API to check on page
    account_number_to_check = acc_details["account_number"]

    response = admin_client.get(f"/admin/customers/{customer_id}")
    assert response.status_code == status.HTTP_200_OK
    assert "Customer Profile: AdminList CustOne" in response.text # Check for page title part
    assert "AdminList CustOne" in response.text
    assert "adminlist1.com" in response.text # Part of email
    assert "Associated Accounts" in response.text
    assert account_number_to_check in response.text # Check if account number is listed

def test_view_customer_detail_not_found_as_admin(admin_client: TestClient):
    """Test viewing a non-existent customer."""
    response = admin_client.get("/admin/customers/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # The global exception handler for HTTPException should render an error page for admin
    # or return JSON. If it's JSON:
    # assert "Customer not found" in response.json()["detail"]
    # If it's HTML (as per current main.py for 403, but 404 might be JSON):
    # For now, assume it might be JSON for 404s until a specific admin 404 page is handled.
    # The current setup in main.py's http_exception_handler_admin_aware does not explicitly render
    # an HTML page for 404s in /admin section, so it will fall back to JSONResponse.
    assert "Customer not found" in response.json()["detail"]


def test_list_customers_as_teller(teller_client: TestClient, setup_customers_for_admin_list):
    """Teller should also be able to view customer list."""
    response = teller_client.get("/admin/customers/")
    assert response.status_code == status.HTTP_200_OK
    assert "Customer Management" in response.text
    assert "AdminList CustOne" in response.text # Check for some customer data
```
