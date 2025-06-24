<template>
  <div class="admin-dashboard-view p-4 md:p-6 lg:p-8 space-y-8">
    <!-- Page Title is handled by AdminLayout using $route.meta.title -->

    <div v-if="dashboardStore.isLoading" class="flex justify-center items-center min-h-[300px]">
      <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-admin-primary"></div>
      <p class="ml-4 text-xl text-gray-600">Loading dashboard data...</p>
    </div>

    <div v-if="dashboardStore.error"
         class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 rounded-md shadow-md" role="alert">
      <div class="flex">
        <div class="py-1"><i class="fas fa-exclamation-triangle text-red-400 mr-3 text-xl"></i></div>
        <div>
          <p class="font-bold">Error Loading Dashboard</p>
          <p class="text-sm">{{ dashboardStore.error }}</p>
        </div>
      </div>
    </div>

    <div v-if="!dashboardStore.isLoading && !dashboardStore.error && dashboardStore.dashboardData" class="space-y-8">
      <!-- Stats Cards Section -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 gap-6">
        <div class="stat-card group">
          <div class="stat-icon bg-blue-500 group-hover:bg-blue-600">
            <i class="fas fa-users text-white text-3xl"></i>
          </div>
          <div class="stat-content">
            <p class="stat-title">Total Customers</p>
            <p class="stat-value">{{ dashboardStore.dashboardData.total_customers }}</p>
          </div>
        </div>
        <div class="stat-card group">
          <div class="stat-icon bg-green-500 group-hover:bg-green-600">
            <i class="fas fa-university text-white text-3xl"></i>
          </div>
          <div class="stat-content">
            <p class="stat-title">Total Accounts</p>
            <p class="stat-value">{{ dashboardStore.dashboardData.total_accounts }}</p>
          </div>
        </div>
        <div class="stat-card group">
          <div class="stat-icon bg-yellow-500 group-hover:bg-yellow-600">
            <i class="fas fa-dollar-sign text-white text-3xl"></i>
          </div>
          <div class="stat-content">
            <p class="stat-title">System Balance</p>
            <p class="stat-value">{{ dashboardStore.dashboardData.total_system_balance_sum.toFixed(2) }}</p>
            <p class="text-xs text-gray-400 group-hover:text-gray-200">{{ dashboardStore.dashboardData.total_system_balance_currency_note }}</p>
          </div>
        </div>
        <div class="stat-card group">
          <div class="stat-icon bg-purple-500 group-hover:bg-purple-600">
            <i class="fas fa-history text-white text-3xl"></i>
          </div>
          <div class="stat-content">
            <p class="stat-title">Transactions (24h)</p>
            <p class="stat-value">{{ dashboardStore.dashboardData.transactions_last_24h }}</p>
          </div>
        </div>
      </div>

      <!-- Recent Transactions Table Section -->
      <div class="bg-white p-6 rounded-xl shadow-lg">
          <h2 class="text-2xl font-semibold text-gray-700 mb-5 border-b pb-3">Recent Transactions</h2>
          <div v-if="dashboardStore.dashboardData.recent_transactions && dashboardStore.dashboardData.recent_transactions.length > 0" class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-100">
                      <tr>
                          <th class="table-header">ID</th>
                          <th class="table-header">Timestamp</th>
                          <th class="table-header">Account #</th>
                          <th class="table-header">Type</th>
                          <th class="table-header text-right">Amount</th>
                          <th class="table-header">Description</th>
                      </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="tx in dashboardStore.dashboardData.recent_transactions" :key="tx.id" class="hover:bg-gray-50 transition-colors duration-150">
                          <td class="table-cell">
                            <router-link :to="{ name: 'AdminTransactionDetail', params: { transactionId: tx.id } }" class="text-admin-primary hover:underline">{{ tx.id }}</router-link>
                          </td>
                          <td class="table-cell">{{ new Date(tx.timestamp).toLocaleString() }}</td>
                          <td class="table-cell">
                            <!-- Assuming AdminAccountDetail route exists and tx.account_id is available on recent tx object -->
                            <!-- For now, AdminDashboardRecentTransaction has account_number, not account_id -->
                             {{ tx.account_number }}
                            <!-- <router-link :to="{ name: 'AdminAccountDetail', params: { accountId: tx.account_id } }" class="text-admin-primary hover:underline">{{ tx.account_number }}</router-link> -->
                          </td>
                          <td class="table-cell">{{ tx.type.replace("_", " ").charAt(0).toUpperCase() + tx.type.replace("_", " ").slice(1) }}</td>
                          <td class="table-cell text-right font-mono" :class="tx.amount < 0 ? 'text-red-600' : 'text-green-600'">{{ tx.amount.toFixed(2) }}</td>
                          <td class="table-cell max-w-xs truncate" :title="tx.description">{{ tx.description || '-' }}</td>
                      </tr>
                  </tbody>
              </table>
          </div>
          <p v-else class="text-center text-gray-500 py-4">No recent transactions found.</p>
      </div>

      <!-- Quick Links Section -->
      <div class="bg-white p-6 rounded-xl shadow-lg">
        <h2 class="text-2xl font-semibold text-gray-700 mb-5 border-b pb-3">Quick Links</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            <router-link :to="{ name: 'AdminUserList' }" class="quick-link group">
                <i class="fas fa-users text-2xl mb-2"></i> Manage Users
            </router-link>
            <router-link :to="{ name: 'AdminAccountList' }" class="quick-link group">
                <i class="fas fa-university text-2xl mb-2"></i> Manage Accounts
            </router-link>
            <router-link :to="{ name: 'AdminCustomerList' }" class="quick-link group">
                <i class="fas fa-user-tie text-2xl mb-2"></i> View Customers
            </router-link>
            <router-link :to="{ name: 'AdminTransactionList' }" class="quick-link group">
                <i class="fas fa-exchange-alt text-2xl mb-2"></i> All Transactions
            </router-link>
            <router-link :to="{ name: 'AdminAuditLogList' }" class="quick-link group">
                <i class="fas fa-history text-2xl mb-2"></i> Audit Logs
            </router-link>
        </div>
      </div>

    </div>
    <div v-else-if="!dashboardStore.isLoading && !dashboardStore.error && !dashboardStore.dashboardData">
        <p class="text-center text-gray-500 py-10 text-lg">No dashboard data available at this time.</p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted } from 'vue';
