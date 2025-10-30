"""
Pytest configuration and fixtures for Goose Slackbot tests
"""

import pytest
import asyncio
import asyncpg
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import json
import uuid

from database import DatabaseManager, DatabaseConfig
from auth import AuthSystem, UserContext
from goose_client import GooseQueryExpertClient, QueryResult, QueryStatus
from slack_bot import SlackResultFormatter, GooseSlackBot
from config import Settings

# Test database configuration
TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/goose_slackbot_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_manager():
    """Create test database manager with in-memory or test database"""
    config = DatabaseConfig(dsn=TEST_DATABASE_URL)
    db_manager = DatabaseManager(config)
    
    try:
        await db_manager.initialize()
        
        # Create test schema
        await create_test_schema(db_manager)
        
        yield db_manager
        
    finally:
        # Cleanup
        await cleanup_test_data(db_manager)
        await db_manager.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return Settings(
        slack_bot_token="xoxb-test-token",
        slack_signing_secret="test-signing-secret",
        slack_app_token="xapp-test-token",
        database_url=TEST_DATABASE_URL,
        goose_api_url="http://localhost:8000",
        goose_api_key="test-api-key",
        max_inline_rows=10,
        max_result_rows=1000,
        enable_interactive_buttons=True,
        enable_file_uploads=True,
        is_development=True
    )


@pytest.fixture
def mock_auth_system():
    """Mock authentication system"""
    auth_system = AsyncMock(spec=AuthSystem)
    
    # Mock user context
    user_context = UserContext(
        user_id="test_user",
        slack_user_id="U123456789",
        ldap_id="test.user",
        email="test@example.com",
        full_name="Test User",
        roles=["analyst"],
        permissions=["query_execute", "query_view"],
        is_active=True
    )
    
    auth_system.authenticate_user.return_value = user_context
    auth_system.check_permission.return_value = True
    
    return auth_system


@pytest.fixture
def mock_goose_client():
    """Mock Goose Query Expert client"""
    client = AsyncMock(spec=GooseQueryExpertClient)
    
    # Mock successful query result
    successful_result = QueryResult(
        query_id="test_query_123",
        sql="SELECT COUNT(*) FROM users",
        columns=["count"],
        rows=[[42]],
        row_count=1,
        execution_time=0.5,
        success=True,
        metadata={
            "table_search": {"tables_found": 1},
            "similar_queries": {"queries_found": 2},
            "experts": [{"user_name": "data_expert", "reason": "frequent user"}]
        }
    )
    
    client.process_user_question.return_value = successful_result
    
    return client


@pytest.fixture
def mock_slack_app():
    """Mock Slack app for testing"""
    app = MagicMock()
    app.client = AsyncMock()
    app.client.auth_test.return_value = {"user_id": "B123456789"}
    app.client.chat_postMessage.return_value = {"ts": "1234567890.123456"}
    app.client.chat_update.return_value = {"ts": "1234567890.123456"}
    app.client.files_upload_v2.return_value = {"file": {"id": "F123456"}}
    
    return app


@pytest.fixture
def sample_query_result():
    """Sample query result for testing"""
    return QueryResult(
        query_id="test_query_123",
        sql="SELECT id, name, email FROM users LIMIT 5",
        columns=["id", "name", "email"],
        rows=[
            [1, "John Doe", "john@example.com"],
            [2, "Jane Smith", "jane@example.com"],
            [3, "Bob Johnson", "bob@example.com"]
        ],
        row_count=3,
        execution_time=0.25,
        success=True,
        metadata={
            "table_search": {"tables_found": 1},
            "similar_queries": {"queries_found": 0},
            "experts": []
        }
    )


@pytest.fixture
def sample_error_result():
    """Sample error result for testing"""
    return QueryResult(
        query_id="test_query_error",
        sql="SELECT * FROM nonexistent_table",
        columns=[],
        rows=[],
        row_count=0,
        execution_time=0.0,
        success=False,
        error_message="Table 'nonexistent_table' doesn't exist",
        metadata={}
    )


