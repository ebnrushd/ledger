import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import customerRoutes from '@customer/router'; // Default export from refactored customer router
import adminRoutes from '@admin/router';     // Default export from refactored admin router

// Import auth stores for the global navigation guard
import { useAuthStore as useCustomerAuthStore } from '@customer/store/auth';
import { useAdminAuthStore } from '@admin/store/adminAuth';

// New AppShell for admin routes
import AppShellAdmin from '@/AppShellAdmin.vue'; // Assuming AppShellAdmin is in src/

const routes: Array<RouteRecordRaw> = [
  ...customerRoutes,
  {
    path: '/admin',
    component: AppShellAdmin, // Parent component for all /admin routes
    redirect: '/admin/dashboard', // Redirect /admin to /admin/dashboard
    children: [
      ...adminRoutes // Admin routes are now children, paths should be relative to /admin
    ]
  },
  // A global catch-all 404, preferably using a layout that fits a generic not-found page
  {
    path: '/:pathMatch(.*)*',
    name: 'GlobalNotFound',
    component: () => import('@customer/views/NotFoundView.vue'), // Default to customer's NotFound for now
    meta: { layout: 'CustomerAuthLayout' } // Or a new 'SimpleLayout' or 'ErrorLayout'
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL || '/'),
  routes,
});

router.beforeEach(async (to, from, next) => {
  // Ensure Pinia stores are accessible. They should be initialized by main.ts by this point.
  // Ensure Pinia stores are accessible. They should be initialized by main.ts by this point.
  const customerAuthStore = useCustomerAuthStore();
  const adminAuthStore = useAdminAuthStore();

  const requiresAuth = to.meta.requiresAuth;
  // Check meta field for admin routes, which is more reliable than path matching for nested routes
  const isAdminRoute = to.matched.some(record => record.meta.isAdminRoute === true);

  // Debugging logs
  // console.log(`Navigating to: ${to.path}, name: ${String(to.name)}`);
  // console.log(`Is admin route: ${isAdminRoute}`);
  // console.log(`Requires auth: ${requiresAuth}`);
  // console.log(`Customer Authenticated: ${customerAuthStore.isUserAuthenticated}`);
  // console.log(`Admin Authenticated: ${adminAuthStore.isUserAdminAuthenticated}`);


  if (isAdminRoute) {
    // Handle /admin/login route specifically
    if (to.name === 'AdminLogin') {
      if (adminAuthStore.isUserAdminAuthenticated) {
        // console.log('Admin already authenticated, redirecting from AdminLogin to AdminDashboard.');
        return next({ name: 'AdminDashboard' });
      } else {
        // console.log('Proceeding to AdminLogin.');
        return next(); // Allow access to login page if not authenticated
      }
    }

    // For all other admin routes that require auth
    if (requiresAuth) {
      if (!adminAuthStore.isUserAdminAuthenticated) {
        // console.log('Admin not authenticated, attempting to check session.');
        // await adminAuthStore.checkAuthStatus(); // Ensure session status is checked.
        // This checkAuthStatus is problematic here if it causes redirect loops or if it's slow.
        // The main.ts already attempts this. If still not authenticated, redirect.
        if (!adminAuthStore.isUserAdminAuthenticated) {
          // console.log('Admin still not authenticated after check, redirecting to AdminLogin.');
          return next({ name: 'AdminLogin', query: { redirect: to.fullPath } });
        }
      }
    }
  } else { // Customer routes
    if ((to.name === 'Login' || to.name === 'Register') && customerAuthStore.isUserAuthenticated) {
      // console.log('Customer authenticated, redirecting from Login/Register to Dashboard.');
      return next({ name: 'Dashboard' });
    }
    if (requiresAuth && !customerAuthStore.isUserAuthenticated) {
      // console.log('Customer not authenticated, redirecting to Login.');
      // Customer's tryAutoLogin is also called from main.ts.
      // If still not authenticated, redirect.
      return next({ name: 'Login', query: { redirect: to.fullPath } });
    }
  }

  // console.log('Proceeding with navigation.');
  next();
});

export default router;
```
