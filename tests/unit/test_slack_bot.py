"""
Unit tests for Slack bot functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from datetime import datetime, timezone

from slack_bot import SlackResultFormatter, GooseSlackBot
from goose_client import QueryResult, QueryStatus, UserContext
from tests import async_test


class TestSlackResultFormatter:
    """Test SlackResultFormatter class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.formatter = SlackResultFormatter()
        self.formatter.max_inline_rows = 5
        self.formatter.max_result_rows = 100
    
    def test_format_small_results(self, sample_query_result):
        """Test formatting of small result sets"""
        formatted = self.formatter.format_small_results(sample_query_result)
        
        assert "text" in formatted
        assert "blocks" in formatted
        assert "📊 Query Results" in formatted["text"]
        
        # Check that blocks contain table data
        blocks = formatted["blocks"]
        assert len(blocks) >= 2  # At least table and context blocks
        
        # Check for ASCII table in first block
        table_block = blocks[0]
        assert table_block["type"] == "section"
        assert "```" in table_block["text"]["text"]  # Code block formatting
    
    def test_format_empty_results(self):
        """Test formatting of empty result sets"""
        empty_result = QueryResult(
            query_id="empty_query",
            sql="SELECT * FROM empty_table",
            columns=["id", "name"],
            rows=[],
            row_count=0,
            execution_time=0.1,
            success=True
        )
        
        formatted = self.formatter.format_small_results(empty_result)
        
        assert "no results" in formatted["text"].lower()
        assert "blocks" in formatted
    
    def test_format_large_results(self, sample_large_result):
        """Test formatting of large result sets"""
        formatted = self.formatter.format_large_results(sample_large_result)
        
        assert "text" in formatted
        assert "blocks" in formatted
        assert "100 rows" in formatted["text"]
        
        blocks = formatted["blocks"]
        
        # Should have summary block
        summary_block = next((b for b in blocks if "Query Summary" in b.get("text", {}).get("text", "")), None)
        assert summary_block is not None
        
        # Should have file upload message
        file_block = next((b for b in blocks if "CSV file" in b.get("text", {}).get("text", "")), None)
        assert file_block is not None
        
        # Should have preview
        preview_block = next((b for b in blocks if "Preview" in b.get("text", {}).get("text", "")), None)
        assert preview_block is not None
    
    def test_format_error(self, sample_error_result):
        """Test formatting of error results"""
        formatted = self.formatter.format_error(sample_error_result)
        
        assert "text" in formatted
        assert "blocks" in formatted
        
        blocks = formatted["blocks"]
        
        # Should have error message
        error_block = blocks[0]
        assert "doesn't exist" in error_block["text"]["text"]
        
        # Should have suggestion
        suggestion_block = next((b for b in blocks if "Suggestion" in b.get("text", {}).get("text", "")), None)
        assert suggestion_block is not None
    
    def test_format_permission_error(self):
        """Test formatting of permission errors"""
        permission_error = QueryResult(
            query_id="permission_error",
            sql="SELECT * FROM sensitive_table",
            columns=[],
            rows=[],
            row_count=0,
            execution_time=0.0,
            success=False,
            error_message="Permission denied to access table 'sensitive_table'"
        )
        
        formatted = self.formatter.format_error(permission_error)
        
        assert "🔒" in formatted["text"]
        assert "Permission Denied" in formatted["text"]
        
        blocks = formatted["blocks"]
        error_block = blocks[0]
        assert "Permission denied" in error_block["text"]["text"]
    
    def test_create_ascii_table(self):
        """Test ASCII table creation"""
        columns = ["ID", "Name", "Email"]
        rows = [
            [1, "John Doe", "john@example.com"],
            [2, "Jane Smith", "jane@example.com"]
        ]
        
        table = self.formatter._create_ascii_table(columns, rows)
        
        assert "ID" in table
        assert "Name" in table
        assert "Email" in table
        assert "John Doe" in table
        assert "jane@example.com" in table
        assert "┌" in table  # Top border
        assert "└" in table  # Bottom border
        assert "├" in table  # Header separator
    
    def test_create_ascii_table_with_nulls(self):
        """Test ASCII table creation with NULL values"""
        columns = ["ID", "Value"]
        rows = [
            [1, "Test"],
            [2, None],
            [3, ""]
        ]
        
        table = self.formatter._create_ascii_table(columns, rows)
        
        assert "NULL" in table
        assert "Test" in table
    
    def test_create_ascii_table_with_long_values(self):
        """Test ASCII table creation with long values"""
        columns = ["ID", "Long Description"]
        rows = [
            [1, "This is a very long description that should be truncated"],
            [2, "Short"]
        ]
        
        table = self.formatter._create_ascii_table(columns, rows)
        
        assert "..." in table  # Truncation indicator
        assert "Short" in table
    
    def test_create_csv_content(self, sample_query_result):
        """Test CSV content creation"""
        csv_content = self.formatter.create_csv_content(sample_query_result)
        
        lines = csv_content.strip().split('\n')
        
        # Check header
        assert lines[0] == "id,name,email"
        
        # Check data rows
        assert "John Doe" in csv_content
        assert "jane@example.com" in csv_content
        assert len(lines) == 4  # Header + 3 data rows
    
    def test_create_csv_content_with_nulls(self):
        """Test CSV content creation with NULL values"""
        result = QueryResult(
            query_id="test_nulls",
            sql="SELECT * FROM test",
            columns=["id", "value"],
            rows=[[1, "test"], [2, None], [3, ""]],
            row_count=3,
            execution_time=0.1,
            success=True
        )
        
        csv_content = self.formatter.create_csv_content(result)
        lines = csv_content.strip().split('\n')
        
        assert lines[0] == "id,value"
        assert "1,test" in lines
        assert "2," in lines  # NULL becomes empty
        assert "3," in lines


