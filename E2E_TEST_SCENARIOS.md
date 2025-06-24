# End-to-End Test Scenarios (Conceptual)

This document outlines key end-to-end test scenarios for the SQL Ledger system. These are conceptual flows to verify major functionalities.

## Scenario 1: Customer Registration & First Login & Account Status Check

1.  **Action:** New user navigates to the customer frontend registration page.
2.  **Action:** User fills out registration form (first name, last name, email, password, phone, address) and submits.
3.  **Expected Backend:**
    *   A new user record is created in the `users` table.
    *   A new customer record is created in the `customers` table, linked to the user.
    *   A new account (e.g., 'savings') is created in the `accounts` table for this customer.
    *   This new account has its `status_id` set to 'pending_approval'.
4.  **Expected Frontend:**
    *   User sees a registration success message.
    *   User navigates to the login page.
    *   User logs in with the new credentials.
    *   Login is successful, JWT token is received and stored.
    *   User is redirected to their dashboard.
    *   Dashboard displays the newly created account with a status clearly indicating "Pending Approval" (or similar).
    *   User should NOT be able to perform transactions on this pending account.

## Scenario 2: Admin Account Approval

1.  **Action:** Admin user logs into the admin panel (`/admin/login`).
2.  **Expected Frontend (Admin):**
    *   Admin is redirected to the admin dashboard.
    *   Admin navigates to "Pending Approvals" (or similar link in sidebar).
3.  **Action:** Admin sees the list of accounts pending approval, including the one created in Scenario 1.
4.  **Action:** Admin clicks "Approve" for that account.
5.  **Expected Backend:**
    *   The account's `status_id` in the `accounts` table is updated to 'active'.
    *   An audit log entry is created for the account approval event.
6.  **Expected Frontend (Admin):**
    *   The account is removed from the "Pending Approvals" list.
    *   A success message is shown.
7.  **Action (Customer):** Customer logs out and logs back into the customer portal.
8.  **Expected Frontend (Customer):**
    *   Dashboard now shows the account with "Active" status.
    *   User should now be able to (conceptually) perform transactions if other conditions allow (e.g., positive balance for withdrawals).

## Scenario 3: Customer Inter-Account Transfer (After Account Approval)

1.  **Prerequisite:** Customer from Scenario 1 & 2 has at least two 'active' accounts. If only one, admin may need to create and activate a second one manually or through an admin UI for testing this. Assume two active accounts exist.
2.  **Action (Customer):** Customer navigates to the "Transfer Funds" page.
3.  **Action:** Customer selects a 'from' account, a 'to' account, enters an amount (ensure 'from' account has sufficient balance), and submits.
4.  **Expected Backend:**
    *   Two transaction records are created in the `transactions` table (a debit from source, a credit to destination).
    *   Balances of both accounts in the `accounts` table are updated accordingly.
    *   Audit log entries are created for both transactions.
5.  **Expected Frontend (Customer):**
    *   Success message for the transfer.
    *   Relevant account balances displayed on the dashboard are updated (may require a refresh or auto-update mechanism).
    *   Transaction history for both accounts shows the transfer.

## Scenario 4: Admin User Management (Teller Creation)

1.  **Action (Admin):** Admin navigates to "User Management" in the admin panel.
2.  **Action:** Admin clicks "Add New User".
3.  **Action:** Admin fills out the form for a new user, selecting the 'teller' role, and submits.
4.  **Expected Backend:**
    *   A new user record is created in the `users` table with the 'teller' role_id and `is_active=true`. No customer record is necessarily linked unless specified.
    *   Audit log entry for user creation.
5.  **Expected Frontend (Admin):**
    *   Success message. New teller user appears in the user list.
6.  **Action (New Teller):** New teller user attempts to log into the admin panel (`/admin/login`).
7.  **Expected Frontend (Admin - Teller Session):**
    *   Login is successful.
    *   Teller is redirected to the admin dashboard.
    *   Teller should only see navigation links and be able to access sections permitted for the 'teller' role (this depends on how Role-Based Access Control (RBAC) is enforced on API endpoints and conditionally rendered in UI). For example, a teller might not see "User Management" or "Settings" but might see "Transaction Lookup" or "Customer Profiles".

## Scenario 5: CLI Tool Usage

1.  **Action (Admin - Server Side):**
    *   Navigate to `config-cli/` directory.
    *   Run `python main.py set TEST_KEY "test_value" --file ../.env` (assuming backend `.env` is at project root).
2.  **Expected:**
    *   `.env` file at project root is updated with `TEST_KEY="test_value"`. An old version is saved as `.env.bak`.
3.  **Action (Admin - Server Side):**
    *   Run `python main.py get TEST_KEY --file ../.env`.
4.  **Expected:** Output `TEST_KEY=test_value`.
5.  **Action (Admin - Server Side):**
    *   Run `python main.py delete TEST_KEY --force --file ../.env`.
6.  **Expected:** `TEST_KEY` is removed from `.env`.
7.  **Action (Admin - Server Side):** Restart the backend FastAPI application.
8.  **Expected:** If `TEST_KEY` was a configuration the backend uses, its behavior might change or it might now use a default if the key is missing. (This part depends on how the backend consumes specific env vars).

## Scenario 6: Access Control

1.  **Unauthenticated User - Customer Frontend:**
    *   **Action:** Attempt to access `/dashboard` (requires auth).
    *   **Expected:** Redirected to `/login`.
2.  **Unauthenticated User - Admin Panel:**
    *   **Action:** Attempt to access `/admin/dashboard` (requires auth).
    *   **Expected:** Redirected to `/admin/login`.
3.  **Authenticated Customer - Admin Panel Access:**
    *   **Action:** Customer user (logged into customer portal) attempts to access `/admin/dashboard`.
    *   **Expected:** Redirected to `/admin/login` because they don't have an admin session.
4.  **Authenticated Admin - Customer Portal Access:**
    *   **Action:** Admin user (logged into admin panel) attempts to access `/dashboard` (customer portal).
    *   **Expected:** If `/dashboard` is public or they also have a customer account and are logged in separately, access is granted. If `/dashboard` requires customer login and admin is not also logged in as a customer, they should be redirected to customer `/login`. (This tests session/token separation).
5.  **Role-Based Access (Conceptual - Admin Panel):**
    *   **Action:** A 'teller' user (created in Scenario 4) attempts to access an admin-only section like "User Management" (assuming direct URL navigation if link is hidden).
    *   **Expected:** Access denied (e.g., 403 Forbidden error page, or redirect to admin dashboard with an error message). This relies on backend API endpoint protection for the data and frontend UI selectively rendering navigation/controls.

These scenarios provide a broad overview of system functionality and interaction between different components and user roles.
```
