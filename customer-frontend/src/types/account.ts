// Based on api.models.AccountDetails Pydantic model
export interface Account {
  account_id: number; // Changed from id to match backend Pydantic model
  customer_id: number;
  account_number: string;
  account_type: string;
  balance: number; // Keep as number for now, use a Decimal library for precision if needed
  currency: string;
  status_name: string; // Changed from status to match backend
  overdraft_limit: number;
  opened_at: string; // ISO date string
  updated_at?: string | null; // ISO date string
}
```
