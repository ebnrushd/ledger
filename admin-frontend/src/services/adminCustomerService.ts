import adminApiClient from './adminApiClient';
import type {
  AdminCustomerListItem,
  AdminCustomerDetails,
  PaginatedAdminCustomersResponse
} from '@/types/customer';

// Define a type for filters if they become more complex
interface CustomerListFilters {
  search_query?: string;
  // Add other potential filters like has_accounts_filter (boolean) etc.
}

const fetchAdminCustomers = async (
  page: number = 1,
  limit: number = 10,
  filters: CustomerListFilters = {}
): Promise<PaginatedAdminCustomersResponse> => {
  try {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(limit), // Ensure backend API uses 'per_page'
    });
    if (filters.search_query) {
      params.append('search_query', filters.search_query);
    }
    // Add other filters to params as needed

    // Endpoint should be /api/admin/customers as defined in backend api_admin router
    const response = await adminApiClient.get<PaginatedAdminCustomersResponse>('/api/admin/customers', { params });
    // Ensure the backend response structure matches PaginatedAdminCustomersResponse
    // Specifically, the list of customers should be under a key like "customers" if the Pydantic model is AdminCustomerListResponse
    // If the backend returns items directly: response.data.items, then PaginatedAdminCustomersResponse.customers should be items.
    // The current AdminCustomerListResponse in api/models.py uses "customers".
    return response.data;
  } catch (error) {
    console.error('Error fetching admin list of customers:', error);
    throw error;
  }
};

const fetchAdminCustomerDetailsById = async (customerId: string | number): Promise<AdminCustomerDetails> => {
  try {
    // Endpoint should be /api/admin/customers/{customerId}
    const response = await adminApiClient.get<AdminCustomerDetails>(`/api/admin/customers/${customerId}`);
    // This assumes the backend directly returns AdminCustomerDetails structure,
    // including potentially nested linked_user and accounts list.
    return response.data;
  } catch (error) {
    console.error(`Error fetching admin customer details for ID ${customerId}:`, error);
    throw error;
  }
};

const adminCustomerService = {
  fetchAdminCustomers,
  fetchAdminCustomerDetailsById,
};

export default adminCustomerService;
```
