"""
Simplified Slack Bot - Uses bot token directly (no OAuth)
For single workspace deployment
"""

import os
import hmac
import hashlib
import time
from typing import Dict, Optional
from datetime import datetime

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

from config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# ============================================================================
# Slack App Initialization - Direct Token (No OAuth)
# ============================================================================

async def create_slack_app():
    """Create Slack app with direct bot token"""
    app = AsyncApp(
        token=settings.slack_bot_token,
        signing_secret=settings.slack_signing_secret,
        process_before_response=True
    )
    
    return app

# ============================================================================
# FastAPI Application
# ============================================================================

fastapi_app = FastAPI(
    title="Goose Query Expert Slackbot",
    description="AI-powered data analysis bot for Slack",
    version="1.0.0"
)

slack_app = None
slack_handler = None

@fastapi_app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global slack_app, slack_handler
    
    logger.info("Starting Goose Query Expert Slackbot (Simple Mode)...")
    
    # Initialize Slack app
    slack_app = await create_slack_app()
    slack_handler = AsyncSlackRequestHandler(slack_app)
    
    # Setup event handlers
    setup_event_handlers(slack_app)
    
    logger.info("Slackbot started successfully")

# ============================================================================
# Webhook Endpoints
# ============================================================================

@fastapi_app.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack events via webhook"""
    body = await request.body()
    logger.info(f"Received Slack event: {body.decode()[:500]}")  # Log first 500 chars
    
    try:
        result = await slack_handler.handle(request)
        logger.info(f"Handler result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error handling Slack event: {str(e)}", exc_info=True)
        raise

@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "goose-query-expert-slackbot",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# Event Handlers
# ============================================================================

def setup_event_handlers(app: AsyncApp):
    """Setup Slack event handlers"""
    
    @app.event("app_mention")
    async def handle_app_mention(event, say, logger):
        """Handle app mentions in channels"""
        logger.info(f"Received app_mention event: {event}")
        
        user_id = event["user"]
        text = event.get("text", "")
        
        # Remove bot mention
        import re
        text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
        
        logger.info(f"Processing message from user {user_id}: {text}")
        
        # Simple response for now
        await say(
            text=f"👋 Hi <@{user_id}>! I received your message: '{text}'\n\n"
                 "I'm now working! The bot is responding to your @mentions.\n\n"
                 "Next step: Connect me to Goose Query Expert to process actual queries.",
            thread_ts=event.get("ts")
        )
    
    @app.command("/goose-query")
    async def handle_slash_command(ack, command, say, logger):
        """Handle slash command"""
        await ack()
        
        logger.info(f"Received slash command: {command}")
        
        await say(
            text=f"👋 Slash command received! You said: {command['text']}\n\n"
                 "The bot is working!"
        )

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "slack_bot_simple:fastapi_app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 3000)),
        reload=False
    )
