import adminApiClient from './adminApiClient';
import type { AdminUser, AdminUserCreatePayload, AdminUserUpdatePayload } from '@/types/adminUser';
import type { Role } from '@/types/role';

// Assuming backend returns a paginated structure for users
// This should align with AdminUserListResponse from api/models.py
export interface PaginatedAdminUsersResponse {
  users: AdminUser[]; // The backend AdminUserListResponse uses UserSchema, which should be compatible
  total_items: number;
  total_pages: number;
  page: number;
  per_page: number;
}

const fetchAdminUsers = async (
  page: number = 1,
  limit: number = 10,
  filters: any = {} // Define a proper filter type if needed
): Promise<PaginatedAdminUsersResponse> => {
  try {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(limit), // Match backend param name if different
    });
    if (filters.search_query) {
      params.append('search_query', filters.search_query);
    }
    if (filters.role_filter) { // Assuming backend supports role_filter by name or ID
        params.append('role_filter', filters.role_filter);
    }
    // Add other filters to params as needed

    // Uses /api/admin/users (from api_admin/users.py)
    const response = await adminApiClient.get<PaginatedAdminUsersResponse>('/api/admin/users', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching admin users:', error);
    throw error;
  }
};

const fetchAdminUserById = async (userId: string | number): Promise<AdminUser> => {
  try {
    const response = await adminApiClient.get<AdminUser>(`/api/admin/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching admin user ${userId}:`, error);
    throw error;
  }
};

const createAdminUser = async (userData: AdminUserCreatePayload): Promise<AdminUser> => {
  try {
    const response = await adminApiClient.post<AdminUser>('/api/admin/users', userData);
    return response.data;
  } catch (error) {
    console.error('Error creating admin user:', error);
    throw error;
  }
};

const updateAdminUser = async (userId: string | number, userData: AdminUserUpdatePayload): Promise<AdminUser> => {
  try {
    const response = await adminApiClient.put<AdminUser>(`/api/admin/users/${userId}`, userData);
    return response.data;
  } catch (error) {
    console.error(`Error updating admin user ${userId}:`, error);
    throw error;
  }
};

const fetchAdminRoles = async (): Promise<Role[]> => {
  // TODO: Replace with actual API call to GET /api/admin/roles when backend endpoint is ready.
  console.warn("fetchAdminRoles is using mocked data. Implement backend endpoint /api/admin/roles.");
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        { role_id: 1, role_name: 'customer' }, // Assuming IDs from auth_schema.sql
        { role_id: 2, role_name: 'teller' },
        { role_id: 3, role_name: 'admin' },
        { role_id: 4, role_name: 'auditor' },
        { role_id: 5, role_name: 'system_process' },
      ]);
    }, 100); // Simulate small delay
  });
  // Example for actual API call:
  // try {
  //   const response = await adminApiClient.get<Role[]>('/api/admin/roles');
  //   return response.data;
  // } catch (error) {
  //   console.error('Error fetching admin roles:', error);
  //   throw error;
  // }
};


const adminUserService = {
  fetchAdminUsers,
  fetchAdminUserById,
  createAdminUser,
  updateAdminUser,
  fetchAdminRoles,
};

export default adminUserService;
```
