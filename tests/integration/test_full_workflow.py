"""
Integration tests for complete Slack bot workflows
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from slack_bot import GooseSlackBot
from database import (
    UserSessionRepository, QueryHistoryRepository, 
    UserMappingRepository, AuditLogRepository
)
from auth import AuthSystem, DatabaseAuthProvider, UserContext
from goose_client import GooseQueryExpertClient, QueryResult, QueryStatus
from tests import async_test


class TestFullWorkflowIntegration:
    """Test complete user interaction workflows"""
    
    @async_test
    async def test_new_user_first_query_workflow(self, test_db_manager):
        """Test complete workflow for new user's first query"""
        # Setup repositories
        user_repo = UserMappingRepository(test_db_manager)
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        audit_repo = AuditLogRepository(test_db_manager)
        
        # Create user mapping
        await user_repo.create_or_update_mapping(
            slack_user_id="U123456789",
            internal_user_id="new_user",
            ldap_id="new.user",
            email="new.user@company.com",
            full_name="New User",
            roles=["analyst"],
            permissions=["query_execute", "query_view"]
        )
        
        # Setup auth system
        db_provider = DatabaseAuthProvider(user_repo)
        auth_system = AuthSystem([db_provider])
        
        # Setup mock Goose client
        mock_goose_client = AsyncMock(spec=GooseQueryExpertClient)
        successful_result = QueryResult(
            query_id="new_user_query_123",
            sql="SELECT COUNT(*) FROM users WHERE created_at >= '2024-01-01'",
            columns=["user_count"],
            rows=[[150]],
            row_count=1,
            execution_time=0.75,
            success=True,
            metadata={
                "table_search": {"tables_found": 1, "primary_table": "users"},
                "similar_queries": {"queries_found": 3},
                "experts": [
                    {"user_name": "data_expert", "reason": "frequent user of users table"}
                ]
            }
        )
        mock_goose_client.process_user_question.return_value = successful_result
        
        # Setup mock Slack app
        mock_slack_app = AsyncMock()
        mock_slack_client = AsyncMock()
        mock_slack_client.auth_test.return_value = {"user_id": "B123456789"}
        mock_slack_client.chat_update.return_value = {"ts": "1234567890.123457"}
        
        # Create bot instance
        bot = GooseSlackBot()
        bot.auth_system = auth_system
        bot.goose_client = mock_goose_client
        bot.session_repo = session_repo
        bot.query_repo = query_repo
        bot.audit_repo = audit_repo
        
        # Simulate Slack message event
        event = {
            "user": "U123456789",
            "channel": "D123456789",  # DM channel
            "text": "How many users signed up this year?",
            "ts": "1234567890.123456",
            "channel_type": "im"
        }
        
        say_mock = AsyncMock()
        say_mock.return_value = {"ts": "1234567890.123456"}
        
        # Process the message
        await bot._process_query_request(event, say_mock, mock_slack_client)
        
        # Verify user was authenticated
        user_context = await auth_system.authenticate_user("U123456789")
        assert user_context is not None
        assert user_context.user_id == "new_user"
        
        # Verify session was created
        session = await session_repo.get_session("new_user", "D123456789")
        assert session is not None
        assert session["user_id"] == "new_user"
        assert session["slack_user_id"] == "U123456789"
        
        # Verify query was processed
        mock_goose_client.process_user_question.assert_called_once()
        call_args = mock_goose_client.process_user_question.call_args
        assert "How many users signed up this year?" in call_args[0]
        
        # Verify query was saved to history
        history = await query_repo.get_user_history("new_user", limit=1)
        assert len(history) == 1
        assert history[0]["query_id"] == "new_user_query_123"
        assert history[0]["success"] is True
        assert history[0]["row_count"] == 1
        
        # Verify audit logs were created
        auth_log = await test_db_manager.execute_one(
            "SELECT * FROM audit_logs WHERE event_type = 'query_request' AND user_id = 'new_user'"
        )
        assert auth_log is not None
        
        execute_log = await test_db_manager.execute_one(
            "SELECT * FROM audit_logs WHERE event_type = 'query_execute' AND user_id = 'new_user'"
        )
        assert execute_log is not None
        assert execute_log["result"] == "success"
    
    @async_test
    async def test_returning_user_query_workflow(self, test_db_manager):
        """Test workflow for returning user with existing session"""
        # Setup repositories
        user_repo = UserMappingRepository(test_db_manager)
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        audit_repo = AuditLogRepository(test_db_manager)
        
        # Create user mapping
        await user_repo.create_or_update_mapping(
            slack_user_id="U987654321",
            internal_user_id="returning_user",
            ldap_id="returning.user",
            email="returning.user@company.com",
            roles=["senior_analyst"],
            permissions=["query_execute", "query_view", "query_share"]
        )
        
        # Create existing session
        existing_session_id = await session_repo.create_session(
            user_id="returning_user",
            slack_user_id="U987654321",
            channel_id="C987654321",
            context={"previous_queries": 5, "preferred_format": "table"}
        )
        
        # Add some query history
        await query_repo.save_query(
            session_id=existing_session_id,
            user_id="returning_user",
            slack_user_id="U987654321",
            channel_id="C987654321",
            query_id="previous_query_1",
            original_question="What was revenue last month?",
            generated_sql="SELECT SUM(amount) FROM orders WHERE month = 'January'",
            success=True,
            execution_time=1.2,
            row_count=1
        )
        
        # Setup auth and mocks
        db_provider = DatabaseAuthProvider(user_repo)
        auth_system = AuthSystem([db_provider])
        
        mock_goose_client = AsyncMock(spec=GooseQueryExpertClient)
        large_result = QueryResult(
            query_id="returning_user_query_456",
            sql="SELECT customer_id, SUM(amount) FROM orders GROUP BY customer_id ORDER BY SUM(amount) DESC LIMIT 100",
            columns=["customer_id", "total_amount"],
            rows=[[f"cust_{i}", 1000 + i*10] for i in range(100)],
            row_count=100,
            execution_time=2.3,
            success=True,
            metadata={
                "table_search": {"tables_found": 1},
                "similar_queries": {"queries_found": 8},
                "experts": [
                    {"user_name": "sales_analyst", "reason": "orders table expert"}
                ]
            }
        )
        mock_goose_client.process_user_question.return_value = large_result
        
        # Create bot
        bot = GooseSlackBot()
        bot.auth_system = auth_system
        bot.goose_client = mock_goose_client
        bot.session_repo = session_repo
        bot.query_repo = query_repo
        bot.audit_repo = audit_repo
        bot.formatter.max_inline_rows = 10  # Force large result handling
        
        # Mock Slack interactions
        mock_slack_client = AsyncMock()
        mock_slack_client.auth_test.return_value = {"user_id": "B123456789"}
        mock_slack_client.chat_update.return_value = {"ts": "1234567890.123457"}
        mock_slack_client.files_upload_v2.return_value = {"file": {"id": "F123456"}}
        
        # Simulate query request
        event = {
            "user": "U987654321",
            "channel": "C987654321",
            "text": "Show me top 100 customers by revenue",
            "ts": "1234567890.123456",
            "channel_type": "channel"
        }
        
        say_mock = AsyncMock()
        say_mock.return_value = {"ts": "1234567890.123456"}
        
        with patch('slack_bot.settings') as mock_settings:
            mock_settings.enable_file_uploads = True
            
            await bot._process_query_request(event, say_mock, mock_slack_client)
        
        # Verify session was reused and updated
        updated_session = await session_repo.get_session("returning_user", "C987654321")
        assert updated_session is not None
        assert updated_session["id"] == existing_session_id
        
        # Verify new query was added to history
        history = await query_repo.get_user_history("returning_user", limit=5)
        assert len(history) == 2  # Previous + new query
        
        new_query = next(h for h in history if h["query_id"] == "returning_user_query_456")
        assert new_query["row_count"] == 100
        assert new_query["success"] is True
        
        # Verify file upload was triggered for large result
        mock_slack_client.files_upload_v2.assert_called_once()
    
    @async_test
    async def test_unauthorized_user_workflow(self, test_db_manager):
        """Test workflow for unauthorized user"""
        # Setup repositories without creating user mapping
        user_repo = UserMappingRepository(test_db_manager)
        session_repo = UserSessionRepository(test_db_manager)
        audit_repo = AuditLogRepository(test_db_manager)
        
        # Setup auth system
        db_provider = DatabaseAuthProvider(user_repo)
        auth_system = AuthSystem([db_provider])
        
        # Create bot
        bot = GooseSlackBot()
        bot.auth_system = auth_system
        bot.session_repo = session_repo
        bot.audit_repo = audit_repo
        
        # Simulate unauthorized user message
        event = {
            "user": "U999999999",  # Non-existent user
            "channel": "D999999999",
            "text": "Show me sensitive data",
            "ts": "1234567890.123456",
            "channel_type": "im"
        }
        
        say_mock = AsyncMock()
        client_mock = AsyncMock()
        
        await bot._process_query_request(event, say_mock, client_mock)
        
        # Verify authentication failure message was sent
        say_mock.assert_called_once()
        call_args = say_mock.call_args[1]
        assert "authenticated" in call_args["text"].lower()
        
        # Verify no session was created
        session = await session_repo.get_session("unknown_user", "D999999999")
        assert session is None
    
    @async_test
    async def test_query_error_workflow(self, test_db_manager):
        """Test workflow when query execution fails"""
        # Setup user and auth
        user_repo = UserMappingRepository(test_db_manager)
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        audit_repo = AuditLogRepository(test_db_manager)
        
        await user_repo.create_or_update_mapping(
            slack_user_id="U555555555",
            internal_user_id="error_user",
            roles=["analyst"],
            permissions=["query_execute"]
        )
        
        db_provider = DatabaseAuthProvider(user_repo)
        auth_system = AuthSystem([db_provider])
        
        # Setup mock Goose client with error result
        mock_goose_client = AsyncMock(spec=GooseQueryExpertClient)
        error_result = QueryResult(
            query_id="error_query_789",
            sql="SELECT * FROM nonexistent_table",
            columns=[],
            rows=[],
            row_count=0,
            execution_time=0.1,
            success=False,
            error_message="Table 'nonexistent_table' doesn't exist or access denied",
            metadata={}
        )
        mock_goose_client.process_user_question.return_value = error_result
        
        # Create bot
        bot = GooseSlackBot()
        bot.auth_system = auth_system
        bot.goose_client = mock_goose_client
        bot.session_repo = session_repo
        bot.query_repo = query_repo
        bot.audit_repo = audit_repo
        
        # Mock Slack client
        mock_slack_client = AsyncMock()
        mock_slack_client.auth_test.return_value = {"user_id": "B123456789"}
        mock_slack_client.chat_update.return_value = {"ts": "1234567890.123457"}
        
        # Simulate error-prone query
        event = {
            "user": "U555555555",
            "channel": "D555555555",
            "text": "SELECT * FROM secret_table",
            "ts": "1234567890.123456",
            "channel_type": "im"
        }
        
        say_mock = AsyncMock()
        say_mock.return_value = {"ts": "1234567890.123456"}
        
        await bot._process_query_request(event, say_mock, mock_slack_client)
        
        # Verify error was handled gracefully
        mock_slack_client.chat_update.assert_called_once()
        
        # Verify error query was still saved to history
        history = await query_repo.get_user_history("error_user", limit=1)
        assert len(history) == 1
        assert history[0]["success"] is False
        assert "doesn't exist" in history[0]["error_message"]
        
        # Verify error was logged in audit
        error_log = await test_db_manager.execute_one(
            "SELECT * FROM audit_logs WHERE result = 'failure' AND user_id = 'error_user'"
        )
        assert error_log is not None
    
    @async_test
    async def test_concurrent_users_workflow(self, test_db_manager):
        """Test handling multiple concurrent users"""
        # Setup multiple users
        user_repo = UserMappingRepository(test_db_manager)
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        audit_repo = AuditLogRepository(test_db_manager)
        
        users = [
            ("U111111111", "user1", "User One"),
            ("U222222222", "user2", "User Two"),
            ("U333333333", "user3", "User Three")
        ]
        
        # Create user mappings
        for slack_id, user_id, name in users:
            await user_repo.create_or_update_mapping(
                slack_user_id=slack_id,
                internal_user_id=user_id,
                full_name=name,
                roles=["analyst"],
                permissions=["query_execute"]
            )
        
        # Setup auth and mocks
        db_provider = DatabaseAuthProvider(user_repo)
        auth_system = AuthSystem([db_provider])
        
        mock_goose_client = AsyncMock(spec=GooseQueryExpertClient)
        
        # Different results for each user
        def mock_process_question(question, user_context, progress_callback=None):
            user_id = user_context.user_id
            return QueryResult(
                query_id=f"{user_id}_query_{hash(question) % 1000}",
                sql=f"SELECT COUNT(*) FROM {user_id}_table",
                columns=["count"],
                rows=[[hash(user_id) % 100]],
                row_count=1,
                execution_time=0.5,
                success=True,
                metadata={}
            )
        
        mock_goose_client.process_user_question.side_effect = mock_process_question
        
        # Create bot
        bot = GooseSlackBot()
        bot.auth_system = auth_system
        bot.goose_client = mock_goose_client
        bot.session_repo = session_repo
        bot.query_repo = query_repo
        bot.audit_repo = audit_repo
        
        # Mock Slack client
        mock_slack_client = AsyncMock()
        mock_slack_client.auth_test.return_value = {"user_id": "B123456789"}
        mock_slack_client.chat_update.return_value = {"ts": "1234567890.123457"}
        
        # Simulate concurrent requests
        async def process_user_query(slack_id, user_id, question):
            event = {
                "user": slack_id,
                "channel": f"D{slack_id[1:]}",  # Convert to DM channel
                "text": question,
                "ts": f"123456789{hash(slack_id) % 10}.123456",
                "channel_type": "im"
            }
            
            say_mock = AsyncMock()
            say_mock.return_value = {"ts": event["ts"]}
            
            await bot._process_query_request(event, say_mock, mock_slack_client)
            return user_id
        
        # Execute concurrent queries
        tasks = [
            process_user_query("U111111111", "user1", "How many orders today?"),
            process_user_query("U222222222", "user2", "What's our revenue?"),
            process_user_query("U333333333", "user3", "Show user signups")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all users were processed
        assert len(results) == 3
        assert set(results) == {"user1", "user2", "user3"}
        
        # Verify each user has their own session and query history
        for slack_id, user_id, _ in users:
            channel_id = f"D{slack_id[1:]}"
            session = await session_repo.get_session(user_id, channel_id)
            assert session is not None
            
            history = await query_repo.get_user_history(user_id, limit=1)
            assert len(history) == 1
            assert history[0]["user_id"] == user_id
        
        # Verify Goose client was called for each user
        assert mock_goose_client.process_user_question.call_count == 3
    
    @async_test
    async def test_app_mention_workflow(self, test_db_manager):
        """Test app mention in channel workflow"""
        # Setup user and auth
        user_repo = UserMappingRepository(test_db_manager)
        session_repo = UserSessionRepository(test_db_manager)
        query_repo = QueryHistoryRepository(test_db_manager)
        audit_repo = AuditLogRepository(test_db_manager)
        
        await user_repo.create_or_update_mapping(
            slack_user_id="U777777777",
            internal_user_id="mention_user",
            roles=["analyst"],
            permissions=["query_execute"]
        )
        
        db_provider = DatabaseAuthProvider(user_repo)
        auth_system = AuthSystem([db_provider])
        
        mock_goose_client = AsyncMock(spec=GooseQueryExpertClient)
        mock_goose_client.process_user_question.return_value = QueryResult(
            query_id="mention_query_999",
            sql="SELECT AVG(rating) FROM reviews",
            columns=["avg_rating"],
            rows=[[4.2]],
            row_count=1,
            execution_time=0.8,
            success=True,
            metadata={}
        )
        
        # Create bot
        bot = GooseSlackBot()
        bot.auth_system = auth_system
        bot.goose_client = mock_goose_client
        bot.session_repo = session_repo
        bot.query_repo = query_repo
        bot.audit_repo = audit_repo
        
        # Mock Slack client
        mock_slack_client = AsyncMock()
        mock_slack_client.auth_test.return_value = {"user_id": "B123456789"}
        mock_slack_client.chat_update.return_value = {"ts": "1234567890.123457"}
        
        # Simulate app mention event
        event = {
            "type": "app_mention",
            "user": "U777777777",
            "channel": "C888888888",
            "text": "<@B123456789> What's our average review rating?",
            "ts": "1234567890.123456"
        }
        
        say_mock = AsyncMock()
        say_mock.return_value = {"ts": "1234567890.123456"}
        
        await bot._handle_mention_event(event, say_mock, mock_slack_client)
        
        # Verify mention was processed
        mock_goose_client.process_user_question.assert_called_once()
        
        # Verify session was created for channel
        session = await session_repo.get_session("mention_user", "C888888888")
        assert session is not None
        
        # Verify query was saved
        history = await query_repo.get_user_history("mention_user", limit=1)
        assert len(history) == 1
        assert history[0]["channel_id"] == "C888888888"
        assert history[0]["query_id"] == "mention_query_999"


class TestSlackIntegration:
    """Test Slack-specific integrations"""
    
    @async_test
    async def test_message_formatting_integration(self):
        """Test message formatting with real Slack constraints"""
        pass
    
    @async_test
    async def test_file_upload_integration(self):
        """Test file upload integration with Slack API"""
        pass
    
    @async_test
    async def test_interactive_buttons_integration(self):
        """Test interactive button handling"""
        pass


class TestDatabaseIntegration:
    """Test database integration scenarios"""
    
    @async_test
    async def test_database_connection_recovery(self, test_db_manager):
        """Test recovery from database connection issues"""
        pass
    
    @async_test
    async def test_transaction_handling(self, test_db_manager):
        """Test transaction handling across operations"""
        pass


class TestGooseAPIIntegration:
    """Test Goose API integration scenarios"""
    
    @async_test
    async def test_api_timeout_handling(self):
        """Test handling of API timeouts"""
        pass
    
    @async_test
    async def test_api_rate_limiting(self):
        """Test handling of API rate limits"""
        pass
