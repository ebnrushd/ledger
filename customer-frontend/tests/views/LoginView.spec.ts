import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, VueWrapper } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing'; // For mocking Pinia stores/actions
import LoginView from '@/views/LoginView.vue';
import router from '@/router'; // Import the actual router for navigation checks if needed
import { useAuthStore } from '@/store/auth'; // To interact with the mocked store

// Mock the router behavior if needed, or use the real router instance for integration-like component tests.
// For unit tests of components, often better to mock router push/replace.
const mockRouterPush = vi.fn();
const mockRouterReplace = vi.fn(); // if used
vi.mock('vue-router', async () => {
    const actualRouter = await vi.importActual('vue-router');
    return {
        ...(actualRouter as any), // Spread actual router exports
        useRouter: () => ({ // Mock specific functions used by component
            push: mockRouterPush,
            replace: mockRouterReplace,
            currentRoute: vi.fn(() => ({ // Mock currentRoute if component uses it (e.g. for redirect query)
                value: { query: {} }
            })),
        }),
        useRoute: () => ({ // Mock useRoute if component uses it
            query: {}, // Default empty query
        }),
    };
});


describe('LoginView.vue', () => {
  let wrapper: VueWrapper<any>;
  let authStore: ReturnType<typeof useAuthStore>;

  beforeEach(async () => {
    // Mount the component before each test
    wrapper = mount(LoginView, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn, // Creates spies for Pinia actions
            stubActions: false, // Set to true if you want to prevent actions from running their original code
                                // For this test, we want actions to run to check their effects,
                                // but the service calls within them will be mocked by their respective service tests.
                                // However, for a true component unit test, we might mock the action itself.
          }),
          router // Provide the actual router or a fully mocked one
        ],
        // stubs: { RouterLink: true } // Optional: stub child components like RouterLink
      },
    });
    authStore = useAuthStore(); // Get the store instance
    mockRouterPush.mockClear(); // Clear router mock calls
  });

  it('renders login form correctly', () => {
    expect(wrapper.find('h2').text()).toBe('Login to Your Account');
    expect(wrapper.find('label[for="username"]').exists()).toBe(true);
    expect(wrapper.find('input#username').exists()).toBe(true);
    expect(wrapper.find('label[for="password"]').exists()).toBe(true);
    expect(wrapper.find('input#password').exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').text()).toBe('Login');
  });

  it('allows typing in username and password fields', async () => {
    const usernameInput = wrapper.find('input#username');
    const passwordInput = wrapper.find('input#password');

    await usernameInput.setValue('test@example.com');
    await passwordInput.setValue('password123');

    expect((usernameInput.element as HTMLInputElement).value).toBe('test@example.com');
    expect((passwordInput.element as HTMLInputElement).value).toBe('password123');
  });

  it('calls authStore.login on form submission and redirects on success', async () => {
    // Mock the store's login action to resolve successfully
    authStore.login = vi.fn().mockResolvedValue(undefined); // Simulate successful login (no error thrown)
    // Alternatively, if not stubbing actions:
    // (authService.loginUser as vi.Mock).mockResolvedValue({ data: { access_token: 'token' } });
    // (jwtDecode as vi.Mock).mockReturnValue({ sub: 'test@example.com', user_id: 1, role: 'customer', exp: Date.now() + 3600000 });


    await wrapper.find('input#username').setValue('test@example.com');
    await wrapper.find('input#password').setValue('password123');
    await wrapper.find('form').trigger('submit.prevent');

    expect(authStore.login).toHaveBeenCalledTimes(1);
    expect(authStore.login).toHaveBeenCalledWith({ username: 'test@example.com', password: 'password123' });

    // Wait for promises to resolve in handleLogin (e.g., router.push)
    // If router.push is called, it should be awaited or handled.
    // Vitest might need a flushPromises or similar if not using await directly on router.push.
    // For now, assuming the mockResolvedValue for login action is enough.
    // The redirect check is tricky if the action itself does it.
    // If handleLogin directly calls router.push:
    await wrapper.vm.$nextTick(); // Wait for UI updates if any
    expect(mockRouterPush).toHaveBeenCalledWith('/dashboard'); // Default redirect
  });

  it('displays error message from store on failed login', async () => {
    const errorMessage = 'Invalid credentials from store';
    // Mock the store's login action to reject or set error
    authStore.login = vi.fn().mockImplementation(async () => {
      authStore.loginError = errorMessage; // Simulate error state in store
      throw new Error(errorMessage); // Simulate action throwing error
    });
    // Or, if testing component's direct error handling from a thrown error:
    // authStore.login = vi.fn().mockRejectedValue(new Error(errorMessage));


    await wrapper.find('input#username').setValue('wrong@example.com');
    await wrapper.find('input#password').setValue('wrongpass');
    await wrapper.find('form').trigger('submit.prevent');

    expect(authStore.login).toHaveBeenCalledTimes(1);

    await wrapper.vm.$nextTick(); // Allow DOM to update with error message

    const errorDiv = wrapper.find('.error-message');
    expect(errorDiv.exists()).toBe(true);
    expect(errorDiv.text()).toBe(errorMessage);
    expect(mockRouterPush).not.toHaveBeenCalled(); // Should not redirect
  });

  it('clears store error when input changes', async () => {
    authStore.loginError = "Previous error"; // Set an initial error
    await wrapper.vm.$nextTick();
    expect(wrapper.find('.error-message').exists()).toBe(true);

    await wrapper.find('input#username').setValue('new@example.com');
    await wrapper.vm.$nextTick();

    // The watch effect in LoginView should clear authStore.loginError
    expect(authStore.loginError).toBeNull();
    expect(wrapper.find('.error-message').exists()).toBe(false); // Error message should disappear
  });

});
```
