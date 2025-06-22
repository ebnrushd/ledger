<template>
  <div class="admin-auth-layout flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-gray-700 via-gray-800 to-gray-900 p-4">
    <main class="auth-main w-full max-w-md bg-white p-8 rounded-xl shadow-2xl">
      <div class="text-center mb-6">
        <!-- You can add a logo here -->
        <h1 class="text-3xl font-bold text-admin-secondary">SQL Ledger Admin</h1>
      </div>
      <router-view />
    </main>
    <footer class="auth-footer mt-8 text-center text-sm text-gray-400">
      <p>&copy; {{ new Date().getFullYear() }} SQL Ledger System. All rights reserved.</p>
    </footer>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'AdminAuthLayout',
});
</script>

<style scoped>
/* AuthLayout specific styles can go here if needed */
.auth-main {
  /* Tailwind classes handle most styling */
}
</style>
```
