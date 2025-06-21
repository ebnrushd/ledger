-- SQL Ledger - Additional Features Schema Updates

-- 1. Overdraft Protection: Add overdraft_limit to accounts table
ALTER TABLE accounts
ADD COLUMN overdraft_limit DECIMAL(15, 2) DEFAULT 0.00;

-- Update existing accounts to have a zero overdraft limit explicitly (optional, depends on desired default behavior for old records)
-- UPDATE accounts SET overdraft_limit = 0.00 WHERE overdraft_limit IS NULL;


-- 3. Fee Calculations and Processing: fee_types table
CREATE TABLE fee_types (
    fee_type_id SERIAL PRIMARY KEY,
    fee_name VARCHAR(100) UNIQUE NOT NULL, -- e.g., 'overdraft_fee', 'monthly_maintenance', 'low_balance_fee'
    default_amount DECIMAL(10, 2) NOT NULL,
    description TEXT
);

-- Example fee types
INSERT INTO fee_types (fee_name, default_amount, description) VALUES
    ('overdraft_usage_fee', 25.00, 'Fee applied when overdraft limit is utilized.'),
    ('monthly_maintenance_fee', 5.00, 'Standard monthly account maintenance fee.'),
    ('low_balance_fee', 10.00, 'Fee applied if account balance drops below a certain threshold (logic external to this table).'),
    ('wire_transfer_fee_outgoing', 15.00, 'Fee for processing an outgoing wire transfer.'),
    ('wire_transfer_fee_incoming', 10.00, 'Fee for receiving an incoming wire transfer.');


-- 4. Currency Conversion for International Transactions: exchange_rates table
CREATE TABLE exchange_rates (
    rate_id SERIAL PRIMARY KEY,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    rate DECIMAL(18, 8) NOT NULL, -- Rate to convert 1 unit of from_currency to to_currency
    effective_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(255), -- e.g., 'CentralBankAPI', 'ManualEntry'
    CONSTRAINT uq_exchange_rate_period UNIQUE (from_currency, to_currency, effective_timestamp)
);

CREATE INDEX idx_exchange_rates_from_to_currency ON exchange_rates(from_currency, to_currency);
CREATE INDEX idx_exchange_rates_effective_timestamp ON exchange_rates(effective_timestamp DESC);

-- Example exchange rates (these would be updated regularly)
INSERT INTO exchange_rates (from_currency, to_currency, rate, source) VALUES
    ('USD', 'EUR', 0.92, 'ExampleSource'),
    ('EUR', 'USD', 1.08, 'ExampleSource'),
    ('USD', 'GBP', 0.79, 'ExampleSource'),
    ('GBP', 'USD', 1.26, 'ExampleSource'),
    ('USD', 'JPY', 150.50, 'ExampleSource'),
    ('JPY', 'USD', 0.00664, 'ExampleSource');


-- 5. Automated Reconciliation Processes: external_transaction_sources and external_transactions tables
CREATE TABLE external_transaction_sources (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'External Bank ABC', 'Payment Processor XYZ', 'ATM Network'
    contact_details TEXT
);

-- Example sources
INSERT INTO external_transaction_sources (source_name, contact_details) VALUES
    ('PaymentProcessorXYZ', 'support@xyzpayments.com'),
    ('ExternalBankABC', 'ops@bankabc.com'),
    ('InternalCashGL', 'Finance Department - General Ledger for Cash Operations');

CREATE TABLE external_transactions (
    ext_transaction_id SERIAL PRIMARY KEY,
    source_id INT NOT NULL,
    reference_id VARCHAR(255), -- Unique ID from the external source for this transaction
    transaction_date DATE NOT NULL,
    posting_date DATE, -- Date it was posted to our system, if different
    amount DECIMAL(15, 2) NOT NULL, -- Positive for credits, negative for debits from the source's perspective
    currency VARCHAR(3) NOT NULL,
    description TEXT,
    memo TEXT, -- Additional unstructured information from source
    status VARCHAR(50) DEFAULT 'pending_match', -- e.g., 'pending_match', 'matched', 'discrepancy', 'ignored'
    ledger_transaction_id INT, -- If matched, FK to our internal transactions table
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ext_source
        FOREIGN KEY(source_id)
        REFERENCES external_transaction_sources(source_id),
    CONSTRAINT fk_ledger_transaction -- Optional: if directly linking
        FOREIGN KEY(ledger_transaction_id)
        REFERENCES transactions(transaction_id)
        ON DELETE SET NULL,
    UNIQUE (source_id, reference_id) -- Ensure unique transactions per source
);

CREATE INDEX idx_ext_transactions_source_ref ON external_transactions(source_id, reference_id);
CREATE INDEX idx_ext_transactions_date ON external_transactions(transaction_date);
CREATE INDEX idx_ext_transactions_status ON external_transactions(status);

-- Function to update updated_at timestamp on external_transactions update
CREATE OR REPLACE FUNCTION update_external_transactions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_external_transactions_updated_at
BEFORE UPDATE ON external_transactions
FOR EACH ROW
EXECUTE FUNCTION update_external_transactions_updated_at();

-- End of schema updates
```
