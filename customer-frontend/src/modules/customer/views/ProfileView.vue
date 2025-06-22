<template>
  <div class="profile-view container mx-auto px-4 py-8 max-w-2xl">
    <h2 class="text-3xl font-semibold text-gray-800 text-center mb-8">User Profile & Settings</h2>

    <!-- Edit Profile Section -->
    <div class="card bg-white p-6 rounded-lg shadow-xl mb-8">
      <div class="card-header border-b border-gray-200 pb-4 mb-4">
        <h3 class="text-xl font-semibold text-gray-700">Edit Profile</h3>
      </div>
      <div class="card-body">
        <form @submit.prevent="handleProfileUpdate" class="space-y-4">
          <div v-if="authStore.profileUpdateError" class="p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">{{ authStore.profileUpdateError }}</div>
          <div v-if="authStore.profileUpdateSuccessMessage" class="p-3 bg-green-100 text-green-700 border border-green-400 rounded-md text-sm">{{ authStore.profileUpdateSuccessMessage }}</div>

          <div>
            <label for="username" class="block text-sm font-medium text-gray-700">Username (Login Email):</label>
            <input type="email" class="mt-1 block w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-md shadow-sm sm:text-sm" id="username" :value="user?.username" readonly disabled>
            <p class="mt-1 text-xs text-gray-500">Username (login email) cannot be changed here. Contact support if needed.</p>
          </div>

          <div>
            <label for="profileEmail" class="block text-sm font-medium text-gray-700">Contact Email:</label>
            <input type="email" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" id="profileEmail" v-model="profileForm.email">
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="firstName" class="block text-sm font-medium text-gray-700">First Name:</label>
              <input type="text" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" id="firstName" v-model="profileForm.first_name">
            </div>
            <div>
              <label for="lastName" class="block text-sm font-medium text-gray-700">Last Name:</label>
              <input type="text" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" id="lastName" v-model="profileForm.last_name">
            </div>
          </div>

          <div>
            <label for="phoneNumber" class="block text-sm font-medium text-gray-700">Phone Number:</label>
            <input type="tel" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" id="phoneNumber" v-model="profileForm.phone_number">
          </div>

          <div>
            <label for="address" class="block text-sm font-medium text-gray-700">Address:</label>
            <textarea class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" id="address" v-model="profileForm.address" rows="3"></textarea>
          </div>

          <div class="pt-2">
            <button type="submit"
                    class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="authStore.isUpdatingProfile">
              {{ authStore.isUpdatingProfile ? 'Updating Profile...' : 'Save Profile Changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Change Password Section -->
    <div class="card bg-white p-6 rounded-lg shadow-xl mb-8">
      <div class="card-header border-b border-gray-200 pb-4 mb-4">
        <h3 class="text-xl font-semibold text-gray-700">Change Password</h3>
      </div>
      <div class="card-body">
        <form @submit.prevent="handleChangePassword" class="space-y-4">
          <div v-if="authStore.changePasswordError" class="p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">{{ authStore.changePasswordError }}</div>
          <div v-if="authStore.changePasswordSuccessMessage" class="p-3 bg-green-100 text-green-700 border border-green-400 rounded-md text-sm">{{ authStore.changePasswordSuccessMessage }}</div>
          <div v-if="passwordFormError" class="p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">{{ passwordFormError }}</div>

          <div>
            <label for="currentPassword" class="block text-sm font-medium text-gray-700">Current Password:</label>
            <input type="password" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" id="currentPassword" v-model="passwordForm.current_password" required>
          </div>
          <div>
            <label for="newPassword" class="block text-sm font-medium text-gray-700">New Password:</label>
            <input type="password" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" id="newPassword" v-model="passwordForm.new_password" required>
          </div>
          <div>
            <label for="confirmNewPassword" class="block text-sm font-medium text-gray-700">Confirm New Password:</label>
            <input type="password" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" id="confirmNewPassword" v-model="passwordForm.confirmNewPassword" required>
          </div>

          <div class="pt-2">
            <button type="submit"
                    class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="authStore.isChangingPassword">
              {{ authStore.isChangingPassword ? 'Changing Password...' : 'Change Password' }}
            </button>
          </div>
        </form>
      </div>
    </div>
     <router-link to="/dashboard"
                 class="inline-flex items-center px-4 py-2 mt-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary">
        &larr; Back to Dashboard
    </router-link>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted, watch } from 'vue';
import { useAuthStore } from '@customer/store/auth';
import { storeToRefs } from 'pinia';
import type { UserProfileUpdatePayload } from '@customer/types/user';

export default defineComponent({
  name: 'ProfileView',
  setup() {
    const authStore = useAuthStore();
    const { user, isUpdatingProfile, profileUpdateError, profileUpdateSuccessMessage,
            isChangingPassword, changePasswordError, changePasswordSuccessMessage } = storeToRefs(authStore);

    const profileForm = ref<UserProfileUpdatePayload>({
      email: user.value?.email || '', // Initialize with contact email
      first_name: user.value?.first_name || '',
      last_name: user.value?.last_name || '',
      phone_number: user.value?.phone_number || '',
      address: user.value?.address || '',
    });

    const passwordForm = ref({
      current_password: '',
      new_password: '',
      confirmNewPassword: '',
    });
    const passwordFormError = ref<string | null>(null);

    const populateProfileForm = () => {
      if (user.value) {
        profileForm.value.email = user.value.email || ''; // This should be contact email
        profileForm.value.first_name = user.value.first_name || '';
        profileForm.value.last_name = user.value.last_name || '';
        profileForm.value.phone_number = user.value.phone_number || null; // Ensure null if empty
        profileForm.value.address = user.value.address || null; // Ensure null if empty
      }
    };

    onMounted(async () => {
      authStore.clearProfileStatusMessages();
      if (!user.value || !user.value.first_name) {
          await authStore.loadUserProfile(); // loadUserProfile merges customer data into user store state
      }
      populateProfileForm();
    });

    watch(user, (newUserValue) => {
        if (newUserValue) {
            populateProfileForm();
        }
    }, { deep: true });


    onUnmounted(() => {
      authStore.clearProfileStatusMessages();
    });

    const handleProfileUpdate = async () => {
      if (!profileForm.value.email) { // Example client validation
        authStore.profileUpdateError = "Contact email cannot be empty.";
        return;
      }
      await authStore.updateUserProfile(profileForm.value);
    };

    const handleChangePassword = async () => {
      passwordFormError.value = null;
      authStore.changePasswordError = null; // Clear store error too
      authStore.changePasswordSuccessMessage = null;

      if (passwordForm.value.new_password !== passwordForm.value.confirmNewPassword) {
        passwordFormError.value = 'New passwords do not match.';
        return;
      }
      if (passwordForm.value.new_password.length < 8) {
        passwordFormError.value = 'New password must be at least 8 characters long.';
        return;
      }

      await authStore.changePassword({
        current_password: passwordForm.value.current_password,
        new_password: passwordForm.value.new_password,
      });

      if (!authStore.changePasswordError) { // Clear form only on success from store perspective
        passwordForm.value.current_password = '';
        passwordForm.value.new_password = '';
        passwordForm.value.confirmNewPassword = '';
      }
    };

    return {
      authStore,
      user,
      profileForm,
      passwordForm,
      passwordFormError,
      handleProfileUpdate,
      handleChangePassword,
    };
  },
});
</script>

<style scoped>
/* Using Tailwind classes directly. Add specific overrides if necessary. */
.card {
    /* Tailwind's shadow-xl is quite strong, ensure it fits design */
}
</style>
```
