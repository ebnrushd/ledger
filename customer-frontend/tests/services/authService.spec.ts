import { describe, it, expect, vi, beforeEach } from 'vitest';
import authService from '@/services/authService';
import apiClient from '@/services/apiClient'; // To be mocked
import type { UserCreateAPI } from '@/types/user';

// Mock the apiClient
vi.mock('@/services/apiClient', () => ({
  default: {
    post: vi.fn(),
    // get: vi.fn(), // if other methods were used by authService
  },
}));

describe('Auth Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('loginUser', () => {
    it('should call apiClient.post with correct URL, data, and headers for login', async () => {
      const credentials = { username: 'test@example.com', password: 'password123' };
      const mockResponse = { data: { access_token: 'fake-token', token_type: 'bearer' } };
      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

      const result = await authService.loginUser(credentials);

      expect(apiClient.post).toHaveBeenCalledTimes(1);
      // Check URL
      expect((apiClient.post as ReturnType<typeof vi.fn>).mock.calls[0][0]).toBe('/auth/login');

      // Check data (URLSearchParams)
      const sentParams = (apiClient.post as ReturnType<typeof vi.fn>).mock.calls[0][1] as URLSearchParams;
      expect(sentParams.get('username')).toBe(credentials.username);
      expect(sentParams.get('password')).toBe(credentials.password);

      // Check headers
      expect((apiClient.post as ReturnType<typeof vi.fn>).mock.calls[0][2]).toEqual({
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      expect(result).toEqual(mockResponse);
    });

    it('should re-throw error if apiClient.post fails for login', async () => {
      const credentials = { username: 'test@example.com', password: 'password123' };
      const mockError = new Error('Network failure');
      (apiClient.post as ReturnType<typeof vi.fn>).mockRejectedValue(mockError);

      await expect(authService.loginUser(credentials)).rejects.toThrow('Network failure');
    });
  });

  describe('registerUser', () => {
    it('should call apiClient.post with correct URL and JSON data for register', async () => {
      const userData: UserCreateAPI = {
        username: 'newuser@example.com',
        email: 'newuser@example.com',
        password: 'Password123!',
        first_name: 'New',
        last_name: 'User',
      };
      const mockResponse = { data: { user_id: 1, ...userData } }; // Simplified response
      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

      const result = await authService.registerUser(userData);

      expect(apiClient.post).toHaveBeenCalledTimes(1);
      expect((apiClient.post as ReturnType<typeof vi.fn>).mock.calls[0][0]).toBe('/auth/register');
      expect((apiClient.post as ReturnType<typeof vi.fn>).mock.calls[0][1]).toEqual(userData); // JSON data
      expect(result).toEqual(mockResponse);
    });

    it('should re-throw error if apiClient.post fails for register', async () => {
      const userData: UserCreateAPI = {
        username: 'newuser@example.com', email: 'newuser@example.com', password: 'Password123!',
        first_name: 'New', last_name: 'User',
      };
      const mockError = new Error('Registration failed');
      (apiClient.post as ReturnType<typeof vi.fn>).mockRejectedValue(mockError);

      await expect(authService.registerUser(userData)).rejects.toThrow('Registration failed');
    });
  });
});
```
