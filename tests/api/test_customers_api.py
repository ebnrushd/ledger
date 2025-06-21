import pytest
from fastapi.testclient import TestClient
from fastapi import status # For status codes

# Assuming conftest.py provides test_client fixture and manages DB for API tests
# from ..models import CustomerDetails, CustomerCreate, CustomerUpdate # Adjust import if needed
# The API models are in api.models, so if tests/api/ is run, it might be `from api.models import ...`
# Or, if PYTHONPATH is set to project root: `from api.models import ...`
# Let's assume the latter based on typical pytest setup from project root.
from api.models import CustomerDetails, CustomerCreate, CustomerUpdate, HttpError

# --- Test Data ---
customer_payload_valid = {
    "first_name": "API_John",
    "last_name": "Doe",
    "email": "api.john.doe@example.com",
    "phone_number": "555-0101",
    "address": "123 API Test St"
}

customer_payload_updated = {
    "first_name": "API_Johnny",
    "phone_number": "555-0102",
    "address": "456 API Updated Ave"
}

# --- Tests for Customer API Endpoints ---

def test_create_customer_success(test_client: TestClient):
    """Test successful customer creation."""
    response = test_client.post("/customers/", json=customer_payload_valid)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == customer_payload_valid["email"]
    assert data["first_name"] == customer_payload_valid["first_name"]
    assert "customer_id" in data
    # Store this ID for subsequent tests if needed, or rely on db_conn fixture's cleanup
    # For true isolation, each test should set up and tear down its own specific data.
    # The db_conn fixture in conftest.py clears tables before each test.

def test_create_customer_duplicate_email(test_client: TestClient):
    """Test creating a customer with an email that already exists."""
    # Create the first customer
    test_client.post("/customers/", json=customer_payload_valid) # Assumes this email is now in DB for this test

    # Attempt to create another customer with the same email
    duplicate_payload = customer_payload_valid.copy()
    duplicate_payload["first_name"] = "AnotherJohn" # Different name, same email
    response = test_client.post("/customers/", json=duplicate_payload)

    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert "Customer with this email already exists" in data["detail"]

def test_create_customer_invalid_input_bad_email(test_client: TestClient):
    """Test customer creation with invalid email format."""
    invalid_payload = customer_payload_valid.copy()
    invalid_payload["email"] = "not-an-email"
    response = test_client.post("/customers/", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # FastAPI/Pydantic validation
    data = response.json()
    assert "Validation Error" in data["detail"]
    assert any("value is not a valid email address" in err for err in data["errors"])


def test_get_customer_success(test_client: TestClient):
    """Test fetching an existing customer by ID."""
    # Create a customer first
    create_response = test_client.post("/customers/", json=customer_payload_valid)
    customer_id = create_response.json()["customer_id"]

    response = test_client.get(f"/customers/{customer_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["customer_id"] == customer_id
    assert data["email"] == customer_payload_valid["email"]

def test_get_customer_not_found(test_client: TestClient):
    """Test fetching a non-existent customer."""
    non_existent_id = 999999
    response = test_client.get(f"/customers/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert f"Customer with ID {non_existent_id} not found" in data["detail"]


def test_update_customer_success(test_client: TestClient):
    """Test successfully updating a customer's information."""
    # Create a customer
    create_response = test_client.post("/customers/", json=customer_payload_valid)
    customer_id = create_response.json()["customer_id"]

    # Update some fields
    update_payload = {
        "first_name": "API_Johnathan",
        "address": "789 New API Rd"
    }
    response = test_client.put(f"/customers/{customer_id}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["customer_id"] == customer_id
    assert data["first_name"] == "API_Johnathan"
    assert data["email"] == customer_payload_valid["email"] # Email should not change if not provided
    assert data["address"] == "789 New API Rd"

def test_update_customer_change_email_success(test_client: TestClient):
    """Test changing a customer's email via API."""
    create_response = test_client.post("/customers/", json=customer_payload_valid)
    customer_id = create_response.json()["customer_id"]

    new_email = "updated.api.email@example.com"
    update_payload_email = {"email": new_email}
    response = test_client.put(f"/customers/{customer_id}", json=update_payload_email)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == new_email

def test_update_customer_email_conflict(test_client: TestClient):
    """Test updating email to one that already exists for another customer."""
    # Customer 1 (will be updated)
    cust1_payload = {"first_name": "Updater", "last_name": "Test", "email": "updater.test@example.com"}
    resp1 = test_client.post("/customers/", json=cust1_payload)
    cust1_id = resp1.json()["customer_id"]

    # Customer 2 (whose email will cause conflict)
    cust2_payload = {"first_name": "Existing", "last_name": "EmailUser", "email": "existing.emailuser@example.com"}
    test_client.post("/customers/", json=cust2_payload) # This email now exists

    # Attempt to update Customer 1's email to Customer 2's email
    conflict_update_payload = {"email": cust2_payload["email"]}
    response = test_client.put(f"/customers/{cust1_id}", json=conflict_update_payload)

    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert f"email {cust2_payload['email']} already exists" in data["detail"]


def test_update_customer_not_found(test_client: TestClient):
    """Test updating a non-existent customer."""
    non_existent_id = 999888
    response = test_client.put(f"/customers/{non_existent_id}", json={"first_name": "GhostAPI"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert f"Customer with ID {non_existent_id} not found" in data["detail"]

def test_update_customer_no_fields(test_client: TestClient):
    """Test calling update endpoint with an empty payload."""
    create_response = test_client.post("/customers/", json=customer_payload_valid)
    customer_id = create_response.json()["customer_id"]

    response = test_client.put(f"/customers/{customer_id}", json={}) # Empty JSON
    assert response.status_code == status.HTTP_400_BAD_REQUEST # As per router logic
    data = response.json()
    assert "No fields provided for update" in data["detail"]

```
