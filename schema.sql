-- Database schema for Slackbot application
-- This file contains the complete database schema with tables, indexes, and constraints

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS query_cache CASCADE;
DROP TABLE IF EXISTS query_history CASCADE;
DROP TABLE IF EXISTS user_mappings CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;

-- User Sessions Table
-- Tracks active user sessions and maintains context between interactions
CREATE TABLE user_sessions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    slack_user_id VARCHAR(50) NOT NULL,
    slack_channel_id VARCHAR(50) NOT NULL,
    slack_team_id VARCHAR(50) NOT NULL,
    
    -- Session context and state
    session_context JSONB DEFAULT '{}',
    current_database VARCHAR(100),
    current_schema VARCHAR(100),
    current_warehouse VARCHAR(100),
    
    -- Session metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    
    -- User preferences
    preferences JSONB DEFAULT '{}'
);

-- User Sessions Indexes
CREATE INDEX idx_user_sessions_slack_user ON user_sessions(slack_user_id);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active, last_activity);
CREATE INDEX idx_user_sessions_team_user ON user_sessions(slack_team_id, slack_user_id);
CREATE INDEX idx_user_sessions_channel ON user_sessions(slack_channel_id);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at) WHERE expires_at IS NOT NULL;

-- User Sessions Triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_sessions_updated_at 
    BEFORE UPDATE ON user_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Query History Table
-- Stores all executed queries, their results, and execution metadata
CREATE TABLE query_history (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    session_id VARCHAR NOT NULL REFERENCES user_sessions(id) ON DELETE CASCADE,
    
    -- Query details
    original_question TEXT NOT NULL,
    generated_query TEXT NOT NULL,
    query_type VARCHAR(50) DEFAULT 'SELECT',
    
    -- Execution details
    database_name VARCHAR(100),
    schema_name VARCHAR(100),
    warehouse VARCHAR(100),
    execution_time_ms INTEGER,
    row_count INTEGER,
    
    -- Results and metadata
    query_result JSONB,
    query_metadata JSONB,
    snowflake_query_id VARCHAR(100),
    snowflake_query_link TEXT,
    
    -- Status and error handling
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- User feedback
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT
);

-- Query History Indexes
CREATE INDEX idx_query_history_session ON query_history(session_id);
CREATE INDEX idx_query_history_status ON query_history(status);
CREATE INDEX idx_query_history_created ON query_history(created_at);
CREATE INDEX idx_query_history_snowflake_id ON query_history(snowflake_query_id);
CREATE INDEX idx_query_history_database ON query_history(database_name);
CREATE INDEX idx_query_history_execution_time ON query_history(execution_time_ms);
CREATE INDEX idx_query_history_rating ON query_history(user_rating) WHERE user_rating IS NOT NULL;

