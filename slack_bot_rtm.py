"""
Slack Bot using RTM (Real-Time Messaging) API
Simpler approach - bot connects directly to Slack, no webhooks needed
"""

import os
import asyncio
import re
from slack_sdk.rtm_v2 import RTMClient
from slack_sdk.web.async_client import AsyncWebClient
import structlog

logger = structlog.get_logger(__name__)

# Get bot token from environment
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

if not SLACK_BOT_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN environment variable is required")

# Initialize clients
rtm_client = RTMClient(token=SLACK_BOT_TOKEN)
web_client = AsyncWebClient(token=SLACK_BOT_TOKEN)

# Store bot user ID
bot_user_id = None

async def get_bot_user_id():
    """Get the bot's user ID"""
    global bot_user_id
    if not bot_user_id:
        response = await web_client.auth_test()
        bot_user_id = response["user_id"]
        logger.info(f"Bot user ID: {bot_user_id}")
    return bot_user_id

@rtm_client.on("message")
async def handle_message(client: RTMClient, event: dict):
    """Handle all message events"""
    
    logger.info(f"Received message event: {event}")
    
    # Get message details
    text = event.get("text", "")
    channel = event.get("channel")
    user = event.get("user")
    ts = event.get("ts")
    
    # Ignore messages from bots
    if event.get("bot_id"):
        return
    
    # Get bot user ID
    bot_id = await get_bot_user_id()
    
    # Check if bot was mentioned
    if f"<@{bot_id}>" in text:
        logger.info(f"Bot was mentioned by user {user} in channel {channel}")
        
        # Remove bot mention from text
        clean_text = re.sub(f'<@{bot_id}>', '', text).strip()
        
        try:
            # Send response
            await web_client.chat_postMessage(
                channel=channel,
                text=f"👋 Hi <@{user}>! I received your message: '{clean_text}'\n\n"
                     "✅ **The bot is working with RTM API!**\n\n"
                     "I can now:\n"
                     "• Respond to @mentions\n"
                     "• Process your queries\n"
                     "• Work in any channel I'm invited to\n\n"
                     "Next step: Connect to Goose Query Expert for data analysis!",
                thread_ts=ts
            )
            logger.info(f"Sent response to user {user}")
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}", exc_info=True)

@rtm_client.on("hello")
async def handle_hello(client: RTMClient, event: dict):
    """Handle connection established"""
    logger.info("✅ Connected to Slack RTM API!")
    await get_bot_user_id()

@rtm_client.on("error")
async def handle_error(client: RTMClient, event: dict):
    """Handle errors"""
    logger.error(f"RTM Error: {event}")

async def main():
    """Main entry point"""
    logger.info("🚀 Starting Slack Bot with RTM API...")
    logger.info(f"Bot token: {SLACK_BOT_TOKEN[:20]}...")
    
    try:
        # Start RTM connection
        await rtm_client.connect()
        logger.info("RTM client started successfully")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
