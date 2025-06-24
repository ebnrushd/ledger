<template>
  <div class="account-details-view container mx-auto px-4 py-8">
    <div v-if="isLoadingAccount && !selectedAccount" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
      <p class="mt-2 text-gray-600">Loading account details...</p>
    </div>
    <div v-if="!isLoadingAccount && accountError && !selectedAccount"
         class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md" role="alert">
      <p class="font-bold">Error Loading Account</p>
      <p>{{ accountError }}</p>
    </div>

    <div v-if="selectedAccount" class="account-summary bg-white shadow-lg rounded-lg p-6 mb-8">
      <div class="flex justify-between items-start mb-4">
        <div>
          <h2 class="text-3xl font-semibold text-primary">{{ selectedAccount.account_number }}</h2>
          <p class="text-lg text-gray-600">{{ selectedAccount.account_type.charAt(0).toUpperCase() + selectedAccount.account_type.slice(1) }} Account</p>
        </div>
        <span :class="['px-4 py-1.5 text-sm font-semibold rounded-full', accountStatusClass(selectedAccount.status_name)]">
          {{ selectedAccount.status_name.replace("_", " ") }}
        </span>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-gray-700">
        <p><strong>Balance:</strong> <span class="text-xl font-mono">{{ selectedAccount.balance.toFixed(2) }} {{ selectedAccount.currency }}</span></p>
        <p><strong>Overdraft Limit:</strong> {{ selectedAccount.overdraft_limit.toFixed(2) }} {{ selectedAccount.currency }}</p>
        <p><strong>Opened:</strong> {{ new Date(selectedAccount.opened_at).toLocaleDateString() }}</p>
        <p v-if="selectedAccount.updated_at"><strong>Last Update:</strong> {{ new Date(selectedAccount.updated_at).toLocaleDateString() }}</p>
      </div>
    </div>

    <div v-if="selectedAccount" class="transaction-history bg-white shadow-lg rounded-lg">
      <div class="card-header bg-gray-50 px-6 py-4 border-b border-gray-200">
        <h3 class="text-xl font-semibold text-gray-700">Transaction History</h3>
      </div>
      <div class="card-body p-6">
        <div v-if="isLoadingTransactions" class="text-center py-6">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p class="mt-2 text-gray-500 text-sm">Loading transactions...</p>
        </div>
        <div v-if="!isLoadingTransactions && transactionError"
             class="bg-red-100 border-red-500 text-red-700 p-3 mb-4 rounded text-sm" role="alert">
          Error loading transactions: {{ transactionError }}
        </div>

        <div v-if="!isLoadingTransactions && transactions && transactions.length > 0" class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Related Account</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="tx in transactions" :key="tx.transaction_id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ new Date(tx.transaction_timestamp).toLocaleString() }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ tx.type_name.replace("_", " ")|title }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 truncate max-w-xs" :title="tx.description">{{ tx.description || '-' }}</td>
                <td :class="['px-6 py-4 whitespace-nowrap text-sm font-medium text-right', tx.amount < 0 ? 'text-red-600' : 'text-green-600']">
                  {{ tx.amount.toFixed(2) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">{{ tx.related_account_number || '-' }}</td>
              </tr>
            </tbody>
          </table>

          <nav aria-label="Transaction Pagination" class="mt-6 flex justify-between items-center" v-if="pagination.totalPages > 1">
            <div>
                <p class="text-sm text-gray-700">
                    Page <span class="font-medium">{{ pagination.currentPage }}</span> of <span class="font-medium">{{ pagination.totalPages }}</span>
                    (Total <span class="font-medium">{{ pagination.totalItems }}</span> transactions)
                </p>
            </div>
            <ul class="pagination inline-flex -space-x-px rounded-md shadow-sm">
              <li>
                <button @click="changePage(pagination.currentPage - 1)" :disabled="pagination.currentPage === 1"
                        class="px-3 py-2 ml-0 leading-tight text-gray-500 bg-white border border-gray-300 rounded-l-lg hover:bg-gray-100 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed">
                  Previous
                </button>
              </li>
              {# Simple page numbers, can be extended with ellipses for many pages #}
              <li v-for="pageNumber in pagination.totalPages" :key="pageNumber">
                <button @click="changePage(pageNumber)"
                        :class="['px-3 py-2 leading-tight border', pageNumber === pagination.currentPage ? 'text-primary bg-blue-50 border-primary hover:bg-blue-100 hover:text-primary' : 'text-gray-500 bg-white border-gray-300 hover:bg-gray-100 hover:text-gray-700']">
                  {{ pageNumber }}
                </button>
              </li>
              <li>
                <button @click="changePage(pagination.currentPage + 1)" :disabled="pagination.currentPage === pagination.totalPages"
                        class="px-3 py-2 leading-tight text-gray-500 bg-white border border-gray-300 rounded-r-lg hover:bg-gray-100 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed">
                  Next
                </button>
              </li>
            </ul>
          </nav>
        </div>
        <p v-if="!isLoadingTransactions && transactions && transactions.length === 0" class="text-gray-600 mt-4">No transactions found for this account in the current view.</p>
      </div>
    </div>

    <router-link to="/dashboard"
                 class="inline-flex items-center px-4 py-2 mt-6 border border-transparent text-sm font-medium rounded-md text-primary bg-transparent hover:bg-green-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary">
        &larr; Back to Dashboard
    </router-link>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, onMounted, watch, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useAccountsStore } from '@customer/store/accounts';
import { useTransactionsStore } from '@customer/store/transactions';
import { storeToRefs } from 'pinia';

export default defineComponent({
  name: 'AccountDetailsView',
  props: {
    accountId: {
      type: [String, Number],
      required: true,
    },
  },
  setup(props) {
    const accountsStore = useAccountsStore();
    const transactionsStore = useTransactionsStore();

    const { isLoading: isLoadingAccountStore, error: accountErrorStore } = storeToRefs(accountsStore);
    const { transactions, isLoading: isLoadingTransactions, error: transactionError, getPaginationDetails: pagination } = storeToRefs(transactionsStore);

    const isLoadingLocalAccount = ref(false);

    const selectedAccount = computed(() => accountsStore.getAccountById(props.accountId));
    const isLoadingAccount = computed(() => isLoadingAccountStore.value || isLoadingLocalAccount.value);
    const accountError = computed(() => accountErrorStore.value);

    const loadTransactionsForPage = (page: number) => {
      transactionsStore.fetchTransactionHistory(props.accountId, page, pagination.value.itemsPerPage);
    };

    const changePage = (page: number) => {
      if (page > 0 && page <= pagination.value.totalPages && page !== pagination.value.currentPage) {
        loadTransactionsForPage(page);
      }
    };

    const accountStatusClass = (statusName: string) => {
      if (statusName === 'active') return 'bg-green-100 text-green-800';
      if (statusName === 'frozen') return 'bg-yellow-100 text-yellow-800';
      if (statusName === 'closed') return 'bg-red-100 text-red-800';
      return 'bg-gray-100 text-gray-800';
    };

    onMounted(async () => {
      if (!selectedAccount.value) {
        isLoadingLocalAccount.value = true;
        try {
          await accountsStore.fetchAccountById(props.accountId);
        } catch (e) { console.error(`AccountDetailsView: Failed to fetch account ${props.accountId}`, e); }
        finally { isLoadingLocalAccount.value = false; }
      }
      loadTransactionsForPage(1);
    });

    watch(() => props.accountId, async (newAccountId) => {
      if (newAccountId) {
        isLoadingLocalAccount.value = true;
        try { await accountsStore.fetchAccountById(newAccountId); }
        catch (e) { console.error(`AccountDetailsView: Failed to fetch new account ${newAccountId}`, e); }
        finally { isLoadingLocalAccount.value = false; }
        loadTransactionsForPage(1);
      }
    }, { immediate: false });

    return {
      selectedAccount, isLoadingAccount, accountError,
      transactions, isLoadingTransactions, transactionError, pagination,
      changePage, accountStatusClass,
    };
  },
});
</script>

<style scoped>
/* Using title filter for type_name in template */
/* Additional specific styles if Tailwind utilities are not enough */
.table-responsive {
    min-height: 200px; /* Ensure table area has some height even when loading/empty */
}
</style>
```
