import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createRouter, createWebHistory, START_LOCATION } from 'vue-router';
import { setActivePinia, createPinia } from 'pinia';
import { useAuthStore } from '@/store/auth'; // Actual store for testing its state

// The router instance with guards is in '@/router/index.ts'
// To test the guard, we need to import the router instance itself,
// or re-define the guard here with mocked dependencies.
// For a true unit test of the guard logic, re-defining it or exporting it separately might be cleaner.
// For an integration test of the router, we use the actual router.

// Let's try to test the actual router instance's beforeEach guard.
// This is more of an integration test for the guard.
import router from '@/router'; // Import the configured router

describe('Router Navigation Guards', () => {
  beforeEach(() => {
    setActivePinia(createPinia()); // New Pinia for each test
    // Reset router to initial state if possible (tricky with global router instance)
    // Or, create a new router instance for each test with the guards applied.
    // For now, we'll use the global router and manage store state.
    // Clear any mocks on router if we were mocking router.push etc.
    vi.clearAllMocks();
  });

  // It's difficult to directly "call" router.beforeEach hooks in isolation with Vitest easily
  // without navigating. So, tests will often involve `router.push` and asserting the outcome.

  it('redirects to /login if route requires auth and user is not authenticated', async () => {
    const authStore = useAuthStore();
    authStore.isAuthenticated = false; // Ensure not authenticated

    try {
      // Attempt to navigate to a protected route (e.g., /dashboard)
      // The router in index.ts has /dashboard marked with requiresAuth: true
      await router.push('/dashboard');
    } catch (error) {
      // vue-router push might throw NavigationFailure if redirected from within guard
      // or if the redirect itself is part of the error handling.
      // console.log("Router push error (expected if redirected):", error);
    }

    // After push, current route should be /login due to redirect by guard
    // Need to allow router to process navigation.
    await router.isReady(); // Ensures navigation is complete

    expect(router.currentRoute.value.name).toBe('Login');
    expect(router.currentRoute.value.query.redirect).toBe('/dashboard');
  });

  it('allows navigation to protected route if user is authenticated', async () => {
    const authStore = useAuthStore();
    // Simulate authenticated state
    authStore.token = 'fake-token';
    authStore.user = { user_id: 1, username: 'test', email: 'test@e.com', role_name: 'customer', is_active: true, created_at: '', customer_id: 1 };
    authStore.isAuthenticated = true;

    await router.push('/dashboard');
    await router.isReady();

    expect(router.currentRoute.value.name).toBe('Dashboard');
  });

  it('redirects to /dashboard if authenticated user tries to access /login', async () => {
    const authStore = useAuthStore();
    authStore.isAuthenticated = true; // Authenticated

    await router.push('/login');
    await router.isReady();

    expect(router.currentRoute.value.name).toBe('Dashboard');
  });

  it('redirects to /dashboard if authenticated user tries to access /register', async () => {
    const authStore = useAuthStore();
    authStore.isAuthenticated = true; // Authenticated

    await router.push('/register');
    await router.isReady();

    expect(router.currentRoute.value.name).toBe('Dashboard');
  });

  it('allows navigation to public route (e.g., /) when not authenticated', async () => {
    const authStore = useAuthStore();
    authStore.isAuthenticated = false;

    // Ensure starting from a different location if router is stateful across tests
    if (router.currentRoute.value.path !== START_LOCATION.path) {
       await router.replace(START_LOCATION); // Reset to initial route
       await router.isReady();
    }

    await router.push('/');
    await router.isReady();

    expect(router.currentRoute.value.name).toBe('Home');
  });

  it('allows navigation to public route (e.g., /) when authenticated', async () => {
    const authStore = useAuthStore();
    authStore.isAuthenticated = true;

    if (router.currentRoute.value.path !== START_LOCATION.path) {
       await router.replace(START_LOCATION);
       await router.isReady();
    }

    await router.push('/');
    await router.isReady();

    expect(router.currentRoute.value.name).toBe('Home');
  });

});
```