-- User Mappings Table
-- Maps Slack users to database users and manages permissions
CREATE TABLE user_mappings (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    slack_user_id VARCHAR(50) NOT NULL UNIQUE,
    slack_team_id VARCHAR(50) NOT NULL,
    
    -- User identity
    slack_username VARCHAR(100),
    slack_display_name VARCHAR(100),
    slack_email VARCHAR(255),
    
    -- Database credentials and permissions
    snowflake_username VARCHAR(100),
    snowflake_role VARCHAR(100),
    default_warehouse VARCHAR(100),
    default_database VARCHAR(100),
    default_schema VARCHAR(100),
    
    -- Access control
    allowed_databases JSONB DEFAULT '[]',
    allowed_warehouses JSONB DEFAULT '[]',
    query_limits JSONB DEFAULT '{}',
    
    -- User status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- User Mappings Indexes
CREATE INDEX idx_user_mappings_slack_user ON user_mappings(slack_user_id);
CREATE INDEX idx_user_mappings_email ON user_mappings(slack_email);
CREATE INDEX idx_user_mappings_active ON user_mappings(is_active);
CREATE INDEX idx_user_mappings_team ON user_mappings(slack_team_id);
CREATE INDEX idx_user_mappings_snowflake_user ON user_mappings(snowflake_username);

-- User Mappings Triggers
CREATE TRIGGER update_user_mappings_updated_at 
    BEFORE UPDATE ON user_mappings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Query Cache Table
-- Caches frequently used queries and their results for performance
CREATE TABLE query_cache (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    
    -- Cache key components
    query_hash VARCHAR(64) NOT NULL UNIQUE,
    original_query TEXT NOT NULL,
    normalized_query TEXT NOT NULL,
    
    -- Context
    database_name VARCHAR(100),
    schema_name VARCHAR(100),
    warehouse VARCHAR(100),
    
    -- Cached results
    result_data JSONB NOT NULL,
    result_metadata JSONB DEFAULT '{}',
    row_count INTEGER,
    execution_time_ms INTEGER,
    
    -- Cache management
    hit_count INTEGER NOT NULL DEFAULT 0,
    last_hit TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    
    -- Cache validation
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,
    invalidated_at TIMESTAMPTZ,
    invalidation_reason VARCHAR(255)
);

-- Query Cache Indexes
CREATE INDEX idx_query_cache_hash ON query_cache(query_hash);
CREATE INDEX idx_query_cache_expires ON query_cache(expires_at);
CREATE INDEX idx_query_cache_valid ON query_cache(is_valid, expires_at);
CREATE INDEX idx_query_cache_hits ON query_cache(hit_count);
CREATE INDEX idx_query_cache_database ON query_cache(database_name);
CREATE INDEX idx_query_cache_created ON query_cache(created_at);

-- Audit Logs Table
-- Comprehensive logging of all system activities and security events
CREATE TABLE audit_logs (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    
    -- Event identification
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(30) NOT NULL,
    event_severity VARCHAR(20) NOT NULL DEFAULT 'info',
    
    -- User and session context
    slack_user_id VARCHAR(50),
    slack_team_id VARCHAR(50),
    session_id VARCHAR,
    
    -- Event details
    event_description TEXT NOT NULL,
    event_data JSONB DEFAULT '{}',
    
    -- Request context
    slack_channel_id VARCHAR(50),
    slack_message_ts VARCHAR(50),
    user_agent VARCHAR(255),
    ip_address INET,
    
    -- Database context
    database_name VARCHAR(100),
    schema_name VARCHAR(100),
    warehouse VARCHAR(100),
    
    -- Performance metrics
    execution_time_ms INTEGER,
    memory_usage_mb INTEGER,
    
    -- Error details
    error_code VARCHAR(50),
    error_message TEXT,
    stack_trace TEXT,
    
    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audit Logs Indexes
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_category ON audit_logs(event_category);
CREATE INDEX idx_audit_logs_severity ON audit_logs(event_severity);
CREATE INDEX idx_audit_logs_user ON audit_logs(slack_user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_session ON audit_logs(session_id);
CREATE INDEX idx_audit_logs_team ON audit_logs(slack_team_id);
CREATE INDEX idx_audit_logs_channel ON audit_logs(slack_channel_id);

-- Composite indexes for common query patterns
CREATE INDEX idx_audit_logs_user_type_date ON audit_logs(slack_user_id, event_type, created_at);
CREATE INDEX idx_audit_logs_category_severity_date ON audit_logs(event_category, event_severity, created_at);

-- Additional constraints and checks
ALTER TABLE query_history ADD CONSTRAINT chk_query_history_status 
    CHECK (status IN ('pending', 'running', 'success', 'error', 'timeout', 'cancelled'));

ALTER TABLE audit_logs ADD CONSTRAINT chk_audit_logs_severity 
    CHECK (event_severity IN ('debug', 'info', 'warning', 'error', 'critical'));

ALTER TABLE audit_logs ADD CONSTRAINT chk_audit_logs_category 
    CHECK (event_category IN ('security', 'query', 'system', 'user', 'performance', 'error'));

-- Views for common queries
-- Active sessions view
CREATE VIEW active_sessions AS
SELECT 
    us.*,
    um.slack_username,
    um.snowflake_username,
    COUNT(qh.id) as query_count,
    MAX(qh.created_at) as last_query_time
FROM user_sessions us
LEFT JOIN user_mappings um ON us.slack_user_id = um.slack_user_id
LEFT JOIN query_history qh ON us.id = qh.session_id
WHERE us.is_active = TRUE
GROUP BY us.id, um.slack_username, um.snowflake_username;

-- Query performance metrics view
CREATE VIEW query_performance_metrics AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as total_queries,
    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_queries,
    COUNT(CASE WHEN status = 'error' THEN 1 END) as failed_queries,
    AVG(execution_time_ms) as avg_execution_time,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time_ms) as median_execution_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_execution_time,
    AVG(row_count) as avg_row_count
FROM query_history 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;

-- User activity summary view
CREATE VIEW user_activity_summary AS
SELECT 
    um.slack_user_id,
    um.slack_username,
    um.slack_display_name,
    COUNT(DISTINCT us.id) as total_sessions,
    COUNT(qh.id) as total_queries,
    COUNT(CASE WHEN qh.status = 'success' THEN 1 END) as successful_queries,
    AVG(qh.execution_time_ms) as avg_query_time,
    MAX(us.last_activity) as last_activity,
    MAX(qh.created_at) as last_query_time
FROM user_mappings um
LEFT JOIN user_sessions us ON um.slack_user_id = us.slack_user_id
LEFT JOIN query_history qh ON us.id = qh.session_id
WHERE um.is_active = TRUE
GROUP BY um.slack_user_id, um.slack_username, um.slack_display_name
ORDER BY last_activity DESC;

-- Cache efficiency view
CREATE VIEW cache_efficiency AS
SELECT 
    DATE_TRUNC('day', created_at) as day,
    COUNT(*) as total_cache_entries,
    SUM(hit_count) as total_hits,
    AVG(hit_count) as avg_hits_per_entry,
    COUNT(CASE WHEN is_valid = TRUE AND expires_at > NOW() THEN 1 END) as valid_entries,
    COUNT(CASE WHEN expires_at <= NOW() THEN 1 END) as expired_entries
FROM query_cache
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY day DESC;

-- Functions for maintenance tasks
-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions(hours_threshold INTEGER DEFAULT 24)
RETURNS INTEGER AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE user_sessions 
    SET is_active = FALSE, updated_at = NOW()
    WHERE is_active = TRUE 
    AND last_activity < NOW() - INTERVAL '1 hour' * hours_threshold;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    INSERT INTO audit_logs (
        event_type, event_category, event_description, event_data
    ) VALUES (
        'session_cleanup', 'system', 
        'Cleaned up expired sessions',
        jsonb_build_object('rows_affected', rows_affected, 'hours_threshold', hours_threshold)
    );
    
    RETURN rows_affected;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    DELETE FROM query_cache 
    WHERE expires_at <= NOW() OR is_valid = FALSE;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    INSERT INTO audit_logs (
        event_type, event_category, event_description, event_data
    ) VALUES (
        'cache_cleanup', 'system', 
        'Cleaned up expired cache entries',
        jsonb_build_object('rows_affected', rows_affected)
    );
    
    RETURN rows_affected;
END;
$$ LANGUAGE plpgsql;

-- Function to archive old audit logs
CREATE OR REPLACE FUNCTION archive_old_audit_logs(days_threshold INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    -- In a production environment, you might want to move these to an archive table
    -- instead of deleting them
    DELETE FROM audit_logs 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_threshold
    AND event_severity NOT IN ('error', 'critical');
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    INSERT INTO audit_logs (
        event_type, event_category, event_description, event_data
    ) VALUES (
        'audit_log_archive', 'system', 
        'Archived old audit logs',
        jsonb_build_object('rows_affected', rows_affected, 'days_threshold', days_threshold)
    );
    
    RETURN rows_affected;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job functions (requires pg_cron extension)
-- Uncomment these if you have pg_cron installed and want automated cleanup

/*
-- Schedule daily cleanup of expired sessions (runs at 2 AM daily)
SELECT cron.schedule('cleanup-expired-sessions', '0 2 * * *', 'SELECT cleanup_expired_sessions(24);');

-- Schedule hourly cleanup of expired cache (runs every hour at minute 30)
SELECT cron.schedule('cleanup-expired-cache', '30 * * * *', 'SELECT cleanup_expired_cache();');

-- Schedule weekly archival of old audit logs (runs Sundays at 3 AM)
SELECT cron.schedule('archive-audit-logs', '0 3 * * 0', 'SELECT archive_old_audit_logs(90);');
*/

-- Insert initial admin user (modify as needed)
INSERT INTO user_mappings (
    slack_user_id, slack_team_id, slack_username, slack_display_name,
    snowflake_username, is_admin, is_active,
    default_warehouse, default_database, default_schema
) VALUES (
    'U_ADMIN_USER', 'T_ADMIN_TEAM', 'admin', 'Admin User',
    'ADMIN_SNOWFLAKE_USER', TRUE, TRUE,
    'COMPUTE_WH', 'ANALYTICS', 'PUBLIC'
) ON CONFLICT (slack_user_id) DO NOTHING;

-- Log the schema creation
INSERT INTO audit_logs (
    event_type, event_category, event_severity, event_description, event_data
) VALUES (
    'schema_created', 'system', 'info', 
    'Database schema created successfully',
    jsonb_build_object(
        'version', '1.0.0',
        'created_at', NOW(),
        'tables_created', ARRAY['user_sessions', 'query_history', 'user_mappings', 'query_cache', 'audit_logs']
    )
);

-- Display completion message
DO $$
BEGIN
    RAISE NOTICE 'Slackbot database schema created successfully!';
    RAISE NOTICE 'Tables created: user_sessions, query_history, user_mappings, query_cache, audit_logs';
    RAISE NOTICE 'Views created: active_sessions, query_performance_metrics, user_activity_summary, cache_efficiency';
    RAISE NOTICE 'Functions created: cleanup_expired_sessions, cleanup_expired_cache, archive_old_audit_logs';
END $$;
