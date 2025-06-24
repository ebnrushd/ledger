import { RouteRecordRaw } from 'vue-router';

// View Components (lazy-loaded)
const AdminLoginView = () => import('@admin/views/AdminLoginView.vue');
const AdminDashboardView = () => import('@admin/views/AdminDashboardView.vue');
const UserListView = () => import('@admin/views/UserListView.vue');
const UserFormView = () => import('@admin/views/UserFormView.vue');
const UserDetailView = () => import('@admin/views/UserDetailView.vue');
const CustomerListView = () => import('@admin/views/CustomerListView.vue');
const CustomerDetailView = () => import('@admin/views/CustomerDetailView.vue');
const AccountListView = () => import('@admin/views/AccountListView.vue');
const AccountDetailView = () => import('@admin/views/AccountDetailView.vue');
const TransactionListView = () => import('@admin/views/TransactionListView.vue');
const TransactionDetailView = () => import('@admin/views/TransactionDetailView.vue');
const AuditLogListView = () => import('@admin/views/AuditLogListView.vue');
const AdminNotFoundView = () => import('@admin/views/NotFoundView.vue'); // Admin specific 404

const adminRoutes: Array<RouteRecordRaw> = [
  {
    path: 'login', // Relative to /admin
    name: 'AdminLogin',
    component: AdminLoginView,
    meta: { layout: 'AdminAuthLayout', title: 'Admin Login', requiresAuth: false, isAdminRoute: true },
  },
  {
    path: 'dashboard', // Relative to /admin
    name: 'AdminDashboard',
    component: AdminDashboardView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Dashboard', isAdminRoute: true },
  },
  {
    path: 'users',
    name: 'AdminUserList',
    component: UserListView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'User Management', isAdminRoute: true },
  },
  {
    path: 'users/new',
    name: 'AdminUserCreate',
    component: UserFormView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Create User', isAdminRoute: true },
  },
  {
    path: 'users/:userId/view',
    name: 'AdminUserDetail',
    component: UserDetailView,
    props: true,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'User Details', isAdminRoute: true },
  },
  {
    path: 'users/:userId/edit',
    name: 'AdminUserEdit',
    component: UserFormView,
    props: true,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Edit User', isAdminRoute: true },
  },
  {
    path: 'customers',
    name: 'AdminCustomerList',
    component: CustomerListView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Customer Management', isAdminRoute: true },
  },
  {
    path: 'customers/:customerId/view',
    name: 'AdminCustomerDetail',
    component: CustomerDetailView,
    props: true,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Customer Details', isAdminRoute: true },
  },
  {
    path: 'accounts',
    name: 'AdminAccountList',
    component: AccountListView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Account Management', isAdminRoute: true },
  },
  {
    path: 'accounts/:accountId/view',
    name: 'AdminAccountDetail',
    component: AccountDetailView,
    props: true,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Account Details', isAdminRoute: true },
  },
  {
    path: 'accounts/pending-approval',
    name: 'AdminPendingAccounts',
    component: () => import('@admin/views/PendingAccountsView.vue'),
    meta: { requiresAuth: true, layout: 'AdminLayout', title: 'Pending Accounts', isAdminRoute: true }
  },
  {
    path: 'transactions',
    name: 'AdminTransactionList',
    component: TransactionListView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Transaction Monitoring', isAdminRoute: true },
  },
  {
    path: 'transactions/:transactionId/view',
    name: 'AdminTransactionDetail',
    component: TransactionDetailView,
    props: true,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Transaction Details', isAdminRoute: true },
  },
  {
    path: 'audit-logs',
    name: 'AdminAuditLogList',
    component: AuditLogListView,
    meta: { layout: 'AdminLayout', requiresAuth: true, title: 'Audit Logs', isAdminRoute: true },
  },
  // Admin-specific catch-all, if needed, can be added here or handled by global.
  // For now, relying on global catch-all. If a specific /admin/not-found is desired:
  {
    path: ':adminPathMatch(.*)*', // Catch-all for /admin sub-paths
    name: 'AdminModuleNotFound',
    component: AdminNotFoundView, // Use the admin-specific NotFoundView
    meta: { layout: 'AdminLayout', title: 'Page Not Found', isAdminRoute: true },
  }
];

export default adminRoutes;
```
