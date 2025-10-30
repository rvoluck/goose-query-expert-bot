-- Migration: Initial Schema
-- Version: V001
-- Created: 2024-01-01

-- UP
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
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
CREATE TABLE IF NOT EXISTS query_history (
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
CREATE TABLE IF NOT EXISTS user_mappings (
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
CREATE TABLE IF NOT EXISTS query_cache (
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
CREATE TABLE IF NOT EXISTS audit_logs (
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_channel ON user_sessions(user_id, channel_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_slack_user ON user_sessions(slack_user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_activity ON user_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_query_history_user ON query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_query_history_created ON query_history(created_at);
CREATE INDEX IF NOT EXISTS idx_user_mappings_internal ON user_mappings(internal_user_id);
CREATE INDEX IF NOT EXISTS idx_query_cache_hash ON query_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);

-- DOWN
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS query_cache;
DROP TABLE IF EXISTS query_history;
DROP TABLE IF EXISTS user_mappings;
DROP TABLE IF EXISTS user_sessions;
DROP EXTENSION IF EXISTS "pg_trgm";
DROP EXTENSION IF EXISTS "uuid-ossp";
