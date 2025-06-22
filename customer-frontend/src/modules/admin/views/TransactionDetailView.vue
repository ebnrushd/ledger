<template>
  <div class="transaction-detail-view p-4 md:p-6 lg:p-8">
    <div v-if="transactionsStore.isLoadingDetails" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-admin-primary mx-auto"></div>
      <p class="mt-3 text-gray-600">Loading transaction details...</p>
    </div>
    <div v-if="transactionsStore.error && !transactionsStore.isLoadingDetails && !transaction"
         class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 mb-6 rounded-md shadow-md" role="alert">
        <p class="font-bold">Error Loading Transaction Details</p>
        <p>{{ transactionsStore.error }}</p>
         <router-link :to="{ name: 'AdminTransactionList' }" class="mt-2 inline-block btn-admin-secondary-outline text-sm">
            Back to Transaction List
        </router-link>
    </div>

    <div v-if="transaction && !transactionsStore.isLoadingDetails && !transactionsStore.error" class="max-w-3xl mx-auto">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <div>
            <h1 class="text-2xl md:text-3xl font-semibold text-gray-800">
                Transaction Details
            </h1>
            <p class="text-gray-600">ID: <span class="font-medium text-admin-primary">{{ transaction.transaction_id }}</span></p>
        </div>
      </div>

      <div class="bg-white shadow-xl rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <h3 class="text-lg font-medium text-gray-700">Transaction Information</h3>
        </div>
        <div class="px-6 py-4">
            <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
              <div><dt class="detail-label">Timestamp:</dt><dd class="detail-value">{{ new Date(transaction.transaction_timestamp).toLocaleString() }}</dd></div>
              <div><dt class="detail-label">Type:</dt><dd class="detail-value">{{ transaction.type_name.replace("_", " ")|title }}</dd></div>
              <div class="sm:col-span-2"><dt class="detail-label">Description:</dt><dd class="detail-value">{{ transaction.description || 'N/A' }}</dd></div>
              <div>
                <dt class="detail-label">Amount:</dt>
                <dd class="detail-value text-xl font-mono" :class="transaction.amount < 0 ? 'text-red-600' : 'text-green-600'">
                    {{ transaction.amount.toFixed(2) }} {{ transaction.currency || '' }}
                </dd>
              </div>
            </dl>
        </div>

        <div class="bg-gray-50 px-6 py-4 border-t border-b border-gray-200 mt-4">
            <h3 class="text-lg font-medium text-gray-700">Primary Account</h3>
        </div>
        <div class="px-6 py-4">
            <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
                <div><dt class="detail-label">Account ID:</dt>
                    <dd class="detail-value">
                        <router-link :to="{ name: 'AdminAccountDetail', params: { accountId: transaction.account_id } }" class="text-admin-primary hover:underline">
                            {{ transaction.account_id }}
                        </router-link>
                    </dd>
                </div>
                <div><dt class="detail-label">Account Number:</dt><dd class="detail-value">{{ transaction.primary_account_number || 'N/A' }}</dd></div>
                <div class="sm:col-span-2"><dt class="detail-label">Customer:</dt>
                    <dd class="detail-value">
                        <router-link v-if="transaction.customer_id" :to="{ name: 'AdminCustomerDetail', params: { customerId: transaction.customer_id } }" class="text-admin-primary hover:underline">
                            {{ transaction.customer_name || `ID: ${transaction.customer_id}` }}
                        </router-link>
                        <span v-else>N/A</span>
                    </dd>
                </div>
            </dl>
        </div>

        <div v-if="transaction.related_account_id">
            <div class="bg-gray-50 px-6 py-4 border-t border-b border-gray-200 mt-4">
                <h3 class="text-lg font-medium text-gray-700">Related Account</h3>
            </div>
            <div class="px-6 py-4">
                 <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
                    <div><dt class="detail-label">Account ID:</dt>
                        <dd class="detail-value">
                            <router-link :to="{ name: 'AdminAccountDetail', params: { accountId: transaction.related_account_id } }" class="text-admin-primary hover:underline">
                                {{ transaction.related_account_id }}
                            </router-link>
                        </dd>
                    </div>
                    <div><dt class="detail-label">Account Number:</dt><dd class="detail-value">{{ transaction.related_account_number || 'N/A' }}</dd></div>
                 </dl>
            </div>
        </div>
      </div>

       <div class="mt-8">
            <router-link :to="{ name: 'AdminTransactionList' }"
                         class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition">
                <i class="fas fa-arrow-left mr-2"></i> Back to Transaction List
            </router-link>
        </div>
    </div>
    <div v-else-if="!transactionsStore.isLoadingDetails && !transactionsStore.error && !transaction" class="text-center py-10">
        <p class="text-xl text-gray-500">Transaction not found.</p>
         <router-link :to="{ name: 'AdminTransactionList' }" class="mt-4 inline-block btn-admin-secondary-outline text-sm">
            Back to Transaction List
        </router-link>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, computed, onUnmounted } from 'vue';
import { useAdminTransactionsStore } from '@/store/adminTransactions';
import { storeToRefs } from 'pinia'; // For reactive access to store state

export default defineComponent({
  name: 'TransactionDetailView',
  props: {
    transactionId: { // From router props: true
      type: [String, Number],
      required: true,
    },
  },
  setup(props) {
    const transactionsStore = useAdminTransactionsStore();
    // Use storeToRefs to get reactive access to selectedTransaction, isLoadingDetails, error
    const { selectedTransaction: transaction, isLoadingDetails, error } = storeToRefs(transactionsStore);

    onMounted(async () => {
      // Clear previous selection/error before fetching new details
      transactionsStore.selectedTransaction = null;
      transactionsStore.error = null; // Assuming error is general for the store, or use specific detailError
      await transactionsStore.fetchTransactionDetails(props.transactionId);
    });

    onUnmounted(() => {
        // Clear selected transaction when leaving the page
        transactionsStore.selectedTransaction = null;
    });

    return {
      transaction, // This is transactionsStore.selectedTransaction (reactive)
      isLoading: isLoadingDetails, // Alias for template clarity
      error, // Alias for template clarity
      transactionsStore, // To access other parts of store if needed
    };
  },
});
</script>

<style scoped>
.detail-label { @apply text-sm font-medium text-gray-500; }
.detail-value { @apply text-sm text-gray-900 mt-1 sm:mt-0; }
.font-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }

.btn-admin-secondary-outline { /* Define if not global */
   @apply py-2 px-4 bg-white text-gray-600 border border-gray-300 font-semibold rounded-lg shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-admin-primary focus:ring-opacity-50;
}
</style>
```
