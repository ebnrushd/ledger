<template>
  <div class="default-layout flex flex-col min-h-screen bg-light-gray">
    <header class="app-header bg-secondary text-white shadow-md">
      <div class="container mx-auto px-4 py-3 flex justify-between items-center">
        <router-link to="/" class="text-xl font-semibold hover:text-gray-300">SQL Ledger</router-link>
        <nav class="space-x-4">
          <router-link to="/" class="hover:text-gray-300">Home</router-link>

          <template v-if="authStore.isUserAuthenticated">
            <router-link to="/dashboard" class="hover:text-gray-300">Dashboard</router-link>
            <router-link to="/transfer" class="hover:text-gray-300">Transfer</router-link>
            <router-link to="/profile" class="hover:text-gray-300">Profile</router-link>
            <a href="#" @click.prevent="handleLogout" class="hover:text-gray-300">Logout ({{ authStore.getUser?.username }})</a>
          </template>
          <template v-else>
            <router-link to="/login" class="hover:text-gray-300">Login</router-link>
            <router-link to="/register" class="hover:text-gray-300">Register</router-link>
          </template>
        </nav>
      </div>
    </header>

    <main class="app-main flex-grow container mx-auto px-4 py-8">
      <router-view />
    </main>

    <footer class="app-footer bg-gray-700 text-gray-300 text-center p-4">
      <p>&copy; {{ new Date().getFullYear() }} SQL Ledger Customer Portal. All rights reserved.</p>
    </footer>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { useAuthStore } from '@customer/store/auth';
import { useRouter } from 'vue-router';

export default defineComponent({
  name: 'DefaultLayout',
  setup() {
    const authStore = useAuthStore();
    const router = useRouter();

    const handleLogout = () => {
      authStore.logout(router);
    };

    return {
      authStore,
      handleLogout,
    };
  },
});
</script>

<style scoped>
/* Scoped styles can still be used for layout-specific things not easily done with utilities,
   or for more complex component-like structures within the layout. */
.app-header nav a.router-link-exact-active {
  @apply text-primary font-bold; /* Using Tailwind's @apply for custom active class */
}
</style>
```
