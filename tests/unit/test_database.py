"""
Unit tests for database operations
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
import json

from database import (
    DatabaseManager, DatabaseConfig, UserSessionRepository,
    QueryHistoryRepository, UserMappingRepository, AuditLogRepository
)
from tests import async_test


class TestDatabaseManager:
    """Test DatabaseManager class"""
    
    @async_test
    async def test_initialization(self):
        """Test database manager initialization"""
        config = DatabaseConfig(dsn="postgresql://test:test@localhost/test")
        db_manager = DatabaseManager(config)
        
        with patch('asyncpg.create_pool') as mock_pool:
            mock_pool.return_value = AsyncMock()
            await db_manager.initialize()
            
            mock_pool.assert_called_once()
            assert db_manager.pool is not None
    
    @async_test
    async def test_execute_query(self, test_db_manager):
        """Test query execution"""
        result = await test_db_manager.execute_scalar("SELECT 1")
        assert result == 1
    
    @async_test
    async def test_connection_error_handling(self):
        """Test connection error handling"""
        config = DatabaseConfig(dsn="postgresql://invalid:invalid@invalid/invalid")
        db_manager = DatabaseManager(config)
        
        with pytest.raises(Exception):
            await db_manager.initialize()


class TestUserSessionRepository:
    """Test UserSessionRepository class"""
    
    @async_test
    async def test_create_session(self, test_db_manager):
        """Test session creation"""
        repo = UserSessionRepository(test_db_manager)
        
        session_id = await repo.create_session(
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321",
            context={"test": "data"}
        )
        
        assert session_id is not None
        assert isinstance(session_id, str)
    
    @async_test
    async def test_get_session(self, test_db_manager):
        """Test session retrieval"""
        repo = UserSessionRepository(test_db_manager)
        
        # Create session first
        session_id = await repo.create_session(
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321"
        )
        
        # Retrieve session
        session = await repo.get_session("test_user", "C987654321")
        
        assert session is not None
        assert session["user_id"] == "test_user"
        assert session["slack_user_id"] == "U123456789"
        assert session["channel_id"] == "C987654321"
    
    @async_test
    async def test_update_session_activity(self, test_db_manager):
        """Test session activity update"""
        repo = UserSessionRepository(test_db_manager)
        
        # Create session
        session_id = await repo.create_session(
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321"
        )
        
        # Update activity
        new_context = {"updated": True}
        await repo.update_session_activity(session_id, new_context)
        
        # Verify update
        session = await repo.get_session("test_user", "C987654321")
        assert session["context"]["updated"] is True
    
    @async_test
    async def test_cleanup_inactive_sessions(self, test_db_manager):
        """Test inactive session cleanup"""
        repo = UserSessionRepository(test_db_manager)
        
        # Create session
        session_id = await repo.create_session(
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321"
        )
        
        # Manually set old activity time
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        await test_db_manager.execute_command(
            "UPDATE user_sessions SET last_activity = $1 WHERE id = $2",
            old_time, session_id
        )
        
        # Cleanup inactive sessions
        await repo.cleanup_inactive_sessions(inactive_hours=24)
        
        # Verify session is inactive
        session = await test_db_manager.execute_one(
            "SELECT is_active FROM user_sessions WHERE id = $1",
            session_id
        )
        assert session["is_active"] is False


class TestQueryHistoryRepository:
    """Test QueryHistoryRepository class"""
    
    @async_test
    async def test_save_query(self, test_db_manager):
        """Test query history saving"""
        # Create session first
        session_repo = UserSessionRepository(test_db_manager)
        session_id = await session_repo.create_session(
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321"
        )
        
        # Save query
        query_repo = QueryHistoryRepository(test_db_manager)
        await query_repo.save_query(
            session_id=session_id,
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321",
            query_id="test_query_123",
            original_question="What is the revenue?",
            generated_sql="SELECT SUM(amount) FROM orders",
            execution_time=1.5,
            row_count=1,
            success=True,
            metadata={"test": "metadata"}
        )
        
        # Verify query was saved
        query = await test_db_manager.execute_one(
            "SELECT * FROM query_history WHERE query_id = $1",
            "test_query_123"
        )
        
        assert query is not None
        assert query["original_question"] == "What is the revenue?"
        assert query["success"] is True
        assert query["execution_time"] == 1.5
    
    @async_test
    async def test_get_user_history(self, test_db_manager):
        """Test user query history retrieval"""
        # Create session and save queries
        session_repo = UserSessionRepository(test_db_manager)
        session_id = await session_repo.create_session(
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321"
        )
        
        query_repo = QueryHistoryRepository(test_db_manager)
        
        # Save multiple queries
        for i in range(3):
            await query_repo.save_query(
                session_id=session_id,
                user_id="test_user",
                slack_user_id="U123456789",
                channel_id="C987654321",
                query_id=f"test_query_{i}",
                original_question=f"Question {i}",
                generated_sql=f"SELECT {i}",
                success=True
            )
        
        # Get history
        history = await query_repo.get_user_history("test_user", limit=5)
        
        assert len(history) == 3
        assert all(h["user_id"] == "test_user" for h in history)
    
    @async_test
    async def test_get_popular_queries(self, test_db_manager):
        """Test popular queries retrieval"""
        # Create session and save duplicate queries
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        
        session_id = await session_repo.create_session(
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321"
        )
        
        # Save same query multiple times
        popular_question = "What is our revenue?"
        popular_sql = "SELECT SUM(amount) FROM orders"
        
        for i in range(3):
            await query_repo.save_query(
                session_id=session_id,
                user_id="test_user",
                slack_user_id="U123456789",
                channel_id="C987654321",
                query_id=f"popular_query_{i}",
                original_question=popular_question,
                generated_sql=popular_sql,
                success=True,
                execution_time=1.0
            )
        
        # Get popular queries
        popular = await query_repo.get_popular_queries(days=7, limit=5)
        
        assert len(popular) >= 1
        assert popular[0]["usage_count"] == 3
        assert popular[0]["original_question"] == popular_question


class TestUserMappingRepository:
    """Test UserMappingRepository class"""
    
    @async_test
    async def test_create_mapping(self, test_db_manager):
        """Test user mapping creation"""
        repo = UserMappingRepository(test_db_manager)
        
        await repo.create_or_update_mapping(
            slack_user_id="U123456789",
            internal_user_id="test_user",
            ldap_id="test.user",
            email="test@example.com",
            full_name="Test User",
            roles=["analyst"],
            permissions=["query_execute"]
        )
        
        # Verify mapping was created
        mapping = await repo.get_mapping("U123456789")
        
        assert mapping is not None
        assert mapping["internal_user_id"] == "test_user"
        assert mapping["ldap_id"] == "test.user"
        assert mapping["email"] == "test@example.com"
        assert "analyst" in mapping["roles"]
        assert "query_execute" in mapping["permissions"]
    
    @async_test
    async def test_update_mapping(self, test_db_manager):
        """Test user mapping update"""
        repo = UserMappingRepository(test_db_manager)
        
        # Create initial mapping
        await repo.create_or_update_mapping(
            slack_user_id="U123456789",
            internal_user_id="test_user",
            email="old@example.com"
        )
        
        # Update mapping
        await repo.create_or_update_mapping(
            slack_user_id="U123456789",
            internal_user_id="test_user",
            email="new@example.com",
            roles=["admin"]
        )
        
        # Verify update
        mapping = await repo.get_mapping("U123456789")
        assert mapping["email"] == "new@example.com"
        assert "admin" in mapping["roles"]
    
    @async_test
    async def test_get_nonexistent_mapping(self, test_db_manager):
        """Test retrieval of non-existent mapping"""
        repo = UserMappingRepository(test_db_manager)
        
        mapping = await repo.get_mapping("U999999999")
        assert mapping is None


class TestAuditLogRepository:
    """Test AuditLogRepository class"""
    
    @async_test
    async def test_log_event(self, test_db_manager):
        """Test audit event logging"""
        repo = AuditLogRepository(test_db_manager)
        
        await repo.log_event(
            event_type="query_execute",
            user_id="test_user",
            action="execute_query",
            result="success",
            slack_user_id="U123456789",
            channel_id="C987654321",
            resource="test_query_123",
            event_data={"question": "What is revenue?"},
            request_id="req_123"
        )
        
        # Verify log was created
        log = await test_db_manager.execute_one(
            "SELECT * FROM audit_logs WHERE user_id = $1 AND action = $2",
            "test_user", "execute_query"
        )
        
        assert log is not None
        assert log["event_type"] == "query_execute"
        assert log["result"] == "success"
        assert log["resource"] == "test_query_123"
        assert json.loads(log["event_data"])["question"] == "What is revenue?"
    
    @async_test
    async def test_log_error_event(self, test_db_manager):
        """Test error event logging"""
        repo = AuditLogRepository(test_db_manager)
        
        await repo.log_event(
            event_type="query_execute",
            user_id="test_user",
            action="execute_query",
            result="failure",
            error_message="Permission denied"
        )
        
        # Verify error log
        log = await test_db_manager.execute_one(
            "SELECT * FROM audit_logs WHERE result = $1",
            "failure"
        )
        
        assert log is not None
        assert log["error_message"] == "Permission denied"


class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    @async_test
    async def test_full_user_workflow(self, test_db_manager):
        """Test complete user workflow"""
        # Initialize repositories
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        user_repo = UserMappingRepository(test_db_manager)
        audit_repo = AuditLogRepository(test_db_manager)
        
        # 1. Create user mapping
        await user_repo.create_or_update_mapping(
            slack_user_id="U123456789",
            internal_user_id="test_user",
            ldap_id="test.user",
            email="test@example.com",
            roles=["analyst"],
            permissions=["query_execute"]
        )
        
        # 2. Create session
        session_id = await session_repo.create_session(
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321"
        )
        
        # 3. Log authentication
        await audit_repo.log_event(
            event_type="user_auth",
            user_id="test_user",
            action="authenticate",
            result="success",
            slack_user_id="U123456789"
        )
        
        # 4. Save query
        await query_repo.save_query(
            session_id=session_id,
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321",
            query_id="workflow_query_123",
            original_question="Test workflow query",
            generated_sql="SELECT 1",
            success=True,
            execution_time=0.5,
            row_count=1
        )
        
        # 5. Log query execution
        await audit_repo.log_event(
            event_type="query_execute",
            user_id="test_user",
            action="execute_query",
            result="success",
            resource="workflow_query_123"
        )
        
        # Verify all data was created correctly
        user_mapping = await user_repo.get_mapping("U123456789")
        session = await session_repo.get_session("test_user", "C987654321")
        history = await query_repo.get_user_history("test_user", limit=1)
        
        assert user_mapping is not None
        assert session is not None
        assert len(history) == 1
        assert history[0]["query_id"] == "workflow_query_123"
    
    @async_test
    async def test_concurrent_operations(self, test_db_manager):
        """Test concurrent database operations"""
        session_repo = UserSessionRepository(test_db_manager)
        
        # Create multiple sessions concurrently
        tasks = []
        for i in range(5):
            task = session_repo.create_session(
                user_id=f"user_{i}",
                slack_user_id=f"U{i:09d}",
                channel_id=f"C{i:09d}"
            )
            tasks.append(task)
        
        session_ids = await asyncio.gather(*tasks)
        
        # Verify all sessions were created
        assert len(session_ids) == 5
        assert all(session_id is not None for session_id in session_ids)
        assert len(set(session_ids)) == 5  # All unique
    
    @async_test
    async def test_transaction_rollback(self, test_db_manager):
        """Test transaction rollback on error"""
        # This would test transaction handling if implemented
        # For now, just test that invalid operations fail gracefully
        
        with pytest.raises(Exception):
            await test_db_manager.execute_command(
                "INSERT INTO nonexistent_table VALUES (1)"
            )
        
        # Verify database is still functional
        result = await test_db_manager.execute_scalar("SELECT 1")
        assert result == 1
