// Need to define the actions outside the return block of setup store for them to be callable correctly
// and to allow them to access other store actions or state.
// Let's redefine using options API style or ensure setup store actions are correctly structured.

// Re-structuring with options-like actions for clarity with cross-store calls.
// No, Pinia's setup store pattern is fine, just ensure actions are defined within setup scope before return.

// Add performTransfer and clearTransferStatus to the existing setup store
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import transactionService from '@customer/services/transactionService';
import type { Transaction, TransactionFilters, PaginatedTransactionsResponse } from '@customer/types/transaction';


export const useTransactionsStore = defineStore('transactions', () => {
  // State (existing)
  const transactions = ref<Transaction[]>([]);
  const isLoading = ref<boolean>(false); // General loading for list
  const error = ref<string | null>(null); // General error for list
  const currentPage = ref<number>(1); // Pagination for list
  const itemsPerPage = ref<number>(10); // Pagination for list
  const totalItems = ref<number>(0); // Pagination for list
  const totalPages = ref<number>(1); // Pagination for list
  const currentAccountId = ref<string | number | null>(null); // Context for which account's tx are loaded

  // New state for transfers
  const isTransferring = ref<boolean>(false);
  const transferError = ref<string | null>(null);
  const transferSuccessMessage = ref<string | null>(null);

  // --- Getters ---
  const getTransactionList = computed(() => transactions.value);
  const isLoadingTransactions = computed(() => isLoading.value);
  const getTransactionError = computed(() => error.value);
  const getPaginationDetails = computed(() => ({
    currentPage: currentPage.value,
    itemsPerPage: itemsPerPage.value,
    totalItems: totalItems.value,
    totalPages: totalPages.value,
  }));

  // --- Actions ---
  async function fetchTransactionHistory(
    accountId: string | number,
    page: number = 1,
    limit: number = itemsPerPage.value,
    filters: TransactionFilters = {}
  ) {
    if (currentAccountId.value !== accountId) { // Reset if context changes
        transactions.value = [];
        currentPage.value = 1;
        totalItems.value = 0;
        totalPages.value = 1;
    }
    currentAccountId.value = accountId;
    isLoading.value = true;
    error.value = null;
    try {
      const response: PaginatedTransactionsResponse = await transactionService.fetchAccountTransactions(
        accountId, page, limit, filters
      );
      transactions.value = response.items; // Assuming API returns { items: [], ... }
      currentPage.value = response.page;
      itemsPerPage.value = response.limit;
      totalItems.value = response.total_items;
      totalPages.value = response.total_pages;
    } catch (err: any) {
      if (err.response && err.response.data && err.response.data.detail) {
        error.value = err.response.data.detail;
      } else { error.value = 'Failed to fetch transaction history.'; }
    } finally {
      isLoading.value = false;
    }
  }

  function setCurrentPage(page: number) { // For components to request page change
    if (page > 0 && page <= totalPages.value) {
      currentPage.value = page;
      // Note: This only updates page number. Component should re-trigger fetch.
    }
  }

  function setItemsPerPage(newLimit: number) { // For components to change items per page
    itemsPerPage.value = newLimit;
    if (currentAccountId.value) { // Re-fetch from page 1 with new limit
        fetchTransactionHistory(currentAccountId.value, 1, newLimit);
    }
  }

  async function performTransfer(transferData: {
    from_account_id: string | number;
    to_account_id: string | number;
    amount: number;
    description?: string
  }) {
    isTransferring.value = true;
    transferError.value = null;
    transferSuccessMessage.value = null;
    let success = false;

    try {
      await transactionService.transferFunds(transferData);
      transferSuccessMessage.value = "Transfer successful!";
      success = true;

      // Attempt to refresh accounts store - dynamic import to avoid cycles
      const accountsStoreModule = await import('@customer/store/accounts');
      const accountsStore = accountsStoreModule.useAccountsStore();
      await accountsStore.fetchAccounts();

      // Re-fetch transactions for the current account if it was involved
      if (currentAccountId.value &&
         (currentAccountId.value === transferData.from_account_id ||
          currentAccountId.value === transferData.to_account_id)) {
        await fetchTransactionHistory(currentAccountId.value, currentPage.value, itemsPerPage.value);
      }

    } catch (err: any) {
      if (err.response && err.response.data && err.response.data.detail) {
        transferError.value = err.response.data.detail;
      } else {
        transferError.value = 'Transfer failed. Please try again.';
      }
      success = false;
    } finally {
      isTransferring.value = false;
    }
    return success;
  }

  function clearTransferStatus() {
    transferError.value = null;
    transferSuccessMessage.value = null;
  }

  return {
    // State
    transactions, isLoading, error,
    currentPage, itemsPerPage, totalItems, totalPages, currentAccountId,
    isTransferring, transferError, transferSuccessMessage,
    // Getters
    getTransactionList, isLoadingTransactions, getTransactionError, getPaginationDetails,
    // Actions
    fetchTransactionHistory, setCurrentPage, setItemsPerPage,
    performTransfer, clearTransferStatus,
  };
});
```
