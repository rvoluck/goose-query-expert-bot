# 🌐 Public Slack App Distribution Setup Guide

## Overview

To distribute your Goose Query Expert bot publicly (or to the Slack App Directory), you need to:

1. **Disable Socket Mode** (not allowed for public apps)
2. **Enable Events API** with a public webhook URL
3. **Configure OAuth & Redirect URLs**
4. **Set up public hosting** (the app needs to be accessible from the internet)
5. **Enable Public Distribution**

---

## 🚨 Key Requirements for Public Distribution

### What Changes:
- ❌ **Socket Mode** → ✅ **Events API with webhooks**
- ❌ **App-level tokens** → ✅ **OAuth flow**
- ❌ **Local hosting** → ✅ **Public HTTPS endpoint**
- ❌ **Manual installation** → ✅ **OAuth installation flow**

### What You Need:
1. **Public domain/URL** (e.g., `https://goose-bot.yourcompany.com`)
2. **SSL certificate** (HTTPS required)
3. **Web server** to receive webhooks
4. **Database** to store team tokens (multi-workspace support)

---

## 📋 Step-by-Step Configuration

### PART 1: Prepare Your Infrastructure

#### Option A: Use a Cloud Platform (Recommended)

**Heroku (Easiest)**
```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku

# Login and create app
heroku login
heroku create goose-query-expert-bot

# Your URL will be: https://goose-query-expert-bot.herokuapp.com
```

**AWS / GCP / Azure**
- Deploy to ECS, Cloud Run, or App Service
- Get a public URL with HTTPS
- Example: `https://goose-bot.yourcompany.com`

**Ngrok (Testing Only)**
```bash
# Install ngrok
brew install ngrok

# Start tunnel (keep this running)
ngrok http 3000

# You'll get: https://abc123.ngrok.io
# ⚠️ This URL changes each time - not for production!
```

