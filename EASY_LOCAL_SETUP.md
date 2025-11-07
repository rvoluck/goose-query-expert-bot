# 🚀 Easy Setup: Connect Bot to Your Local Goose

## ✅ No Dependencies Needed!

I created a simple MCP server that uses **only Python standard library** - no pip installs required!

## Quick Start (3 Steps)

### Step 1: Start the MCP Server

```bash
cd /Users/rleach/goose-slackbot
python3 simple_mcp_server.py
```

You should see:
```
============================================================
🚀 Goose Query Expert MCP Server
============================================================
📡 Listening on: http://0.0.0.0:8765
🔍 Health check: http://localhost:8765/health
📬 MCP endpoint: http://localhost:8765/mcp

✅ Ready to receive requests from Slackbot!
💡 Make sure Goose Query Expert extension is enabled

Press Ctrl+C to stop
============================================================
```

**Keep this terminal open!**

### Step 2: Start ngrok Tunnel

Open a **NEW terminal** and run:

```bash
ngrok http 8765
```

You'll see:
```
Forwarding   https://abc123.ngrok.io -> http://localhost:8765
```

**Copy that `https://...ngrok.io` URL!**

### Step 3: Configure Heroku

1. Go to: https://dashboard.heroku.com/apps/goose-query-expert-bot/settings
2. Click "Reveal Config Vars"
3. Set these values:
   - `MOCK_MODE` = `false`
   - `GOOSE_MCP_SERVER_URL` = `https://your-ngrok-url.ngrok.io`
4. Click "More" → "Restart all dynos"

### Step 4: Test in Slack!

```
@goose query expert What tables do we have for revenue?
```

## 🔍 Verify It's Working

### In Terminal 1 (MCP Server)
You should see:
```
📨 Received MCP request: queryexpert__find_table_meta_data
🔧 Calling: goose toolkit call queryexpert__find_table_meta_data...
✅ Sent response
```

### In Slack
You should get a real response with:
- Actual tables from your Snowflake
- Real similar queries from your team
- Generated SQL that makes sense
- Actual query results

## ⚠️ Important Notes

### Keep Both Terminals Running
- Terminal 1: `python3 simple_mcp_server.py`
- Terminal 2: `ngrok http 8765`

### ngrok URL Changes
Free ngrok URLs change every restart. When you restart ngrok:
1. Copy the new URL
2. Update `GOOSE_MCP_SERVER_URL` in Heroku
3. Restart Heroku dyno

### Your Laptop Must Be On
The bot only works while:
- Your laptop is on
- Both terminals are running
- You're connected to internet

## 🐛 Troubleshooting

### "goose: command not found"
Make sure Goose is installed:
```bash
which goose
```

If not found, install Goose or add it to your PATH.

### Bot still returns mock data
1. Check `MOCK_MODE=false` in Heroku config vars
2. Check `GOOSE_MCP_SERVER_URL` is your ngrok URL
3. Restart Heroku: "More" → "Restart all dynos"
4. Test MCP server: `curl https://your-ngrok-url.ngrok.io/health`

### "Query Expert extension not found"
Make sure Query Expert is enabled in Goose:
```bash
goose config show
```

### Connection timeout
- Is MCP server running? Check Terminal 1
- Is ngrok running? Check Terminal 2
- Test locally: `curl http://localhost:8765/health`
- Test ngrok: `curl https://your-ngrok-url.ngrok.io/health`

## 📊 What You'll See

### Before (Mock Mode):
```
📊 Query Analysis Results
Your Question: What was our revenue?

Relevant Tables Found:
• ANALYTICS.SALES.REVENUE_BY_CATEGORY - Daily revenue...
(fake sample data)
```

### After (Real Query Expert):
```
📊 Query Analysis Results
Your Question: What was our revenue?

Relevant Tables Found:
• YOUR_ACTUAL_SCHEMA.YOUR_ACTUAL_TABLE - Real description
(real tables from your Snowflake!)

Generated SQL:
SELECT ... (real SQL that works!)

Results Summary:
• Found X rows (real data!)
```

---

**Ready to try?** Just run `python3 simple_mcp_server.py`! 🎉
