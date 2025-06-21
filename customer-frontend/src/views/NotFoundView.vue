<template>
  <div class="not-found-container flex flex-col items-center justify-center text-center py-10 md:py-20 bg-gray-50 flex-grow">
    <div class="container mx-auto px-4">
      <h1 class="text-6xl font-bold text-primary mb-4">404</h1>
      <h2 class="text-3xl font-semibold text-gray-700 mb-6">Page Not Found</h2>
      <p class="text-lg text-gray-600 mb-8 max-w-md mx-auto">
        Sorry, the page you are looking for could not be found. It might have been removed, had its name changed, or is temporarily unavailable.
      </p>
      <router-link
        to="/"
        class="inline-block px-6 py-3 bg-primary text-white text-lg font-medium rounded-md shadow-md hover:bg-green-600 transition duration-300"
      >
        Go to Homepage
      </router-link>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'NotFoundView',
});
</script>

<style scoped>
/* Specific styles for NotFoundView if needed */
</style>
```
