# Goose Slackbot API Documentation

This document provides comprehensive API documentation for the Goose Slackbot, including internal APIs, webhook endpoints, and integration interfaces.

## 📋 Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Slack Integration APIs](#slack-integration-apis)
4. [Goose Integration APIs](#goose-integration-apis)
5. [Database APIs](#database-apis)
6. [Admin APIs](#admin-apis)
7. [Health and Monitoring](#health-and-monitoring)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [SDK Examples](#sdk-examples)

## 🌐 API Overview

The Goose Slackbot exposes several API endpoints for different purposes:

- **Slack Webhooks**: Handle Slack events and interactions
- **Admin Interface**: Manage users, permissions, and configuration
- **Health Endpoints**: Monitor application health and metrics
- **Integration APIs**: Interface with external services

### Base URLs

- **Development**: `http://localhost:3000`
- **Production**: `https://your-domain.com`

### Content Types

All APIs accept and return JSON unless otherwise specified.

```http
Content-Type: application/json
Accept: application/json
```

## 🔐 Authentication

### Slack Event Authentication

Slack events are authenticated using the signing secret:

```python
import hmac
import hashlib
import time

def verify_slack_signature(signing_secret, timestamp, body, signature):
    """Verify Slack request signature"""
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False
    
    sig_basestring = f"v0:{timestamp}:{body}"
    computed_signature = 'v0=' + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)
```

### Admin API Authentication

Admin APIs use JWT tokens:

```http
Authorization: Bearer <jwt-token>
```

### API Key Authentication

Some endpoints support API key authentication:

```http
X-API-Key: <api-key>
```

## 📱 Slack Integration APIs

### Event Webhook

Handles all Slack events (messages, mentions, interactions).

```http
POST /slack/events
Content-Type: application/json
X-Slack-Signature: v0=<signature>
X-Slack-Request-Timestamp: <timestamp>
```

**Request Body**:
```json
{
  "token": "verification-token",
  "team_id": "T1234567890",
  "api_app_id": "A1234567890",
  "event": {
    "type": "message",
    "user": "U1234567890",
    "text": "What was our revenue last month?",
    "channel": "C1234567890",
    "ts": "1234567890.123456"
  },
  "type": "event_callback",
  "event_id": "Ev1234567890",
  "event_time": 1234567890
}
```

**Response**:
```json
{
  "status": "ok",
  "message": "Event processed successfully"
}
```

### Interactive Components

Handles button clicks and interactive elements.

```http
POST /slack/interactive
Content-Type: application/x-www-form-urlencoded
X-Slack-Signature: v0=<signature>
X-Slack-Request-Timestamp: <timestamp>
```

**Request Body** (URL-encoded):
```
payload={"type":"block_actions","user":{"id":"U1234567890"},"actions":[{"action_id":"refine_query","value":"query-123"}]}
```

**Response**:
```json
{
  "response_type": "ephemeral",
  "text": "Processing your request..."
}
```

### Slash Commands

Handles `/goose-query` slash command.

```http
POST /slack/commands
Content-Type: application/x-www-form-urlencoded
X-Slack-Signature: v0=<signature>
X-Slack-Request-Timestamp: <timestamp>
```

**Request Body** (URL-encoded):
```
token=verification-token&
team_id=T1234567890&
team_domain=company&
channel_id=C1234567890&
channel_name=general&
user_id=U1234567890&
user_name=john.doe&
command=/goose-query&
text=What was our revenue last month?&
response_url=https://hooks.slack.com/commands/...
```

**Response**:
```json
{
  "response_type": "in_channel",
  "text": "🤔 Processing your query...",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "🤔 Let me search for the best way to answer that..."
      }
    }
  ]
}
```

## 🦆 Goose Integration APIs

### Query Processing

Internal API for processing queries through Goose.

```python
from goose_client import GooseQueryExpertClient, UserContext

# Initialize client
client = GooseQueryExpertClient()

# Create user context
user_context = UserContext(
    user_id="user-123",
    slack_user_id="U1234567890",
    email="user@company.com",
    permissions=["query_execute"],
    ldap_id="jdoe"
)

# Process query
result = await client.process_user_question(
    question="What was our revenue last month?",
    user_context=user_context,
    progress_callback=progress_callback
)
```

### Query Result Structure

```python
class QueryResult:
    query_id: str
    sql: str
    success: bool
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time: float
    error_message: Optional[str]
    experts: List[Dict[str, str]]
    metadata: Dict[str, Any]
```

### Progress Callbacks

```python
async def progress_callback(query_id: str, status: QueryStatus):
    """Handle query progress updates"""
    status_messages = {
        QueryStatus.SEARCHING_TABLES: "🔍 Searching for relevant tables...",
        QueryStatus.SEARCHING_QUERIES: "📊 Looking for similar queries...",
        QueryStatus.GENERATING_SQL: "⚡ Generating SQL...",
        QueryStatus.EXECUTING: "🏃 Executing query...",
        QueryStatus.COMPLETED: "✅ Completed!",
        QueryStatus.FAILED: "❌ Failed"
    }
    
    # Update Slack message with progress
    await update_slack_message(query_id, status_messages[status])
```

## 🗄️ Database APIs

### User Management

#### Get User
```python
from database import UserMappingRepository

repo = UserMappingRepository(db_manager)

# Get user by Slack ID
user = await repo.get_user_by_slack_id("U1234567890")

# Get user by email
user = await repo.get_user_by_email("user@company.com")
```

#### Create User
```python
user_id = await repo.create_user(
    slack_user_id="U1234567890",
    email="user@company.com",
    ldap_id="jdoe",
    permissions=["query_execute"],
    metadata={"department": "engineering"}
)
```

#### Update User
```python
await repo.update_user(
    user_id=user_id,
    permissions=["query_execute", "query_share"],
    metadata={"department": "data"}
)
```

### Session Management

#### Create Session
```python
from database import UserSessionRepository

repo = UserSessionRepository(db_manager)

session_id = await repo.create_session(
    user_id="user-123",
    slack_user_id="U1234567890",
    channel_id="C1234567890"
)
```

#### Get Session
```python
session = await repo.get_session("user-123", "C1234567890")
```

### Query History

#### Save Query
```python
from database import QueryHistoryRepository

repo = QueryHistoryRepository(db_manager)

await repo.save_query(
    session_id=session_id,
    user_id="user-123",
    slack_user_id="U1234567890",
    channel_id="C1234567890",
    query_id="query-456",
    original_question="What was our revenue?",
    generated_sql="SELECT SUM(amount) FROM sales...",
    query_result=result_dict,
    execution_time=2.5,
    row_count=1,
    success=True
)
```

#### Get Query History
```python
# Get user's query history
history = await repo.get_user_query_history("user-123", limit=10)

# Get session query history
history = await repo.get_session_query_history(session_id, limit=5)

# Search query history
history = await repo.search_query_history(
    user_id="user-123",
    search_term="revenue",
    limit=10
)
```

### Audit Logging

#### Log Event
```python
from database import AuditLogRepository

repo = AuditLogRepository(db_manager)

await repo.log_event(
    event_type="query_execute",
    user_id="user-123",
    slack_user_id="U1234567890",
    channel_id="C1234567890",
    action="query_complete",
    result="success",
    resource="query-456",
    event_data={"execution_time": 2.5},
    ip_address="192.168.1.100"
)
```

## 👨‍💼 Admin APIs

### User Management Endpoints

#### List Users
```http
GET /api/admin/users
Authorization: Bearer <jwt-token>
```

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `search`: Search term
- `permissions`: Filter by permissions

**Response**:
```json
{
  "users": [
    {
      "id": "user-123",
      "slack_user_id": "U1234567890",
      "email": "user@company.com",
      "ldap_id": "jdoe",
      "permissions": ["query_execute"],
      "created_at": "2023-01-01T00:00:00Z",
      "last_active": "2023-12-01T12:00:00Z",
      "is_active": true
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

#### Create User
```http
POST /api/admin/users
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "slack_user_id": "U1234567890",
  "email": "user@company.com",
  "ldap_id": "jdoe",
  "permissions": ["query_execute"],
  "metadata": {
    "department": "engineering"
  }
}
```

**Response**:
```json
{
  "id": "user-123",
  "message": "User created successfully"
}
```

#### Update User
```http
PUT /api/admin/users/{user_id}
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "permissions": ["query_execute", "query_share"],
  "is_active": true,
  "metadata": {
    "department": "data"
  }
}
```

#### Delete User
```http
DELETE /api/admin/users/{user_id}
Authorization: Bearer <jwt-token>
```

### Query Management Endpoints

#### Get Query Statistics
```http
GET /api/admin/queries/stats
Authorization: Bearer <jwt-token>
```

**Query Parameters**:
- `start_date`: Start date (ISO format)
- `end_date`: End date (ISO format)
- `user_id`: Filter by user

**Response**:
```json
{
  "total_queries": 1250,
  "successful_queries": 1100,
  "failed_queries": 150,
  "average_execution_time": 3.2,
  "most_active_users": [
    {
      "user_id": "user-123",
      "email": "user@company.com",
      "query_count": 45
    }
  ],
  "popular_tables": [
    {
      "table_name": "sales.transactions",
      "query_count": 89
    }
  ]
}
```

#### Export Query History
```http
GET /api/admin/queries/export
Authorization: Bearer <jwt-token>
```

**Query Parameters**:
- `format`: Export format (csv, json)
- `start_date`: Start date
- `end_date`: End date
- `user_id`: Filter by user

**Response**: CSV or JSON file download

### System Configuration

#### Get Configuration
```http
GET /api/admin/config
Authorization: Bearer <jwt-token>
```

**Response**:
```json
{
  "max_result_rows": 10000,
  "max_inline_rows": 10,
  "query_timeout_seconds": 300,
  "rate_limit_per_user_per_minute": 10,
  "enable_query_history": true,
  "enable_interactive_buttons": true,
  "enable_file_uploads": true
}
```

#### Update Configuration
```http
PUT /api/admin/config
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "max_result_rows": 15000,
  "query_timeout_seconds": 600
}
```

## 🏥 Health and Monitoring

### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "goose": "healthy",
    "slack": "healthy"
  },
  "uptime": 86400
}
```

### Detailed Health Check
```http
GET /health/detailed
```

**Response**:
```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time": 12,
      "details": {
        "pool_size": 10,
        "active_connections": 3
      }
    },
    "redis": {
      "status": "healthy",
      "response_time": 5,
      "details": {
        "memory_usage": "15MB",
        "connected_clients": 2
      }
    },
    "goose": {
      "status": "healthy",
      "response_time": 45,
      "details": {
        "version": "1.2.0",
        "active_queries": 2
      }
    }
  }
}
```

### Metrics Endpoint
```http
GET /metrics
```

**Response** (Prometheus format):
```
# HELP goose_slackbot_queries_total Total number of queries processed
# TYPE goose_slackbot_queries_total counter
goose_slackbot_queries_total{status="success"} 1100
goose_slackbot_queries_total{status="failure"} 150

# HELP goose_slackbot_query_duration_seconds Query execution duration
# TYPE goose_slackbot_query_duration_seconds histogram
goose_slackbot_query_duration_seconds_bucket{le="1.0"} 450
goose_slackbot_query_duration_seconds_bucket{le="5.0"} 980
goose_slackbot_query_duration_seconds_bucket{le="10.0"} 1200
goose_slackbot_query_duration_seconds_bucket{le="+Inf"} 1250

# HELP goose_slackbot_active_users Current number of active users
# TYPE goose_slackbot_active_users gauge
goose_slackbot_active_users 25
```

## ❌ Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    },
    "timestamp": "2023-12-01T12:00:00Z",
    "request_id": "req-123456"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `AUTHENTICATION_ERROR` | 401 | Invalid or missing authentication |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | External service unavailable |

### Slack-Specific Errors

```json
{
  "response_type": "ephemeral",
  "text": "❌ Error: You don't have permission to execute queries",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "🔒 *Permission Denied*\nContact your admin to request query execution permissions."
      }
    }
  ]
}
```

## 🚦 Rate Limiting

### Rate Limit Headers

All API responses include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 60
```

### Rate Limit Configuration

```python
# Per-user rate limits
RATE_LIMIT_PER_USER_PER_MINUTE = 10
RATE_LIMIT_PER_USER_PER_HOUR = 100

# Global rate limits
RATE_LIMIT_GLOBAL_PER_MINUTE = 1000
RATE_LIMIT_GLOBAL_PER_HOUR = 10000

# Admin API rate limits
ADMIN_API_RATE_LIMIT = 100  # per minute
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 10,
      "window": 60,
      "retry_after": 45
    }
  }
}
```

## 💻 SDK Examples

### Python SDK

```python
import asyncio
from goose_slackbot_client import GooseSlackbotClient