@pytest.fixture
def sample_large_result():
    """Sample large result for testing file upload"""
    rows = [[i, f"User {i}", f"user{i}@example.com"] for i in range(1, 101)]
    
    return QueryResult(
        query_id="test_query_large",
        sql="SELECT id, name, email FROM users",
        columns=["id", "name", "email"],
        rows=rows,
        row_count=100,
        execution_time=2.5,
        success=True,
        metadata={
            "table_search": {"tables_found": 1},
            "similar_queries": {"queries_found": 5},
            "experts": [{"user_name": "data_expert", "reason": "table owner"}]
        }
    )


@pytest.fixture
def slack_event_message():
    """Sample Slack message event"""
    return {
        "type": "message",
        "user": "U123456789",
        "channel": "C987654321",
        "text": "What was our revenue last month?",
        "ts": "1234567890.123456",
        "channel_type": "channel"
    }


@pytest.fixture
def slack_event_dm():
    """Sample Slack DM event"""
    return {
        "type": "message",
        "user": "U123456789",
        "channel": "D123456789",
        "text": "Show me user signups this week",
        "ts": "1234567890.123456",
        "channel_type": "im"
    }


@pytest.fixture
def slack_event_mention():
    """Sample Slack app mention event"""
    return {
        "type": "app_mention",
        "user": "U123456789",
        "channel": "C987654321",
        "text": "<@B123456789> How many orders were placed today?",
        "ts": "1234567890.123456"
    }


async def create_test_schema(db_manager: DatabaseManager):
    """Create test database schema"""
    schema_sql = """
    -- Drop existing test tables
    DROP TABLE IF EXISTS audit_logs CASCADE;
    DROP TABLE IF EXISTS query_cache CASCADE;
    DROP TABLE IF EXISTS query_history CASCADE;
    DROP TABLE IF EXISTS user_sessions CASCADE;
    DROP TABLE IF EXISTS user_mappings CASCADE;
    
    -- Create test tables (simplified versions)
    CREATE TABLE user_sessions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id VARCHAR(50) NOT NULL,
        slack_user_id VARCHAR(50) NOT NULL,
        channel_id VARCHAR(50) NOT NULL,
        context JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        last_activity TIMESTAMPTZ DEFAULT NOW(),
        is_active BOOLEAN DEFAULT true
    );
    
    CREATE TABLE query_history (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    
    CREATE TABLE user_mappings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    
    CREATE TABLE audit_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_type VARCHAR(50) NOT NULL,
        user_id VARCHAR(50) NOT NULL,
        slack_user_id VARCHAR(50),
        channel_id VARCHAR(50),
        action VARCHAR(100) NOT NULL,
        resource VARCHAR(255),
        result VARCHAR(20),
        event_data JSONB DEFAULT '{}',
        error_message TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    
    async with db_manager.pool.acquire() as conn:
        await conn.execute(schema_sql)


async def cleanup_test_data(db_manager: DatabaseManager):
    """Clean up test data"""
    cleanup_sql = """
    TRUNCATE TABLE audit_logs CASCADE;
    TRUNCATE TABLE query_history CASCADE;
    TRUNCATE TABLE user_sessions CASCADE;
    TRUNCATE TABLE user_mappings CASCADE;
    """
    
    try:
        async with db_manager.pool.acquire() as conn:
            await conn.execute(cleanup_sql)
    except Exception:
        pass  # Ignore cleanup errors


# Utility functions for tests
def create_test_user_mapping():
    """Create test user mapping data"""
    return {
        "slack_user_id": "U123456789",
        "internal_user_id": "test_user",
        "ldap_id": "test.user",
        "email": "test@example.com",
        "full_name": "Test User",
        "roles": ["analyst"],
        "permissions": ["query_execute", "query_view"],
        "is_active": True
    }


def create_test_session():
    """Create test session data"""
    return {
        "id": str(uuid.uuid4()),
        "user_id": "test_user",
        "slack_user_id": "U123456789",
        "channel_id": "C987654321",
        "context": {},
        "created_at": datetime.now(timezone.utc),
        "is_active": True
    }


def create_test_query_history():
    """Create test query history data"""
    return {
        "query_id": "test_query_123",
        "user_id": "test_user",
        "slack_user_id": "U123456789",
        "channel_id": "C987654321",
        "original_question": "What was our revenue last month?",
        "generated_sql": "SELECT SUM(amount) FROM orders WHERE created_at >= '2024-01-01'",
        "success": True,
        "execution_time": 1.5,
        "row_count": 1
    }
