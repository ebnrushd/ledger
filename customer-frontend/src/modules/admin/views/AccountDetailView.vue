<template>
  <div class="account-detail-view p-4 md:p-6 lg:p-8">
    <div v-if="accountsStore.isLoadingDetails" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-admin-primary mx-auto"></div>
      <p class="mt-3 text-gray-600">Loading account details...</p>
    </div>
    <div v-if="accountsStore.error && !accountsStore.isLoadingDetails && !account"
         class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 mb-6 rounded-md shadow-md" role="alert">
        <p class="font-bold">Error Loading Account Details</p>
        <p>{{ accountsStore.error }}</p>
         <router-link :to="{ name: 'AdminAccountList' }" class="mt-2 inline-block btn-admin-secondary-outline text-sm">
            Back to Account List
        </router-link>
    </div>

    <div v-if="account && !accountsStore.isLoadingDetails" class="max-w-4xl mx-auto">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
            <div>
                <h1 class="text-2xl md:text-3xl font-semibold text-gray-800">
                    Account: <span class="text-admin-primary">{{ account.account_number }}</span>
                </h1>
                <p class="text-gray-600">Customer:
                    <router-link v-if="account.customer_id"
                                 :to="{ name: 'AdminCustomerDetail', params: { customerId: account.customer_id } }"
                                 class="text-admin-primary hover:underline">
                        {{ account.customer_first_name || '' }} {{ account.customer_last_name || '' }} (ID: {{ account.customer_id }})
                    </router-link>
                    <span v-else>N/A</span>
                </p>
            </div>
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
         <div v-if="clientFormError"
             class="my-4 p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">
            {{ clientFormError }}
        </div>


        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Account Info Card -->
            <div class="lg:col-span-2 bg-white shadow-xl rounded-lg p-6">
                <h3 class="text-xl font-semibold text-gray-700 mb-4 border-b pb-3">Account Summary</h3>
                <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3">
                    <div><dt class="detail-label">Account ID:</dt><dd class="detail-value">{{ account.account_id }}</dd></div>
                    <div><dt class="detail-label">Type:</dt><dd class="detail-value">{{ account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1) }}</dd></div>
                    <div><dt class="detail-label">Balance:</dt><dd class="detail-value font-mono">{{ account.balance.toFixed(2) }} {{ account.currency }}</dd></div>
                    <div><dt class="detail-label">Status:</dt>
                        <dd class="detail-value">
                             <span :class="['px-2.5 py-0.5 text-xs font-semibold rounded-full', accountStatusClass(account.status_name)]">
                                {{ account.status_name.replace("_", " ")|title }}
                            </span>
                        </dd>
                    </div>
                    <div><dt class="detail-label">Overdraft Limit:</dt><dd class="detail-value font-mono">{{ account.overdraft_limit.toFixed(2) }} {{ account.currency }}</dd></div>
                    <div><dt class="detail-label">Opened:</dt><dd class="detail-value">{{ new Date(account.opened_at).toLocaleDateString() }}</dd></div>
                </dl>
            </div>

            <!-- Management Card -->
            <div class="lg:col-span-1 bg-white shadow-xl rounded-lg p-6 space-y-6">
                <div>
                    <h3 class="text-lg font-medium text-gray-700 mb-2">Update Status</h3>
                    <form @submit.prevent="handleStatusUpdate">
                        <label for="accountStatus" class="sr-only">Account Status</label>
                        <select id="accountStatus" v-model="selectedStatusName"
                                class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm bg-white">
                            <option v-for="statusType in accountsStore.accountStatusTypes" :key="statusType.status_id" :value="statusType.status_name">
                                {{ statusType.status_name.charAt(0).toUpperCase() + statusType.status_name.slice(1) }}
                            </option>
                        </select>
                        <button type="submit" :disabled="accountsStore.isUpdatingStatus || selectedStatusName === account.status_name"
                                class="mt-2 w-full btn-admin-primary py-1.5 text-sm disabled:bg-gray-400">
                            {{ accountsStore.isUpdatingStatus ? 'Updating...' : 'Set Status' }}
                        </button>
                    </form>
                </div>
                <div>
                    <h3 class="text-lg font-medium text-gray-700 mb-2">Update Overdraft Limit</h3>
                    <form @submit.prevent="handleOverdraftUpdate">
                        <label for="overdraftLimit" class="sr-only">Overdraft Limit</label>
                        <div class="mt-1 relative rounded-md shadow-sm">
                            <input type="number" id="overdraftLimit" v-model.number="newOverdraftLimit" step="0.01" min="0" required
                                   class="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm"
                                   placeholder="0.00">
                            <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                                <span class="text-gray-500 sm:text-sm">{{ account.currency }}</span>
                            </div>
                        </div>
                        <button type="submit" :disabled="accountsStore.isUpdatingOverdraft || newOverdraftLimit === account.overdraft_limit"
                                class="mt-2 w-full btn-admin-primary py-1.5 text-sm disabled:bg-gray-400">
                            {{ accountsStore.isUpdatingOverdraft ? 'Updating...' : 'Set Overdraft' }}
                        </button>
                    </form>
                </div>
            </div>
        </div>

        <!-- Transaction History (Placeholder for now) -->
        <div class="mt-8 bg-white shadow-xl rounded-lg">
            <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <h3 class="text-lg font-medium text-gray-700">Recent Transactions</h3>
                <router-link :to="{ name: 'AdminTransactionList', query: { account_id_filter: account.account_id } }"
                             class="text-sm text-admin-primary hover:underline">
                    View All Transactions
                </router-link>
            </div>
            <div class="p-6 text-sm text-gray-500">
                (Transaction list display here is part of a future step or can be added by fetching via transactions store)
            </div>
        </div>

        <div class="mt-8">
            <router-link :to="{ name: 'AdminAccountList' }"
                         class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition">
                <i class="fas fa-arrow-left mr-2"></i> Back to Account List
            </router-link>
        </div>
    </div>
    <div v-else-if="!accountsStore.isLoadingDetails && !accountsStore.error && !account" class="text-center py-10">
        <p class="text-xl text-gray-500">Account not found.</p>
         <router-link :to="{ name: 'AdminAccountList' }" class="mt-4 inline-block btn-admin-secondary-outline text-sm">
            Back to Account List
        </router-link>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed, watch, onUnmounted } from 'vue';
