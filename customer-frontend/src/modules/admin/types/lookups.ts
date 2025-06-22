// For generic lookup types used in admin panel, e.g., for populating dropdowns

export interface AccountStatusType {
  status_id: number;
  status_name: string;
}

export interface TransactionType {
  transaction_type_id: number;
  type_name: string;
}

export interface RoleType { // From auth_schema.sql, if needed for lookups
    role_id: number;
    role_name: string;
}

// Add other lookup types as needed
```
