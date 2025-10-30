#!/bin/bash
# GitHub Deployment Script for Goose Query Expert Slackbot

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                      ║${NC}"
echo -e "${BLUE}║   🚀 Goose Query Expert Slackbot - GitHub Deployment Script         ║${NC}"
echo -e "${BLUE}║                                                                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print section headers
print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to prompt for input
prompt_input() {
    local prompt="$1"
    local var_name="$2"
    local default="$3"
    
    if [ -n "$default" ]; then
        read -p "$(echo -e ${YELLOW}${prompt}${NC} [${default}]: )" input
        eval "$var_name=\"${input:-$default}\""
    else
        read -p "$(echo -e ${YELLOW}${prompt}${NC}: )" input
        eval "$var_name=\"$input\""
    fi
}

# Function to prompt for yes/no
prompt_yes_no() {
    local prompt="$1"
    local default="$2"
    
    if [ "$default" = "y" ]; then
        read -p "$(echo -e ${YELLOW}${prompt}${NC} [Y/n]: )" response
        response=${response:-y}
    else
        read -p "$(echo -e ${YELLOW}${prompt}${NC} [y/N]: )" response
        response=${response:-n}
    fi
    
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

print_section "📋 Step 1: Prerequisites Check"

# Check Git
if command_exists git; then
    echo -e "${GREEN}✅ Git installed:${NC} $(git --version)"
else
    echo -e "${RED}❌ Git not found. Please install Git first.${NC}"
    exit 1
fi

# Check if in git repository
if [ -d .git ]; then
    echo -e "${GREEN}✅ Git repository initialized${NC}"
else
    echo -e "${YELLOW}⚠️  Not a git repository. Initializing...${NC}"
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
fi

# Check Heroku CLI
if command_exists heroku; then
    echo -e "${GREEN}✅ Heroku CLI installed:${NC} $(heroku --version | head -n 1)"
else
    echo -e "${YELLOW}⚠️  Heroku CLI not found.${NC}"
    if prompt_yes_no "Would you like to install Heroku CLI?" "y"; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew tap heroku/brew && brew install heroku
        else
            curl https://cli-assets.heroku.com/install.sh | sh
        fi
    else
        echo -e "${YELLOW}⚠️  You'll need Heroku CLI for deployment. Install it later from: https://devcenter.heroku.com/articles/heroku-cli${NC}"
    fi
fi

# Check GitHub CLI (optional)
if command_exists gh; then
    echo -e "${GREEN}✅ GitHub CLI installed:${NC} $(gh --version | head -n 1)"
else
    echo -e "${YELLOW}⚠️  GitHub CLI not found (optional)${NC}"
fi

print_section "📦 Step 2: Repository Setup"

# Check for .gitignore
if [ -f .gitignore ]; then
    echo -e "${GREEN}✅ .gitignore exists${NC}"
else
    echo -e "${RED}❌ .gitignore not found!${NC}"
    echo -e "${YELLOW}Creating .gitignore...${NC}"
    # .gitignore should already exist from previous step
fi

# Check for .env
if [ -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file found${NC}"
    if grep -q "^\.env$" .gitignore; then
        echo -e "${GREEN}✅ .env is in .gitignore${NC}"
    else
        echo -e "${RED}❌ WARNING: .env is NOT in .gitignore!${NC}"
        echo ".env" >> .gitignore
        echo -e "${GREEN}✅ Added .env to .gitignore${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No .env file found (will use env.example)${NC}"
fi

print_section "🔧 Step 3: GitHub Configuration"

# Get GitHub username
if command_exists gh && gh auth status >/dev/null 2>&1; then
    GITHUB_USER=$(gh api user -q .login)
    echo -e "${GREEN}✅ Logged into GitHub as: ${GITHUB_USER}${NC}"
else
    prompt_input "Enter your GitHub username" GITHUB_USER
fi

# Get repository name
CURRENT_DIR=$(basename "$PWD")
prompt_input "Enter repository name" REPO_NAME "$CURRENT_DIR"

# Check if repository should be private
if prompt_yes_no "Make repository private?" "y"; then
    REPO_VISIBILITY="--private"
else
    REPO_VISIBILITY="--public"
fi

print_section "🚀 Step 4: Create GitHub Repository"

# Check if remote already exists
if git remote get-url origin >/dev/null 2>&1; then
    EXISTING_REMOTE=$(git remote get-url origin)
    echo -e "${YELLOW}⚠️  Remote 'origin' already exists: ${EXISTING_REMOTE}${NC}"
    if prompt_yes_no "Use existing remote?" "y"; then
        echo -e "${GREEN}✅ Using existing remote${NC}"
    else
        git remote remove origin
        echo -e "${YELLOW}Removed existing remote${NC}"
    fi
fi

# Create repository
if ! git remote get-url origin >/dev/null 2>&1; then
    if command_exists gh; then
        echo -e "${YELLOW}Creating GitHub repository...${NC}"
        gh repo create "$REPO_NAME" $REPO_VISIBILITY --source=. --remote=origin
        echo -e "${GREEN}✅ Repository created${NC}"
    else
        echo -e "${YELLOW}Please create repository manually at: https://github.com/new${NC}"
        echo -e "${YELLOW}Repository name: ${REPO_NAME}${NC}"
        echo -e "${YELLOW}Visibility: ${REPO_VISIBILITY}${NC}"
        echo ""
        prompt_input "Enter the repository URL (e.g., https://github.com/user/repo.git)" REPO_URL
        git remote add origin "$REPO_URL"
        echo -e "${GREEN}✅ Remote added${NC}"
    fi
fi

print_section "📝 Step 5: Commit and Push"

# Stage all files
echo -e "${YELLOW}Staging files...${NC}"
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo -e "${YELLOW}⚠️  No changes to commit${NC}"
else
    # Create commit
    echo -e "${YELLOW}Creating commit...${NC}"
    git commit -m "Initial commit: Goose Query Expert Slackbot

- Complete Slack integration with Events API + OAuth
- Goose Query Expert MCP client
- PostgreSQL + Redis for persistence
- Authentication and authorization system
- Comprehensive testing framework
- Docker and Kubernetes deployment configs
- Full documentation
- GitHub Actions CI/CD workflows"
    
    echo -e "${GREEN}✅ Commit created${NC}"
fi

# Push to GitHub
echo -e "${YELLOW}Pushing to GitHub...${NC}"
git branch -M main
git push -u origin main

echo -e "${GREEN}✅ Code pushed to GitHub${NC}"

print_section "🏗️  Step 6: Heroku Setup"

# Check if logged into Heroku
if command_exists heroku; then
    if heroku auth:whoami >/dev/null 2>&1; then
        HEROKU_USER=$(heroku auth:whoami)
        echo -e "${GREEN}✅ Logged into Heroku as: ${HEROKU_USER}${NC}"
    else
        echo -e "${YELLOW}⚠️  Not logged into Heroku${NC}"
        if prompt_yes_no "Login to Heroku now?" "y"; then
            heroku login
        else
            echo -e "${YELLOW}⚠️  Skipping Heroku deployment. Run 'heroku login' later.${NC}"
            exit 0
        fi
    fi
    
    # Create Heroku app
    prompt_input "Enter Heroku app name (leave blank for auto-generated)" HEROKU_APP_NAME
    
    echo -e "${YELLOW}Creating Heroku app...${NC}"
    if [ -n "$HEROKU_APP_NAME" ]; then
        heroku create "$HEROKU_APP_NAME"
    else
        heroku create
        HEROKU_APP_NAME=$(heroku apps:info -j | grep -o '"name":"[^"]*' | cut -d'"' -f4)
    fi
    
    echo -e "${GREEN}✅ Heroku app created: ${HEROKU_APP_NAME}${NC}"
    echo -e "${GREEN}   URL: https://${HEROKU_APP_NAME}.herokuapp.com${NC}"
    
    # Add addons
    echo -e "${YELLOW}Adding PostgreSQL...${NC}"
    heroku addons:create heroku-postgresql:mini
    
    echo -e "${YELLOW}Adding Redis...${NC}"
    heroku addons:create heroku-redis:mini
    
    echo -e "${GREEN}✅ Addons added${NC}"
    
    print_section "🔐 Step 7: Configure Environment Variables"
    
    echo -e "${YELLOW}You need to set the following environment variables:${NC}"
    echo ""
    echo "Required from Slack App:"
    echo "  - SLACK_CLIENT_ID"
    echo "  - SLACK_CLIENT_SECRET"
    echo "  - SLACK_SIGNING_SECRET"
    echo "  - SLACK_APP_ID"
    echo ""
    
    if prompt_yes_no "Do you have your Slack credentials ready?" "n"; then
        prompt_input "SLACK_CLIENT_ID" SLACK_CLIENT_ID
        prompt_input "SLACK_CLIENT_SECRET" SLACK_CLIENT_SECRET
        prompt_input "SLACK_SIGNING_SECRET" SLACK_SIGNING_SECRET
        prompt_input "SLACK_APP_ID" SLACK_APP_ID
        
        # Generate secrets
        JWT_SECRET=$(openssl rand -hex 32)
        ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        
        # Set config vars
        echo -e "${YELLOW}Setting environment variables...${NC}"
        heroku config:set \
            ENVIRONMENT=production \
            SLACK_CLIENT_ID="$SLACK_CLIENT_ID" \
            SLACK_CLIENT_SECRET="$SLACK_CLIENT_SECRET" \
            SLACK_SIGNING_SECRET="$SLACK_SIGNING_SECRET" \
            SLACK_APP_ID="$SLACK_APP_ID" \
            PUBLIC_URL="https://${HEROKU_APP_NAME}.herokuapp.com" \
            SLACK_OAUTH_REDIRECT_URL="https://${HEROKU_APP_NAME}.herokuapp.com/slack/oauth_redirect" \
            JWT_SECRET_KEY="$JWT_SECRET" \
            ENCRYPTION_KEY="$ENCRYPTION_KEY" \
            GOOSE_MODE=mock \
            LOG_LEVEL=INFO
        
        echo -e "${GREEN}✅ Environment variables set${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping environment variable setup${NC}"
        echo -e "${YELLOW}   Set them later with: heroku config:set KEY=value${NC}"
    fi
    
    print_section "🚀 Step 8: Deploy to Heroku"
    
    if prompt_yes_no "Deploy to Heroku now?" "y"; then
        echo -e "${YELLOW}Deploying...${NC}"
        git push heroku main
        
        echo -e "${YELLOW}Running database migrations...${NC}"
        heroku run python scripts/db_migrate.py up
        
        echo -e "${YELLOW}Scaling web dyno...${NC}"
        heroku ps:scale web=1
        
        echo -e "${GREEN}✅ Deployment complete!${NC}"
        
        # Open app
        if prompt_yes_no "Open app in browser?" "y"; then
            heroku open
        fi
        
        # View logs
        if prompt_yes_no "View logs?" "y"; then
            heroku logs --tail
        fi
    else
        echo -e "${YELLOW}⚠️  Skipping deployment. Deploy later with: git push heroku main${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Heroku CLI not available. Skipping Heroku setup.${NC}"
fi

print_section "✅ Deployment Complete!"

echo -e "${GREEN}Your Goose Query Expert Slackbot is now on GitHub!${NC}"
echo ""
echo "📍 Repository: https://github.com/${GITHUB_USER}/${REPO_NAME}"
if [ -n "$HEROKU_APP_NAME" ]; then
    echo "🌐 App URL: https://${HEROKU_APP_NAME}.herokuapp.com"
fi
echo ""
echo "📚 Next Steps:"
echo "  1. Configure your Slack app settings (see PUBLIC_APP_SETUP_GUIDE.md)"
echo "  2. Update Event Subscriptions URL"
echo "  3. Update OAuth Redirect URL"
echo "  4. Test your bot in Slack"
echo ""
echo "📖 Documentation:"
echo "  - GITHUB_DEPLOYMENT_GUIDE.md - Complete guide"
echo "  - PUBLIC_APP_SETUP_GUIDE.md - Slack configuration"
echo "  - HEROKU_DEPLOYMENT_GUIDE.md - Heroku details"
echo ""
echo -e "${GREEN}Happy deploying! 🚀${NC}"
