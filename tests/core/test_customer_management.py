import pytest
import psycopg2 # For type hinting and specific exceptions if needed

# Import functions to be tested
from core.customer_management import (
    add_customer,
    get_customer_by_id,
    get_customer_by_email,
    update_customer_info,
    CustomerNotFoundError
)

# Test data
@pytest.fixture
def sample_customer_data():
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone_number": "555-1234",
        "address": "123 Main St, Anytown"
    }

@pytest.fixture
def another_customer_data():
    return {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "phone_number": "555-5678",
        "address": "456 Oak Ave, Otherville"
    }

# --- Tests for add_customer ---
def test_add_customer_success(db_conn, sample_customer_data):
    """Test successfully adding a new customer."""
    customer_id = add_customer(**sample_customer_data)
    assert customer_id is not None
    assert isinstance(customer_id, int)

    # Verify by fetching
    fetched_customer = get_customer_by_id(customer_id) # Uses its own connection via execute_query
    assert fetched_customer is not None
    assert fetched_customer["email"] == sample_customer_data["email"]
    assert fetched_customer["first_name"] == sample_customer_data["first_name"]

def test_add_customer_duplicate_email(db_conn, sample_customer_data):
    """Test adding a customer with an email that already exists."""
    add_customer(**sample_customer_data) # Add first customer

    with pytest.raises(ValueError, match="Customer with email .* already exists"):
        # Attempt to add another customer with the same email
        add_customer(
            first_name="Johnny",
            last_name="Doeman",
            email=sample_customer_data["email"] # Same email
        )

def test_add_customer_minimal_data(db_conn):
    """Test adding a customer with only required fields."""
    customer_id = add_customer(first_name="Min", last_name="Mal", email="min.mal@example.com")
    assert customer_id is not None
    fetched_customer = get_customer_by_id(customer_id)
    assert fetched_customer["email"] == "min.mal@example.com"
    assert fetched_customer["phone_number"] is None
    assert fetched_customer["address"] is None


# --- Tests for get_customer_by_id ---
def test_get_customer_by_id_success(db_conn, create_customer_fx, sample_customer_data):
    """Test fetching an existing customer by their ID."""
    # Use fixture to create a customer first for this specific test, ensuring isolation
    # The email in sample_customer_data might conflict if create_customer_fx uses it directly
    # and a previous test in this file also used it.
    # create_customer_fx generates unique emails, so it's fine.
    customer_id = create_customer_fx(
        first_name=sample_customer_data["first_name"],
        last_name=sample_customer_data["last_name"],
        email_suffix="@getbyid.example.com", # Ensure unique email domain for this test
        phone=sample_customer_data["phone_number"],
        address=sample_customer_data["address"]
    )

    customer = get_customer_by_id(customer_id)
    assert customer is not None
    assert customer["customer_id"] == customer_id
    assert customer["first_name"] == sample_customer_data["first_name"]
    assert customer["email"].endswith("@getbyid.example.com")


def test_get_customer_by_id_not_found(db_conn):
    """Test fetching a non-existent customer by ID."""
    non_existent_id = 9999999
    with pytest.raises(CustomerNotFoundError, match=f"Customer with ID {non_existent_id} not found"):
        get_customer_by_id(non_existent_id)


# --- Tests for get_customer_by_email ---
def test_get_customer_by_email_success(db_conn, create_customer_fx, sample_customer_data):
    """Test fetching an existing customer by their email."""
    unique_email = f"get.by.email.{sample_customer_data['first_name'].lower()}@example.com"
    create_customer_fx(
        first_name=sample_customer_data["first_name"],
        last_name=sample_customer_data["last_name"],
        email_suffix=unique_email.split('@')[1], # Pass only the domain part or adjust fixture
        # For simplicity, let's just provide the full unique email to the fixture if it supports it
        # Or, adjust create_customer_fx to take a full email.
        # Current create_customer_fx builds email, so we need to match its pattern or fetch what it created.
        # Let's assume create_customer_fx takes full email for this test or we adapt.
        # For now, let's use the fixture's generated email.
    )
    # This is tricky. The create_customer_fx generates a UUID based email.
    # To test get_customer_by_email, we need to know the email.
    # Option 1: Modify create_customer_fx to return the created email or accept a fixed one.
    # Option 2: Create customer directly here.

    direct_email = "direct.fetch@example.com"
    add_customer(
        first_name="Direct", last_name="Fetch", email=direct_email,
        phone_number=sample_customer_data["phone_number"], address=sample_customer_data["address"]
    )

    customer = get_customer_by_email(direct_email)
    assert customer is not None
    assert customer["email"] == direct_email
    assert customer["first_name"] == "Direct"

