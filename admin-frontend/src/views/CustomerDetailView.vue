<template>
  <div class="p-6">
     <div v-if="isLoading" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-admin-primary mx-auto"></div>
      <p class="mt-2 text-gray-600">Loading customer details...</p>
    </div>
    <div v-if="error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md">
        <p class="font-bold">Error</p>
        <p>{{ error }}</p>
    </div>

    <div v-if="customer && !isLoading && !error">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-semibold text-gray-800">
                Customer Profile: <span class="text-admin-primary">{{ customer.first_name }} {{ customer.last_name }}</span>
            </h1>
            <!-- Add Edit Customer button if functionality exists -->
            <!-- <router-link :to="{ name: 'AdminCustomerEditForm', params: { customerId: customer.customer_id } }" class="btn-admin-primary">
                <i class="fas fa-edit mr-2"></i> Edit Customer
            </router-link> -->
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Customer Info Card -->
            <div class="bg-white shadow-xl rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-700 mb-3 border-b pb-2">Contact Information</h3>
                <dl class="space-y-2">
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Customer ID:</dt><dd class="w-2/3 text-sm text-gray-900">{{ customer.customer_id }}</dd></div>
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Email:</dt><dd class="w-2/3 text-sm text-gray-900">{{ customer.email }}</dd></div>
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Phone:</dt><dd class="w-2/3 text-sm text-gray-900">{{ customer.phone_number || 'N/A' }}</dd></div>
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Address:</dt><dd class="w-2/3 text-sm text-gray-900">{{ customer.address || 'N/A' }}</dd></div>
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Created At:</dt><dd class="w-2/3 text-sm text-gray-900">{{ new Date(customer.created_at).toLocaleString() }}</dd></div>
                </dl>
            </div>

            <!-- Associated User Card (if applicable) -->
            <div v-if="linkedUser" class="bg-white shadow-xl rounded-lg p-6">
                 <h3 class="text-lg font-medium text-gray-700 mb-3 border-b pb-2">Linked User Account</h3>
                 <dl class="space-y-2">
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">User ID:</dt>
                        <dd class="w-2/3 text-sm text-gray-900">
                             <router-link :to="{ name: 'AdminUserDetail', params: { userId: linkedUser.user_id } }" class="text-admin-primary hover:underline">
                                {{ linkedUser.user_id }}
                            </router-link>
                        </dd>
                    </div>
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Username:</dt><dd class="w-2/3 text-sm text-gray-900">{{ linkedUser.username }}</dd></div>
                    <div class="flex"><dt class="w-1/3 text-sm font-medium text-gray-500">Role:</dt><dd class="w-2/3 text-sm text-gray-900">{{ linkedUser.role_name }}</dd></div>
                 </dl>
            </div>
             <div v-else-if="!isLoadingUserLink" class="bg-white shadow-xl rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-700 mb-3 border-b pb-2">Linked User Account</h3>
                <p class="text-sm text-gray-600">No user account directly linked to this customer profile via `users.customer_id`.</p>
            </div>
            <div v-if="isLoadingUserLink" class="bg-white shadow-xl rounded-lg p-6 text-center">
                <p class="text-sm text-gray-500">Loading linked user info...</p>
            </div>
        </div>

        <!-- Associated Accounts List -->
        <div class="mt-8 bg-white shadow-xl rounded-lg">
            <div class="card-header bg-gray-50 px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-medium text-gray-700">Associated Bank Accounts</h3>
            </div>
            <div class="card-body p-0">
                <div v-if="isLoadingAccounts" class="p-6 text-center text-gray-500">Loading accounts...</div>
                <div v-if="accountsError" class="p-6 text-red-500">{{ accountsError }}</div>
                <div v-if="!isLoadingAccounts && accounts && accounts.length > 0" class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-100"><tr><th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Acc #</th><th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th><th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Balance</th><th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th><th class="px-4 py-2"></th></tr></thead>
                        <tbody class="divide-y divide-gray-200">
                            <tr v-for="acc in accounts" :key="acc.account_id" class="hover:bg-gray-50">
                                <td class="px-4 py-3 text-sm font-medium text-gray-900">{{acc.account_number}}</td>
                                <td class="px-4 py-3 text-sm text-gray-600">{{acc.account_type}}</td>
                                <td class="px-4 py-3 text-sm text-right tabular-nums">{{acc.balance.toFixed(2)}} {{acc.currency}}</td>
                                <td class="px-4 py-3 text-sm"><span :class="['px-2 py-0.5 text-xs font-semibold rounded-full', accountStatusClass(acc.status_name)]">{{acc.status_name}}</span></td>
                                <td class="px-4 py-3 text-sm"><router-link :to="{ name: 'AdminAccountDetail', params: { accountId: acc.account_id } }" class="text-admin-accent hover:underline">View</router-link></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                 <p v-if="!isLoadingAccounts && accounts && accounts.length === 0" class="p-6 text-sm text-gray-600">No bank accounts found for this customer.</p>
            </div>
        </div>

        <div class="mt-6">
            <router-link :to="{ name: 'AdminCustomerList' }" class="btn-admin-secondary-outline">
                <i class="fas fa-arrow-left mr-2"></i> Back to Customer List
            </router-link>
        </div>
    </div>
     <div v-else-if="!isLoading && !error">
        <p class="text-center text-gray-500">Customer not found.</p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import adminApiClient from '@/services/adminApiClient';
