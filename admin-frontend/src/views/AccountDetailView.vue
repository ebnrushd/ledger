<template>
  <div class="p-6">
    <div v-if="isLoading" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-admin-primary mx-auto"></div>
      <p class="mt-2 text-gray-600">Loading account details...</p>
    </div>
    <div v-if="error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md">
        <p class="font-bold">Error</p>
        <p>{{ error }}</p>
    </div>

    <div v-if="account && !isLoading && !error">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-semibold text-gray-800">
                Account: <span class="text-admin-primary">{{ account.account_number }}</span>
            </h1>
            <!-- Actions like edit status/overdraft are handled by forms below -->
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Account Info Card -->
            <div class="bg-white shadow-xl rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-700 mb-3 border-b pb-2">Account Summary</h3>
                <dl class="space-y-2">
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Account ID:</dt><dd class="w-2/3 text-sm text-gray-900">{{ account.account_id }}</dd></div>
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Type:</dt><dd class="w-2/3 text-sm text-gray-900">{{ account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1) }}</dd></div>
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Balance:</dt><dd class="w-2/3 text-sm text-gray-900 font-mono">{{ account.balance.toFixed(2) }} {{ account.currency }}</dd></div>
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Status:</dt>
                        <dd class="w-2/3 text-sm">
                             <span :class="['px-2 py-0.5 text-xs font-semibold rounded-full', accountStatusClass(account.status_name)]">
                                {{ account.status_name }}
                            </span>
                        </dd>
                    </div>
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Overdraft Limit:</dt><dd class="w-2/3 text-sm text-gray-900 font-mono">{{ account.overdraft_limit.toFixed(2) }} {{ account.currency }}</dd></div>
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Opened:</dt><dd class="w-2/3 text-sm text-gray-900">{{ new Date(account.opened_at).toLocaleDateString() }}</dd></div>
                </dl>
            </div>

            <!-- Customer Info Card -->
            <div class="bg-white shadow-xl rounded-lg p-6">
                 <h3 class="text-lg font-medium text-gray-700 mb-3 border-b pb-2">Customer Information</h3>
                 <div v-if="customer">
                    <dl class="space-y-2">
                        <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Customer ID:</dt>
                            <dd class="w-2/3 text-sm text-gray-900">
                                <router-link :to="{ name: 'AdminCustomerDetail', params: { customerId: customer.customer_id } }" class="text-admin-primary hover:underline">
                                    {{ customer.customer_id }}
                                </router-link>
                            </dd>
                        </div>
                        <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Name:</dt><dd class="w-2/3 text-sm text-gray-900">{{customer.first_name}} {{customer.last_name}}</dd></div>
                        <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Email:</dt><dd class="w-2/3 text-sm text-gray-900">{{customer.email}}</dd></div>
                    </dl>
                 </div>
                 <p v-else class="text-sm text-gray-500">Customer details not available or not loaded.</p>
            </div>
        </div>

        <!-- Forms for Status & Overdraft (Placeholder - these are part of HTML admin panel) -->
        <!-- If JSON API needs to do this, specific PUT endpoints on /api/admin/accounts/{id}/status etc. exist -->
        <div class="mt-6 text-sm text-gray-600">
            <p>Account status and overdraft limit modifications are handled via specific PUT requests to this API or through the HTML Admin Panel forms.</p>
        </div>


        <!-- Transaction History (Placeholder - could be a separate component or fetched here) -->
        <div class="mt-8 bg-white shadow-xl rounded-lg">
            <div class="card-header bg-gray-50 px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-medium text-gray-700">Recent Transactions (Placeholder)</h3>
            </div>
            <div class="p-6 text-sm text-gray-500">
                Full transaction history and filtering available on the main Transactions page.
                <router-link :to="{ name: 'AdminTransactionList', query: { account_id_filter: account.account_id } }" class="text-admin-primary hover:underline">
                    View all transactions for this account
                </router-link>
            </div>
        </div>


        <div class="mt-6">
            <router-link :to="{ name: 'AdminAccountList' }" class="btn-admin-secondary-outline">
                 <i class="fas fa-arrow-left mr-2"></i> Back to Account List
            </router-link>
        </div>
    </div>
    <div v-else-if="!isLoading && !error">
        <p class="text-center text-gray-500">Account not found.</p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import adminApiClient from '@/services/adminApiClient';
import type { AccountDetails, CustomerDetails } from '@/models'; // Using main models

export default defineComponent({
  name: 'AccountDetailView',
  props: {
    accountId: { type: [String, Number], required: true },
  },
  setup(props) {
    const account = ref<AccountDetails | null>(null);
    const customer = ref<CustomerDetails | null>(null);
    // transactions list placeholder
    const isLoading = ref(true);
    const error = ref<string | null>(null);

    const accountStatusClass = (statusName: string) => {
      if (statusName === 'active') return 'bg-green-100 text-green-800';
      if (statusName === 'frozen') return 'bg-yellow-100 text-yellow-800';
      if (statusName === 'closed') return 'bg-red-100 text-red-800';
      return 'bg-gray-100 text-gray-800';
    };

    const fetchAccountDetails = async () => {
      isLoading.value = true; error.value = null;
      try {
        // Use the AdminAccountDetailResponse model if it includes customer directly from backend
        // For now, assuming /api/admin/accounts/{accountId} returns AccountDetails structure
        const response = await adminApiClient.get<AccountDetails & { customer?: CustomerDetails }>(`/api/admin/accounts/${props.accountId}`);
        account.value = response.data;
        if (response.data.customer) { // If customer is nested in account detail response
            customer.value = response.data.customer;
        } else if (account.value?.customer_id) { // Else, fetch customer separately
            const custResponse = await adminApiClient.get<CustomerDetails>(`/api/admin/customers/${account.value.customer_id}`);
            customer.value = custResponse.data;
        }
        // Fetch recent transactions here if needed for this view specifically
      } catch (err: any) {
        error.value = err.response?.data?.detail || `Failed to load account details: ${err.message}`;
      } finally { isLoading.value = false; }
    };

    onMounted(fetchAccountDetails);

    return { account, customer, isLoading, error, accountStatusClass };
  },
});
</script>

<style scoped>
.font-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.tabular-nums { font-variant-numeric: tabular-nums; }
.btn-admin-primary, .btn-admin-secondary-outline { /* Define if not global */
  @apply py-2 px-4 font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-primary { @apply bg-admin-primary text-white hover:bg-blue-700 focus:ring-blue-500; }
.btn-admin-secondary-outline { @apply bg-white text-gray-600 border border-gray-300 hover:bg-gray-50 focus:ring-admin-primary; }
</style>
```
