import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import adminTransactionService from '@admin/services/adminTransactionService';
import type {
    AdminTransactionListItem,
    AdminTransactionDetail,
    PaginatedAdminTransactionsResponse,
    AdminTransactionFilters
} from '@admin/types/transaction';
import type { TransactionType } from '@admin/types/lookups';

export const useAdminTransactionsStore = defineStore('adminTransactions', () => {
  // State
  const transactions = ref<AdminTransactionListItem[]>([]);
  const selectedTransaction = ref<AdminTransactionDetail | null>(null);
  const transactionTypes = ref<TransactionType[]>([]);

  const isLoadingList = ref<boolean>(false);
  const isLoadingDetails = ref<boolean>(false);
  const isLoadingTypes = ref<boolean>(false); // Separate loading for types
  const error = ref<string | null>(null); // General error

  // Pagination state
  const currentPage = ref<number>(1);
  const itemsPerPage = ref<number>(10);
  const totalItems = ref<number>(0);
  const totalPages = ref<number>(1);

  // Getters
  const getTransactionList = computed(() => transactions.value);
  const getSelectedTransaction = computed(() => selectedTransaction.value);
  const getTransactionTypes = computed(() => transactionTypes.value);
  const getPagination = computed(() => ({
    currentPage: currentPage.value, itemsPerPage: itemsPerPage.value,
    totalItems: totalItems.value, totalPages: totalPages.value,
  }));

  // Actions
  async function fetchTransactions(page: number = 1, limit: number = itemsPerPage.value, filters: AdminTransactionFilters = {}) {
    isLoadingList.value = true;
    error.value = null;
    try {
      const response = await adminTransactionService.fetchAdminTransactions(page, limit, filters);
      transactions.value = response.transactions;
      currentPage.value = response.page;
      itemsPerPage.value = response.per_page;
      totalItems.value = response.total_items;
      totalPages.value = response.total_pages;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch transactions.';
      transactions.value = [];
    } finally {
      isLoadingList.value = false;
    }
  }

  async function fetchTransactionDetails(transactionId: string | number) {
    isLoadingDetails.value = true;
    error.value = null;
    selectedTransaction.value = null;
    try {
      const txData = await adminTransactionService.fetchAdminTransactionDetailsById(transactionId);
      selectedTransaction.value = txData;
      return txData;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || `Failed to fetch transaction details for ID ${transactionId}.`;
      throw err;
    } finally {
      isLoadingDetails.value = false;
    }
  }

  async function fetchTransactionTypes() {
    isLoadingTypes.value = true;
    // error.value = null; // Could use a separate error for types if needed
    try {
      const types = await adminTransactionService.fetchAdminTransactionTypes();
      transactionTypes.value = types;
    } catch (err: any) {
      console.error("Failed to fetch transaction types:", err);
      // error.value = err.response?.data?.detail || err.message || 'Failed to fetch transaction types.';
      // Service might provide fallback, so UI might still work.
    } finally {
      isLoadingTypes.value = false;
    }
  }

  function clearError() { // General error clear, can be more specific if needed
    error.value = null;
  }

  return {
    transactions, selectedTransaction, transactionTypes,
    isLoadingList, isLoadingDetails, isLoadingTypes, error,
    currentPage, itemsPerPage, totalItems, totalPages,
    getTransactionList, getSelectedTransaction, getTransactionTypes, getPagination,
    fetchTransactions, fetchTransactionDetails, fetchTransactionTypes,
    clearError,
  };
});
```
