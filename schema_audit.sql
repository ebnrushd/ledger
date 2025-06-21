-- Audit Log Table for non-transactional changes

CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    user_id INT, -- Nullable if action can be system-generated or user not always available
    action_type VARCHAR(100) NOT NULL, -- e.g., 'CUSTOMER_UPDATE', 'ACCOUNT_STATUS_CHANGE'
    target_entity VARCHAR(100) NOT NULL, -- e.g., 'customers', 'accounts'
    target_id VARCHAR(255) NOT NULL, -- Can be INT or VARCHAR depending on the target table's PK type
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details_json JSONB, -- Stores a JSON object of what changed, e.g., {"old_values": {...}, "new_values": {...}}
    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(user_id) -- Assumes a 'users' table will exist (defined in auth_schema.sql)
        ON DELETE SET NULL -- Keep audit log even if user is deleted, but nullify user_id
);

CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action_type ON audit_log(action_type);
CREATE INDEX idx_audit_log_target_entity_target_id ON audit_log(target_entity, target_id);
