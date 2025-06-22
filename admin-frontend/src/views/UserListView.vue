<template>
  <div class="user-list-view p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-semibold text-gray-800">User Management</h1>
      <router-link :to="{ name: 'AdminUserCreateForm' }" class="btn-admin-primary">
        <i class="fas fa-plus mr-2"></i> Add New User
      </router-link>
    </div>

    <!-- Filters/Search -->
    <div class="bg-white p-4 rounded-lg shadow mb-6">
      <form @submit.prevent="applyFilters" class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
        <div>
          <label for="search" class="block text-sm font-medium text-gray-700">Search:</label>
          <input type="text" id="search" v-model="filterState.searchQuery"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm"
                 placeholder="Username, email, role...">
        </div>
        <div>
          <label for="role" class="block text-sm font-medium text-gray-700">Role:</label>
          <select id="role" v-model="filterState.roleFilter"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
            <option value="">All Roles</option>
            <!-- Populate roles dynamically from store or API if needed -->
            <option value="admin">Admin</option>
            <option value="teller">Teller</option>
            <option value="customer">Customer</option>
            <option value="auditor">Auditor</option>
          </select>
        </div>
        <div class="md:col-span-1 flex items-end space-x-2">
          <button type="submit" class="btn-admin-primary w-full md:w-auto">Filter</button>
          <button type="button" @click="clearFilters" class="btn-admin-secondary w-full md:w-auto">Clear</button>
        </div>
      </form>
    </div>

    <div v-if="isLoading" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-admin-primary mx-auto"></div>
    </div>
    <div v-if="error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md">{{ error }}</div>

    <div v-if="!isLoading && !error && userListResponse" class="bg-white p-2 rounded-lg shadow-xl">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="user in userListResponse.users" :key="user.user_id" class="hover:bg-gray-50">
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ user.user_id }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{{ user.username }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ user.email }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ user.role_name }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm">
                <span :class="['px-2 inline-flex text-xs leading-5 font-semibold rounded-full', user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
                  {{ user.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm font-medium">
                <router-link :to="{ name: 'AdminUserDetail', params: { userId: user.user_id } }" class="text-admin-accent hover:underline mr-3">View</router-link>
                <router-link :to="{ name: 'AdminUserEdit', params: { userId: user.user_id } }" class="text-indigo-600 hover:text-indigo-900">Edit</router-link> {/* Updated route name */}
              </td>
            </tr>
            <tr v-if="userListResponse.users.length === 0">
                <td colspan="6" class="text-center text-gray-500 py-4">No users found matching your criteria.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Pagination -->
      <div v-if="userListResponse.total_pages > 1" class="py-4 px-2 flex justify-between items-center text-sm">
        <button @click="changePage(userListResponse.page - 1)" :disabled="userListResponse.page <= 1"
                class="btn-admin-secondary-outline">Previous</button>
        <span>Page {{ userListResponse.page }} of {{ userListResponse.total_pages }} ({{ userListResponse.total_items }} users)</span>
        <button @click="changePage(userListResponse.page + 1)" :disabled="userListResponse.page >= userListResponse.total_pages"
                class="btn-admin-secondary-outline">Next</button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, reactive, watch } from 'vue';
import adminApiClient from '@/services/adminApiClient';
import type { AdminUserListResponse, UserSchema } from '@/models'; // Assuming AdminUserListResponse is in main models
import { useRouter, useRoute } from 'vue-router';

export default defineComponent({
  name: 'UserListView',
  setup() {
    const router = useRouter();
    const route = useRoute();

    const userListResponse = ref<AdminUserListResponse | null>(null);
    const isLoading = ref(true);
    const error = ref<string | null>(null);

    const filterState = reactive({
        searchQuery: route.query.search_query as string || '',
        roleFilter: route.query.role_filter as string || '',
        currentPage: Number(route.query.page) || 1
    });

    const fetchUsers = async (page = filterState.currentPage) => {
      isLoading.value = true;
      error.value = null;
      filterState.currentPage = page; // Ensure current page is updated
      try {
        const params = new URLSearchParams();
        params.append('page', String(page));
        params.append('per_page', '10'); // Or make this configurable
        if (filterState.searchQuery) params.append('search_query', filterState.searchQuery);
        if (filterState.roleFilter) params.append('role_filter', filterState.roleFilter); // Backend needs to support this

        // Update router query without navigation for bookmarkable filters
        router.replace({ query: { ...route.query, ...filterState } });

        const response = await adminApiClient.get<AdminUserListResponse>('/api/admin/users', { params });
        userListResponse.value = response.data;
      } catch (err: any) {
        error.value = err.response?.data?.detail || 'Failed to fetch users.';
        console.error('Error fetching users:', err);
      } finally {
        isLoading.value = false;
      }
    };

    const applyFilters = () => {
        fetchUsers(1); // Reset to page 1 when applying new filters
    };

    const clearFilters = () => {
        filterState.searchQuery = '';
        filterState.roleFilter = '';
        fetchUsers(1);
    };

    const changePage = (newPage: number) => {
        if (newPage > 0 && userListResponse.value && newPage <= userListResponse.value.total_pages) {
            fetchUsers(newPage);
        }
    };

    onMounted(() => {
        fetchUsers();
    });

    // Watch for route query changes if you want to re-fetch when browser back/forward used with filters
    // watch(() => route.query, () => { fetchUsers(Number(route.query.page) || 1); }, { deep: true });


    return {
      userListResponse,
      isLoading,
      error,
      filterState,
      applyFilters,
      clearFilters,
      changePage,
    };
  },
});
</script>

<style scoped>
/* Reusable button styles (consider moving to a global stylesheet or base component if used often) */
.btn-admin-primary {
  @apply py-2 px-4 bg-admin-primary text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-secondary {
   @apply py-2 px-4 bg-gray-500 text-white font-semibold rounded-lg shadow-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-secondary-outline {
   @apply py-2 px-4 bg-white text-gray-600 border border-gray-300 font-semibold rounded-lg shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-admin-primary focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed;
}
/* Font Awesome icons need to be included in index.html or via main.ts */
</style>
```
