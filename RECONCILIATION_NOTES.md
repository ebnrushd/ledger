# Automated Reconciliation Process Notes

This document outlines conceptual steps and considerations for an automated reconciliation process within the SQL Ledger system. The goal is to compare transactions recorded in our ledger against external transaction records (e.g., bank statements, payment processor reports) to ensure consistency and identify discrepancies.

The `external_transaction_sources` and `external_transactions` tables defined in `schema_updates.sql` provide the foundation for storing external transaction data.

## Reconciliation Process Steps

1.  **Data Import:**
    *   **Source Configuration:** For each `external_transaction_sources` (e.g., 'External Bank ABC', 'Payment Processor XYZ'), define how to fetch or receive their transaction data. This could be via API, SFTP download of CSV/BAI2/MT940 files, or manual upload.
    *   **Parser Implementation:** Develop parsers for each external data format to transform the data into the structure of the `external_transactions` table.
    *   **Secure Storage:** Store imported raw files securely for audit purposes.
    *   **Loading:** Load parsed external transactions into the `external_transactions` table with an initial status like 'pending_match'.

2.  **Matching Rules Engine:**
    *   Develop a flexible matching engine that attempts to link `external_transactions` with internal `transactions`.
    *   **Matching Criteria (configurable per source or generally):**
        *   **Primary Criteria (strong indicators):**
            *   `Reference ID`: Match `external_transactions.reference_id` with a corresponding field in internal transactions if available (e.g., a payment gateway ID stored in `transactions.description` or a dedicated column).
            *   `Amount + Date (+/- tolerance)`: Match `external_transactions.amount` with `transactions.amount` (signs might need normalization based on perspective) and `external_transactions.transaction_date` with `transactions.transaction_timestamp` (date part). A small date tolerance (e.g., +/- 1-2 days) and amount tolerance (e.g., for minor rounding) might be necessary.
            *   `Account Number / Identifier`: If the external data contains an account identifier that can be mapped to our `accounts.account_number`.
        *   **Secondary Criteria (weaker indicators, used to confirm or narrow down):**
            *   `Description`: Fuzzy matching or keyword matching on transaction descriptions.
            *   `Transaction Type`: Mapping external transaction types to internal `transaction_types.type_name`.
    *   **One-to-One, One-to-Many, Many-to-Many:** The engine should ideally be capable of handling various matching scenarios, though one-to-one is the most common starting point.
    *   **Passes:** Matching might occur in multiple passes, starting with the strictest criteria and gradually becoming more lenient if initial matches are not found.

3.  **Execution and Status Updates:**
    *   Run the matching process (e.g., as a nightly batch job or on-demand).
    *   If a match is found:
        *   Update `external_transactions.status` to 'matched'.
        *   Link to the internal transaction by setting `external_transactions.ledger_transaction_id`.
        *   Optionally, mark the internal `transactions` record as 'reconciled' (might require adding a `reconciliation_status` column to `transactions`).
    *   If no match is found after all passes, `external_transactions.status` might remain 'pending_match' or be moved to 'unmatched'.

4.  **Discrepancy Handling and Reporting:**
    *   **Discrepancy Identification:**
        *   Transactions in our ledger but not in the external statement.
        *   Transactions in the external statement but not in our ledger.
        *   Matched transactions with amount differences (outside tolerance).
    *   **Reporting:** Generate reports detailing matched transactions, unmatched internal transactions, unmatched external transactions, and discrepancies.
    *   **User Interface (Future):** A UI would be beneficial for:
        *   Reviewing automated matches.
        *   Manually matching transactions.
        *   Investigating and resolving discrepancies (e.g., creating missing internal transactions, marking external items as 'ignore' with a reason, initiating dispute processes).
        *   Adjusting matching rules.
    *   **Aging:** Track how long items remain unmatched to prioritize investigation.

5.  **Automation and Scheduling:**
    *   Automate the import and matching processes to run regularly.
    *   Set up alerts for high numbers of discrepancies or critical failures in the reconciliation process.

## Schema Considerations (Already in `schema_updates.sql`)

*   **`external_transaction_sources`:**
    *   `source_id`: PK
    *   `source_name`: Name of the external entity.
*   **`external_transactions`:**
    *   `ext_transaction_id`: PK
    *   `source_id`: FK to `external_transaction_sources`.
    *   `reference_id`: Crucial for matching; external system's unique ID for the transaction.
    *   `transaction_date`, `amount`, `currency`, `description`: Standard transaction details.
    *   `status`: Tracks the reconciliation state ('pending_match', 'matched', 'unmatched', 'discrepancy', 'ignored').
    *   `ledger_transaction_id`: FK to our `transactions` table upon successful match.

## Future Enhancements

*   **Machine Learning for Matching:** For complex scenarios, ML models could be trained to improve matching accuracy.
*   **Automated Adjustments:** For certain types of known, small discrepancies (e.g., bank fees not yet booked), automated creation of internal transactions could be considered with strict controls.
*   **Workflow for Discrepancy Resolution:** Implementing a case management system or workflow for tracking and resolving identified discrepancies.

This document provides a high-level overview. A detailed design would require further analysis of specific external data sources and business reconciliation rules.
```
