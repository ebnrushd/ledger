import adminApiClient from './adminApiClient';
import type { AdminDashboardData } from '@admin/types/adminDashboard';

const fetchAdminDashboardData = async (): Promise<AdminDashboardData> => {
  try {
    // The backend endpoint is GET /api/admin/dashboard/
    // adminApiClient already has the base URL configured (e.g., http://localhost:8000)
    const response = await adminApiClient.get<AdminDashboardData>('/api/admin/dashboard/');
    return response.data;
  } catch (error) {
    console.error('Error fetching admin dashboard data:', error);
    // Error will be handled by the Axios interceptor for generic errors (like 401/403 for session)
    // or by the calling action in the store for specific UI error messages.
    throw error; // Re-throw to be caught by the store action
  }
};

const adminDashboardService = {
  fetchAdminDashboardData,
};

export default adminDashboardService;
```
