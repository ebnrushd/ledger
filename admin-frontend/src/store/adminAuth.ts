import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import adminAuthService from '@/services/adminAuthService';
import type { AdminUser, AdminLoginCredentials } from '@/types/adminUser';
import { useRouter } from 'vue-router'; // For programmatic navigation if needed inside actions

export const useAdminAuthStore = defineStore('adminAuth', () => {
  // State
  const adminUser = ref<AdminUser | null>(null);
  const isAdminAuthenticated = ref<boolean>(false); // Initialize as false
  const authError = ref<string | null>(null);
  const isLoading = ref<boolean>(false); // For login, logout, checkAuthStatus

  // Getters
  const isUserAdminAuthenticated = computed(() => isAdminAuthenticated.value);
  const getAdminUser = computed(() => adminUser.value);
  const getAuthError = computed(() => authError.value);
  const getIsLoadingAuth = computed(() => isLoading.value);

  // Actions
  async function login(credentials: AdminLoginCredentials): Promise<boolean> {
    isLoading.value = true;
    authError.value = null;
    try {
      const userData = await adminAuthService.loginAdmin(credentials); // This now fetches user data
      if (userData && userData.user_id) { // Check if user_id exists, basic validation
        adminUser.value = userData;
        isAdminAuthenticated.value = true;
        localStorage.setItem('isAdminLoggedIn', 'true'); // Placeholder for router guard
        return true;
      } else {
        // This case might occur if loginAdmin resolves but doesn't return valid user
        authError.value = "Login succeeded but user data could not be retrieved.";
        _clearSessionState(); // Clear any partial state
        return false;
      }
    } catch (error: any) {
      if (error.response && error.response.data && error.response.data.detail) {
        authError.value = error.response.data.detail;
      } else if (error.message) {
        authError.value = error.message;
      } else {
        authError.value = 'Login failed. Please try again.';
      }
      _clearSessionState();
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function logout() {
    isLoading.value = true;
    authError.value = null;
    try {
      await adminAuthService.logoutAdmin();
    } catch (error: any) {
      // Log error, but proceed with client-side logout anyway
      console.error("Error during server logout, proceeding with client-side logout:", error);
    } finally {
      _clearSessionState();
      isLoading.value = false;
      // Router push is typically handled by component or interceptor after logout action
    }
  }

  async function checkAuthStatus(): Promise<boolean> {
    isLoading.value = true;
    authError.value = null;
    try {
      // This relies on /api/admin/users/me returning user data if session is valid,
      // or throwing an error (e.g. 401) if not, which adminApiClient interceptor might catch.
      const userData = await adminAuthService.fetchCurrentAdminUser();
      adminUser.value = userData;
      isAdminAuthenticated.value = true;
      localStorage.setItem('isAdminLoggedIn', 'true'); // Placeholder for router guard
      return true;
    } catch (error) {
      _clearSessionState(); // Clear any remnants if auth check fails
      // No need to set authError here as it's just a status check, not a user action failure
      console.log("checkAuthStatus: User not authenticated or session expired.");
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  // Internal helper
  function _clearSessionState() {
    adminUser.value = null;
    isAdminAuthenticated.value = false;
    localStorage.removeItem('isAdminLoggedIn'); // Placeholder for router guard
    // Note: Actual session cookie is HttpOnly, cannot be cleared by JS.
    // Backend logout is responsible for invalidating it.
  }

  return {
    adminUser,
    isAdminAuthenticated,
    authError,
    isLoading,
    isUserAdminAuthenticated,
    getAdminUser,
    getAuthError,
    getIsLoadingAuth,
    login,
    logout,
    checkAuthStatus,
  };
});
```
