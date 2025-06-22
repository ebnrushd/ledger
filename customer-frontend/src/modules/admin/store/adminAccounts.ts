import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import adminAccountService from '@admin/services/adminAccountService';
import type { AdminAccount, AccountStatusType, PaginatedAdminAccountsResponse } from '@admin/types/account';
import type { Decimal } from 'decimal.js'; // Or number if not using Decimal.js

export const useAdminAccountsStore = defineStore('adminAccounts', () => {
  // State
  const accounts = ref<AdminAccount[]>([]);
  const selectedAccount = ref<AdminAccount | null>(null);
  const accountStatusTypes = ref<AccountStatusType[]>([]);

  const isLoadingList = ref<boolean>(false);
  const isLoadingDetails = ref<boolean>(false);
  const isUpdatingStatus = ref<boolean>(false);
  const isUpdatingOverdraft = ref<boolean>(false);

  const error = ref<string | null>(null); // General error for list/details
  const updateError = ref<string | null>(null); // Specific for update operations
  const successMessage = ref<string | null>(null);

  // Pagination state
  const currentPage = ref<number>(1);
  const itemsPerPage = ref<number>(10);
  const totalItems = ref<number>(0);
  const totalPages = ref<number>(1);

  // Getters
  const getAccountList = computed(() => accounts.value);
  const getSelectedAccount = computed(() => selectedAccount.value);
  const getAccountStatusTypes = computed(() => accountStatusTypes.value);
  const getPagination = computed(() => ({
    currentPage: currentPage.value, itemsPerPage: itemsPerPage.value,
    totalItems: totalItems.value, totalPages: totalPages.value,
  }));

  // Actions
  async function fetchAccounts(page: number = 1, limit: number = itemsPerPage.value, filters: any = {}) {
    isLoadingList.value = true;
    error.value = null;
    try {
      const response = await adminAccountService.fetchAdminAccounts(page, limit, filters);
      accounts.value = response.accounts;
      currentPage.value = response.page;
      itemsPerPage.value = response.per_page;
      totalItems.value = response.total_items;
      totalPages.value = response.total_pages;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch accounts.';
      accounts.value = [];
    } finally {
      isLoadingList.value = false;
    }
  }

  async function fetchAccountDetails(accountId: string | number) {
    isLoadingDetails.value = true;
    error.value = null; // Clear general list error, or use specific detailError
    selectedAccount.value = null;
    try {
      const accountData = await adminAccountService.fetchAdminAccountDetailsById(accountId);
      selectedAccount.value = accountData;
      return accountData;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || `Failed to fetch account details for ID ${accountId}.`;
      throw err;
    } finally {
      isLoadingDetails.value = false;
    }
  }

  async function updateAccountStatus(accountId: string | number, statusName: string): Promise<boolean> {
    isUpdatingStatus.value = true;
    updateError.value = null;
    successMessage.value = null;
    try {
      const updatedAccount = await adminAccountService.updateAdminAccountStatus(accountId, statusName);
      selectedAccount.value = updatedAccount; // Update details if viewing this account
      // Refresh list if current view is list, or find and update in list
      const index = accounts.value.findIndex(acc => acc.account_id === updatedAccount.account_id);
      if (index !== -1) accounts.value[index] = updatedAccount;

      successMessage.value = `Account ${updatedAccount.account_number} status updated to ${statusName}.`;
      return true;
    } catch (err: any)
       updateError.value = err.response?.data?.detail || err.message || 'Failed to update account status.';
      return false;
    } finally {
      isUpdatingStatus.value = false;
    }
  }

  async function updateOverdraftLimit(accountId: string | number, newLimit: number): Promise<boolean> {
    isUpdatingOverdraft.value = true;
    updateError.value = null;
    successMessage.value = null;
    try {
      const updatedAccount = await adminAccountService.updateAdminAccountOverdraftLimit(accountId, newLimit);
      selectedAccount.value = updatedAccount;
      const index = accounts.value.findIndex(acc => acc.account_id === updatedAccount.account_id);
      if (index !== -1) accounts.value[index] = updatedAccount;

      successMessage.value = `Account ${updatedAccount.account_number} overdraft limit updated to ${newLimit.toFixed(2)}.`;
      return true;
    } catch (err: any) {
      updateError.value = err.response?.data?.detail || err.message || 'Failed to update overdraft limit.';
      return false;
    } finally {
      isUpdatingOverdraft.value = false;
    }
  }

  async function fetchAccountStatusTypes() {
    // isLoadingRoles.value = true; // Consider separate loading flag if needed
    // rolesError.value = null;
    try {
      const types = await adminAccountService.fetchAdminAccountStatusTypes();
      accountStatusTypes.value = types;
    } catch (err: any)
      // rolesError.value = err.response?.data?.detail || err.message || 'Failed to fetch account status types.';
      console.error("Failed to fetch account status types:", err); // Log, but use fallback from service
      // If service has fallback, this might not be critical to block UI
      // If it throws and has no fallback, then set an error.
      if (accountStatusTypes.value.length === 0) { // If service didn't provide fallback and threw
          error.value = "Could not load account status types for forms."
      }
    } finally {
      // isLoadingRoles.value = false;
    }
  }

  function clearMessages() {
    error.value = null;
    updateError.value = null;
    successMessage.value = null;
  }

  return {
    accounts, selectedAccount, accountStatusTypes,
    isLoadingList, isLoadingDetails, isUpdatingStatus, isUpdatingOverdraft,
    error, updateError, successMessage,
    currentPage, itemsPerPage, totalItems, totalPages,
    getAccountList, getSelectedAccount, getAccountStatusTypes, getPaginationDetails,
    fetchAccounts, fetchAccountDetails, updateAccountStatus, updateOverdraftLimit,
    fetchAccountStatusTypes, clearMessages,
  };
});
```
