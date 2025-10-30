# 🚀 GitHub Deployment - Quick Start Guide

**Deploy your Goose Query Expert Slackbot using GitHub in 30 minutes!**

---

## 🎯 Why GitHub Deployment?

✅ **Version Control** - Track all changes
✅ **Automatic Deployments** - Push to deploy
✅ **Team Collaboration** - Work together
✅ **Easy Rollbacks** - Undo mistakes quickly
✅ **CI/CD Integration** - Automated testing
✅ **Professional** - Industry standard

---

## 📋 Prerequisites

Before you start, make sure you have:

- [ ] GitHub account (free)
- [ ] Heroku account (free tier available)
- [ ] Git installed on your computer
- [ ] Access to create Slack apps
- [ ] 30 minutes of time

---

## 🚀 Three-Step Deployment

### **Step 1: Push to GitHub** (10 minutes)

#### Option A: Automated Script (Easiest!)

```bash
cd /Users/rleach/goose-slackbot

# Run the automated deployment script
./scripts/github-deploy.sh

# The script will:
# ✅ Check prerequisites
# ✅ Create .gitignore
# ✅ Initialize git repository
# ✅ Create GitHub repository
# ✅ Push your code
# ✅ Set up Heroku (optional)
```

#### Option B: Manual Steps

```bash
cd /Users/rleach/goose-slackbot

# 1. Initialize git (if not done)
git init

# 2. Add all files
git add .

# 3. Create initial commit
git commit -m "Initial commit: Goose Query Expert Slackbot"

# 4. Create GitHub repository
# Go to: https://github.com/new
# Repository name: goose-slackbot
# Make it private
# Don't initialize with README

# 5. Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/goose-slackbot.git
git branch -M main
git push -u origin main
```

**✅ Checkpoint:** Your code is now on GitHub!

---

### **Step 2: Deploy to Heroku** (15 minutes)

#### 2.1 Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Verify
heroku --version
```

#### 2.2 Login to Heroku

```bash
heroku login
# Opens browser for authentication
```

#### 2.3 Create Heroku App

```bash
# Create app
heroku create goose-slackbot-YOUR-NAME

# Note the URL: https://YOUR-APP-NAME.herokuapp.com
```

#### 2.4 Add Database and Redis

```bash
# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Add Redis
heroku addons:create heroku-redis:mini
```

#### 2.5 Connect GitHub to Heroku

**Via Heroku Dashboard (Recommended):**

1. Go to https://dashboard.heroku.com/apps
2. Click your app name
3. Go to "Deploy" tab
4. Under "Deployment method", click **GitHub**
5. Click "Connect to GitHub"
6. Search for `goose-slackbot`
7. Click "Connect"
8. Enable "Automatic deploys" from `main` branch
9. Click "Deploy Branch" for initial deployment

**Via CLI:**

```bash
# Add Heroku remote
heroku git:remote -a YOUR-APP-NAME

# Deploy
git push heroku main
```

#### 2.6 Set Environment Variables

First, get your Slack credentials from https://api.slack.com/apps

Then set them:

```bash
heroku config:set \
  ENVIRONMENT=production \
  SLACK_CLIENT_ID=your_client_id_here \
  SLACK_CLIENT_SECRET=your_client_secret_here \
  SLACK_SIGNING_SECRET=your_signing_secret_here \
  SLACK_APP_ID=your_app_id_here \
  PUBLIC_URL=https://YOUR-APP-NAME.herokuapp.com \
  SLACK_OAUTH_REDIRECT_URL=https://YOUR-APP-NAME.herokuapp.com/slack/oauth_redirect \
  JWT_SECRET_KEY=$(openssl rand -hex 32) \
  ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())") \
  GOOSE_MODE=mock \
  LOG_LEVEL=INFO
```

#### 2.7 Scale and Start

```bash
# Start web dyno
heroku ps:scale web=1

# Check status
heroku ps

# View logs
heroku logs --tail
```

**✅ Checkpoint:** Your app is now running on Heroku!

---

### **Step 3: Configure Slack App** (5 minutes)

Go to https://api.slack.com/apps → Your App

#### 3.1 Disable Socket Mode

1. Go to "Socket Mode"
2. Toggle **OFF**

#### 3.2 Configure OAuth & Permissions

1. Go to "OAuth & Permissions"
2. **Redirect URLs**: Add
   ```
   https://YOUR-APP-NAME.herokuapp.com/slack/oauth_redirect
   ```
3. **Bot Token Scopes**: Ensure these are added:
   - `app_mentions:read`
   - `channels:history`
   - `chat:write`
   - `commands`
   - `files:write`
   - `im:history`
   - `im:write`
   - `users:read`

#### 3.3 Configure Event Subscriptions

1. Go to "Event Subscriptions"
2. Toggle **ON**
3. **Request URL**: 
   ```
   https://YOUR-APP-NAME.herokuapp.com/slack/events
   ```
4. Wait for ✅ Verified
5. **Subscribe to bot events**:
   - `app_mention`
   - `message.channels`
   - `message.im`
6. Save Changes

#### 3.4 Configure Interactivity

1. Go to "Interactivity & Shortcuts"
2. Toggle **ON**
3. **Request URL**:
   ```
   https://YOUR-APP-NAME.herokuapp.com/slack/interactions
   ```
4. Save Changes

#### 3.5 Activate Public Distribution

1. Go to "Manage Distribution"
2. Review checklist
3. Click "Activate Public Distribution"

**✅ Checkpoint:** Slack app is configured!

---

## 🧪 Test Your Deployment

### Test 1: Health Check

```bash
curl https://YOUR-APP-NAME.herokuapp.com/health
```

Should return: `{"status":"healthy"}`

### Test 2: Install App

1. Go to: `https://YOUR-APP-NAME.herokuapp.com/slack/install`
2. Click "Add to Slack"
3. Authorize the app

