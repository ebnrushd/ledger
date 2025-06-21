-- User and Role-Based Access Control (RBAC) Schema

-- Roles table
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL -- e.g., 'customer', 'teller', 'admin', 'auditor'
);

-- Default roles (examples)
INSERT INTO roles (role_name) VALUES ('customer'), ('teller'), ('admin'), ('auditor'), ('system_process');

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Store securely hashed passwords (e.g., bcrypt, scrypt, Argon2)
    role_id INT NOT NULL,
    customer_id INT UNIQUE, -- Nullable, links user to a customer profile if applicable. UNIQUE ensures one user per customer.
    email VARCHAR(100) UNIQUE NOT NULL, -- User's email for notifications, password resets, etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_role
        FOREIGN KEY(role_id)
        REFERENCES roles(role_id),
    CONSTRAINT fk_customer_profile
        FOREIGN KEY(customer_id)
        REFERENCES customers(customer_id)
        ON DELETE SET NULL -- If customer profile is deleted, user remains but link is severed.
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role_id ON users(role_id);

-- Permissions table (defines granular actions)
CREATE TABLE permissions (
    permission_id SERIAL PRIMARY KEY,
    permission_name VARCHAR(100) UNIQUE NOT NULL, -- e.g., 'VIEW_OWN_ACCOUNT_DETAILS', 'PERFORM_TRANSFER', 'MANAGE_USERS'
    description TEXT
);

-- Example permissions
INSERT INTO permissions (permission_name, description) VALUES
    ('VIEW_OWN_ACCOUNT_DETAILS', 'Allows viewing details of own linked accounts.'),
    ('VIEW_OWN_TRANSACTIONS', 'Allows viewing own transaction history.'),
    ('PERFORM_DEPOSIT_OWN_ACCOUNT', 'Allows depositing into own accounts.'),
    ('PERFORM_WITHDRAWAL_OWN_ACCOUNT', 'Allows withdrawing from own accounts.'),
    ('PERFORM_TRANSFER_OWN_ACCOUNTS', 'Allows transferring between own accounts.'),
    ('VIEW_CUSTOMER_DETAILS', 'Allows viewing customer PII and account list (for tellers/admins).'),
    ('OPEN_NEW_ACCOUNT', 'Allows opening a new account for a customer.'),
    ('MODIFY_ACCOUNT_STATUS', 'Allows changing an account status (e.g., freeze/unfreeze).'),
    ('PERFORM_CUSTOMER_TRANSACTION', 'Allows performing transactions on behalf of a customer (teller).'),
    ('VIEW_ALL_TRANSACTIONS', 'Allows viewing transaction history for any account (admin/auditor).'),
    ('VIEW_AUDIT_LOGS', 'Allows viewing the audit log (admin/auditor).'),
    ('MANAGE_USERS', 'Allows creating, updating, and disabling users (admin).'),
    ('MANAGE_ROLES_PERMISSIONS', 'Allows defining roles and assigning permissions (admin).'),
    ('RUN_SYSTEM_REPORTS', 'Allows generating system-wide reports (admin/auditor).'),
    ('EXECUTE_LEDGER_VALIDATION', 'Allows running ledger integrity checks (admin/auditor).');


-- Role_Permissions table (links roles to permissions, many-to-many)
CREATE TABLE role_permissions (
    role_permission_id SERIAL PRIMARY KEY,
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    CONSTRAINT fk_role_assoc
        FOREIGN KEY(role_id)
        REFERENCES roles(role_id)
        ON DELETE CASCADE, -- If role is deleted, its permissions are removed
    CONSTRAINT fk_permission_assoc
        FOREIGN KEY(permission_id)
        REFERENCES permissions(permission_id)
        ON DELETE CASCADE, -- If a permission is deleted, remove it from roles
    UNIQUE (role_id, permission_id) -- Ensure a role doesn't have the same permission multiple times
);

CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);

-- Now, go back to schema_audit.sql and uncomment or add the FK constraint from audit_log.user_id to users.user_id
-- ALTER TABLE audit_log
-- ADD CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE SET NULL;
-- (This step should be done manually or as a separate migration after users table is created)
-- For the purpose of this subtask, the definition of audit_log in schema_audit.sql already has this,
-- assuming users table would be created.

-- Example: Assign some permissions to roles (can be expanded significantly)
-- This would typically be managed by application logic or a setup script.

-- Customer Role Permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id FROM roles r, permissions p
WHERE r.role_name = 'customer' AND p.permission_name IN (
    'VIEW_OWN_ACCOUNT_DETAILS',
    'VIEW_OWN_TRANSACTIONS',
    'PERFORM_DEPOSIT_OWN_ACCOUNT',
    'PERFORM_WITHDRAWAL_OWN_ACCOUNT',
    'PERFORM_TRANSFER_OWN_ACCOUNTS'
);

-- Teller Role Permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id FROM roles r, permissions p
WHERE r.role_name = 'teller' AND p.permission_name IN (
    'VIEW_CUSTOMER_DETAILS',
    'PERFORM_CUSTOMER_TRANSACTION', -- This is broad, could be broken down further
    'OPEN_NEW_ACCOUNT',
    'MODIFY_ACCOUNT_STATUS', -- e.g. freeze, but maybe not close
    'VIEW_OWN_TRANSACTIONS' -- For their operational till if applicable, or just general access
);

-- Admin Role Permissions (gets almost all)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id FROM roles r, permissions p
WHERE r.role_name = 'admin'; -- Simplification: Admin gets all defined permissions.
-- A more granular setup would list them explicitly.

-- Auditor Role Permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id FROM roles r, permissions p
WHERE r.role_name = 'auditor' AND p.permission_name IN (
    'VIEW_ALL_TRANSACTIONS',
    'VIEW_AUDIT_LOGS',
    'RUN_SYSTEM_REPORTS',
    'EXECUTE_LEDGER_VALIDATION',
    'VIEW_CUSTOMER_DETAILS' -- Read-only access to customer info typically
);

-- Note: The 'system_process' role might have specific permissions for automated tasks,
-- for example, if interest calculation was an automated user process:
-- INSERT INTO role_permissions (role_id, permission_id)
-- SELECT r.role_id, p.permission_id FROM roles r, permissions p
-- WHERE r.role_name = 'system_process' AND p.permission_name = 'POST_INTEREST_TRANSACTIONS'; (assuming such a perm exists)

```
