<template>
  <div class="account-list-view p-4 md:p-6 lg:p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl md:text-3xl font-semibold text-gray-800">Account Management</h1>
      <!-- No "Add New Account" button as per current spec (admin usually doesn't create accounts directly here) -->
    </div>

    <!-- Filters/Search -->
    <div class="bg-white p-4 rounded-lg shadow-md mb-6">
      <form @submit.prevent="applyFiltersAndSearch" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 items-end">
        <div>
          <label for="searchQuery" class="block text-sm font-medium text-gray-700">Search:</label>
          <input type="text" id="searchQuery" v-model="filterState.searchQuery"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm"
                 placeholder="Acc #, Cust ID, Name, Email...">
        </div>
        <div>
          <label for="statusFilter" class="block text-sm font-medium text-gray-700">Status:</label>
          <select id="statusFilter" v-model="filterState.statusFilter"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm bg-white">
            <option value="">All Statuses</option>
            <option v-for="status in accountsStore.accountStatusTypes" :key="status.status_id" :value="status.status_name">
              {{ status.status_name.charAt(0).toUpperCase() + status.status_name.slice(1) }}
            </option>
          </select>
        </div>
        <div>
          <label for="accountTypeFilter" class="block text-sm font-medium text-gray-700">Account Type:</label>
          <select id="accountTypeFilter" v-model="filterState.accountTypeFilter"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm bg-white">
            <option value="">All Types</option>
            <option v-for="accType in availableAccountTypes" :key="accType" :value="accType">
              {{ accType.charAt(0).toUpperCase() + accType.slice(1) }}
            </option>
          </select>
        </div>
        <div class="flex items-end space-x-2">
          <button type="submit"
                  class="w-full sm:w-auto px-4 py-2 bg-admin-primary text-white rounded-md shadow hover:bg-blue-700 transition duration-150">Filter</button>
          <button type="button" @click="clearAllFilters"
                  class="w-full sm:w-auto px-4 py-2 bg-gray-200 text-gray-700 rounded-md shadow hover:bg-gray-300 transition duration-150">Clear</button>
        </div>
      </form>
    </div>

    <div v-if="accountsStore.isLoadingList" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-admin-primary mx-auto"></div>
      <p class="mt-3 text-gray-600">Loading accounts...</p>
    </div>
    <div v-if="accountsStore.error && !accountsStore.isLoadingList"
         class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 mb-6 rounded-md shadow-md" role="alert">
        <p class="font-bold">Error Loading Accounts</p>
        <p>{{ accountsStore.error }}</p>
    </div>

    <div v-if="!accountsStore.isLoadingList && !accountsStore.error && accountsStore.accounts" class="bg-white rounded-lg shadow-xl overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-100">
            <tr>
              <th class="table-header">ID</th>
              <th class="table-header">Account #</th>
              <th class="table-header">Customer</th>
              <th class="table-header">Type</th>
              <th class="table-header text-right">Balance</th>
              <th class="table-header">Status</th>
              <th class="table-header text-right">Overdraft Limit</th>
              <th class="table-header">Opened</th>
              <th class="table-header">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="account in accountsStore.accounts" :key="account.account_id" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell">{{ account.account_id }}</td>
              <td class="table-cell font-medium text-gray-900">{{ account.account_number }}</td>
              <td class="table-cell">
                <router-link v-if="account.customer_id" :to="{ name: 'AdminCustomerDetail', params: { customerId: account.customer_id } }" class="text-admin-primary hover:underline">
                  {{ account.customer_first_name || '' }} {{ account.customer_last_name || '' }} ({{ account.customer_id }})
                </router-link>
                <span v-else>N/A</span>
              </td>
              <td class="table-cell">{{ account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1) }}</td>
              <td class="table-cell text-right font-mono">{{ account.balance.toFixed(2) }} {{ account.currency }}</td>
              <td class="table-cell">
                <span :class="['px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full', accountStatusClass(account.status_name)]">
                  {{ account.status_name.replace("_", " ")|title }}
                </span>
              </td>
              <td class="table-cell text-right font-mono">{{ account.overdraft_limit.toFixed(2) }}</td>
              <td class="table-cell">{{ new Date(account.opened_at).toLocaleDateString() }}</td>
              <td class="table-cell space-x-2 whitespace-nowrap">
                <router-link :to="{ name: 'AdminAccountDetail', params: { accountId: account.account_id } }"
                             class="px-3 py-1 text-xs font-medium text-white bg-blue-500 rounded hover:bg-blue-600 transition">View</router-link>
              </td>
            </tr>
            <tr v-if="accountsStore.accounts.length === 0">
                <td colspan="9" class="text-center text-gray-500 py-6">No accounts found matching your criteria.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Pagination -->
      <div v-if="accountsStore.totalPages > 1" class="py-4 px-4 flex justify-between items-center text-sm text-gray-600 bg-gray-50 border-t">
        <button @click="changePage(accountsStore.currentPage - 1)" :disabled="accountsStore.currentPage <= 1"
                class="btn-admin-secondary-outline">Previous</button>
        <span>Page {{ accountsStore.currentPage }} of {{ accountsStore.totalPages }} (Total: {{ accountsStore.totalItems }} accounts)</span>
        <button @click="changePage(accountsStore.currentPage + 1)" :disabled="accountsStore.currentPage >= accountsStore.totalPages"
                class="btn-admin-secondary-outline">Next</button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, reactive, watch, computed, ref } from 'vue';
