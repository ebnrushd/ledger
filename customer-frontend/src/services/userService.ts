import apiClient from './apiClient';
import type { User, UserProfileUpdatePayload } from '@/types/user'; // Import User and new payload type

interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

// This User type is what the API /users/me should return.
// It might be slightly different from what's stored in Pinia if Pinia merges data.
// For now, assuming User type is consistent.

const fetchUserProfile = async (): Promise<User> => {
  try {
    // Assuming backend has a /api/v1/users/me endpoint that returns User data
    // If not, this might need to call /api/v1/customers/me and merge with user data from token/authStore
    // For this task, let's assume /api/v1/users/me exists and returns comprehensive User data.
    // If there isn't a dedicated /api/v1/users/me, the authStore.user (populated from token
    // and potentially a /customers/me call) might be the source of truth for "profile".
    // Let's assume for now we need to create a /api/v1/users/me endpoint on the backend.
    // If this endpoint is not part of this subtask's backend scope, this function will be a placeholder.

    // Placeholder if /api/v1/users/me is not yet defined for GET:
    // For now, we'll simulate by assuming that the customer profile is the primary "user profile" for v1 users.
    // This means we will fetch from /api/v1/customers/me.
    // The authStore already holds user_id, username, role from token.
    // This function would then enrich it with customer details.

    // If there was a dedicated /api/v1/users/me endpoint:
    // const response = await apiClient.get<User>('/users/me');
    // return response.data;

    // Simulating: In reality, this data would come from a dedicated backend endpoint.
    // For now, this service will be more about *updating* data.
    // Fetching the profile is primarily done on login (token decode) and then potentially customer details.
    // Let's make this a placeholder that would call such an endpoint.
    console.warn("fetchUserProfile called, but relies on a hypothetical /api/v1/users/me endpoint or similar for full profile data beyond token/customer profile.");
    // This function might not be strictly needed if authStore.user is kept up-to-date from token + customer/me calls.
    // It's more for a scenario where user table has more editable fields than just email.

    // Fallback: if no single /users/me, then profile view will construct from authStore.user + separate customer fetch.
    // For now, this function can be a no-op or throw indicating it needs a proper backend endpoint.
    return Promise.reject(new Error("Dedicated /api/v1/users/me endpoint for fetching full profile is not assumed to exist for this service function. Profile data is built from token and /customers/me."));

  } catch (error) {
    console.error('Error fetching user profile:', error);
    throw error;
  }
};

const updateUserProfile = async (profileData: UserProfileUpdatePayload): Promise<User> => {
  // This will primarily update the linked Customer record via /api/v1/customers/me
  // If `email` is part of UserProfileUpdatePayload and refers to `users.email`,
  // then a separate call to a /api/v1/users/me (PUT) would be needed for that.
  // For this subtask, assume UserProfileUpdatePayload contains fields for the *customer* aspect.
  try {
    const response = await apiClient.put<User>('/customers/me', profileData); // Assuming User type is returned
    return response.data;
  } catch (error) {
    console.error('Error updating user profile:', error);
    throw error;
  }
};

const changePassword = async (passwordData: ChangePasswordPayload): Promise<any> => { // Replace 'any' with specific response type
  try {
    // Assumes backend endpoint /api/v1/users/me/change-password or similar
    // The backend API spec mentions /api/v1/auth/change-password - let's use that if it was a typo in prompt.
    // For now, sticking to prompt's /api/v1/users/me/change-password.
    // This needs to be created in the backend if it doesn't exist.
    const response = await apiClient.post('/users/me/change-password', passwordData);
    return response.data; // Expects success message or updated user
  } catch (error) {
    console.error('Error changing password:', error);
    throw error;
  }
};

const userService = {
  fetchUserProfile, // Placeholder - needs backend endpoint
  updateUserProfile,
  changePassword,
};

export default userService;
```
