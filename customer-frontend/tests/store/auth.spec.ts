import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAuthStore } from '@/store/auth';
import authService from '@/services/authService'; // To be mocked
import apiClient from '@/services/apiClient'; // To check default headers
import type { User, TokenPayload } from '@/types/user';
import { jwtDecode } from 'jwt-decode'; // Actual jwtDecode for tests if needed for complex checks

// Mock the authService
vi.mock('@/services/authService', () => ({
  default: {
    loginUser: vi.fn(),
    registerUser: vi.fn(),
  },
}));

// Mock jwt-decode
vi.mock('jwt-decode', () => ({
  jwtDecode: vi.fn(),
}));


describe('Auth Store (Pinia)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    // Reset localStorage before each test relevant to authStore
    localStorage.clear();
    // Reset mocks
    vi.clearAllMocks();
  });

  it('initial state', () => {
    const authStore = useAuthStore();
    expect(authStore.token).toBeNull();
    expect(authStore.user).toBeNull();
    expect(authStore.isAuthenticated).toBe(false);
    expect(authStore.loginError).toBeNull();
  });

  describe('login action', () => {
    it('successful login updates state and localStorage', async () => {
      const authStore = useAuthStore();
      const mockToken = 'mock-jwt-token';
      const mockUsername = 'test@example.com';
      const mockDecodedToken: TokenPayload = {
        sub: mockUsername,
        user_id: 1,
        role: 'customer',
        exp: Date.now() / 1000 + 3600, // Expires in 1 hour
        customer_id: 101
      };

      (authService.loginUser as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { access_token: mockToken, token_type: 'bearer' },
      });
      (jwtDecode as ReturnType<typeof vi.fn>).mockReturnValue(mockDecodedToken);

      await authStore.login({ username: mockUsername, password: 'password' });

      expect(authService.loginUser).toHaveBeenCalledWith({ username: mockUsername, password: 'password' });
      expect(authStore.token).toBe(mockToken);
      expect(authStore.user).toEqual({
        user_id: 1,
        username: mockUsername,
        email: mockUsername, // As per current _setAuthData logic
        role_name: 'customer',
        is_active: true,
        customer_id: 101,
        created_at: '', // Not set by _setAuthData from token alone
        last_login: expect.any(String), // Approximate check
      });
      expect(authStore.isAuthenticated).toBe(true);
      expect(localStorage.getItem('authToken')).toBe(mockToken);
      expect(JSON.parse(localStorage.getItem('authUser') || '{}')).toEqual(authStore.user);
      expect(apiClient.defaults.headers.common['Authorization']).toBe(`Bearer ${mockToken}`);
      expect(authStore.loginError).toBeNull();
    });

    it('failed login sets error and clears auth data', async () => {
      const authStore = useAuthStore();
      const apiError = { response: { data: { detail: 'Invalid credentials' } } };
      (authService.loginUser as ReturnType<typeof vi.fn>).mockRejectedValue(apiError);

      await expect(authStore.login({ username: 'wrong@example.com', password: 'wrong' }))
        .rejects.toEqual(apiError); // Check if error is re-thrown

      expect(authStore.loginError).toBe('Invalid credentials');
      expect(authStore.token).toBeNull();
      expect(authStore.user).toBeNull();
      expect(authStore.isAuthenticated).toBe(false);
      expect(localStorage.getItem('authToken')).toBeNull();
      expect(apiClient.defaults.headers.common['Authorization']).toBeUndefined();
    });
  });

  describe('register action', () => {
    it('successful registration sets success message', async () => {
      const authStore = useAuthStore();
      const userData = { username: 'new@example.com', password: 'password123', first_name: 'New', last_name: 'User', email: 'new@example.com' };
      (authService.registerUser as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { username: 'new@example.com', /* other user fields */ },
      });

      await authStore.register(userData);
      expect(authService.registerUser).toHaveBeenCalledWith(userData);
      expect(authStore.registerSuccessMessage).toContain('Registration successful for new@example.com');
      expect(authStore.registerError).toBeNull();
    });

    it('failed registration sets error message', async () => {
        const authStore = useAuthStore();
        const userData = { username: 'new@example.com', password: 'password123', first_name: 'New', last_name: 'User', email: 'new@example.com' };
        const apiError = { response: { data: { detail: 'Email already exists' } } };
        (authService.registerUser as ReturnType<typeof vi.fn>).mockRejectedValue(apiError);

        await expect(authStore.register(userData)).rejects.toEqual(apiError);
        expect(authStore.registerError).toBe('Email already exists');
        expect(authStore.registerSuccessMessage).toBeNull();
      });
  });

  describe('logout action', () => {
    it('clears auth state and localStorage', () => {
      const authStore = useAuthStore();
      // Simulate logged-in state
      const mockToken = 'mock-jwt-token';
      const mockUsername = 'test@example.com';
      const mockDecodedToken: TokenPayload = { sub: mockUsername, user_id: 1, role: 'customer', exp: Date.now() / 1000 + 3600, customer_id: 101 };
      authStore._setAuthData(mockToken, mockDecodedToken); // Use internal helper to set state for test

      expect(authStore.isAuthenticated).toBe(true);

      authStore.logout(); // Router not passed, will use window.location

      expect(authStore.token).toBeNull();
      expect(authStore.user).toBeNull();
      expect(authStore.isAuthenticated).toBe(false);
      expect(localStorage.getItem('authToken')).toBeNull();
      expect(localStorage.getItem('authUser')).toBeNull();
      expect(apiClient.defaults.headers.common['Authorization']).toBeUndefined();
    });
  });

  describe('tryAutoLogin action', () => {
    it('restores session from valid localStorage token', () => {
      const authStore = useAuthStore();
      const mockToken = 'valid-token-for-autologin';
      const mockUsername = 'autologin@example.com';
      const mockDecodedToken: TokenPayload = {
        sub: mockUsername,
        user_id: 2,
        role: 'customer',
        exp: Date.now() / 1000 + 3600, // Not expired
        customer_id: 102
      };
      const mockUser = { user_id: 2, username: mockUsername, email: mockUsername, role_name: 'customer', is_active: true, customer_id: 102, created_at: '', last_login: ''};

      localStorage.setItem('authToken', mockToken);
      localStorage.setItem('authUser', JSON.stringify(mockUser)); // Store mock user as _setAuthData would
      (jwtDecode as ReturnType<typeof vi.fn>).mockReturnValue(mockDecodedToken);

      authStore.tryAutoLogin();

      expect(authStore.isAuthenticated).toBe(true);
      expect(authStore.token).toBe(mockToken);
      expect(authStore.user?.user_id).toBe(2);
      expect(authStore.user?.username).toBe(mockUsername);
      expect(apiClient.defaults.headers.common['Authorization']).toBe(`Bearer ${mockToken}`);
    });

    it('clears session if token is expired', () => {
        const authStore = useAuthStore();
        const mockToken = 'expired-token';
        const mockDecodedToken: TokenPayload = {
          sub: 'user', user_id: 3, role: 'customer',
          exp: Date.now() / 1000 - 3600 // Expired one hour ago
        };

        localStorage.setItem('authToken', mockToken);
        (jwtDecode as ReturnType<typeof vi.fn>).mockReturnValue(mockDecodedToken);

        authStore.tryAutoLogin();

        expect(authStore.isAuthenticated).toBe(false);
        expect(authStore.token).toBeNull();
        expect(localStorage.getItem('authToken')).toBeNull(); // Should be cleared
      });
  });

  // TODO: Tests for profile and password change actions
});
```
