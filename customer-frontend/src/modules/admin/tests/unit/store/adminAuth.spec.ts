import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAdminAuthStore } from '@admin/store/adminAuth';
import adminAuthService from '@admin/services/adminAuthService';

vi.mock('@admin/services/adminAuthService', () => ({
  default: {
    loginAdmin: vi.fn(),
    logoutAdmin: vi.fn(),
    fetchCurrentAdminUser: vi.fn(),
  },
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => (store[key] = value.toString()),
    removeItem: (key: string) => delete store[key],
    clear: () => (store = {}),
  };
})();
vi.stubGlobal('localStorage', localStorageMock);


describe('Admin Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorage.clear(); // Clear localStorage before each test
  });

  it('initializes with correct default values', () => {
    const store = useAdminAuthStore();
    expect(store.adminUser).toBeNull();
    expect(store.isAdminAuthenticated).toBe(false);
    expect(store.authError).toBeNull();
    expect(store.isLoading).toBe(false);
  });

  describe('login action', () => {
    it('sets user and token on successful login', async () => {
      const store = useAdminAuthStore();
      const mockUserData = { user_id: 1, username: 'admin', email: 'admin@example.com', role_name: 'admin', is_active: true };
      (adminAuthService.loginAdmin as vi.Mock).mockResolvedValue(mockUserData);
      // fetchCurrentAdminUser is called by loginAdmin service, so it's part of the mock for loginAdmin

      await store.login({ username: 'admin', password: 'password' });

      expect(store.adminUser).toEqual(mockUserData);
      expect(store.isAdminAuthenticated).toBe(true);
      expect(store.authError).toBeNull();
      expect(localStorage.getItem('isAdminLoggedIn')).toBe('true');
    });

    it('sets error on failed login', async () => {
      const store = useAdminAuthStore();
      (adminAuthService.loginAdmin as vi.Mock).mockRejectedValue({ response: { data: { detail: 'Login failed' } } });

      try {
        await store.login({ username: 'admin', password: 'wrongpassword' });
      } catch (e) {
        // Expected to throw
      }

      expect(store.adminUser).toBeNull();
      expect(store.isAdminAuthenticated).toBe(false);
      expect(store.authError).toBe('Login failed');
      expect(localStorage.getItem('isAdminLoggedIn')).toBeNull();
    });
  });

  describe('logout action', () => {
    it('clears user and token on logout', async () => {
      const store = useAdminAuthStore();
      // Simulate logged-in state
      store.adminUser = { user_id: 1, username: 'admin', email: 'admin@example.com', role_name: 'admin', is_active: true };
      store.isAdminAuthenticated = true;
      localStorage.setItem('isAdminLoggedIn', 'true');
      (adminAuthService.logoutAdmin as vi.Mock).mockResolvedValue(undefined);

      await store.logout();

      expect(store.adminUser).toBeNull();
      expect(store.isAdminAuthenticated).toBe(false);
      expect(localStorage.getItem('isAdminLoggedIn')).toBeNull();
    });
  });

  describe('checkAuthStatus action', () => {
    it('authenticates user if service returns user data', async () => {
      const store = useAdminAuthStore();
      const mockUserData = { user_id: 1, username: 'admin', email: 'admin@example.com', role_name: 'admin', is_active: true };
      (adminAuthService.fetchCurrentAdminUser as vi.Mock).mockResolvedValue(mockUserData);

      const result = await store.checkAuthStatus();

      expect(result).toBe(true);
      expect(store.isAdminAuthenticated).toBe(true);
      expect(store.adminUser).toEqual(mockUserData);
    });

    it('does not authenticate if service fails', async () => {
      const store = useAdminAuthStore();
      (adminAuthService.fetchCurrentAdminUser as vi.Mock).mockRejectedValue(new Error('Session expired'));

      const result = await store.checkAuthStatus();

      expect(result).toBe(false);
      expect(store.isAdminAuthenticated).toBe(false);
      expect(store.adminUser).toBeNull();
    });
  });
});
```
