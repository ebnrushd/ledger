import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import adminAuditLogService from '@/services/adminAuditLogService';
import type { AuditLogEntry, PaginatedAuditLogsResponse, AuditLogFilters } from '@/types/auditLog';

export const useAdminAuditLogsStore = defineStore('adminAuditLogs', () => {
  // State
  const auditLogs = ref<AuditLogEntry[]>([]);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);

  // Pagination state
  const currentPage = ref<number>(1);
  const itemsPerPage = ref<number>(15); // Default items per page for logs
  const totalItems = ref<number>(0);
  const totalPages = ref<number>(1);

  // Getters
  const getAuditLogList = computed(() => auditLogs.value);
  const isLoadingLogs = computed(() => isLoading.value); // Specific getter name
  const getError = computed(() => error.value);
  const getPaginationDetails = computed(() => ({
    currentPage: currentPage.value,
    itemsPerPage: itemsPerPage.value,
    totalItems: totalItems.value,
    totalPages: totalPages.value,
  }));

  // Actions
  async function fetchAuditLogs(page: number = 1, limit: number = itemsPerPage.value, filters: AuditLogFilters = {}) {
    isLoading.value = true;
    error.value = null;
    try {
      const response: PaginatedAuditLogsResponse = await adminAuditLogService.fetchAdminAuditLogs(page, limit, filters);
      auditLogs.value = response.audit_logs; // Key in response is "audit_logs"
      currentPage.value = response.page;
      itemsPerPage.value = response.per_page;
      totalItems.value = response.total_items;
      totalPages.value = response.total_pages;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch audit logs.';
      auditLogs.value = []; // Clear on error
    } finally {
      isLoading.value = false;
    }
  }

  function clearError() {
    error.value = null;
  }

  // Action to parse details_json if it's a string
  // This might be better handled in the component or as a utility function
  // function getParsedDetails(logEntry: AuditLogEntry): Record<string, any> | string {
  //   if (typeof logEntry.details_json === 'string') {
  //     try {
  //       return JSON.parse(logEntry.details_json);
  //     } catch (e) {
  //       return "Invalid JSON string";
  //     }
  //   }
  //   return logEntry.details_json || {};
  // }

  return {
    auditLogs, isLoading, error,
    currentPage, itemsPerPage, totalItems, totalPages,
    getAuditLogList, isLoadingLogs, getError, getPaginationDetails,
    fetchAuditLogs, clearError,
    // getParsedDetails, // If adding helper
  };
});
```
