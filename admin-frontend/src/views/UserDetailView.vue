<template>
  <div class="p-6">
    <div v-if="isLoading" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-admin-primary mx-auto"></div>
      <p class="mt-2 text-gray-600">Loading user details...</p>
    </div>
    <div v-if="error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md">
        <p class="font-bold">Error</p>
        <p>{{ error }}</p>
    </div>

    <div v-if="user && !isLoading && !error">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-semibold text-gray-800">
            User Profile: <span class="text-admin-primary">{{ user.username }}</span>
        </h1>
        <router-link :to="{ name: 'AdminUserEditForm', params: { userId: user.user_id } }" class="btn-admin-primary">
          <i class="fas fa-edit mr-2"></i> Edit User
        </router-link>
      </div>

      <div class="bg-white shadow-xl rounded-lg p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 class="text-lg font-medium text-gray-700 mb-2">Account Information</h3>
            <dl class="space-y-2">
              <div class="flex">
                <dt class="w-1/3 text-sm font-medium text-gray-500">User ID:</dt>
                <dd class="w-2/3 text-sm text-gray-900">{{ user.user_id }}</dd>
              </div>
              <div class="flex">
                <dt class="w-1/3 text-sm font-medium text-gray-500">Username:</dt>
                <dd class="w-2/3 text-sm text-gray-900">{{ user.username }}</dd>
              </div>
              <div class="flex">
                <dt class="w-1/3 text-sm font-medium text-gray-500">Email:</dt>
                <dd class="w-2/3 text-sm text-gray-900">{{ user.email }}</dd>
              </div>
            </dl>
          </div>
          <div>
            <h3 class="text-lg font-medium text-gray-700 mb-2">Role & Status</h3>
            <dl class="space-y-2">
              <div class="flex">
                <dt class="w-1/3 text-sm font-medium text-gray-500">Role:</dt>
                <dd class="w-2/3 text-sm text-gray-900">{{ user.role_name }}</dd>
              </div>
              <div class="flex">
                <dt class="w-1/3 text-sm font-medium text-gray-500">Status:</dt>
                <dd class="w-2/3 text-sm">
                  <span :class="['px-2 inline-flex text-xs leading-5 font-semibold rounded-full', user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
                    {{ user.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </dd>
              </div>
              <div class="flex">
                <dt class="w-1/3 text-sm font-medium text-gray-500">Linked Customer ID:</dt>
                <dd class="w-2/3 text-sm text-gray-900">
                  <router-link v-if="user.customer_id" :to="{ name: 'AdminCustomerDetail', params: { customerId: user.customer_id } }" class="text-admin-primary hover:underline">
                    {{ user.customer_id }}
                  </router-link>
                  <span v-else>N/A</span>
                </dd>
              </div>
            </dl>
          </div>
          <div>
            <h3 class="text-lg font-medium text-gray-700 mb-2">Timestamps</h3>
            <dl class="space-y-2">
              <div class="flex">
                <dt class="w-1/3 text-sm font-medium text-gray-500">Created At:</dt>
                <dd class="w-2/3 text-sm text-gray-900">{{ new Date(user.created_at).toLocaleString() }}</dd>
              </div>
              <div class="flex">
                <dt class="w-1/3 text-sm font-medium text-gray-500">Last Login:</dt>
                <dd class="w-2/3 text-sm text-gray-900">{{ user.last_login ? new Date(user.last_login).toLocaleString() : 'Never' }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
       <div class="mt-6">
            <router-link :to="{ name: 'AdminUserList' }" class="btn-admin-secondary-outline">
                <i class="fas fa-arrow-left mr-2"></i> Back to User List
            </router-link>
        </div>
    </div>
    <div v-else-if="!isLoading && !error">
        <p class="text-center text-gray-500">User not found.</p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import adminApiClient from '@/services/adminApiClient';
import type { UserSchema } from '@/models'; // Assuming UserSchema is in main models

export default defineComponent({
  name: 'UserDetailView',
  props: {
    userId: {
      type: [String, Number],
      required: true,
    },
  },
  setup(props) {
    const route = useRoute(); // For params if not using props, but props is better
    const user = ref<UserSchema | null>(null);
    const isLoading = ref(true);
    const error = ref<string | null>(null);

    const fetchUserDetails = async () => {
      isLoading.value = true;
      error.value = null;
      try {
        const response = await adminApiClient.get<UserSchema>(`/api/admin/users/${props.userId}`);
        user.value = response.data;
      } catch (err: any) {
        error.value = err.response?.data?.detail || `Failed to load user details: ${err.message}`;
        console.error(`Error fetching user ${props.userId}:`, err);
      } finally {
        isLoading.value = false;
      }
    };

    onMounted(fetchUserDetails);

    // Optional: Watch for prop changes if the same component instance might be reused
    // watch(() => props.userId, fetchUserDetails);

    return {
      user,
      isLoading,
      error,
    };
  },
});
</script>

<style scoped>
/* Using Tailwind, but if custom button styles were defined in UserListView, they could be here too or global */
.btn-admin-primary {
  @apply py-2 px-4 bg-admin-primary text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75;
}
.btn-admin-secondary-outline {
   @apply py-2 px-4 bg-white text-gray-600 border border-gray-300 font-semibold rounded-lg shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-admin-primary focus:ring-opacity-50;
}
</style>
```
