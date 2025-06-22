import axios from 'axios';

const baseURL = import.meta.env.VITE_ADMIN_API_BASE_URL || 'http://localhost:8000'; // Fallback

const adminApiClient = axios.create({
  baseURL: baseURL,
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest', // Often helpful for backend to identify AJAX requests
  },
  withCredentials: true, // Crucial for sending/receiving HTTP-only session cookies
});

// Optional: Interceptors for admin API client

// Request Interceptor: Can be used for CSRF tokens if needed, or other specific headers.
adminApiClient.interceptors.request.use(
  (config) => {
    // Example: If you had a CSRF token stored in a cookie or meta tag
    // const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1];
    // if (csrfToken) {
    //   config.headers['X-CSRFToken'] = csrfToken;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle global errors, e.g., redirect to login on 401/403 for session expiry
adminApiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      const status = error.response.status;
      // If session expired or not authorized, redirect to admin login
      if (status === 401 || status === 403) {
        // Check current location to avoid redirect loops if already on login page
        if (window.location.pathname !== '/login' && !window.location.pathname.startsWith('/admin/login')) { // Adjust path if admin login is /admin/login
          // Construct login URL carefully, considering potential base paths or router mode
          const loginPath = '/login'; // Assuming admin login is at root /login for admin frontend
          console.warn(`Admin API request unauthorized (${status}), redirecting to login: ${loginPath}`);
          window.location.href = loginPath; // Or use router if accessible and configured
        }
      }
    }
    return Promise.reject(error);
  }
);

export default adminApiClient;
```
