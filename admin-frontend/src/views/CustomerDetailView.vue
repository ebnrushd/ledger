<template>
  <div class="customer-detail-view p-4 md:p-6 lg:p-8">
     <div v-if="customersStore.isLoadingDetails" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-admin-primary mx-auto"></div>
      <p class="mt-3 text-gray-600">Loading customer details...</p>
    </div>
    <div v-if="customersStore.error && !customersStore.isLoadingDetails"
         class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 mb-6 rounded-md shadow-md" role="alert">
        <p class="font-bold">Error Loading Customer Details</p>
        <p>{{ customersStore.error }}</p>
         <router-link :to="{ name: 'AdminCustomerList' }" class="mt-2 inline-block btn-admin-secondary-outline text-sm">
            Back to Customer List
        </router-link>
    </div>

    <div v-if="customer && !customersStore.isLoadingDetails && !customersStore.error" class="max-w-4xl mx-auto">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
            <div>
                <h1 class="text-2xl md:text-3xl font-semibold text-gray-800">
                    Customer Profile
                </h1>
                <p class="text-gray-600">Details for <span class="font-medium text-admin-primary">{{ customer.first_name }} {{ customer.last_name }}</span> (ID: {{ customer.customer_id }})</p>
            </div>
            <!-- No edit customer button for now as per view-only spec -->
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Customer Info Card -->
            <div class="lg:col-span-1 bg-white shadow-xl rounded-lg p-6">
                <h3 class="text-xl font-semibold text-gray-700 mb-4 border-b pb-3">Contact Information</h3>
                <dl class="space-y-3">
                    <div><dt class="detail-label">Email:</dt><dd class="detail-value">{{ customer.email }}</dd></div>
                    <div><dt class="detail-label">Phone:</dt><dd class="detail-value">{{ customer.phone_number || 'N/A' }}</dd></div>
                    <div><dt class="detail-label">Address:</dt><dd class="detail-value leading-relaxed">{{ customer.address || 'N/A' }}</dd></div>
                    <div><dt class="detail-label">Profile Created:</dt><dd class="detail-value">{{ new Date(customer.created_at).toLocaleString() }}</dd></div>
                </dl>
            </div>

            <!-- Linked User & Accounts Card -->
            <div class="lg:col-span-2 space-y-6">
                <div v-if="customer.linked_user" class="bg-white shadow-xl rounded-lg p-6">
                    <h3 class="text-lg font-medium text-gray-700 mb-3 border-b pb-2">Linked User Account</h3>
                    <dl class="space-y-2">
                        <div class="flex"><dt class="w-1/3 detail-label">User ID:</dt>
                            <dd class="w-2/3 detail-value">
                                <router-link :to="{ name: 'AdminUserDetail', params: { userId: customer.linked_user.user_id } }" class="text-admin-primary hover:underline">
                                    {{ customer.linked_user.user_id }}
                                </router-link>
                            </dd>
                        </div>
                        <div class="flex"><dt class="w-1/3 detail-label">Username:</dt><dd class="w-2/3 detail-value">{{ customer.linked_user.username }}</dd></div>
                        <div class="flex"><dt class="w-1/3 detail-label">Role:</dt><dd class="w-2/3 detail-value">{{ customer.linked_user.role_name }}</dd></div>
                        <div class="flex"><dt class="w-1/3 detail-label">Status:</dt>
                            <dd class="w-2/3 detail-value">
                                <span :class="['px-2 py-0.5 text-xs font-semibold rounded-full', customer.linked_user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
                                    {{ customer.linked_user.is_active ? 'Active' : 'Inactive' }}
                                </span>
                            </dd>
                        </div>
                    </dl>
                </div>
                <div v-else class="bg-white shadow-xl rounded-lg p-6">
                    <h3 class="text-lg font-medium text-gray-700 mb-2">Linked User Account</h3>
                    <p class="text-sm text-gray-500">No user account is directly linked to this customer profile via `users.customer_id`.</p>
                </div>

                <div class="bg-white shadow-xl rounded-lg">
                    <div class="px-6 py-4 border-b border-gray-200">
                        <h3 class="text-lg font-medium text-gray-700">Bank Accounts ({{ customer.accounts?.length || 0 }})</h3>
                    </div>
                    <div class="p-0">
                        <div v-if="customer.accounts && customer.accounts.length > 0" class="overflow-x-auto">
                            <table class="min-w-full divide-y divide-gray-100">
                                <thead class="bg-gray-50"><tr><th class="table-header-sm">Acc #</th><th class="table-header-sm">Type</th><th class="table-header-sm text-right">Balance</th><th class="table-header-sm">Status</th><th class="table-header-sm"></th></tr></thead>
                                <tbody class="divide-y divide-gray-100">
                                    <tr v-for="acc in customer.accounts" :key="acc.account_id" class="hover:bg-gray-50">
                                        <td class="table-cell-sm font-medium">{{acc.account_number}}</td>
                                        <td class="table-cell-sm">{{acc.account_type.charAt(0).toUpperCase() + acc.account_type.slice(1)}}</td>
                                        <td class="table-cell-sm text-right font-mono">{{acc.balance.toFixed(2)}} {{acc.currency}}</td>
                                        <td class="table-cell-sm"><span :class="['px-2 py-0.5 text-xs font-semibold rounded-full', accountStatusClass(acc.status_name)]">{{acc.status_name}}</span></td>
                                        <td class="table-cell-sm text-center"><router-link :to="{ name: 'AdminAccountDetail', params: { accountId: acc.account_id } }" class="text-admin-accent hover:underline text-xs">View</router-link></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <p v-else class="p-6 text-sm text-gray-600">No bank accounts found for this customer.</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="mt-8">
            <router-link :to="{ name: 'AdminCustomerList' }"
                         class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition">
                <i class="fas fa-arrow-left mr-2"></i> Back to Customer List
            </router-link>
        </div>
    </div>
    <div v-else-if="!customersStore.isLoadingDetails && !customersStore.error && !customer" class="text-center py-10">
        <p class="text-xl text-gray-500">Customer not found or data is unavailable.</p>
         <router-link :to="{ name: 'AdminCustomerList' }" class="mt-4 inline-block btn-admin-secondary-outline text-sm">
            Back to Customer List
        </router-link>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed, onUnmounted } from 'vue';
