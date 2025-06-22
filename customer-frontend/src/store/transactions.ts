import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import transactionService from '@/services/transactionService';
import type { Transaction, TransactionFilters, PaginatedTransactionsResponse } from '@/types/transaction';

export const useTransactionsStore = defineStore('transactions', () => {
  // State
  const transactions = ref<Transaction[]>([]);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);

  // Pagination state
  const currentPage = ref<number>(1);
  const itemsPerPage = ref<number>(10); // Default items per page
  const totalItems = ref<number>(0);
  const totalPages = ref<number>(1);

  // Current context (e.g., which account's transactions are loaded)
  const currentAccountId = ref<string | number | null>(null);


  // Getters
  const getTransactionList = computed(() => transactions.value);
  const isLoadingTransactions = computed(() => isLoading.value);
  const getTransactionError = computed(() => error.value);
  const getPaginationDetails = computed(() => ({
    currentPage: currentPage.value,
    itemsPerPage: itemsPerPage.value,
    totalItems: totalItems.value,
    totalPages: totalPages.value,
  }));

  // Actions
  async function fetchTransactionHistory(
    accountId: string | number,
    page: number = 1,
    limit: number = itemsPerPage.value, // Use store's itemsPerPage as default
    filters: TransactionFilters = {}
  ) {
    if (currentAccountId.value !== accountId) {
        // Reset if fetching for a new account
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
        accountId,
        page,
        limit,
        filters
      );
      transactions.value = response.items;
      currentPage.value = response.page;
      itemsPerPage.value = response.limit; // Update if API can change limit per response
      totalItems.value = response.total_items;
      totalPages.value = response.total_pages;

    } catch (err: any) {
      if (err.response && err.response.data && err.response.data.detail) {
        error.value = err.response.data.detail;
      } else if (err.message) {
        error.value = err.message;
      } else {
        error.value = 'Failed to fetch transaction history. Please try again.';
      }
      console.error(`Error in fetchTransactionHistory for account ${accountId}:`, err);
      // Optionally clear transactions on error or keep stale data
      // transactions.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  function setCurrentPage(page: number) {
    if (page > 0 && page <= totalPages.value) {
      currentPage.value = page;
      // This action alone doesn't re-fetch. The component watching currentPage should call fetch.
    }
  }

  function setItemsPerPage(newLimit: number) {
    itemsPerPage.value = newLimit;
    // Reset to page 1 and re-fetch when limit changes
    if (currentAccountId.value) {
        fetchTransactionHistory(currentAccountId.value, 1, newLimit);
    }
  }


  return {
    transactions,
    isLoading,
    error,
    currentPage,
    itemsPerPage,
    totalItems,
    totalPages,
    currentAccountId,
    // New state for transfers
    isTransferring: ref<boolean>(false),
    transferError: ref<string | null>(null),
    transferSuccessMessage: ref<string | null>(null),

    getTransactionList,
    isLoadingTransactions,
    getTransactionError,
    getPaginationDetails,
    fetchTransactionHistory,
    setCurrentPage,
    setItemsPerPage,
  };
});

// Need to define the actions outside the return block of setup store for them to be callable correctly
// and to allow them to access other store actions or state.
// Let's redefine using options API style or ensure setup store actions are correctly structured.

// Re-structuring with options-like actions for clarity with cross-store calls.
// No, Pinia's setup store pattern is fine, just ensure actions are defined within setup scope before return.

// Add performTransfer and clearTransferStatus to the existing setup store
export const useTransactionsStore = defineStore('transactions', () => {
  // State (existing)
  const transactions = ref<Transaction[]>([]);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);
  const currentPage = ref<number>(1);
  const itemsPerPage = ref<number>(10);
  const totalItems = ref<number>(0);
  const totalPages = ref<number>(1);
  const currentAccountId = ref<string | number | null>(null);

  // New state for transfers
  const isTransferring = ref<boolean>(false);
  const transferError = ref<string | null>(null);
  const transferSuccessMessage = ref<string | null>(null);

  // Getters (existing)
  const getTransactionList = computed(() => transactions.value);
  const isLoadingTransactions = computed(() => isLoading.value); // This might need to be separate from isTransferring
  const getTransactionError = computed(() => error.value);
  const getPaginationDetails = computed(() => ({
    currentPage: currentPage.value,
    itemsPerPage: itemsPerPage.value,
    totalItems: totalItems.value,
    totalPages: totalPages.value,
  }));

  // Actions (existing)
  async function fetchTransactionHistory(
    accountId: string | number,
    page: number = 1,
    limit: number = itemsPerPage.value,
    filters: TransactionFilters = {}
  ) {
    if (currentAccountId.value !== accountId) {
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
      transactions.value = response.items;
      currentPage.value = response.page;
      itemsPerPage.value = response.limit;
      totalItems.value = response.total_items;
      totalPages.value = response.total_pages;
    } catch (err: any) {
      // Error handling... (same as before)
      if (err.response && err.response.data && err.response.data.detail) {
        error.value = err.response.data.detail;
      } else { error.value = 'Failed to fetch transaction history.'; }
    } finally {
      isLoading.value = false;
    }
  }

  function setCurrentPage(page: number) {
    if (page > 0 && page <= totalPages.value) {
      currentPage.value = page;
    }
  }

  function setItemsPerPage(newLimit: number) {
    itemsPerPage.value = newLimit;
    if (currentAccountId.value) {
        fetchTransactionHistory(currentAccountId.value, 1, newLimit);
    }
  }

  // New Actions for Transfer
  // Import accounts store for updating balances after transfer
  const { useAccountsStore } = await import('@/store/accounts'); // Dynamic import to avoid cycles if modules are complexly related
                                                               // Or, structure so this is not an issue (e.g. event bus)
                                                               // Simpler: Direct import, assuming Vite handles it.
  // import { useAccountsStore } from './accounts'; // This might cause issues if accounts store imports this one.
  // A common pattern is to pass the Pinia instance to stores or use a plugin for cross-store access.
  // For now, let's try direct import and see. If it fails, use dynamic or alternative.
  // Let's assume direct import works for now for simplicity of this step.
  // const accountsStore = useAccountsStore(); // This cannot be called at the top level of setup store.
  // It needs to be called inside an action or computed property when Pinia is active.

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

      // Refresh accounts list in accountsStore as balances have changed
      // This is the tricky part for cross-store updates.
      // Option 1: Direct import and call (might lead to circular deps if not careful)
      const accountsStore = useAccountsStore(); // Call inside action
      await accountsStore.fetchAccounts();

      // Option 2: Emit an event that App.vue or a layout listens to, then calls fetchAccounts.
      // Option 3: Pass callback or use a more advanced state management pattern.

      // Re-fetch transactions for the current account if it was involved in the transfer
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
      console.error('Error in performTransfer store action:', err);
      success = false;
      // Do not re-throw, let component check success status and error message from store
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
    transactions, isLoading, error,
    currentPage, itemsPerPage, totalItems, totalPages, currentAccountId,
    isTransferring, transferError, transferSuccessMessage, // New state
    getTransactionList, isLoadingTransactions, getTransactionError, getPaginationDetails,
    fetchTransactionHistory, setCurrentPage, setItemsPerPage,
    performTransfer, clearTransferStatus, // New actions
  };
});
```
