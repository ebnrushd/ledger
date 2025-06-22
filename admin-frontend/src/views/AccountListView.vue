<template>
  <div class="account-list-view p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-semibold text-gray-800">Account Management</h1>
      <!-- No "Add New Account" button for admin here, usually accounts are opened via customer context or specific processes -->
    </div>

    <!-- Filters/Search -->
    <div class="bg-white p-4 rounded-lg shadow mb-6">
      <form @submit.prevent="applyFilters" class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 items-end">
        <div>
          <label for="search" class="block text-sm font-medium text-gray-700">Search:</label>
          <input type="text" id="search" v-model="filterState.searchQuery"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm"
                 placeholder="Acc #, Cust ID, Name, Email...">
        </div>
        <div>
          <label for="status" class="block text-sm font-medium text-gray-700">Status:</label>
          <select id="status" v-model="filterState.statusFilter"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
            <option value="">All Statuses</option>
            <option v-for="status in availableStatuses" :key="status.status_id" :value="status.status_name">
              {{ status.status_name.charAt(0).toUpperCase() + status.status_name.slice(1) }}
            </option>
          </select>
        </div>
        <div>
          <label for="type" class="block text-sm font-medium text-gray-700">Account Type:</label>
          <select id="type" v-model="filterState.accountTypeFilter"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
            <option value="">All Types</option>
            <option v-for="accType in availableAccountTypes" :key="accType" :value="accType">
              {{ accType.charAt(0).toUpperCase() + accType.slice(1) }}
            </option>
          </select>
        </div>
        <div class="flex items-end space-x-2">
          <button type="submit" class="btn-admin-primary w-full md:w-auto">Filter</button>
          <button type="button" @click="clearFilters" class="btn-admin-secondary w-full md:w-auto">Clear</button>
        </div>
      </form>
    </div>

    <div v-if="isLoading" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-admin-primary mx-auto"></div>
    </div>
    <div v-if="error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md">{{ error }}</div>

    <div v-if="!isLoading && !error && accountListResponse" class="bg-white p-2 rounded-lg shadow-xl">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Account #</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Balance</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Overdraft Limit</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="account in accountListResponse.accounts" :key="account.account_id" class="hover:bg-gray-50">
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ account.account_id }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{{ account.account_number }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                <router-link :to="{ name: 'AdminCustomerDetail', params: { customerId: account.customer_id } }" class="text-admin-primary hover:underline">
                  {{ account.customer_first_name }} {{ account.customer_last_name }} (ID: {{ account.customer_id }})
                </router-link>
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1) }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-right tabular-nums">{{ account.balance.toFixed(2) }} {{ account.currency }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm">
                <span :class="['px-2 inline-flex text-xs leading-5 font-semibold rounded-full', accountStatusClass(account.status_name)]">
                  {{ account.status_name.replace("_", " ")|title }}
                </span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-right tabular-nums">{{ account.overdraft_limit.toFixed(2) }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm font-medium">
                <router-link :to="{ name: 'AdminAccountDetail', params: { accountId: account.account_id } }" class="text-admin-accent hover:underline">View</router-link>
              </td>
            </tr>
             <tr v-if="accountListResponse.accounts.length === 0">
                <td colspan="8" class="text-center text-gray-500 py-4">No accounts found matching your criteria.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Pagination -->
       <div v-if="accountListResponse.total_pages > 1" class="py-4 px-2 flex justify-between items-center text-sm">
        <button @click="changePage(accountListResponse.page - 1)" :disabled="accountListResponse.page <= 1"
                class="btn-admin-secondary-outline">Previous</button>
        <span>Page {{ accountListResponse.page }} of {{ accountListResponse.total_pages }} ({{ accountListResponse.total_items }} accounts)</span>
        <button @click="changePage(accountListResponse.page + 1)" :disabled="accountListResponse.page >= accountListResponse.total_pages"
                class="btn-admin-secondary-outline">Next</button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, reactive } from 'vue';
import adminApiClient from '@/services/adminApiClient';
import type { AdminAccountListResponse } from '@/models'; // Assuming this is in main models
import { useRouter, useRoute } from 'vue-router';
import { SUPPORTED_ACCOUNT_TYPES } from '@/utils/constants'; // Assuming constants file for this

