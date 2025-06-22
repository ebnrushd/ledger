import axios from 'axios';

// Get the API base URL from environment variables
// Vite exposes env variables prefixed with VITE_ on import.meta.env
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'; // Fallback if not set

const apiClient = axios.create({
  baseURL: baseURL,
  headers: {
    'Content-Type': 'application/json',
    // You can add other default headers here if needed
  },
});

// Optional: Add interceptors for request or response handling
// For example, to automatically add JWT token to requests:
apiClient.interceptors.request.use(
  (config) => {
    // Dynamically import store here or ensure it's initialized before first API call
    // For simplicity, we assume Pinia is set up and store is accessible.
    // A more robust way is to pass the store instance or use a plugin system.
    // This dynamic import might be problematic. Better: access store after it's created.
    // Let's assume main.ts has run and Pinia is active.
    // We can't directly use `useAuthStore` here as it's outside Vue setup context.
    // Instead, the token can be read from localStorage directly, as the store also uses it.
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Example: Response interceptor for handling global errors like 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => { // Made async to potentially use async store actions
    if (error.response && error.response.status === 401) {
      console.error('Unauthorized (401) response from API.');
      // To properly use the store here for logout, we need to avoid circular dependencies
      // and ensure the store is available.
      // This is a common challenge. One way is to emit an event that App.vue listens to,
      // or have a global error handler that can access the router and store.

      // For now, directly clearing localStorage and redirecting.
      // A full solution would call authStore.logout().
      const token = localStorage.getItem('authToken');
      if (token) { // Only logout if there was a token, otherwise it might be a login attempt failing
        console.log('Clearing token and redirecting to login due to 401.');
        localStorage.removeItem('authToken');
        localStorage.removeItem('authUser');
        localStorage.removeItem('username'); // Clear any related user data
        delete apiClient.defaults.headers.common['Authorization'];

        // Redirect to login. This might be too aggressive if some 401s are not due to expired token.
        // For example, a login attempt itself failing with 401 should not redirect from login to login.
        // Check if current path is not already login/register
        if (!window.location.pathname.endsWith('/login') && !window.location.pathname.endsWith('/register')) {
            window.location.href = '/login?session_expired=true';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```
