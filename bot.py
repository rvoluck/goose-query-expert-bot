"""
Ultra-simple Slack bot - Socket Mode
No database, no OAuth, just pure bot token
"""

import os
import asyncio
import re
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from aiohttp import web

# Get tokens
BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
APP_TOKEN = os.environ["SLACK_APP_TOKEN"]

print(f"🚀 Starting bot...")
print(f"Bot token: {BOT_TOKEN[:20]}...")
print(f"App token: {APP_TOKEN[:20]}...")

# Create app with single-workspace authorization (no OAuth)
# This bypasses the installation store completely
async def authorize():
    """Simple authorization - just return the bot token"""
    from slack_bolt.authorization import AuthorizeResult
    return AuthorizeResult(
        bot_token=BOT_TOKEN,
        bot_id=None,
        bot_user_id=None,
    )

app = AsyncApp(
    authorize=authorize,
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET", ""),
    process_before_response=True
)

@app.event("app_mention")
async def mention_handler(event, say):
    """Handle @mentions"""
    print(f"📨 Got mention: {event}")
    
    user = event["user"]
    text = re.sub(r'<@[A-Z0-9]+>', '', event.get("text", "")).strip()
    
    await say(
        text=f"👋 Hi <@{user}>! You said: '{text}'\n\n✅ **IT WORKS!**",
        thread_ts=event.get("ts")
    )
    print("✅ Sent response!")

async def health_server():
    """Health check server"""
    async def health(request):
        return web.json_response({"status": "ok"})
    
    app_web = web.Application()
    app_web.router.add_get('/health', health)
    app_web.router.add_get('/', health)
    
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()
    print(f"🌐 Health server ready")

async def main():
    await health_server()
    handler = AsyncSocketModeHandler(app, APP_TOKEN)
    print("🔌 Connecting...")
    await handler.start_async()
    print("✅ CONNECTED! Bot is live!")
    
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