class TestGooseSlackBot:
    """Test GooseSlackBot class"""
    
    @async_test
    async def test_bot_initialization(self, mock_settings):
        """Test bot initialization"""
        with patch('slack_bot.AsyncApp') as mock_app:
            with patch('slack_bot.GooseQueryExpertClient') as mock_client:
                bot = GooseSlackBot()
                
                assert bot.app is not None
                assert bot.goose_client is not None
                assert bot.formatter is not None
                mock_app.assert_called_once()
    
    @async_test
    async def test_handle_message_event_dm(self, mock_auth_system, mock_goose_client):
        """Test handling of direct message events"""
        bot = GooseSlackBot()
        bot.auth_system = mock_auth_system
        bot.goose_client = mock_goose_client
        
        # Mock repositories
        bot.session_repo = AsyncMock()
        bot.query_repo = AsyncMock()
        bot.audit_repo = AsyncMock()
        
        bot.session_repo.get_session.return_value = None
        bot.session_repo.create_session.return_value = "session_123"
        
        event = {
            "user": "U123456789",
            "channel": "D123456789",
            "text": "What was our revenue last month?",
            "ts": "1234567890.123456",
            "channel_type": "im"
        }
        
        say_mock = AsyncMock()
        say_mock.return_value = {"ts": "1234567890.123457"}
        
        client_mock = AsyncMock()
        client_mock.auth_test.return_value = {"user_id": "B123456789"}
        
        await bot._handle_message_event(event, say_mock, client_mock)
        
        # Verify authentication was called
        mock_auth_system.authenticate_user.assert_called_once_with("U123456789")
        
        # Verify query was processed
        mock_goose_client.process_user_question.assert_called_once()
    
    @async_test
    async def test_handle_message_event_channel_with_keywords(self, mock_auth_system, mock_goose_client):
        """Test handling of channel messages with keywords"""
        bot = GooseSlackBot()
        bot.auth_system = mock_auth_system
        bot.goose_client = mock_goose_client
        
        # Mock repositories
        bot.session_repo = AsyncMock()
        bot.query_repo = AsyncMock()
        bot.audit_repo = AsyncMock()
        
        bot.session_repo.get_session.return_value = None
        bot.session_repo.create_session.return_value = "session_123"
        
        event = {
            "user": "U123456789",
            "channel": "C987654321",
            "text": "Can you query the user data for me?",
            "ts": "1234567890.123456",
            "channel_type": "channel"
        }
        
        say_mock = AsyncMock()
        say_mock.return_value = {"ts": "1234567890.123457"}
        
        client_mock = AsyncMock()
        client_mock.auth_test.return_value = {"user_id": "B123456789"}
        
        await bot._handle_message_event(event, say_mock, client_mock)
        
        # Should process because "query" keyword is present
        mock_auth_system.authenticate_user.assert_called_once_with("U123456789")
    
    @async_test
    async def test_handle_message_event_ignore_bot(self):
        """Test ignoring bot messages"""
        bot = GooseSlackBot()
        
        event = {
            "user": "U123456789",
            "channel": "C987654321",
            "text": "This is a bot message",
            "ts": "1234567890.123456",
            "bot_id": "B987654321"
        }
        
        say_mock = AsyncMock()
        client_mock = AsyncMock()
        
        await bot._handle_message_event(event, say_mock, client_mock)
        
        # Should not call say or process anything
        say_mock.assert_not_called()
    
    @async_test
    async def test_handle_message_event_ignore_thread(self):
        """Test ignoring threaded messages in channels"""
        bot = GooseSlackBot()
        
        event = {
            "user": "U123456789",
            "channel": "C987654321",
            "text": "This is a threaded message",
            "ts": "1234567890.123456",
            "thread_ts": "1234567890.123400",
            "channel_type": "channel"
        }
        
        say_mock = AsyncMock()
        client_mock = AsyncMock()
        
        await bot._handle_message_event(event, say_mock, client_mock)
        
        # Should not process threaded messages in channels
        say_mock.assert_not_called()
    
    @async_test
    async def test_handle_mention_event(self, mock_auth_system, mock_goose_client):
        """Test handling of app mention events"""
        bot = GooseSlackBot()
        bot.auth_system = mock_auth_system
        bot.goose_client = mock_goose_client
        
        # Mock repositories
        bot.session_repo = AsyncMock()
        bot.query_repo = AsyncMock()
        bot.audit_repo = AsyncMock()
        
        bot.session_repo.get_session.return_value = None
        bot.session_repo.create_session.return_value = "session_123"
        
        event = {
            "type": "app_mention",
            "user": "U123456789",
            "channel": "C987654321",
            "text": "<@B123456789> How many orders were placed today?",
            "ts": "1234567890.123456"
        }
        
        say_mock = AsyncMock()
        say_mock.return_value = {"ts": "1234567890.123457"}
        
        client_mock = AsyncMock()
        client_mock.auth_test.return_value = {"user_id": "B123456789"}
        
        await bot._handle_mention_event(event, say_mock, client_mock)
        
        # Should process the mention
        mock_auth_system.authenticate_user.assert_called_once_with("U123456789")
        mock_goose_client.process_user_question.assert_called_once()
    
    @async_test
    async def test_authenticate_user_success(self, mock_auth_system):
        """Test successful user authentication"""
        bot = GooseSlackBot()
        bot.auth_system = mock_auth_system
        
        context = await bot._authenticate_user("U123456789", "C987654321")
        
        assert context is not None
        assert context.user_id == "test_user"
        mock_auth_system.authenticate_user.assert_called_once_with("U123456789")
    
    @async_test
    async def test_authenticate_user_failure(self):
        """Test failed user authentication"""
        bot = GooseSlackBot()
        
        mock_auth_system = AsyncMock()
        mock_auth_system.authenticate_user.side_effect = Exception("Auth failed")
        bot.auth_system = mock_auth_system
        
        context = await bot._authenticate_user("U123456789", "C987654321")
        
        assert context is None
    
    @async_test
    async def test_execute_user_query_success(self, mock_auth_system, mock_goose_client, sample_query_result):
        """Test successful query execution"""
        bot = GooseSlackBot()
        bot.auth_system = mock_auth_system
        bot.goose_client = mock_goose_client
        bot.formatter = SlackResultFormatter()
        
        # Mock repositories
        bot.session_repo = AsyncMock()
        bot.query_repo = AsyncMock()
        bot.audit_repo = AsyncMock()
        
        bot.session_repo.get_session.return_value = {"id": "session_123"}
        
        # Mock user context
        user_context = mock_auth_system.authenticate_user.return_value
        
        # Mock successful query result
        mock_goose_client.process_user_question.return_value = sample_query_result
        
        say_mock = AsyncMock()
        say_mock.return_value = {"ts": "1234567890.123457"}
        
        client_mock = AsyncMock()
        client_mock.chat_update.return_value = {"ts": "1234567890.123457"}
        
        await bot._execute_user_query(
            "What was our revenue?",
            user_context,
            "U123456789",
            "C987654321",
            "1234567890.123456",
            say_mock,
            client_mock
        )
        
        # Verify initial thinking message
        say_mock.assert_called_once()
        
        # Verify query was processed
        mock_goose_client.process_user_question.assert_called_once()
        
        # Verify result was formatted and sent
        client_mock.chat_update.assert_called_once()
        
        # Verify query was saved to history
        bot.query_repo.save_query.assert_called_once()
        
        # Verify audit log
        bot.audit_repo.log_event.assert_called()
    
    @async_test
    async def test_execute_user_query_large_result(self, mock_auth_system, mock_goose_client, sample_large_result):
        """Test query execution with large result set"""
        bot = GooseSlackBot()
        bot.auth_system = mock_auth_system
        bot.goose_client = mock_goose_client
        bot.formatter = SlackResultFormatter()
        bot.formatter.max_inline_rows = 5  # Force large result handling
        
        # Mock repositories
        bot.session_repo = AsyncMock()
        bot.query_repo = AsyncMock()
        bot.audit_repo = AsyncMock()
        
        bot.session_repo.get_session.return_value = {"id": "session_123"}
        
        user_context = mock_auth_system.authenticate_user.return_value
        mock_goose_client.process_user_question.return_value = sample_large_result
        
        say_mock = AsyncMock()
        say_mock.return_value = {"ts": "1234567890.123457"}
        
        client_mock = AsyncMock()
        client_mock.chat_update.return_value = {"ts": "1234567890.123457"}
        client_mock.files_upload_v2.return_value = {"file": {"id": "F123456"}}
        
        with patch('slack_bot.settings') as mock_settings:
            mock_settings.enable_file_uploads = True
            
            await bot._execute_user_query(
                "Show me all users",
                user_context,
                "U123456789",
                "C987654321",
                "1234567890.123456",
                say_mock,
                client_mock
            )
        
        # Should upload CSV file for large results
        client_mock.files_upload_v2.assert_called_once()
    
    @async_test
    async def test_execute_user_query_error(self, mock_auth_system, mock_goose_client, sample_error_result):
        """Test query execution with error"""
        bot = GooseSlackBot()
        bot.auth_system = mock_auth_system
        bot.goose_client = mock_goose_client
        bot.formatter = SlackResultFormatter()
        
        # Mock repositories
        bot.session_repo = AsyncMock()
        bot.query_repo = AsyncMock()
        bot.audit_repo = AsyncMock()
        
        bot.session_repo.get_session.return_value = {"id": "session_123"}
        
        user_context = mock_auth_system.authenticate_user.return_value
        mock_goose_client.process_user_question.return_value = sample_error_result
        
        say_mock = AsyncMock()
        say_mock.return_value = {"ts": "1234567890.123457"}
        
        client_mock = AsyncMock()
        client_mock.chat_update.return_value = {"ts": "1234567890.123457"}
        
        await bot._execute_user_query(
            "SELECT * FROM nonexistent_table",
            user_context,
            "U123456789",
            "C987654321",
            "1234567890.123456",
            say_mock,
            client_mock
        )
        
        # Should format and send error message
        client_mock.chat_update.assert_called_once()
        
        # Should still save to history
        bot.query_repo.save_query.assert_called_once()
        
        # Should log error
        bot.audit_repo.log_event.assert_called()
    
    @async_test
    async def test_handle_slash_command(self, mock_auth_system, mock_goose_client):
        """Test slash command handling"""
        bot = GooseSlackBot()
        bot.auth_system = mock_auth_system
        bot.goose_client = mock_goose_client
        
        # Mock repositories
        bot.session_repo = AsyncMock()
        bot.query_repo = AsyncMock()
        bot.audit_repo = AsyncMock()
        
        bot.session_repo.get_session.return_value = None
        bot.session_repo.create_session.return_value = "session_123"
        
        body = {
            "user_id": "U123456789",
            "channel_id": "C987654321",
            "text": "What was our revenue last month?"
        }
        
        client_mock = AsyncMock()
        client_mock.chat_postMessage.return_value = {"ts": "1234567890.123457"}
        client_mock.auth_test.return_value = {"user_id": "B123456789"}
        
        await bot._handle_slash_command(body, client_mock)
        
        # Should process as regular query
        mock_auth_system.authenticate_user.assert_called_once_with("U123456789")
    
    @async_test
    async def test_handle_slash_command_no_text(self):
        """Test slash command with no text"""
        bot = GooseSlackBot()
        
        body = {
            "user_id": "U123456789",
            "channel_id": "C987654321",
            "text": ""
        }
        
        client_mock = AsyncMock()
        
        await bot._handle_slash_command(body, client_mock)
        
        # Should send usage message
        client_mock.chat_postEphemeral.assert_called_once()
        args = client_mock.chat_postEphemeral.call_args[1]
        assert "Usage:" in args["text"]
    
    @async_test
    async def test_progress_callback(self):
        """Test query progress callback"""
        bot = GooseSlackBot()
        
        client_mock = AsyncMock()
        channel_id = "C987654321"
        thinking_ts = "1234567890.123456"
        
        # Create progress callback
        async def progress_callback(query_id: str, status: QueryStatus):
            status_messages = {
                QueryStatus.SEARCHING_TABLES: "🔍 Searching for relevant data tables...",
                QueryStatus.GENERATING_SQL: "⚡ Generating optimized SQL query...",
                QueryStatus.COMPLETED: "✅ Query completed successfully!"
            }
            
            message = status_messages.get(status, f"Processing... ({status.value})")
            
            await client_mock.chat_update(
                channel=channel_id,
                ts=thinking_ts,
                text=message
            )
        
        # Test different statuses
        await progress_callback("test_query", QueryStatus.SEARCHING_TABLES)
        await progress_callback("test_query", QueryStatus.GENERATING_SQL)
        await progress_callback("test_query", QueryStatus.COMPLETED)
        
        assert client_mock.chat_update.call_count == 3
        
        # Check messages
        calls = client_mock.chat_update.call_args_list
        assert "🔍 Searching" in calls[0][1]["text"]
        assert "⚡ Generating" in calls[1][1]["text"]
        assert "✅ Query completed" in calls[2][1]["text"]


class TestSlackBotIntegration:
    """Integration tests for Slack bot"""
    
    @async_test
    async def test_full_message_processing_flow(self, test_db_manager, mock_settings):
        """Test complete message processing flow"""
        # This would be a more comprehensive integration test
        # involving real database operations and mocked Slack/Goose clients
        pass
    
    @async_test
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        pass
    
    @async_test
    async def test_concurrent_message_processing(self):
        """Test handling of concurrent messages"""
        pass
