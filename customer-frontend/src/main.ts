import { createApp } from 'vue'
import App from './App.vue'
import router from './modules/customer/router' // Updated path
import pinia from './modules/customer/store'  // Updated path
// import './assets/main.css'  // Remove old global styles
import './modules/customer/assets/css/tailwind.css' // Updated path

const app = createApp(App)

app.use(pinia)  // Use Pinia
app.use(router) // Use router

// Attempt to auto-login user if token exists from previous session
// This should be done after Pinia is initialized but before app is mounted,
// or as part of the auth store's own setup.
// If called here, useAuthStore must be callable.
import { useAuthStore } from './store/auth'; // Import store
const authStore = useAuthStore(); // Initialize store instance
authStore.tryAutoLogin(); // Attempt to restore session

app.mount('#app')
```