# Initialize client
client = GooseSlackbotClient(
    base_url="https://your-domain.com",
    api_key="your-api-key"
)

async def main():
    # Get user information
    user = await client.get_user("U1234567890")
    print(f"User: {user['email']}")
    
    # Get query history
    history = await client.get_query_history(
        user_id=user['id'],
        limit=10
    )
    
    # Get system health
    health = await client.get_health()
    print(f"System status: {health['status']}")

asyncio.run(main())
```

### JavaScript SDK

```javascript
const { GooseSlackbotClient } = require('goose-slackbot-client');

const client = new GooseSlackbotClient({
  baseUrl: 'https://your-domain.com',
  apiKey: 'your-api-key'
});

async function main() {
  try {
    // Get user information
    const user = await client.getUser('U1234567890');
    console.log(`User: ${user.email}`);
    
    // Get query statistics
    const stats = await client.getQueryStats({
      startDate: '2023-01-01',
      endDate: '2023-12-31'
    });
    
    console.log(`Total queries: ${stats.totalQueries}`);
  } catch (error) {
    console.error('API Error:', error.message);
  }
}

main();
```

### cURL Examples

#### Create User
```bash
curl -X POST https://your-domain.com/api/admin/users \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slack_user_id": "U1234567890",
    "email": "user@company.com",
    "permissions": ["query_execute"]
  }'