#### Option B: Use Your Own Server
- Set up a server with public IP
- Configure DNS: `goose-bot.yourcompany.com`
- Install SSL certificate (Let's Encrypt)
- Open port 443 (HTTPS)

---

### PART 2: Update Slack App Configuration

Go to https://api.slack.com/apps → Select your app

#### 1. Disable Socket Mode
1. Click **"Socket Mode"** in left sidebar
2. Toggle **OFF**
3. Confirm the change

#### 2. Configure Event Subscriptions
1. Click **"Event Subscriptions"** in left sidebar
2. Toggle **"Enable Events"** to **ON**
3. **Request URL**: Enter your public URL + `/slack/events`
   ```
   https://goose-query-expert-bot.herokuapp.com/slack/events
   ```
4. Slack will send a challenge request - your app must respond
5. Subscribe to bot events (same as before):
   - `app_mention`
   - `message.channels`
   - `message.groups`
   - `message.im`
   - `message.mpim`
6. Click **"Save Changes"**

#### 3. Configure Interactive Components
1. Click **"Interactivity & Shortcuts"** in left sidebar
2. Toggle **ON**
3. **Request URL**: Enter your public URL + `/slack/interactions`
   ```
   https://goose-query-expert-bot.herokuapp.com/slack/interactions
   ```
4. Click **"Save Changes"**

#### 4. Configure OAuth & Permissions
1. Click **"OAuth & Permissions"** in left sidebar
2. **Redirect URLs** → Click **"Add New Redirect URL"**
3. Add your OAuth callback URL:
   ```
   https://goose-query-expert-bot.herokuapp.com/slack/oauth_redirect
   ```
4. Click **"Add"** then **"Save URLs"**

#### 5. Enable Public Distribution
1. Click **"Manage Distribution"** in left sidebar
2. Review the checklist:
   - ✅ App name and description
   - ✅ App icon uploaded
   - ✅ OAuth redirect URLs configured
   - ✅ Events API configured
   - ✅ Required scopes added
3. Click **"Activate Public Distribution"**
4. You'll get a **shareable install link**:
   ```
   https://slack.com/oauth/v2/authorize?client_id=YOUR_CLIENT_ID&scope=...
   ```

---

### PART 3: Update Your Application Code

I'll create the updated code for you that supports:
- ✅ Events API (webhook-based)
- ✅ OAuth flow (multi-workspace)
- ✅ Token storage per workspace
- ✅ Public distribution

---

## 🔧 Architecture Changes

### Before (Socket Mode):
```
Slack ←→ WebSocket ←→ Your App (local)
```

### After (Events API):
```
Slack → HTTPS POST → Your App (public)
                    ↓
              Store tokens in DB
              Process events
              Respond to Slack
```

---

## 🗄️ Database Schema for Multi-Workspace

You'll need to store OAuth tokens for each workspace that installs your app:

```sql
CREATE TABLE slack_installations (
    id UUID PRIMARY KEY,
    team_id VARCHAR(50) UNIQUE NOT NULL,
    team_name VARCHAR(255),
    bot_token TEXT NOT NULL,  -- xoxb-... token
    bot_user_id VARCHAR(50),
    scope TEXT,
    installed_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📝 Environment Variables Update

Your `.env` will change:

### Remove (Socket Mode):
```bash
# SLACK_APP_TOKEN=xapp-...  ← Remove this
```

### Add (OAuth):
```bash
# Slack OAuth Configuration
SLACK_CLIENT_ID=1234567890.1234567890
SLACK_CLIENT_SECRET=abcdef1234567890abcdef1234567890
SLACK_SIGNING_SECRET=your-signing-secret

# Public URL (your deployed app)
PUBLIC_URL=https://goose-query-expert-bot.herokuapp.com

# OAuth redirect
SLACK_OAUTH_REDIRECT_URL=https://goose-query-expert-bot.herokuapp.com/slack/oauth_redirect
```

---

## 🚀 Deployment Options

### Option 1: Heroku (Easiest)

**Pros:**
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Easy deployment
- ✅ Built-in PostgreSQL

**Setup:**
```bash
# Create Heroku app
heroku create goose-query-expert-bot

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Add Redis
heroku addons:create heroku-redis:mini

# Set environment variables
heroku config:set SLACK_CLIENT_ID=your-client-id
heroku config:set SLACK_CLIENT_SECRET=your-client-secret
heroku config:set SLACK_SIGNING_SECRET=your-signing-secret

# Deploy
git push heroku main

# Your app is now at:
# https://goose-query-expert-bot.herokuapp.com
```

### Option 2: AWS (Production)

**Use:**
- ECS/Fargate for containers
- RDS for PostgreSQL
- ElastiCache for Redis
- ALB for load balancing
- Route53 for DNS

### Option 3: Google Cloud (Production)

**Use:**
- Cloud Run for containers
- Cloud SQL for PostgreSQL
- Memorystore for Redis
- Cloud Load Balancing
- Cloud DNS

### Option 4: Railway (Easy Alternative)

**Pros:**
- Similar to Heroku
- Free tier
- Easy deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

---

## 🔐 Security Considerations

### 1. Verify Slack Requests
Always verify the signing secret:
```python
import hmac
import hashlib

def verify_slack_signature(request_body, timestamp, signature, signing_secret):
    basestring = f"v0:{timestamp}:{request_body}"
    my_signature = 'v0=' + hmac.new(
        signing_secret.encode(),
        basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(my_signature, signature)
```

### 2. Store Tokens Securely
- Encrypt tokens in database
- Use environment variables
- Never commit tokens to git
- Rotate secrets regularly

### 3. Rate Limiting
- Implement per-workspace rate limits
- Prevent abuse
- Monitor usage

---

## 📊 Multi-Workspace Support

When multiple workspaces install your app, you need to:

1. **Store each workspace's token**
2. **Look up the correct token** when receiving events
3. **Handle OAuth installation flow**
4. **Support uninstallation**

Example flow:
```
1. User clicks "Add to Slack" button
2. Redirected to Slack OAuth page
3. User authorizes
4. Slack redirects to your OAuth callback
5. You receive bot token
6. Store token in database with team_id
7. When event arrives, look up token by team_id
8. Use that token to respond
```

---

## 🧪 Testing Public Distribution

### 1. Test OAuth Flow
```bash
# Visit your install URL
https://slack.com/oauth/v2/authorize?client_id=YOUR_CLIENT_ID&scope=...

# Complete installation
# Check database for stored token
```

### 2. Test Event Webhooks
```bash
# Slack will POST to your /slack/events endpoint
# Check logs to see events arriving
heroku logs --tail
```

### 3. Test Multi-Workspace
- Install in a test workspace
- Install in another test workspace
- Verify both work independently

---

## 📋 Checklist for Public Distribution

- [ ] Public HTTPS URL configured
- [ ] Socket Mode disabled
- [ ] Events API enabled with webhook URL
- [ ] Interactive Components configured
- [ ] OAuth redirect URLs added
- [ ] Public Distribution activated
- [ ] Database for token storage set up
- [ ] OAuth flow implemented
- [ ] Webhook endpoints implemented
- [ ] Signature verification working
- [ ] Multi-workspace support tested
- [ ] App icon uploaded
- [ ] App description written
- [ ] Privacy policy URL added (required)
- [ ] Support email configured

---

## 🌐 Required URLs for Public Apps

You need to provide these URLs in your app configuration:

1. **Privacy Policy URL** (required)
   - Example: `https://yourcompany.com/privacy`
   - Can be a simple page explaining data handling

2. **Support Email** (required)
   - Example: `support@yourcompany.com`

3. **App Homepage** (optional)
   - Example: `https://yourcompany.com/goose-bot`

---

## 🚨 Important Notes

### Limitations of Public Distribution:
1. **Must be publicly accessible** - Can't be behind VPN
2. **HTTPS required** - No HTTP allowed
3. **Webhook-based** - No Socket Mode
4. **Multi-tenant** - Must support multiple workspaces
5. **OAuth flow** - Users install via OAuth
6. **Review process** - Slack reviews public apps

### Timeline:
- **Development**: 2-3 days to convert code
- **Testing**: 1-2 days
- **Deployment**: 1 day
- **Slack Review**: 1-2 weeks (if submitting to directory)

---

## 🎯 Next Steps

1. **Choose hosting platform** (Heroku recommended for start)
2. **Get public URL** with HTTPS
3. **I'll create the updated code** for Events API + OAuth
4. **Deploy to hosting platform**
5. **Configure Slack app settings**
6. **Test OAuth flow**
7. **Enable public distribution**

---

## 💡 Quick Decision: Do You Need Public Distribution?

**You DON'T need public distribution if:**
- Only your organization will use it
- You can get IT approval for internal app
- Socket Mode is acceptable

**You DO need public distribution if:**
- Multiple organizations will use it
- Submitting to Slack App Directory
- IT requires "official" Slack apps
- Want anyone to install it

---

## 🆘 Alternative: Request Internal App Approval

**Instead of public distribution, try:**

1. **Request exception from IT**
   - Explain it's internal-only
   - Show security measures
   - Offer to host on company infrastructure

2. **Deploy on company infrastructure**
   - Use company AWS/GCP account
   - Behind company VPN
   - Internal domain (goose-bot.internal.company.com)

3. **Use Socket Mode internally**
   - Simpler architecture
   - No public webhooks needed
   - Easier to secure

---

**Ready to proceed? Let me know:**
1. **Which hosting platform** do you want to use?
2. **Do you have a public domain** available?
3. **Should I create the updated code** for Events API + OAuth?

I'll help you through the entire conversion! 🚀
