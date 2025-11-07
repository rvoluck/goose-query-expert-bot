# 🚀 Deploy MCP Server to Heroku (Super Easy!)

We'll create a **second Heroku app** that runs the MCP server from the same GitHub repo.

## Quick Setup (5 Minutes)

### Step 1: Create MCP Server App

1. Go to: https://dashboard.heroku.com/
2. Click **"New"** → **"Create new app"**
3. App name: `goose-mcp-server` (or your choice)
4. Click **"Create app"**

### Step 2: Connect to Your GitHub Repo

In the new app's dashboard:

1. **Deploy** tab → **"GitHub"** → **"Connect to GitHub"**
2. Search for: `goose-query-expert-bot`
3. Click **"Connect"**
4. Enable **"Automatic deploys"** from `main` branch

### Step 3: Configure the MCP App

Go to **Settings** tab → **"Reveal Config Vars"**:

Add these:
```
APP_TYPE = mcp
MOCK_MODE = true
```

That's it! The `APP_TYPE=mcp` tells it to run the MCP server instead of the Slackbot.

### Step 4: Deploy

**Deploy** tab → **"Manual deploy"** → **"Deploy Branch"**

Wait for build to complete...

### Step 5: Test MCP Server

Click **"Open app"** or visit:
```
https://goose-mcp-server.herokuapp.com/health
```

Should see:
```json
{"status": "healthy", "service": "goose-mcp-server", "mode": "heroku"}
```

✅ MCP Server is running!

### Step 6: Connect Slackbot to MCP Server

Go to your **Slackbot** app:
https://dashboard.heroku.com/apps/goose-query-expert-bot/settings

**Settings** → **"Reveal Config Vars"** → Update:

```
APP_TYPE = slackbot
MOCK_MODE = false
GOOSE_MCP_SERVER_URL = https://goose-mcp-server.herokuapp.com
```

(Replace with your actual MCP server URL)

**More** → **"Restart all dynos"**

### Step 7: Test in Slack!

```
@goose query expert What tables do we have?
```

## 🔍 How It Works

```
┌─────────────────────────────────────────┐
│  GitHub Repo (goose-query-expert-bot)   │
│  - bot.py (Slackbot code)               │
│  - mcp_server_heroku.py (MCP code)      │
│  - start.py (chooses which to run)      │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────┐       ┌──────────────┐
│ Heroku App 1  │       │ Heroku App 2 │
│ Slackbot      │       │ MCP Server   │
│ APP_TYPE=     │       │ APP_TYPE=mcp │
│  slackbot     │       │              │
└───────────────┘       └──────────────┘
        │                       ▲
        │  Makes requests to    │
        └───────────────────────┘
```

## 🎯 Verify Everything

### Check MCP Server Logs:
In terminal or Heroku dashboard:
```bash
heroku logs --tail -a goose-mcp-server
```

Should see:
```
🚀 Starting MCP Server...
📡 Port: 12345
✅ Ready!
```

### Check Slackbot Logs:
```bash
heroku logs --tail -a goose-query-expert-bot
```

Should see:
```
🤖 Starting Slackbot...
Processing question with Query Expert
```

### Test the Connection:
```bash
curl https://goose-mcp-server.herokuapp.com/health
```

## 🐛 Troubleshooting

### MCP server shows "Application Error"
- Check `APP_TYPE=mcp` is set in MCP app config vars
- Check logs: `heroku logs --tail -a goose-mcp-server`
- Verify code is deployed: Check "Activity" tab

### Slackbot can't connect to MCP
- Test MCP health endpoint (curl command above)
- Verify `GOOSE_MCP_SERVER_URL` in Slackbot config
- Check both apps have dynos running (Resources tab)

### Still getting old responses
- Make sure `MOCK_MODE=false` in **Slackbot** config
- Make sure `MOCK_MODE=true` in **MCP Server** config (for now)
- Restart Slackbot dyno
- Try in a new Slack channel

## 📊 Current Setup

- **MCP Server**: Returns realistic mock data
- **Slackbot**: Connects to MCP server for Query Expert features
- **No laptop needed**: Both run 24/7 on Heroku

## 🎯 Next: Add Real Snowflake

Once this works, you can update the MCP server to query real Snowflake:

1. Add Snowflake credentials to MCP server config vars
2. Update `mcp_server_heroku.py` to use snowflake-connector
3. Set `MOCK_MODE=false` in MCP server

But for now, mock mode gives you realistic responses to test with!

---

**Ready?** Start with Step 1! 🚀
