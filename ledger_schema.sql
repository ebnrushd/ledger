CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL  -- e.g., 'asset', 'liability', 'equity', 'revenue', 'expense'
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    description TEXT
);

CREATE TABLE ledger_entries (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE RESTRICT,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    type TEXT NOT NULL CHECK (type IN ('debit', 'credit')),
    amount NUMERIC NOT NULL CHECK (amount >= 0)
);

CREATE INDEX ON ledger_entries (account_id);
CREATE INDEX ON ledger_entries (transaction_id);

CREATE TYPE account_entry AS (
    account_id INTEGER,
    type TEXT,
    amount NUMERIC
);

CREATE OR REPLACE FUNCTION create_transaction(
    p_description TEXT,
    p_entries account_entry[]
) RETURNS INTEGER AS $$
DECLARE
    v_trans_id INTEGER;
    v_total_debit NUMERIC := 0;
    v_total_credit NUMERIC := 0;
    v_entry account_entry;
BEGIN
    -- Insert the transaction
    INSERT INTO transactions (description) VALUES (p_description) RETURNING id INTO v_trans_id;

    -- Loop over entries
    FOREACH v_entry IN ARRAY p_entries
    LOOP
        -- Validate the type
        IF v_entry.type NOT IN ('debit', 'credit') THEN
            RAISE EXCEPTION 'Invalid entry type: % for account_id %', v_entry.type, v_entry.account_id;
        END IF;

        IF v_entry.amount < 0 THEN
            RAISE EXCEPTION 'Entry amount cannot be negative: % for account_id %', v_entry.amount, v_entry.account_id;
        END IF;

        INSERT INTO ledger_entries (transaction_id, account_id, type, amount)
        VALUES (v_trans_id, v_entry.account_id, v_entry.type, v_entry.amount);

        IF v_entry.type = 'debit' THEN
            v_total_debit := v_total_debit + v_entry.amount;
        ELSE
            v_total_credit := v_total_credit + v_entry.amount;
        END IF;
    END LOOP;

    -- Check if the transaction balances
    IF v_total_debit <> v_total_credit THEN
        RAISE EXCEPTION 'Transaction % does not balance: debit total = %, credit total = %', v_trans_id, v_total_debit, v_total_credit;
    END IF;

    RETURN v_trans_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION prevent_updates()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Updates are not allowed on this table';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION prevent_deletes()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Deletes are not allowed on this table';
END;
$$ LANGUAGE plpgsql;

-- Attach to transactions
CREATE TRIGGER transactions_prevent_update
BEFORE UPDATE ON transactions
FOR EACH ROW EXECUTE FUNCTION prevent_updates();

CREATE TRIGGER transactions_prevent_delete
BEFORE DELETE ON transactions
FOR EACH ROW EXECUTE FUNCTION prevent_deletes();

-- Attach to ledger_entries
CREATE TRIGGER ledger_entries_prevent_update
BEFORE UPDATE ON ledger_entries
FOR EACH ROW EXECUTE FUNCTION prevent_updates();

CREATE TRIGGER ledger_entries_prevent_delete
BEFORE DELETE ON ledger_entries
FOR EACH ROW EXECUTE FUNCTION prevent_deletes();

-- Table for money box serials
CREATE TABLE money_box_serials (
    serial_number TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'VALID' CHECK (status IN ('VALID', 'INVALID')),
    imported_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add columns to transactions table for money box serial and Oracle reference
ALTER TABLE transactions
ADD COLUMN money_box_serial_used TEXT NULL,
ADD COLUMN oracle_transaction_ref TEXT NULL;

-- Indexes for new columns/tables
CREATE INDEX ON money_box_serials (status);
CREATE INDEX ON transactions (money_box_serial_used);

-- Updated function to create a transaction with money box serial and Oracle reference
CREATE OR REPLACE FUNCTION create_transaction(
    p_description TEXT,
    p_entries account_entry[],
    p_money_box_serial_used TEXT DEFAULT NULL,
    p_oracle_transaction_ref TEXT DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_trans_id INTEGER;
    v_total_debit NUMERIC := 0;
    v_total_credit NUMERIC := 0;
    v_entry account_entry;
BEGIN
    -- Insert the transaction, including new optional fields
    INSERT INTO transactions (description, money_box_serial_used, oracle_transaction_ref)
    VALUES (p_description, p_money_box_serial_used, p_oracle_transaction_ref)
    RETURNING id INTO v_trans_id;

    -- Loop over entries
    FOREACH v_entry IN ARRAY p_entries
    LOOP
        -- Validate the type
        IF v_entry.type NOT IN ('debit', 'credit') THEN
            RAISE EXCEPTION 'Invalid entry type: % for account_id %', v_entry.type, v_entry.account_id;
        END IF;

        IF v_entry.amount < 0 THEN
            RAISE EXCEPTION 'Entry amount cannot be negative: % for account_id %', v_entry.amount, v_entry.account_id;
        END IF;

        INSERT INTO ledger_entries (transaction_id, account_id, type, amount)
        VALUES (v_trans_id, v_entry.account_id, v_entry.type, v_entry.amount);

        IF v_entry.type = 'debit' THEN
            v_total_debit := v_total_debit + v_entry.amount;
        ELSE
            v_total_credit := v_total_credit + v_entry.amount;
        END IF;
    END LOOP;

    -- Check if the transaction balances
    IF v_total_debit <> v_total_credit THEN
        RAISE EXCEPTION 'Transaction % does not balance: debit total = %, credit total = %', v_trans_id, v_total_debit, v_total_credit;
    END IF;

    RETURN v_trans_id;
END;
$$ LANGUAGE plpgsql;
