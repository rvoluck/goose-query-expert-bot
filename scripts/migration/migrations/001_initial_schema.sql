-- Migration: Initial Schema
-- Version: 001
-- Description: Create initial database schema for Goose Slackbot
-- Dependencies: 
-- Created: 2024-01-15T10:00:00Z

-- UP: Apply migration

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- User sessions table
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL,
    slack_user_id VARCHAR(50) NOT NULL,
    channel_id VARCHAR(50) NOT NULL,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Query history table
CREATE TABLE query_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES user_sessions(id),
    user_id VARCHAR(50) NOT NULL,
    slack_user_id VARCHAR(50) NOT NULL,
    channel_id VARCHAR(50) NOT NULL,
    query_id VARCHAR(100) UNIQUE NOT NULL,
    original_question TEXT NOT NULL,
    generated_sql TEXT,
    query_result JSONB,
    execution_time FLOAT,
    row_count INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    table_metadata JSONB,
    similar_queries JSONB,
    experts JSONB,
    similar_tables JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User mappings table
CREATE TABLE user_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slack_user_id VARCHAR(50) UNIQUE NOT NULL,
    internal_user_id VARCHAR(50) NOT NULL,
    ldap_id VARCHAR(100),
    email VARCHAR(255),
    full_name VARCHAR(255),
    roles JSONB DEFAULT '[]',
    permissions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Query cache table
CREATE TABLE query_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    query_sql TEXT NOT NULL,
    result_data JSONB,
    row_count INTEGER DEFAULT 0,
    execution_time FLOAT,
    cache_hits INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    slack_user_id VARCHAR(50),
    channel_id VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(255),
    result VARCHAR(20),
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    session_id VARCHAR(100),
    event_data JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for user_sessions
CREATE INDEX idx_user_sessions_user_channel ON user_sessions(user_id, channel_id);
CREATE INDEX idx_user_sessions_slack_user ON user_sessions(slack_user_id);
CREATE INDEX idx_user_sessions_activity ON user_sessions(last_activity);

-- Create indexes for query_history
CREATE INDEX idx_query_history_user ON query_history(user_id);
CREATE INDEX idx_query_history_slack_user ON query_history(slack_user_id);
CREATE INDEX idx_query_history_channel ON query_history(channel_id);
CREATE INDEX idx_query_history_created ON query_history(created_at);
CREATE INDEX idx_query_history_success ON query_history(success);

-- Create indexes for user_mappings
CREATE INDEX idx_user_mappings_internal ON user_mappings(internal_user_id);
CREATE INDEX idx_user_mappings_ldap ON user_mappings(ldap_id);
CREATE INDEX idx_user_mappings_email ON user_mappings(email);

-- Create indexes for query_cache
CREATE INDEX idx_query_cache_hash ON query_cache(query_hash);
CREATE INDEX idx_query_cache_expires ON query_cache(expires_at);
CREATE INDEX idx_query_cache_accessed ON query_cache(last_accessed);

-- Create indexes for audit_logs
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_slack_user ON audit_logs(slack_user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_result ON audit_logs(result);

-- Create full-text search indexes
CREATE INDEX idx_query_history_question_gin ON query_history USING gin(to_tsvector('english', original_question));
CREATE INDEX idx_query_history_sql_gin ON query_history USING gin(to_tsvector('english', generated_sql));

-- DOWN: Rollback migration

-- Drop indexes first
DROP INDEX IF EXISTS idx_query_history_sql_gin;
DROP INDEX IF EXISTS idx_query_history_question_gin;
DROP INDEX IF EXISTS idx_audit_logs_result;
DROP INDEX IF EXISTS idx_audit_logs_created;
DROP INDEX IF EXISTS idx_audit_logs_slack_user;
DROP INDEX IF EXISTS idx_audit_logs_user;
DROP INDEX IF EXISTS idx_audit_logs_event_type;
DROP INDEX IF EXISTS idx_query_cache_accessed;
DROP INDEX IF EXISTS idx_query_cache_expires;
DROP INDEX IF EXISTS idx_query_cache_hash;
DROP INDEX IF EXISTS idx_user_mappings_email;
DROP INDEX IF EXISTS idx_user_mappings_ldap;
DROP INDEX IF EXISTS idx_user_mappings_internal;
DROP INDEX IF EXISTS idx_query_history_success;
DROP INDEX IF EXISTS idx_query_history_created;
DROP INDEX IF EXISTS idx_query_history_channel;
DROP INDEX IF EXISTS idx_query_history_slack_user;
DROP INDEX IF EXISTS idx_query_history_user;
DROP INDEX IF EXISTS idx_user_sessions_activity;
DROP INDEX IF EXISTS idx_user_sessions_slack_user;
DROP INDEX IF EXISTS idx_user_sessions_user_channel;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS query_cache;
DROP TABLE IF EXISTS query_history;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS user_mappings;

-- Drop extensions (optional, might be used by other applications)
-- DROP EXTENSION IF EXISTS "pg_trgm";
-- DROP EXTENSION IF EXISTS "uuid-ossp";
