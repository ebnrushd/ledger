<template>
  <component :is="currentLayoutComponent">
    <router-view />
  </component>
</template>

<script lang="ts">
import { defineComponent, computed, shallowRef, watch, defineAsyncComponent } from 'vue';
import { useRoute } from 'vue-router';

// Layouts - Using defineAsyncComponent for potential code splitting of layouts
const AdminLayout = defineAsyncComponent(() => import('./layouts/AdminLayout.vue'));
const AdminAuthLayout = defineAsyncComponent(() => import('./layouts/AdminAuthLayout.vue'));
// A simple layout for general errors or pages without full admin chrome
const SimpleLayout = defineAsyncComponent(() => import('./layouts/SimpleLayout.vue')); // Needs to be created

export default defineComponent({
  name: 'App',
  setup() {
    const route = useRoute();

    const layouts: Record<string, any> = {
      AdminLayout,
      AdminAuthLayout,
      SimpleLayout, // For pages like a generic 404 if not using AdminLayout
    };

    // Default to AdminLayout if route doesn't specify or specifies an unknown one
    const currentLayoutComponent = computed(() => {
      const layoutName = route.meta.layout as string;
      return layouts[layoutName] || AdminLayout; // Fallback to AdminLayout
    });

    return {
      currentLayoutComponent,
    };
  },
});
</script>

<style>
/* Global styles imported via admin-tailwind.css in main.ts */
/* App-specific global styles can go here if necessary */
#app {
  display: flex; /* Needed if layouts are flex containers */
  flex-direction: column;
  min-height: 100vh;
}
</style>
```
