# 🚀 Deploy Your Slackbot NOW - Step by Step

## Prerequisites Needed

Before we can deploy, you need to set up a Slack app and get credentials.

---

## STEP 1: Create Slack App (10 minutes)

### 1.1 Go to Slack API
Visit: https://api.slack.com/apps

### 1.2 Create New App
1. Click "Create New App"
2. Choose "From scratch"
3. Name: "Goose Query Expert"
4. Select your workspace
5. Click "Create App"

### 1.3 Configure Bot Token Scopes
1. Go to "OAuth & Permissions" in left sidebar
2. Scroll to "Bot Token Scopes"
3. Add these scopes:
   - `chat:write`
   - `chat:write.public`
   - `files:write`
   - `users:read`
   - `channels:read`
   - `groups:read`
   - `im:read`
   - `mpim:read`
   - `app_mentions:read`
   - `commands`

### 1.4 Enable Socket Mode
1. Go to "Socket Mode" in left sidebar
2. Enable Socket Mode
3. Give it a name: "Goose Bot Socket"
4. Copy the **App-Level Token** (starts with `xapp-`)
   - Save this as: `SLACK_APP_TOKEN`

### 1.5 Enable Events
1. Go to "Event Subscriptions"
2. Enable Events
3. Subscribe to bot events:
   - `app_mention`
   - `message.channels`
   - `message.groups`
   - `message.im`
   - `message.mpim`

### 1.6 Install App to Workspace
1. Go to "Install App" in left sidebar
2. Click "Install to Workspace"
3. Authorize the app
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)
   - Save this as: `SLACK_BOT_TOKEN`

### 1.7 Get Signing Secret
1. Go to "Basic Information"
2. Scroll to "App Credentials"
3. Copy the **Signing Secret**
   - Save this as: `SLACK_SIGNING_SECRET`

---

## STEP 2: Configure Environment

Once you have the three Slack credentials, provide them to me:

```
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_APP_TOKEN=xapp-your-token-here
SLACK_SIGNING_SECRET=your-secret-here
```

---

## STEP 3: Choose Deployment Mode

### Option A: Simple Local Mode (Fastest - No Docker)
- Runs on your Mac
- Uses SQLite instead of PostgreSQL
- No Redis (in-memory cache)
- Perfect for testing
- **Time: 5 minutes**

### Option B: Docker Development Mode
- Full stack with PostgreSQL + Redis
- Requires Docker Desktop
- Production-like environment
- **Time: 15 minutes**

### Option C: Production Deployment
- Kubernetes or cloud platform
- Full monitoring stack
- Auto-scaling
- **Time: 1-2 hours**

---

## What I Need From You

**Please provide:**

1. **Your Slack credentials** (from Step 1 above)
   - SLACK_BOT_TOKEN
   - SLACK_APP_TOKEN
   - SLACK_SIGNING_SECRET

2. **Deployment preference:**
   - Option A: Simple local (recommended to start)
   - Option B: Docker development
   - Option C: Production deployment

3. **Goose Query Expert access:**
   - Do you have Goose running with Query Expert extension?
   - What's the MCP server URL? (or should we use mock mode for testing?)

---

## Once You Provide This Info

I will:
1. ✅ Create your `.env` file with proper configuration
2. ✅ Set up the database
3. ✅ Install dependencies
4. ✅ Create initial admin user
5. ✅ Start the bot
6. ✅ Test with a sample query
7. ✅ Give you the invite link for your team

---

## Quick Test Mode (No Slack App Needed)

If you want to test the code first without setting up Slack:

```bash
cd /Users/rleach/goose-slackbot

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Test individual components
python config.py
python goose_client.py
python database.py
```

---

## Ready to Deploy?

**Reply with:**
1. Your three Slack credentials
2. Your deployment preference (A, B, or C)
3. Goose Query Expert setup (URL or mock mode)

And I'll deploy it immediately! 🚀
