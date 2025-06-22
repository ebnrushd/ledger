import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router'; // Import directly if needed for actions, or pass router instance
import authService from '@/services/authService'; // API calls
import apiClient from '@/services/apiClient'; // To set/remove auth header
import type { User, TokenPayload } from '@/types/user'; // User interface
import { jwtDecode } from 'jwt-decode'; // Helper to decode JWT for payload (npm install jwt-decode)

// Helper to parse JWT. In a real app, more robust error handling might be needed.
const parseJwt = (token: string): TokenPayload | null => {
  try {
    return jwtDecode<TokenPayload>(token);
  } catch (e) {
    console.error("Failed to decode JWT:", e);
    return null;
  }
};

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('authToken'));
  const user = ref<User | null>(JSON.parse(localStorage.getItem('authUser') || 'null'));
  const isAuthenticated = ref<boolean>(!!token.value); // Initial state based on token presence
  const loginError = ref<string | null>(null);
  const registerError = ref<string | null>(null);
  const registerSuccessMessage = ref<string | null>(null);
  const isLoading = ref(false);

  // Getters (computed properties)
  const getUser = computed(() => user.value);
  const getToken = computed(() => token.value);
  const isUserAuthenticated = computed(() => isAuthenticated.value);

  // Actions
  function setAuthData(newToken: string, userDataFromToken: TokenPayload) {
    token.value = newToken;
    // Map token payload to User interface. Adjust as needed.
    user.value = {
        user_id: userDataFromToken.user_id,
        username: userDataFromToken.sub, // 'sub' claim usually holds username/email
        email: userDataFromToken.sub, // Assuming username is email
        role_name: userDataFromToken.role,
        is_active: true, // Assume active if token issued, or fetch /me to confirm
        // customer_id might not be in token, fetch from /me if needed
    };
    isAuthenticated.value = true;
    localStorage.setItem('authToken', newToken);
    localStorage.setItem('authUser', JSON.stringify(user.value)); // Store basic user info
    localStorage.setItem('username', user.value.username); // For DashboardView example
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
  }

  function clearAuthData() {
    token.value = null;
    user.value = null;
    isAuthenticated.value = false;
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    localStorage.removeItem('username');
    delete apiClient.defaults.headers.common['Authorization'];
  }

  async function login(credentials: { username: string; password: any }) {
    isLoading.value = true;
    loginError.value = null;
    try {
      const response = await authService.loginUser(credentials);
      const newToken = response.data.access_token;
      const decodedToken = parseJwt(newToken);
      if (decodedToken) {
        setAuthData(newToken, decodedToken);
        // Router push is usually handled by the component after action resolves
      } else {
        throw new Error("Invalid token received from server.");
      }
    } catch (error: any) {
      if (error.response && error.response.data && error.response.data.detail) {
        loginError.value = error.response.data.detail;
      } else {
        loginError.value = 'Login failed. Please try again.';
      }
      clearAuthData(); // Ensure no partial login state
      throw error; // Re-throw for component to handle
    } finally {
      isLoading.value = false;
    }
  }

  async function register(userData: any) {
    isLoading.value = true;
    registerError.value = null;
    registerSuccessMessage.value = null;
    try {
      const response = await authService.registerUser(userData);
      // Assuming API returns created user data matching UserSchema
      registerSuccessMessage.value = `Registration successful for ${response.data.username}! You can now log in.`;
      // No automatic login after register for this example
    } catch (error: any) {
      if (error.response && error.response.data && error.response.data.detail) {
        registerError.value = error.response.data.detail;
      } else {
        registerError.value = 'Registration failed. Please try again.';
      }
      throw error; // Re-throw for component
    } finally {
      isLoading.value = false;
    }
  }

  function logout(router?: any) { // Optional router instance for explicit redirect
    clearAuthData();
    if (router && typeof router.push === 'function') {
        router.push('/login');
    } else {
        // Fallback if router not passed or in a context where it's not available (e.g. interceptor)
        window.location.href = '/login'; // Force redirect
    }
  }

  function tryAutoLogin() {
    console.log("Attempting auto-login...");
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      const decodedToken = parseJwt(storedToken);
      if (decodedToken && decodedToken.exp * 1000 > Date.now()) { // Check expiration
        console.log("Valid token found, attempting to set auth data.");
        setAuthData(storedToken, decodedToken);
        // Optionally, you could add a call to a '/users/me' endpoint here
        // to validate the token with the backend and refresh user data.
        // If that call fails (e.g. token revoked server-side), then call clearAuthData().
      } else {
        console.log("Token expired or invalid, clearing auth data.");
        clearAuthData(); // Token expired or invalid
      }
    } else {
        console.log("No token found for auto-login.");
    }
  }

  // Call tryAutoLogin when store is initialized (Pinia setup phase)
  // This is one way; another is calling it in main.ts or App.vue's created hook.
  // If called here, it runs as soon as the store is first used/imported.
  // tryAutoLogin(); // Let's call it from main.ts for more explicit app lifecycle control.

  return {
    token,
    user,
    isAuthenticated,
    loginError,
    registerError,
    registerSuccessMessage,
    isLoading, // General loading for login/register

    // New state for profile and password
    isUpdatingProfile: ref<boolean>(false),
    profileUpdateError: ref<string | null>(null),
    profileUpdateSuccessMessage: ref<string | null>(null),
    isChangingPassword: ref<boolean>(false),
    changePasswordError: ref<string | null>(null),
    changePasswordSuccessMessage: ref<string | null>(null),

    getUser,
    getToken,
    isUserAuthenticated,
    login,
    register,
    logout,
    tryAutoLogin,
    setAuthData,
    clearAuthData,
  };
});

