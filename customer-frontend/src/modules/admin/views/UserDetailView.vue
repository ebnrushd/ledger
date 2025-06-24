<template>
  <div class="user-detail-view p-4 md:p-6 lg:p-8">
    <div v-if="usersStore.isLoadingSingleUser" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-admin-primary mx-auto"></div>
      <p class="mt-3 text-gray-600">Loading user details...</p>
    </div>
    <div v-if="usersStore.singleUserError && !usersStore.isLoadingSingleUser"
         class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 mb-6 rounded-md shadow-md" role="alert">
        <p class="font-bold">Error Loading User</p>
        <p>{{ usersStore.singleUserError }}</p>
         <router-link :to="{ name: 'AdminUserList' }" class="mt-2 inline-block btn-admin-secondary-outline text-sm">
            Back to User List
        </router-link>
    </div>

    <div v-if="user && !usersStore.isLoadingSingleUser && !usersStore.singleUserError" class="max-w-3xl mx-auto">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <div>
            <h1 class="text-2xl md:text-3xl font-semibold text-gray-800">
                User Profile
            </h1>
            <p class="text-gray-600">Details for <span class="font-medium text-admin-primary">{{ user.username }}</span></p>
        </div>
        <router-link :to="{ name: 'AdminUserEdit', params: { userId: user.user_id } }"
                     class="mt-3 sm:mt-0 px-4 py-2 bg-yellow-500 text-white rounded-md shadow hover:bg-yellow-600 transition duration-150 flex items-center text-sm">
          <i class="fas fa-edit mr-2"></i> Edit User
        </router-link>
      </div>

      <div class="bg-white shadow-xl rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <h3 class="text-lg font-medium text-gray-700">Account Information</h3>
        </div>
        <div class="px-6 py-4">
            <dl class="grid grid-cols-1 sm:grid-cols-3 gap-x-4 gap-y-6">
              <div class="sm:col-span-1"><dt class="detail-label">User ID:</dt><dd class="detail-value">{{ user.user_id }}</dd></div>
              <div class="sm:col-span-2"><dt class="detail-label">Username (Login):</dt><dd class="detail-value">{{ user.username }}</dd></div>

              <div class="sm:col-span-1"><dt class="detail-label">Contact Email:</dt><dd class="detail-value">{{ user.email }}</dd></div>
              <div class="sm:col-span-2"><dt class="detail-label">Role:</dt><dd class="detail-value">{{ user.role_name }}</dd></div>

              <div class="sm:col-span-1"><dt class="detail-label">Status:</dt>
                <dd class="detail-value">
                  <span :class="['px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full', user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
                    {{ user.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </dd>
              </div>
              <div class="sm:col-span-2"><dt class="detail-label">Linked Customer ID:</dt>
                <dd class="detail-value">
                  <router-link v-if="user.customer_id" :to="{ name: 'AdminCustomerDetail', params: { customerId: user.customer_id } }" class="text-admin-primary hover:underline">
                    {{ user.customer_id }}
                  </router-link>
                  <span v-else>N/A</span>
                </dd>
              </div>

              <div class="sm:col-span-1"><dt class="detail-label">Created At:</dt><dd class="detail-value">{{ new Date(user.created_at).toLocaleString() }}</dd></div>
              <div class="sm:col-span-2"><dt class="detail-label">Last Login:</dt><dd class="detail-value">{{ user.last_login ? new Date(user.last_login).toLocaleString() : 'Never' }}</dd></div>
            </dl>
        </div>
      </div>
       <div class="mt-8 text-center">
            <router-link :to="{ name: 'AdminUserList' }"
                         class="px-6 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition">
                <i class="fas fa-arrow-left mr-2"></i> Back to User List
            </router-link>
        </div>
    </div>
    <div v-else-if="!usersStore.isLoadingSingleUser && !usersStore.singleUserError && !user" class="text-center py-10">
        <p class="text-xl text-gray-500">User not found.</p>
         <router-link :to="{ name: 'AdminUserList' }" class="mt-4 inline-block btn-admin-secondary-outline text-sm">
            Back to User List
        </router-link>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed, onUnmounted } from 'vue';
import { useRoute } from 'vue-router'; // Or use props
import { useAdminUsersStore } from '@admin/store/adminUsers';
import { storeToRefs } from 'pinia';

export default defineComponent({
  name: 'UserDetailView',
  props: {
    userId: {
      type: [String, Number],
      required: true,
    },
  },
  setup(props) {
    const usersStore = useAdminUsersStore();
    // Use storeToRefs to get reactive access to selectedUser, isLoadingSingleUser, singleUserError
    const { selectedUser: user, isLoadingSingleUser, singleUserError } = storeToRefs(usersStore);

    onMounted(async () => {
      // Clear any previous selection or error before fetching
      usersStore.selectedUser = null;
      usersStore.singleUserError = null;
      await usersStore.fetchUser(props.userId);
    });

    onUnmounted(() => {
        // Clear selected user when leaving the page to avoid showing stale data briefly
        usersStore.selectedUser = null;
    });

    return {
      user, // This is usersStore.selectedUser now reactive via storeToRefs
      isLoading: isLoadingSingleUser, // For template clarity
      error: singleUserError, // For template clarity
      usersStore, // To access other parts of store if needed, or for template direct access
    };
  },
});
</script>

<style scoped>
.detail-label {
  @apply text-sm font-medium text-gray-500;
}
.detail-value {
  @apply text-sm text-gray-900 mt-1 sm:mt-0;
}
/* Reusable button styles (can be global or component-based) */
.btn-admin-primary {
  @apply py-2 px-4 bg-admin-primary text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75;
}
.btn-admin-secondary-outline {
   @apply py-2 px-4 bg-white text-gray-600 border border-gray-300 font-semibold rounded-lg shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-admin-primary focus:ring-opacity-50;
}
</style>
```
