# Slackbot Database Setup

This directory contains the complete database setup for the Slackbot application, including SQLAlchemy models, schema definitions, migration tools, and configuration management.

## 📁 Files Overview

- **`database.py`** - Main database module with SQLAlchemy models and async operations
- **`schema.sql`** - Complete SQL schema with tables, indexes, views, and functions
- **`migrations.py`** - Database migration and initialization utilities
- **`db_config.py`** - Configuration management for different environments
- **`requirements-db.txt`** - Python dependencies for database functionality

## 🗄️ Database Schema

### Core Tables

1. **`user_sessions`** - Tracks active user sessions and context
2. **`query_history`** - Stores all executed queries and results
3. **`user_mappings`** - Maps Slack users to database users and permissions
4. **`query_cache`** - Caches frequently used queries for performance
5. **`audit_logs`** - Comprehensive logging of all system activities

### Key Features

- **Async Support**: Full async/await support with asyncpg
- **Connection Pooling**: Configurable connection pools for performance
- **Caching**: Query result caching with TTL and invalidation
- **Audit Trail**: Comprehensive audit logging for security and debugging
- **Session Management**: User session tracking with context preservation
- **Migration Support**: Database versioning and migration tools

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-db.txt
```

### 2. Set Environment Variables

```bash
# Basic configuration
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/slackbot_db"

# Or individual components
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="slackbot_db"
export DB_USER="slackbot_user"
export DB_PASSWORD="your_password"
```

### 3. Initialize Database

```python
# Using the migration utility
python migrations.py init $DATABASE_URL

# Or programmatically
import asyncio
from migrations import init_database

async def setup():
    await init_database("postgresql+asyncpg://user:pass@localhost/db")

asyncio.run(setup())
```

### 4. Basic Usage

```python
import asyncio
from database import DatabaseManager, DatabaseOperations

async def example():
    # Initialize database manager
    db_manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/db")
    db_ops = DatabaseOperations(db_manager)
    
    # Create a user session
    session = await db_ops.create_user_session(
        slack_user_id="U123456789",
        slack_channel_id="C123456789",
        slack_team_id="T123456789"
    )
    
    # Log a query execution
    query_log = await db_ops.log_query_execution(
        session_id=session.id,
        original_question="Show me sales data",
        generated_query="SELECT * FROM sales",
        status="success"
    )
    
    await db_manager.close()

asyncio.run(example())
```

## ⚙️ Configuration

### Environment-Based Configuration

The system supports multiple configuration methods:

```python
from db_config import get_database_config

# From environment variables
config = get_database_config()

# Environment-specific presets
dev_config = get_database_config('development')
prod_config = get_database_config('production')

# From DATABASE_URL
config = get_database_config()  # Automatically uses DATABASE_URL if set
```

### Configuration Options

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Host | `DB_HOST` | localhost | Database host |
| Port | `DB_PORT` | 5432 | Database port |
| Database | `DB_NAME` | slackbot_db | Database name |
| Username | `DB_USER` | slackbot_user | Database username |
| Password | `DB_PASSWORD` | "" | Database password |
| Pool Size | `DB_POOL_SIZE` | 10 | Connection pool size |
| Max Overflow | `DB_MAX_OVERFLOW` | 20 | Max overflow connections |
| Query Timeout | `DB_QUERY_TIMEOUT` | 300 | Query timeout (seconds) |
| SSL Mode | `DB_SSL_MODE` | prefer | SSL connection mode |

## 🔧 Database Operations

### Session Management

```python
# Create and manage user sessions
session = await db_ops.create_user_session(
    slack_user_id="U123",
    slack_channel_id="C123",
    slack_team_id="T123",
    current_database="ANALYTICS",
    preferences={"theme": "dark"}
)

# Get active session
active_session = await db_ops.get_active_session("U123", "C123")

# Update session activity
await db_ops.update_session_activity(session.id)
```

### Query Logging

```python
# Log query execution
query_log = await db_ops.log_query_execution(
    session_id=session.id,
    original_question="What are our top products?",
    generated_query="SELECT product_name, SUM(sales) FROM products GROUP BY product_name",
    database_name="SALES_DB",
    status="success",
    execution_time_ms=1250,
    row_count=150
)

