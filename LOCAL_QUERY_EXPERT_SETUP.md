# 🏠 Connect Slackbot to Your Local Goose Query Expert

## What This Does

Allows your Heroku Slackbot to use **your local Goose installation** with Query Expert, so it can access your actual Snowflake data and query history.

## Architecture

```
Slack → Heroku Bot → ngrok tunnel → Your Mac → Goose Query Expert → Snowflake
```

## Prerequisites

✅ Goose installed locally (you have this)
✅ Query Expert extension enabled in Goose
✅ Query Expert configured with Snowflake credentials

## Step-by-Step Setup

### 1. Install ngrok (if not already installed)

```bash
brew install ngrok
```

Or download from: https://ngrok.com/download

### 2. Start the Local MCP Server

In your terminal:

```bash
cd /Users/rleach/goose-slackbot
python3 mcp_server.py
```

You should see:
```
🚀 Starting Goose Query Expert MCP Server...
📡 This will expose your local Goose Query Expert to the Slackbot
🔒 Make sure Query Expert extension is enabled in your Goose config

INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8765
```

**Keep this terminal window open!**

### 3. Start ngrok Tunnel (in a NEW terminal)

```bash
ngrok http 8765
```

You'll see something like:
```
Session Status                online
Account                       your-account
Forwarding                    https://abc123.ngrok.io -> http://localhost:8765
```

**Copy that `https://abc123.ngrok.io` URL!**

### 4. Configure Heroku

Go to: https://dashboard.heroku.com/apps/goose-query-expert-bot/settings

Click "Reveal Config Vars" and set:

```
MOCK_MODE = false
GOOSE_MCP_SERVER_URL = https://abc123.ngrok.io  (your ngrok URL)
```

### 5. Restart Heroku

```bash
# In Heroku dashboard, click "More" → "Restart all dynos"
```

Or in terminal (if you have Heroku CLI):
```bash
heroku restart -a goose-query-expert-bot
```

### 6. Test in Slack!

```
@goose query expert What tables do we have for revenue data?
```

You should now see **real** results from your Query Expert!

## 🔍 Verify It's Working

### Check MCP Server Logs
In the terminal where `mcp_server.py` is running, you should see:
```
INFO: Received MCP request tool=queryexpert__find_table_meta_data
INFO: Calling Goose tool tool=queryexpert__find_table_meta_data
```

### Check Heroku Logs
```bash
heroku logs --tail -a goose-query-expert-bot
```

Look for:
```
Processing question with Query Expert query=...
Query completed successfully
```

## ⚠️ Important Notes

### ngrok URL Changes
- Free ngrok URLs change every time you restart ngrok
- You'll need to update `GOOSE_MCP_SERVER_URL` in Heroku each time
- Consider getting a paid ngrok account for a static URL

### Keep Terminals Open
You need to keep **both** terminals running:
1. `python3 mcp_server.py` (MCP server)
2. `ngrok http 8765` (tunnel)

### Alternative: Use the Helper Script

Instead of steps 2-3, you can run:
```bash
./start_local_mcp.sh
```

This starts both the MCP server and ngrok in one command.

## 🐛 Troubleshooting

### "goose: command not found"
Make sure Goose is in your PATH:
```bash
which goose
```

### "Query Expert extension not found"
Check your Goose config has Query Expert enabled:
```bash
goose config show
```

### Bot still returns mock data
1. Verify `MOCK_MODE=false` in Heroku config vars
2. Verify `GOOSE_MCP_SERVER_URL` is set to your ngrok URL
3. Restart Heroku dyno
4. Check MCP server is running and accessible

### Connection timeout
- Check ngrok tunnel is running
- Test the URL: `curl https://your-ngrok-url.ngrok.io/health`
- Should return: `{"status":"healthy"}`

## 🎯 Production Alternative

For production use (not requiring your laptop to be on), consider:

1. **Deploy MCP server to Heroku** (separate app)
2. **Use Goose Cloud** (if available)
3. **Direct Snowflake integration** (bypass Goose entirely)

---

**Ready to try it?** Start with step 1! 🚀
