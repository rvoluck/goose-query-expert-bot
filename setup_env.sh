#!/bin/bash

# Setup Environment Script for Goose Query Expert Slackbot
# This script helps you create your .env file with proper configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Goose Query Expert Slackbot - Environment Setup              ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file already exists!${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Setup cancelled.${NC}"
        exit 1
    fi
    mv .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✓ Backed up existing .env${NC}"
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: Slack Credentials${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "You need 3 tokens from https://api.slack.com/apps"
echo "See SLACK_APP_SETUP_GUIDE.md for detailed instructions"
echo ""

# Get Slack Bot Token
while true; do
    read -p "Enter SLACK_BOT_TOKEN (starts with xoxb-): " SLACK_BOT_TOKEN
    if [[ $SLACK_BOT_TOKEN == xoxb-* ]]; then
        echo -e "${GREEN}✓ Valid bot token format${NC}"
        break
    else
        echo -e "${RED}✗ Bot token should start with 'xoxb-'${NC}"
    fi
done

# Get Slack App Token
while true; do
    read -p "Enter SLACK_APP_TOKEN (starts with xapp-): " SLACK_APP_TOKEN
    if [[ $SLACK_APP_TOKEN == xapp-* ]]; then
        echo -e "${GREEN}✓ Valid app token format${NC}"
        break
    else
        echo -e "${RED}✗ App token should start with 'xapp-'${NC}"
    fi
done

# Get Slack Signing Secret
read -p "Enter SLACK_SIGNING_SECRET: " SLACK_SIGNING_SECRET
if [ -n "$SLACK_SIGNING_SECRET" ]; then
    echo -e "${GREEN}✓ Signing secret set${NC}"
else
    echo -e "${RED}✗ Signing secret is required${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2: Deployment Mode${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Choose deployment mode:"
echo "  1) Development (Mock mode, SQLite, no Redis)"
echo "  2) Development with services (PostgreSQL + Redis)"
echo "  3) Production"
echo ""
read -p "Enter choice (1-3): " DEPLOY_MODE

case $DEPLOY_MODE in
    1)
        ENVIRONMENT="development"
        DEBUG="true"
        MOCK_MODE="true"
        DATABASE_URL="sqlite:///./slackbot.db"
        REDIS_URL="redis://localhost:6379/0"
        echo -e "${GREEN}✓ Development mode (mock) selected${NC}"
        ;;
    2)
        ENVIRONMENT="development"
        DEBUG="true"
        MOCK_MODE="false"
        DATABASE_URL="postgresql://slackbot:slackbot@localhost:5432/slackbot_db"
        REDIS_URL="redis://localhost:6379/0"
        echo -e "${GREEN}✓ Development mode (with services) selected${NC}"
        ;;
    3)
        ENVIRONMENT="production"
        DEBUG="false"
        MOCK_MODE="false"
        read -p "Enter DATABASE_URL: " DATABASE_URL
        read -p "Enter REDIS_URL: " REDIS_URL
        echo -e "${GREEN}✓ Production mode selected${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice. Defaulting to development mode.${NC}"
        ENVIRONMENT="development"
        DEBUG="true"
        MOCK_MODE="true"
        DATABASE_URL="sqlite:///./slackbot.db"
        REDIS_URL="redis://localhost:6379/0"
        ;;
esac

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 3: Goose Query Expert Configuration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$MOCK_MODE" = "true" ]; then
    GOOSE_MCP_SERVER_URL="http://localhost:8000"
    echo -e "${YELLOW}ℹ  Mock mode enabled - Goose URL not required${NC}"
