import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';

// Layouts
// It's common to import layouts here if routes define them,
// or App.vue can handle layout switching based on route meta.
// For this setup, we'll assume App.vue handles layout switching using route meta fields.
// import DefaultLayout from '@/layouts/DefaultLayout.vue';
// import AuthLayout from '@customer/layouts/AuthLayout.vue';

// View Components
import HomeView from '@customer/views/HomeView.vue';
import LoginView from '@customer/views/LoginView.vue';
import RegisterView from '@customer/views/RegisterView.vue';
import DashboardView from '@customer/views/DashboardView.vue';
// Placeholder for a protected route example
// import ProfileView from '@customer/views/ProfileView.vue';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: HomeView,
    meta: { layout: 'DefaultLayout' }, // Custom meta field for layout
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { layout: 'AuthLayout' },
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: { layout: 'AuthLayout' },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: { layout: 'DefaultLayout', requiresAuth: true }, // Example: requiresAuth for protected routes
  },
  // Example of another protected route:
  // {
  //   path: '/profile',
  //   name: 'Profile',
  //   component: ProfileView,
  //   meta: { layout: 'DefaultLayout', requiresAuth: true },
  // },
  {
    path: '/:pathMatch(.*)*', // Catch-all route for 404
    name: 'NotFound',
    component: () => import('@customer/views/NotFoundView.vue'), // Lazy load 404 page
    meta: { layout: 'DefaultLayout' },
  },
  {
    path: '/accounts/:accountId', // Using accountId to match common param naming
    name: 'AccountDetails',
    component: () => import('@customer/views/AccountDetailsView.vue'), // To be created
    meta: { layout: 'DefaultLayout', requiresAuth: true },
    props: true // Pass route params (like accountId) as props to the component
  },
  {
    path: '/transfer',
    name: 'TransferFunds',
    component: () => import('@customer/views/TransferFundsView.vue'),
    meta: { layout: 'DefaultLayout', requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'UserProfile',
    component: () => import('@customer/views/ProfileView.vue'),
    meta: { requiresAuth: true, layout: 'DefaultLayout' }
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL || '/'), // BASE_URL for subfolder deployment
  routes,
});

// Optional: Navigation Guards (for authentication)
// This guard should be placed AFTER router initialization and BEFORE exporting the router.
// It also needs access to the auth store.
import { useAuthStore } from '@customer/store/auth'; // Import store
// Pinia instance needs to be passed to the store hook if used outside setup() context,
// OR ensure Pinia is initialized before router setup if store is instantiated here.
// For simplicity, assume Pinia is initialized (in main.ts) and store can be used.

router.beforeEach((to, from, next) => {
  // It's better to initialize the store usage inside the guard,
  // as Pinia might not be fully available when this module is first imported.
  const authStore = useAuthStore(); // Get store instance

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const isAuthenticated = authStore.isUserAuthenticated; // Use getter

  if (requiresAuth && !isAuthenticated) {
    console.log(`Navigation blocked to "${String(to.name)}" (requires auth), redirecting to Login.`);
    next({ name: 'Login', query: { redirect: to.fullPath } });
  } else if ((to.name === 'Login' || to.name === 'Register') && isAuthenticated) {
    console.log(`User is authenticated, redirecting from "${String(to.name)}" to Dashboard.`);
    next({ name: 'Dashboard' });
  } else {
    next();
  }
});

export default router;
```
