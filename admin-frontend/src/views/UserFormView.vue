<template>
  <div class="p-6">
    <h1 class="text-2xl font-semibold text-gray-800 mb-4">
      {{ isEditMode ? 'Edit User' : 'Create New User' }}
      <span v-if="isEditMode && userData" class="text-gray-600">- {{ userData.username }}</span>
    </h1>
    <div class="bg-white p-6 rounded-lg shadow">
      <p v-if="isLoading">Loading user data...</p>
      <p v-if="error" class="text-red-500">{{ error }}</p>
      <form v-if="!isLoading && (!isEditMode || (isEditMode && userData))" @submit.prevent="handleSubmit">
        <!-- Username -->
        <div class="mb-4">
          <label for="username" class="block text-sm font-medium text-gray-700">Username (Email for login)</label>
          <input type="email" id="username" v-model="formData.username" required
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
        </div>

        <!-- Email (Contact) -->
        <div class="mb-4">
          <label for="email" class="block text-sm font-medium text-gray-700">Contact Email</label>
          <input type="email" id="email" v-model="formData.email" required
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
        </div>

        <!-- Password -->
        <div class="mb-4">
          <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
          <input type="password" id="password" v-model="formData.password" :placeholder="isEditMode ? 'Leave blank to keep current' : ''" :required="!isEditMode"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
        </div>

        <!-- Role -->
        <div class="mb-4">
          <label for="role_id" class="block text-sm font-medium text-gray-700">Role</label>
          <select id="role_id" v-model="formData.role_id" required
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
            <option value="" disabled>Select role</option>
            <option v-for="role in availableRoles" :key="role.role_id" :value="role.role_id">{{ role.role_name }}</option>
          </select>
        </div>

        <!-- Customer ID (Optional) -->
        <div class="mb-4">
          <label for="customer_id" class="block text-sm font-medium text-gray-700">Link to Customer ID (Optional)</label>
          <input type="number" id="customer_id" v-model.number="formData.customer_id"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm" placeholder="Enter Customer ID">
        </div>

        <!-- Is Active -->
        <div class="mb-4">
          <label class="flex items-center">
            <input type="checkbox" v-model="formData.is_active" class="h-4 w-4 text-admin-primary border-gray-300 rounded focus:ring-admin-primary">
            <span class="ml-2 text-sm text-gray-700">User is Active</span>
          </label>
        </div>

        <div class="flex justify-end space-x-3">
          <router-link :to="{ name: 'AdminUserList' }" class="btn-admin-secondary-outline">Cancel</router-link>
          <button type="submit" class="btn-admin-primary" :disabled="isSubmitting">
            {{ isSubmitting ? (isEditMode ? 'Updating...' : 'Creating...') : (isEditMode ? 'Save Changes' : 'Create User') }}
          </button>
        </div>
        <p v-if="submitError" class="text-red-500 text-sm mt-2">{{ submitError }}</p>
      </form>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import adminApiClient from '@/services/adminApiClient';
import type { UserSchema, AdminUserCreateRequest, AdminUserUpdateRequest } from '@/models'; // Assuming these are in main models

interface Role {
  role_id: number;
  role_name: string;
}

export default defineComponent({
  name: 'UserFormView',
  props: {
    userId: { // Passed from router if in edit mode
      type: String,
      required: false,
    },
  },
  setup(props) {
    const route = useRoute();
    const router = useRouter();

    const isEditMode = computed(() => !!props.userId);
    const userData = ref<UserSchema | null>(null); // For pre-filling form in edit mode
    const formData = ref({
      username: '',
      email: '',
      password: '',
      role_id: '' as string | number, // Allow empty string for initial select state
      customer_id: null as number | null,
      is_active: true,
    });
    const availableRoles = ref<Role[]>([]);

    const isLoading = ref(false);
    const error = ref<string | null>(null);
    const isSubmitting = ref(false);
    const submitError = ref<string | null>(null);

    const fetchUserAndRoles = async () => {
      isLoading.value = true;
      error.value = null;
      try {
        // Fetch roles for dropdown
        const rolesResponse = await adminApiClient.get('/api/admin/lookups/roles'); // Needs this endpoint
        availableRoles.value = rolesResponse.data;

        if (isEditMode.value && props.userId) {
          const response = await adminApiClient.get<UserSchema>(`/api/admin/users/${props.userId}`);
          userData.value = response.data;
          formData.value.username = userData.value.username;
          formData.value.email = userData.value.email;
          formData.value.role_id = userData.value.role_id; // UserSchema should have role_id
          formData.value.customer_id = userData.value.customer_id || null;
          formData.value.is_active = userData.value.is_active;
          // Password not pre-filled
        } else {
            formData.value.is_active = true; // Default for new user
        }
      } catch (err: any) {
        error.value = err.response?.data?.detail || `Failed to load data: ${err.message}`;
      } finally {
        isLoading.value = false;
      }
    };

    const handleSubmit = async () => {
      isSubmitting.value = true;
      submitError.value = null;
      try {
        const payload: AdminUserCreateRequest | AdminUserUpdateRequest = {
          username: formData.value.username,
          email: formData.value.email,
          role_id: Number(formData.value.role_id),
          customer_id: formData.value.customer_id || undefined, // Send undefined if null/empty for Pydantic optional
          is_active: formData.value.is_active,
        };
        if (formData.value.password || !isEditMode.value) {
          if (formData.value.password.length < 8 && !isEditMode.value) { // Basic validation
             submitError.value = "Password must be at least 8 characters for new users.";
             isSubmitting.value = false;
             return;
          }
          if(formData.value.password) (payload as any).password = formData.value.password;
        }

        if (isEditMode.value && props.userId) {
          await adminApiClient.put(`/api/admin/users/${props.userId}`, payload);
        } else {
          await adminApiClient.post('/api/admin/users', payload);
        }
        router.push({ name: 'AdminUserList', query: { success_message: `User ${isEditMode.value ? 'updated' : 'created'} successfully.` } });
      } catch (err: any) {
        submitError.value = err.response?.data?.detail || `Operation failed: ${err.message}`;
      } finally {
        isSubmitting.value = false;
      }
    };

    onMounted(fetchUserAndRoles);

    // Watch for prop changes if navigating between edit forms for different users
    watch(() => props.userId, fetchUserAndRoles);


    return {
      isEditMode,
      userData,
      formData,
      availableRoles,
      isLoading,
      error,
      isSubmitting,
      submitError,
      handleSubmit,
    };
  },
});
</script>

<style scoped>
/* Basic button styles from previous examples, can be global or component-based */
.btn-admin-primary {
  @apply py-2 px-4 bg-admin-primary text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-secondary-outline {
   @apply py-2 px-4 bg-white text-gray-600 border border-gray-300 font-semibold rounded-lg shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-admin-primary focus:ring-opacity-50 disabled:opacity-50;
}
</style>
```
