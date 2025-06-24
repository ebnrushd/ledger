// Based on api.models.TransactionDetails Pydantic model
// and assuming a paginated response structure from the backend.

export interface Transaction {
  transaction_id: number; // Changed from string | number to number
  account_id: number;
  type_name: string; // Renamed from transaction_type_name to match common usage
  amount: number; // Keep as number for now, use Decimal.js or string for precision if needed
  transaction_timestamp: string; // ISO date string
  description?: string | null;
  related_account_id?: number | null;
  related_account_number?: string | null; // Added this if backend can provide it
  // currency?: string; // Usually implied by the account's currency. Add if API provides it per transaction.
}

export interface PaginatedTransactionsResponse {
  items: Transaction[];
  page: number;
  limit: number; // Corresponds to 'per_page' or 'itemsPerPage'
  total_items: number;
  total_pages: number;
}

// Example of filter parameters that might be used for fetching transactions
export interface TransactionFilters {
  date_from?: string; // YYYY-MM-DD
  date_to?: string;   // YYYY-MM-DD
  type?: string;      // e.g., 'deposit', 'withdrawal'
  // Add other potential filters
}
```
