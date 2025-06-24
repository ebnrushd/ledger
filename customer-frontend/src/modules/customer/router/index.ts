import { RouteRecordRaw } from 'vue-router';

// View Components
import HomeView from '@customer/views/HomeView.vue';
import LoginView from '@customer/views/LoginView.vue';
import RegisterView from '@customer/views/RegisterView.vue';
import DashboardView from '@customer/views/DashboardView.vue';

const customerRoutes: Array<RouteRecordRaw> = [
  {
    path: '/', // This will be the app's root path
    name: 'Home',
    component: HomeView,
    meta: { layout: 'CustomerDefaultLayout' },
  },
  {
    path: '/login',
    name: 'Login', // Will be CustomerLogin to distinguish from AdminLogin
    component: LoginView,
    meta: { layout: 'CustomerAuthLayout' },
  },
  {
    path: '/register',
    name: 'Register', // Will be CustomerRegister
    component: RegisterView,
    meta: { layout: 'CustomerAuthLayout' },
  },
  {
    path: '/dashboard',
    name: 'Dashboard', // Will be CustomerDashboard
    component: DashboardView,
    meta: { layout: 'CustomerDefaultLayout', requiresAuth: true },
  },
  {
    path: '/accounts/:accountId',
    name: 'AccountDetails', // Will be CustomerAccountDetails
    component: () => import('@customer/views/AccountDetailsView.vue'),
    meta: { layout: 'CustomerDefaultLayout', requiresAuth: true },
    props: true
  },
  {
    path: '/transfer',
    name: 'TransferFunds', // Will be CustomerTransferFunds
    component: () => import('@customer/views/TransferFundsView.vue'),
    meta: { layout: 'CustomerDefaultLayout', requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'UserProfile', // Will be CustomerUserProfile
    component: () => import('@customer/views/ProfileView.vue'),
    meta: { requiresAuth: true, layout: 'CustomerDefaultLayout' }
  }
  // Note: The catch-all 404 route will be handled by the main router.
  // Any specific customer 404 logic could be a specific route if needed.
];

export default customerRoutes; // Exporting the routes array
```