import { useAdminDashboardStore } from '@/store/adminDashboard';
// storeToRefs can be used if destructuring store properties, but direct store access is fine too.
// import { storeToRefs } from 'pinia';

export default defineComponent({
  name: 'AdminDashboardView',
  setup() {
    const dashboardStore = useAdminDashboardStore();

    onMounted(() => {
      dashboardStore.fetchDashboardData();
    });

    // Expose the whole store instance to the template
    return {
      dashboardStore,
    };
  },
});
</script>

<style scoped>
.stat-card {
  @apply bg-white p-5 rounded-xl shadow-lg flex items-center space-x-4 transform transition-all duration-300 ease-in-out;
}
.stat-card:hover {
  @apply shadow-2xl -translate-y-1;
}
.stat-icon {
  @apply p-4 rounded-full flex items-center justify-center transition-colors duration-300;
}
.stat-content .stat-title {
  @apply text-sm text-gray-500 uppercase tracking-wider group-hover:text-gray-200;
}
.stat-content .stat-value {
  @apply text-3xl font-bold text-gray-800 group-hover:text-white;
}
.stat-card:hover .stat-content .stat-title,
.stat-card:hover .stat-content .stat-value,
.stat-card:hover .stat-content .text-xs {
    @apply text-white;
}
.stat-card:hover .stat-icon i { /* Ensure icon color contrasts with hover background */
    /* This might need specific icon color changes if default text-white isn't enough due to parent hover */
}

/* Blue card hover */
.stat-card:hover .bg-blue-500 { @apply bg-blue-600; }
/* Green card hover */
.stat-card:hover .bg-green-500 { @apply bg-green-600; }
/* Yellow card hover */
.stat-card:hover .bg-yellow-500 { @apply bg-yellow-600; }
/* Purple card hover */
.stat-card:hover .bg-purple-500 { @apply bg-purple-600; }


.table-header {
  @apply px-5 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider bg-gray-100;
}
.table-cell {
  @apply px-5 py-4 whitespace-nowrap text-sm text-gray-700;
}
.quick-link {
  @apply flex flex-col items-center justify-center p-4 bg-gray-50 rounded-lg text-gray-700 hover:bg-admin-primary hover:text-white transition-all duration-200 ease-in-out shadow hover:shadow-lg;
  min-height: 100px; /* Ensure consistent height */
}
.quick-link i {
  @apply text-3xl mb-2 text-gray-400 group-hover:text-white transition-colors duration-200;
}
</style>
```