import { useRoute } from 'vue-router'; // Or use props
import { useAdminCustomersStore } from '@/store/adminCustomers';
import { storeToRefs } from 'pinia';
import type { Account } from '@/types/account'; // For explicit typing if needed for accounts list

export default defineComponent({
  name: 'CustomerDetailView',
  props: {
    customerId: { type: [String, Number], required: true },
  },
  setup(props) {
    const customersStore = useAdminCustomersStore();
    const { selectedCustomer: customer, isLoadingDetails, error } = storeToRefs(customersStore);

    const accountStatusClass = (statusName: string) => {
      if (statusName === 'active') return 'bg-green-100 text-green-800';
      if (statusName === 'frozen') return 'bg-yellow-100 text-yellow-800';
      if (statusName === 'closed') return 'bg-red-100 text-red-800';
      return 'bg-gray-100 text-gray-800';
    };

    onMounted(async () => {
      // Clear previous selection/error before fetching new details
      customersStore.selectedCustomer = null;
      customersStore.error = null; // Assuming error is general for the store, or have specific detailError
      await customersStore.fetchCustomerDetails(props.customerId);
    });

    onUnmounted(() => {
        // Clear selected customer when leaving the page
        customersStore.selectedCustomer = null;
    });

    return {
        customer,
        isLoading: isLoadingDetails, // Alias for template clarity
        error,
        customersStore, // To access store directly if needed
        accountStatusClass
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

.btn-admin-primary, .btn-admin-secondary-outline { /* Define if not global */
  @apply py-2 px-4 font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-primary { @apply bg-admin-primary text-white hover:bg-blue-700 focus:ring-blue-500; }
.btn-admin-secondary-outline { @apply bg-white text-gray-600 border border-gray-300 hover:bg-gray-50 focus:ring-admin-primary; }
</style>
```
