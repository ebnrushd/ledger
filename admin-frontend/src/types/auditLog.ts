// Types for Admin Panel Audit Log Viewer

export interface AuditLogEntry {
  log_id: number;
  timestamp: string; // ISO date string
  user_id?: number | null;
  user_username?: string | null; // Joined from users table by backend service
  action_type: string;
  target_entity?: string | null;
  target_id?: string | null; // Can be string or number, but API sends as string from target_id VARCHAR
  details_json?: Record<string, any> | string | null; // Parsed JSON or string
}

export interface PaginatedAuditLogsResponse {
  audit_logs: AuditLogEntry[]; // Changed from items for consistency with backend model if it uses "audit_logs"
  total_items: number;
  total_pages: number;
  page: number;
  per_page: number;
}

export interface AuditLogFilters {
  user_id_filter?: number | null;
  action_type_filter?: string | null;
  target_entity_filter?: string | null;
  target_id_filter?: string | null;
  start_date_filter?: string | null; // YYYY-MM-DD
  end_date_filter?: string | null;   // YYYY-MM-DD
}
```
