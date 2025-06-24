import adminApiClient from './adminApiClient';
import type {
  AdminTransactionListItem,
  AdminTransactionDetail,
  PaginatedAdminTransactionsResponse,
  AdminTransactionFilters
} from '@admin/types/transaction';
import type { TransactionType } from '@admin/types/lookups';

const fetchAdminTransactions = async (
  page: number = 1,
  limit: number = 10,
  filters: AdminTransactionFilters = {}
): Promise<PaginatedAdminTransactionsResponse> => {
  try {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(limit), // Ensure backend API uses 'per_page'
    });

    if (filters.account_id_filter !== null && filters.account_id_filter !== undefined) {
      params.append('account_id_filter', String(filters.account_id_filter));
    }
    if (filters.transaction_type_filter) {
      params.append('transaction_type_filter', filters.transaction_type_filter);
    }
    if (filters.start_date_filter) {
      params.append('start_date_filter', filters.start_date_filter);
    }
    if (filters.end_date_filter) {
      params.append('end_date_filter', filters.end_date_filter);
    }
    // Add other potential filters from AdminTransactionFilters to params here

    // Endpoint: /api/admin/transactions (from api_admin/transactions.py)
    const response = await adminApiClient.get<PaginatedAdminTransactionsResponse>('/api/admin/transactions/', { params });
    // Assumes backend directly returns PaginatedAdminTransactionsResponse structure
    // (e.g. { transactions: [], total_items: ..., ... })
    return response.data;
  } catch (error) {
    console.error('Error fetching admin list of transactions:', error);
    throw error;
  }
};

const fetchAdminTransactionDetailsById = async (transactionId: string | number): Promise<AdminTransactionDetail> => {
  try {
    // Endpoint: /api/admin/transactions/{transactionId}
    const response = await adminApiClient.get<AdminTransactionDetail>(`/api/admin/transactions/${transactionId}/view`); // Path corrected to match router
    return response.data;
  } catch (error) {
    console.error(`Error fetching admin transaction details for ID ${transactionId}:`, error);
    throw error;
  }
};

const fetchAdminTransactionTypes = async (): Promise<TransactionType[]> => {
  try {
    // Endpoint: /api/admin/lookups/transaction-types
    const response = await adminApiClient.get<TransactionType[]>('/api/admin/lookups/transaction-types');
    return response.data;
  } catch (error) {
    console.error('Error fetching admin transaction types:', error);
    // Fallback to a static list if API fails or is not ready, similar to AccountStatusTypes
    console.warn("Failed to fetch transaction types from API, using fallback list.");
    return Promise.resolve([
        { transaction_type_id: 1, type_name: 'deposit' },
        { transaction_type_id: 2, type_name: 'withdrawal' },
        { transaction_type_id: 3, type_name: 'transfer' },
        { transaction_type_id: 4, type_name: 'ach_credit' },
        { transaction_type_id: 5, type_name: 'ach_debit' },
        { transaction_type_id: 6, type_name: 'wire_transfer' },
        // Add more if defined in your schema's default inserts for transaction_types
    ]);
  }
};

const adminTransactionService = {
  fetchAdminTransactions,
  fetchAdminTransactionDetailsById,
  fetchAdminTransactionTypes,
};

export default adminTransactionService;
```