export default defineComponent({
  name: 'AccountListView',
  setup() {
    const router = useRouter();
    const route = useRoute();

    const accountListResponse = ref<AdminAccountListResponse | null>(null);
    const isLoading = ref(true);
    const error = ref<string | null>(null);
    const availableStatuses = ref<{status_id: number, status_name: string}[]>([]); // For filter dropdown
    const availableAccountTypes = ref(SUPPORTED_ACCOUNT_TYPES);

    const filterState = reactive({
        searchQuery: route.query.search_query as string || '',
        statusFilter: route.query.status_filter as string || '',
        accountTypeFilter: route.query.account_type_filter as string || '',
        customerIdeFilter: route.query.customer_id_filter ? Number(route.query.customer_id_filter) : null,
        currentPage: Number(route.query.page) || 1
    });

    const fetchAccountStatuses = async () => {
        try {
            // This could be a generic service call if statuses are dynamic from DB often
            // For now, direct call or hardcode if static enough for admin panel.
            // Simulating fetch or using a static list:
            // const response = await adminApiClient.get('/api/admin/lookups/account_statuses');
            // availableStatuses.value = response.data;
            // Using static for now, as done in HTML admin routers
            availableStatuses.value = [
                { status_id: 1, status_name: 'active'}, { status_id: 2, status_name: 'frozen'}, { status_id: 3, status_name: 'closed'}
            ];
        } catch (e) {
            console.error("Failed to fetch account statuses for filter:", e);
        }
    };

    const fetchAccounts = async (page = filterState.currentPage) => {
      isLoading.value = true;
      error.value = null;
      filterState.currentPage = page;
      try {
        const params = new URLSearchParams();
        params.append('page', String(page));
        params.append('per_page', '10');
        if (filterState.searchQuery) params.append('search_query', filterState.searchQuery);
        if (filterState.statusFilter) params.append('status_filter', filterState.statusFilter);
        if (filterState.accountTypeFilter) params.append('account_type_filter', filterState.accountTypeFilter);
        if (filterState.customerIdeFilter) params.append('customer_id_filter', String(filterState.customerIdeFilter));

        router.replace({ query: { ...route.query, ...filterState } });

        const response = await adminApiClient.get<AdminAccountListResponse>('/api/admin/accounts', { params });
        accountListResponse.value = response.data;
      } catch (err: any) {
        error.value = err.response?.data?.detail || 'Failed to fetch accounts.';
      } finally {
        isLoading.value = false;
      }
    };

    const accountStatusClass = (statusName: string) => {
      if (statusName === 'active') return 'bg-green-100 text-green-800';
      if (statusName === 'frozen') return 'bg-yellow-100 text-yellow-800';
      if (statusName === 'closed') return 'bg-red-100 text-red-800';
      return 'bg-gray-100 text-gray-800';
    };

    const applyFilters = () => fetchAccounts(1);
    const clearFilters = () => {
        filterState.searchQuery = ''; filterState.statusFilter = '';
        filterState.accountTypeFilter = ''; filterState.customerIdeFilter = null;
        fetchAccounts(1);
    };
    const changePage = (newPage: number) => {
        if (newPage > 0 && accountListResponse.value && newPage <= accountListResponse.value.total_pages) {
            fetchAccounts(newPage);
        }
    };

    onMounted(() => {
        fetchAccountStatuses();
        fetchAccounts();
    });

    return {
      accountListResponse, isLoading, error, filterState,
      availableStatuses, availableAccountTypes,
      applyFilters, clearFilters, changePage, accountStatusClass,
    };
  },
});
</script>

<style scoped>
.tabular-nums {
  font-variant-numeric: tabular-nums;
}
.btn-admin-primary, .btn-admin-secondary, .btn-admin-secondary-outline { /* Define if not global */
  @apply py-2 px-4 font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-primary { @apply bg-admin-primary text-white hover:bg-blue-700 focus:ring-blue-500; }
.btn-admin-secondary { @apply bg-gray-500 text-white hover:bg-gray-600 focus:ring-gray-400; }
.btn-admin-secondary-outline { @apply bg-white text-gray-600 border border-gray-300 hover:bg-gray-50 focus:ring-admin-primary; }
</style>
```
