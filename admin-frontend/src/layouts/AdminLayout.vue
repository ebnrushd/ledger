<template>
  <div class="admin-layout flex h-screen bg-admin-light-gray">
    <!-- Sidebar -->
    <aside class="w-64 bg-admin-secondary text-gray-100 p-4 space-y-6 fixed h-full shadow-lg">
      <div class="text-center py-2">
          <router-link :to="{ name: 'AdminDashboard' }" class="text-2xl font-semibold hover:text-gray-300">Admin Panel</router-link>
      </div>
      <nav class="mt-10">
        <router-link
            :to="{ name: 'AdminDashboard' }"
          class="flex items-center py-2.5 px-4 rounded transition duration-200 hover:bg-gray-700 hover:text-white"
          active-class="bg-gray-700 text-white"
        >
          <i class="fas fa-tachometer-alt mr-3"></i> Dashboard
        </router-link>
        <router-link
            :to="{ name: 'AdminUserList' }"
          class="flex items-center py-2.5 px-4 rounded transition duration-200 hover:bg-gray-700 hover:text-white"
          active-class="bg-gray-700 text-white"
        >
          <i class="fas fa-users mr-3"></i> Users
        </router-link>
        <router-link
            :to="{ name: 'AdminAccountList' }"
          class="flex items-center py-2.5 px-4 rounded transition duration-200 hover:bg-gray-700 hover:text-white"
          active-class="bg-gray-700 text-white"
        >
          <i class="fas fa-university mr-3"></i> Accounts
        </router-link>
         <router-link
            :to="{ name: 'AdminCustomerList' }"  {# Assuming AdminCustomerList route name #}
          class="flex items-center py-2.5 px-4 rounded transition duration-200 hover:bg-gray-700 hover:text-white"
          active-class="bg-gray-700 text-white"
        >
            <i class="fas fa-user-tie mr-3"></i> Customers
        </router-link>
         <router-link
            :to="{ name: 'AdminTransactionList' }" {# Assuming AdminTransactionList route name #}
          class="flex items-center py-2.5 px-4 rounded transition duration-200 hover:bg-gray-700 hover:text-white"
          active-class="bg-gray-700 text-white"
        >
            <i class="fas fa-exchange-alt mr-3"></i> Transactions
        </router-link>
        <router-link
            :to="{ name: 'AdminAuditLogList' }" {# Assuming AdminAuditLogList route name #}
          class="flex items-center py-2.5 px-4 rounded transition duration-200 hover:bg-gray-700 hover:text-white"
          active-class="bg-gray-700 text-white"
        >
            <i class="fas fa-history mr-3"></i> Audit Logs
        </router-link>
      </nav>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col overflow-hidden ml-64"> {# Adjust ml-64 to match sidebar width #}
      <!-- Header -->
      <header class="bg-white shadow-md p-4 flex justify-between items-center">
        <div>
          <h1 class="text-xl font-semibold text-gray-700">{{ $route.meta.title || 'Admin Page' }}</h1>
        </div>
        <div v-if="adminUsername" class="flex items-center">
          <span class="text-gray-600 text-sm">
            Welcome, {{ adminUsername }} <span v-if="adminRoleName">({{ adminRoleName }})</span>
          </span>
          <button @click="handleLogout" class="ml-4 text-sm text-admin-primary hover:underline focus:outline-none">Logout</button>
        </div>
        <div v-else>
            <span class="text-gray-500 text-sm">Not logged in</span>
        </div>
      </header>

      <!-- Page Content -->
      <main class="flex-1 overflow-x-hidden overflow-y-auto bg-admin-light-gray p-6">
        <router-view />
      </main>
    </div>
  </div>
  <!-- Font Awesome for icons - Add to index.html if not already present -->
  <!-- <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" /> -->
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { useRouter } from 'vue-router';
// Import auth store if available for logout and user display
// import { useAuthStore } from '@/store/authAdmin'; // Assuming a separate admin auth store

export default defineComponent({
  name: 'AdminLayout',
  setup() {
    const router = useRouter();
    const authStore = useAdminAuthStore();

    const handleLogout = async () => {
      // isLoading state can be used from authStore if logout action sets it
      await authStore.logout();
      // The store's logout action should handle redirecting via window.location or passed router.
      // If it doesn't, or for certainty:
      router.push({ name: 'AdminLogin', query: { logged_out: 'true' } });
    };

    // Expose user details for header display
    const adminUsername = computed(() => authStore.getAdminUser?.username);
    const adminRoleName = computed(() => authStore.getAdminUser?.role_name);


    return {
      handleLogout,
      adminUsername,
      adminRoleName,
      // authStore, // Can also pass whole store if preferred for template
    };
  },
});
</script>

<style scoped>
/* Using Font Awesome, ensure it's included in your project or via CDN in index.html */
/* Example for active class if not using active-class prop directly */
/* .router-link-active, .router-link-exact-active {
  background-color: theme('colors.gray.700');
  color: theme('colors.white');
} */
</style>
```
