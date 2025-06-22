import adminApiClient from './adminApiClient'; // Uses withCredentials: true
import type { AdminUser, AdminLoginCredentials } from '@/types/adminUser';

const loginAdmin = async (credentials: AdminLoginCredentials): Promise<AdminUser> => {
  try {
    // The HTML Admin Panel login is POST /admin/login and expects form data.
    // For a JSON API, we'd ideally have POST /api/admin/auth/login expecting JSON or form data.
    // Let's assume the backend has been adapted or a new endpoint `/api/admin/auth/login` exists
    // that accepts JSON and returns JSON upon successful session cookie setting.

    // If the backend /admin/login (from api.routers.admin.auth.py) is still the primary session creator
    // and it only accepts 'application/x-www-form-urlencoded', we must send data that way.
    // And it redirects, which Axios won't follow by default for POST.
    // This makes SPA-style login tricky with that specific HTML-first endpoint.

    // **Assumption for this service:** Backend provides a JSON-friendly login endpoint for admins
    // that sets the session cookie and returns user data. e.g., `/api/admin/auth/login`.
    // If not, this service would be more complex (e.g. hidden iframe or expecting specific redirect handling).

    const params = new URLSearchParams();
    params.append('username', credentials.username);
    params.append('password', credentials.password);

    // Using the existing /admin/login which expects form data and sets session cookie upon redirect
    // This will be tricky because Axios doesn't follow POST redirects by default.
    // The actual response here might be the redirect HTML if not handled.
    // For a true SPA with session, the backend login should ideally return JSON with user details.
    // Let's proceed assuming the backend /admin/login route in api.routers.admin.auth.py
    // can also handle an XHR request and return JSON if it detects one, or that
    // the client will handle the redirect correctly (which is hard for JS).

    // For robust SPA session login:
    // Backend's POST /admin/login (from api.routers.admin.auth.py) should ideally:
    // 1. Set the session cookie.
    // 2. Instead of redirecting (if it's an XHR/JSON request), return a JSON response like { success: true, user: AdminUser }.
    // For now, we'll call it and assume it works for setting the cookie.
    // The actual user data will be fetched by fetchCurrentAdminUser.

    await adminApiClient.post('/admin/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    // After this call, the HTTP-only session cookie should be set by the browser.
    // Now, fetch the user details to confirm login and get user data.
    return fetchCurrentAdminUser();

  } catch (error) {
    console.error('Admin login service error:', error);
    throw error;
  }
};

const logoutAdmin = async (): Promise<void> => {
  try {
    // This should hit POST /admin/logout which clears the session server-side.
    // The route api.routers.admin.auth.py has GET /admin/logout.
    // For consistency with POST for actions, let's assume it's POST or change it.
    // For now, using GET as per current backend route.
    await adminApiClient.get('/admin/logout'); // Changed to GET
    // Cookie should be cleared by the server.
  } catch (error) {
    console.error('Admin logout service error:', error);
    // Even if logout API call fails, client should clear its state.
    // Throwing error so store can know, but UI should proceed to clear state.
    throw error;
  }
};

const fetchCurrentAdminUser = async (): Promise<AdminUser> => {
  try {
    // This endpoint needs to exist on the backend, protected by session auth.
    // e.g., GET /api/admin/users/me
    const response = await adminApiClient.get<AdminUser>('/api/admin/users/me');
    return response.data;
  } catch (error) {
    console.error('Error fetching current admin user:', error);
    // This error (e.g., 401/403) will be handled by apiClient interceptor to redirect.
    // Or, if it's another error, it's re-thrown.
    throw error;
  }
};

const adminAuthService = {
  loginAdmin,
  logoutAdmin,
  fetchCurrentAdminUser,
};

export default adminAuthService;
```
