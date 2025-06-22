// Represents the data structure for an authenticated admin user
export interface AdminUser {
  user_id: number;
  username: string; // Typically email for login
  email: string;
  role_name: string; // e.g., 'admin', 'teller', 'auditor'
  is_active: boolean;
  customer_id?: number | null; // Admin users might not always be linked to a customer
  // Add any other relevant fields returned by the backend's /api/admin/users/me endpoint
  // For example:
  // first_name?: string;
  // last_name?: string;
}

// For login credentials
export interface AdminLoginCredentials {
  username: string;
  password: any; // Keep as 'any' if backend expects specific type not just string for form data
}

// Payload for creating an admin user (matches AdminUserCreateRequest from backend models)
export interface AdminUserCreatePayload {
  username: string; // Typically email
  email: string;    // Contact email
  password: string;
  role_id: number;
  customer_id?: number | null;
  is_active?: boolean;
}

// Payload for updating an admin user (matches AdminUserUpdateRequest from backend models)
export interface AdminUserUpdatePayload {
  username?: string;
  email?: string;
  password?: string | null; // Optional: only if changing
  role_id?: number;
  customer_id?: number | null;
  is_active?: boolean;
}
```
