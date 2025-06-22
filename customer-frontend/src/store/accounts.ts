import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import accountService from '@/services/accountService';
import type { Account } from '@/types/account';

export const useAccountsStore = defineStore('accounts', () => {
  // State
  const accounts = ref<Account[]>([]);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);

  // Getters
  const getAccountList = computed(() => accounts.value);
  const isLoadingAccounts = computed(() => isLoading.value);
  const getAccountError = computed(() => error.value);

  // Actions
  async function fetchAccounts() {
    isLoading.value = true;
    error.value = null;
    try {
      const userAccounts = await accountService.fetchUserAccounts();
      accounts.value = userAccounts;
    } catch (err: any) {
      if (err.response && err.response.data && err.response.data.detail) {
        error.value = err.response.data.detail;
      } else if (err.message) {
        error.value = err.message;
      } else {
        error.value = 'Failed to fetch accounts. Please try again.';
      }
      console.error('Error in fetchAccounts store action:', err);
      accounts.value = []; // Clear accounts on error
    } finally {
      isLoading.value = false;
    }
  }

  // Action to get a single account by ID from the already fetched list
  // Or, you could add an action to fetch a single account from API if needed:
    async function fetchAccountById(accountId: string | number) {
        isLoading.value = true; // Can use a separate loading state for single account if preferred
        error.value = null;
        try {
            const accountData = await accountService.fetchAccountDetails(accountId);
            // Update or add this account in the main list
            const index = accounts.value.findIndex(acc => acc.account_id === accountData.account_id);
            if (index !== -1) {
                accounts.value[index] = accountData;
            } else {
                accounts.value.push(accountData);
            }
            // Optionally, return the fetched account directly if action is used that way
            return accountData;
        } catch (err: any) {
            if (err.response && err.response.data && err.response.data.detail) {
                error.value = err.response.data.detail;
            } else if (err.message) {
                error.value = err.message;
            } else {
                error.value = `Failed to fetch account ${accountId}.`;
            }
            console.error(`Error in fetchAccountById store action for account ${accountId}:`, err);
            throw err; // Re-throw for component to handle if needed
        } finally {
            isLoading.value = false;
        }
    }

  const getAccountById = (accountId: number | string) => {
    const id = Number(accountId); // Ensure comparison with number
    return accounts.value.find(acc => acc.account_id === id);
  };


  return {
    accounts,
    isLoading,
    error,
    getAccountList,
    isLoadingAccounts,
    getAccountError,
    fetchAccounts,
        fetchAccountById, // Expose new action
    getAccountById,
  };
});
```
