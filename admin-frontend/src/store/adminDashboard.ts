import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import adminDashboardService from '@/services/adminDashboardService';
import type { AdminDashboardData } from '@/types/adminDashboard';

export const useAdminDashboardStore = defineStore('adminDashboard', () => {
  // State
  const dashboardData = ref<AdminDashboardData | null>(null);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);

  // Getters
  const getDashboardData = computed(() => dashboardData.value);
  const isLoadingData = computed(() => isLoading.value);
  const getError = computed(() => error.value);

  // Actions
  async function fetchDashboardData() {
    isLoading.value = true;
    error.value = null;
    try {
      const data = await adminDashboardService.fetchAdminDashboardData();
      dashboardData.value = data;
    } catch (err: any) {
      if (err.response && err.response.data && err.response.data.detail) {
        error.value = err.response.data.detail;
      } else if (err.message) {
        error.value = err.message;
      } else {
        error.value = 'Failed to fetch dashboard data. Please try again.';
      }
      console.error('Error in fetchDashboardData store action:', err);
      dashboardData.value = null; // Clear data on error
    } finally {
      isLoading.value = false;
    }
  }

  return {
    dashboardData,
    isLoading,
    error,
    getDashboardData,
    isLoadingData,
    getError,
    fetchDashboardData,
  };
});
```
