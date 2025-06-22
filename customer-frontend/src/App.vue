<template>
  <component :is="currentLayout">
    <router-view />
  </component>
</template>

<script lang="ts">
import { defineComponent, computed, shallowRef, watch } from 'vue';
import { useRoute } from 'vue-router';

// Import layout components using new paths
// These will be refactored later when main router combines admin/customer layouts
const CustomerDefaultLayout = defineAsyncComponent(() => import('./modules/customer/layouts/DefaultLayout.vue'));
const CustomerAuthLayout = defineAsyncComponent(() => import('./modules/customer/layouts/AuthLayout.vue'));
// Placeholder for a potential shared "SimpleLayout" or future Admin layouts
// const SimpleLayout = defineAsyncComponent(() => import('./shared/layouts/SimpleLayout.vue'));

export default defineComponent({
  name: 'App',
  // No need to register components here if using defineAsyncComponent in setup directly for currentLayoutComponent
  setup() {
    const route = useRoute();

    const layouts: Record<string, any> = {
      DefaultLayout: CustomerDefaultLayout, // Map generic name to specific customer layout
      AuthLayout: CustomerAuthLayout,
      // SimpleLayout: SimpleLayout,
    };

    const currentLayoutComponent = computed(() => {
      const layoutName = route.meta.layout as string;
      // Fallback to CustomerDefaultLayout if no layout specified or name is unknown
      return layouts[layoutName] || CustomerDefaultLayout;
    });

    // Watch for route changes is implicitly handled by computed property reacting to route.meta
    // No explicit watch needed here anymore if currentLayoutComponent is a computed property.

    return {
      currentLayoutComponent,
    };
  },
});
</script>

<style>
/* App.vue specific styles or global styles not in main.css */
/* For example, ensuring the app takes full height if layouts need it */
html, body {
  height: 100%;
  margin: 0;
}
#app {
  /* display: flex; flex-direction: column; min-height: 100vh; */ /* Already in main.css */
}
</style>
```