def test_get_customer_by_email_not_found(db_conn):
    """Test fetching a non-existent customer by email."""
    non_existent_email = "no.one.here@example.com"
    with pytest.raises(CustomerNotFoundError, match=f"Customer with email {non_existent_email} not found"):
        get_customer_by_email(non_existent_email)

# --- Tests for update_customer_info ---
def test_update_customer_info_success(db_conn, create_customer_fx):
    """Test successfully updating customer's information."""
    customer_id = create_customer_fx(first_name="Initial", last_name="Name", email_suffix="@update.example.com")

    update_data = {
        "first_name": "UpdatedFirst",
        "phone_number": "555-9999",
        "address": "1 New Address Lane"
    }
    success = update_customer_info(customer_id, **update_data)
    assert success is True

    updated_customer = get_customer_by_id(customer_id)
    assert updated_customer["first_name"] == "UpdatedFirst"
    assert updated_customer["last_name"] == "Name" # Should not change
    assert updated_customer["phone_number"] == "555-9999"
    assert updated_customer["address"] == "1 New Address Lane"

def test_update_customer_info_change_email(db_conn, create_customer_fx):
    """Test changing a customer's email."""
    customer_id = create_customer_fx(email_suffix="@changeemail.example.com")
    new_email = "changed.email@example.com"

    success = update_customer_info(customer_id, email=new_email)
    assert success is True
    updated_customer = get_customer_by_id(customer_id)
    assert updated_customer["email"] == new_email

def test_update_customer_info_duplicate_email_on_update(db_conn, create_customer_fx, another_customer_data):
    """Test updating email to one that already exists for another customer."""
    # Create first customer (will be updated)
    customer_id_to_update = create_customer_fx(first_name="Original", email_suffix="@original.example.com")
    # Create second customer whose email we will try to use
    existing_email_customer_id = create_customer_fx(
        first_name=another_customer_data["first_name"],
        last_name=another_customer_data["last_name"],
        email_suffix=f".{another_customer_data['last_name'].lower()}@existing.example.com" # Ensure unique email
    )
    existing_customer = get_customer_by_id(existing_email_customer_id)
    email_to_conflict_with = existing_customer["email"]

    with pytest.raises(ValueError, match=f"Cannot update: email {email_to_conflict_with} already exists"):
        update_customer_info(customer_id_to_update, email=email_to_conflict_with)

def test_update_customer_info_no_fields_provided(db_conn, create_customer_fx):
    """Test updating with no actual data fields provided (should ideally be a no-op or specific return)."""
    customer_id = create_customer_fx(email_suffix="@nofields.example.com")
    original_customer = get_customer_by_id(customer_id)

    # The core function currently returns False if no fields are to update.
    success = update_customer_info(customer_id) # No update kwargs
    assert success is False

    # Verify no changes occurred
    current_customer = get_customer_by_id(customer_id)
    assert current_customer["first_name"] == original_customer["first_name"]
    assert current_customer["email"] == original_customer["email"]


def test_update_customer_info_non_existent_customer(db_conn):
    """Test updating a customer that does not exist."""
    non_existent_id = 888888
    with pytest.raises(CustomerNotFoundError, match=f"Customer with ID {non_existent_id} not found"):
        update_customer_info(non_existent_id, first_name="Ghost")

```
