import apiClient from './apiClient';
import type { Account } from '@customer/types/account'; // Import the Account interface

const fetchUserAccounts = async (): Promise<Account[]> => {
  try {
    // The backend endpoint /api/v1/accounts (GET) returns a List[AccountDetails]
    // which should match Account[] here.
    const response = await apiClient.get<Account[]>('/accounts/');
    return response.data;
  } catch (error) {
    // The error will be handled by the Axios interceptor for generic errors (like 401)
    // or by the calling action in the store for specific handling.
    console.error('Error fetching user accounts:', error);
    throw error; // Re-throw to be caught by the store action
  }
};

const accountService = {
  fetchUserAccounts,
  fetchAccountDetails: async (accountId: string | number): Promise<Account> => {
    try {
      const response = await apiClient.get<Account>(`/accounts/${accountId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching details for account ${accountId}:`, error);
      throw error;
    }
  }
};

export default accountService;
```
