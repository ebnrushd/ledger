import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import adminCustomerService from '@admin/services/adminCustomerService';
import type { AdminCustomerListItem, AdminCustomerDetails, PaginatedAdminCustomersResponse } from '@admin/types/customer';

export const useAdminCustomersStore = defineStore('adminCustomers', () => {
  // State
  const customers = ref<AdminCustomerListItem[]>([]);
  const selectedCustomer = ref<AdminCustomerDetails | null>(null);

  const isLoadingCustomers = ref<boolean>(false);
  const isLoadingDetails = ref<boolean>(false);
  const error = ref<string | null>(null); // General error for the store

  // Pagination state for customer list
  const currentPage = ref<number>(1);
  const itemsPerPage = ref<number>(10);
  const totalItems = ref<number>(0);
  const totalPages = ref<number>(1);

  // Getters
  const getCustomerList = computed(() => customers.value);
  const getSelectedCustomerDetails = computed(() => selectedCustomer.value);
  const getPaginationDetails = computed(() => ({
    currentPage: currentPage.value,
    itemsPerPage: itemsPerPage.value,
    totalItems: totalItems.value,
    totalPages: totalPages.value,
  }));

  // Actions
  async function fetchCustomers(page: number = 1, limit: number = itemsPerPage.value, filters: any = {}) {
    isLoadingCustomers.value = true;
    error.value = null;
    try {
      const response: PaginatedAdminCustomersResponse = await adminCustomerService.fetchAdminCustomers(page, limit, filters);
      customers.value = response.customers; // Assuming 'customers' is the key for items
      currentPage.value = response.page;
      itemsPerPage.value = response.per_page; // Assuming backend returns 'per_page'
      totalItems.value = response.total_items;
      totalPages.value = response.total_pages;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch customers.';
      customers.value = []; // Clear on error
    } finally {
      isLoadingCustomers.value = false;
    }
  }

  async function fetchCustomerDetails(customerId: string | number) {
    isLoadingDetails.value = true;
    error.value = null; // Clear general error, or use a specific error for details
    selectedCustomer.value = null; // Clear previous selection
    try {
      const customerData = await adminCustomerService.fetchAdminCustomerDetailsById(customerId);
      selectedCustomer.value = customerData;
      return customerData;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || `Failed to fetch customer details for ID ${customerId}.`;
      throw err; // Re-throw for component to handle if needed
    } finally {
      isLoadingDetails.value = false;
    }
  }

  function clearError() {
    error.value = null;
  }

  return {
    customers, selectedCustomer,
    isLoadingCustomers, isLoadingDetails, error,
    currentPage, itemsPerPage, totalItems, totalPages,
    getCustomerList, getSelectedCustomerDetails, getPaginationDetails,
    fetchCustomers, fetchCustomerDetails,
    clearError,
  };
});
```
