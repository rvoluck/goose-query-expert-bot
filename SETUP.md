# Goose Slackbot Setup Guide

This comprehensive guide will walk you through setting up the Goose Slackbot from scratch, including all prerequisites, configuration, and deployment steps.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Slack App Setup](#slack-app-setup)
5. [Goose Integration](#goose-integration)
6. [Authentication Setup](#authentication-setup)
7. [Configuration](#configuration)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Post-Deployment](#post-deployment)

## 🔧 Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.9 or higher
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: At least 1GB free space

### Required Services

1. **PostgreSQL 12+**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS with Homebrew
   brew install postgresql
   
   # Start PostgreSQL
   sudo systemctl start postgresql  # Linux
   brew services start postgresql   # macOS
   ```

2. **Redis 6+**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS with Homebrew
   brew install redis
   
   # Start Redis
   sudo systemctl start redis-server  # Linux
   brew services start redis          # macOS
   ```

3. **Git**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install git
   
   # macOS with Homebrew
   brew install git
   ```

### Access Requirements

- **Slack Workspace**: Admin access to create and configure apps
- **Goose Query Expert**: Running instance with API access
- **Snowflake**: Account with appropriate permissions
- **LDAP Server**: (Optional) For user authentication

## 🌍 Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd goose-slackbot
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 4. Verify Installation

```bash
python -c "import slack_sdk; print('Slack SDK installed successfully')"
python -c "import asyncpg; print('PostgreSQL driver installed successfully')"
python -c "import redis; print('Redis client installed successfully')"
```

## 🗄️ Database Configuration

### 1. Create Database

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Create database and user
CREATE DATABASE goose_slackbot;
CREATE USER goose_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE goose_slackbot TO goose_user;

# Exit PostgreSQL
\q
```

### 2. Configure Database Connection

```bash
# Test database connection
psql -h localhost -U goose_user -d goose_slackbot -c "SELECT version();"
```

### 3. Run Database Migrations

```bash
# Copy environment template
cp env.example .env

# Edit .env file with database URL
DATABASE_URL=postgresql://goose_user:secure_password@localhost:5432/goose_slackbot

# Run migrations
python migrations.py
```

### 4. Verify Database Setup

```bash
# Check tables were created
psql -h localhost -U goose_user -d goose_slackbot -c "\dt"
```

Expected tables:
- `users`
- `user_sessions`
- `query_history`
- `user_mappings`
- `audit_logs`

## 📱 Slack App Setup

### Step 1: Create Slack App

1. Go to [Slack API Dashboard](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Enter app details:
   - **App Name**: `Goose Query Expert`
   - **Workspace**: Select your workspace
5. Click **"Create App"**

### Step 2: Configure Basic Information

1. In the **Basic Information** section:
   - Add **App Description**: "AI-powered data querying bot"
   - Upload **App Icon** (optional)
   - Set **Background Color**: `#4A90E2`

### Step 3: Configure OAuth & Permissions

1. Navigate to **OAuth & Permissions**
2. In **Scopes** section, add **Bot Token Scopes**:
   ```
   app_mentions:read
   channels:history
   channels:read
   chat:write
   chat:write.public
   commands
   files:write
   groups:history
   groups:read
   im:history
   im:read
   im:write
   mpim:history
   mpim:read
   mpim:write
   users:read
   users:read.email
   ```

3. In **User Token Scopes** (if needed):
   ```
   identify
   ```

4. Click **"Install to Workspace"**
5. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### Step 4: Configure Socket Mode (Development)

1. Navigate to **Socket Mode**
2. Enable Socket Mode
3. Generate **App-Level Token**:
   - **Token Name**: `goose-bot-token`
   - **Scopes**: `connections:write`
4. Copy the **App-Level Token** (starts with `xapp-`)

### Step 5: Configure Event Subscriptions

1. Navigate to **Event Subscriptions**
2. Enable Events
3. Add **Bot Events**:
   ```
   app_mention
   message.channels
   message.groups
   message.im
   message.mpim
   ```

### Step 6: Configure Slash Commands

1. Navigate to **Slash Commands**
2. Click **"Create New Command"**
3. Configure command:
   - **Command**: `/goose-query`
   - **Request URL**: `https://your-domain.com/slack/commands` (for production)
   - **Short Description**: "Ask data questions"
   - **Usage Hint**: `What was our revenue last month?`

### Step 7: Configure Interactive Components

1. Navigate to **Interactivity & Shortcuts**
2. Enable Interactivity
3. Set **Request URL**: `https://your-domain.com/slack/interactive` (for production)

### Step 8: Get App Credentials

From your Slack app settings, collect:

1. **Basic Information** → **App Credentials**:
   - **Signing Secret**
2. **OAuth & Permissions**:
   - **Bot User OAuth Token**
3. **Socket Mode**:
   - **App-Level Token**

## 🦆 Goose Integration

### 1. Install Goose Query Expert

Follow the [Goose installation guide](https://github.com/block/goose) to set up Goose Query Expert.

### 2. Configure Goose MCP Server

```bash
# Start Goose MCP server
goose-mcp-server --port 8000 --host 0.0.0.0
```

### 3. Test Goose Connection

```bash
# Test API endpoint
curl http://localhost:8000/health
```

### 4. Configure Snowflake Integration

Ensure Goose has access to your Snowflake instance:

```bash
# Set Snowflake credentials for Goose
export SNOWFLAKE_ACCOUNT=your-account
export SNOWFLAKE_USER=your-user
export SNOWFLAKE_PASSWORD=your-password
export SNOWFLAKE_WAREHOUSE=COMPUTE_WH
export SNOWFLAKE_DATABASE=ANALYTICS
export SNOWFLAKE_SCHEMA=PUBLIC
```

## 🔐 Authentication Setup

### Option 1: LDAP Authentication

1. **Configure LDAP Server**:
   ```bash
   # In .env file
   LDAP_SERVER=ldap://your-ldap-server.com:389
   LDAP_BASE_DN=dc=company,dc=com
   LDAP_BIND_USER=cn=admin,dc=company,dc=com
   LDAP_BIND_PASSWORD=admin-password
   ```

2. **Test LDAP Connection**:
   ```python
   python -c "
   from auth import LDAPAuthenticator
   auth = LDAPAuthenticator()
   result = auth.test_connection()
   print('LDAP connection:', result)
   "
   ```

### Option 2: Database Authentication

1. **Create Initial Admin User**:
   ```bash
   python -c "
   import asyncio
   from auth import create_auth_system
   from database import get_database_manager
   
   async def create_admin():
       auth = await create_auth_system()
       db = await get_database_manager()
       
       # Create admin user
       await auth.create_user(
           slack_user_id='U1234567890',  # Your Slack user ID
           email='admin@company.com',
           ldap_id='admin',
           permissions=['admin', 'query_execute', 'user_manage']
       )
       print('Admin user created')
   
   asyncio.run(create_admin())
   "
   ```

### Option 3: External User Service

1. **Configure User Mapping Service**:
   ```bash
   # In .env file
   USER_MAPPING_SERVICE_URL=https://your-user-service.com/api
   USER_MAPPING_API_KEY=your-api-key
   ```

## ⚙️ Configuration

### 1. Environment Variables

Create and configure your `.env` file:

```bash
cp env.example .env
```

Edit `.env` with your specific configuration:

```bash
# ================================
# SLACK CONFIGURATION
# ================================
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_ADMIN_CHANNEL=C1234567890  # Optional: admin notifications channel

# ================================
# DATABASE CONFIGURATION
# ================================
DATABASE_URL=postgresql://goose_user:secure_password@localhost:5432/goose_slackbot
REDIS_URL=redis://localhost:6379/0

# ================================
# GOOSE INTEGRATION
# ================================
GOOSE_MCP_SERVER_URL=http://localhost:8000
GOOSE_MCP_TIMEOUT=300
GOOSE_MAX_CONCURRENT_QUERIES=10

# ================================
# SNOWFLAKE CONFIGURATION
# ================================
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=ANALYTICS
SNOWFLAKE_SCHEMA=PUBLIC

# ================================
# SECURITY CONFIGURATION
# ================================
JWT_SECRET_KEY=your-very-secure-secret-key-here
ENCRYPTION_KEY=your-32-character-encryption-key-here
RATE_LIMIT_PER_USER_PER_MINUTE=10

# ================================
# APPLICATION CONFIGURATION
# ================================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
MAX_RESULT_ROWS=10000
MAX_INLINE_ROWS=10

# ================================
# FEATURE FLAGS
# ================================
ENABLE_QUERY_HISTORY=true
ENABLE_INTERACTIVE_BUTTONS=true
ENABLE_FILE_UPLOADS=true
ENABLE_USER_PERMISSIONS=true
```

### 2. Generate Security Keys

```bash
# Generate JWT secret key
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate encryption key
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32)[:32])"
```

### 3. Validate Configuration

```bash
python config.py
```

Expected output:
```
✅ Configuration loaded successfully
Environment: development
Debug mode: True
Mock mode: False
```

## 🧪 Testing

### 1. Unit Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test categories
pytest tests/test_slack_bot.py -v
pytest tests/test_auth.py -v
pytest tests/test_database.py -v
```

### 2. Integration Tests

```bash
# Test database connection
python -c "
import asyncio
from database import get_database_manager

async def test_db():
    db = await get_database_manager()
    result = await db.fetch('SELECT 1 as test')
    print('Database test:', result)
    await db.close()

asyncio.run(test_db())
"
```

### 3. Slack Integration Test

```bash
# Test Slack connection
python -c "
from slack_sdk import WebClient
from config import get_settings

settings = get_settings()
client = WebClient(token=settings.slack_bot_token)

try:
    response = client.auth_test()
    print('Slack connection successful:', response['user'])
except Exception as e:
    print('Slack connection failed:', e)
"
```

### 4. Goose Integration Test

```bash
# Test Goose connection
python -c "
import asyncio
from goose_client import GooseQueryExpertClient

async def test_goose():
    client = GooseQueryExpertClient()
    health = await client.health_check()
    print('Goose health check:', health)

asyncio.run(test_goose())
"
```

## 🚀 Deployment

### Development Deployment

```bash
# Run in development mode
python slack_bot.py
```

### Production Deployment

#### Option 1: Direct Python

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker slack_bot:app --bind 0.0.0.0:3000
```

#### Option 2: Docker

1. **Build Docker Image**:
   ```bash
   docker build -t goose-slackbot .
   ```

2. **Run Container**:
   ```bash
   docker run -d \
     --name goose-slackbot \
     --env-file .env \
     -p 3000:3000 \
     goose-slackbot
   ```

3. **Docker Compose**:
   ```bash
   docker-compose up -d
   ```

#### Option 3: Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### Production Configuration Updates

1. **Update Slack App URLs**:
   - **Event Subscriptions Request URL**: `https://your-domain.com/slack/events`
   - **Interactive Components Request URL**: `https://your-domain.com/slack/interactive`
   - **Slash Commands Request URL**: `https://your-domain.com/slack/commands`

2. **Environment Variables**:
   ```bash
   ENVIRONMENT=production
   DEBUG=false
   HOST=0.0.0.0
   PORT=3000
   ```

3. **SSL/TLS Configuration**:
   - Ensure HTTPS is enabled
   - Use valid SSL certificates
   - Configure reverse proxy if needed

## 📋 Post-Deployment

### 1. Health Checks

```bash
# Check application health
curl https://your-domain.com/health

# Check metrics endpoint
curl https://your-domain.com/metrics
```

### 2. Initial User Setup

1. **Add yourself as admin**:
   ```bash
   # Get your Slack user ID from Slack profile
   # Run admin creation script
   python scripts/create_admin.py --slack-id U1234567890 --email admin@company.com
   ```

2. **Test bot functionality**:
   - Send DM to bot: "Hello"
   - Mention bot in channel: "@goose-bot What is 2+2?"
   - Try slash command: `/goose-query Show me current time`

### 3. User Onboarding

1. **Create user mapping**:
   ```bash
   # For each user, create mapping
   python scripts/add_user.py --slack-id U2345678901 --email user@company.com --permissions query_execute
   ```

2. **Announce to team**:
   ```
   🎉 Goose Query Expert bot is now available!
   
   You can:
   • DM @goose-bot with data questions
   • Mention @goose-bot in channels
   • Use /goose-query command
   
   Try asking: "What was our revenue last month?"
   ```

### 4. Monitoring Setup

1. **Configure monitoring**:
   - Set up Prometheus scraping
   - Configure alerting rules
   - Set up dashboards

2. **Log aggregation**:
   - Configure log shipping to your log aggregation system
   - Set up log-based alerts

### 5. Backup Strategy

1. **Database backups**:
   ```bash
   # Daily backup script
   pg_dump goose_slackbot > backup_$(date +%Y%m%d).sql
   ```

2. **Configuration backups**:
   - Store `.env` files securely
   - Version control configuration files

## 🔧 Troubleshooting Common Issues

### Slack Connection Issues

```bash
# Check bot token
python -c "
from slack_sdk import WebClient
client = WebClient(token='your-bot-token')
print(client.auth_test())
"
```

### Database Connection Issues

```bash
# Test database connection
psql -h localhost -U goose_user -d goose_slackbot -c "SELECT version();"
```

### Goose Integration Issues

```bash
# Check Goose server
curl http://localhost:8000/health
```

### Permission Issues

```bash
# Check user permissions
python -c "
import asyncio
from auth import create_auth_system

async def check_user():
    auth = await create_auth_system()
    user = await auth.get_user_by_slack_id('U1234567890')
    print('User permissions:', user.permissions if user else 'User not found')

asyncio.run(check_user())
"
```

## 📞 Support

If you encounter issues during setup:

1. Check the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) guide
2. Review application logs: `tail -f logs/goose-slackbot.log`
3. Verify all prerequisites are installed and running
4. Ensure all environment variables are correctly set
5. Contact the development team for assistance

## ✅ Setup Checklist

- [ ] Prerequisites installed (Python, PostgreSQL, Redis)
- [ ] Repository cloned and dependencies installed
- [ ] Database created and migrations run
- [ ] Slack app created and configured
- [ ] Goose Query Expert running and accessible
- [ ] Authentication system configured
- [ ] Environment variables set
- [ ] Configuration validated
- [ ] Tests passing
- [ ] Application deployed
- [ ] Health checks passing
- [ ] Initial users created
- [ ] Team notified and onboarded

Congratulations! Your Goose Slackbot should now be fully operational. 🎉
