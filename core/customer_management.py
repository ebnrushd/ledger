import sys
import os
# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import execute_query, get_db_connection # execute_query might be deprecated for functions taking 'conn'

class CustomerNotFoundError(Exception):
    """Custom exception for when a customer is not found."""
    pass

def add_customer(first_name, last_name, email, phone_number=None, address=None, conn=None):
    """
    Adds a new customer to the customers table.
    If `conn` is provided, uses it; otherwise, manages its own connection.
    """
    query = """
        INSERT INTO customers (first_name, last_name, email, phone_number, address, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        RETURNING customer_id;
    """
    params = (first_name, last_name, email, phone_number, address)

    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection()
        _conn_needs_managing = True
        conn.autocommit = False # Manage transaction explicitly

    try:
        with conn.cursor() as cur:
            # Check for duplicate email first using the same connection
            cur.execute("SELECT customer_id FROM customers WHERE email = %s;", (email,))
            if cur.fetchone():
                raise ValueError(f"Customer with email {email} already exists.")

            cur.execute(query, params)
            customer_id = cur.fetchone()[0]

        if _conn_needs_managing:
            conn.commit()

        print(f"Customer {first_name} {last_name} added with ID: {customer_id}.")
        return customer_id
    except ValueError: # Duplicate email
        if _conn_needs_managing and conn and not conn.closed: conn.rollback()
        raise
    except Exception as e:
        if _conn_needs_managing and conn and not conn.closed: conn.rollback()
        print(f"Error adding customer {email}: {e}")
        # Consider raising a more specific error if possible, e.g., from psycopg2.Error
        raise RuntimeError(f"Failed to add customer {email}: {e}") # Generic runtime for other DB errors
    finally:
        if _conn_needs_managing and conn and not conn.closed:
            conn.close()

