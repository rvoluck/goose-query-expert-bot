"""
Database models and operations for Goose Slackbot
Handles user sessions, query history, and audit logging
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import uuid

import asyncpg
import structlog
from sqlalchemy import (
    Column, String, Integer, DateTime, Text, Boolean, 
    JSON, Float, Index, ForeignKey, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

Base = declarative_base()


class UserSession(Base):
    """User session storage"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), nullable=False)
    slack_user_id = Column(String(50), nullable=False)
    channel_id = Column(String(50), nullable=False)
    context = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_activity = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    queries = relationship("QueryHistory", back_populates="session")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_sessions_user_channel", "user_id", "channel_id"),
        Index("idx_user_sessions_slack_user", "slack_user_id"),
        Index("idx_user_sessions_activity", "last_activity"),
    )


class QueryHistory(Base):
    """Query execution history"""
    __tablename__ = "query_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"))
    user_id = Column(String(50), nullable=False)
    slack_user_id = Column(String(50), nullable=False)
    channel_id = Column(String(50), nullable=False)
    
    # Query details
    query_id = Column(String(100), unique=True, nullable=False)
    original_question = Column(Text, nullable=False)
    generated_sql = Column(Text)
    query_result = Column(JSON)
    
    # Execution metadata
    execution_time = Column(Float)
    row_count = Column(Integer, default=0)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    
    # Query Expert metadata
    table_metadata = Column(JSON)
    similar_queries = Column(JSON)
    experts = Column(JSON)
    similar_tables = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    session = relationship("UserSession", back_populates="queries")
    
    # Indexes
    __table_args__ = (
        Index("idx_query_history_user", "user_id"),
        Index("idx_query_history_slack_user", "slack_user_id"),
        Index("idx_query_history_channel", "channel_id"),
        Index("idx_query_history_created", "created_at"),
        Index("idx_query_history_success", "success"),
    )


class UserMapping(Base):
    """Slack user to internal user mapping"""
    __tablename__ = "user_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slack_user_id = Column(String(50), unique=True, nullable=False)
    internal_user_id = Column(String(50), nullable=False)
    ldap_id = Column(String(100))
    email = Column(String(255))
    full_name = Column(String(255))
    
    # Permissions and roles
    roles = Column(JSON, default=list)
    permissions = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index("idx_user_mappings_internal", "internal_user_id"),
        Index("idx_user_mappings_ldap", "ldap_id"),
        Index("idx_user_mappings_email", "email"),
    )


class QueryCache(Base):
    """Cache for query results"""
    __tablename__ = "query_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_hash = Column(String(64), unique=True, nullable=False)  # SHA-256 hash
    query_sql = Column(Text, nullable=False)
    result_data = Column(JSON)
    
    # Cache metadata
    row_count = Column(Integer, default=0)
    execution_time = Column(Float)
    cache_hits = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_accessed = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True))
    
    # Indexes
    __table_args__ = (
        Index("idx_query_cache_hash", "query_hash"),
        Index("idx_query_cache_expires", "expires_at"),
        Index("idx_query_cache_accessed", "last_accessed"),
    )


