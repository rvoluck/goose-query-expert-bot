-- Migration: Add Performance Indexes
-- Version: 002
-- Description: Add additional indexes for better query performance
-- Dependencies: 001
-- Created: 2024-01-15T11:00:00Z

-- UP: Apply migration

-- Add composite indexes for common query patterns
CREATE INDEX idx_query_history_user_success ON query_history(user_id, success, created_at DESC);
CREATE INDEX idx_query_history_channel_recent ON query_history(channel_id, created_at DESC) WHERE success = true;
CREATE INDEX idx_user_sessions_active_recent ON user_sessions(is_active, last_activity DESC) WHERE is_active = true;

-- Add indexes for audit log analysis
CREATE INDEX idx_audit_logs_user_event_time ON audit_logs(user_id, event_type, created_at DESC);
CREATE INDEX idx_audit_logs_result_time ON audit_logs(result, created_at DESC);

-- Add partial indexes for active records
CREATE INDEX idx_user_mappings_active ON user_mappings(slack_user_id, internal_user_id) WHERE is_active = true;

-- Add index for cache cleanup
CREATE INDEX idx_query_cache_cleanup ON query_cache(expires_at) WHERE expires_at IS NOT NULL;

-- Add trigram indexes for better text search
CREATE INDEX idx_query_history_question_trgm ON query_history USING gin(original_question gin_trgm_ops);
CREATE INDEX idx_user_mappings_name_trgm ON user_mappings USING gin(full_name gin_trgm_ops);

-- Add index for JSON queries on user roles and permissions
CREATE INDEX idx_user_mappings_roles_gin ON user_mappings USING gin(roles);
CREATE INDEX idx_user_mappings_permissions_gin ON user_mappings USING gin(permissions);

-- Add index for session context queries
CREATE INDEX idx_user_sessions_context_gin ON user_sessions USING gin(context);

-- DOWN: Rollback migration

-- Drop all indexes added in this migration
DROP INDEX IF EXISTS idx_user_sessions_context_gin;
DROP INDEX IF EXISTS idx_user_mappings_permissions_gin;
DROP INDEX IF EXISTS idx_user_mappings_roles_gin;
DROP INDEX IF EXISTS idx_user_mappings_name_trgm;
DROP INDEX IF EXISTS idx_query_history_question_trgm;
DROP INDEX IF EXISTS idx_query_cache_cleanup;
DROP INDEX IF EXISTS idx_user_mappings_active;
DROP INDEX IF EXISTS idx_audit_logs_result_time;
DROP INDEX IF EXISTS idx_audit_logs_user_event_time;
DROP INDEX IF EXISTS idx_user_sessions_active_recent;
DROP INDEX IF EXISTS idx_query_history_channel_recent;
DROP INDEX IF EXISTS idx_query_history_user_success;
