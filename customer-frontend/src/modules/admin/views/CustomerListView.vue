<template>
  <div class="customer-list-view p-4 md:p-6 lg:p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl md:text-3xl font-semibold text-gray-800">Customer Management</h1>
      <!-- No "Add Customer" button here as per spec (view-only for customers in admin) -->
    </div>

    <!-- Filters/Search -->
    <div class="bg-white p-4 rounded-lg shadow-md mb-6">
      <form @submit.prevent="applyFiltersAndSearch" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 items-end">
        <div>
          <label for="search" class="block text-sm font-medium text-gray-700">Search:</label>
          <input type="text" id="search" v-model="filterState.searchQuery"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm"
                 placeholder="Name, email, Customer ID...">
        </div>
        <div class="col-span-1 sm:col-span-2 md:col-span-1 flex items-end space-x-2">
          <button type="submit"
                  class="w-full sm:w-auto px-4 py-2 bg-admin-primary text-white rounded-md shadow hover:bg-blue-700 transition duration-150">Search</button>
          <button type="button" @click="clearAllFilters"
                  class="w-full sm:w-auto px-4 py-2 bg-gray-200 text-gray-700 rounded-md shadow hover:bg-gray-300 transition duration-150">Clear</button>
        </div>
      </form>
    </div>

    <div v-if="customersStore.isLoadingCustomers" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-admin-primary mx-auto"></div>
      <p class="mt-3 text-gray-600">Loading customers...</p>
    </div>
    <div v-if="customersStore.error && !customersStore.isLoadingCustomers"
         class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 mb-6 rounded-md shadow-md" role="alert">
        <p class="font-bold">Error Loading Customers</p>
        <p>{{ customersStore.error }}</p>
    </div>

    <div v-if="!customersStore.isLoadingCustomers && !customersStore.error && customersStore.customers" class="bg-white rounded-lg shadow-xl overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-100">
            <tr>
              <th class="table-header">ID</th>
              <th class="table-header">Name</th>
              <th class="table-header">Email</th>
              <th class="table-header">Phone</th>
              <th class="table-header">Linked User</th>
              <th class="table-header text-center"># Accounts</th>
              <th class="table-header">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="customer in customersStore.customers" :key="customer.customer_id" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell">{{ customer.customer_id }}</td>
              <td class="table-cell font-medium text-gray-900">{{ customer.first_name }} {{ customer.last_name }}</td>
              <td class="table-cell">{{ customer.email }}</td>
              <td class="table-cell">{{ customer.phone_number || 'N/A' }}</td>
              <td class="table-cell">
                <span v-if="customer.linked_user_username">{{ customer.linked_user_username }}</span>
                <span v-else class="text-gray-400 italic">None</span>
              </td>
              <td class="table-cell text-center">{{ customer.account_count || 0 }}</td>
              <td class="table-cell space-x-2 whitespace-nowrap">
                <router-link :to="{ name: 'AdminCustomerDetail', params: { customerId: customer.customer_id } }"
                             class="px-3 py-1 text-xs font-medium text-white bg-blue-500 rounded hover:bg-blue-600 transition">View Details</router-link>
              </td>
            </tr>
            <tr v-if="customersStore.customers.length === 0">
                <td colspan="7" class="text-center text-gray-500 py-6">No customers found matching your criteria.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Pagination -->
      <div v-if="customersStore.totalPages > 1" class="py-4 px-4 flex justify-between items-center text-sm text-gray-600 bg-gray-50 border-t">
        <button @click="changePage(customersStore.currentPage - 1)" :disabled="customersStore.currentPage <= 1"
                class="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
          Previous
        </button>
        <span>Page {{ customersStore.currentPage }} of {{ customersStore.totalPages }} (Total: {{ customersStore.totalItems }} customers)</span>
        <button @click="changePage(customersStore.currentPage + 1)" :disabled="customersStore.currentPage >= customersStore.totalPages"
                class="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, reactive, watch } from 'vue';
import { useAdminCustomersStore } from '@/store/adminCustomers';
import { storeToRefs } from 'pinia'; // Optional, for cleaner access to reactive props
import { useRouter, useRoute } from 'vue-router';

export default defineComponent({
  name: 'CustomerListView',
  setup() {
    const customersStore = useAdminCustomersStore();
    const router = useRouter();
    const route = useRoute();

    // Use storeToRefs if you want to destructure store state/getters while keeping reactivity
    // const { customers, isLoadingCustomers, error, currentPage, totalPages, totalItems } = storeToRefs(customersStore);

    const filterState = reactive({
        searchQuery: (route.query.search_query as string) || '',
        currentPage: Number(route.query.page) || 1
    });

    const fetchCustomerList = (page = filterState.currentPage) => {
      filterState.currentPage = page;
      const filters = {
          search_query: filterState.searchQuery,
      };
      customersStore.fetchCustomers(page, customersStore.itemsPerPage, filters);
    };

    const applyFiltersAndSearch = () => {
        const query: any = { page: '1' };
        if (filterState.searchQuery) query.search_query = filterState.searchQuery;
        // No other filters for now, but could add them here
        router.push({ query });
        // Watcher will trigger fetchCustomerList due to query change
    };

    const clearAllFilters = () => {
        filterState.searchQuery = '';
        router.push({ query: {} }); // Clear query params
        // Watcher will trigger fetchCustomerList
    };

    const changePage = (newPage: number) => {
        if (newPage > 0 && newPage <= customersStore.totalPages) {
            filterState.currentPage = newPage;
            router.push({ query: { ...route.query, page: String(newPage) } });
            // Watcher will trigger fetchCustomerList
        }
    };

    watch(() => route.query, (newQuery) => {
        filterState.searchQuery = (newQuery.search_query as string) || '';
        filterState.currentPage = Number(newQuery.page) || 1;
        fetchCustomerList(filterState.currentPage);
    }, { deep: true });


    onMounted(() => {
        customersStore.clearError(); // Clear previous errors
        fetchCustomerList(); // Initial fetch based on current route query or defaults
    });

    return {
      customersStore, // Provide store directly to template
      filterState,
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
.btn-admin-primary, .btn-admin-secondary-outline { /* Define if not global */
  @apply py-2 px-4 font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-primary { @apply bg-admin-primary text-white hover:bg-blue-700 focus:ring-blue-500; }
.btn-admin-secondary-outline { @apply bg-white text-gray-600 border border-gray-300 hover:bg-gray-50 focus:ring-admin-primary; }
</style>
```
