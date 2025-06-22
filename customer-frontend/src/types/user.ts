export interface User {
  user_id: number;
  username: string; // This is the login username, often an email
  email: string;    // Contact email, could be same as username or different
  role_name: string;
  is_active: boolean;
  customer_id?: number | null;
  created_at: string; // ISO date string
  last_login?: string | null; // ISO date string

  // Fields from linked customer profile that might be part of a "user profile view"
  first_name?: string;
  last_name?: string;
  phone_number?: string | null;
  address?: string | null;
}

export interface UserProfileUpdatePayload {
    email?: string; // User's primary email for login/notifications if changeable
    // Customer-related fields
    first_name?: string;
    last_name?: string;
    phone_number?: string | null;
    address?: string | null;
}


export interface TokenPayload { // Data decoded from JWT
  sub: string; // username (usually email)
  user_id: number;
  role: string; // role_name
  exp: number; // Expiration timestamp
  // Add other custom claims if you put them in the JWT (e.g. customer_id)
  customer_id?: number | null;
}
```
