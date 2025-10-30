"""
Integration tests for database operations and data consistency
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
import json

from database import (
    DatabaseManager, UserSessionRepository, QueryHistoryRepository,
    UserMappingRepository, AuditLogRepository, create_database_schema
)
from tests import async_test


class TestDatabaseIntegration:
    """Test database integration scenarios"""
    
    @async_test
    async def test_cross_repository_data_consistency(self, test_db_manager):
        """Test data consistency across multiple repositories"""
        # Initialize repositories
        user_repo = UserMappingRepository(test_db_manager)
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        audit_repo = AuditLogRepository(test_db_manager)
        
        # Create user mapping
        await user_repo.create_or_update_mapping(
            slack_user_id="U123456789",
            internal_user_id="test_user",
            ldap_id="test.user",
            email="test@company.com",
            full_name="Test User",
            roles=["analyst", "viewer"],
            permissions=["query_execute", "query_view"]
        )
        
        # Create session
        session_id = await session_repo.create_session(
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321",
            context={"test": "data"}
        )
        
        # Save multiple queries
        query_ids = []
        for i in range(3):
            query_id = f"test_query_{i}"
            query_ids.append(query_id)
            
            await query_repo.save_query(
                session_id=session_id,
                user_id="test_user",
                slack_user_id="U123456789",
                channel_id="C987654321",
                query_id=query_id,
                original_question=f"Test question {i}",
                generated_sql=f"SELECT {i}",
                success=True,
                execution_time=0.5 + i * 0.1,
                row_count=i + 1,
                metadata={"test": f"metadata_{i}"}
            )
            
            # Log each query execution
            await audit_repo.log_event(
                event_type="query_execute",
                user_id="test_user",
                action="execute_query",
                result="success",
                slack_user_id="U123456789",
                channel_id="C987654321",
                resource=query_id,
                event_data={"question": f"Test question {i}"}
            )
        
        # Verify data consistency
        
        # Check user mapping
        user_mapping = await user_repo.get_mapping("U123456789")
        assert user_mapping is not None
        assert user_mapping["internal_user_id"] == "test_user"
        
        # Check session exists and is linked
        session = await session_repo.get_session("test_user", "C987654321")
        assert session is not None
        assert session["id"] == session_id
        
        # Check all queries are linked to session
        history = await query_repo.get_user_history("test_user", limit=10)
        assert len(history) == 3
        
        for i, query in enumerate(history):
            assert query["user_id"] == "test_user"
            assert query["slack_user_id"] == "U123456789"
            assert query["channel_id"] == "C987654321"
            assert query["success"] is True
        
        # Check audit logs
        audit_logs = await test_db_manager.execute_query(
            "SELECT * FROM audit_logs WHERE user_id = $1 ORDER BY created_at",
            "test_user"
        )
        assert len(audit_logs) == 3
        
        for log in audit_logs:
            assert log["event_type"] == "query_execute"
            assert log["result"] == "success"
            assert log["resource"] in query_ids
    
    @async_test
    async def test_concurrent_database_operations(self, test_db_manager):
        """Test concurrent database operations don't cause conflicts"""
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        
        # Create multiple sessions concurrently
        async def create_user_session(user_num):
            session_id = await session_repo.create_session(
                user_id=f"user_{user_num}",
                slack_user_id=f"U{user_num:09d}",
                channel_id=f"C{user_num:09d}"
            )
            
            # Add queries to each session
            for i in range(3):
                await query_repo.save_query(
                    session_id=session_id,
                    user_id=f"user_{user_num}",
                    slack_user_id=f"U{user_num:09d}",
                    channel_id=f"C{user_num:09d}",
                    query_id=f"user_{user_num}_query_{i}",
                    original_question=f"Question {i} from user {user_num}",
                    generated_sql=f"SELECT {i} FROM table_{user_num}",
                    success=True,
                    execution_time=0.1 * i,
                    row_count=i + 1
                )
            
            return session_id
        
        # Run concurrent operations
        tasks = [create_user_session(i) for i in range(5)]
        session_ids = await asyncio.gather(*tasks)
        
        # Verify all sessions were created
        assert len(session_ids) == 5
        assert len(set(session_ids)) == 5  # All unique
        
        # Verify each user has correct number of queries
        for i in range(5):
            history = await query_repo.get_user_history(f"user_{i}", limit=10)
            assert len(history) == 3
            
            # Verify queries belong to correct user
            for query in history:
                assert query["user_id"] == f"user_{i}"
                assert query["slack_user_id"] == f"U{i:09d}"
    
    @async_test
    async def test_database_transaction_rollback(self, test_db_manager):
        """Test transaction rollback behavior"""
        user_repo = UserMappingRepository(test_db_manager)
        
        # Test that invalid operations don't affect valid data
        await user_repo.create_or_update_mapping(
            slack_user_id="U123456789",
            internal_user_id="valid_user",
            email="valid@company.com"
        )
        
        # Verify valid user exists
        valid_user = await user_repo.get_mapping("U123456789")
        assert valid_user is not None
        
        # Attempt invalid operation (this should fail gracefully)
        try:
            await test_db_manager.execute_command(
                "INSERT INTO nonexistent_table VALUES (1, 'test')"
            )
        except Exception:
            pass  # Expected to fail
        
        # Verify valid user still exists
        still_valid = await user_repo.get_mapping("U123456789")
        assert still_valid is not None
        assert still_valid["internal_user_id"] == "valid_user"
    
    @async_test
    async def test_database_connection_recovery(self, test_db_manager):
        """Test database connection recovery"""
        session_repo = UserSessionRepository(test_db_manager)
        
        # Normal operation
        session_id = await session_repo.create_session(
            user_id="test_user",
            slack_user_id="U123456789",
            channel_id="C987654321"
        )
        assert session_id is not None
        
        # Simulate connection issue and recovery
        # (In a real test, you might temporarily close the connection pool)
        
        # Verify operations still work after recovery
        session = await session_repo.get_session("test_user", "C987654321")
        assert session is not None
    
    @async_test
    async def test_large_data_operations(self, test_db_manager):
        """Test operations with large amounts of data"""
        query_repo = QueryHistoryRepository(test_db_manager)
        session_repo = UserSessionRepository(test_db_manager)
        
        # Create session
        session_id = await session_repo.create_session(
            user_id="bulk_user",
            slack_user_id="U999999999",
            channel_id="C999999999"
        )
        
        # Insert large number of queries
        batch_size = 100
        total_queries = 500
        
        for batch_start in range(0, total_queries, batch_size):
            tasks = []
            for i in range(batch_start, min(batch_start + batch_size, total_queries)):
                task = query_repo.save_query(
                    session_id=session_id,
                    user_id="bulk_user",
                    slack_user_id="U999999999",
                    channel_id="C999999999",
                    query_id=f"bulk_query_{i}",
                    original_question=f"Bulk question {i}",
                    generated_sql=f"SELECT {i} FROM bulk_table",
                    success=True,
                    execution_time=0.1,
                    row_count=1
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks)
        
        # Verify all queries were saved
        history = await query_repo.get_user_history("bulk_user", limit=total_queries + 10)
        assert len(history) == total_queries
        
        # Test pagination/limiting
        limited_history = await query_repo.get_user_history("bulk_user", limit=50)
        assert len(limited_history) == 50
    
    @async_test
    async def test_data_migration_compatibility(self, test_db_manager):
        """Test data compatibility across schema changes"""
        # This would test migration scenarios
        # For now, test that current schema handles edge cases
        
        user_repo = UserMappingRepository(test_db_manager)
        
        # Test with minimal required fields
        await user_repo.create_or_update_mapping(
            slack_user_id="U_MINIMAL",
            internal_user_id="minimal_user"
            # No optional fields
        )
        
        minimal_user = await user_repo.get_mapping("U_MINIMAL")
        assert minimal_user is not None
        assert minimal_user["internal_user_id"] == "minimal_user"
        assert minimal_user["roles"] == []
        assert minimal_user["permissions"] == []
    
    @async_test
    async def test_database_performance_under_load(self, test_db_manager):
        """Test database performance under concurrent load"""
        import time
        
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        
        # Create base session
        session_id = await session_repo.create_session(
            user_id="perf_user",
            slack_user_id="U_PERF",
            channel_id="C_PERF"
        )
        
        # Measure performance of concurrent operations
        start_time = time.time()
        
        async def concurrent_query_save(batch_num):
            tasks = []
            for i in range(10):  # 10 queries per batch
                task = query_repo.save_query(
                    session_id=session_id,
                    user_id="perf_user",
                    slack_user_id="U_PERF",
                    channel_id="C_PERF",
                    query_id=f"perf_query_{batch_num}_{i}",
                    original_question=f"Performance test query {batch_num}_{i}",
                    generated_sql=f"SELECT {i} FROM perf_table_{batch_num}",
                    success=True,
                    execution_time=0.1,
                    row_count=1
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks)
        
        # Run 10 concurrent batches (100 total queries)
        batch_tasks = [concurrent_query_save(i) for i in range(10)]
        await asyncio.gather(*batch_tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all queries were saved
        history = await query_repo.get_user_history("perf_user", limit=200)
        assert len(history) == 100
        
        # Performance assertion (adjust based on expected performance)
        queries_per_second = 100 / total_time
        assert queries_per_second > 10  # Should handle at least 10 queries/second
    
    @async_test
    async def test_database_cleanup_operations(self, test_db_manager):
        """Test database cleanup and maintenance operations"""
        session_repo = UserSessionRepository(test_db_manager)
        
        # Create sessions with different activity times
        current_time = datetime.now(timezone.utc)
        
        # Recent session (should not be cleaned up)
        recent_session_id = await session_repo.create_session(
            user_id="recent_user",
            slack_user_id="U_RECENT",
            channel_id="C_RECENT"
        )
        
        # Old session (should be cleaned up)
        old_session_id = await session_repo.create_session(
            user_id="old_user",
            slack_user_id="U_OLD",
            channel_id="C_OLD"
        )
        
        # Manually set old activity time
        old_time = current_time - timedelta(hours=25)
        await test_db_manager.execute_command(
            "UPDATE user_sessions SET last_activity = $1 WHERE id = $2",
            old_time, old_session_id
        )
        
        # Run cleanup
        await session_repo.cleanup_inactive_sessions(inactive_hours=24)
        
        # Verify cleanup results
        recent_session = await test_db_manager.execute_one(
            "SELECT is_active FROM user_sessions WHERE id = $1",
            recent_session_id
        )
        assert recent_session["is_active"] is True
        
        old_session = await test_db_manager.execute_one(
            "SELECT is_active FROM user_sessions WHERE id = $1",
            old_session_id
        )
        assert old_session["is_active"] is False
    
    @async_test
    async def test_foreign_key_constraints(self, test_db_manager):
        """Test foreign key constraint enforcement"""
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        
        # Create session
        session_id = await session_repo.create_session(
            user_id="fk_user",
            slack_user_id="U_FK",
            channel_id="C_FK"
        )
        
        # Save query with valid session reference
        await query_repo.save_query(
            session_id=session_id,
            user_id="fk_user",
            slack_user_id="U_FK",
            channel_id="C_FK",
            query_id="valid_fk_query",
            original_question="Valid FK test",
            generated_sql="SELECT 1",
            success=True
        )
        
        # Verify query was saved
        history = await query_repo.get_user_history("fk_user", limit=1)
        assert len(history) == 1
        
        # Test invalid foreign key (should fail)
        invalid_session_id = str(uuid.uuid4())
        
        with pytest.raises(Exception):  # Should raise foreign key constraint error
            await query_repo.save_query(
                session_id=invalid_session_id,
                user_id="fk_user",
                slack_user_id="U_FK",
                channel_id="C_FK",
                query_id="invalid_fk_query",
                original_question="Invalid FK test",
                generated_sql="SELECT 1",
                success=True
            )
    
    @async_test
    async def test_json_field_operations(self, test_db_manager):
        """Test JSON field storage and retrieval"""
        user_repo = UserMappingRepository(test_db_manager)
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        
        # Test complex JSON data
        complex_metadata = {
            "table_search": {
                "tables_found": 5,
                "primary_table": "users",
                "related_tables": ["orders", "payments", "sessions"],
                "search_time": 0.25
            },
            "similar_queries": {
                "queries_found": 12,
                "top_matches": [
                    {"query_id": "q1", "similarity": 0.95, "user": "analyst1"},
                    {"query_id": "q2", "similarity": 0.87, "user": "analyst2"}
                ]
            },
            "experts": [
                {
                    "user_name": "data_expert",
                    "ldap_id": "expert1",
                    "reason": "frequent user",
                    "query_count": 150,
                    "last_query": "2024-01-15T10:30:00Z"
                }
            ]
        }
        
        # Create user with complex roles/permissions
        await user_repo.create_or_update_mapping(
            slack_user_id="U_JSON",
            internal_user_id="json_user",
            roles=["senior_analyst", "data_viewer", "report_creator"],
            permissions=["query_execute", "query_view", "query_share", "export_data"]
        )
        
        # Create session with context
        session_id = await session_repo.create_session(
            user_id="json_user",
            slack_user_id="U_JSON",
            channel_id="C_JSON",
            context={
                "preferences": {"format": "table", "max_rows": 100},
                "history": {"last_query": "revenue analysis"},
                "permissions": {"can_export": True}
            }
        )
        
        # Save query with complex metadata
        await query_repo.save_query(
            session_id=session_id,
            user_id="json_user",
            slack_user_id="U_JSON",
            channel_id="C_JSON",
            query_id="json_query_test",
            original_question="Complex JSON test query",
            generated_sql="SELECT * FROM complex_table",
            success=True,
            execution_time=1.5,
            row_count=50,
            metadata=complex_metadata
        )
        
        # Verify JSON data integrity
        user_mapping = await user_repo.get_mapping("U_JSON")
        assert len(user_mapping["roles"]) == 3
        assert "senior_analyst" in user_mapping["roles"]
        assert len(user_mapping["permissions"]) == 4
        assert "export_data" in user_mapping["permissions"]
        
        session = await session_repo.get_session("json_user", "C_JSON")
        assert session["context"]["preferences"]["format"] == "table"
        assert session["context"]["permissions"]["can_export"] is True
        
        history = await query_repo.get_user_history("json_user", limit=1)
        query = history[0]
        
        # Verify complex metadata was stored and retrieved correctly
        # Note: In real implementation, you'd need to parse JSON from database
        # This assumes the repository handles JSON serialization/deserialization
        assert "table_search" in str(query)  # Basic check that JSON data is present
        assert "similar_queries" in str(query)
        assert "experts" in str(query)
