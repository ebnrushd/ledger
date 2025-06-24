import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia, Pinia } from 'pinia';
import { createRouter, createWebHistory, Router, RouteRecordRaw, START_LOCATION } from 'vue-router';
import App from '@/App.vue'; // Testing the main App.vue

// Mock Layouts
const CustomerDefaultLayout = { template: '<div>CustomerDefaultLayout<router-view/></div>', name: 'CustomerDefaultLayout' };
const CustomerAuthLayout = { template: '<div>CustomerAuthLayout<router-view/></div>', name: 'CustomerAuthLayout' };
const AdminLayout = { template: '<div>AdminLayout<router-view/></div>', name: 'AdminLayout' };
const AdminAuthLayout = { template: '<div>AdminAuthLayout<router-view/></div>', name: 'AdminAuthLayout' };
const SimpleLayout = { template: '<div>SimpleLayout<router-view/></div>', name: 'SimpleLayout' };

// Mock Stores
const mockUseCustomerAuthStore = vi.fn(() => ({
  isUserAuthenticated: false,
  tryAutoLogin: vi.fn().mockResolvedValue(undefined),
}));
const mockUseAdminAuthStore = vi.fn(() => ({
  isUserAdminAuthenticated: false,
  checkAuthStatus: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('@customer/layouts/DefaultLayout.vue', () => ({ default: CustomerDefaultLayout }));
vi.mock('@customer/layouts/AuthLayout.vue', () => ({ default: CustomerAuthLayout }));
vi.mock('@admin/layouts/AdminLayout.vue', () => ({ default: AdminLayout }));
vi.mock('@admin/layouts/AdminAuthLayout.vue', () => ({ default: AdminAuthLayout }));
vi.mock('@/layouts/SimpleLayout.vue', () => ({ default: SimpleLayout }));

vi.mock('@customer/store/auth', () => ({ useAuthStore: mockUseCustomerAuthStore }));
vi.mock('@admin/store/adminAuth', () => ({ useAdminAuthStore: mockUseAdminAuthStore }));


describe('App.vue', () => {
  let pinia: Pinia;
  let router: Router;

  const createTestRouter = (routes: RouteRecordRaw[] = []) => {
    return createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', name: 'Home', component: { template: '<div>Home</div>' }, meta: { layout: 'CustomerDefaultLayout' } },
        { path: '/login', name: 'Login', component: { template: '<div>Login</div>' }, meta: { layout: 'CustomerAuthLayout' } },
        { path: '/admin/login', name: 'AdminLogin', component: { template: '<div>Admin Login</div>' }, meta: { layout: 'AdminAuthLayout' } },
        { path: '/admin/dashboard', name: 'AdminDashboard', component: { template: '<div>Admin Dashboard</div>' }, meta: { layout: 'AdminLayout' } },
        { path: '/simple', name: 'Simple', component: { template: '<div>Simple Page</div>' }, meta: { layout: 'SimpleLayout' } },
        { path: '/no-layout', name: 'NoLayout', component: { template: '<div>No Layout Page</div>' } }, // Test fallback
        ...routes,
      ],
    });
  };

  beforeEach(async () => {
    pinia = createPinia();
    setActivePinia(pinia);

    // Reset mocks for store method calls
    mockUseCustomerAuthStore().tryAutoLogin.mockClear();
    mockUseAdminAuthStore().checkAuthStatus.mockClear();
  });

  it('renders SimpleLayout by default if no meta.layout is specified', async () => {
    router = createTestRouter();
    await router.push('/no-layout');
    await router.isReady(); // Wait for router to be ready and navigation to complete

    const wrapper = mount(App, {
      global: {
        plugins: [pinia, router],
      },
    });
    await nextTick(); // Allow Vue to render updates
    expect(wrapper.findComponent(SimpleLayout).exists()).toBe(true);
  });

  it('renders CustomerDefaultLayout for Home route', async () => {
    router = createTestRouter();
    await router.push('/');
    await router.isReady();
    const wrapper = mount(App, { global: { plugins: [pinia, router] } });
    await nextTick();
    expect(wrapper.findComponent(CustomerDefaultLayout).exists()).toBe(true);
  });

  it('renders CustomerAuthLayout for Login route', async () => {
    router = createTestRouter();
    await router.push('/login');
    await router.isReady();
    const wrapper = mount(App, { global: { plugins: [pinia, router] } });
    await nextTick();
    expect(wrapper.findComponent(CustomerAuthLayout).exists()).toBe(true);
  });

  it('renders AdminLayout for AdminDashboard route', async () => {
    router = createTestRouter();
    await router.push('/admin/dashboard');
    await router.isReady();
    const wrapper = mount(App, { global: { plugins: [pinia, router] } });
    await nextTick();
    expect(wrapper.findComponent(AdminLayout).exists()).toBe(true);
  });

  it('renders AdminAuthLayout for AdminLogin route', async () => {
    router = createTestRouter();
    await router.push('/admin/login');
    await router.isReady();
    const wrapper = mount(App, { global: { plugins: [pinia, router] } });
    await nextTick();
    expect(wrapper.findComponent(AdminAuthLayout).exists()).toBe(true);
  });

  it('calls tryAutoLogin and checkAuthStatus on mount if stores are not authenticated', async () => {
    mockUseCustomerAuthStore().isUserAuthenticated = false; // Ensure initial state is not authenticated
    mockUseAdminAuthStore().isUserAdminAuthenticated = false;

    router = createTestRouter();
    await router.push('/'); // Initial navigation
    await router.isReady();

    const wrapper = mount(App, { global: { plugins: [pinia, router] } });
    // onMounted hooks are called after the component is mounted
    await nextTick(); // Allow onMounted to execute

    expect(mockUseCustomerAuthStore().tryAutoLogin).toHaveBeenCalledTimes(1);
    expect(mockUseAdminAuthStore().checkAuthStatus).toHaveBeenCalledTimes(1);
  });

  it('does NOT call tryAutoLogin or checkAuthStatus on mount if stores ARE authenticated', async () => {
    // Set store mocks to return authenticated state
     mockUseCustomerAuthStore.mockImplementationOnce(() => ({ // Use mockImplementationOnce for specific test case
        isUserAuthenticated: true,
        tryAutoLogin: vi.fn().mockResolvedValue(undefined),
     }));
     mockUseAdminAuthStore.mockImplementationOnce(() => ({
        isUserAdminAuthenticated: true,
        checkAuthStatus: vi.fn().mockResolvedValue(undefined),
     }));

    // Re-initialize stores with new mocked implementations for this test
    const customerAuth = useCustomerAuthStore(); // These will use the mockImplementationOnce
    const adminAuth = useAdminAuthStore();


    router = createTestRouter();
    await router.push('/');
    await router.isReady();

    const wrapper = mount(App, { global: { plugins: [pinia, router] } });
    await nextTick();

    expect(customerAuth.tryAutoLogin).not.toHaveBeenCalled();
    expect(adminAuth.checkAuthStatus).not.toHaveBeenCalled();

    // Restore default mocks for other tests
    mockUseCustomerAuthStore.mockImplementation(() => ({
        isUserAuthenticated: false, tryAutoLogin: vi.fn().mockResolvedValue(undefined),
    }));
    mockUseAdminAuthStore.mockImplementation(() => ({
        isUserAdminAuthenticated: false, checkAuthStatus: vi.fn().mockResolvedValue(undefined),
    }));
  });
});

```
