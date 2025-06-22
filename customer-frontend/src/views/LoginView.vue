<template>
  <div class="login-view">
    <h2 class="text-2xl font-bold text-center text-gray-800 mb-8">Login to Your Account</h2>
    <form @submit.prevent="handleLogin" class="space-y-6">
      <div>
        <label for="username" class="block text-sm font-medium text-gray-700">Username (Email):</label>
        <input type="email" id="username" v-model="username"
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
               required />
      </div>
      <div>
        <label for="password" class="block text-sm font-medium text-gray-700">Password:</label>
        <input type="password" id="password" v-model="password"
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
               required />
      </div>

      <div v-if="errorMessage" class="p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">
        {{ errorMessage }}
      </div>

      <button type="submit" :disabled="isLoading"
              class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed">
        {{ isLoading ? 'Logging in...' : 'Login' }}
      </button>
    </form>
    <p class="mt-6 text-center text-sm">
      Don't have an account?
      <router-link to="/register" class="font-medium text-primary hover:text-green-600">Register here</router-link>
    </p>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, watch, onMounted } from 'vue'; // Added watch, onMounted, computed
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/store/auth';

export default defineComponent({
  name: 'LoginView',
  setup() {
    const username = ref('');
    const password = ref('');
    const authStore = useAuthStore();
    const router = useRouter();
    const route = useRoute();

    // Use computed properties to react to store changes for error and loading
    const errorMessage = computed(() => authStore.loginError);
    const isLoading = computed(() => authStore.isLoading);

    // Clear previous login errors when component is mounted or inputs change
    const clearError = () => {
      if (authStore.loginError) {
        authStore.loginError = null; // Reset error in store
      }
    };
    watch([username, password], clearError);
    onMounted(clearError);


    const handleLogin = async () => {
      // isLoading is reactive via computed property from store
      // errorMessage is reactive via computed property from store
      try {
        await authStore.login({ username: username.value, password: password.value });
        // On successful login, Pinia action updates isAuthenticated.
        // The router guard will then allow navigation or redirect from /login.
        const redirectPath = route.query.redirect as string | undefined;
        router.push(redirectPath || '/dashboard');
      } catch (error: any) {
        // Error message is already set in authStore.loginError by the store action
        console.error('Login view error (already set in store):', error);
      }
      // isLoading is managed by the store action
    };

    return {
      username,
      password,
      handleLogin,
      errorMessage,
      isLoading,
    };
  },
});
</script>

<style scoped>
/* Styles are primarily Tailwind utility classes. */
/* AuthLayout already handles centering and max-width for the form container. */
</style>
```
