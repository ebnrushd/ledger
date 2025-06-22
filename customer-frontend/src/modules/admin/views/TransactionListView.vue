<template>
  <div class="transaction-list-view p-4 md:p-6 lg:p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl md:text-3xl font-semibold text-gray-800">Transaction Monitoring</h1>
      <!-- No "Add Transaction" button as transactions are system-generated or via user actions -->
    </div>

    <!-- Filters/Search -->
    <div class="bg-white p-4 rounded-lg shadow-md mb-6">
      <form @submit.prevent="applyFiltersAndSearch" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 items-end">
        <div>
          <label for="accountIdFilter" class="block text-sm font-medium text-gray-700">Account ID:</label>
          <input type="number" id="accountIdFilter" v-model.number="filterState.accountIdFilter"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm"
                 placeholder="Enter Account ID">
        </div>
        <div>
          <label for="typeFilter" class="block text-sm font-medium text-gray-700">Type:</label>
          <select id="typeFilter" v-model="filterState.transactionTypeFilter"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm bg-white">
            <option value="">All Types</option>
            <option v-for="ttype in transactionsStore.transactionTypes" :key="ttype.transaction_type_id" :value="ttype.type_name">
              {{ ttype.type_name.replace("_", " ")|title }}
            </option>
          </select>
        </div>
        <div>
          <label for="startDateFilter" class="block text-sm font-medium text-gray-700">From Date:</label>
          <input type="date" id="startDateFilter" v-model="filterState.startDateFilter"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
        </div>
        <div>
          <label for="endDateFilter" class="block text-sm font-medium text-gray-700">To Date:</label>
          <input type="date" id="endDateFilter" v-model="filterState.endDateFilter"
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
        </div>
        <div class="flex items-end space-x-2">
          <button type="submit"
                  class="w-full sm:w-auto px-4 py-2 bg-admin-primary text-white rounded-md shadow hover:bg-blue-700 transition duration-150">Filter</button>
          <button type="button" @click="clearAllFilters"
                  class="w-full sm:w-auto px-4 py-2 bg-gray-200 text-gray-700 rounded-md shadow hover:bg-gray-300 transition duration-150">Clear</button>
        </div>
      </form>
    </div>

    <div v-if="transactionsStore.isLoadingList" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-admin-primary mx-auto"></div>
      <p class="mt-3 text-gray-600">Loading transactions...</p>
    </div>
    <div v-if="transactionsStore.error && !transactionsStore.isLoadingList"
         class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 mb-6 rounded-md shadow-md" role="alert">
        <p class="font-bold">Error Loading Transactions</p>
        <p>{{ transactionsStore.error }}</p>
    </div>

    <div v-if="!transactionsStore.isLoadingList && !transactionsStore.error && transactionsStore.transactions" class="bg-white rounded-lg shadow-xl overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-100">
            <tr>
              <th class="table-header">ID</th>
              <th class="table-header">Timestamp</th>
              <th class="table-header">Account #</th>
              <th class="table-header">Customer</th>
              <th class="table-header">Type</th>
              <th class="table-header text-right">Amount</th>
              <th class="table-header">Description</th>
              <th class="table-header">Related Acc #</th>
              <th class="table-header">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="tx in transactionsStore.transactions" :key="tx.transaction_id" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell">{{ tx.transaction_id }}</td>
              <td class="table-cell">{{ new Date(tx.transaction_timestamp).toLocaleString() }}</td>
              <td class="table-cell">
                <router-link :to="{ name: 'AdminAccountDetail', params: { accountId: tx.account_id } }" class="text-admin-primary hover:underline">
                  {{ tx.primary_account_number }}
                </router-link>
              </td>
              <td class="table-cell">
                 <router-link v-if="tx.customer_id" :to="{ name: 'AdminCustomerDetail', params: { customerId: tx.customer_id } }" class="text-admin-primary hover:underline">
                    {{ tx.customer_name || `ID: ${tx.customer_id}` }}
                 </router-link>
                 <span v-else>N/A</span>
              </td>
              <td class="table-cell">{{ tx.type_name.replace("_", " ")|title }}</td>
              <td class="table-cell text-right font-mono" :class="tx.amount < 0 ? 'text-red-600' : 'text-green-600'">
                {{ tx.amount.toFixed(2) }} {{ tx.currency }}
              </td>
              <td class="table-cell max-w-xs truncate" :title="tx.description">{{ tx.description || '-' }}</td>
              <td class="table-cell">
                <router-link v-if="tx.related_account_id && tx.related_account_number"
                             :to="{ name: 'AdminAccountDetail', params: { accountId: tx.related_account_id } }"
                             class="text-admin-primary hover:underline">
                  {{ tx.related_account_number }}
                </router-link>
                <span v-else-if="tx.related_account_id">{{ tx.related_account_id }}</span>
                <span v-else>N/A</span>
              </td>
              <td class="table-cell space-x-2 whitespace-nowrap">
                <router-link :to="{ name: 'AdminTransactionDetail', params: { transactionId: tx.transaction_id } }"
                             class="px-3 py-1 text-xs font-medium text-white bg-blue-500 rounded hover:bg-blue-600 transition">View</router-link>
              </td>
            </tr>
            <tr v-if="transactionsStore.transactions.length === 0">
                <td colspan="9" class="text-center text-gray-500 py-6">No transactions found matching your criteria.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Pagination -->
      <div v-if="transactionsStore.totalPages > 1" class="py-4 px-4 flex justify-between items-center text-sm text-gray-600 bg-gray-50 border-t">
        <button @click="changePage(transactionsStore.currentPage - 1)" :disabled="transactionsStore.currentPage <= 1"
                class="btn-admin-secondary-outline">Previous</button>
        <span>Page {{ transactionsStore.currentPage }} of {{ transactionsStore.totalPages }} (Total: {{ transactionsStore.totalItems }} transactions)</span>
        <button @click="changePage(transactionsStore.currentPage + 1)" :disabled="transactionsStore.currentPage >= transactionsStore.totalPages"
                class="btn-admin-secondary-outline">Next</button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, reactive, watch } from 'vue';