def get_customer_by_id(customer_id, conn=None):
    """Retrieves customer details by customer_id. Uses provided conn or manages its own."""
    query = "SELECT customer_id, first_name, last_name, email, phone_number, address, created_at FROM customers WHERE customer_id = %s;"
    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection()
        _conn_needs_managing = True

    try:
        with conn.cursor() as cur:
            cur.execute(query, (customer_id,))
            result = cur.fetchone()

        if result:
            return {
                "customer_id": result[0], "first_name": result[1], "last_name": result[2],
                "email": result[3], "phone_number": result[4], "address": result[5],
                "created_at": result[6]
            }
        raise CustomerNotFoundError(f"Customer with ID {customer_id} not found.")
    except CustomerNotFoundError:
        raise
    except Exception as e:
        print(f"Error retrieving customer by ID {customer_id}: {e}")
        raise RuntimeError(f"Failed to retrieve customer by ID {customer_id}: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed:
            conn.close()

def get_customer_by_email(email, conn=None):
    """Retrieves customer details by email. Uses provided conn or manages its own."""
    query = "SELECT customer_id, first_name, last_name, email, phone_number, address, created_at FROM customers WHERE email = %s;"
    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection()
        _conn_needs_managing = True

    try:
        with conn.cursor() as cur:
            cur.execute(query, (email,))
            result = cur.fetchone()

        if result:
            return {
                "customer_id": result[0], "first_name": result[1], "last_name": result[2],
                "email": result[3], "phone_number": result[4], "address": result[5],
                "created_at": result[6]
            }
        raise CustomerNotFoundError(f"Customer with email {email} not found.")
    except CustomerNotFoundError:
        raise
    except Exception as e:
        print(f"Error retrieving customer by email {email}: {e}")
        raise RuntimeError(f"Failed to retrieve customer by email {email}: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed:
            conn.close()


def update_customer_info(customer_id, conn=None, **update_data):
    """
    Updates customer information for a given customer_id using provided fields.
    If `conn` is provided, uses it; otherwise, manages its own connection.
    Returns True if update was successful, False if no fields to update or other non-exception failure.
    """
    # Ensure customer exists first using the same connection context
    try:
        get_customer_by_id(customer_id, conn=conn)
    except CustomerNotFoundError:
        raise # Re-raise if customer not found

    fields_to_update = []
    params = []

    for key, value in update_data.items():
        if key in ["first_name", "last_name", "email", "phone_number", "address"]:
            fields_to_update.append(f"{key} = %s")
            params.append(value)

    if not fields_to_update:
        print("No valid fields provided for customer update.")
        return False

    query = f"UPDATE customers SET {', '.join(fields_to_update)} WHERE customer_id = %s RETURNING customer_id;"
    params.append(customer_id)

    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection()
        _conn_needs_managing = True
        conn.autocommit = False

    try:
        # Check for email conflict if email is being updated
        if "email" in update_data:
            email_to_update = update_data["email"]
            with conn.cursor() as cur_check:
                cur_check.execute("SELECT customer_id FROM customers WHERE email = %s AND customer_id != %s;", (email_to_update, customer_id))
                if cur_check.fetchone():
                    raise ValueError(f"Cannot update: email {email_to_update} already exists for another customer.")

        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            updated_id_tuple = cur.fetchone()

        if not updated_id_tuple:
            # This might happen if customer_id was valid at get_customer_by_id check but deleted before UPDATE (race condition)
            # Or if RETURNING clause behaves unexpectedly with no actual row change (though SET should always change something if fields are valid)
            raise RuntimeError(f"Customer update for ID {customer_id} did not return an ID, possibly no row updated.")

        if _conn_needs_managing:
            conn.commit()

        print(f"Customer ID {updated_id_tuple[0]} updated successfully.")
        return True

    except ValueError: # Duplicate email
        if _conn_needs_managing and conn and not conn.closed: conn.rollback()
        raise
    except Exception as e:
        if _conn_needs_managing and conn and not conn.closed: conn.rollback()
        print(f"Error updating customer {customer_id}: {e}")
        raise RuntimeError(f"Failed to update customer {customer_id}: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed:
            conn.close()

def list_customers(page=1, per_page=20, search_query=None, conn=None):
    """
    Lists customers with pagination and optional search.
    Uses provided conn or manages its own.
    """
    offset = (page - 1) * per_page
    base_query_fields = "customer_id, first_name, last_name, email, phone_number, address, created_at"

    count_query_base = "SELECT COUNT(*) FROM customers"
    list_query_base = f"SELECT {base_query_fields} FROM customers"

    conditions = []
    params_where = [] # Params for WHERE clause (used in both count and list)

    if search_query:
        search_term = f"%{search_query}%"
        # Check if search_query could be an ID
        id_search_param = None
        if search_query.isdigit():
            id_search_param = int(search_query)
            conditions.append("(first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s OR customer_id = %s)")
            params_where.extend([search_term, search_term, search_term, id_search_param])
        else:
            conditions.append("(first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s)")
            params_where.extend([search_term, search_term, search_term])


    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        count_query_base += where_clause
        list_query_base += where_clause

    list_query_base += " ORDER BY customer_id DESC LIMIT %s OFFSET %s;"

    list_params = params_where + [per_page, offset] # Params for the final list query

    _conn_needs_managing = False
    if conn is None:
        conn = get_db_connection()
        _conn_needs_managing = True

    customers_list_of_dicts = []
    total_customers = 0
    try:
        with conn.cursor() as cur:
            cur.execute(count_query_base, tuple(params_where))
            total_customers = cur.fetchone()[0]

            cur.execute(list_query_base, tuple(list_params))
            records = cur.fetchall()

            colnames = [desc[0] for desc in cur.description]
            for record_tuple in records:
                customers_list_of_dicts.append(dict(zip(colnames, record_tuple)))

        return {"customers": customers_list_of_dicts, "total_customers": total_customers, "page": page, "per_page": per_page}
    except Exception as e:
        # Using RuntimeError for general DB errors from these service functions for now
        raise RuntimeError(f"Error listing customers: {e}")
    finally:
        if _conn_needs_managing and conn and not conn.closed:
            conn.close()


if __name__ == '__main__':
    print("Running customer_management.py direct tests...")
    # Note: These tests require a running PostgreSQL database with the schema applied.
    # And environment variables for DB connection set (DB_NAME, DB_USER, DB_PASSWORD etc.)

    # Simplified test structure for direct run, pytest provides better fixtures and isolation.
    test_email_main = "direct.run.test@example.com"
    test_cust_id = None

    def _cleanup_direct_test_customer(email_to_clean):
        conn_clean = None
        try:
            conn_clean = get_db_connection()
            with conn_clean.cursor() as cur_clean:
                # First, find customer_id if exists by email
                cur_clean.execute("SELECT customer_id FROM customers WHERE email = %s;", (email_to_clean,))
                res = cur_clean.fetchone()
                if res:
                    cust_id_to_del = res[0]
                    # Delete associated data from other tables if necessary (e.g., accounts, then users if linked)
                    # For now, just customer. This might fail if FKs exist and are restrictive.
                    print(f"   Cleaning up customer ID {cust_id_to_del} with email {email_to_clean}")
                    cur_clean.execute("DELETE FROM customers WHERE customer_id = %s;", (cust_id_to_del,))
                    conn_clean.commit()
        except Exception as e_cl:
            print(f"   Error during direct test cleanup: {e_cl}")
        finally:
            if conn_clean: conn_clean.close()

    _cleanup_direct_test_customer(test_email_main) # Clean before starting

    try:
        print("\n1. Attempting to add a new customer...")
        test_cust_id = add_customer("John_Direct", "Doe_Direct", test_email_main, "123-456-7890", "123 Main St Direct")
        assert test_cust_id, "Failed to add customer."
        print(f"   Successfully added customer John_Direct Doe_Direct with ID: {test_cust_id}")

        print("\n2. Attempting to retrieve customer by ID...")
        customer = get_customer_by_id(test_cust_id)
        assert customer and customer['first_name'] == "John_Direct", "Failed to retrieve or match customer by ID."
        print(f"   Successfully retrieved: {customer['first_name']} {customer['last_name']}")

        print("\n3. Listing customers (expecting at least one)...")
        customer_list_data = list_customers(search_query=test_email_main)
        assert customer_list_data["total_customers"] >= 1
        assert any(c['customer_id'] == test_cust_id for c in customer_list_data['customers'])
        print(f"   Found customer in list. Total matching: {customer_list_data['total_customers']}")

        print("\n4. Attempting to update customer info...")
        update_success = update_customer_info(test_cust_id, phone_number="987-654-0000", address="456 New Ave Direct")
        assert update_success, "Update customer info failed."
        updated_customer = get_customer_by_id(test_cust_id)
        assert updated_customer['phone_number'] == "987-654-0000", "Phone number not updated."
        print(f"   Successfully updated. New phone: {updated_customer['phone_number']}")

    except (CustomerNotFoundError, ValueError, RuntimeError) as e:
        print(f"   Error during direct tests: {e}")
    except Exception as e_unhandled:
        print(f"   Unexpected error during direct tests: {e_unhandled}")
        import traceback
        traceback.print_exc()
    finally:
        _cleanup_direct_test_customer(test_email_main) # Clean after tests

    print("\nCustomer_management.py direct tests finished.")

```
