import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router'; // New main router
import './assets/css/tailwind.css'; // Main global CSS (Tailwind)

const app = createApp(App);
const pinia = createPinia(); // Single Pinia instance

app.use(pinia);
app.use(router);

// App-wide initialization for auth stores.
// This helps ensure stores are ready before initial navigation guards run.
// Note: Actual auto-login logic is within each store's tryAutoLogin/checkAuthStatus methods.
// We are just ensuring these stores are instantiated and their initial checks are kicked off.
import { useAuthStore as useCustomerAuthStore } from '@customer/store/auth';
import { useAdminAuthStore } from '@admin/store/adminAuth';

const customerAuthStore = useCustomerAuthStore(pinia);
const adminAuthStore = useAdminAuthStore(pinia);

// Initialize stores and attempt auto-login/status check.
// The router.isReady() ensures that async operations within router guards
// (like the ones we'll add for auth) complete before mounting the app.
Promise.allSettled([
  customerAuthStore.tryAutoLogin(), // For customer frontend
  adminAuthStore.checkAuthStatus()  // For admin frontend session check
]).then(() => {
  router.isReady().then(() => {
    app.mount('#app');
  });
}).catch(error => {
  console.error("Error during initial auth store checks:", error);
  // Still mount the app even if auth checks fail, guards will handle redirection.
  router.isReady().then(() => {
    app.mount('#app');
  });
});
```
