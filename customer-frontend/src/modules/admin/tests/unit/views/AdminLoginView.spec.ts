import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia, Pinia } from 'pinia';
import AdminLoginView from '@admin/views/AdminLoginView.vue';
import { useAdminAuthStore } from '@admin/store/adminAuth';
import { nextTick } from 'vue';

// Mock Vue Router
const mockRouterPush = vi.fn();
const mockRoute = { query: {} }; // Default mock route

vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router');
  return {
    ...actual,
    useRouter: () => ({ push: mockRouterPush }),
    useRoute: () => mockRoute, // Provide a default mock, can be overridden in tests
  };
});


describe('AdminLoginView.vue', () => {
  let pinia: Pinia;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    // Reset mocks
    mockRouterPush.mockClear();
    // Reset store state by re-creating it or calling a reset action if available
    const authStore = useAdminAuthStore();
    authStore.$reset = () => { // Simple reset for testing
        authStore.adminUser = null;
        authStore.isAdminAuthenticated = false;
        authStore.authError = null;
        authStore.isLoading = false;
    };
    authStore.$reset();
    mockRoute.query = {}; // Reset route query
  });

  it('renders login form', () => {
    const wrapper = mount(AdminLoginView, {
      global: {
        plugins: [pinia],
      }
    });
    expect(wrapper.find('input#username').exists()).toBe(true);
    expect(wrapper.find('input#password').exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it('calls store login action on form submit', async () => {
    const authStore = useAdminAuthStore();
    authStore.login = vi.fn().mockResolvedValue(true); // Mock successful login

    const wrapper = mount(AdminLoginView, {
      global: {
        plugins: [pinia],
      }
    });

    await wrapper.find('input#username').setValue('admin@example.com');
    await wrapper.find('input#password').setValue('password');
    await wrapper.find('form').trigger('submit.prevent');

    expect(authStore.login).toHaveBeenCalledWith({ username: 'admin@example.com', password: 'password' });
  });

  it('redirects to dashboard on successful login', async () => {
    const authStore = useAdminAuthStore();
    authStore.login = vi.fn().mockResolvedValue(true); // Mock store action for successful login

    const wrapper = mount(AdminLoginView, {
      global: {
        plugins: [pinia],
      }
    });

    await wrapper.find('input#username').setValue('admin@example.com');
    await wrapper.find('input#password').setValue('password');
    await wrapper.find('form').trigger('submit.prevent');
    await nextTick(); // Wait for async operations in handleLogin

    expect(mockRouterPush).toHaveBeenCalledWith('/dashboard');
  });

  it('redirects to query param on successful login if redirect query exists', async () => {
    const authStore = useAdminAuthStore();
    authStore.login = vi.fn().mockResolvedValue(true);
    mockRoute.query = { redirect: '/admin/users' }; // Simulate redirect query param

    const wrapper = mount(AdminLoginView, {
      global: {
        plugins: [pinia],
      }
    });

    await wrapper.find('input#username').setValue('admin@example.com');
    await wrapper.find('input#password').setValue('password');
    await wrapper.find('form').trigger('submit.prevent');
    await nextTick();

    expect(mockRouterPush).toHaveBeenCalledWith('/admin/users');
  });


  it('displays error message from store on failed login', async () => {
    const authStore = useAdminAuthStore();
    authStore.login = vi.fn().mockRejectedValue(new Error("Login failed")); // Simulate failed login in action
    authStore.authError = 'Invalid credentials'; // Store sets this error

    const wrapper = mount(AdminLoginView, {
      global: {
        plugins: [pinia],
      }
    });

    await wrapper.find('input#username').setValue('admin@example.com');
    await wrapper.find('input#password').setValue('wrong');
    await wrapper.find('form').trigger('submit.prevent');
    await nextTick(); // for error message to appear

    expect(authStore.login).toHaveBeenCalled();
    expect(wrapper.text()).toContain('Invalid credentials');
    expect(mockRouterPush).not.toHaveBeenCalled();
  });

  it('disables button while loading', async () => {
    const authStore = useAdminAuthStore();
    authStore.isLoading = true; // Simulate loading state

    const wrapper = mount(AdminLoginView, {
      global: {
        plugins: [pinia],
      }
    });
    expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined();
    expect(wrapper.find('button[type="submit"]').text()).toContain('Logging in...');

    authStore.isLoading = false; // Reset for other tests
  });
});
```