# Update query results
await db_ops.update_query_result(
    query_id=query_log.id,
    status="success",
    query_result={"data": [...], "columns": [...]},
    snowflake_query_id="01234567-89ab-cdef-0123-456789abcdef"
)
```

### Caching

```python
# Cache query results
cache_entry = await db_ops.cache_query_result(
    query_hash="abc123...",
    original_query="SELECT * FROM users",
    normalized_query="select * from users",
    result_data={"rows": [...], "columns": [...]},
    expires_at=datetime.now() + timedelta(hours=1)
)

# Retrieve cached results
cached = await db_ops.get_cached_result("abc123...")
if cached:
    print(f"Cache hit! Data: {cached.result_data}")
```

### Audit Logging

```python
# Log system events
await db_ops.log_audit_event(
    event_type="user_login",
    event_category="security",
    event_description="User logged in successfully",
    slack_user_id="U123",
    event_data={"login_method": "oauth", "ip_address": "192.168.1.1"}
)
```

## 🛠️ Migration Management

### Initialize Database

```bash
# Create database and run schema
python migrations.py init postgresql+asyncpg://user:pass@localhost/db

# Check database health
python migrations.py health postgresql+asyncpg://user:pass@localhost/db

# Clean up old records
python migrations.py cleanup postgresql+asyncpg://user:pass@localhost/db 30
```

### Custom Migrations

```python
from migrations import MigrationManager

migration_manager = MigrationManager(database_url)

# Generate new migration
migration_file = migration_manager.generate_migration(
    name="add_user_preferences",
    up_sql="ALTER TABLE user_sessions ADD COLUMN preferences JSONB DEFAULT '{}'",
    down_sql="ALTER TABLE user_sessions DROP COLUMN preferences"
)

# Apply migration
await migration_manager.apply_migration(
    version="20241027_120000_add_user_preferences",
    name="Add user preferences",
    sql="ALTER TABLE user_sessions ADD COLUMN preferences JSONB DEFAULT '{}'"
)
```

## 📊 Database Views and Functions

### Built-in Views

- **`active_sessions`** - Current active user sessions with user info
- **`query_performance_metrics`** - Hourly query performance statistics
- **`user_activity_summary`** - User activity and query statistics
- **`cache_efficiency`** - Cache hit rates and efficiency metrics

### Maintenance Functions

- **`cleanup_expired_sessions(hours)`** - Clean up old inactive sessions
- **`cleanup_expired_cache()`** - Remove expired cache entries
- **`archive_old_audit_logs(days)`** - Archive old audit log entries

```sql
-- Example usage
SELECT cleanup_expired_sessions(24);  -- Clean sessions older than 24 hours
SELECT cleanup_expired_cache();       -- Clean expired cache
SELECT archive_old_audit_logs(90);    -- Archive logs older than 90 days
```

## 🔍 Monitoring and Health Checks

### Health Check

```python
from migrations import DatabaseHealthChecker

checker = DatabaseHealthChecker(database_url)

# Basic health check
health = await checker.check_connection()
print(f"Status: {health['status']}")
print(f"Response time: {health['response_time_ms']}ms")

# Detailed statistics
stats = await checker.get_table_stats()
print(f"Active sessions: {stats['active_sessions']}")
print(f"Recent queries: {stats['recent_queries_24h']}")
```

### Performance Monitoring

```sql
-- Query performance over time
SELECT * FROM query_performance_metrics 
ORDER BY hour DESC LIMIT 24;

-- User activity summary
SELECT * FROM user_activity_summary 
ORDER BY last_activity DESC;

