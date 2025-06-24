<template>
  <component :is="currentLayout" />
</template>

<script lang="ts">
import { defineComponent, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';

// Import all possible layouts
import CustomerDefaultLayout from '@customer/layouts/DefaultLayout.vue';
import CustomerAuthLayout from '@customer/layouts/AuthLayout.vue';
import AdminLayout from '@admin/layouts/AdminLayout.vue';
import AdminAuthLayout from '@admin/layouts/AdminAuthLayout.vue';
import SimpleLayout from '@/layouts/SimpleLayout.vue'; // New basic layout

// Import auth stores for initialization
import { useAuthStore as useCustomerAuthStore } from '@customer/store/auth';
import { useAdminAuthStore } from '@admin/store/adminAuth';

export default defineComponent({
  name: 'App',
  setup() {
    const route = useRoute();

    const layouts: Record<string, any> = {
      CustomerDefaultLayout,
      CustomerAuthLayout,
      AdminLayout,
      AdminAuthLayout,
      SimpleLayout,
    };

    const currentLayout = computed(() => {
      const layoutName = route.meta.layout as string | undefined;
      return layouts[layoutName || 'SimpleLayout'] || SimpleLayout; // Fallback to SimpleLayout
    });

    onMounted(async () => {
      const customerAuthStore = useCustomerAuthStore();
      const adminAuthStore = useAdminAuthStore();

      // These checks are also in main.ts but running them here ensures they are re-checked
      // if the app is rehydrated or if main.ts execution timing is nuanced.
      // The stores themselves should prevent redundant API calls if already checked.
      if (!customerAuthStore.isUserAuthenticated) { // Corrected getter name
        await customerAuthStore.tryAutoLogin();
      }
      if (!adminAuthStore.isUserAdminAuthenticated) { // Corrected getter name
        await adminAuthStore.checkAuthStatus();
      }
    });

    return {
      currentLayout,
    };
  },
});
</script>

<style>
/* Global styles can remain if truly global, or be moved to ./assets/css/tailwind.css */
/* Ensure html, body, and #app take full height for layouts that need it. */
html, body, #app {
  height: 100%;
  margin: 0;
  /* background-color: #f0f2f5; /* Example global background */
}
</style>
```