### Test 3: Use in Slack

```
DM the bot: @Goose Query Expert What was our revenue last month?
```

### Monitor Logs

```bash
heroku logs --tail
```

---

## 🔄 Making Changes

### The GitHub Workflow

```bash
# 1. Make changes to code
vim slack_bot_public.py

# 2. Commit changes
git add .
git commit -m "Update: improved error handling"

# 3. Push to GitHub
git push origin main

# 4. Heroku automatically deploys! 🎉
```

### Manual Deploy

```bash
# Deploy specific branch
git push heroku your-branch:main
```

---

## 📊 Monitor Your App

### View Logs

```bash
# Stream logs
heroku logs --tail

# View recent logs
heroku logs -n 100

# Search logs
heroku logs --tail | grep ERROR
```

### Check Status

```bash
# App info
heroku info

# Dyno status
heroku ps

# Database info
heroku pg:info

# Redis info
heroku redis:info
```

### View Metrics

```bash
# Open dashboard
heroku open

# Or visit: https://dashboard.heroku.com/apps/YOUR-APP-NAME
```

---

## 🐛 Troubleshooting

### Issue: "Application Error"

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
# Verify config
heroku config

# Restart app
heroku restart
```

### Issue: Slack Events Not Received

**Verify:**
1. Event Subscriptions URL shows ✅ Verified
2. Bot is invited to channels
3. Heroku app is running

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

---

## 💰 Cost Breakdown

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

---

## 🎓 Advanced Features

### Enable GitHub Actions CI/CD

Your repository already has GitHub Actions workflows:

- `.github/workflows/deploy.yml` - Automated deployment
- `.github/workflows/test.yml` - Automated testing

**To enable:**

1. Go to GitHub → Settings → Secrets
2. Add these secrets:
   - `HEROKU_API_KEY` (from `heroku auth:token`)
   - `HEROKU_APP_NAME` (your app name)
   - `HEROKU_EMAIL` (your Heroku email)

Now every push to `main` will:
1. Run tests
2. Deploy to Heroku (if tests pass)
3. Run database migrations
4. Perform health check

### Set Up Staging Environment

```bash
# Create staging app
heroku create goose-slackbot-staging

# Add addons
heroku addons:create heroku-postgresql:mini --app goose-slackbot-staging
heroku addons:create heroku-redis:mini --app goose-slackbot-staging

# Set config vars
heroku config:set ENVIRONMENT=staging --app goose-slackbot-staging

# Deploy
git push https://git.heroku.com/goose-slackbot-staging.git main
```

### Scale Your App

```bash
# Scale up dynos
heroku ps:scale web=2

# Use larger dyno type
heroku ps:type web=standard-1x

# Enable autoscaling (requires paid plan)
heroku ps:autoscale:enable web --min 1 --max 3
```

---

## 📚 Documentation

**Setup Guides:**
- `GITHUB_DEPLOYMENT_GUIDE.md` - Complete GitHub guide (this file)
- `HEROKU_DEPLOYMENT_GUIDE.md` - Detailed Heroku guide
- `PUBLIC_APP_SETUP_GUIDE.md` - Slack app configuration

**Comparison:**
- `SOCKET_VS_PUBLIC_COMPARISON.md` - Compare deployment methods

**Reference:**
- `README.md` - Project overview
- `USER_MANUAL.md` - How to use
- `ADMIN_GUIDE.md` - Administration
- `FAQ.md` - Common questions

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
- [ ] Socket Mode disabled
- [ ] OAuth redirect URL updated
- [ ] Event subscriptions URL configured
- [ ] Interactivity URL configured
- [ ] Public distribution activated
- [ ] Bot scopes configured

### Testing
- [ ] Health check passes
- [ ] OAuth installation works
- [ ] Bot responds to mentions
- [ ] Bot responds to DMs
- [ ] Query execution works
- [ ] Results formatted correctly

### Monitoring
- [ ] Logs accessible
- [ ] Metrics visible
- [ ] GitHub Actions configured (optional)
- [ ] Backup strategy in place

---

## 🎉 Success!

Your Goose Query Expert Slackbot is now:
- ✅ Version controlled on GitHub
- ✅ Automatically deployed to Heroku
- ✅ Publicly distributed via Slack
- ✅ Monitored and scalable
- ✅ Ready for team collaboration

**Next Steps:**
1. Share with your team
2. Monitor usage and performance
3. Iterate based on feedback
4. Add new features via GitHub PRs

---

## 🆘 Need Help?

**Quick Fixes:**
- Check `heroku logs --tail`
- Verify `heroku config`
- Restart with `heroku restart`

**Documentation:**
- `GITHUB_DEPLOYMENT_GUIDE.md` - Detailed guide
- `TROUBLESHOOTING.md` - Common issues
- `FAQ.md` - Frequently asked questions

**Still stuck?**
- Review Heroku logs for errors
- Check Slack API logs
- Verify all environment variables are set

---

## 🚀 Quick Command Reference

```bash
# Deploy
git push origin main  # Auto-deploys to Heroku

# View logs
heroku logs --tail

# Check status
heroku ps

# Restart app
heroku restart

# Run migrations
heroku run python scripts/db_migrate.py up

# Open app
heroku open

# Access database
heroku pg:psql

# Check config
heroku config
```

---

**Happy deploying! 🎉🚀📊**

---

*Last updated: 2025-10-29*
*Version: 2.0.0 - GitHub Deployment*
