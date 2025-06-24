import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAdminAccountsStore } from '@admin/store/adminAccounts';
import adminAccountService from '@admin/services/adminAccountService';

// Mock the adminAccountService
vi.mock('@admin/services/adminAccountService', () => ({
  default: {
    fetchAdminAccounts: vi.fn(),
    fetchAdminAccountDetailsById: vi.fn(),
    updateAdminAccountStatus: vi.fn(),
    updateAdminAccountOverdraftLimit: vi.fn(),
    fetchAdminAccountStatusTypes: vi.fn(),
  },
}));

describe('Admin Accounts Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    // Reset mocks before each test
    vi.clearAllMocks();
  });

  it('initializes with correct default values', () => {
    const store = useAdminAccountsStore();
    expect(store.accounts).toEqual([]);
    expect(store.selectedAccount).toBeNull();
    expect(store.isLoadingList).toBe(false);
    expect(store.error).toBeNull();
    expect(store.currentPage).toBe(1);
  });

  describe('fetchAccounts', () => {
    it('fetches accounts successfully', async () => {
      const store = useAdminAccountsStore();
      const mockResponse = {
        accounts: [{ account_id: 1, account_number: '123', status_name: 'active' }],
        page: 1,
        per_page: 10,
        total_items: 1,
        total_pages: 1,
      };
      (adminAccountService.fetchAdminAccounts as vi.Mock).mockResolvedValue(mockResponse);

      await store.fetchAccounts(1, 10, {});

      expect(store.isLoadingList).toBe(false);
      expect(store.accounts).toEqual(mockResponse.accounts);
      expect(store.currentPage).toBe(mockResponse.page);
      expect(store.totalItems).toBe(mockResponse.total_items);
      expect(store.error).toBeNull();
    });

    it('handles error during fetchAccounts', async () => {
      const store = useAdminAccountsStore();
      (adminAccountService.fetchAdminAccounts as vi.Mock).mockRejectedValue(new Error('Network error'));

      await store.fetchAccounts(1, 10, {});

      expect(store.isLoadingList).toBe(false);
      expect(store.accounts).toEqual([]);
      expect(store.error).toBe('Network error');
    });
  });

  describe('updateAccountStatus', () => {
    it('updates account status and calls refresh callback if provided', async () => {
      const store = useAdminAccountsStore();
      const mockUpdatedAccount = { account_id: 1, account_number: '123', status_name: 'active' };
      (adminAccountService.updateAdminAccountStatus as vi.Mock).mockResolvedValue(mockUpdatedAccount);

      const refreshCallback = vi.fn().mockResolvedValue(undefined);

      const result = await store.updateAccountStatus(1, 'active', refreshCallback);

      expect(result).toBe(true);
      expect(store.isUpdatingStatus).toBe(false);
      expect(store.selectedAccount).toEqual(mockUpdatedAccount); // Assuming it also updates selectedAccount
      expect(store.successMessage).toContain('status updated to active');
      expect(refreshCallback).toHaveBeenCalledTimes(1);
      expect(store.updateError).toBeNull();
    });

    it('updates account status and updates item in list if no callback', async () => {
      const store = useAdminAccountsStore();
      // Pre-fill accounts list
      store.accounts = [{ account_id: 1, account_number: '123', status_name: 'pending_approval' }] as any;

      const mockUpdatedAccount = { account_id: 1, account_number: '123', status_name: 'active' };
      (adminAccountService.updateAdminAccountStatus as vi.Mock).mockResolvedValue(mockUpdatedAccount);

      const result = await store.updateAccountStatus(1, 'active', null);

      expect(result).toBe(true);
      expect(store.isUpdatingStatus).toBe(false);
      expect(store.accounts[0]).toEqual(mockUpdatedAccount); // Check if item in list is updated
      expect(store.successMessage).toContain('status updated to active');
    });

    it('handles error during updateAccountStatus', async () => {
      const store = useAdminAccountsStore();
      (adminAccountService.updateAdminAccountStatus as vi.Mock).mockRejectedValue(new Error('Update failed'));

      const refreshCallback = vi.fn();
      const result = await store.updateAccountStatus(1, 'active', refreshCallback);

      expect(result).toBe(false);
      expect(store.isUpdatingStatus).toBe(false);
      expect(store.updateError).toBe('Update failed');
      expect(store.successMessage).toBeNull();
      expect(refreshCallback).not.toHaveBeenCalled();
    });
  });

  describe('fetchAccountStatusTypes', () => {
    it('fetches account status types successfully', async () => {
      const store = useAdminAccountsStore();
      const mockStatusTypes = [{ status_id: 1, status_name: 'active' }];
      (adminAccountService.fetchAdminAccountStatusTypes as vi.Mock).mockResolvedValue(mockStatusTypes);

      await store.fetchAccountStatusTypes();

      expect(store.accountStatusTypes).toEqual(mockStatusTypes);
      expect(store.error).toBeNull(); // Assuming 'error' is for general list/details, not for this specific fetch
    });

    it('handles error during fetchAccountStatusTypes and uses fallback if service returns empty', async () => {
      const store = useAdminAccountsStore();
      // Simulate service throwing an error AND store.accountStatusTypes is empty initially
      store.accountStatusTypes = [];
      (adminAccountService.fetchAdminAccountStatusTypes as vi.Mock).mockRejectedValue(new Error('API down'));

      await store.fetchAccountStatusTypes();

      // The store's fetchAccountStatusTypes logs error but doesn't throw, relies on service's fallback.
      // If service fallback is also empty or fails, it sets store.error.
      // The current service mock returns a promise that resolves with some values upon error,
      // so store.error might not be set unless that fallback fails or is removed.
      // Let's test the condition where the service fails and the list remains empty, setting store.error.
      // For this, we need the service mock to not return a fallback for this specific test path.
      (adminAccountService.fetchAdminAccountStatusTypes as vi.Mock).mockImplementation(async () => {
        throw new Error("API is down and no fallback from service for this test");
      });
      store.accountStatusTypes = []; // Reset for this specific test case

      await store.fetchAccountStatusTypes();
      expect(store.accountStatusTypes).toEqual([]);
      expect(store.error).toBe("Could not load account status types for forms.");
    });

     it('uses service fallback if API fails and store list is initially empty', async () => {
      const store = useAdminAccountsStore();
      store.accountStatusTypes = []; // Ensure it's empty
      // Default mock for fetchAdminAccountStatusTypes in adminAccountService returns a fallback on error.
      // So, we reset to the default mock behavior for this test.
      vi.mocked(adminAccountService.fetchAdminAccountStatusTypes).mockImplementation(async () => {
        // This is the fallback behavior defined in the actual service
        console.warn('Error fetching admin account status types from API, using mock/fallback (VITEST MOCK)');
        return Promise.resolve([
            { status_id: 1, status_name: 'active' },
            { status_id: 2, status_name: 'frozen' },
            { status_id: 3, status_name: 'closed' },
        ]);
      });


      await store.fetchAccountStatusTypes();

      expect(store.accountStatusTypes.length).toBeGreaterThan(0);
      expect(store.error).toBeNull(); // Error should be null because fallback was used by service
    });
  });
});
```
