// Types for Admin Panel Transaction Monitoring

// For transaction list items - may include joined data from backend service
export interface AdminTransactionListItem {
  transaction_id: number;
  transaction_timestamp: string; // ISO date string
  account_id: number;
  primary_account_number?: string; // Joined from accounts table
  customer_id?: number; // Joined from accounts -> customers table
  customer_name?: string; // Example: (customer_first_name + customer_last_name) - if joined
  type_name: string; // Joined from transaction_types table
  amount: number; // Or string for precision handling
  currency?: string; // From accounts table, useful if multiple currencies are possible
  description?: string | null;
  related_account_id?: number | null;
  related_account_number?: string | null; // Joined from related accounts table
}

// For transaction detail view - can extend list item or be more comprehensive
// This should match the structure returned by the backend's /api/admin/transactions/{transactionId}
export interface AdminTransactionDetail extends AdminTransactionListItem {
  // Specific fields returned by the detailed transaction endpoint:
  primary_cust_fname?: string | null; // From customers table via accounts
  primary_cust_lname?: string | null; // From customers table via accounts
  // related_account_customer_name?: string | null; // If related account's customer is also joined
}

export interface PaginatedAdminTransactionsResponse {
  transactions: AdminTransactionListItem[];
  total_items: number;
  total_pages: number;
  page: number;
  per_page: number;
}

// Filters for fetching admin transactions
export interface AdminTransactionFilters {
  account_id_filter?: number | null;
  // account_number_filter?: string | null; // Service uses account_id, but UI might take number
  transaction_type_filter?: string | null;
  start_date_filter?: string | null; // YYYY-MM-DD
  end_date_filter?: string | null;   // YYYY-MM-DD
  // Optional: min_amount_filter?: number | null;
  // Optional: max_amount_filter?: number | null;
  // Optional: search_query_description?: string | null;
}
```
