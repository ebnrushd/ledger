import pytest
from fastapi.testclient import TestClient
from fastapi import status

# Test using the admin_client fixture from conftest.py for authenticated requests

def test_get_admin_dashboard_success(admin_client: TestClient):
    """Test that the admin dashboard loads successfully for an authenticated admin."""
    response = admin_client.get("/admin/dashboard")
    assert response.status_code == status.HTTP_200_OK
    assert "Dashboard Overview" in response.text # Check for page title
    assert "Total Customers" in response.text
    assert "Total Accounts" in response.text
    assert "Recent Transactions" in response.text
    # Further checks could involve asserting specific data if test data is pre-populated
    # For example, if we know there's 1 customer and 2 accounts after setup:
    # assert "1</p>" in response.text # For total customers, simplistic check
    # This requires more control over data state or more complex parsing.

def test_get_admin_dashboard_unauthenticated(test_client: TestClient): # Uses non-authenticated client
    """Test accessing dashboard unauthenticated redirects to login."""
    response = test_client.get("/admin/dashboard")
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert "login" in response.headers["location"]

def test_get_admin_dashboard_as_teller(teller_client: TestClient):
    """Test that a teller can also access the admin dashboard."""
    response = teller_client.get("/admin/dashboard")
    assert response.status_code == status.HTTP_200_OK
    assert "Dashboard Overview" in response.text
    assert "Welcome, test_teller_user" in response.text # Verify teller username displayed

# More detailed tests for dashboard data would require:
# 1. Fixtures to create a known state (e.g., specific number of customers, accounts, recent transactions).
# 2. Parsing HTML to extract the displayed numbers and compare them.
# For this subtask, ensuring the page loads with key sections is a good start.
# Example (conceptual, requires HTML parsing library like BeautifulSoup):
# from bs4 import BeautifulSoup
# def test_dashboard_data_accuracy(admin_client: TestClient, setup_specific_dashboard_data):
#     # setup_specific_dashboard_data would be a fixture creating, e.g., 2 customers, 3 accounts, 5 txns
#     response = admin_client.get("/admin/dashboard")
#     soup = BeautifulSoup(response.text, "html.parser")
#     # Example: find the card for total customers and check its text
#     # This is highly dependent on exact HTML structure from the template.
#     total_customers_card = soup.find(...)
#     assert "2" in total_customers_card.text
```
