import adminApiClient from './adminApiClient';
import type {
  AuditLogEntry,
  PaginatedAuditLogsResponse,
  AuditLogFilters
} from '@/types/auditLog';

const fetchAdminAuditLogs = async (
  page: number = 1,
  limit: number = 15, // Default to 15 per page for logs, can be adjusted
  filters: AuditLogFilters = {}
): Promise<PaginatedAuditLogsResponse> => {
  try {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(limit),
    });

    if (filters.user_id_filter !== null && filters.user_id_filter !== undefined) {
      params.append('user_id_filter', String(filters.user_id_filter));
    }
    if (filters.action_type_filter) {
      params.append('action_type_filter', filters.action_type_filter);
    }
    if (filters.target_entity_filter) {
      params.append('target_entity_filter', filters.target_entity_filter);
    }
    if (filters.target_id_filter) {
      params.append('target_id_filter', filters.target_id_filter);
    }
    if (filters.start_date_filter) {
      params.append('start_date_filter', filters.start_date_filter);
    }
    if (filters.end_date_filter) {
      params.append('end_date_filter', filters.end_date_filter);
    }

    // Endpoint: /api/admin/audit_logs (from api_admin/audit.py)
    const response = await adminApiClient.get<PaginatedAuditLogsResponse>('/api/admin/audit_logs/', { params });
    // Assumes backend response matches PaginatedAuditLogsResponse structure,
    // especially the key for the list of logs (e.g., "audit_logs").
    // The Pydantic model AdminAuditLogListResponse uses "audit_logs".
    return response.data;
  } catch (error) {
    console.error('Error fetching admin audit logs:', error);
    throw error;
  }
};

const adminAuditLogService = {
  fetchAdminAuditLogs,
};

export default adminAuditLogService;
```
