-- Database schema for SQL Ledger

-- Customers table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    address VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Account status types table
CREATE TABLE account_status_types (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) UNIQUE NOT NULL -- e.g., active, frozen, closed
);

-- Default account statuses
INSERT INTO account_status_types (status_name) VALUES ('active'), ('frozen'), ('closed');

-- Accounts table
CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    account_type VARCHAR(50) NOT NULL, -- e.g., checking, savings
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD', -- ISO 4217 currency code
    status_id INT NOT NULL,
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_customer
        FOREIGN KEY(customer_id)
        REFERENCES customers(customer_id),
    CONSTRAINT fk_status
        FOREIGN KEY(status_id)
        REFERENCES account_status_types(status_id)
);

-- Transaction types table
CREATE TABLE transaction_types (
    transaction_type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) UNIQUE NOT NULL -- e.g., deposit, withdrawal, transfer, ACH, wire
);

-- Default transaction types
INSERT INTO transaction_types (type_name) VALUES ('deposit'), ('withdrawal'), ('transfer'), ('ach_credit'), ('ach_debit'), ('wire_transfer');

-- Transactions table
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id INT NOT NULL,
    transaction_type_id INT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    transaction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    related_account_id INT, -- For transfers, this would be the other account involved
    CONSTRAINT fk_account
        FOREIGN KEY(account_id)
        REFERENCES accounts(account_id),
    CONSTRAINT fk_transaction_type
        FOREIGN KEY(transaction_type_id)
        REFERENCES transaction_types(transaction_type_id),
    CONSTRAINT fk_related_account
        FOREIGN KEY(related_account_id)
        REFERENCES accounts(account_id) -- Self-referencing for transfers
);

-- Indexes for performance optimization
CREATE INDEX idx_customer_email ON customers(email);
CREATE INDEX idx_account_number ON accounts(account_number);
CREATE INDEX idx_account_customer_id ON accounts(customer_id);
CREATE INDEX idx_transaction_account_id ON transactions(account_id);
CREATE INDEX idx_transaction_timestamp ON transactions(transaction_timestamp);
CREATE INDEX idx_transaction_type_id ON transactions(transaction_type_id);

-- Function to update updated_at timestamp on account update
CREATE OR REPLACE FUNCTION update_account_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_account_updated_at
BEFORE UPDATE ON accounts
FOR EACH ROW
EXECUTE FUNCTION update_account_updated_at();

-- End of schema
