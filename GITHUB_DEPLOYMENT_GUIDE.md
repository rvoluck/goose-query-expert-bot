# 🚀 GitHub Deployment Guide for Goose Query Expert Slackbot

Complete guide to deploy your Slackbot using GitHub + Heroku (or other platforms).

---

## 📋 Prerequisites

- [ ] GitHub account
- [ ] Git installed locally
- [ ] Heroku account (or AWS/GCP/Azure)
- [ ] Slack app created (see `SLACK_APP_SETUP_GUIDE.md`)

---

## 🎯 Deployment Overview

```
Local Code → GitHub Repository → Heroku/Cloud Platform → Slack
```

**Benefits:**
- ✅ Version control and collaboration
- ✅ Automatic deployments on push
- ✅ Easy rollbacks
- ✅ CI/CD integration
- ✅ Team collaboration

---

## 📦 Step 1: Prepare Your Repository

### 1.1 Initialize Git Repository

```bash
cd /Users/rleach/goose-slackbot

# Initialize git (if not already done)
git init

# Check status
git status
```

### 1.2 Create `.gitignore`

We'll create a comprehensive `.gitignore` to exclude sensitive files:

```bash
# This will be created in the next step
cat .gitignore
```

### 1.3 Review Files to Commit

**Files to INCLUDE:**
- ✅ All `.py` files
- ✅ All `.md` documentation
- ✅ `requirements*.txt`
- ✅ `Procfile`, `runtime.txt`
- ✅ `Dockerfile*`, `docker-compose*.yml`
- ✅ `k8s/*.yaml`
- ✅ `migrations/*.sql`
- ✅ `scripts/*.sh`, `scripts/*.py`
- ✅ `tests/**`
- ✅ `Makefile`
- ✅ `env.example`, `env.public.example`

**Files to EXCLUDE (via .gitignore):**
- ❌ `.env` (contains secrets!)
- ❌ `venv/`, `__pycache__/`
- ❌ `*.pyc`, `*.pyo`
- ❌ `.DS_Store`
- ❌ Database files (`*.db`)
- ❌ Log files (`*.log`)

---

## 🔐 Step 2: Secure Your Secrets

### 2.1 Never Commit Secrets!

**CRITICAL:** Never commit these to GitHub:
- `SLACK_BOT_TOKEN`
- `SLACK_CLIENT_SECRET`
- `SLACK_SIGNING_SECRET`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `ENCRYPTION_KEY`

### 2.2 Use Environment Variables

All secrets should be:
1. Stored in `.env` locally (git-ignored)
2. Set as environment variables on Heroku/cloud platform
3. Never hardcoded in source files

---

## 📤 Step 3: Push to GitHub

### 3.1 Create GitHub Repository

**Option A: Via GitHub Website**
1. Go to https://github.com/new
2. Repository name: `goose-slackbot` (or your choice)
3. Description: "Slackbot for Goose Query Expert - Team Data Collaboration"
4. Choose **Private** (recommended for internal tools)
5. **Do NOT** initialize with README (we have one)
6. Click "Create repository"

**Option B: Via GitHub CLI**
```bash
# Install GitHub CLI if needed: brew install gh
gh auth login
gh repo create goose-slackbot --private --source=. --remote=origin
```

### 3.2 Add Remote and Push

```bash
# Add GitHub as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/goose-slackbot.git

# Stage all files
git add .

# Create initial commit
git commit -m "Initial commit: Goose Query Expert Slackbot

- Complete Slack integration with Events API + OAuth
- Goose Query Expert MCP client
- PostgreSQL + Redis for persistence
- Authentication and authorization system
- Comprehensive testing framework
- Docker and Kubernetes deployment configs
- Full documentation"

# Push to GitHub
git push -u origin main
```

### 3.3 Verify on GitHub

Visit your repository: `https://github.com/YOUR_USERNAME/goose-slackbot`

You should see:
- ✅ All source files
- ✅ Documentation
- ✅ No `.env` file
- ✅ README.md displayed

