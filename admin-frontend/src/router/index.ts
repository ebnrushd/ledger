import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';

// View Components (lazy-loaded)
const AdminLoginView = () => import('@/views/AdminLoginView.vue');
const AdminDashboardView = () => import('@/views/AdminDashboardView.vue');

const UserListView = () => import('@/views/UserListView.vue');
const UserFormView = () => import('@/views/UserFormView.vue');
const UserDetailView = () => import('@/views/UserDetailView.vue');

const CustomerListView = () => import('@/views/CustomerListView.vue');
const CustomerDetailView = () => import('@/views/CustomerDetailView.vue');

const AccountListView = () => import('@/views/AccountListView.vue');
const AccountDetailView = () => import('@/views/AccountDetailView.vue');

const TransactionListView = () => import('@/views/TransactionListView.vue');
const TransactionDetailView = () => import('@/views/TransactionDetailView.vue');

const AuditLogListView = () => import('@/views/AuditLogListView.vue');

const NotFoundView = () => import('@/views/NotFoundView.vue');

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'AdminLogin',
    component: AdminLoginView,
    meta: { layout: 'AdminAuthLayout', title: 'Admin Login', requiresAuth: false },
  },
  {
    path: '/',
    redirect: '/dashboard',
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard',
    name: 'AdminDashboard',
    component: AdminDashboardView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Dashboard' },
  },
  // User Management
  {
    path: '/users',
    name: 'AdminUserList',
    component: UserListView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'User Management' },
  },
  {
    path: '/users/new',
    name: 'AdminUserCreate',
    component: UserFormView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Create User' },
  },
  {
    path: '/users/:userId/view',
    name: 'AdminUserDetail',
    component: UserDetailView,
    props: true,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'User Details' },
  },
  {
    path: '/users/:userId/edit',
    name: 'AdminUserEdit',
    component: UserFormView,
    props: true,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Edit User' },
  },
  // Customer Management
  {
    path: '/customers',
    name: 'AdminCustomerList',
    component: CustomerListView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Customer Management'},
  },
  {
    path: '/customers/:customerId/view',
    name: 'AdminCustomerDetail',
    component: CustomerDetailView,
    props: true,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Customer Details' },
  },
  // Account Management
  {
    path: '/accounts',
    name: 'AdminAccountList',
    component: AccountListView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Account Management' },
  },
  {
    path: '/accounts/:accountId/view',
    name: 'AdminAccountDetail',
    component: AccountDetailView,
    props: true,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Account Details' },
  },
  // Transaction Monitoring
  {
    path: '/transactions',
    name: 'AdminTransactionList',
    component: TransactionListView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Transaction Monitoring' },
  },
  {
    path: '/transactions/:transactionId/view',
    name: 'AdminTransactionDetail',
    component: TransactionDetailView,
    props: true,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Transaction Details' },
  },
  // Audit Logs
  {
    path: '/audit-logs',
    name: 'AdminAuditLogList',
    component: AuditLogListView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Audit Logs' },
  },

  // Catch-all 404
  {
    path: '/:pathMatch(.*)*',
    name: 'AdminNotFound',
    component: NotFoundView,
    meta: { layout: 'AdminLayout', title: 'Page Not Found' }, // Or a SimpleLayout
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL || '/admin/'), // Base for admin panel
  routes,
});

import { useAdminAuthStore } from '@/store/adminAuth';

router.beforeEach((to, from, next) => {
  const adminAuthStore = useAdminAuthStore();
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const isAuthenticated = adminAuthStore.isUserAdminAuthenticated;

  if (requiresAuth && !isAuthenticated) {
    if (to.name !== 'AdminLogin') {
        console.log(`Admin Router Guard: Not authenticated for "${String(to.name)}", redirecting to Login.`);
        next({ name: 'AdminLogin', query: { redirect: to.fullPath } });
    } else {
        next();
    }
  } else if (to.name === 'AdminLogin' && isAuthenticated) {
    console.log(`Admin Router Guard: Authenticated, redirecting from Login to Dashboard.`);
    next({ name: 'AdminDashboard' });
  } else {
    next();
  }
});

export default router;
```
