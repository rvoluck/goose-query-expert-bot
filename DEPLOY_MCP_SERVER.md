# 🚀 Deploy MCP Server to Heroku

This creates a **separate Heroku app** for the MCP server, so your Slackbot can connect to it without needing your laptop on.

## Step-by-Step Deployment

### 1. Create the MCP Server App in Heroku Dashboard

1. Go to: https://dashboard.heroku.com/
2. Click **"New"** → **"Create new app"**
3. App name: `goose-mcp-server` (or whatever you want)
4. Region: United States
5. Click **"Create app"**

### 2. Connect to GitHub

In your new app's dashboard:

1. Go to the **"Deploy"** tab
2. Deployment method: Click **"GitHub"**
3. Click **"Connect to GitHub"**
4. Search for: `goose-query-expert-bot` (your repo)
5. Click **"Connect"**

### 3. Configure the App

Go to the **"Settings"** tab:

#### Add Buildpack:
1. Scroll to "Buildpacks"
2. Click **"Add buildpack"**
3. Select **"Python"**
4. Click **"Save changes"**

#### Set Config Vars:
1. Click **"Reveal Config Vars"**
2. Add these:

```
MOCK_MODE = true
MODE = heroku
```

(We'll start with mock mode, then can add real Snowflake later)

### 4. Deploy

Go back to the **"Deploy"** tab:

1. Scroll to "Manual deploy"
2. Branch: `main`
3. Click **"Deploy Branch"**

Wait for it to build... You'll see:
```
-----> Building on the Heroku-24 stack
-----> Using buildpack: heroku/python
-----> Python app detected
...
-----> Launching...
       Released v1
       https://goose-mcp-server-xxxxx.herokuapp.com/ deployed to Heroku
```

### 5. Test the MCP Server

Click **"Open app"** or visit:
```
https://your-mcp-app-name.herokuapp.com/health
```

You should see:
```json
{"status": "healthy", "service": "goose-mcp-server", "mode": "heroku"}
```

### 6. Configure Your Slackbot to Use It

Go to your **Slackbot app** settings:
https://dashboard.heroku.com/apps/goose-query-expert-bot/settings

1. Click **"Reveal Config Vars"**
2. Update these:

```
MOCK_MODE = false
GOOSE_MCP_SERVER_URL = https://your-mcp-app-name.herokuapp.com
```

3. Go to **"More"** → **"Restart all dynos"**

### 7. Test in Slack!

```
@goose query expert What was our revenue last month?
```

You should now get responses that go through your MCP server!

## 🔍 Verify It's Working

### Check MCP Server Logs:
```bash
heroku logs --tail -a goose-mcp-server
```

You should see:
```
📨 MCP request: queryexpert__find_table_meta_data
✅ Response sent
```

### Check Slackbot Logs:
```bash
heroku logs --tail -a goose-query-expert-bot
```

You should see:
```
Processing question with Query Expert query=...
Query completed successfully
```

## 📊 Architecture

```
Slack User
    ↓
Slackbot (Heroku App 1)
    ↓
MCP Server (Heroku App 2) ← You just deployed this!
    ↓
Mock Data (for now)
```

## 🎯 Next Steps: Add Real Snowflake

Once this is working, you can add real Snowflake credentials to the MCP server:

1. Install snowflake-connector: Add to requirements
2. Set Snowflake config vars in MCP server app
3. Update `mcp_server_heroku.py` to query Snowflake directly
4. Set `MOCK_MODE=false` in MCP server

But for now, mock mode will give you realistic-looking responses to test with!

## 🐛 Troubleshooting

### "Application Error" when opening MCP app
- Check logs: `heroku logs --tail -a goose-mcp-server`
- Make sure Python buildpack is added
- Verify `Procfile.mcp` exists in repo

### Slackbot can't connect to MCP server
- Test MCP health: `curl https://your-mcp-app.herokuapp.com/health`
- Verify `GOOSE_MCP_SERVER_URL` in Slackbot config vars
- Check both apps are running: Dashboard → Resources → dyno ON

### Still getting old mock responses
- Make sure you restarted Slackbot dyno after config change
- Check `MOCK_MODE=false` in **Slackbot** config (not MCP server)
- Clear Slack cache: Quit and reopen Slack

---

**Ready to deploy?** Start with Step 1! 🎉