---

## 🚀 Step 4: Deploy to Heroku from GitHub

### 4.1 Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Verify installation
heroku --version
```

### 4.2 Login to Heroku

```bash
heroku login
# Opens browser for authentication
```

### 4.3 Create Heroku App

```bash
# Create app (Heroku will assign a name if you don't specify)
heroku create goose-slackbot-YOUR-NAME

# Or let Heroku choose a name
heroku create

# Note the app URL: https://YOUR-APP-NAME.herokuapp.com
```

### 4.4 Connect GitHub to Heroku

**Option A: Via Heroku Dashboard (Recommended)**

1. Go to https://dashboard.heroku.com/apps
2. Click your app name
3. Go to "Deploy" tab
4. Under "Deployment method", click **GitHub**
5. Click "Connect to GitHub"
6. Search for `goose-slackbot`
7. Click "Connect"
8. Enable "Automatic deploys" from `main` branch
9. Click "Deploy Branch" for initial deployment

**Option B: Via Heroku CLI**

```bash
# Add Heroku remote
heroku git:remote -a YOUR-APP-NAME

# Deploy
git push heroku main
```

### 4.5 Add Database and Redis

```bash
# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Add Redis
heroku addons:create heroku-redis:mini

# Verify addons
heroku addons
```

### 4.6 Set Environment Variables

```bash
# Set all required environment variables
heroku config:set \
  ENVIRONMENT=production \
  SLACK_CLIENT_ID=your_client_id \
  SLACK_CLIENT_SECRET=your_client_secret \
  SLACK_SIGNING_SECRET=your_signing_secret \
  SLACK_APP_ID=your_app_id \
  PUBLIC_URL=https://YOUR-APP-NAME.herokuapp.com \
  SLACK_OAUTH_REDIRECT_URL=https://YOUR-APP-NAME.herokuapp.com/slack/oauth_redirect \
  JWT_SECRET_KEY=$(openssl rand -hex 32) \
  ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())") \
  GOOSE_MODE=mock \
  LOG_LEVEL=INFO

# Database and Redis URLs are automatically set by Heroku addons

# View all config
heroku config
```

### 4.7 Scale Dynos

```bash
# Start web dyno
heroku ps:scale web=1

# Check status
heroku ps
```

### 4.8 View Logs

```bash
# Stream logs
heroku logs --tail

# View recent logs
heroku logs --tail -n 100
```

---

## 🔧 Step 5: Configure Slack App

Now that your app is deployed, update your Slack app settings:

### 5.1 Get Your Public URL

```bash
heroku info
# Note the "Web URL": https://YOUR-APP-NAME.herokuapp.com
```

### 5.2 Update Slack App Settings

Go to https://api.slack.com/apps → Your App

**A. OAuth & Permissions**
1. **Redirect URLs**: Add `https://YOUR-APP-NAME.herokuapp.com/slack/oauth_redirect`
2. **Bot Token Scopes**: Ensure these are added:
   - `app_mentions:read`
   - `channels:history`
   - `chat:write`
   - `commands`
   - `files:write`
   - `im:history`
   - `im:write`
   - `users:read`

**B. Event Subscriptions**
1. **Enable Events**: Toggle ON
2. **Request URL**: `https://YOUR-APP-NAME.herokuapp.com/slack/events`
3. Wait for verification (should show ✅ Verified)
4. **Subscribe to bot events**:
   - `app_mention`
   - `message.channels`
   - `message.im`
5. Save Changes

**C. Interactivity & Shortcuts**
1. **Interactivity**: Toggle ON
2. **Request URL**: `https://YOUR-APP-NAME.herokuapp.com/slack/interactions`
3. Save Changes

**D. Slash Commands** (Optional)
1. Create command: `/goose-query`
2. **Request URL**: `https://YOUR-APP-NAME.herokuapp.com/slack/events`
3. **Short Description**: "Ask Goose Query Expert a question"
4. Save

