<template>
  <div class="audit-log-list-view p-4 md:p-6 lg:p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl md:text-3xl font-semibold text-gray-800">System Audit Logs</h1>
    </div>

    <!-- Filters -->
    <div class="bg-white p-4 rounded-lg shadow-md mb-6">
      <form @submit.prevent="applyFiltersAndSearch" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 items-end">
        <div>
          <label for="userIdFilter" class="block text-sm font-medium text-gray-700">User ID:</label>
          <input type="number" id="userIdFilter" v-model.number="filterState.userIdFilter"
                 class="filter-input" placeholder="e.g., 123">
        </div>
        <div>
          <label for="actionTypeFilter" class="block text-sm font-medium text-gray-700">Action Type:</label>
          <input type="text" id="actionTypeFilter" v-model="filterState.actionTypeFilter"
                 class="filter-input" placeholder="e.g., USER_CREATED">
        </div>
        <div>
          <label for="targetEntityFilter" class="block text-sm font-medium text-gray-700">Target Entity:</label>
          <input type="text" id="targetEntityFilter" v-model="filterState.targetEntityFilter"
                 class="filter-input" placeholder="e.g., accounts">
        </div>
        <div>
          <label for="targetIdFilter" class="block text-sm font-medium text-gray-700">Target ID:</label>
          <input type="text" id="targetIdFilter" v-model="filterState.targetIdFilter"
                 class="filter-input" placeholder="e.g., 456">
        </div>
        <!-- TODO: Date range filters if needed -->
        <div class="col-span-1 sm:col-span-2 md:col-span-3 lg:col-span-1 flex items-end space-x-2">
          <button type="submit"
                  class="w-full sm:w-auto px-4 py-2 bg-admin-primary text-white rounded-md shadow hover:bg-blue-700 transition duration-150">Filter</button>
        </div>
        <div class="col-span-1 sm:col-span-2 md:col-span-3 lg:col-span-1 flex items-end">
          <button type="button" @click="clearAllFilters"
                  class="w-full sm:w-auto px-4 py-2 bg-gray-200 text-gray-700 rounded-md shadow hover:bg-gray-300 transition duration-150">Clear</button>
        </div>
      </form>
    </div>

    <div v-if="auditLogsStore.isLoadingLogs" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-admin-primary mx-auto"></div>
      <p class="mt-3 text-gray-600">Loading audit logs...</p>
    </div>
    <div v-if="auditLogsStore.error && !auditLogsStore.isLoadingLogs"
         class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 mb-6 rounded-md shadow-md" role="alert">
        <p class="font-bold">Error Loading Audit Logs</p>
        <p>{{ auditLogsStore.error }}</p>
    </div>

    <div v-if="!auditLogsStore.isLoadingLogs && !auditLogsStore.error && auditLogsStore.auditLogs" class="bg-white rounded-lg shadow-xl overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-100">
            <tr>
              <th class="table-header">Log ID</th>
              <th class="table-header">Timestamp</th>
              <th class="table-header">User</th>
              <th class="table-header">Action Type</th>
              <th class="table-header">Target Entity</th>
              <th class="table-header">Target ID</th>
              <th class="table-header">Details</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="log in auditLogsStore.auditLogs" :key="log.log_id" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell text-xs">{{ log.log_id }}</td>
              <td class="table-cell text-xs">{{ new Date(log.timestamp).toLocaleString() }}</td>
              <td class="table-cell text-xs">
                <router-link v-if="log.user_id && log.user_username" :to="{ name: 'AdminUserDetail', params: { userId: log.user_id } }" class="text-admin-primary hover:underline">
                    {{ log.user_username }} ({{ log.user_id }})
                </router-link>
                <span v-else-if="log.user_id">{{ log.user_id }}</span>
                <span v-else class="italic text-gray-500">System</span>
              </td>
              <td class="table-cell text-xs font-medium text-gray-800">{{ log.action_type }}</td>
              <td class="table-cell text-xs">{{ log.target_entity || 'N/A' }}</td>
              <td class="table-cell text-xs">
                <!-- Basic linking for known entities -->
                <router-link v-if="log.target_entity === 'accounts' && log.target_id" :to="{ name: 'AdminAccountDetail', params: { accountId: log.target_id } }" class="text-admin-primary hover:underline">{{ log.target_id }}</router-link>
                <router-link v-else-if="log.target_entity === 'customers' && log.target_id" :to="{ name: 'AdminCustomerDetail', params: { customerId: log.target_id } }" class="text-admin-primary hover:underline">{{ log.target_id }}</router-link>
                <router-link v-else-if="log.target_entity === 'users' && log.target_id" :to="{ name: 'AdminUserDetail', params: { userId: log.target_id } }" class="text-admin-primary hover:underline">{{ log.target_id }}</router-link>
                <span v-else>{{ log.target_id || 'N/A' }}</span>
              </td>
              <td class="table-cell text-xs">
                <pre class="max-h-20 overflow-y-auto bg-gray-50 p-1 rounded text-xs whitespace-pre-wrap break-all">{{ JSON.stringify(log.details_json, null, 2) || '{}' }}</pre>
              </td>
            </tr>
            <tr v-if="auditLogsStore.auditLogs.length === 0">
                <td colspan="7" class="text-center text-gray-500 py-6">No audit logs found matching your criteria.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Pagination -->
      <div v-if="auditLogsStore.totalPages > 1" class="py-4 px-4 flex justify-between items-center text-sm text-gray-600 bg-gray-50 border-t">
        <button @click="changePage(auditLogsStore.currentPage - 1)" :disabled="auditLogsStore.currentPage <= 1"
                class="btn-admin-secondary-outline">Previous</button>
        <span>Page {{ auditLogsStore.currentPage }} of {{ auditLogsStore.totalPages }} (Total: {{ auditLogsStore.totalItems }} logs)</span>
        <button @click="changePage(auditLogsStore.currentPage + 1)" :disabled="auditLogsStore.currentPage >= auditLogsStore.totalPages"
                class="btn-admin-secondary-outline">Next</button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, reactive, watch, ref } from 'vue';
