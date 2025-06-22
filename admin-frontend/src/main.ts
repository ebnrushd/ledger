import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './store' // Assuming src/store/index.ts exports the Pinia instance
import './assets/css/admin-tailwind.css' // Main Tailwind CSS import

// Optional: Global error handler for Vue (mainly for unhandled issues within Vue lifecycle)
// app.config.errorHandler = (err, instance, info) => {
//   console.error("Vue Error:", err);
//   console.log("Vue Instance:", instance);
//   console.log("Vue Info:", info);
//   // Potentially send to an error tracking service
// };

const app = createApp(App)

app.use(pinia)
app.use(router)

// Router isReady promise ensures async components in router (like lazy-loaded views)
// and async guards are resolved before mounting the app.
// We need to check auth status *before* router is fully ready or first navigation happens,
// so guards have correct initial state.

async function initializeApp() {
  const adminAuthStore = useAdminAuthStore(); // Initialize store instance
  try {
    await adminAuthStore.checkAuthStatus(); // Verify session with backend
  } catch (error) {
    console.error("Initial auth check failed:", error);
    // App will proceed, router guards will redirect to login if needed
  }

  // Ensure router is ready before mounting, especially if guards depend on async operations
  // or if there are async components in the initial route.
  router.isReady().then(() => {
    app.mount('#app');
  });
}

initializeApp();
```
