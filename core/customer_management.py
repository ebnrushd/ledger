import sys
import os
# Add project root to sys.path to allow importing 'database'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import execute_query

class CustomerNotFoundError(Exception):
    """Custom exception for when a customer is not found."""
    pass

def add_customer(first_name, last_name, email, phone_number=None, address=None):
    """
    Adds a new customer to the customers table.

    Args:
        first_name (str): Customer's first name.
        last_name (str): Customer's last name.
        email (str): Customer's email address (must be unique).
        phone_number (str, optional): Customer's phone number. Defaults to None.
        address (str, optional): Customer's physical address. Defaults to None.

    Returns:
        int: The customer_id of the newly created customer, or None if creation failed.
    """
    query = """
        INSERT INTO customers (first_name, last_name, email, phone_number, address)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING customer_id;
    """
    params = (first_name, last_name, email, phone_number, address)
    try:
        result = execute_query(query, params, fetch_one=True, commit=True)
        if result:
            print(f"Customer {first_name} {last_name} added with ID: {result[0]}.")
            return result[0]
        return None
    except Exception as e:
        # Specific error handling for duplicate email could be added here by checking e.pgcode
        print(f"Error adding customer {email}: {e}")
        if 'unique constraint "customers_email_key"' in str(e).lower():
             raise ValueError(f"Customer with email {email} already exists.")
        raise # Re-raise for other types of errors

def get_customer_by_id(customer_id):
    """
    Retrieves customer details by customer_id.

    Args:
        customer_id (int): The ID of the customer to retrieve.

    Returns:
        dict: A dictionary containing customer details, or None if not found.
    """
    query = "SELECT customer_id, first_name, last_name, email, phone_number, address, created_at FROM customers WHERE customer_id = %s;"
    params = (customer_id,)
    try:
        result = execute_query(query, params, fetch_one=True)
        if result:
            return {
                "customer_id": result[0],
                "first_name": result[1],
                "last_name": result[2],
                "email": result[3],
                "phone_number": result[4],
                "address": result[5],
                "created_at": result[6]
            }
        raise CustomerNotFoundError(f"Customer with ID {customer_id} not found.")
    except Exception as e:
        print(f"Error retrieving customer by ID {customer_id}: {e}")
        raise

def get_customer_by_email(email):
    """
    Retrieves customer details by email.

    Args:
        email (str): The email of the customer to retrieve.

    Returns:
        dict: A dictionary containing customer details, or None if not found.
    """
    query = "SELECT customer_id, first_name, last_name, email, phone_number, address, created_at FROM customers WHERE email = %s;"
    params = (email,)
    try:
        result = execute_query(query, params, fetch_one=True)
        if result:
            return {
                "customer_id": result[0],
                "first_name": result[1],
                "last_name": result[2],
                "email": result[3],
                "phone_number": result[4],
                "address": result[5],
                "created_at": result[6]
            }
        raise CustomerNotFoundError(f"Customer with email {email} not found.")
    except Exception as e:
        print(f"Error retrieving customer by email {email}: {e}")
        raise

def update_customer_info(customer_id, first_name=None, last_name=None, email=None, phone_number=None, address=None):
    """
    Updates customer information for a given customer_id.
    Only fields that are not None will be updated.

    Args:
        customer_id (int): The ID of the customer to update.
        first_name (str, optional): New first name.
        last_name (str, optional): New last name.
        email (str, optional): New email.
        phone_number (str, optional): New phone number.
        address (str, optional): New address.

    Returns:
        bool: True if update was successful, False otherwise.
    """
    # First, check if customer exists
    customer = get_customer_by_id(customer_id) # This will raise CustomerNotFoundError if not found

    fields_to_update = []
    params = []

    if first_name is not None:
        fields_to_update.append("first_name = %s")
        params.append(first_name)
    if last_name is not None:
        fields_to_update.append("last_name = %s")
        params.append(last_name)
    if email is not None:
        fields_to_update.append("email = %s")
        params.append(email)
    if phone_number is not None:
        fields_to_update.append("phone_number = %s")
        params.append(phone_number)
    if address is not None:
        fields_to_update.append("address = %s")
        params.append(address)

    if not fields_to_update:
        print("No fields provided to update.")
        return False

    query = f"UPDATE customers SET {', '.join(fields_to_update)} WHERE customer_id = %s RETURNING customer_id;"
    params.append(customer_id)

    try:
        result = execute_query(query, tuple(params), commit=True, fetch_one=True)
        if result:
            print(f"Customer ID {result[0]} updated successfully.")
            return True
        # This part might not be reached if RETURNING is used and no rows are updated,
        # but get_customer_by_id should prevent that if customer_id is valid.
        # If customer_id was invalid, execute_query would ideally not find a row to update.
        return False
    except Exception as e:
        print(f"Error updating customer {customer_id}: {e}")
        if 'unique constraint "customers_email_key"' in str(e).lower():
             raise ValueError(f"Cannot update: email {email} already exists for another customer.")
        raise

