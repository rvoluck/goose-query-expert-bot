# 🎯 Simple Heroku MCP Setup

Since we can't have two Procfiles in one repo, here's the easiest approach:

## Option A: Use the Same Repo (Recommended)

We'll configure Heroku to use different files for each app.

### For the MCP Server App:

When you create the MCP server app in Heroku, you'll need to tell it which file to run.

**In the Heroku Dashboard for your MCP server:**

1. Go to **Settings** tab
2. Click **"Reveal Config Vars"**
3. Add:
   ```
   PROCFILE = web: python3 mcp_server_heroku.py
   ```

Actually, simpler approach - let's just add the MCP server as a worker process to your existing app!

## ✅ EASIEST SOLUTION: Add MCP as Second Process

Update your existing Procfile to run BOTH:

