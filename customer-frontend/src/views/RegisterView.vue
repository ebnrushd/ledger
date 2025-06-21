<template>
  <div class="register-view">
    <h2 class="text-2xl font-bold text-center text-gray-800 mb-8">Create Your Account</h2>
    <form @submit.prevent="handleRegister" class="space-y-4">
      <div>
        <label for="firstName" class="block text-sm font-medium text-gray-700">First Name:</label>
        <input type="text" id="firstName" v-model="firstName" required
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" />
      </div>
      <div>
        <label for="lastName" class="block text-sm font-medium text-gray-700">Last Name:</label>
        <input type="text" id="lastName" v-model="lastName" required
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" />
      </div>
      <div>
        <label for="email" class="block text-sm font-medium text-gray-700">Email (used as username):</label>
        <input type="email" id="email" v-model="email" required
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" />
      </div>
      <div>
        <label for="password" class="block text-sm font-medium text-gray-700">Password:</label>
        <input type="password" id="password" v-model="password" required
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" />
      </div>
      <div>
        <label for="confirmPassword" class="block text-sm font-medium text-gray-700">Confirm Password:</label>
        <input type="password" id="confirmPassword" v-model="confirmPassword" required
               class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm" />
      </div>

      <div v-if="clientErrorMessage" class="p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">
        {{ clientErrorMessage }}
      </div>
      <div v-if="authStore.registerError" class="p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">
        {{ authStore.registerError }}
      </div>
      <div v-if="authStore.registerSuccessMessage" class="p-3 bg-green-100 text-green-700 border border-green-400 rounded-md text-sm">
        {{ authStore.registerSuccessMessage }}
      </div>

      <button type="submit" :disabled="authStore.isLoading || isLoading"
              class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed">
        {{ authStore.isLoading || isLoading ? 'Registering...' : 'Register' }}
      </button>
    </form>
     <p class="mt-6 text-center text-sm">
      Already have an account? <router-link to="/login" class="font-medium text-primary hover:text-green-600">Login here</router-link>
    </p>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/store/auth';

export default defineComponent({
  name: 'RegisterView',
  setup() {
    const firstName = ref('');
    const lastName = ref('');
    const email = ref('');
    const password = ref('');
    const confirmPassword = ref('');
    const clientErrorMessage = ref<string | null>(null); // For client-side validation errors
    // isLoading for this component might be slightly different from store's global isLoading if needed
    const isLoading = ref(false); // Local loading state for form submission process

    const router = useRouter();
    const authStore = useAuthStore();

    // Watch inputs to clear client-side error and potentially store errors
    watch([firstName, lastName, email, password, confirmPassword], () => {
        clientErrorMessage.value = null;
        if(authStore.registerError) authStore.registerError = null; // Clear store error on new input
        if(authStore.registerSuccessMessage) authStore.registerSuccessMessage = null;
    });
    onMounted(() => { // Clear messages on component load
        authStore.clearTransferStatus(); // This clears transfer messages, should be more generic or specific
        authStore.registerError = null;
        authStore.registerSuccessMessage = null;
    });


    const handleRegister = async () => {
      isLoading.value = true; // Use local isLoading for the button disable state during this action
      clientErrorMessage.value = null;
      authStore.registerError = null;
      authStore.registerSuccessMessage = null;

      if (password.value !== confirmPassword.value) {
        clientErrorMessage.value = 'Passwords do not match.';
        isLoading.value = false;
        return;
      }
      if (password.value.length < 8) {
        clientErrorMessage.value = 'Password must be at least 8 characters long.';
        isLoading.value = false;
        return;
      }

      try {
        await authStore.register({
          username: email.value,
          email: email.value,
          password: password.value,
          first_name: firstName.value,
          last_name: lastName.value,
        });

        if (authStore.registerSuccessMessage) {
            // Form can be cleared here if desired
            firstName.value = ''; lastName.value = ''; email.value = '';
            password.value = ''; confirmPassword.value = '';

            setTimeout(() => { // Keep success message for a bit before redirect
                router.push('/login?registration_success=true');
            }, 2000);
        }
      } catch (error: any) {
        // Error message is already set in authStore.registerError by the store action
        // clientErrorMessage.value could be used for errors not from store.
        console.error('Register view error (already set in store):', error);
      } finally {
        isLoading.value = false;
      }
    };

    return {
      firstName, lastName, email, password, confirmPassword,
      clientErrorMessage, // For client-side form validation errors
      isLoading, // Local loading state for form
      authStore, // To access store's error/success messages and isLoading directly in template
      handleRegister,
    };
  },
});
</script>

<style scoped>
/* Styles are primarily Tailwind utility classes. */
/* AuthLayout handles centering and max-width. */
</style>
```
