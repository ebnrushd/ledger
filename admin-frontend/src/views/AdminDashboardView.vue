<template>
  <div class="admin-dashboard-view p-6">
    <!-- Page Title is now handled by AdminLayout using $route.meta.title -->
    <!-- <h1 class="text-3xl font-semibold text-gray-800 mb-6">Admin Dashboard</h1> -->

    <div v-if="dashboardStore.isLoading" class="text-center py-10">
      <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-admin-primary mx-auto"></div>
      <p class="mt-4 text-lg text-gray-600">Loading dashboard data...</p>
    </div>

    <div v-if="dashboardStore.error"
         class="bg-red-100 border-l-4 border-red-500 text-red-700 p-6 mb-6 rounded-md shadow-md" role="alert">
      <p class="font-bold text-lg mb-2">Error Loading Dashboard</p>
      <p>{{ dashboardStore.error }}</p>
    </div>

    <div v-if="!dashboardStore.isLoading && !dashboardStore.error && dashboardStore.dashboardData" class="space-y-8">
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="stat-card bg-white p-6 rounded-xl shadow-lg flex items-center space-x-4 hover:shadow-2xl transition-shadow">
          <div><i class="fas fa-users text-4xl text-blue-500"></i></div>
          <div>
            <p class="text-sm text-gray-500 uppercase tracking-wider">Total Customers</p>
            <p class="text-3xl font-bold text-gray-800">{{ dashboardStore.dashboardData.total_customers }}</p>
          </div>
        </div>
        <div class="stat-card bg-white p-6 rounded-xl shadow-lg flex items-center space-x-4 hover:shadow-2xl transition-shadow">
          <div><i class="fas fa-university text-4xl text-green-500"></i></div>
          <div>
            <p class="text-sm text-gray-500 uppercase tracking-wider">Total Accounts</p>
            <p class="text-3xl font-bold text-gray-800">{{ dashboardStore.dashboardData.total_accounts }}</p>
          </div>
        </div>
        <div class="stat-card bg-white p-6 rounded-xl shadow-lg flex items-center space-x-4 hover:shadow-2xl transition-shadow">
          <div><i class="fas fa-dollar-sign text-4xl text-yellow-500"></i></div>
          <div>
            <p class="text-sm text-gray-500 uppercase tracking-wider">System Balance</p>
            <p class="text-3xl font-bold text-gray-800">{{ dashboardStore.dashboardData.total_system_balance_sum.toFixed(2) }}</p>
            <p class="text-xs text-gray-400">{{ dashboardStore.dashboardData.total_system_balance_currency_note }}</p>
          </div>
        </div>
        <div class="stat-card bg-white p-6 rounded-xl shadow-lg flex items-center space-x-4 hover:shadow-2xl transition-shadow">
          <div><i class="fas fa-history text-4xl text-purple-500"></i></div>
          <div>
            <p class="text-sm text-gray-500 uppercase tracking-wider">Transactions (24h)</p>
            <p class="text-3xl font-bold text-gray-800">{{ dashboardStore.dashboardData.transactions_last_24h }}</p>
          </div>
        </div>
      </div>

      <!-- Recent Transactions Table -->
      <div class="bg-white p-6 rounded-xl shadow-lg">
          <h2 class="text-2xl font-semibold text-gray-700 mb-4">Recent Transactions</h2>
          <div v-if="dashboardStore.dashboardData.recent_transactions && dashboardStore.dashboardData.recent_transactions.length > 0" class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-100">
                      <tr>
                          <th class="px-5 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">ID</th>
                          <th class="px-5 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Timestamp</th>
                          <th class="px-5 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Account #</th>
                          <th class="px-5 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Type</th>
                          <th class="px-5 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">Amount</th>
                          <th class="px-5 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Description</th>
                      </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="tx in dashboardStore.dashboardData.recent_transactions" :key="tx.id" class="hover:bg-gray-50 transition-colors">
                          <td class="px-5 py-4 whitespace-nowrap text-sm text-gray-700">
                            <router-link :to="{ name: 'AdminTransactionDetail', params: { transactionId: tx.id } }" class="text-admin-primary hover:underline">{{ tx.id }}</router-link>
                          </td>
                          <td class="px-5 py-4 whitespace-nowrap text-sm text-gray-700">{{ new Date(tx.timestamp).toLocaleString() }}</td>
                          <td class="px-5 py-4 whitespace-nowrap text-sm text-gray-700">
                            <!-- Assuming account_id is available on tx for linking. The current AdminDashboardRecentTransaction doesn't have account_id.
                                 This should be added to the backend response if linking is desired.
                                 For now, just displaying number.
                            -->
                            {{ tx.account_number }}
                          </td>
                          <td class="px-5 py-4 whitespace-nowrap text-sm text-gray-700">{{ tx.type.replace("_", " ")|title }}</td>
                          <td class="px-5 py-4 whitespace-nowrap text-sm font-medium text-right" :class="tx.amount < 0 ? 'text-red-600' : 'text-green-600'">{{ tx.amount.toFixed(2) }}</td>
                          <td class="px-5 py-4 whitespace-nowrap text-sm text-gray-500 max-w-xs truncate" :title="tx.description">{{ tx.description || '-' }}</td>
                      </tr>
                  </tbody>
              </table>
          </div>
          <p v-else class="text-center text-gray-500 py-4">No recent transactions found.</p>
      </div>
    </div>
    <div v-else-if="!dashboardStore.isLoading && !dashboardStore.error && !dashboardStore.dashboardData">
        <p class="text-center text-gray-500 py-10">No dashboard data available.</p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted } from 'vue';
import { useAdminDashboardStore } from '@/store/adminDashboard';
import { storeToRefs } from 'pinia'; // To make store state reactive in setup

export default defineComponent({
  name: 'AdminDashboardView',
  setup() {
    const dashboardStore = useAdminDashboardStore();

    // Use storeToRefs to get reactive access to store properties
    // This is not strictly necessary if you always use `dashboardStore.property` in template,
    // but can be convenient if you want to destructure or pass to other composables.
    // For direct template usage, `dashboardStore` itself is enough.
    // const { dashboardData, isLoading, error } = storeToRefs(dashboardStore);

    onMounted(() => {
      dashboardStore.fetchDashboardData();
    });

    // The template directly uses dashboardStore.isLoading, dashboardStore.error, dashboardStore.dashboardData
    return {
      dashboardStore, // Provide the whole store instance to the template
    };
  },
});
</script>

<style scoped>
/* Using Tailwind classes directly in template. Add FontAwesome via index.html for icons */
.stat-card:hover {
    transform: translateY(-3px);
}
.tabular-nums {
    font-variant-numeric: tabular-nums;
}
/* Add Font Awesome to index.html or main.ts using imports if you want to use these icons:
   Example: @import '@fortawesome/fontawesome-free/css/all.min.css';
   Or via CDN in index.html.
   The AdminLayout.vue also uses fas icons.
*/
</style>
```
