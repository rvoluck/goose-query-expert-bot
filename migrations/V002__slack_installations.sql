-- Migration V002: Add Slack Installations table for multi-workspace support
-- This table stores OAuth tokens for each workspace that installs the app

-- Create slack_installations table
CREATE TABLE IF NOT EXISTS slack_installations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id VARCHAR(50) UNIQUE NOT NULL,
    team_name VARCHAR(255),
    enterprise_id VARCHAR(50),
    bot_token TEXT NOT NULL,
    bot_user_id VARCHAR(50),
    bot_scopes TEXT,
    user_id VARCHAR(50),
    user_token TEXT,
    user_scopes TEXT,
    installed_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_slack_installations_team_id ON slack_installations(team_id);
CREATE INDEX IF NOT EXISTS idx_slack_installations_enterprise_id ON slack_installations(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_slack_installations_is_active ON slack_installations(is_active);

-- Add comments
COMMENT ON TABLE slack_installations IS 'Stores OAuth installation data for each Slack workspace';
COMMENT ON COLUMN slack_installations.team_id IS 'Slack workspace/team ID';
COMMENT ON COLUMN slack_installations.bot_token IS 'Bot user OAuth token (xoxb-)';
COMMENT ON COLUMN slack_installations.bot_user_id IS 'Bot user ID in the workspace';
COMMENT ON COLUMN slack_installations.bot_scopes IS 'Comma-separated list of bot scopes';

-- Migration complete
SELECT 'V002: Slack installations table created' as migration_status;