else
    read -p "Enter GOOSE_MCP_SERVER_URL (or press Enter for default): " GOOSE_INPUT
    GOOSE_MCP_SERVER_URL=${GOOSE_INPUT:-http://localhost:8000}
    echo -e "${GREEN}✓ Goose URL: $GOOSE_MCP_SERVER_URL${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 4: Generating Security Keys${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Generate JWT secret
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo -e "${GREEN}✓ Generated JWT secret key${NC}"

# Generate encryption key
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo -e "${GREEN}✓ Generated encryption key${NC}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 5: Creating .env File${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Create .env file
cat > .env << EOF
# Goose Query Expert Slackbot Configuration
# Generated on $(date)

# ================================
# SLACK CONFIGURATION
# ================================
SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
SLACK_APP_TOKEN=$SLACK_APP_TOKEN
SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET
SLACK_ADMIN_CHANNEL=#data-team-alerts

# ================================
# GOOSE INTEGRATION
# ================================
GOOSE_MCP_SERVER_URL=$GOOSE_MCP_SERVER_URL
GOOSE_MCP_TIMEOUT=300
GOOSE_MAX_CONCURRENT_QUERIES=10

# ================================
# DATABASE CONFIGURATION
# ================================
DATABASE_URL=$DATABASE_URL
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

REDIS_URL=$REDIS_URL
REDIS_SESSION_TTL=3600
REDIS_CACHE_TTL=1800

# ================================
# SECURITY CONFIGURATION
# ================================
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

ENCRYPTION_KEY=$ENCRYPTION_KEY

RATE_LIMIT_PER_USER_PER_MINUTE=10
RATE_LIMIT_GLOBAL_PER_MINUTE=100

# ================================
# APPLICATION CONFIGURATION
# ================================
HOST=0.0.0.0
PORT=3000
WORKERS=4

DEBUG=$DEBUG
ENVIRONMENT=$ENVIRONMENT
LOG_LEVEL=INFO

MAX_RESULT_ROWS=10000
MAX_INLINE_ROWS=10
QUERY_TIMEOUT_SECONDS=300

# ================================
# FEATURE FLAGS
# ================================
ENABLE_QUERY_HISTORY=true
ENABLE_QUERY_SHARING=true
ENABLE_INTERACTIVE_BUTTONS=true
ENABLE_FILE_UPLOADS=true
ENABLE_THREAD_MANAGEMENT=true
ENABLE_USER_PERMISSIONS=true

# ================================
# DEVELOPMENT SETTINGS
# ================================
MOCK_MODE=$MOCK_MODE
MOCK_DELAY_SECONDS=2
AUTO_RELOAD=false
EOF

echo -e "${GREEN}✓ Created .env file${NC}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 6: Verification${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test configuration
if python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; assert os.getenv('SLACK_BOT_TOKEN')" 2>/dev/null; then
    echo -e "${GREEN}✓ Configuration file is valid${NC}"
else
    echo -e "${YELLOW}⚠  Could not verify configuration (python-dotenv not installed)${NC}"
    echo -e "${YELLOW}   This is OK - the bot will still work${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Setup Complete!                                            ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo ""

echo -e "${BLUE}Configuration Summary:${NC}"
echo -e "  Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "  Mock Mode: ${GREEN}$MOCK_MODE${NC}"
echo -e "  Database: ${GREEN}${DATABASE_URL%%@*}@...${NC}"
echo -e "  Goose URL: ${GREEN}$GOOSE_MCP_SERVER_URL${NC}"
echo ""

echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo -e "1. ${YELLOW}Install dependencies:${NC}"
echo -e "   ${GREEN}python3 -m venv venv${NC}"
echo -e "   ${GREEN}source venv/bin/activate${NC}"
echo -e "   ${GREEN}pip install -r requirements.txt${NC}"
echo ""

if [ "$MOCK_MODE" = "false" ] && [ "$DEPLOY_MODE" = "2" ]; then
    echo -e "2. ${YELLOW}Start services (PostgreSQL + Redis):${NC}"
    echo -e "   ${GREEN}docker-compose up -d postgres redis${NC}"
    echo ""
fi

echo -e "3. ${YELLOW}Run the bot:${NC}"
echo -e "   ${GREEN}python3 slack_bot.py${NC}"
echo ""

echo -e "4. ${YELLOW}Test in Slack:${NC}"
echo -e "   • Invite bot to a channel: ${GREEN}/invite @Goose Query Expert${NC}"
echo -e "   • Ask a question: ${GREEN}@Goose Query Expert What was our revenue?${NC}"
echo ""

echo -e "${BLUE}Documentation:${NC}"
echo -e "  • Full guide: ${GREEN}SLACK_APP_SETUP_GUIDE.md${NC}"
echo -e "  • Quick start: ${GREEN}QUICK_START.md${NC}"
echo -e "  • User manual: ${GREEN}USER_MANUAL.md${NC}"
echo ""

echo -e "${GREEN}Happy querying! 🚀${NC}"
echo ""
