<template>
  <component :is="currentLayout">
    <router-view />
  </component>
</template>

<script lang="ts">
import { defineComponent, computed, shallowRef, watch } from 'vue';
import { useRoute } from 'vue-router';

// Import layout components
import DefaultLayout from './layouts/DefaultLayout.vue';
import AuthLayout from './layouts/AuthLayout.vue';
// Import other layouts if you have them, e.g., AdminLayout

export default defineComponent({
  name: 'App',
  components: {
    DefaultLayout,
    AuthLayout,
    // Register other layouts here
  },
  setup() {
    const route = useRoute();

    // shallowRef is used for performance if layouts are complex,
    // as it only makes the .value reactive, not the object itself.
    const currentLayout = shallowRef(DefaultLayout); // Default to DefaultLayout

    // Watch for route changes to update the layout
    watch(
      () => route.meta,
      async (meta) => {
        try {
          if (meta.layout && typeof meta.layout === 'string') {
            // Dynamically import the layout component
            // Note: For this to work well with Vite's build, often explicit imports are better,
            // or ensure Vite knows about these dynamic paths.
            // For simplicity here, we'll use a map or direct component check.
            if (meta.layout === 'AuthLayout') {
              currentLayout.value = AuthLayout;
            } else if (meta.layout === 'DefaultLayout') {
              currentLayout.value = DefaultLayout;
            } else {
              // Fallback to DefaultLayout if specified layout is unknown
              console.warn(`Unknown layout: ${meta.layout}, defaulting to DefaultLayout.`);
              currentLayout.value = DefaultLayout;
            }
          } else {
            // No layout specified in meta, use default
            currentLayout.value = DefaultLayout;
          }
        } catch (e) {
          console.error('Failed to load layout:', meta.layout, e);
          currentLayout.value = DefaultLayout; // Fallback on error
        }
      },
      { immediate: true } // immediate: true to run the watcher on initial load
    );

    return {
      currentLayout,
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
