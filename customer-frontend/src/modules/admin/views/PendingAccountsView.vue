<template>
  <div class="pending-accounts-view p-4 md:p-6 lg:p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl md:text-3xl font-semibold text-gray-800">Accounts Pending Approval</h1>
    </div>

    <div v-if="accountsStore.isLoadingList" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-admin-primary mx-auto"></div>
      <p class="mt-3 text-gray-600">Loading pending accounts...</p>
    </div>

    <div v-if="accountsStore.error && !accountsStore.isLoadingList"
         class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 mb-6 rounded-md shadow-md" role="alert">
        <p class="font-bold">Error Loading Accounts</p>
        <p>{{ accountsStore.error }}</p>
    </div>

    <!-- Success/Error Messages for updates -->
    <div v-if="accountsStore.updateError"
          class="my-4 p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">
        <p class="font-bold">Update Failed:</p> {{ accountsStore.updateError }}
    </div>
    <div v-if="accountsStore.successMessage"
          class="my-4 p-3 bg-green-100 text-green-700 border border-green-400 rounded-md text-sm">
        {{ accountsStore.successMessage }}
    </div>

    <div v-if="!accountsStore.isLoadingList && !accountsStore.error" class="bg-white rounded-lg shadow-xl overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-100">
            <tr>
              <th class="table-header">ID</th>
              <th class="table-header">Account #</th>
              <th class="table-header">Customer</th>
              <th class="table-header">Type</th>
              <th class="table-header text-right">Balance</th>
              <th class="table-header">Currency</th>
              <th class="table-header">Opened At</th>
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
              <td class="table-cell text-right font-mono">{{ account.balance.toFixed(2) }}</td>
              <td class="table-cell">{{ account.currency }}</td>
              <td class="table-cell">{{ new Date(account.opened_at).toLocaleDateString() }}</td>
              <td class="table-cell space-x-2 whitespace-nowrap">
                <button @click="approveAccount(account.account_id)"
                        :disabled="accountsStore.isUpdatingStatus"
                        class="px-3 py-1 text-xs font-medium text-white bg-green-500 rounded hover:bg-green-600 transition disabled:opacity-50">Approve</button>
                <button @click="rejectAccount(account.account_id)"
                        :disabled="accountsStore.isUpdatingStatus"
                        class="px-3 py-1 text-xs font-medium text-white bg-red-500 rounded hover:bg-red-600 transition disabled:opacity-50">Reject</button>
                 <router-link :to="{ name: 'AdminAccountDetail', params: { accountId: account.account_id } }"
                             class="px-3 py-1 text-xs font-medium text-white bg-blue-500 rounded hover:bg-blue-600 transition">View</router-link>
              </td>
            </tr>
            <tr v-if="accountsStore.accounts.length === 0">
                <td colspan="8" class="text-center text-gray-500 py-6">No accounts pending approval.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Pagination -->
      <div v-if="accountsStore.totalPages > 1" class="py-4 px-4 flex justify-between items-center text-sm text-gray-600 bg-gray-50 border-t">
        <button @click="changePage(accountsStore.currentPage - 1)" :disabled="accountsStore.currentPage <= 1"
                class="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
          Previous
        </button>
        <span>Page {{ accountsStore.currentPage }} of {{ accountsStore.totalPages }} (Total: {{ accountsStore.totalItems }} accounts)</span>
        <button @click="changePage(accountsStore.currentPage + 1)" :disabled="accountsStore.currentPage >= accountsStore.totalPages"
                class="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, reactive, computed } from 'vue';
import { useAdminAccountsStore } from '@admin/store/adminAccounts';
import { storeToRefs } from 'pinia'; // Optional, for easier access to reactive store props

export default defineComponent({
  name: 'PendingAccountsView',
  setup() {
    const accountsStore = useAdminAccountsStore();
    const { accounts, isLoadingList, error, updateError, successMessage, currentPage, totalPages, itemsPerPage } = storeToRefs(accountsStore);

    const pendingFilter = reactive({ status_name: 'pending_approval' }); // Or use the correct ID if available/preferred

    const loadPendingAccounts = async (page = 1) => {
      // Clear previous messages before fetching
      accountsStore.clearMessages();
      await accountsStore.fetchAccounts(page, itemsPerPage.value, pendingFilter);
    };

    onMounted(() => {
      loadPendingAccounts();
    });

    const approveAccount = async (accountId: string | number) => {
      accountsStore.clearMessages();
      await accountsStore.updateAccountStatus(accountId, 'active', () => loadPendingAccounts(currentPage.value));
    };

    const rejectAccount = async (accountId: string | number) => {
      // Consider if 'rejected' is a status or if 'closed' is appropriate. Using 'closed' for now.
      accountsStore.clearMessages();
      await accountsStore.updateAccountStatus(accountId, 'closed', () => loadPendingAccounts(currentPage.value));
    };

    const changePage = (newPage: number) => {
        if (newPage > 0 && newPage <= totalPages.value) {
            loadPendingAccounts(newPage);
        }
    };

    return {
      accountsStore, // Expose store directly for template access to isLoadingList, error, etc.
      // accounts, // from storeToRefs
      // isLoadingList,
      // error,
      // updateError,
      // successMessage,
      // currentPage,
      // totalPages,
      // itemsPerPage,
      approveAccount,
      rejectAccount,
      changePage,
    };
  },
});
</script>

<style scoped>
.table-header { @apply px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider bg-gray-100; }
.table-cell { @apply px-4 py-3 whitespace-nowrap text-sm text-gray-700; }
.font-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
</style>
```
