"""
Slack Bot using Socket Mode
Simpler than webhooks - uses WebSocket connection
"""

import os
import asyncio
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from aiohttp import web
import structlog

logger = structlog.get_logger(__name__)

# Get tokens from environment
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

if not SLACK_BOT_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN environment variable is required")
if not SLACK_APP_TOKEN:
    raise ValueError("SLACK_APP_TOKEN environment variable is required (starts with xapp-)")

# Initialize Slack app
app = AsyncApp(token=SLACK_BOT_TOKEN)

@app.event("app_mention")
async def handle_app_mention(event, say, logger):
    """Handle app mentions"""
    logger.info(f"📨 Received app_mention: {event}")
    
    user_id = event["user"]
    text = event.get("text", "")
    
    # Remove bot mention
    import re
    text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
    
    logger.info(f"Processing message from {user_id}: {text}")
    
    try:
        await say(
            text=f"👋 Hi <@{user_id}>! I received your message: '{text}'\n\n"
                 "✅ **The bot is working with Socket Mode!**\n\n"
                 "I can now:\n"
                 "• Respond to @mentions\n"
                 "• Process your queries\n"
                 "• Work in any channel I'm invited to\n\n"
                 "Next step: Connect to Goose Query Expert for data analysis!",
            thread_ts=event.get("ts")
        )
        logger.info("✅ Response sent successfully")
    except Exception as e:
        logger.error(f"Error sending response: {str(e)}", exc_info=True)

@app.event("message")
async def handle_message(event, logger):
    """Handle message events"""
    # Only log, don't respond to every message
    if event.get("subtype") is None:  # Regular messages only
        logger.info(f"📝 Message received: {event.get('text', '')[:50]}...")

async def start_web_server():
    """Start web server for Heroku health checks"""
    async def health_check(request):
        return web.json_response({
            "status": "healthy",
            "service": "goose-query-expert-slackbot-socket",
            "mode": "socket"
        })
    
    web_app = web.Application()
    web_app.router.add_get('/health', health_check)
    web_app.router.add_get('/', health_check)
    
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"🌐 Web server started on port {port}")
    return runner

async def main():
    """Main entry point"""
    logger.info("🚀 Starting Slack Bot with Socket Mode...")
    logger.info(f"Bot token: {SLACK_BOT_TOKEN[:20]}...")
    logger.info(f"App token: {SLACK_APP_TOKEN[:20]}...")
    
    try:
        # Start web server
        runner = await start_web_server()
        
        # Start Socket Mode handler
        handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
        
        logger.info("🔌 Connecting to Slack via Socket Mode...")
        await handler.start_async()
        
        logger.info("✅ Socket Mode connected! Bot is ready to receive messages.")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
