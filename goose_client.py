"""
Goose MCP Client for Query Expert Integration
Handles communication with Goose Query Expert via MCP protocol
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import structlog
from contextlib import asynccontextmanager

from config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class QueryStatus(Enum):
    """Query execution status"""
    PENDING = "pending"
    SEARCHING_TABLES = "searching_tables"
    SEARCHING_QUERIES = "searching_queries"
    GENERATING_SQL = "generating_sql"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueryResult:
    """Structure for query execution results"""
    query_id: str
    sql: str
    rows: List[List[Any]]
    columns: List[str]
    row_count: int
    execution_time: float
    status: QueryStatus
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    experts: Optional[List[Dict[str, str]]] = None
    similar_tables: Optional[List[Dict[str, str]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @property
    def success(self) -> bool:
        """Check if query was successful"""
        return self.status == QueryStatus.COMPLETED and self.error_message is None


@dataclass
class UserContext:
    """User context for query execution"""
    user_id: str
    slack_user_id: str
    email: Optional[str] = None
    permissions: List[str] = None
    ldap_id: Optional[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []


class MockGooseClient:
    """Mock Goose client for testing and development"""
    
    async def find_table_metadata(self, search_text: str, **kwargs) -> Dict[str, Any]:
        """Mock table metadata search"""
        await asyncio.sleep(settings.mock_delay_seconds)
        
        return {
            "tables": [
                {
                    "table_name": "ANALYTICS.SALES.REVENUE_BY_CATEGORY",
                    "description": "Daily revenue aggregated by product category",
                    "columns": ["date", "product_category", "revenue", "transaction_count"],
                    "verification_status": "VERIFIED",
                    "total_users_recent": 25
                },
                {
                    "table_name": "ANALYTICS.SALES.CUSTOMER_METRICS", 
                    "description": "Customer acquisition and retention metrics",
                    "columns": ["customer_id", "acquisition_date", "ltv", "churn_risk"],
                    "verification_status": "VERIFIED",
                    "total_users_recent": 18
                }
            ]
        }
    
    async def search_similar_queries(self, search_text: str, **kwargs) -> Dict[str, Any]:
        """Mock similar query search"""
        await asyncio.sleep(settings.mock_delay_seconds)
        
        return {
            "queries": [
                {
                    "query_text": "SELECT product_category, SUM(revenue) FROM ANALYTICS.SALES.REVENUE_BY_CATEGORY GROUP BY product_category",
                    "user_name": "john.doe",
                    "query_description": "Revenue analysis by product category",
                    "similarity_score": 0.95
                },
                {
                    "query_text": "SELECT DATE_TRUNC('month', date) as month, SUM(revenue) FROM ANALYTICS.SALES.REVENUE_BY_CATEGORY GROUP BY month",
                    "user_name": "jane.smith", 
                    "query_description": "Monthly revenue trends",
                    "similarity_score": 0.87
                }
            ]
        }
    
    async def execute_query(self, sql: str, **kwargs) -> Dict[str, Any]:
        """Mock query execution"""
        await asyncio.sleep(settings.mock_delay_seconds)
        
        # Generate mock data based on query
        if "revenue" in sql.lower():
            return {
                "columns": ["product_category", "total_revenue", "transaction_count"],
                "rows": [
                    ["Electronics", 1250000.50, 15420],
                    ["Clothing", 890000.25, 22100],
                    ["Home & Garden", 675000.75, 8930],
                    ["Books", 234000.00, 12500]
                ],
                "row_count": 4,
                "execution_time": 2.34
            }
        else:
            return {
                "columns": ["id", "name", "value"],
                "rows": [
                    [1, "Sample Data", 100.0],
                    [2, "Test Record", 200.0]
                ],
                "row_count": 2,
                "execution_time": 1.23
            }


class GooseMCPClient:
    """MCP client for communicating with Goose Query Expert"""
    
    def __init__(self):
        self.base_url = settings.goose_mcp_server_url
        self.timeout = settings.goose_mcp_timeout
        self.max_concurrent = settings.goose_max_concurrent_queries
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._session_pool = {}
        self._health_check_interval = 30
        self._last_health_check = 0
        
        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5)
        )
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def health_check(self) -> bool:
        """Check if Goose MCP server is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False
    
    async def _ensure_healthy(self):
        """Ensure the server is healthy before making requests"""
        current_time = time.time()
        if current_time - self._last_health_check > self._health_check_interval:
            if not await self.health_check():
                raise ConnectionError("Goose MCP server is not healthy")
            self._last_health_check = current_time
    
    async def _make_mcp_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Make an MCP tool call"""
        await self._ensure_healthy()
        
        payload = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": parameters
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/mcp",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            if "error" in result:
                raise Exception(f"MCP error: {result['error']}")
            
            return result.get("result", {})
            
        except httpx.TimeoutException:
            raise TimeoutError(f"MCP call to {tool_name} timed out after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error("MCP call failed", tool=tool_name, error=str(e))
            raise
    
    async def find_table_metadata(self, search_text: str, **kwargs) -> Dict[str, Any]:
        """Find relevant table metadata using Query Expert"""
        parameters = {
            "search_text": search_text,
            "limit": kwargs.get("limit", "5"),
            "table_verification_status": kwargs.get("table_verification_status", "VERIFIED"),
            "table_type": kwargs.get("table_type"),
            "brand": kwargs.get("brand"),
            "table_database": kwargs.get("table_database"),
            "table_schema": kwargs.get("table_schema"),
            "table_owner": kwargs.get("table_owner")
        }
        
        # Remove None values
        parameters = {k: v for k, v in parameters.items() if v is not None}
        
        return await self._make_mcp_call("queryexpert__find_table_meta_data", parameters)
    
    async def search_similar_queries(self, search_text: str, **kwargs) -> Dict[str, Any]:
        """Search for similar queries using Query Expert"""
        parameters = {
            "search_text": search_text,
            "limit": kwargs.get("limit", "5"),
            "user_name": kwargs.get("user_name"),
            "table_names": kwargs.get("table_names"),
            "query_source": kwargs.get("query_source")
        }
        
        # Remove None values
        parameters = {k: v for k, v in parameters.items() if v is not None}
        
        return await self._make_mcp_call("queryexpert__query_expert_search", parameters)
    
    async def execute_query(self, sql: str, **kwargs) -> Dict[str, Any]:
        """Execute SQL query using Query Expert"""
        parameters = {
            "query": sql,
            "database": kwargs.get("database"),
            "schema": kwargs.get("schema"),
            "warehouse": kwargs.get("warehouse")
        }
        
        # Remove None values
        parameters = {k: v for k, v in parameters.items() if v is not None}
        
        return await self._make_mcp_call("queryexpert__execute_query", parameters)
    
    async def check_permissions(self, table_list: List[str]) -> Dict[str, Any]:
        """Check table access permissions"""
        parameters = {"table_list": table_list}
        return await self._make_mcp_call("queryexpert__check_permissions", parameters)


class GooseQueryExpertClient:
    """High-level client for Goose Query Expert operations"""
    
    def __init__(self):
        if settings.mock_mode:
            self.client = MockGooseClient()
        else:
            self.client = GooseMCPClient()
        
        self._active_queries = {}
        self._query_counter = 0
    
    def _generate_query_id(self) -> str:
        """Generate unique query ID"""
        self._query_counter += 1
        return f"query_{int(time.time())}_{self._query_counter}"
    
    async def process_user_question(
        self, 
        question: str, 
        user_context: UserContext,
        progress_callback: Optional[callable] = None
    ) -> QueryResult:
        """
        Process user question through complete Query Expert pipeline
        """
        query_id = self._generate_query_id()
        start_time = time.time()
        
        logger.info("Processing user question", 
                   query_id=query_id, 
                   user_id=user_context.user_id,
                   question=question[:100])
        
        try:
            # Step 1: Search for relevant tables
            if progress_callback:
                await progress_callback(query_id, QueryStatus.SEARCHING_TABLES)
            
            table_search = await self.client.find_table_metadata(
                search_text=question,
                limit="5",
                table_verification_status="VERIFIED"
            )
            
            # Step 2: Search for similar queries
            if progress_callback:
                await progress_callback(query_id, QueryStatus.SEARCHING_QUERIES)
            
            similar_queries = await self.client.search_similar_queries(
                search_text=question,
                limit="3",
                user_name=user_context.ldap_id
            )
            
            # Step 3: Generate SQL query
            if progress_callback:
                await progress_callback(query_id, QueryStatus.GENERATING_SQL)
            
            generated_sql = await self._generate_sql_from_context(
                question, table_search, similar_queries
            )
            
            # Step 4: Execute query
            if progress_callback:
                await progress_callback(query_id, QueryStatus.EXECUTING)
            
            execution_result = await self.client.execute_query(
                sql=generated_sql,
                warehouse=settings.snowflake_warehouse
            )
            
            # Step 5: Process results
            execution_time = time.time() - start_time
            
            result = QueryResult(
                query_id=query_id,
                sql=generated_sql,
                rows=execution_result.get("rows", []),
                columns=execution_result.get("columns", []),
                row_count=execution_result.get("row_count", 0),
                execution_time=execution_time,
                status=QueryStatus.COMPLETED,
                metadata={
                    "table_search": table_search,
                    "similar_queries": similar_queries,
                    "user_context": {
                        "user_id": user_context.user_id,
                        "permissions": user_context.permissions
                    }
                },
                experts=self._extract_experts(table_search, similar_queries),
                similar_tables=self._extract_similar_tables(table_search)
            )
            
            if progress_callback:
                await progress_callback(query_id, QueryStatus.COMPLETED)
            
            logger.info("Query completed successfully",
                       query_id=query_id,
                       execution_time=execution_time,
                       row_count=result.row_count)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error("Query execution failed",
                        query_id=query_id,
                        error=error_msg,
                        execution_time=execution_time)
            
            result = QueryResult(
                query_id=query_id,
                sql="",
                rows=[],
                columns=[],
                row_count=0,
                execution_time=execution_time,
                status=QueryStatus.FAILED,
                error_message=error_msg
            )
            
            if progress_callback:
                await progress_callback(query_id, QueryStatus.FAILED)
            
            return result
    
    async def _generate_sql_from_context(
        self, 
        question: str, 
        table_search: Dict[str, Any], 
        similar_queries: Dict[str, Any]
    ) -> str:
        """Generate SQL query from search context"""
        
        # For now, use the most similar query as a starting point
        # In a full implementation, this would use an LLM to generate optimized SQL
        
        queries = similar_queries.get("queries", [])
        if queries:
            # Use the highest scoring similar query
            best_query = max(queries, key=lambda q: q.get("similarity_score", 0))
            return best_query.get("query_text", "")
        
        # Fallback: generate basic query from table metadata
        tables = table_search.get("tables", [])
        if tables:
            table = tables[0]  # Use first table
            table_name = table.get("table_name", "")
            columns = table.get("columns", [])
            
            if columns:
                column_list = ", ".join(columns[:5])  # Limit to first 5 columns
                return f"SELECT {column_list} FROM {table_name} LIMIT 10"
        
        # Ultimate fallback
        return "SELECT 1 as result"
    
    def _extract_experts(
        self, 
        table_search: Dict[str, Any], 
        similar_queries: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Extract data experts from search results"""
        experts = []
        
        # From similar queries
        for query in similar_queries.get("queries", []):
            user_name = query.get("user_name")
            if user_name:
                experts.append({
                    "user_name": user_name,
                    "reason": f"Has written similar queries: {query.get('query_description', 'N/A')}"
                })
        
        # From table metadata (owners and frequent users)
        for table in table_search.get("tables", []):
            owners = table.get("table_owners", [])
            for owner in owners:
                experts.append({
                    "user_name": owner,
                    "reason": f"Owner of {table.get('table_name', 'table')}"
                })
        
        return experts[:5]  # Limit to top 5 experts
    
    def _extract_similar_tables(self, table_search: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract similar tables from search results"""
        similar_tables = []
        
        for table in table_search.get("tables", []):
            similar_tables.append({
                "table_name": table.get("table_name", ""),
                "description": table.get("description", ""),
                "reason": f"Relevance score: {table.get('score', 0):.2f}"
            })
        
        return similar_tables
    
    async def get_query_status(self, query_id: str) -> Optional[QueryStatus]:
        """Get status of a running query"""
        return self._active_queries.get(query_id)
    
    async def cancel_query(self, query_id: str) -> bool:
        """Cancel a running query"""
        if query_id in self._active_queries:
            # In a real implementation, this would cancel the actual query
            del self._active_queries[query_id]
            return True
        return False


@asynccontextmanager
async def get_goose_client():
    """Get Goose client with proper cleanup"""
    client = GooseQueryExpertClient()
    try:
        yield client
    finally:
        if hasattr(client.client, 'close'):
            await client.client.close()


# Global client instance for reuse
_global_client = None


async def get_global_goose_client() -> GooseQueryExpertClient:
    """Get global Goose client instance"""
    global _global_client
    if _global_client is None:
        _global_client = GooseQueryExpertClient()
    return _global_client


if __name__ == "__main__":
    # Test the client
    async def test_client():
        async with get_goose_client() as client:
            user_context = UserContext(
                user_id="test_user",
                slack_user_id="U123456789",
                email="test@example.com",
                permissions=["query_execute"]
            )
            
            result = await client.process_user_question(
                "What was our revenue last month?",
                user_context
            )
            
            print(f"Query ID: {result.query_id}")
            print(f"Status: {result.status}")
            print(f"SQL: {result.sql}")
            print(f"Rows: {result.row_count}")
            print(f"Execution time: {result.execution_time:.2f}s")
            
            if result.success:
                print("✅ Query completed successfully")
            else:
                print(f"❌ Query failed: {result.error_message}")
    
    asyncio.run(test_client())
