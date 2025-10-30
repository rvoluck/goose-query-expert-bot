"""
Unit tests for Goose Query Expert client
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from datetime import datetime, timezone

from goose_client import (
    GooseQueryExpertClient, QueryResult, QueryStatus, UserContext,
    GooseAPIError, QueryTimeoutError
)
from tests import async_test


class TestQueryResult:
    """Test QueryResult class"""
    
    def test_query_result_creation(self):
        """Test QueryResult creation"""
        result = QueryResult(
            query_id="test_query_123",
            sql="SELECT COUNT(*) FROM users",
            columns=["count"],
            rows=[[42]],
            row_count=1,
            execution_time=0.5,
            success=True,
            metadata={"test": "data"}
        )
        
        assert result.query_id == "test_query_123"
        assert result.sql == "SELECT COUNT(*) FROM users"
        assert result.columns == ["count"]
        assert result.rows == [[42]]
        assert result.row_count == 1
        assert result.execution_time == 0.5
        assert result.success is True
        assert result.error_message is None
        assert result.metadata == {"test": "data"}
    
    def test_query_result_error(self):
        """Test QueryResult with error"""
        result = QueryResult(
            query_id="error_query",
            sql="SELECT * FROM nonexistent",
            columns=[],
            rows=[],
            row_count=0,
            execution_time=0.0,
            success=False,
            error_message="Table 'nonexistent' doesn't exist"
        )
        
        assert result.success is False
        assert result.error_message == "Table 'nonexistent' doesn't exist"
        assert result.row_count == 0
    
    def test_query_result_to_dict(self):
        """Test QueryResult serialization"""
        result = QueryResult(
            query_id="test_query",
            sql="SELECT 1",
            columns=["value"],
            rows=[[1]],
            row_count=1,
            execution_time=0.1,
            success=True,
            metadata={"experts": []}
        )
        
        data = result.to_dict()
        
        assert data["query_id"] == "test_query"
        assert data["sql"] == "SELECT 1"
        assert data["columns"] == ["value"]
        assert data["rows"] == [[1]]
        assert data["success"] is True
        assert data["metadata"] == {"experts": []}
    
    def test_query_result_from_dict(self):
        """Test QueryResult deserialization"""
        data = {
            "query_id": "test_query",
            "sql": "SELECT 1",
            "columns": ["value"],
            "rows": [[1]],
            "row_count": 1,
            "execution_time": 0.1,
            "success": True,
            "error_message": None,
            "metadata": {"test": "data"}
        }
        
        result = QueryResult.from_dict(data)
        
        assert result.query_id == "test_query"
        assert result.sql == "SELECT 1"
        assert result.columns == ["value"]
        assert result.rows == [[1]]
        assert result.success is True
        assert result.metadata == {"test": "data"}


class TestUserContext:
    """Test UserContext class"""
    
    def test_user_context_creation(self):
        """Test UserContext creation"""
        context = UserContext(
            user_id="test_user",
            slack_user_id="U123456789",
            email="test@example.com",
            permissions=["query_execute"],
            ldap_id="test.user"
        )
        
        assert context.user_id == "test_user"
        assert context.slack_user_id == "U123456789"
        assert context.email == "test@example.com"
        assert context.permissions == ["query_execute"]
        assert context.ldap_id == "test.user"
    
    def test_user_context_to_dict(self):
        """Test UserContext serialization"""
        context = UserContext(
            user_id="test_user",
            slack_user_id="U123456789",
            email="test@example.com",
            permissions=["query_execute"]
        )
        
        data = context.to_dict()
        
        assert data["user_id"] == "test_user"
        assert data["slack_user_id"] == "U123456789"
        assert data["email"] == "test@example.com"
        assert data["permissions"] == ["query_execute"]


class TestGooseQueryExpertClient:
    """Test GooseQueryExpertClient class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.client = GooseQueryExpertClient()
        self.client.api_url = "http://localhost:8000"
        self.client.api_key = "test_api_key"
        self.client.timeout = 30
    
    @async_test
    async def test_process_user_question_success(self):
        """Test successful query processing"""
        mock_response_data = {
            "query_id": "test_query_123",
            "sql": "SELECT COUNT(*) FROM users",
            "columns": ["count"],
            "rows": [[42]],
            "row_count": 1,
            "execution_time": 0.5,
            "success": True,
            "metadata": {
                "table_search": {"tables_found": 1},
                "similar_queries": {"queries_found": 2},
                "experts": [{"user_name": "data_expert", "reason": "frequent user"}]
            }
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            user_context = UserContext(
                user_id="test_user",
                slack_user_id="U123456789",
                email="test@example.com"
            )
            
            result = await self.client.process_user_question(
                "How many users do we have?",
                user_context
            )
            
            assert result.success is True
            assert result.query_id == "test_query_123"
            assert result.sql == "SELECT COUNT(*) FROM users"
            assert result.row_count == 1
            assert result.execution_time == 0.5
            assert len(result.experts) == 1
            assert result.experts[0]["user_name"] == "data_expert"
    
    @async_test
    async def test_process_user_question_with_progress_callback(self):
        """Test query processing with progress callback"""
        # Mock streaming response
        mock_progress_responses = [
            {"status": "searching_tables", "message": "Searching for tables..."},
            {"status": "searching_queries", "message": "Finding similar queries..."},
            {"status": "generating_sql", "message": "Generating SQL..."},
            {"status": "executing", "message": "Executing query..."},
            {
                "status": "completed",
                "result": {
                    "query_id": "test_query_123",
                    "sql": "SELECT COUNT(*) FROM users",
                    "columns": ["count"],
                    "rows": [[42]],
                    "row_count": 1,
                    "execution_time": 0.5,
                    "success": True,
                    "metadata": {}
                }
            }
        ]
        
        async def mock_stream_response():
            for response in mock_progress_responses:
                yield json.dumps(response).encode() + b'\n'
        
        mock_response = AsyncMock()
        mock_response.content.iter_chunked.return_value = mock_stream_response()
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        progress_calls = []
        
        async def progress_callback(query_id: str, status: QueryStatus):
            progress_calls.append((query_id, status))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            user_context = UserContext(
                user_id="test_user",
                slack_user_id="U123456789"
            )
            
            result = await self.client.process_user_question(
                "How many users do we have?",
                user_context,
                progress_callback
            )
            
            assert result.success is True
            assert result.query_id == "test_query_123"
            
            # Check progress callbacks were called
            assert len(progress_calls) == 4  # All status updates except completed
            statuses = [call[1] for call in progress_calls]
            assert QueryStatus.SEARCHING_TABLES in statuses
            assert QueryStatus.SEARCHING_QUERIES in statuses
            assert QueryStatus.GENERATING_SQL in statuses
            assert QueryStatus.EXECUTING in statuses
    
    @async_test
    async def test_process_user_question_api_error(self):
        """Test API error handling"""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal Server Error"
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            user_context = UserContext(
                user_id="test_user",
                slack_user_id="U123456789"
            )
            
            with pytest.raises(GooseAPIError):
                await self.client.process_user_question(
                    "Test question",
                    user_context
                )
    
    @async_test
    async def test_process_user_question_timeout(self):
        """Test timeout handling"""
        import asyncio
        
        mock_session = AsyncMock()
        mock_session.post.side_effect = asyncio.TimeoutError()
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            user_context = UserContext(
                user_id="test_user",
                slack_user_id="U123456789"
            )
            
            with pytest.raises(QueryTimeoutError):
                await self.client.process_user_question(
                    "Test question",
                    user_context
                )
    
    @async_test
    async def test_process_user_question_invalid_response(self):
        """Test handling of invalid JSON response"""
        mock_response = AsyncMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.status = 200
        mock_response.text.return_value = "Invalid JSON response"
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            user_context = UserContext(
                user_id="test_user",
                slack_user_id="U123456789"
            )
            
            with pytest.raises(GooseAPIError):
                await self.client.process_user_question(
                    "Test question",
                    user_context
                )
    
    @async_test
    async def test_search_similar_queries(self):
        """Test searching for similar queries"""
        mock_response_data = {
            "queries": [
                {
                    "query_id": "similar_1",
                    "question": "How many users signed up?",
                    "sql": "SELECT COUNT(*) FROM users WHERE created_at >= '2024-01-01'",
                    "similarity_score": 0.85,
                    "user_name": "analyst_1"
                },
                {
                    "query_id": "similar_2",
                    "question": "What's our user count?",
                    "sql": "SELECT COUNT(*) FROM users",
                    "similarity_score": 0.92,
                    "user_name": "analyst_2"
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            results = await self.client.search_similar_queries(
                "How many users do we have?",
                limit=5
            )
            
            assert len(results) == 2
            assert results[0]["similarity_score"] == 0.85
            assert results[1]["similarity_score"] == 0.92
            assert "SELECT COUNT(*)" in results[1]["sql"]
    
    @async_test
    async def test_get_table_metadata(self):
        """Test getting table metadata"""
        mock_response_data = {
            "tables": [
                {
                    "table_name": "users",
                    "description": "User account information",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "description": "User ID"},
                        {"name": "email", "type": "VARCHAR", "description": "Email address"},
                        {"name": "created_at", "type": "TIMESTAMP", "description": "Account creation date"}
                    ],
                    "row_count": 10000,
                    "last_updated": "2024-01-15T10:30:00Z"
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            metadata = await self.client.get_table_metadata("users")
            
            assert len(metadata) == 1
            assert metadata[0]["table_name"] == "users"
            assert metadata[0]["description"] == "User account information"
            assert len(metadata[0]["columns"]) == 3
            assert metadata[0]["row_count"] == 10000
    
    @async_test
    async def test_execute_sql_query(self):
        """Test direct SQL query execution"""
        mock_response_data = {
            "query_id": "direct_query_123",
            "columns": ["id", "name", "email"],
            "rows": [
                [1, "John Doe", "john@example.com"],
                [2, "Jane Smith", "jane@example.com"]
            ],
            "row_count": 2,
            "execution_time": 0.15,
            "success": True
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            user_context = UserContext(
                user_id="test_user",
                slack_user_id="U123456789"
            )
            
            result = await self.client.execute_sql_query(
                "SELECT id, name, email FROM users LIMIT 2",
                user_context
            )
            
            assert result.success is True
            assert result.row_count == 2
            assert len(result.columns) == 3
            assert len(result.rows) == 2
            assert result.execution_time == 0.15
    
    @async_test
    async def test_get_query_experts(self):
        """Test getting query experts"""
        mock_response_data = {
            "experts": [
                {
                    "user_name": "data_expert_1",
                    "ldap_id": "expert1",
                    "email": "expert1@company.com",
                    "reason": "Frequent user of users table",
                    "query_count": 150,
                    "expertise_score": 0.95
                },
                {
                    "user_name": "data_expert_2",
                    "ldap_id": "expert2",
                    "email": "expert2@company.com",
                    "reason": "Table owner",
                    "query_count": 89,
                    "expertise_score": 0.88
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            experts = await self.client.get_query_experts(
                tables=["users", "orders"],
                limit=5
            )
            
            assert len(experts) == 2
            assert experts[0]["user_name"] == "data_expert_1"
            assert experts[0]["expertise_score"] == 0.95
            assert experts[1]["reason"] == "Table owner"
    
    @async_test
    async def test_client_configuration(self):
        """Test client configuration"""
        client = GooseQueryExpertClient(
            api_url="https://custom.api.com",
            api_key="custom_key",
            timeout=60
        )
        
        assert client.api_url == "https://custom.api.com"
        assert client.api_key == "custom_key"
        assert client.timeout == 60
    
    @async_test
    async def test_client_headers(self):
        """Test client request headers"""
        mock_session = AsyncMock()
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            user_context = UserContext(
                user_id="test_user",
                slack_user_id="U123456789"
            )
            
            # Mock response to avoid actual API call
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"query_id": "test", "success": False}
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            await self.client.process_user_question("test", user_context)
            
            # Check that headers were set correctly
            call_args = mock_session.post.call_args
            headers = call_args[1]["headers"]
            
            assert headers["Authorization"] == f"Bearer {self.client.api_key}"
            assert headers["Content-Type"] == "application/json"
            assert "User-Agent" in headers
    
    @async_test
    async def test_request_payload_structure(self):
        """Test request payload structure"""
        mock_session = AsyncMock()
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            user_context = UserContext(
                user_id="test_user",
                slack_user_id="U123456789",
                email="test@example.com",
                permissions=["query_execute"]
            )
            
            # Mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"query_id": "test", "success": False}
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            await self.client.process_user_question("Test question", user_context)
            
            # Check payload structure
            call_args = mock_session.post.call_args
            payload = json.loads(call_args[1]["data"])
            
            assert payload["question"] == "Test question"
            assert payload["user_context"]["user_id"] == "test_user"
            assert payload["user_context"]["slack_user_id"] == "U123456789"
            assert payload["user_context"]["email"] == "test@example.com"
            assert payload["user_context"]["permissions"] == ["query_execute"]


class TestGooseClientIntegration:
    """Integration tests for Goose client"""
    
    @async_test
    async def test_end_to_end_query_flow(self):
        """Test complete query flow from question to result"""
        # This would test the full flow with a real or more comprehensive mock
        pass
    
    @async_test
    async def test_error_recovery_and_retry(self):
        """Test error recovery and retry mechanisms"""
        pass
    
    @async_test
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        pass


class TestQueryStatus:
    """Test QueryStatus enum"""
    
    def test_query_status_values(self):
        """Test QueryStatus enum values"""
        assert QueryStatus.SEARCHING_TABLES.value == "searching_tables"
        assert QueryStatus.SEARCHING_QUERIES.value == "searching_queries"
        assert QueryStatus.GENERATING_SQL.value == "generating_sql"
        assert QueryStatus.EXECUTING.value == "executing"
        assert QueryStatus.COMPLETED.value == "completed"
        assert QueryStatus.FAILED.value == "failed"
    
    def test_query_status_from_string(self):
        """Test creating QueryStatus from string"""
        assert QueryStatus("searching_tables") == QueryStatus.SEARCHING_TABLES
        assert QueryStatus("executing") == QueryStatus.EXECUTING
        assert QueryStatus("completed") == QueryStatus.COMPLETED


class TestExceptionHandling:
    """Test exception classes"""
    
    def test_goose_api_error(self):
        """Test GooseAPIError exception"""
        error = GooseAPIError("API request failed", status_code=500)
        
        assert str(error) == "API request failed"
        assert error.status_code == 500
    
    def test_query_timeout_error(self):
        """Test QueryTimeoutError exception"""
        error = QueryTimeoutError("Query timed out after 30 seconds", timeout=30)
        
        assert str(error) == "Query timed out after 30 seconds"
        assert error.timeout == 30
