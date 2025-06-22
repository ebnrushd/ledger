<template>
  <div class="dashboard-view container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-3xl font-semibold text-gray-800">Customer Dashboard</h2>
      <button @click="handleLogout"
              class="px-4 py-2 bg-secondary text-white rounded hover:bg-gray-700 transition duration-150">
        Logout
      </button>
    </div>
    <p class="text-lg text-gray-600 mb-8">Welcome back, <span class="font-medium text-primary">{{ authUser?.username || 'User' }}</span>!</p>

    <div v-if="isLoadingAccounts" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
      <p class="mt-2 text-gray-600">Loading account data...</p>
    </div>
    <div v-if="accountsError"
         class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md" role="alert">
      <p class="font-bold">Error Loading Accounts</p>
      <p>{{ accountsError }}</p>
    </div>

    <div v-if="!isLoadingAccounts && !accountsError">
      <h3 class="text-2xl font-semibold text-gray-700 mb-4">Your Accounts</h3>
      <div v-if="accounts && accounts.length > 0"
           class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="account in accounts" :key="account.account_id"
             class="account-card bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300">
          <div class="flex justify-between items-center mb-2">
            <h4 class="text-xl font-semibold text-primary">{{ account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1) }}</h4>
            <span :class="['px-3 py-1 text-xs font-semibold rounded-full', accountStatusClass(account.status_name)]">
              {{ account.status_name.replace("_", " ") }}
            </span>
          </div>
          <p class="text-gray-600"><strong>Number:</strong> {{ account.account_number }}</p>
          <p class="text-2xl font-bold text-gray-800 my-3">
            {{ account.balance.toFixed(2) }}
            <span class="text-sm text-gray-500">{{ account.currency }}</span>
          </p>
          <p class="text-sm text-gray-500">Overdraft Limit: {{ account.overdraft_limit.toFixed(2) }} {{ account.currency }}</p>
          <div class="mt-4 text-right">
            <router-link
              :to="{ name: 'AccountDetails', params: { accountId: account.account_id } }"
              class="inline-block px-4 py-2 bg-primary text-white text-sm font-medium rounded hover:bg-green-600 transition duration-150">
              View Details
            </router-link>
          </div>
        </div>
      </div>
      <div v-else class="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 rounded-md">
        <p>You currently have no accounts.
           <router-link to="/open-account" v-if="false" class="font-medium text-primary hover:underline">Open one now!</router-link> {/* Placeholder */}
        </p>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, computed } from 'vue';
import { useAuthStore } from '@/store/auth';
import { useAccountsStore } from '@/store/accounts';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';

export default defineComponent({
  name: 'DashboardView',
  setup() {
    const authStore = useAuthStore();
    const accountsStore = useAccountsStore();
    const router = useRouter();

    const { user: authUser, isUserAuthenticated } = storeToRefs(authStore);
    const { accounts, isLoading: isLoadingAccounts, error: accountsError } = storeToRefs(accountsStore);

    const fetchUserAccounts = () => {
      if (isUserAuthenticated.value) {
        accountsStore.fetchAccounts();
      }
    };

    const handleLogout = () => {
      authStore.logout(router);
    };

    onMounted(() => {
      fetchUserAccounts();
    });

    const accountStatusClass = (statusName: string) => {
      if (statusName === 'active') return 'bg-green-200 text-green-800';
      if (statusName === 'frozen') return 'bg-yellow-200 text-yellow-800';
      if (statusName === 'closed') return 'bg-red-200 text-red-800';
      return 'bg-gray-200 text-gray-800';
    };

    return {
      authUser,
      accounts,
      isLoadingAccounts,
      accountsError,
      handleLogout,
      accountStatusClass,
    };
  },
});
</script>

<style scoped>
/* Scoped styles can complement Tailwind if needed for very specific things */
/* For example, a custom spinner if not using a Tailwind one in template */
.account-card p strong { /* Tailwind's font-medium is often enough for 'strong' */
  @apply font-medium text-gray-700;
}
</style>
```