```

#### Get Query Statistics
```bash
curl -X GET "https://your-domain.com/api/admin/queries/stats?start_date=2023-01-01&end_date=2023-12-31" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

#### Health Check
```bash
curl -X GET https://your-domain.com/health
```

## 🔧 Integration Examples

### Webhook Integration

```python
from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/webhook/query-complete', methods=['POST'])
def handle_query_complete():
    """Handle query completion webhook"""
    data = request.json
    
    # Process query completion
    query_id = data['query_id']
    success = data['success']
    user_id = data['user_id']
    
    if success:
        # Send notification to data team
        send_slack_notification(
            channel="#data-team",
            message=f"Query {query_id} completed successfully for user {user_id}"
        )
    
    return {"status": "ok"}

def send_slack_notification(channel, message):
    """Send Slack notification"""
    webhook_url = "https://hooks.slack.com/services/..."
    requests.post(webhook_url, json={
        "channel": channel,
        "text": message
    })
```

### Custom Authentication Provider

```python
from auth import AuthProvider

class CustomAuthProvider(AuthProvider):
    """Custom authentication provider"""
    
    async def authenticate_user(self, slack_user_id: str) -> Optional[UserContext]:
        """Authenticate user against custom system"""
        
        # Call your authentication service
        response = await self.http_client.get(
            f"https://auth.company.com/api/users/{slack_user_id}"
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return UserContext(
                user_id=user_data['id'],
                slack_user_id=slack_user_id,
                email=user_data['email'],
                permissions=user_data['permissions'],
                ldap_id=user_data['ldap_id']
            )
        
        return None
```

## 📚 Additional Resources

- [Slack API Documentation](https://api.slack.com/)
- [Goose Query Expert Documentation](https://github.com/block/goose)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

For more detailed examples and advanced usage, see the `/examples` directory in the repository.
