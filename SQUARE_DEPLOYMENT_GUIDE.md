# 🚀 Square Cloud CD Deployment Guide

**Deploy your Goose Query Expert Slackbot using Square's Cloud CD platform**

See: [go/ccd](https://go/ccd) for Cloud CD documentation

---

## 📋 **PREREQUISITES**

### **1. Access Required**
- [ ] Square GitHub access
- [ ] Cloud CD access (request via go/ccd)
- [ ] Secret Manager access (for storing credentials)
- [ ] Registry access (request if needed)

### **2. Credentials to Gather**
- [ ] Slack Bot Token (`xoxb-...`)
- [ ] Slack Client ID
- [ ] Slack Client Secret
- [ ] Slack Signing Secret
- [ ] Slack App ID

---

## 🚀 **DEPLOYMENT STEPS**

### **STEP 1: Push Code to Square GitHub**

```bash
cd /Users/rleach/goose-slackbot

# Add Square GitHub remote (if not already added)
git remote add square git@git.sqprod.co:your-team/goose-query-expert-bot.git

# Push to Square GitHub
git push square main
```

**Don't have a Square GitHub repo yet?**
1. Go to [git.sqprod.co](https://git.sqprod.co)
2. Create new repository: `goose-query-expert-bot`
3. Add your team as collaborators

---

### **STEP 2: Store Secrets in Secret Manager**

Go to Square's Secret Manager and create these secrets:

```bash
# Slack credentials
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CLIENT_ID=your-client-id
SLACK_CLIENT_SECRET=your-client-secret
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_ID=your-app-id
SLACK_OAUTH_REDIRECT_URL=https://goose-slackbot.sqprod.co/slack/oauth_redirect

# Security keys (generate new ones)
JWT_SECRET_KEY=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Database (will be auto-provisioned by SKI)
DATABASE_URL=postgresql://goose_user:password@postgres:5432/goose_slackbot

# Redis (will be auto-provisioned by SKI)
REDIS_URL=redis://:password@redis:6379/0

# Snowflake (if needed)
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_PASSWORD=your-password
```

**How to add secrets:**
1. Go to [go/secrets](https://go/secrets) or your team's secret manager
2. Create a new secret group: `goose-query-expert-bot`
3. Add each secret listed above
4. Grant access to your SKI service

---

### **STEP 3: Onboard to Cloud CD**

Follow the Cloud CD onboarding guide:

```bash
# 1. Install Cloud CD CLI (if needed)
brew install square/tap/ccd

# 2. Initialize Cloud CD in your repo
ccd init

# 3. Validate your configuration
ccd validate

# 4. Create deployment pipeline
ccd create-pipeline
```

**Or manually:**
1. Go to [go/ccd](https://go/ccd)
2. Click "Onboard New Service"
3. Select your GitHub repo
4. Follow the onboarding wizard

---

### **STEP 4: Configure Databases**

Your `ski.yaml` already includes PostgreSQL and Redis dependencies. Cloud CD will automatically provision them.

**To verify:**
```bash
ccd status goose-query-expert-bot
```

**To connect manually (for testing):**
```bash
ccd db-connect goose-query-expert-bot --env staging
```

---

### **STEP 5: Deploy to Staging**

Once onboarded, Cloud CD will automatically deploy to staging when you push to `main`:

```bash
# Push to main branch
git push square main

# Watch deployment
ccd watch goose-query-expert-bot --env staging

# Check status
ccd status goose-query-expert-bot --env staging

# View logs
ccd logs goose-query-expert-bot --env staging --follow
```

**Get your staging URL:**
```bash
ccd url goose-query-expert-bot --env staging
```

Should be something like: `https://goose-slackbot-staging.sqprod.co`

---

### **STEP 6: Test in Staging**

1. **Test health endpoint:**
   ```bash
   curl https://goose-slackbot-staging.sqprod.co/health
   ```

2. **Update Slack app with staging URL** (for testing):
   - Event Subscriptions: `https://goose-slackbot-staging.sqprod.co/slack/events`
   - Interactivity: `https://goose-slackbot-staging.sqprod.co/slack/events`
   - OAuth Redirect: `https://goose-slackbot-staging.sqprod.co/slack/oauth_redirect`

3. **Test in a Slack channel:**
   - @mention the bot
   - Try a query

---

### **STEP 7: Deploy to Production**

Once staging is working, promote to production:

```bash
# Option 1: Auto-deploy (if enabled in env.yaml)
# Just push to main and it will auto-deploy after approval

# Option 2: Manual promotion
ccd promote goose-query-expert-bot --from staging --to production

# Option 3: Via Console UI
# Go to go/console and click "Deploy to Production"
```

**Production URL:**
```bash
ccd url goose-query-expert-bot --env production
```

Should be: `https://goose-slackbot.sqprod.co`

---

### **STEP 8: Update Slack App for Production**

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click your app
3. Update URLs:
   - Event Subscriptions: `https://goose-slackbot.sqprod.co/slack/events`
   - Interactivity: `https://goose-slackbot.sqprod.co/slack/events`
   - OAuth Redirect: `https://goose-slackbot.sqprod.co/slack/oauth_redirect`

4. Get shareable URL for security team:
   - Go to **Manage Distribution**
   - Copy the shareable URL
   - Send to security team for approval

---

## 📊 **MONITORING & OPERATIONS**

### **View Logs**
```bash
# Staging logs
ccd logs goose-query-expert-bot --env staging --follow

# Production logs
ccd logs goose-query-expert-bot --env production --follow

# Filter by error level
ccd logs goose-query-expert-bot --env production --level error
```

### **Check Metrics**
```bash
# Service metrics
ccd metrics goose-query-expert-bot --env production

# Or view in Datadog
# Go to go/datadog and search for "goose-query-expert-bot"
```

### **Scale Service**
```bash
# Scale up
ccd scale goose-query-expert-bot --env production --replicas 5

# Scale down
ccd scale goose-query-expert-bot --env production --replicas 2
```

### **Rollback**
```bash
# Automatic rollback is enabled in ski.yaml
# Manual rollback:
ccd rollback goose-query-expert-bot --env production

# Rollback to specific version
ccd rollback goose-query-expert-bot --env production --version v1.2.3
```

---

## 🔧 **TROUBLESHOOTING**

### **Deployment Stuck**
```bash
# Check deployment status
ccd status goose-query-expert-bot --env staging

# View events
ccd events goose-query-expert-bot --env staging

# Cancel stuck deployment
ccd cancel goose-query-expert-bot --env staging
```

### **Health Check Failing**
```bash
# Check health endpoint directly
curl https://goose-slackbot-staging.sqprod.co/health

# View detailed logs
ccd logs goose-query-expert-bot --env staging --tail 100

# SSH into pod (if needed)
ccd ssh goose-query-expert-bot --env staging
```

### **Database Connection Issues**
```bash
# Verify database is running
ccd db-status goose-query-expert-bot --env staging

# Test connection
ccd db-connect goose-query-expert-bot --env staging

# View database logs
ccd db-logs goose-query-expert-bot --env staging
```

### **Secrets Not Loading**
```bash
# Verify secrets exist
ccd secrets list goose-query-expert-bot

# Verify service has access
ccd secrets verify goose-query-expert-bot

# Refresh secrets
ccd secrets refresh goose-query-expert-bot --env staging
```

---

## 🆘 **GETTING HELP**

### **Cloud CD Support**
- **Slack:** [#blockplat-helpchannel](https://square.slack.com/archives/blockplat-helpchannel)
- **Hours:** 9am-5pm PT
- **Emergency:** Page Cloud CD oncall

### **Documentation**
- [go/ccd](https://go/ccd) - Cloud CD main docs
- [go/ski](https://go/ski) - SKI documentation
- [go/ccd-faq](https://go/ccd-faq) - FAQ

### **Raise a Ticket**
In `#blockplat-helpchannel`:
```
/ticket create
Title: Goose Slackbot deployment issue
Description: [your issue]
Priority: [normal/urgent]
```

---

## ✅ **DEPLOYMENT CHECKLIST**

### **Pre-Deployment**
- [ ] Code pushed to Square GitHub
- [ ] All secrets stored in Secret Manager
- [ ] `ski.yaml` and `env.yaml` configured
- [ ] Onboarded to Cloud CD
- [ ] Databases provisioned

### **Staging Deployment**
- [ ] Deployed to staging
- [ ] Health check passing
- [ ] Slack URLs updated for staging
- [ ] Tested @mentions in Slack
- [ ] Tested slash commands
- [ ] Reviewed logs for errors

### **Production Deployment**
- [ ] Staging tests passed
- [ ] Approval obtained (if required)
- [ ] Deployed to production
- [ ] Health check passing
- [ ] Slack URLs updated for production
- [ ] Monitoring alerts configured
- [ ] Shared installation link with security team

### **Post-Deployment**
- [ ] Monitored for 24 hours
- [ ] No critical alerts
- [ ] User feedback collected
- [ ] Documentation updated

---

## 🎯 **QUICK REFERENCE**

```bash
# Common commands
ccd status <service>                    # Check status
ccd logs <service> --follow             # View logs
ccd deploy <service> --env <env>        # Deploy
ccd rollback <service> --env <env>      # Rollback
ccd scale <service> --replicas <n>      # Scale
ccd url <service> --env <env>           # Get URL

# Deployment workflow
git push square main                    # Push code
ccd watch <service> --env staging       # Watch deployment
ccd promote <service> --to production   # Promote to prod
```

---

**Ready to deploy?** 🚀

1. Push code to Square GitHub
2. Store secrets
3. Run `ccd init`
4. Watch it deploy!

Questions? Ask in [#blockplat-helpchannel](https://square.slack.com/archives/blockplat-helpchannel)