import { useAdminTransactionsStore } from '@/store/adminTransactions';
import { useRouter, useRoute } from 'vue-router';
// Helper to convert "" to null for optional number filters if needed, or handle in service/API.

export default defineComponent({
  name: 'TransactionListView',
  setup() {
    const transactionsStore = useAdminTransactionsStore();
    const router = useRouter();
    const route = useRoute();

    const filterState = reactive({
        accountIdFilter: route.query.account_id_filter ? Number(route.query.account_id_filter) : null,
        transactionTypeFilter: (route.query.transaction_type_filter as string) || '',
        startDateFilter: (route.query.start_date_filter as string) || '',
        endDateFilter: (route.query.end_date_filter as string) || '',
        currentPage: Number(route.query.page) || 1
    });

    const fetchTransactionList = (page = filterState.currentPage) => {
      filterState.currentPage = page;
      const filters = {
          account_id_filter: filterState.accountIdFilter,
          transaction_type_filter: filterState.transactionTypeFilter,
          start_date_filter: filterState.startDateFilter,
          end_date_filter: filterState.endDateFilter,
      };
      transactionsStore.fetchTransactions(page, transactionsStore.itemsPerPage, filters);
    };

    const applyFiltersAndSearch = () => {
        const query: any = { page: '1' };
        if (filterState.accountIdFilter) query.account_id_filter = String(filterState.accountIdFilter);
        if (filterState.transactionTypeFilter) query.transaction_type_filter = filterState.transactionTypeFilter;
        if (filterState.startDateFilter) query.start_date_filter = filterState.startDateFilter;
        if (filterState.endDateFilter) query.end_date_filter = filterState.endDateFilter;
        router.push({ query });
    };

    const clearAllFilters = () => {
        filterState.accountIdFilter = null;
        filterState.transactionTypeFilter = '';
        filterState.startDateFilter = '';
        filterState.endDateFilter = '';
        router.push({ query: {} });
    };

    const changePage = (newPage: number) => {
        if (newPage > 0 && newPage <= transactionsStore.totalPages) {
            filterState.currentPage = newPage;
            router.push({ query: { ...route.query, page: String(newPage) } });
        }
    };

    watch(() => route.query, (newQuery) => {
        filterState.accountIdFilter = newQuery.account_id_filter ? Number(newQuery.account_id_filter) : null;
        filterState.transactionTypeFilter = (newQuery.transaction_type_filter as string) || '';
        filterState.startDateFilter = (newQuery.start_date_filter as string) || '';
        filterState.endDateFilter = (newQuery.end_date_filter as string) || '';
        filterState.currentPage = Number(newQuery.page) || 1;
        fetchTransactionList(filterState.currentPage);
    }, { deep: true });

    onMounted(() => {
        transactionsStore.clearError();
        transactionsStore.fetchTransactionTypes(); // For filter dropdown
        fetchTransactionList();
    });

    return {
      transactionsStore,
      filterState,
      applyFiltersAndSearch,
      clearAllFilters,
      changePage,
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
