"""
End-to-end integration tests for Goose Slackbot
Tests complete user workflows from Slack message to query response
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from slack_bot import SlackBot
from goose_client import GooseClient
from database import DatabaseManager, UserSessionRepository, QueryHistoryRepository
from auth import AuthManager


@pytest.mark.integration
@pytest.mark.asyncio
class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""
    
    async def test_complete_query_workflow(self, slack_bot, mock_goose_client, db_manager):
        """Test complete workflow: message -> auth -> query -> response"""
        
        # Setup
        user_id = "U123456789"
        channel_id = "C987654321"
        message = "Show me sales data for last month"
        
        # Mock Slack event
        event = {
            "type": "message",
            "user": user_id,
            "channel": channel_id,
            "text": message,
            "ts": "1234567890.123456"
        }
        
        # Mock Goose response
        mock_goose_client.execute_query.return_value = {
            "success": True,
            "query_id": "q123",
            "sql": "SELECT * FROM sales WHERE date >= '2024-09-01'",
            "results": [
                {"date": "2024-09-01", "amount": 1000},
                {"date": "2024-09-02", "amount": 1500}
            ],
            "row_count": 2,
            "execution_time": 0.5
        }
        
        # Execute workflow
        await slack_bot.handle_message(event)
        
        # Verify session was created
        session_repo = UserSessionRepository(db_manager)
        session = await session_repo.get_session(user_id, channel_id)
        assert session is not None
        assert session["user_id"] == user_id
        
        # Verify query was saved to history
        query_repo = QueryHistoryRepository(db_manager)
        history = await query_repo.get_user_history(user_id, limit=1)
        assert len(history) > 0
        assert history[0]["original_question"] == message
        assert history[0]["success"] is True
        
        # Verify Slack response was sent
        assert slack_bot.client.chat_postMessage.called
    
    async def test_authentication_workflow(self, slack_bot, auth_manager, db_manager):
        """Test user authentication workflow"""
        
        user_id = "U123456789"
        slack_user_id = "U123456789"
        
        # Test authentication
        is_authenticated = await auth_manager.authenticate_user(slack_user_id)
        assert is_authenticated is True
        
        # Verify user mapping was created
        from database import UserMappingRepository
        user_repo = UserMappingRepository(db_manager)
        mapping = await user_repo.get_mapping(slack_user_id)
        
        assert mapping is not None
        assert mapping["slack_user_id"] == slack_user_id
    
    async def test_error_handling_workflow(self, slack_bot, mock_goose_client, db_manager):
        """Test error handling in complete workflow"""
        
        user_id = "U123456789"
        channel_id = "C987654321"
        message = "Invalid query that will fail"
        
        # Mock Goose error response
        mock_goose_client.execute_query.return_value = {
            "success": False,
            "error": "SQL syntax error",
            "query_id": "q456"
        }
        
        event = {
            "type": "message",
            "user": user_id,
            "channel": channel_id,
            "text": message,
            "ts": "1234567890.123456"
        }
        
        # Execute workflow
        await slack_bot.handle_message(event)
        
        # Verify error was logged
        query_repo = QueryHistoryRepository(db_manager)
        history = await query_repo.get_user_history(user_id, limit=1)
        assert len(history) > 0
        assert history[0]["success"] is False
        assert history[0]["error_message"] is not None
        
        # Verify error message was sent to user
        assert slack_bot.client.chat_postMessage.called
        call_args = slack_bot.client.chat_postMessage.call_args
        assert "error" in call_args[1]["text"].lower()
    
    async def test_concurrent_queries_workflow(self, slack_bot, mock_goose_client, db_manager):
        """Test handling multiple concurrent queries"""
        
        user_id = "U123456789"
        channel_id = "C987654321"
        
        # Mock Goose responses
        mock_goose_client.execute_query.return_value = {
            "success": True,
            "query_id": "q789",
            "sql": "SELECT * FROM test",
            "results": [{"id": 1}],
            "row_count": 1,
            "execution_time": 0.1
        }
        
        # Create multiple concurrent events
        events = [
            {
                "type": "message",
                "user": user_id,
                "channel": channel_id,
                "text": f"Query {i}",
                "ts": f"123456789{i}.123456"
            }
            for i in range(5)
        ]
        
        # Execute concurrently
        tasks = [slack_bot.handle_message(event) for event in events]
        await asyncio.gather(*tasks)
        
        # Verify all queries were processed
        query_repo = QueryHistoryRepository(db_manager)
        history = await query_repo.get_user_history(user_id, limit=10)
        assert len(history) >= 5
    
    async def test_session_persistence_workflow(self, slack_bot, db_manager):
        """Test session persistence across multiple messages"""
        
        user_id = "U123456789"
        channel_id = "C987654321"
        
        # First message
        event1 = {
            "type": "message",
            "user": user_id,
            "channel": channel_id,
            "text": "First query",
            "ts": "1234567890.123456"
        }
        
        await slack_bot.handle_message(event1)
        
        # Get session
        session_repo = UserSessionRepository(db_manager)
        session1 = await session_repo.get_session(user_id, channel_id)
        session_id1 = session1["id"]
        
        # Second message (should use same session)
        event2 = {
            "type": "message",
            "user": user_id,
            "channel": channel_id,
            "text": "Second query",
            "ts": "1234567891.123456"
        }
        
        await slack_bot.handle_message(event2)
        
        # Verify same session is used
        session2 = await session_repo.get_session(user_id, channel_id)
        assert session2["id"] == session_id1
        
        # Verify last_activity was updated
        assert session2["last_activity"] > session1["last_activity"]
    
    async def test_rate_limiting_workflow(self, slack_bot, mock_goose_client):
        """Test rate limiting enforcement"""
        
        user_id = "U123456789"
        channel_id = "C987654321"
        
        # Send many messages quickly
        events = [
            {
                "type": "message",
                "user": user_id,
                "channel": channel_id,
                "text": f"Query {i}",
                "ts": f"123456789{i}.123456"
            }
            for i in range(20)  # Exceed rate limit
        ]
        
        responses = []
        for event in events:
            try:
                await slack_bot.handle_message(event)
                responses.append("success")
            except Exception as e:
                if "rate limit" in str(e).lower():
                    responses.append("rate_limited")
                else:
                    responses.append("error")
        
        # Verify some requests were rate limited
        assert "rate_limited" in responses
    
    async def test_file_upload_workflow(self, slack_bot, mock_goose_client, db_manager):
        """Test file upload and processing workflow"""
        
        user_id = "U123456789"
        channel_id = "C987654321"
        
        # Mock file upload event
        event = {
            "type": "file_shared",
            "user_id": user_id,
            "channel_id": channel_id,
            "file": {
                "id": "F123456789",
                "name": "data.csv",
                "mimetype": "text/csv",
                "url_private": "https://files.slack.com/files-pri/T123/F123/data.csv"
            }
        }
        
        # Mock file content
        mock_file_content = "date,amount\n2024-09-01,1000\n2024-09-02,1500"
        
        with patch("slack_bot.download_file", return_value=mock_file_content):
            await slack_bot.handle_file_upload(event)
        
        # Verify file was processed
        assert slack_bot.client.chat_postMessage.called
    
    async def test_thread_management_workflow(self, slack_bot, mock_goose_client):
        """Test threaded conversation workflow"""
        
        user_id = "U123456789"
        channel_id = "C987654321"
        thread_ts = "1234567890.123456"
        
        # First message in thread
        event1 = {
            "type": "message",
            "user": user_id,
            "channel": channel_id,
            "text": "Start thread query",
            "ts": thread_ts
        }
        
        await slack_bot.handle_message(event1)
        
        # Reply in thread
        event2 = {
            "type": "message",
            "user": user_id,
            "channel": channel_id,
            "text": "Follow-up query",
            "ts": "1234567891.123456",
            "thread_ts": thread_ts
        }
        
        await slack_bot.handle_message(event2)
        
        # Verify both messages were processed in same thread
        calls = slack_bot.client.chat_postMessage.call_args_list
        assert len(calls) >= 2
        # Check that thread_ts is preserved
        assert any(call[1].get("thread_ts") == thread_ts for call in calls)


@pytest.mark.integration
@pytest.mark.asyncio
class TestDataPersistence:
    """Test data persistence across operations"""
    
    async def test_query_history_persistence(self, db_manager):
        """Test query history is properly persisted"""
        
        query_repo = QueryHistoryRepository(db_manager)
        session_repo = UserSessionRepository(db_manager)
        
        # Create session
        session_id = await session_repo.create_session(
            "test_user", "U123", "C456"
        )
        
        # Save multiple queries
        for i in range(5):
            await query_repo.save_query(
                session_id=session_id,
                user_id="test_user",
                slack_user_id="U123",
                channel_id="C456",
                query_id=f"q{i}",
                original_question=f"Query {i}",
                generated_sql=f"SELECT {i}",
                success=True,
                row_count=10,
                execution_time=0.5
            )
        
        # Retrieve history
        history = await query_repo.get_user_history("test_user", limit=10)
        assert len(history) == 5
        
        # Verify order (most recent first)
        assert history[0]["original_question"] == "Query 4"
        assert history[4]["original_question"] == "Query 0"
    
    async def test_session_cleanup(self, db_manager):
        """Test inactive session cleanup"""
        
        session_repo = UserSessionRepository(db_manager)
        
        # Create old session
        session_id = await session_repo.create_session(
            "test_user", "U123", "C456"
        )
        
        # Manually set old last_activity
        await db_manager.execute_command(
            """
            UPDATE user_sessions 
            SET last_activity = NOW() - INTERVAL '25 hours'
            WHERE id = $1
            """,
            session_id
        )
        
        # Run cleanup
        await session_repo.cleanup_inactive_sessions(inactive_hours=24)
        
        # Verify session is inactive
        session = await session_repo.get_session("test_user", "C456")
        assert session is None  # Should not return inactive session
    
    async def test_user_mapping_updates(self, db_manager):
        """Test user mapping updates"""
        
        from database import UserMappingRepository
        user_repo = UserMappingRepository(db_manager)
        
        # Create mapping
        await user_repo.create_or_update_mapping(
            slack_user_id="U123",
            internal_user_id="user123",
            email="test@example.com",
            full_name="Test User",
            roles=["analyst"]
        )
        
        # Update mapping
        await user_repo.create_or_update_mapping(
            slack_user_id="U123",
            internal_user_id="user123",
            email="test@example.com",
            full_name="Test User Updated",
            roles=["analyst", "admin"]
        )
        
        # Verify update
        mapping = await user_repo.get_mapping("U123")
        assert mapping["full_name"] == "Test User Updated"
        assert "admin" in mapping["roles"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestErrorRecovery:
    """Test error recovery and resilience"""
    
    async def test_database_connection_retry(self, db_manager):
        """Test database connection retry logic"""
        
        # Simulate connection failure
        with patch.object(db_manager.pool, "acquire", side_effect=Exception("Connection failed")):
            with pytest.raises(Exception):
                await db_manager.execute_query("SELECT 1")
    
    async def test_goose_timeout_handling(self, mock_goose_client):
        """Test handling of Goose timeout"""
        
        mock_goose_client.execute_query.side_effect = asyncio.TimeoutError()
        
        with pytest.raises(asyncio.TimeoutError):
            await mock_goose_client.execute_query("test query")
    
    async def test_slack_api_error_handling(self, slack_bot):
        """Test handling of Slack API errors"""
        
        slack_bot.client.chat_postMessage.side_effect = Exception("Slack API error")
        
        event = {
            "type": "message",
            "user": "U123",
            "channel": "C456",
            "text": "test",
            "ts": "123.456"
        }
        
        # Should not crash, should log error
        await slack_bot.handle_message(event)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
