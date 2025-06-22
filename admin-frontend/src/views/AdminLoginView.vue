<template>
  <div class="admin-login-view p-4">
    <h2 class="text-2xl font-bold text-center text-gray-800 mb-6">Admin Login</h2>
    <form @submit.prevent="handleLogin" class="space-y-5">
      <div>
        <label for="username" class="block text-sm font-medium text-gray-700">Username (Email):</label>
        <input type="text" id="username" v-model="username" required
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm" />
      </div>
      <div>
        <label for="password" class="block text-sm font-medium text-gray-700">Password:</label>
        <input type="password" id="password" v-model="password" required
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm" />
      </div>
      <div v-if="errorMessage" class="p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">
        {{ errorMessage }}
      </div>
      <button type="submit" :disabled="isLoading"
              class="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-admin-primary hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-admin-primary disabled:opacity-60 disabled:cursor-not-allowed">
        {{ isLoading ? 'Logging in...' : 'Login' }}
      </button>
    </form>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAdminAuthStore } from '@/store/adminAuth'; // Use the new admin auth store

export default defineComponent({
  name: 'AdminLoginView',
  setup() {
    const username = ref('');
    const password = ref('');
    const router = useRouter();
    const route = useRoute();
    const authStore = useAdminAuthStore();

    // Use computed properties for reactive error and loading state from store
    const errorMessage = computed(() => authStore.authError);
    const isLoading = computed(() => authStore.isLoading);

    onMounted(() => {
      authStore.authError = null; // Clear any previous login errors on component mount
    });

    const handleLogin = async () => {
      // isLoading state is managed by the store action
      // errorMessage will be updated by the store action if login fails
      const success = await authStore.login({
          username: username.value,
          password: password.value
      });

      if (success) {
        const redirectPath = route.query.redirect as string || '/dashboard';
        router.push(redirectPath);
      }
      // If login fails, errorMessage computed property will update from store's authError
    };

    return {
      username,
      password,
      errorMessage, // Now a computed ref to store's error
      isLoading,    // Now a computed ref to store's loading state
      handleLogin,
    };
  },
});
</script>

<style scoped>
/* Using Tailwind classes directly in template. */
</style>
```
