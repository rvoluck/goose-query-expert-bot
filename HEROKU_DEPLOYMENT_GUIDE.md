# 🚀 Heroku Deployment Guide for Public Slack App

## Complete step-by-step guide to deploy your Goose Query Expert bot publicly

---

## ✅ Prerequisites

- [ ] Heroku account (free tier works)
- [ ] Heroku CLI installed
- [ ] Git installed
- [ ] Slack app created (from earlier steps)

---

## 📋 Step-by-Step Deployment

### STEP 1: Install Heroku CLI (if not installed)

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Verify installation
heroku --version
```

### STEP 2: Login to Heroku

```bash
heroku login
# This will open your browser to log in
```

### STEP 3: Create Heroku App

```bash
cd /Users/rleach/goose-slackbot

# Create app (choose a unique name)
heroku create goose-query-expert-bot

# Your app URL will be:
# https://goose-query-expert-bot.herokuapp.com
```

**Note**: If that name is taken, try:
- `goose-query-expert-YOUR-COMPANY`
- `goose-bot-YOUR-NAME`
- Heroku will suggest alternatives

### STEP 4: Add PostgreSQL Database

```bash
# Add PostgreSQL (free tier)
heroku addons:create heroku-postgresql:mini

# Verify it was added
heroku addons
```

### STEP 5: Add Redis

```bash
# Add Redis (free tier)
heroku addons:create heroku-redis:mini

# Verify
heroku addons
```

### STEP 6: Get Your Slack Credentials

Go to https://api.slack.com/apps → Select your app

**You need:**
1. **Client ID**: Basic Information → App Credentials
2. **Client Secret**: Basic Information → App Credentials (click Show)
3. **Signing Secret**: Basic Information → App Credentials (click Show)
4. **App ID**: Basic Information → App Credentials

### STEP 7: Set Environment Variables

```bash
# Slack OAuth credentials
heroku config:set SLACK_CLIENT_ID=1234567890.1234567890
heroku config:set SLACK_CLIENT_SECRET=your-client-secret
heroku config:set SLACK_SIGNING_SECRET=your-signing-secret
heroku config:set SLACK_APP_ID=A01234567

# Public URL (use your actual Heroku app URL)
heroku config:set PUBLIC_URL=https://goose-query-expert-bot.herokuapp.com
heroku config:set SLACK_OAUTH_REDIRECT_URL=https://goose-query-expert-bot.herokuapp.com/slack/oauth_redirect

# Security keys (generate new ones)
heroku config:set JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
heroku config:set ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Application settings
heroku config:set ENVIRONMENT=production
heroku config:set DEBUG=false
heroku config:set LOG_LEVEL=INFO

# Goose configuration (adjust as needed)
heroku config:set GOOSE_MCP_SERVER_URL=http://your-goose-server:8000
heroku config:set MOCK_MODE=false

# Verify all config vars
heroku config
```

### STEP 8: Initialize Git Repository

```bash
cd /Users/rleach/goose-slackbot

# Initialize git if not already done
git init

# Create .gitignore
cat > .gitignore << 'EOF'
.env
.env.*
!.env.example
!env.example
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
*.db
*.sqlite
.DS_Store
oauth_states/
*.log
EOF

# Add files
git add .
git commit -m "Initial commit - Goose Query Expert Slackbot"
```

### STEP 9: Deploy to Heroku

```bash
# Add Heroku remote
heroku git:remote -a goose-query-expert-bot

# Deploy
git push heroku main

# If you're on master branch:
# git push heroku master:main
```

**Watch the deployment logs**. You should see:
- Building
- Installing dependencies
- Running migrations
- Starting web process

### STEP 10: Verify Deployment

```bash
# Check if app is running
heroku ps

# View logs
heroku logs --tail

# Open app in browser
heroku open
```

You should see:
```json
{
  "name": "Goose Query Expert Slackbot",
  "description": "AI-powered data analysis bot for Slack",
  "install_url": "https://slack.com/oauth/v2/authorize?...",
  "documentation": "https://goose-query-expert-bot.herokuapp.com/docs"
}
```

### STEP 11: Update Slack App Configuration

Now that your app is deployed, update Slack settings:

#### A. Event Subscriptions
1. Go to https://api.slack.com/apps → Your App
2. Click **"Event Subscriptions"**
3. Toggle **ON**
4. **Request URL**: `https://goose-query-expert-bot.herokuapp.com/slack/events`
5. Wait for ✅ Verified
6. Subscribe to bot events (same as before)
7. **Save Changes**

#### B. Interactivity & Shortcuts
1. Click **"Interactivity & Shortcuts"**
2. Toggle **ON**
3. **Request URL**: `https://goose-query-expert-bot.herokuapp.com/slack/interactions`
4. **Save Changes**

#### C. OAuth & Permissions
1. Click **"OAuth & Permissions"**
2. **Redirect URLs** → **Add New Redirect URL**
3. Add: `https://goose-query-expert-bot.herokuapp.com/slack/oauth_redirect`
4. **Add** then **Save URLs**

#### D. Disable Socket Mode
1. Click **"Socket Mode"**
2. Toggle **OFF**
3. Confirm

