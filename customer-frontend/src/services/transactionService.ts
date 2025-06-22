import apiClient from './apiClient';
import type { PaginatedTransactionsResponse, TransactionFilters } from '@/types/transaction';

const fetchAccountTransactions = async (
  accountId: string | number,
  page: number = 1,
  limit: number = 10,
  filters: TransactionFilters = {}
): Promise<PaginatedTransactionsResponse> => {
  try {
    const params = new URLSearchParams({
      page: String(page),
      limit: String(limit),
    });

    // Add filters to params if they exist
    if (filters.date_from) {
      params.append('date_from', filters.date_from);
    }
    if (filters.date_to) {
      params.append('date_to', filters.date_to);
    }
    if (filters.type) {
      params.append('type', filters.type);
    }
    // Add other filters as needed

    const response = await apiClient.get<PaginatedTransactionsResponse>(
      `/accounts/${accountId}/transactions`,
      { params }
    );
    // Assuming the backend returns data directly matching PaginatedTransactionsResponse
    // If it's nested, e.g., response.data.data, adjust here.
    return response.data;
  } catch (error) {
    console.error(`Error fetching transactions for account ${accountId}:`, error);
    throw error; // Re-throw to be caught by the store action
  }
};

const transactionService = {
  fetchAccountTransactions,
  transferFunds: async (transferData: {
    from_account_id: string | number;
    to_account_id: string | number;
    amount: number;
    description?: string
  }): Promise<any> => { // Replace 'any' with a more specific response type if backend provides one for transfer
    try {
      // The backend endpoint /api/v1/transactions/transfer expects a JSON body
      // matching TransferRequest Pydantic model.
      const response = await apiClient.post('/transactions/transfer', transferData);
      return response.data; // Backend returns TransferResponse with debit and credit transaction details
    } catch (error) {
      console.error('Error performing transfer:', error);
      throw error; // Re-throw for store action to handle
    }
  }
};

export default transactionService;
```