import { useAdminAuditLogsStore } from '@admin/store/adminAuditLogs';
import { useRouter, useRoute } from 'vue-router';
import type { AuditLogFilters } from '@admin/types/auditLog';

export default defineComponent({
  name: 'AuditLogListView',
  setup() {
    const auditLogsStore = useAdminAuditLogsStore();
    const router = useRouter();
    const route = useRoute();

    const filterState = reactive<AuditLogFilters>({
        userIdFilter: route.query.user_id_filter ? Number(route.query.user_id_filter) : null,
        actionTypeFilter: (route.query.action_type_filter as string) || '',
        targetEntityFilter: (route.query.target_entity_filter as string) || '',
        targetIdFilter: (route.query.target_id_filter as string) || '',
        startDateFilter: (route.query.start_date_filter as string) || '',
        endDateFilter: (route.query.end_date_filter as string) || '',
    });
    // Store currentPage separately for pagination controls that don't submit the whole form
    const currentPageRef = ref(Number(route.query.page) || 1);


    const fetchLogList = (page = currentPageRef.value) => {
      currentPageRef.value = page;
      const filters: AuditLogFilters = {
          user_id_filter: filterState.userIdFilter || undefined, // Send undefined if null/empty
          action_type_filter: filterState.actionTypeFilter || undefined,
          target_entity_filter: filterState.targetEntityFilter || undefined,
          target_id_filter: filterState.targetIdFilter || undefined,
          start_date_filter: filterState.startDateFilter || undefined,
          end_date_filter: filterState.endDateFilter || undefined,
      };
      auditLogsStore.fetchAuditLogs(page, auditLogsStore.itemsPerPage, filters);
    };

    const applyFiltersAndSearch = () => {
        // Update query params to make filters bookmarkable before fetching
        const query: any = { page: '1' };
        if (filterState.userIdFilter) query.user_id_filter = String(filterState.userIdFilter);
        if (filterState.actionTypeFilter) query.action_type_filter = filterState.actionTypeFilter;
        if (filterState.targetEntityFilter) query.target_entity_filter = filterState.targetEntityFilter;
        if (filterState.targetIdFilter) query.target_id_filter = filterState.targetIdFilter;
        if (filterState.startDateFilter) query.start_date_filter = filterState.startDateFilter;
        if (filterState.endDateFilter) query.end_date_filter = filterState.endDateFilter;
        router.push({ query });
        // Watcher on route.query will trigger fetchLogList
    };

    const clearAllFilters = () => {
        filterState.userIdFilter = null;
        filterState.actionTypeFilter = '';
        filterState.targetEntityFilter = '';
        filterState.targetIdFilter = '';
        filterState.startDateFilter = '';
        filterState.endDateFilter = '';
        router.push({ query: {} });
    };

    const changePage = (newPage: number) => {
        if (newPage > 0 && newPage <= auditLogsStore.totalPages) {
            currentPageRef.value = newPage; // Update local ref for pagination controls
            // Update only the page query parameter, keeping other filters
            const newQuery = { ...route.query, page: String(newPage) };
            if (!filterState.userIdFilter) delete newQuery.user_id_filter; // Clean up empty params
            // ... (similar for other filters if they are empty in filterState)
            router.push({ query: newQuery });
        }
    };

    watch(() => route.query, (newQuery) => {
        filterState.userIdFilter = newQuery.user_id_filter ? Number(newQuery.user_id_filter) : null;
        filterState.actionTypeFilter = (newQuery.action_type_filter as string) || '';
        filterState.targetEntityFilter = (newQuery.target_entity_filter as string) || '';
        filterState.targetIdFilter = (newQuery.target_id_filter as string) || '';
        filterState.startDateFilter = (newQuery.start_date_filter as string) || '';
        filterState.endDateFilter = (newQuery.end_date_filter as string) || '';
        currentPageRef.value = Number(newQuery.page) || 1;
        fetchLogList(currentPageRef.value);
    }, { deep: true, immediate: false }); // Not immediate, onMounted handles initial

    onMounted(() => {
        auditLogsStore.clearError();
        // Set initial filterState from route.query before first fetch
        filterState.userIdFilter = route.query.user_id_filter ? Number(route.query.user_id_filter) : null;
        filterState.actionTypeFilter = (route.query.action_type_filter as string) || '';
        filterState.targetEntityFilter = (route.query.target_entity_filter as string) || '';
        filterState.targetIdFilter = (route.query.target_id_filter as string) || '';
        filterState.startDateFilter = (route.query.start_date_filter as string) || '';
        filterState.endDateFilter = (route.query.end_date_filter as string) || '';
        currentPageRef.value = Number(route.query.page) || 1;
        fetchLogList();
    });

    return {
      auditLogsStore,
      filterState,
      applyFiltersAndSearch,
      clearAllFilters,
      changePage,
    };
  },
});
</script>

<style scoped>
.table-header { @apply px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-100; }
.table-cell { @apply px-3 py-2 whitespace-nowrap text-sm text-gray-700; }
.filter-input { @apply mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm; }

.btn-admin-primary, .btn-admin-secondary-outline, .btn-admin-secondary {
  @apply py-2 px-4 font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-primary { @apply bg-admin-primary text-white hover:bg-blue-700 focus:ring-blue-500; }
.btn-admin-secondary-outline { @apply bg-white text-gray-600 border border-gray-300 hover:bg-gray-50 focus:ring-admin-primary; }
.btn-admin-secondary { @apply bg-gray-200 text-gray-700 hover:bg-gray-300 focus:ring-gray-400; }

pre {
  font-size: 0.75rem; /* Smaller font for JSON details */
}
</style>
```