class AuditLog(Base):
    """Audit logging for security and compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # query_execute, user_auth, etc.
    user_id = Column(String(50), nullable=False)
    slack_user_id = Column(String(50))
    channel_id = Column(String(50))
    
    # Action details
    action = Column(String(100), nullable=False)
    resource = Column(String(255))  # table name, query ID, etc.
    result = Column(String(20))  # success, failure, denied
    
    # Context
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    request_id = Column(String(100))
    session_id = Column(String(100))
    
    # Data
    event_data = Column(JSON, default=dict)
    error_message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_logs_event_type", "event_type"),
        Index("idx_audit_logs_user", "user_id"),
        Index("idx_audit_logs_slack_user", "slack_user_id"),
        Index("idx_audit_logs_created", "created_at"),
        Index("idx_audit_logs_result", "result"),
    )


@dataclass
class DatabaseConfig:
    """Database configuration"""
    dsn: str
    min_size: int = 1
    max_size: int = 10
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0


class DatabaseManager:
    """Async database connection manager"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.config.dsn,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
            )
            logger.info("Database connection pool initialized")
            
            # Test connection
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def execute_query(self, query: str, *args) -> Any:
        """Execute a query and return results"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_one(self, query: str, *args) -> Any:
        """Execute a query and return single result"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def execute_scalar(self, query: str, *args) -> Any:
        """Execute a query and return scalar result"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_command(self, command: str, *args) -> str:
        """Execute a command (INSERT, UPDATE, DELETE)"""
        async with self.pool.acquire() as conn:
            return await conn.execute(command, *args)


class UserSessionRepository:
    """Repository for user session operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_session(
        self, 
        user_id: str, 
        slack_user_id: str, 
        channel_id: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Create a new user session"""
        session_id = str(uuid.uuid4())
        context = context or {}
        
        await self.db.execute_command(
            """
            INSERT INTO user_sessions (id, user_id, slack_user_id, channel_id, context)
            VALUES ($1, $2, $3, $4, $5)
            """,
            session_id, user_id, slack_user_id, channel_id, json.dumps(context)
        )
        
        logger.info("Created user session", session_id=session_id, user_id=user_id)
        return session_id
    
    async def get_session(self, user_id: str, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get active session for user in channel"""
        row = await self.db.execute_one(
            """
            SELECT id, user_id, slack_user_id, channel_id, context, 
                   created_at, updated_at, last_activity
            FROM user_sessions 
            WHERE user_id = $1 AND channel_id = $2 AND is_active = true
            ORDER BY last_activity DESC
            LIMIT 1
            """,
            user_id, channel_id
        )
        
        if row:
            return dict(row)
        return None
    
    async def update_session_activity(self, session_id: str, context: Dict[str, Any] = None):
        """Update session activity and context"""
        now = datetime.now(timezone.utc)
        
        if context:
            await self.db.execute_command(
                """
                UPDATE user_sessions 
                SET last_activity = $1, updated_at = $1, context = $2
                WHERE id = $3
                """,
                now, json.dumps(context), session_id
            )
        else:
            await self.db.execute_command(
                """
                UPDATE user_sessions 
                SET last_activity = $1, updated_at = $1
                WHERE id = $3
                """,
                now, session_id
            )
    
    async def cleanup_inactive_sessions(self, inactive_hours: int = 24):
        """Clean up inactive sessions"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=inactive_hours)
        
        result = await self.db.execute_command(
            """
            UPDATE user_sessions 
            SET is_active = false 
            WHERE last_activity < $1 AND is_active = true
            """,
            cutoff
        )
        
        logger.info("Cleaned up inactive sessions", result=result)


class QueryHistoryRepository:
    """Repository for query history operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def save_query(
        self,
        session_id: str,
        user_id: str,
        slack_user_id: str,
        channel_id: str,
        query_id: str,
        original_question: str,
        generated_sql: str = None,
        query_result: Dict[str, Any] = None,
        execution_time: float = None,
        row_count: int = 0,
        success: bool = False,
        error_message: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Save query execution to history"""
        
        await self.db.execute_command(
            """
            INSERT INTO query_history (
                session_id, user_id, slack_user_id, channel_id, query_id,
                original_question, generated_sql, query_result, execution_time,
                row_count, success, error_message, table_metadata, similar_queries,
                experts, similar_tables
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """,
            session_id, user_id, slack_user_id, channel_id, query_id,
            original_question, generated_sql, 
            json.dumps(query_result) if query_result else None,
            execution_time, row_count, success, error_message,
            json.dumps(metadata.get("table_search", {})) if metadata else None,
            json.dumps(metadata.get("similar_queries", {})) if metadata else None,
            json.dumps(metadata.get("experts", [])) if metadata else None,
            json.dumps(metadata.get("similar_tables", [])) if metadata else None
        )
        
        logger.info("Saved query to history", query_id=query_id, user_id=user_id)
    
    async def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent query history for user"""
        rows = await self.db.execute_query(
            """
            SELECT query_id, original_question, generated_sql, success, 
                   execution_time, row_count, created_at
            FROM query_history 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
            """,
            user_id, limit
        )
        
        return [dict(row) for row in rows]
    
    async def get_popular_queries(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular queries from recent days"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        rows = await self.db.execute_query(
            """
            SELECT original_question, generated_sql, COUNT(*) as usage_count,
                   AVG(execution_time) as avg_execution_time,
                   AVG(row_count) as avg_row_count
            FROM query_history 
            WHERE created_at >= $1 AND success = true
            GROUP BY original_question, generated_sql
            ORDER BY usage_count DESC, avg_execution_time ASC
            LIMIT $2
            """,
            cutoff, limit
        )
        
        return [dict(row) for row in rows]


class UserMappingRepository:
    """Repository for user mapping operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_or_update_mapping(
        self,
        slack_user_id: str,
        internal_user_id: str,
        ldap_id: str = None,
        email: str = None,
        full_name: str = None,
        roles: List[str] = None,
        permissions: List[str] = None
    ):
        """Create or update user mapping"""
        
        await self.db.execute_command(
            """
            INSERT INTO user_mappings (
                slack_user_id, internal_user_id, ldap_id, email, full_name,
                roles, permissions, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (slack_user_id) DO UPDATE SET
                internal_user_id = EXCLUDED.internal_user_id,
                ldap_id = EXCLUDED.ldap_id,
                email = EXCLUDED.email,
                full_name = EXCLUDED.full_name,
                roles = EXCLUDED.roles,
                permissions = EXCLUDED.permissions,
                updated_at = EXCLUDED.updated_at
            """,
            slack_user_id, internal_user_id, ldap_id, email, full_name,
            json.dumps(roles or []), json.dumps(permissions or []),
            datetime.now(timezone.utc)
        )
        
        logger.info("Updated user mapping", slack_user_id=slack_user_id)
    
    async def get_mapping(self, slack_user_id: str) -> Optional[Dict[str, Any]]:
        """Get user mapping by Slack user ID"""
        row = await self.db.execute_one(
            """
            SELECT slack_user_id, internal_user_id, ldap_id, email, full_name,
                   roles, permissions, is_active, metadata, created_at, updated_at
            FROM user_mappings 
            WHERE slack_user_id = $1 AND is_active = true
            """,
            slack_user_id
        )
        
        if row:
            mapping = dict(row)
            mapping["roles"] = json.loads(mapping["roles"] or "[]")
            mapping["permissions"] = json.loads(mapping["permissions"] or "[]")
            mapping["metadata"] = json.loads(mapping["metadata"] or "{}")
            return mapping
        
        return None


class AuditLogRepository:
    """Repository for audit log operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def log_event(
        self,
        event_type: str,
        user_id: str,
        action: str,
        result: str = "success",
        slack_user_id: str = None,
        channel_id: str = None,
        resource: str = None,
        ip_address: str = None,
        user_agent: str = None,
        request_id: str = None,
        session_id: str = None,
        event_data: Dict[str, Any] = None,
        error_message: str = None
    ):
        """Log an audit event"""
        
        await self.db.execute_command(
            """
            INSERT INTO audit_logs (
                event_type, user_id, slack_user_id, channel_id, action,
                resource, result, ip_address, user_agent, request_id,
                session_id, event_data, error_message
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            event_type, user_id, slack_user_id, channel_id, action,
            resource, result, ip_address, user_agent, request_id,
            session_id, json.dumps(event_data or {}), error_message
        )


# Database initialization
async def create_database_schema(db_manager: DatabaseManager):
    """Create database schema"""
    schema_sql = """
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
    CREATE INDEX IF NOT EXISTS idx_query_history_slack_user ON query_history(slack_user_id);
    CREATE INDEX IF NOT EXISTS idx_query_history_channel ON query_history(channel_id);
    CREATE INDEX IF NOT EXISTS idx_query_history_created ON query_history(created_at);
    CREATE INDEX IF NOT EXISTS idx_query_history_success ON query_history(success);
    
    CREATE INDEX IF NOT EXISTS idx_user_mappings_internal ON user_mappings(internal_user_id);
    CREATE INDEX IF NOT EXISTS idx_user_mappings_ldap ON user_mappings(ldap_id);
    CREATE INDEX IF NOT EXISTS idx_user_mappings_email ON user_mappings(email);
    
    CREATE INDEX IF NOT EXISTS idx_query_cache_hash ON query_cache(query_hash);
    CREATE INDEX IF NOT EXISTS idx_query_cache_expires ON query_cache(expires_at);
    CREATE INDEX IF NOT EXISTS idx_query_cache_accessed ON query_cache(last_accessed);
    
    CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_slack_user ON audit_logs(slack_user_id);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_result ON audit_logs(result);
    """
    
    async with db_manager.pool.acquire() as conn:
        await conn.execute(schema_sql)
    
    logger.info("Database schema created successfully")


# Global database manager instance
_db_manager = None


async def get_database_manager() -> DatabaseManager:
    """Get global database manager"""
    global _db_manager
    if _db_manager is None:
        config = DatabaseConfig(dsn=settings.database_url)
        _db_manager = DatabaseManager(config)
        await _db_manager.initialize()
    return _db_manager


async def initialize_database():
    """Initialize database with schema"""
    db_manager = await get_database_manager()
    await create_database_schema(db_manager)
    return db_manager


if __name__ == "__main__":
    # Test database operations
    async def test_database():
        db_manager = await initialize_database()
        
        # Test repositories
        session_repo = UserSessionRepository(db_manager)
        query_repo = QueryHistoryRepository(db_manager)
        user_repo = UserMappingRepository(db_manager)
        audit_repo = AuditLogRepository(db_manager)
        
        # Test session creation
        session_id = await session_repo.create_session(
            "test_user", "U123456789", "C987654321"
        )
        print(f"Created session: {session_id}")
        
        # Test user mapping
        await user_repo.create_or_update_mapping(
            "U123456789", "test_user", "test.user", "test@example.com",
            "Test User", ["analyst"], ["query_execute"]
        )
        
        mapping = await user_repo.get_mapping("U123456789")
        print(f"User mapping: {mapping}")
        
        # Test audit logging
        await audit_repo.log_event(
            "user_auth", "test_user", "login", "success",
            slack_user_id="U123456789"
        )
        
        print("✅ Database tests completed successfully")
        
        await db_manager.close()
    
    asyncio.run(test_database())