**E. Manage Distribution**
1. Go to "Manage Distribution"
2. **Remove Hard Coded Information**: Review and fix any issues
3. **Activate Public Distribution**: Click "Activate"

### 5.3 Verify Slack Configuration

Check your Heroku logs:
```bash
heroku logs --tail
```

You should see:
```
✅ Slack event verification successful
✅ Database connected
✅ Redis connected
✅ Application started
```

---

## 🧪 Step 6: Test Your Deployment

### 6.1 Install App to Workspace

1. Go to your app's install URL:
   ```
   https://YOUR-APP-NAME.herokuapp.com/slack/install
   ```
2. Click "Add to Slack"
3. Authorize the app
4. You should be redirected back with success message

### 6.2 Test in Slack

**Test 1: Direct Message**
```
DM the bot: @Goose Query Expert What was our revenue last month?
```

**Test 2: Channel Mention**
```
In a channel: @Goose Query Expert Show me top customers
```

**Test 3: Slash Command** (if configured)
```
/goose-query How many active users do we have?
```

### 6.3 Monitor Logs

```bash
# Watch logs in real-time
heroku logs --tail

# Check for errors
heroku logs --tail | grep ERROR
```

---

## 🔄 Step 7: Continuous Deployment

### 7.1 Enable Auto-Deploy

If you connected GitHub to Heroku (Step 4.4 Option A):
- ✅ Every push to `main` branch automatically deploys
- ✅ Heroku runs tests before deploying (if configured)
- ✅ Automatic rollback on failure

### 7.2 Make Changes

```bash
# Make code changes
vim slack_bot_public.py

# Commit and push
git add .
git commit -m "Update: improved error handling"
git push origin main

# Heroku automatically deploys!
```

### 7.3 Manual Deploy

```bash
# Deploy specific branch
git push heroku your-branch:main

# Or via dashboard
# Go to Heroku → Deploy tab → Manual deploy
```

---

## 🔍 Step 8: Monitoring and Maintenance

### 8.1 View Application Metrics

```bash
# Open Heroku dashboard
heroku open

# View metrics
heroku logs --tail
heroku ps
heroku pg:info
heroku redis:info
```

### 8.2 Database Management

```bash
# Run migrations
heroku run python scripts/db_migrate.py up

# Access database
heroku pg:psql

# Backup database
heroku pg:backups:capture
heroku pg:backups:download
```

### 8.3 Scale Application

```bash
# Scale up
heroku ps:scale web=2

# Scale down
heroku ps:scale web=1

# Use larger dyno
heroku ps:type web=standard-1x
```

### 8.4 Set Up Monitoring

**Option A: Heroku Metrics (Built-in)**
- Go to Heroku Dashboard → Metrics tab
- View response times, memory, throughput

**Option B: External Monitoring**
```bash
# Add New Relic
heroku addons:create newrelic:wayne

# Add Papertrail (logging)
heroku addons:create papertrail:choklad
```

---

## 🐛 Troubleshooting

### Issue: "Application Error" in Slack

**Check logs:**
```bash
heroku logs --tail
```

**Common causes:**
- Missing environment variables
- Database connection issues
- Redis connection issues

**Fix:**
```bash
# Verify all config vars are set
heroku config

# Restart app
heroku restart
```

### Issue: Slack Events Not Received

**Verify:**
1. Event Subscriptions URL is correct
2. URL shows ✅ Verified in Slack settings
3. Bot is invited to channels

**Test webhook:**
```bash
curl -X POST https://YOUR-APP-NAME.herokuapp.com/slack/events \
  -H "Content-Type: application/json" \
  -d '{"type":"url_verification","challenge":"test123"}'
```

### Issue: OAuth Installation Fails

**Check:**
1. Redirect URL matches exactly
2. Client ID and Secret are correct
3. App is activated for distribution

**Verify:**
```bash
heroku config:get SLACK_CLIENT_ID
heroku config:get SLACK_OAUTH_REDIRECT_URL
```

