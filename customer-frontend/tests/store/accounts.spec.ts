import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAccountsStore } from '@/store/accounts';
import accountService from '@/services/accountService'; // To be mocked
import type { Account } from '@/types/account';

// Mock the accountService
vi.mock('@/services/accountService', () => ({
  default: {
    fetchUserAccounts: vi.fn(),
    fetchAccountDetails: vi.fn(), // If testing fetchAccountById
  },
}));

describe('Accounts Store (Pinia)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('initial state', () => {
    const accountsStore = useAccountsStore();
    expect(accountsStore.accounts).toEqual([]);
    expect(accountsStore.isLoading).toBe(false);
    expect(accountsStore.error).toBeNull();
  });

  describe('fetchAccounts action', () => {
    const mockAccounts: Account[] = [
      { account_id: 1, customer_id: 1, account_number: 'ACC001', account_type: 'savings', balance: 1000, currency: 'USD', status_name: 'active', overdraft_limit: 0, opened_at: new Date().toISOString() },
      { account_id: 2, customer_id: 1, account_number: 'ACC002', account_type: 'checking', balance: 500, currency: 'USD', status_name: 'active', overdraft_limit: 50, opened_at: new Date().toISOString() },
    ];

    it('successfully fetches and stores accounts', async () => {
      const accountsStore = useAccountsStore();
      (accountService.fetchUserAccounts as ReturnType<typeof vi.fn>).mockResolvedValue(mockAccounts);

      await accountsStore.fetchAccounts();

      expect(accountService.fetchUserAccounts).toHaveBeenCalledTimes(1);
      expect(accountsStore.accounts).toEqual(mockAccounts);
      expect(accountsStore.isLoading).toBe(false);
      expect(accountsStore.error).toBeNull();
    });

    it('handles API error when fetching accounts', async () => {
      const accountsStore = useAccountsStore();
      const errorMessage = 'Network Error';
      (accountService.fetchUserAccounts as ReturnType<typeof vi.fn>).mockRejectedValue({ message: errorMessage });

      await accountsStore.fetchAccounts();

      expect(accountsStore.error).toBe(errorMessage);
      expect(accountsStore.accounts).toEqual([]); // Should clear accounts on error
      expect(accountsStore.isLoading).toBe(false);
    });

    it('handles API error with response.data.detail', async () => {
        const accountsStore = useAccountsStore();
        const detailErrorMessage = 'Specific API error detail';
        (accountService.fetchUserAccounts as ReturnType<typeof vi.fn>).mockRejectedValue({
          response: { data: { detail: detailErrorMessage } }
        });

        await accountsStore.fetchAccounts();

        expect(accountsStore.error).toBe(detailErrorMessage);
        expect(accountsStore.isLoading).toBe(false);
      });
  });

  describe('fetchAccountById action', () => {
    const mockAccount: Account = {
        account_id: 1, customer_id: 1, account_number: 'ACC001', account_type: 'savings',
        balance: 1000, currency: 'USD', status_name: 'active', overdraft_limit: 0, opened_at: new Date().toISOString()
    };

    it('successfully fetches and adds/updates a single account', async () => {
        const accountsStore = useAccountsStore();
        (accountService.fetchAccountDetails as ReturnType<typeof vi.fn>).mockResolvedValue(mockAccount);

        const fetchedAccount = await accountsStore.fetchAccountById(1);

        expect(accountService.fetchAccountDetails).toHaveBeenCalledWith(1);
        expect(fetchedAccount).toEqual(mockAccount);
        expect(accountsStore.accounts).toContainEqual(mockAccount);
        expect(accountsStore.isLoading).toBe(false); // Assuming fetchAccountById also sets loading state
        expect(accountsStore.error).toBeNull();

        // Test update if account already exists
        const updatedMockAccount = { ...mockAccount, balance: 1200 };
        (accountService.fetchAccountDetails as ReturnType<typeof vi.fn>).mockResolvedValue(updatedMockAccount);
        await accountsStore.fetchAccountById(1);
        expect(accountsStore.accounts.find(acc => acc.account_id === 1)?.balance).toBe(1200);
        expect(accountsStore.accounts.length).toBe(1); // Still one account
    });

    it('handles error when fetching a single account', async () => {
        const accountsStore = useAccountsStore();
        const errorMessage = "Failed to fetch single account";
        (accountService.fetchAccountDetails as ReturnType<typeof vi.fn>).mockRejectedValue({ message: errorMessage });

        await expect(accountsStore.fetchAccountById(99)).rejects.toMatchObject({ message: errorMessage });
        expect(accountsStore.error).toBe(errorMessage);
    });
  });

  describe('getAccountById getter/selector', () => {
    it('returns correct account from state if present', () => {
        const accountsStore = useAccountsStore();
        const acc1: Account = { account_id: 1, customer_id:1, account_number: 'A1', account_type: 's', balance: 10, currency: 'USD', status_name:'active', overdraft_limit:0, opened_at: ''};
        const acc2: Account = { account_id: 2, customer_id:1, account_number: 'A2', account_type: 'c', balance: 20, currency: 'USD', status_name:'active', overdraft_limit:0, opened_at: ''};
        accountsStore.accounts = [acc1, acc2];

        expect(accountsStore.getAccountById(1)).toEqual(acc1);
        expect(accountsStore.getAccountById(2)).toEqual(acc2);
        expect(accountsStore.getAccountById(3)).toBeUndefined();
    });
  });

});
```