-- Cache efficiency
SELECT * FROM cache_efficiency 
ORDER BY day DESC LIMIT 7;
```

## 🔒 Security Considerations

### SSL Configuration

```python
# Production SSL configuration
config = DatabaseConfig(
    ssl_mode="verify-full",
    ssl_ca="/path/to/ca-cert.pem",
    ssl_cert="/path/to/client-cert.pem",
    ssl_key="/path/to/client-key.pem"
)
```

### Connection Security

- Use strong passwords and rotate them regularly
- Enable SSL/TLS for all connections
- Implement proper firewall rules
- Use connection pooling to prevent connection exhaustion
- Monitor audit logs for suspicious activity

### Data Privacy

- Audit logs capture system events but avoid logging sensitive data
- Query results can be cached but consider data sensitivity
- User sessions store context but not credentials
- Implement proper data retention policies

## 🧪 Testing

### Test Database Setup

```python
# Use testing configuration
from db_config import EnvironmentConfig

test_config = EnvironmentConfig.testing()
test_db_manager = DatabaseManager(test_config.get_async_url())

# Run tests with isolated database
async def test_user_session():
    db_ops = DatabaseOperations(test_db_manager)
    session = await db_ops.create_user_session(
        slack_user_id="TEST_USER",
        slack_channel_id="TEST_CHANNEL",
        slack_team_id="TEST_TEAM"
    )
    assert session.id is not None
    assert session.is_active is True
```

### Integration Tests

```bash
# Set up test database
export DATABASE_URL="postgresql+asyncpg://test:test@localhost/slackbot_test"
python migrations.py init $DATABASE_URL

# Run tests
pytest tests/ -v
```

## 📈 Performance Optimization

### Connection Pooling

```python
# Optimize for your workload
config = DatabaseConfig(
    pool_size=20,        # Base connections
    max_overflow=30,     # Additional connections
    pool_recycle=1800,   # Recycle every 30 minutes
    pool_pre_ping=True   # Validate connections
)
```

### Query Optimization

- Use appropriate indexes (already defined in schema)
- Monitor slow queries through audit logs
- Implement query result caching
- Use connection pooling effectively
- Consider read replicas for heavy read workloads

### Caching Strategy

```python
# Configure caching
config = DatabaseConfig(
    cache_ttl_seconds=3600,    # 1 hour default TTL
    max_cache_entries=1000     # Maximum cached queries
)
```

## 🚨 Troubleshooting

### Common Issues

1. **Connection Timeouts**
   ```python
   # Increase timeouts
   config.pool_timeout = 60
   config.query_timeout = 600
   ```

2. **Pool Exhaustion**
   ```python
   # Increase pool size or check for connection leaks
   config.pool_size = 20
   config.max_overflow = 40
   ```

3. **SSL Connection Issues**
   ```python
   # Disable SSL for development
   config.ssl_mode = "disable"
   ```

### Debugging

```python
# Enable SQL logging
config.echo_sql = True
config.log_level = "DEBUG"

# Check database health
health = await checker.check_connection()
if health['status'] != 'healthy':
    print(f"Database issue: {health['error']}")
```

## 🔄 Maintenance

### Regular Maintenance Tasks

```bash
# Daily cleanup (can be automated)
python migrations.py cleanup $DATABASE_URL 30

# Weekly health check
python migrations.py health $DATABASE_URL

# Monitor performance
psql $DATABASE_URL -c "SELECT * FROM query_performance_metrics LIMIT 10;"
```

### Automated Maintenance

The schema includes functions that can be scheduled with pg_cron or external schedulers:

```sql
-- Schedule with pg_cron (if available)
SELECT cron.schedule('cleanup-sessions', '0 2 * * *', 'SELECT cleanup_expired_sessions(24);');
SELECT cron.schedule('cleanup-cache', '30 * * * *', 'SELECT cleanup_expired_cache();');
```

## 📚 Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Alembic Migration Tool](https://alembic.sqlalchemy.org/)

## 🤝 Contributing

When contributing to the database layer:

1. Follow the existing naming conventions
2. Add appropriate indexes for new queries
3. Include audit logging for significant operations
4. Update this README for new features
5. Add tests for new database operations
6. Consider performance implications of schema changes

## 📄 License

This database schema and code is part of the Slackbot application. See the main project license for details.