### Issue: Database Connection Errors

**Check database:**
```bash
heroku pg:info
heroku pg:diagnose
```

**Reset database:**
```bash
heroku pg:reset DATABASE_URL --confirm YOUR-APP-NAME
heroku run python scripts/db_migrate.py up
```

---

## 📊 Cost Breakdown

### Free Tier (Testing)
- **Heroku Dyno**: Free (550-1000 hrs/month)
- **PostgreSQL**: Free (10K rows)
- **Redis**: Free (25MB)
- **Total**: $0/month

### Hobby Tier (Production)
- **Heroku Dyno**: $7/month (always on)
- **PostgreSQL**: $9/month (10M rows)
- **Redis**: $15/month (30MB)
- **Total**: $31/month

### Standard Tier (Scale)
- **Heroku Dyno**: $25-50/month
- **PostgreSQL**: $50/month (64GB)
- **Redis**: $30/month (100MB)
- **Total**: $105-130/month

---

## 🎓 Best Practices

### 1. Branch Strategy

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push to GitHub
git push origin feature/new-feature

# Create Pull Request on GitHub
# After review, merge to main
# Heroku auto-deploys!
```

### 2. Environment Management

```bash
# Development
ENVIRONMENT=development

# Staging (optional)
heroku create goose-slackbot-staging
# Deploy to staging first

# Production
heroku create goose-slackbot-production
```

### 3. Secrets Management

```bash
# Use Heroku Config Vars (never commit secrets)
heroku config:set SECRET_KEY=value

# For team access, use 1Password/Vault
# Share Heroku app access, not secrets
```

### 4. Monitoring

```bash
# Set up alerts
heroku labs:enable runtime-dyno-metadata

# Add health checks
# Your app already has /health endpoint
```

---

## 🚀 Advanced: CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Heroku

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: "YOUR-APP-NAME"
          heroku_email: "your-email@example.com"
      
      - name: Run Tests
        run: |
          heroku run python -m pytest tests/
```

---

## 📚 Additional Resources

- **Heroku Documentation**: https://devcenter.heroku.com/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Slack API**: https://api.slack.com/
- **Project Documentation**: See `DOCUMENTATION_INDEX.md`

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Code reviewed and tested locally
- [ ] `.gitignore` configured correctly
- [ ] No secrets in code
- [ ] Documentation updated

### GitHub Setup
- [ ] Repository created (private recommended)
- [ ] Code pushed to GitHub
- [ ] `.env` not committed
- [ ] README.md visible

### Heroku Setup
- [ ] App created
- [ ] GitHub connected
- [ ] Auto-deploy enabled
- [ ] PostgreSQL addon added
- [ ] Redis addon added
- [ ] All environment variables set

### Slack Configuration
- [ ] OAuth redirect URL updated
- [ ] Event subscriptions URL configured
- [ ] Interactivity URL configured
- [ ] Public distribution activated
- [ ] Bot scopes configured

### Testing
- [ ] OAuth installation works
- [ ] Bot responds to mentions
- [ ] Bot responds to DMs
- [ ] Query execution works
- [ ] Results formatted correctly

### Monitoring
- [ ] Logs accessible
- [ ] Metrics visible
- [ ] Alerts configured
- [ ] Backup strategy in place

---

## 🎉 Success!

Your Goose Query Expert Slackbot is now:
- ✅ Version controlled on GitHub
- ✅ Automatically deployed to Heroku
- ✅ Publicly distributed via Slack
- ✅ Monitored and scalable

**Next Steps:**
1. Share with your team
2. Monitor usage and performance
3. Iterate based on feedback
4. Add new features via GitHub PRs

---

## 🆘 Need Help?

- **Heroku Issues**: Check `heroku logs --tail`
- **Slack Issues**: Check Slack API logs
- **Code Issues**: Review `TROUBLESHOOTING.md`
- **Questions**: Check `FAQ.md`

Happy deploying! 🚀