// Actions for profile and password need to be added to the store definition.
// The current structure returns an object from setup(). We need to add new actions there.

// Re-defining the store to include new actions correctly.
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import authService from '@/services/authService';
import userService from '@/services/userService'; // Import new service
import apiClient from '@/services/apiClient';
import type { User, TokenPayload, UserProfileUpdatePayload } from '@/types/user';
import { jwtDecode } from 'jwt-decode';

const parseJwtLocal = (token: string): TokenPayload | null => { // Renamed to avoid conflict if this file is re-evaluated
  try { return jwtDecode<TokenPayload>(token); }
  catch (e) { console.error("Failed to decode JWT:", e); return null; }
};

export const useAuthStore = defineStore('auth', () => {
  // --- State ---
  const token = ref<string | null>(localStorage.getItem('authToken'));
  const user = ref<User | null>(JSON.parse(localStorage.getItem('authUser') || 'null'));
  const isAuthenticated = ref<boolean>(!!token.value);

  const loginError = ref<string | null>(null);
  const registerError = ref<string | null>(null);
  const registerSuccessMessage = ref<string | null>(null);
  const isLoading = ref(false); // For login/register

  const isUpdatingProfile = ref<boolean>(false);
  const profileUpdateError = ref<string | null>(null);
  const profileUpdateSuccessMessage = ref<string | null>(null);

  const isChangingPassword = ref<boolean>(false);
  const changePasswordError = ref<string | null>(null);
  const changePasswordSuccessMessage = ref<string | null>(null);

  // --- Getters ---
  const getUser = computed(() => user.value);
  const getToken = computed(() => token.value);
  const isUserAuthenticated = computed(() => isAuthenticated.value);

  // --- Actions ---
  function _setAuthData(newToken: string, userDataFromToken: TokenPayload, fetchedCustomerProfile?: Partial<User>) {
    token.value = newToken;

    let combinedUserData: User = {
        user_id: userDataFromToken.user_id,
        username: userDataFromToken.sub,
        email: userDataFromToken.sub, // Default email to username from token
        role_name: userDataFromToken.role,
        is_active: true, // Assume active from successful token
        customer_id: userDataFromToken.customer_id || null,
        created_at: '', // This should come from /users/me or be part of token if needed
        last_login: new Date().toISOString(), // Approximate
    };

    if (fetchedCustomerProfile) { // Merge customer profile data if available
        combinedUserData = { ...combinedUserData, ...fetchedCustomerProfile, email: fetchedCustomerProfile.email || combinedUserData.email };
    } else if (user.value && user.value.customer_id === combinedUserData.customer_id) {
        // If not fetching profile now, but old user state had matching customer data, retain it
        combinedUserData.first_name = user.value.first_name;
        combinedUserData.last_name = user.value.last_name;
        combinedUserData.phone_number = user.value.phone_number;
        combinedUserData.address = user.value.address;
        // Ensure contact email from customer profile is preferred if available
        if(user.value.email && user.value.customer_id) combinedUserData.email = user.value.email;
    }

    user.value = combinedUserData;
    isAuthenticated.value = true;
    localStorage.setItem('authToken', newToken);
    localStorage.setItem('authUser', JSON.stringify(user.value));
    localStorage.setItem('username', user.value.username); // For simple display
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
  }

  function _clearAuthData() {
    token.value = null; user.value = null; isAuthenticated.value = false;
    localStorage.removeItem('authToken'); localStorage.removeItem('authUser'); localStorage.removeItem('username');
    delete apiClient.defaults.headers.common['Authorization'];
  }

  async function login(credentials: { username: string; password: any }) {
    isLoading.value = true; loginError.value = null;
    try {
      const response = await authService.loginUser(credentials);
      const newToken = response.data.access_token;
      const decodedToken = parseJwtLocal(newToken);
      if (decodedToken) {
        // After login, token has user_id, role. Customer details (name, address) might need separate fetch
        // or be included in token if small, or fetched via a /users/me that joins customer data.
        // For now, _setAuthData will use token data and merge if customer profile is passed.
        // We could call a function here to fetch customer profile if customer_id is in token.
        let customerProfileData: Partial<User> = {};
        if (decodedToken.customer_id) {
            try {
                // This assumes updateUserProfile actually calls /customers/me (GET)
                // This is a bit of a hack. Better to have a dedicated customerService.fetchMyCustomerProfile()
                // For now, let's assume the token and initial localstorage `authUser` is enough
                // or `loadUserProfile` will be called by the component.
                // The `UserSchema` from backend's `/api/v1/auth/register` returns a full user object.
                // `/api/v1/auth/login` only returns a token. So after login, we need to get user details.
                // This could be done by a /users/me call or similar.
                // For this subtask, we'll assume the token is enough to populate basic user info
                // and profile view will call loadUserProfile for more.
            } catch (e) { console.error("Could not fetch customer profile post-login", e); }
        }
        _setAuthData(newToken, decodedToken, customerProfileData);
      } else { throw new Error("Invalid token received."); }
    } catch (error: any) {
      _clearAuthData();
      loginError.value = error.response?.data?.detail || error.message || 'Login failed.';
      throw error;
    } finally { isLoading.value = false; }
  }

  async function register(userData: UserCreateAPI) { // UserCreateAPI from types/user
    isLoading.value = true; registerError.value = null; registerSuccessMessage.value = null;
    try {
      const response = await authService.registerUser(userData); // Returns UserSchema like data
      registerSuccessMessage.value = `Registration successful for ${response.data.username}! You can now log in.`;
    } catch (error: any) {
      registerError.value = error.response?.data?.detail || error.message || 'Registration failed.';
      throw error;
    } finally { isLoading.value = false; }
  }

  function logout(router?: any) {
    const userIdForAudit = user.value?.user_id; // Get before clearing
    const usernameForAudit = user.value?.username;
    _clearAuthData();
    // Audit logout - this is client side, so less critical, but can be done.
    // Requires DB connection via an API call or a non-authed endpoint if desired.
    // For simplicity, not making an API call here to log client-side logout.
    console.log(`User ${usernameForAudit} (ID: ${userIdForAudit}) logged out.`);

    if (router && typeof router.push === 'function') { router.push('/login?logged_out=true'); }
    else { window.location.href = '/login?logged_out=true'; }
  }

  function tryAutoLogin() {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      const decodedToken = parseJwtLocal(storedToken);
      if (decodedToken && decodedToken.exp * 1000 > Date.now()) {
        // Token is present and not expired.
        // Reconstruct user state from localStorage if available, then potentially refresh from API.
        const storedUser = JSON.parse(localStorage.getItem('authUser') || 'null');
        _setAuthData(storedToken, decodedToken, storedUser || undefined); // Pass storedUser as fetchedCustomerProfile
        // Optionally trigger a background refresh of user profile from server:
        // loadUserProfile(); // This will be a new action
      } else { _clearAuthData(); }
    }
  }

  // --- New Actions for Profile Management ---
  async function loadUserProfile() {
    // This action assumes that the user is already authenticated (token exists).
    // It will fetch detailed customer profile data and merge it with user data from token.
    if (!token.value) {
        // profileUpdateError.value = "Not authenticated to load profile.";
        return; // Or throw error
    }
    isUpdatingProfile.value = true; // Reuse for loading indicator
    profileUpdateError.value = null;
    try {
        // Assuming userService.updateUserProfile actually calls PUT /api/v1/customers/me
        // We need a GET /api/v1/customers/me for this.
        // Let's assume the backend /api/v1/customers/me (GET) exists and returns CustomerDetails
        const customerProfileResponse = await apiClient.get<UserProfileUpdatePayload>('/customers/me');

        if (user.value) { // Ensure user object exists from token
            const updatedUserData: User = {
                ...user.value, // Keep existing user_id, username, role from token
                email: customerProfileResponse.data.email || user.value.email, // Prefer customer profile email if available
                first_name: customerProfileResponse.data.first_name,
                last_name: customerProfileResponse.data.last_name,
                phone_number: customerProfileResponse.data.phone_number,
                address: customerProfileResponse.data.address,
            };
            user.value = updatedUserData;
            localStorage.setItem('authUser', JSON.stringify(user.value));
        }
    } catch (error: any) {
        profileUpdateError.value = error.response?.data?.detail || error.message || "Failed to load user profile.";
        // Do not clear auth data here, token might still be valid.
    } finally {
        isUpdatingProfile.value = false;
    }
  }


  async function updateUserProfile(profileData: UserProfileUpdatePayload) {
    isUpdatingProfile.value = true;
    profileUpdateError.value = null;
    profileUpdateSuccessMessage.value = null;
    try {
      const updatedProfile = await userService.updateUserProfile(profileData); // Returns updated User/Customer data
      // Merge updatedProfile into existing user state
      if (user.value) {
        user.value = { ...user.value, ...updatedProfile };
        localStorage.setItem('authUser', JSON.stringify(user.value));
      }
      profileUpdateSuccessMessage.value = "Profile updated successfully!";
    } catch (error: any) {
      profileUpdateError.value = error.response?.data?.detail || error.message || "Profile update failed.";
      throw error;
    } finally {
      isUpdatingProfile.value = false;
    }
  }

  async function changePassword(passwordData: { current_password: string; new_password: string }) {
    isChangingPassword.value = true;
    changePasswordError.value = null;
    changePasswordSuccessMessage.value = null;
    try {
      await userService.changePassword(passwordData);
      changePasswordSuccessMessage.value = "Password changed successfully. You may need to log in again with your new password if your session is affected.";
      // Backend might invalidate current token/session, or not.
      // For simplicity, we don't force logout here. User can continue or will be forced if token is invalid.
    } catch (error: any) {
      changePasswordError.value = error.response?.data?.detail || error.message || "Password change failed.";
      throw error;
    } finally {
      isChangingPassword.value = false;
    }
  }

  function clearProfileStatusMessages() {
    profileUpdateError.value = null;
    profileUpdateSuccessMessage.value = null;
    changePasswordError.value = null;
    changePasswordSuccessMessage.value = null;
  }

  return {
    // Existing
    token, user, isAuthenticated, loginError, registerError, registerSuccessMessage, isLoading,
    getUser, getToken, isUserAuthenticated,
    login, register, logout, tryAutoLogin,
    _setAuthData, _clearAuthData, // Keep internal helpers if needed, or make private if possible with convention _

    // New for profile
    isUpdatingProfile, profileUpdateError, profileUpdateSuccessMessage,
    isChangingPassword, changePasswordError, changePasswordSuccessMessage,
    loadUserProfile, updateUserProfile, changePassword, clearProfileStatusMessages
  };
});
```