### STEP 12: Enable Public Distribution

1. Click **"Manage Distribution"** in left sidebar
2. Review the checklist - everything should be ✅
3. Click **"Activate Public Distribution"**
4. Copy your **Shareable Install Link**:
   ```
   https://slack.com/oauth/v2/authorize?client_id=YOUR_CLIENT_ID&scope=...
   ```

### STEP 13: Test Installation

1. Open your install link in a browser
2. Select a test workspace
3. Click **"Allow"**
4. You should be redirected back to your app
5. Check Heroku logs:
   ```bash
   heroku logs --tail
   ```
6. You should see: "Saved installation for team_id=..."

### STEP 14: Test the Bot

1. In Slack, go to any channel
2. Invite the bot: `/invite @Goose Query Expert`
3. Ask a question: `@Goose Query Expert What was our revenue last month?`
4. Watch it work! 🎉

---

## 🔍 Troubleshooting

### "Application Error" on Heroku

```bash
# Check logs
heroku logs --tail

# Check if dynos are running
heroku ps

# Restart if needed
heroku restart
```

### "url_verification failed" in Slack

```bash
# Check if your app is responding
curl https://goose-query-expert-bot.herokuapp.com/health

# Should return: {"status":"healthy",...}
```

### "Invalid signature" errors

```bash
# Verify signing secret is correct
heroku config:get SLACK_SIGNING_SECRET

# Compare with Slack app settings
```

### Database connection errors

```bash
# Check if PostgreSQL is attached
heroku pg:info

# Check DATABASE_URL is set
heroku config:get DATABASE_URL

# Run migrations manually if needed
heroku run python scripts/db_migrate.py up
```

### Redis connection errors

```bash
# Check if Redis is attached
heroku redis:info

# Check REDIS_URL is set
heroku config:get REDIS_URL
```

---

## 📊 Monitoring Your App

### View Logs

```bash
# Real-time logs
heroku logs --tail

# Last 1000 lines
heroku logs -n 1000

# Filter for errors
heroku logs --tail | grep ERROR
```

### Check App Status

```bash
# See running dynos
heroku ps

# See app info
heroku apps:info

# See metrics (requires paid dyno)
heroku metrics
```

### Database Management

```bash
# Connect to PostgreSQL
heroku pg:psql

# View database info
heroku pg:info

# Backup database
heroku pg:backups:capture
heroku pg:backups:download
```

---

## 🔧 Updating Your App

### Deploy Updates

```bash
# Make changes to code
# Commit changes
git add .
git commit -m "Update: description of changes"

# Deploy
git push heroku main

# Watch deployment
heroku logs --tail
```

### Update Environment Variables

```bash
# Update a config var
heroku config:set SOME_VAR=new_value

# Remove a config var
heroku config:unset SOME_VAR

# View all config vars
heroku config
```

### Run Database Migrations

```bash
# Run migrations
heroku run python scripts/db_migrate.py up

# Check migration status
heroku run python scripts/db_migrate.py status
```

---

## 💰 Cost Breakdown

### Free Tier (Sufficient for Testing)
- **Dyno**: Free (550-1000 hours/month)
- **PostgreSQL**: Free (10,000 rows)
- **Redis**: Free (25MB)
- **Total**: $0/month

### Hobby Tier (Recommended for Production)
- **Dyno**: $7/month (always on)
- **PostgreSQL**: $9/month (10M rows)
- **Redis**: $15/month (100MB)
- **Total**: ~$31/month

### Production Tier (High Traffic)
- **Dyno**: $25-50/month (multiple dynos)
- **PostgreSQL**: $50/month (64GB)
- **Redis**: $30/month (1GB)
- **Total**: ~$105-130/month

---

## 🚀 Going Live Checklist

Before sharing with your organization:

- [ ] App deployed successfully
- [ ] Health check endpoint working
- [ ] OAuth flow tested
- [ ] Bot responds to messages
- [ ] Database migrations run
- [ ] Environment variables set
- [ ] Logs show no errors
- [ ] Tested in multiple workspaces
- [ ] Documentation updated
- [ ] Support email configured
- [ ] Privacy policy URL added
- [ ] Monitoring set up

---

## 📝 Next Steps

1. **Share install link** with your team
2. **Monitor logs** for issues
3. **Gather feedback** from users
4. **Iterate** on features
5. **Scale** as needed

---

## 🆘 Getting Help

**Heroku Issues:**
- Docs: https://devcenter.heroku.com/
- Status: https://status.heroku.com/
- Support: https://help.heroku.com/

**Slack Issues:**
- Docs: https://api.slack.com/docs
- Community: https://community.slack.com/

**App Issues:**
- Check logs: `heroku logs --tail`
- Check status: `heroku ps`
- Restart: `heroku restart`

---

## 🎉 Success!

Your Goose Query Expert bot is now publicly available!

**Install URL:**
```
https://slack.com/oauth/v2/authorize?client_id=YOUR_CLIENT_ID&scope=...
```

**Share this link** with anyone who wants to install the bot!

---

*Deployment completed! Your bot is live! 🚀*