import { useAdminAccountsStore } from '@admin/store/adminAccounts';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router'; // For potential navigation after update

export default defineComponent({
  name: 'AccountDetailView',
  props: {
    accountId: { type: [String, Number], required: true },
  },
  setup(props) {
    const accountsStore = useAdminAccountsStore();
    const router = useRouter();
    // Reactive references to store state
    const { selectedAccount: account, isLoadingDetails, error,
            accountStatusTypes, isUpdatingStatus, isUpdatingOverdraft,
            updateError, successMessage
          } = storeToRefs(accountsStore);

    const selectedStatusName = ref('');
    const newOverdraftLimit = ref<number | null>(null);
    const clientFormError = ref<string|null>(null);

    const accountStatusClass = (statusName: string) => {
      if (statusName === 'active') return 'bg-green-100 text-green-800';
      if (statusName === 'frozen') return 'bg-yellow-100 text-yellow-800';
      if (statusName === 'closed') return 'bg-red-100 text-red-800';
      return 'bg-gray-100 text-gray-800';
    };

    const loadInitialData = async () => {
        accountsStore.clearMessages();
        await accountsStore.fetchAccountStatusTypes(); // For status dropdown
        try {
            await accountsStore.fetchAccountDetails(props.accountId);
            if (account.value) { // Check if account is loaded
                selectedStatusName.value = account.value.status_name;
                newOverdraftLimit.value = account.value.overdraft_limit;
            }
        } catch (e) {
            // Error is already set in store by fetchAccountDetails
            console.error("Error fetching account details in view:", e);
        }
    };

    onMounted(loadInitialData);

    // Watch for prop changes if navigating between different account detail pages
    watch(() => props.accountId, (newId) => {
        if(newId) loadInitialData();
    });

    // Watch for selectedAccount changes to re-sync form fields if data is refreshed
    watch(account, (newAccountData) => {
        if (newAccountData) {
            selectedStatusName.value = newAccountData.status_name;
            newOverdraftLimit.value = newAccountData.overdraft_limit;
        }
    }, { deep: true });

    const handleStatusUpdate = async () => {
        clientFormError.value = null;
        if (!selectedStatusName.value || selectedStatusName.value === account.value?.status_name) {
            clientFormError.value = "Please select a new status or no change needed.";
            return;
        }
        const success = await accountsStore.updateAccountStatus(props.accountId, selectedStatusName.value);
        if (success) {
            // Optionally, refresh all data or rely on store's update to selectedAccount
            // await accountsStore.fetchAccountDetails(props.accountId); // Re-fetch to confirm
        }
        // Error/success messages are reactive from store
    };

    const handleOverdraftUpdate = async () => {
        clientFormError.value = null;
        if (newOverdraftLimit.value === null || newOverdraftLimit.value < 0) {
            clientFormError.value = "Overdraft limit must be a non-negative number.";
            return;
        }
        if (newOverdraftLimit.value === account.value?.overdraft_limit) {
            clientFormError.value = "No change in overdraft limit.";
            return;
        }
        const success = await accountsStore.updateAccountOverdraftLimit(props.accountId, newOverdraftLimit.value);
        if (success) {
            // await accountsStore.fetchAccountDetails(props.accountId); // Re-fetch
        }
    };

    onUnmounted(() => {
        accountsStore.clearMessages();
        accountsStore.selectedAccount = null; // Clear selection when leaving
    });

    return {
        account,
        isLoading: isLoadingDetails, // Alias for template
        error,
        accountsStore, // To access other store states like isUpdatingStatus etc.
        selectedStatusName, newOverdraftLimit, clientFormError,
        accountStatusClass,
        handleStatusUpdate, handleOverdraftUpdate
    };
  },
});
</script>

<style scoped>
.detail-label { @apply text-sm font-medium text-gray-500; }
.detail-value { @apply text-sm text-gray-900 mt-1 sm:mt-0; }
.table-header-sm { @apply px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider; }
.table-cell-sm { @apply px-3 py-2 whitespace-nowrap text-sm text-gray-600; }
.font-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }

.btn-admin-primary, .btn-admin-secondary-outline {
  @apply py-2 px-4 font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-primary { @apply bg-admin-primary text-white hover:bg-blue-700 focus:ring-blue-500; }
.btn-admin-secondary-outline { @apply bg-white text-gray-600 border border-gray-300 hover:bg-gray-50 focus:ring-admin-primary; }
</style>
```