if __name__ == '__main__':
    print("Running customer_management.py direct tests...")
    # Note: These tests require a running PostgreSQL database with the schema applied.
    # And environment variables for DB connection set (DB_NAME, DB_USER, DB_PASSWORD etc.)
    # Example:
    # export DB_NAME="sql_ledger_db"
    # export DB_USER="ledger_user"
    # export DB_PASSWORD="securepassword123"
    #
    # Before running, ensure the DB is clean or manage test data appropriately.
    # For simplicity, these tests might fail if data from previous runs exists (e.g., unique email).

    try:
        print("\n1. Attempting to add a new customer...")
        new_customer_id = add_customer("John", "Doe", "john.doe@example.com", "123-456-7890", "123 Main St")
        if new_customer_id:
            print(f"   Successfully added customer John Doe with ID: {new_customer_id}")

            print("\n2. Attempting to retrieve customer by ID...")
            customer = get_customer_by_id(new_customer_id)
            if customer:
                print(f"   Successfully retrieved: {customer['first_name']} {customer['last_name']}")
            else:
                print(f"   Failed to retrieve customer ID {new_customer_id}")

            print("\n3. Attempting to retrieve customer by email...")
            customer_by_email = get_customer_by_email("john.doe@example.com")
            if customer_by_email:
                print(f"   Successfully retrieved by email: {customer_by_email['first_name']} (ID: {customer_by_email['customer_id']})")
            else:
                print("   Failed to retrieve customer by email john.doe@example.com")

            print("\n4. Attempting to update customer information...")
            updated = update_customer_info(new_customer_id, phone_number="987-654-3210", address="456 New Ave")
            if updated:
                print("   Successfully updated customer info.")
                updated_customer = get_customer_by_id(new_customer_id)
                print(f"   New phone: {updated_customer['phone_number']}, New address: {updated_customer['address']}")
            else:
                print("   Failed to update customer info.")

            print("\n5. Attempting to add a customer with a duplicate email (should fail)...")
            try:
                add_customer("Jane", "Doe", "john.doe@example.com")
            except ValueError as ve:
                print(f"   Successfully caught expected error: {ve}")
            except Exception as e:
                print(f"   Caught unexpected error: {e}")


        else:
            print("   Failed to add customer John Doe.")

        print("\n6. Attempting to retrieve a non-existent customer by ID (should fail)...")
        try:
            get_customer_by_id(999999)
        except CustomerNotFoundError as e:
            print(f"   Successfully caught expected error: {e}")
        except Exception as e:
            print(f"   Caught unexpected error: {e}")

        print("\n7. Attempting to retrieve a non-existent customer by email (should fail)...")
        try:
            get_customer_by_email("noone@example.com")
        except CustomerNotFoundError as e:
            print(f"   Successfully caught expected error: {e}")
        except Exception as e:
            print(f"   Caught unexpected error: {e}")

        print("\n8. Attempting to update a non-existent customer (should fail)...")
        try:
            update_customer_info(88888, first_name="Ghost")
        except CustomerNotFoundError as e:
            print(f"   Successfully caught expected error for non-existent customer: {e}")
        except Exception as e:
            print(f"   Caught unexpected error: {e}")


    except Exception as e:
        print(f"\nAn error occurred during customer_management tests: {e}")
        print("Ensure DB is running, schema.sql is applied, and DB connection details are correct.")
        print("You might need to clean up the 'customers' table if you re-run these tests (e.g., DELETE FROM customers WHERE email = 'john.doe@example.com';)")

    finally:
        # Clean up test data (optional, but good for rerunnability)
        # In a real test suite, you'd use a dedicated test database or transactions and rollbacks.
        print("\nAttempting to clean up test customer john.doe@example.com...")
        try:
            # Need a way to connect and execute a simple delete without using execute_query's error handling for this cleanup
            from database import get_db_connection
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM customers WHERE email = %s;", ("john.doe@example.com",))
            conn.commit()
            print("   Cleanup successful or customer was not present.")
            cur.close()
            conn.close()
        except Exception as e:
            print(f"   Cleanup failed: {e}")
