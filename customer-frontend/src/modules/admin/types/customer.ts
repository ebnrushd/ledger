import type { AdminUser } from './adminUser'; // Assuming AdminUser is defined
import type { Account } from './account';   // Assuming Account is defined for admin context

// For the list view - a subset of fields
export interface AdminCustomerListItem {
  customer_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string | null;
  // Fields that might come from joins or aggregated data in the backend response
  linked_user_username?: string | null;
  account_count?: number;
}

// For the detail view - more comprehensive
export interface AdminCustomerDetails extends AdminCustomerListItem {
  address?: string | null;
  created_at: string; // ISO date string
  // updated_at?: string; // If backend provides this for customers table
  linked_user?: Partial<AdminUser> | null; // Partial to avoid full AdminUser complexity if not needed
  accounts?: Account[]; // List of associated bank accounts
}

// For paginated API response for customer list
export interface PaginatedAdminCustomersResponse {
  customers: AdminCustomerListItem[]; // Changed from items to customers to match backend likely
  total_items: number;
  total_pages: number;
  page: number;
  per_page: number; // Assuming backend uses per_page
}
```
