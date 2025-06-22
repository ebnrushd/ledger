<template>
  <div class="not-found-admin flex flex-col items-center justify-center text-center py-10 md:py-20 bg-admin-light-gray flex-grow">
    <div class="container mx-auto px-4">
      <h1 class="text-6xl font-bold text-admin-primary mb-4">404</h1>
      <h2 class="text-3xl font-semibold text-gray-700 mb-6">Page Not Found</h2>
      <p class="text-lg text-gray-600 mb-8 max-w-md mx-auto">
        Sorry, the admin page you are looking for could not be found.
      </p>
      <router-link
        :to="{ name: 'AdminDashboard' }"
        class="inline-block px-6 py-3 bg-admin-primary text-white text-lg font-medium rounded-md shadow-md hover:bg-blue-700 transition duration-300"
      >
        Go to Admin Dashboard
      </router-link>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'AdminNotFoundView', // Renamed to avoid conflict with customer frontend's NotFoundView if ever merged/imported
});
</script>

<style scoped>
/* Specific styles for AdminNotFoundView if needed */
</style>
```
