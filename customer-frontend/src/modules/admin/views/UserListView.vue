<template>
  <div class="user-list-view p-4 md:p-6 lg:p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl md:text-3xl font-semibold text-gray-800">User Management</h1>
      <router-link :to="{ name: 'AdminUserCreate' }"
                   class="px-4 py-2 bg-admin-primary text-white rounded-md shadow hover:bg-blue-700 transition duration-150 flex items-center">
        <i class="fas fa-plus mr-2"></i> Add New User
      </router-link>
    </div>

    <!-- Filters/Search -->
    <div class="bg-white p-4 rounded-lg shadow-md mb-6">
      <form @submit.prevent="applyFiltersAndSearch" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 items-end">
        <div>
          <label for="search" class="block text-sm font-medium text-gray-700">Search:</label>
          <input type="text" id="search" v-model="filterState.searchQuery"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm"
                 placeholder="Username, email...">
        </div>
        <div>
          <label for="role" class="block text-sm font-medium text-gray-700">Role:</label>
          <select id="role" v-model="filterState.roleFilter"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
            <option value="">All Roles</option>
            <option v-for="role in rolesStore.roles" :key="role.role_id" :value="role.role_name">
              {{ role.role_name.charAt(0).toUpperCase() + role.role_name.slice(1) }}
            </option>
          </select>
        </div>
        <div class="col-span-1 sm:col-span-2 md:col-span-1 flex items-end space-x-2">
          <button type="submit"
                  class="w-full sm:w-auto px-4 py-2 bg-admin-primary text-white rounded-md shadow hover:bg-blue-700 transition duration-150">Filter</button>
          <button type="button" @click="clearAllFilters"
                  class="w-full sm:w-auto px-4 py-2 bg-gray-200 text-gray-700 rounded-md shadow hover:bg-gray-300 transition duration-150">Clear</button>
        </div>
      </form>
    </div>

    <div v-if="usersStore.isLoadingUsers" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-admin-primary mx-auto"></div>
      <p class="mt-3 text-gray-600">Loading users...</p>
    </div>
    <div v-if="usersStore.usersError"
         class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 mb-6 rounded-md shadow-md" role="alert">
        <p class="font-bold">Error Loading Users</p>
        <p>{{ usersStore.usersError }}</p>
    </div>

    <div v-if="!usersStore.isLoadingUsers && !usersStore.usersError && usersStore.users" class="bg-white rounded-lg shadow-xl overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-100">
            <tr>
              <th class="table-header">ID</th>
              <th class="table-header">Username</th>
              <th class="table-header">Email</th>
              <th class="table-header">Role</th>
              <th class="table-header">Status</th>
              <th class="table-header">Customer ID</th>
              <th class="table-header">Created At</th>
              <th class="table-header">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="user in usersStore.users" :key="user.user_id" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell">{{ user.user_id }}</td>
              <td class="table-cell font-medium text-gray-900">{{ user.username }}</td>
              <td class="table-cell">{{ user.email }}</td>
              <td class="table-cell">{{ user.role_name }}</td>
              <td class="table-cell">
                <span :class="['px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full', user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
                  {{ user.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td class="table-cell">
                <router-link v-if="user.customer_id" :to="{ name: 'AdminCustomerDetail', params: { customerId: user.customer_id } }" class="text-admin-primary hover:underline">
                    {{ user.customer_id }}
                </router-link>
                <span v-else>N/A</span>
              </td>
              <td class="table-cell">{{ new Date(user.created_at).toLocaleDateString() }}</td>
              <td class="table-cell space-x-2 whitespace-nowrap">
                <router-link :to="{ name: 'AdminUserDetail', params: { userId: user.user_id } }"
                             class="px-3 py-1 text-xs font-medium text-white bg-blue-500 rounded hover:bg-blue-600 transition">View</router-link>
                <router-link :to="{ name: 'AdminUserEdit', params: { userId: user.user_id } }"
                             class="px-3 py-1 text-xs font-medium text-white bg-yellow-500 rounded hover:bg-yellow-600 transition">Edit</router-link>
              </td>
            </tr>
            <tr v-if="usersStore.users.length === 0">
                <td colspan="8" class="text-center text-gray-500 py-6">No users found matching your criteria.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Pagination -->
      <div v-if="usersStore.totalPages > 1" class="py-4 px-4 flex justify-between items-center text-sm text-gray-600 bg-gray-50 border-t">
        <button @click="changePage(usersStore.currentPage - 1)" :disabled="usersStore.currentPage <= 1"
                class="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
          Previous
        </button>
        <span>Page {{ usersStore.currentPage }} of {{ usersStore.totalPages }} (Total: {{ usersStore.totalItems }} users)</span>
        <button @click="changePage(usersStore.currentPage + 1)" :disabled="usersStore.currentPage >= usersStore.totalPages"
                class="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, reactive, watch } from 'vue';
import { useAdminUsersStore } from '@/store/adminUsers';
import { storeToRefs } from 'pinia';
import { useRouter, useRoute } from 'vue-router';

export default defineComponent({
  name: 'UserListView',
  setup() {
    const usersStore = useAdminUsersStore();
    const router = useRouter();
    const route = useRoute();

    // Use storeToRefs for reactive access to parts of the store state if needed,
    // but for lists and pagination, accessing via usersStore.property in template is often fine.
    // const { users, isLoadingUsers, usersError, currentPage, totalPages, totalItems } = storeToRefs(usersStore);
    // For roles, we need to fetch them.
    const rolesStore = useAdminUsersStore(); // Can use same store instance if roles are there.
                                         // Or if roles are in a separate store: const rolesStore = useRolesStore();

    const filterState = reactive({
        searchQuery: (route.query.search_query as string) || '',
        roleFilter: (route.query.role_filter as string) || '', // Assuming role_name for filter
        currentPage: Number(route.query.page) || 1
    });

    const fetchUsersList = (page = filterState.currentPage) => {
      filterState.currentPage = page;
      const filters = {
          search_query: filterState.searchQuery,
          role_filter: filterState.roleFilter,
          // Backend `list_users` expects role_filter as string (role_name)
      };
      // Update URL query params without triggering full navigation / re-running setup if possible
      // router.replace({ query: { ...route.query, ...filterState } }); // This might re-trigger watch/onMounted if not careful
      usersStore.fetchUsers(page, usersStore.itemsPerPage, filters);
    };

    const applyFiltersAndSearch = () => {
        // Update query params to make filters bookmarkable before fetching
        const query = { ...route.query, page: '1' }; // Reset to page 1 on new filter
        if (filterState.searchQuery) query.search_query = filterState.searchQuery; else delete query.search_query;
        if (filterState.roleFilter) query.role_filter = filterState.roleFilter; else delete query.role_filter;
        router.push({ query }); // This will trigger the watcher below if query changes
        // fetchUsersList(1); // Fetch directly if watcher is not robust for all cases
    };

    const clearAllFilters = () => {
        filterState.searchQuery = '';
        filterState.roleFilter = '';
        // router.push({ query: {} }); // Clear query params, will trigger watcher
        applyFiltersAndSearch(); // Or call this, which also updates query
    };

    const changePage = (newPage: number) => {
        if (newPage > 0 && newPage <= usersStore.totalPages) {
            filterState.currentPage = newPage;
            // Update just the page query parameter
            router.push({ query: { ...route.query, page: String(newPage) } });
            // fetchUsersList(newPage); // Watcher on route.query should handle this
        }
    };

    // Watch for route query changes to re-fetch data (e.g. from pagination clicking)
    watch(() => route.query, (newQuery) => {
        filterState.searchQuery = (newQuery.search_query as string) || '';
        filterState.roleFilter = (newQuery.role_filter as string) || '';
        filterState.currentPage = Number(newQuery.page) || 1;
        fetchUsersList(filterState.currentPage);
    }, { deep: true });


    onMounted(() => {
        usersStore.fetchRoles(); // Fetch roles for the filter dropdown
        fetchUsersList(); // Initial fetch based on current route query or defaults
    });

    return {
      usersStore, // Provide store directly to template for users, isLoading, error, pagination
      filterState,
      rolesStore, // For roles in dropdown
      applyFiltersAndSearch,
      clearAllFilters,
      changePage,
    };
  },
});
</script>

<style scoped>
.table-header {
  @apply px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-100;
}
.table-cell {
  @apply px-4 py-3 whitespace-nowrap text-sm text-gray-700;
}
/* Reusable button styles (can be global or component-based) */
.btn-admin-primary {
  @apply py-2 px-4 bg-admin-primary text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-secondary-outline {
   @apply py-2 px-4 bg-white text-gray-600 border border-gray-300 font-semibold rounded-lg shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-admin-primary focus:ring-opacity-75 disabled:opacity-50 disabled:cursor-not-allowed;
}
.btn-admin-secondary {
   @apply py-2 px-4 bg-gray-200 text-gray-700 font-semibold rounded-lg shadow-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-opacity-75 disabled:opacity-50;
}
</style>
```