import type { CustomerDetails, AccountDetails, UserSchema } from '@/models';

export default defineComponent({
  name: 'CustomerDetailView',
  props: {
    customerId: { type: [String, Number], required: true },
  },
  setup(props) {
    const customer = ref<CustomerDetails | null>(null);
    const accounts = ref<AccountDetails[]>([]);
    const linkedUser = ref<Partial<UserSchema> | null>(null); // Only store parts needed like username, role
    const isLoading = ref(true);
    const isLoadingAccounts = ref(false);
    const isLoadingUserLink = ref(false);
    const error = ref<string | null>(null);
    const accountsError = ref<string | null>(null);

    const fetchCustomerData = async () => {
      isLoading.value = true; error.value = null;
      isLoadingAccounts.value = true; accountsError.value = null;
      isLoadingUserLink.value = true;
      try {
        const response = await adminApiClient.get<CustomerDetails>(`/api/admin/customers/${props.customerId}`);
        customer.value = response.data;

        // Fetch associated accounts
        try {
            const accResponse = await adminApiClient.get<any>(`/api/admin/accounts?customer_id_filter=${props.customerId}&per_page=200`); // Assuming AdminAccountListResponse
            accounts.value = accResponse.data.accounts;
        } catch (e_acc) {
            accountsError.value = `Failed to load accounts: ${(e_acc as any).message}`;
        } finally { isLoadingAccounts.value = false; }

        // Attempt to find a user linked to this customer_id
        try {
            // This assumes an endpoint that can find a user by customer_id.
            // Or, if users list is small, list all and filter. For now, placeholder.
            // const userResponse = await adminApiClient.get<any>(`/api/admin/users?customer_id_filter=${props.customerId}`);
            // if (userResponse.data.users && userResponse.data.users.length > 0) {
            //   linkedUser.value = userResponse.data.users[0];
            // }
            // This is complex and might not be a direct 1-1 link always.
            // For now, this part is conceptual.
            console.warn("Fetching linked user by customer_id is conceptual for admin view.");
        } catch (e_user) {
            console.error("Error fetching linked user:", e_user);
        } finally { isLoadingUserLink.value = false; }

      } catch (err: any) {
        error.value = err.response?.data?.detail || `Failed to load customer: ${err.message}`;
      } finally { isLoading.value = false;}
    };

    const accountStatusClass = (statusName: string) => {
      if (statusName === 'active') return 'bg-green-100 text-green-800';
      if (statusName === 'frozen') return 'bg-yellow-100 text-yellow-800';
      if (statusName === 'closed') return 'bg-red-100 text-red-800';
      return 'bg-gray-100 text-gray-800';
    };

    onMounted(fetchCustomerData);

    return { customer, accounts, linkedUser, isLoading, error, accountsError, isLoadingAccounts, isLoadingUserLink, accountStatusClass };
  },
});
</script>

<style scoped>
.tabular-nums { font-variant-numeric: tabular-nums; }
.btn-admin-primary, .btn-admin-secondary-outline { /* Define if not global */
  @apply py-2 px-4 font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-primary { @apply bg-admin-primary text-white hover:bg-blue-700 focus:ring-blue-500; }
.btn-admin-secondary-outline { @apply bg-white text-gray-600 border border-gray-300 hover:bg-gray-50 focus:ring-admin-primary; }
</style>
```
