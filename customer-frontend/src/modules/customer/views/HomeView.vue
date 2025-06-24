<template>
  <div class="home-view text-center py-10 md:py-20 bg-gray-50 flex-grow flex flex-col justify-center items-center">
    <div class="container mx-auto px-4">
      <h1 class="text-4xl md:text-5xl font-bold text-primary mb-6">
        Welcome to the SQL Ledger Customer Portal
      </h1>
      <p class="text-lg md:text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
        Manage your accounts, view transaction history, transfer funds, and update your profile with ease and security.
      </p>
      <div class="space-x-0 space-y-4 sm:space-x-4 sm:space-y-0">
        <router-link
          to="/login"
          class="inline-block px-8 py-3 bg-primary text-white text-lg font-medium rounded-md shadow-md hover:bg-green-600 transition duration-300"
        >
          Login
        </router-link>
        <router-link
          to="/register"
          class="inline-block px-8 py-3 bg-secondary text-white text-lg font-medium rounded-md shadow-md hover:bg-gray-700 transition duration-300"
        >
          Register
        </router-link>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'HomeView',
});
</script>

<style scoped>
/* Any additional specific styles for HomeView can go here if Tailwind utilities are not sufficient */
.home-view {
  /* Example: if you wanted a specific background pattern or image */
}
</style>
```
