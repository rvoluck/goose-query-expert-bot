"""
Startup script that launches either the Slackbot or MCP server
Based on APP_TYPE environment variable
"""

import os
import sys
import subprocess

app_type = os.environ.get("APP_TYPE", "slackbot").lower()

if app_type == "mcp":
    print("🚀 Starting MCP Server...")
    import mcp_server_heroku
    mcp_server_heroku.run_server()
elif app_type == "slackbot":
    print("🤖 Starting Slackbot...")
    # Run bot.py as a subprocess since it has its own event loop
    subprocess.run([sys.executable, "bot.py"])
else:
    print(f"❌ Unknown APP_TYPE: {app_type}")
    print("Set APP_TYPE to 'slackbot' or 'mcp'")
    sys.exit(1)
