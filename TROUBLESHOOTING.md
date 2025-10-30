# Goose Slackbot Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Goose Slackbot. Issues are organized by category with step-by-step solutions.

## 📋 Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Slack Integration Issues](#slack-integration-issues)
3. [Database Connection Issues](#database-connection-issues)
4. [Goose Integration Issues](#goose-integration-issues)
5. [Authentication Problems](#authentication-problems)
6. [Query Execution Issues](#query-execution-issues)
7. [Performance Issues](#performance-issues)
8. [Deployment Issues](#deployment-issues)
9. [Configuration Problems](#configuration-problems)
10. [Monitoring and Logging](#monitoring-and-logging)

## 🔍 Quick Diagnostics

### Health Check Commands

Run these commands to quickly assess system health:

```bash
# Check application health
curl http://localhost:3000/health

# Check detailed health status
curl http://localhost:3000/health/detailed

# Test database connection
python -c "
import asyncio
from database import get_database_manager
async def test():
    db = await get_database_manager()
    result = await db.fetch('SELECT 1')
    print('DB OK:', result)
    await db.close()
asyncio.run(test())
"

# Test Slack connection
python -c "
from slack_sdk import WebClient
from config import get_settings
settings = get_settings()
client = WebClient(token=settings.slack_bot_token)
try:
    response = client.auth_test()
    print('Slack OK:', response['user'])
except Exception as e:
    print('Slack Error:', e)
"

# Test Goose connection
curl http://localhost:8000/health
```

### Log Analysis

Check application logs for errors:

```bash
# View recent logs
tail -f logs/goose-slackbot.log

# Search for errors
grep -i error logs/goose-slackbot.log | tail -20

# Search for specific user issues
grep "user_id=U1234567890" logs/goose-slackbot.log

# Check startup logs
grep -i "starting\|initialized\|error" logs/goose-slackbot.log
```

## 📱 Slack Integration Issues

### Issue: Bot Not Responding to Messages

**Symptoms**:
- Bot doesn't respond to direct messages
- Bot doesn't respond to mentions in channels
- No error messages in Slack

**Diagnosis**:
```bash
# Check if bot is running
ps aux | grep slack_bot.py

# Check Slack token
python -c "
from slack_sdk import WebClient
client = WebClient(token='$SLACK_BOT_TOKEN')
print(client.auth_test())
"

# Check event subscriptions
curl -X POST https://api.slack.com/api/apps.event.subscriptions.list \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN"
```

**Solutions**:

1. **Verify Bot Token**:
   ```bash
   # Check token in .env file
   grep SLACK_BOT_TOKEN .env
   
   # Test token validity
   curl -X POST https://api.slack.com/api/auth.test \
     -H "Authorization: Bearer $SLACK_BOT_TOKEN"
   ```

2. **Check Bot Permissions**:
   - Go to Slack App settings → OAuth & Permissions
   - Verify required scopes are granted:
     - `app_mentions:read`
     - `chat:write`
     - `im:read`
     - `im:write`

3. **Verify Event Subscriptions**:
   - Go to Slack App settings → Event Subscriptions
   - Ensure events are enabled
   - Check that required events are subscribed:
     - `app_mention`
     - `message.im`

4. **Socket Mode Issues** (Development):
   ```bash
   # Check app-level token
   grep SLACK_APP_TOKEN .env
   
   # Verify Socket Mode is enabled in Slack App settings
   ```

### Issue: Slash Command Not Working

**Symptoms**:
- `/goose-query` command not recognized
- Command recognized but no response
- Error message when using command

**Solutions**:

1. **Verify Command Registration**:
   - Go to Slack App settings → Slash Commands
   - Ensure `/goose-query` is registered
   - Check Request URL is correct

2. **Check Command Handler**:
   ```python
   # Test command handler directly
   python -c "
   from slack_bot import GooseSlackBot
   bot = GooseSlackBot()
   # Check if command handler is registered
   print(bot.app._commands)
   "
   ```

3. **Production URL Issues**:
   ```bash
   # Test webhook endpoint
   curl -X POST https://your-domain.com/slack/commands \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "token=test&command=/goose-query&text=test"
   ```

### Issue: Interactive Buttons Not Working

**Symptoms**:
- Buttons appear but don't respond when clicked
- Error messages when clicking buttons
- Buttons missing from messages

**Solutions**:

1. **Check Interactive Components Setup**:
   - Go to Slack App settings → Interactivity & Shortcuts
   - Verify Interactivity is enabled
   - Check Request URL

2. **Test Button Handlers**:
   ```python
   # Check registered action handlers
   python -c "
   from slack_bot import GooseSlackBot
   bot = GooseSlackBot()
   print(bot.app._actions)
   "
   ```

3. **Verify Button Configuration**:
   ```python
   # Check if buttons are enabled
   python -c "
   from config import get_settings
   settings = get_settings()
   print('Interactive buttons enabled:', settings.enable_interactive_buttons)
   "
   ```

## 🗄️ Database Connection Issues

### Issue: Cannot Connect to Database

**Symptoms**:
- "Connection refused" errors
- "Database does not exist" errors
- Authentication failures

**Diagnosis**:
```bash
# Test database connection
psql -h localhost -U goose_user -d goose_slackbot -c "SELECT version();"

# Check if PostgreSQL is running
systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Check database exists
psql -h localhost -U postgres -c "\l" | grep goose_slackbot
```

**Solutions**:

1. **Start PostgreSQL**:
   ```bash
   # Linux
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   
   # macOS
   brew services start postgresql
   ```

2. **Create Database**:
   ```bash
   # Connect as superuser
   sudo -u postgres psql
   
   # Create database and user
   CREATE DATABASE goose_slackbot;
   CREATE USER goose_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE goose_slackbot TO goose_user;
   ```

3. **Fix Connection String**:
   ```bash
   # Check .env file
   grep DATABASE_URL .env
   
   # Correct format:
   DATABASE_URL=postgresql://username:password@host:port/database
   ```

4. **Check Firewall/Network**:
   ```bash
   # Test port connectivity
   telnet localhost 5432
   
   # Check PostgreSQL configuration
   sudo nano /etc/postgresql/*/main/postgresql.conf
   # Ensure: listen_addresses = 'localhost'
   
   sudo nano /etc/postgresql/*/main/pg_hba.conf
   # Add: local all goose_user md5
   ```

### Issue: Database Migration Failures

**Symptoms**:
- Tables not created
- Migration script errors
- Schema version mismatches

**Solutions**:

1. **Run Migrations Manually**:
   ```bash
   # Check current schema
   psql -h localhost -U goose_user -d goose_slackbot -c "\dt"
   
   # Run migrations
   python migrations.py
   
   # Check migration status
   psql -h localhost -U goose_user -d goose_slackbot -c "SELECT * FROM schema_migrations;"
   ```

2. **Reset Database** (if safe to do so):
   ```bash
   # Drop and recreate database
   sudo -u postgres psql -c "DROP DATABASE goose_slackbot;"
   sudo -u postgres psql -c "CREATE DATABASE goose_slackbot;"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE goose_slackbot TO goose_user;"
   
   # Run migrations
   python migrations.py
   ```

3. **Manual Schema Creation**:
   ```bash
   # Apply schema directly
   psql -h localhost -U goose_user -d goose_slackbot -f schema.sql
   ```

## 🦆 Goose Integration Issues

### Issue: Cannot Connect to Goose MCP Server

**Symptoms**:
- "Connection refused" to Goose server
- Timeout errors when processing queries
- Goose health check failures

**Diagnosis**:
```bash
# Check if Goose server is running
curl http://localhost:8000/health

# Check Goose server logs
journalctl -u goose-mcp-server -f

# Test network connectivity
telnet localhost 8000
```

**Solutions**:

1. **Start Goose MCP Server**:
   ```bash
   # Start server manually
   goose-mcp-server --port 8000 --host 0.0.0.0
   
   # Or as systemd service
   sudo systemctl start goose-mcp-server
   sudo systemctl enable goose-mcp-server
   ```

2. **Check Goose Configuration**:
   ```bash
   # Verify Goose environment variables
   env | grep GOOSE
   env | grep SNOWFLAKE
   
   # Test Goose CLI
   goose --help
   ```

3. **Update Goose URL**:
   ```bash
   # Check configuration
   grep GOOSE_MCP_SERVER_URL .env
   
   # Update if necessary
   GOOSE_MCP_SERVER_URL=http://localhost:8000
   ```

### Issue: Goose Query Generation Failures

**Symptoms**:
- "No suitable tables found" errors
- Poor quality SQL generation
- Timeout during query generation

**Solutions**:

1. **Check Snowflake Connection**:
   ```bash
   # Test Snowflake connectivity from Goose
   goose query "SELECT CURRENT_TIMESTAMP()"
   ```

2. **Verify Table Metadata**:
   ```bash
   # Check if Goose can access table metadata
   goose list-tables
   
   # Update table metadata cache
   goose refresh-metadata
   ```

3. **Improve Query Context**:
   ```python
   # Provide more context in queries
   question = "What was our total revenue last month from the sales.transactions table?"
   # Instead of: "What was our revenue?"
   ```

## 🔐 Authentication Problems

### Issue: User Authentication Failures

**Symptoms**:
- "User not found" errors
- "Permission denied" messages
- LDAP connection failures

**Diagnosis**:
```bash
# Check user exists in database
psql -h localhost -U goose_user -d goose_slackbot -c "SELECT * FROM users WHERE slack_user_id = 'U1234567890';"

# Test LDAP connection
python -c "
from auth import LDAPAuthenticator
auth = LDAPAuthenticator()
result = auth.test_connection()
print('LDAP test:', result)
"
```

**Solutions**:

1. **Create Missing User**:
   ```python
   # Create user manually
   python -c "
   import asyncio
   from auth import create_auth_system
   
   async def create_user():
       auth = await create_auth_system()
       await auth.create_user(
           slack_user_id='U1234567890',
           email='user@company.com',
           ldap_id='username',
           permissions=['query_execute']
       )
       print('User created')
   
   asyncio.run(create_user())
   "
   ```

2. **Fix LDAP Configuration**:
   ```bash
   # Check LDAP settings
   grep LDAP .env
   
   # Test LDAP connection
   ldapsearch -x -H ldap://your-server.com -D "cn=admin,dc=company,dc=com" -W -b "dc=company,dc=com" "(uid=username)"
   ```

3. **Grant Permissions**:
   ```python
   # Update user permissions
   python -c "
   import asyncio
   from database import get_database_manager, UserMappingRepository
   
   async def update_permissions():
       db = await get_database_manager()
       repo = UserMappingRepository(db)
       
       await repo.update_user_permissions(
           slack_user_id='U1234567890',
           permissions=['query_execute', 'query_share']
       )
       print('Permissions updated')
       await db.close()
   
   asyncio.run(update_permissions())
   "
   ```

### Issue: JWT Token Problems

**Symptoms**:
- "Invalid token" errors
- Token expiration issues
- Admin API authentication failures

**Solutions**:

1. **Check JWT Configuration**:
   ```bash
   # Verify JWT secret is set
   grep JWT_SECRET_KEY .env
   
   # Generate new secret if needed
   python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
   ```

2. **Test Token Generation**:
   ```python
   # Generate test token
   python -c "
   from auth import JWTManager
   from config import get_settings
   
   settings = get_settings()
   jwt_manager = JWTManager(settings.jwt_secret_key)
   
   token = jwt_manager.create_token({'user_id': 'test'})
   print('Token:', token)
   
   payload = jwt_manager.verify_token(token)
   print('Payload:', payload)
   "
   ```

## 📊 Query Execution Issues

### Issue: Queries Timing Out

**Symptoms**:
- "Query timeout" errors
- Long-running queries never complete
- Snowflake connection timeouts

**Solutions**:

1. **Increase Timeout Settings**:
   ```bash
   # Update configuration
   echo "QUERY_TIMEOUT_SECONDS=600" >> .env
   echo "GOOSE_MCP_TIMEOUT=600" >> .env
   ```

2. **Optimize Query Performance**:
   ```python
   # Use more specific queries
   # Instead of: "Show me all sales data"
   # Use: "Show me sales data for last 30 days"
   ```

3. **Check Snowflake Warehouse**:
   ```bash
   # Use larger warehouse for complex queries
   echo "SNOWFLAKE_WAREHOUSE=COMPUTE_WH_LARGE" >> .env
   ```

### Issue: Permission Denied on Snowflake

**Symptoms**:
- "Object does not exist or not authorized" errors
- "Access denied" messages
- Empty result sets

**Solutions**:

1. **Check Snowflake Permissions**:
   ```sql
   -- Connect to Snowflake and check grants
   SHOW GRANTS TO USER your_user;
   SHOW GRANTS TO ROLE your_role;
   
   -- Check table access
   SELECT * FROM information_schema.table_privileges 
   WHERE grantee = 'YOUR_USER';
   ```

2. **Grant Required Permissions**:
   ```sql
   -- Grant database access
   GRANT USAGE ON DATABASE analytics TO USER your_user;
   GRANT USAGE ON SCHEMA analytics.public TO USER your_user;
   GRANT SELECT ON ALL TABLES IN SCHEMA analytics.public TO USER your_user;
   ```

3. **Update Snowflake Configuration**:
   ```bash
   # Check Snowflake settings
   grep SNOWFLAKE .env
   
   # Ensure correct account/user/role
   SNOWFLAKE_ACCOUNT=your-account
   SNOWFLAKE_USER=your-user
   SNOWFLAKE_ROLE=your-role
   ```

## 🚀 Performance Issues

### Issue: Slow Query Response Times

**Symptoms**:
- Queries take longer than expected
- Slack timeouts
- High CPU/memory usage

**Diagnosis**:
```bash
# Check system resources
top
htop
free -h
df -h

# Check database performance
psql -h localhost -U goose_user -d goose_slackbot -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"

# Check Redis performance
redis-cli info stats
```

**Solutions**:

1. **Database Optimization**:
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_query_history_user_id ON query_history(user_id);
   CREATE INDEX idx_query_history_created_at ON query_history(created_at);
   CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
   
   -- Analyze tables
   ANALYZE;
   ```

2. **Redis Caching**:
   ```bash
   # Check Redis memory usage
   redis-cli info memory
   
   # Increase cache TTL for frequently accessed data
   echo "REDIS_CACHE_TTL=3600" >> .env
   ```

3. **Application Optimization**:
   ```bash
   # Increase worker processes
   echo "WORKERS=8" >> .env
   
   # Optimize database pool
   echo "DATABASE_POOL_SIZE=20" >> .env
   echo "DATABASE_MAX_OVERFLOW=30" >> .env
   ```

### Issue: Memory Leaks

**Symptoms**:
- Increasing memory usage over time
- Out of memory errors
- Application crashes

**Solutions**:

1. **Monitor Memory Usage**:
   ```bash
   # Monitor application memory
   ps aux | grep slack_bot.py
   
   # Use memory profiler
   pip install memory-profiler
   python -m memory_profiler slack_bot.py
   ```

2. **Fix Connection Leaks**:
   ```python
   # Ensure connections are properly closed
   # Check database connection usage
   python -c "
   import asyncio
   from database import get_database_manager
   
   async def check_connections():
       db = await get_database_manager()
       result = await db.fetch('SELECT count(*) FROM pg_stat_activity')
       print('Active connections:', result[0]['count'])
       await db.close()
   
   asyncio.run(check_connections())
   "
   ```

3. **Restart Application Periodically**:
   ```bash
   # Add to crontab for daily restart
   0 2 * * * systemctl restart goose-slackbot
   ```

## 🐳 Deployment Issues

### Issue: Docker Container Startup Failures

**Symptoms**:
- Container exits immediately
- "Port already in use" errors
- Environment variable issues

**Solutions**:

1. **Check Container Logs**:
   ```bash
   # View container logs
   docker logs goose-slackbot
   
   # Follow logs in real-time
   docker logs -f goose-slackbot
   ```

2. **Fix Port Conflicts**:
   ```bash
   # Check what's using the port
   lsof -i :3000
   
   # Use different port
   docker run -p 3001:3000 goose-slackbot
   ```

3. **Environment Variables**:
   ```bash
   # Check environment variables in container
   docker exec goose-slackbot env | grep SLACK
   
   # Pass environment file
   docker run --env-file .env goose-slackbot
   ```

### Issue: Kubernetes Deployment Problems

**Symptoms**:
- Pods in CrashLoopBackOff state
- Service not accessible
- ConfigMap/Secret issues

**Solutions**:

1. **Check Pod Status**:
   ```bash
   # Check pod status
   kubectl get pods -n goose-slackbot
   
   # Describe problematic pod
   kubectl describe pod goose-slackbot-xxx -n goose-slackbot
   
   # Check pod logs
   kubectl logs goose-slackbot-xxx -n goose-slackbot
   ```

2. **Fix ConfigMap Issues**:
   ```bash
   # Check ConfigMap
   kubectl get configmap goose-slackbot-config -o yaml
   
   # Update ConfigMap
   kubectl create configmap goose-slackbot-config --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
   ```

3. **Service Connectivity**:
   ```bash
   # Check service
   kubectl get svc -n goose-slackbot
   
   # Test service connectivity
   kubectl port-forward svc/goose-slackbot 3000:3000 -n goose-slackbot
   ```

## ⚙️ Configuration Problems

### Issue: Environment Variables Not Loading

**Symptoms**:
- Default values being used instead of configured values
- "Configuration error" messages
- Missing required settings

**Solutions**:

1. **Check .env File**:
   ```bash
   # Verify .env file exists and has correct format
   cat .env | head -10
   
   # Check for syntax errors
   python -c "
   from dotenv import load_dotenv
   load_dotenv('.env')
   print('Environment loaded successfully')
   "
   ```

2. **Validate Configuration**:
   ```bash
   # Test configuration loading
   python config.py
   
   # Check specific settings
   python -c "
   from config import get_settings
   settings = get_settings()
   print('Slack token set:', bool(settings.slack_bot_token))
   print('Database URL set:', bool(settings.database_url))
   "
   ```

3. **Fix File Permissions**:
   ```bash
   # Check .env file permissions
   ls -la .env
   
   # Fix permissions if needed
   chmod 600 .env
   ```

### Issue: Feature Flags Not Working

**Symptoms**:
- Features not enabling/disabling as expected
- Interactive buttons missing
- File uploads not working

**Solutions**:

1. **Check Feature Flag Settings**:
   ```bash
   # Check current feature flags
   python -c "
   from config import get_settings
   settings = get_settings()
   print('Interactive buttons:', settings.enable_interactive_buttons)
   print('File uploads:', settings.enable_file_uploads)
   print('Query history:', settings.enable_query_history)
   "
   ```

2. **Update Feature Flags**:
   ```bash
   # Enable features in .env
   echo "ENABLE_INTERACTIVE_BUTTONS=true" >> .env
   echo "ENABLE_FILE_UPLOADS=true" >> .env
   echo "ENABLE_QUERY_HISTORY=true" >> .env
   ```

## 📊 Monitoring and Logging

### Issue: Missing or Incomplete Logs

**Symptoms**:
- No log files generated
- Logs missing important information
- Log rotation issues

**Solutions**:

1. **Configure Logging**:
   ```bash
   # Check log configuration
   python -c "
   from config import setup_logging, get_settings
   settings = get_settings()
   print('Log level:', settings.log_level)
   print('Log format:', settings.log_format)
   setup_logging()
   "
   ```

2. **Create Log Directory**:
   ```bash
   # Create logs directory
   mkdir -p logs
   chmod 755 logs
   
   # Check log file permissions
   ls -la logs/
   ```

3. **Fix Log Rotation**:
   ```bash
   # Configure logrotate
   sudo nano /etc/logrotate.d/goose-slackbot
   
   # Add configuration:
   /path/to/goose-slackbot/logs/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
       create 644 app app
   }
   ```

### Issue: Metrics Not Available

**Symptoms**:
- `/metrics` endpoint returns 404
- Prometheus scraping failures
- Missing performance data

**Solutions**:

1. **Enable Metrics**:
   ```bash
   # Check metrics configuration
   grep METRICS .env
   
   # Enable metrics
   echo "METRICS_ENABLED=true" >> .env
   echo "METRICS_PORT=9090" >> .env
   ```

2. **Test Metrics Endpoint**:
   ```bash
   # Test metrics endpoint
   curl http://localhost:9090/metrics
   
   # Check if port is open
   netstat -tlnp | grep 9090
   ```

## 🆘 Getting Help

### Collecting Debug Information

When reporting issues, collect this information:

```bash
#!/bin/bash
# Debug information collection script

echo "=== System Information ==="
uname -a
python --version
pip list | grep -E "(slack|asyncpg|redis|pydantic)"

echo "=== Application Health ==="
curl -s http://localhost:3000/health || echo "Health check failed"

echo "=== Configuration ==="
python -c "
from config import get_settings
settings = get_settings()
print(f'Environment: {settings.environment}')
print(f'Debug: {settings.debug}')
print(f'Slack token set: {bool(settings.slack_bot_token)}')
print(f'Database URL set: {bool(settings.database_url)}')
"

echo "=== Recent Logs ==="
tail -50 logs/goose-slackbot.log 2>/dev/null || echo "No logs found"

echo "=== Database Status ==="
psql -h localhost -U goose_user -d goose_slackbot -c "SELECT version();" 2>/dev/null || echo "Database connection failed"

echo "=== Redis Status ==="
redis-cli ping 2>/dev/null || echo "Redis connection failed"

echo "=== Process Status ==="
ps aux | grep -E "(slack_bot|goose)" | grep -v grep
```

### Support Channels

- **GitHub Issues**: Report bugs and feature requests
- **Slack Channel**: #data-support for team assistance
- **Email**: data-team@company.com for urgent issues
- **Documentation**: Check README.md and other docs

### Escalation Process

1. **Level 1**: Check this troubleshooting guide
2. **Level 2**: Search existing GitHub issues
3. **Level 3**: Contact team in Slack channel
4. **Level 4**: Create detailed GitHub issue
5. **Level 5**: Email data team for urgent production issues

Remember to include debug information and steps to reproduce the issue when seeking help!
