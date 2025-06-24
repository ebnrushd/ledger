<template>
  <div class="auth-layout flex flex-col items-center justify-center min-h-screen bg-light-gray p-4">
    <main class="auth-main w-full max-w-md bg-white p-8 rounded-lg shadow-xl">
      <div class="auth-content">
        <router-view />
      </div>
    </main>
    <footer class="auth-footer mt-6 text-center text-sm text-gray-600">
      <p>&copy; {{ new Date().getFullYear() }} SQL Ledger</p>
      <p><router-link to="/" class="text-primary hover:underline">Back to Home</router-link></p>
    </footer>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'AuthLayout',
});
</script>

<style scoped>
/* AuthLayout specific styles can go here if needed,
   but most should be achievable with Tailwind utilities directly in the template. */
/* For example, if you had a logo specific to the auth pages:
.auth-logo {
  max-width: 150px;
  margin-bottom: 2rem;
}
*/
</style>
```
