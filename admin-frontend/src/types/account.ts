// For the Admin Panel, representing account data

// From the backend /api/admin/lookups/account-status-types
export interface AccountStatusType {
  status_id: number;
  status_name: string;
}

// Represents an account item in a list or detailed view within the admin panel
// This should align with what account_management.list_accounts and get_account_by_id return,
// particularly the list_accounts which joins customer info.
export interface AdminAccount {
  account_id: number;
  customer_id: number;
  account_number: string;
  account_type: string;
  balance: number; // Keep as number for display, or use string for precision handling
  currency: string;
  status_name: string;
  overdraft_limit: number; // Keep as number
  opened_at: string; // ISO date string
  updated_at?: string | null; // ISO date string

  // Joined fields from customer table (as returned by core.account_management.list_accounts)
  customer_first_name?: string | null;
  customer_last_name?: string | null;
  customer_email?: string | null; // May not be strictly needed in all list views but good to have

  // For detail view, potentially more nested data
  // For example, if the backend /api/admin/accounts/{accountId} endpoint joins more:
  // customer?: AdminCustomerListItem; // (Defined in types/customer.ts)
  // recent_transactions?: Transaction[]; // (Defined in types/transaction.ts)
}

export interface PaginatedAdminAccountsResponse {
  accounts: AdminAccount[]; // Changed from items to accounts, and type to AdminAccount
  total_items: number;
  total_pages: number;
  page: number;
  per_page: number;
}
```
