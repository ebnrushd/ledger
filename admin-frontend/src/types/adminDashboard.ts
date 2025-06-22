// Based on api.models.AdminDashboardData and AdminDashboardRecentTransaction

export interface AdminDashboardRecentTransaction {
  id: number; // Was transaction_id in Python, usually becomes id or transactionId in JS/TS
  timestamp: string; // ISO format string
  account_number: string;
  type: string; // transaction_type_name
  amount: number; // Keep as number for display, or use string for precision with a library
  description?: string | null;
  // currency?: string; // Add if backend provides it per transaction in this summary
}

export interface AdminDashboardData {
  total_customers: number;
  total_accounts: number; // This was accounts_summary.total_accounts in prompt, backend provides total_accounts
  // total_users: number; // Backend provides this? Check api/models.py -> AdminDashboardData
  total_system_balance_sum: number; // Backend provides this
  total_system_balance_currency_note: string; // Backend provides this
  transactions_last_24h: number; // Backend provides this
  recent_transactions: AdminDashboardRecentTransaction[]; // Backend provides this (renamed from recent_transactions_sample)

  // Example if backend had accounts_summary nested object:
  // accounts_summary?: {
  //   total_accounts: number;
  //   checking_accounts: number;
  //   savings_accounts: number;
  //   credit_accounts: number;
  // };
}

// Note: The Python Pydantic model AdminDashboardData in `api/models.py` has:
// total_customers: int
// total_accounts: int
// total_system_balance_sum: Decimal
// total_system_balance_currency_note: str
// transactions_last_24h: int
// recent_transactions: List[AdminDashboardRecentTransaction]

// And AdminDashboardRecentTransaction Python model has:
// id: int
// timestamp: str (already string from isoformat())
// account_number: str
// type: str
// amount: Decimal
// description: Optional[str]

// The TypeScript interfaces above are adjusted to match this structure.
// `total_users` was not in the backend Pydantic model, so it's removed here for now.
// `accounts_summary` was also not in the backend model, `total_accounts` is top-level.
```