import { useAdminAccountsStore } from '@admin/store/adminAccounts';
import { useRouter, useRoute } from 'vue-router';
import { SUPPORTED_ACCOUNT_TYPES } from '@admin/utils/constants';

export default defineComponent({
  name: 'AccountListView',
  setup() {
    const accountsStore = useAdminAccountsStore();
    const router = useRouter();
    const route = useRoute();

    const filterState = reactive({
        searchQuery: (route.query.search_query as string) || '',
        statusFilter: (route.query.status_filter as string) || '',
        accountTypeFilter: (route.query.account_type_filter as string) || '',
        customerIdeFilter: route.query.customer_id_filter ? Number(route.query.customer_id_filter) : null, // Not used yet in UI
        currentPage: Number(route.query.page) || 1
    });

    const availableAccountTypes = ref(SUPPORTED_ACCOUNT_TYPES); // From constants or could be fetched

    const fetchAccountList = (page = filterState.currentPage) => {
      filterState.currentPage = page;
      const filters = {
          search_query: filterState.searchQuery,
          status_filter: filterState.statusFilter,
          account_type_filter: filterState.accountTypeFilter,
          customer_id_filter: filterState.customerIdeFilter
      };
      accountsStore.fetchAccounts(page, accountsStore.itemsPerPage, filters);
    };

    const applyFiltersAndSearch = () => {
        const query: any = { page: '1' }; // Reset to page 1 on new filter/search
        if (filterState.searchQuery) query.search_query = filterState.searchQuery;
        if (filterState.statusFilter) query.status_filter = filterState.statusFilter;
        if (filterState.accountTypeFilter) query.account_type_filter = filterState.accountTypeFilter;
        if (filterState.customerIdeFilter) query.customer_id_filter = String(filterState.customerIdeFilter);
        router.push({ query });
    };

    const clearAllFilters = () => {
        filterState.searchQuery = ''; filterState.statusFilter = '';
        filterState.accountTypeFilter = ''; filterState.customerIdeFilter = null;
        router.push({ query: {} });
    };

    const changePage = (newPage: number) => {
        if (newPage > 0 && newPage <= accountsStore.totalPages) {
            filterState.currentPage = newPage;
            router.push({ query: { ...route.query, page: String(newPage) } });
        }
    };

    watch(() => route.query, (newQuery) => {
        filterState.searchQuery = (newQuery.search_query as string) || '';
        filterState.statusFilter = (newQuery.status_filter as string) || '';
        filterState.accountTypeFilter = (newQuery.account_type_filter as string) || '';
        filterState.customerIdeFilter = newQuery.customer_id_filter ? Number(newQuery.customer_id_filter) : null;
        filterState.currentPage = Number(newQuery.page) || 1;
        fetchAccountList(filterState.currentPage);
    }, { deep: true });

    const accountStatusClass = (statusName: string) => {
      if (statusName === 'active') return 'bg-green-100 text-green-800';
      if (statusName === 'frozen') return 'bg-yellow-100 text-yellow-800';
      if (statusName === 'closed') return 'bg-red-100 text-red-800';
      return 'bg-gray-100 text-gray-800';
    };

    onMounted(() => {
        accountsStore.clearMessages();
        accountsStore.fetchAccountStatusTypes(); // For filter dropdown
        fetchAccountList();
    });

    return {
      accountsStore,
      filterState,
      availableAccountTypes, // For dropdown
      applyFiltersAndSearch,
      clearAllFilters,
      changePage,
      accountStatusClass,
    };
  },
});
</script>

<style scoped>
.table-header { @apply px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-100; }
.table-cell { @apply px-4 py-3 whitespace-nowrap text-sm text-gray-700; }
.font-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.btn-admin-primary, .btn-admin-secondary-outline, .btn-admin-secondary {
  @apply py-2 px-4 font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-primary { @apply bg-admin-primary text-white hover:bg-blue-700 focus:ring-blue-500; }
.btn-admin-secondary-outline { @apply bg-white text-gray-600 border border-gray-300 hover:bg-gray-50 focus:ring-admin-primary; }
.btn-admin-secondary { @apply bg-gray-200 text-gray-700 hover:bg-gray-300 focus:ring-gray-400; }
</style>
```
