"""
Public Slack Bot Implementation for Goose Query Expert
Supports Events API, OAuth, and multi-workspace distribution
"""

import os
import asyncio
import hmac
import hashlib
import time
from typing import Dict, Optional
from datetime import datetime

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings
from slack_sdk.oauth.installation_store import Installation
from slack_sdk.oauth.state_store import FileOAuthStateStore
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import structlog

from config import get_settings
from database import get_database_manager, UserSessionRepository, QueryHistoryRepository
from goose_client import GooseQueryExpertClient, UserContext

logger = structlog.get_logger(__name__)
settings = get_settings()


# ============================================================================
# Installation Store - Stores OAuth tokens for each workspace
# ============================================================================

class DatabaseInstallationStore:
    """Store Slack installations in PostgreSQL"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    async def async_save(self, installation: Installation):
        """Save installation to database"""
        await self.db.execute_command(
            """
            INSERT INTO slack_installations 
            (team_id, team_name, bot_token, bot_user_id, bot_scopes, installed_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            ON CONFLICT (team_id) DO UPDATE SET
                team_name = EXCLUDED.team_name,
                bot_token = EXCLUDED.bot_token,
                bot_user_id = EXCLUDED.bot_user_id,
                bot_scopes = EXCLUDED.bot_scopes,
                updated_at = NOW()
            """,
            installation.team_id,
            installation.team_name,
            installation.bot_token,
            installation.bot_user_id,
            ','.join(installation.bot_scopes) if installation.bot_scopes else ''
        )
        logger.info("Saved installation", team_id=installation.team_id)
    
    async def async_find_installation(
        self, 
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
        is_enterprise_install: Optional[bool] = False
    ) -> Optional[Installation]:
        """Find installation by team_id"""
        
        row = await self.db.execute_one(
            """
            SELECT team_id, team_name, bot_token, bot_user_id, bot_scopes
            FROM slack_installations
            WHERE team_id = $1
            """,
            team_id
        )
        
        if not row:
            return None
        
        return Installation(
            app_id=settings.slack_app_id,
            enterprise_id=enterprise_id,
            team_id=row['team_id'],
            team_name=row['team_name'],
            bot_token=row['bot_token'],
            bot_id=row['bot_user_id'],
            bot_user_id=row['bot_user_id'],
            bot_scopes=row['bot_scopes'].split(',') if row['bot_scopes'] else [],
            user_id=user_id,
            installed_at=time.time()
        )
    
    async def async_delete_installation(
        self,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None
    ):
        """Delete installation"""
        await self.db.execute_command(
            "DELETE FROM slack_installations WHERE team_id = $1",
            team_id
        )
        logger.info("Deleted installation", team_id=team_id)


# ============================================================================
# OAuth Settings
# ============================================================================

async def get_oauth_settings():
    """Create OAuth settings with database installation store"""
    db_manager = await get_database_manager()
    
    return AsyncOAuthSettings(
        client_id=settings.slack_client_id,
        client_secret=settings.slack_client_secret,
        scopes=[
            "app_mentions:read",
            "channels:history",
            "channels:read",
            "chat:write",
            "commands",
            "users:read"
        ],
        installation_store=DatabaseInstallationStore(db_manager),
        state_store=FileOAuthStateStore(
            expiration_seconds=600,
            base_dir="./oauth_states"
        ),
        redirect_uri=settings.slack_oauth_redirect_url
    )


# ============================================================================
# Slack App Initialization
# ============================================================================

async def create_slack_app():
    """Create Slack app with OAuth support"""
    oauth_settings = await get_oauth_settings()
    
    app = AsyncApp(
        signing_secret=settings.slack_signing_secret,
        oauth_settings=oauth_settings,
        process_before_response=True  # Important for webhooks
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

# Global Slack app instance
slack_app = None
slack_handler = None


@fastapi_app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global slack_app, slack_handler
    
    logger.info("Starting Goose Query Expert Slackbot...")
    
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
    
    # Verify Slack signature
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    
    if not verify_slack_signature(body, timestamp, signature):
        return JSONResponse({"error": "Invalid signature"}, status_code=403)
    
    # Handle the event
    return await slack_handler.handle(request)


@fastapi_app.post("/slack/interactions")
async def slack_interactions(request: Request):
    """Handle Slack interactive components"""
    
    # Verify signature
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    
    if not verify_slack_signature(body, timestamp, signature):
        return JSONResponse({"error": "Invalid signature"}, status_code=403)
    
    return await slack_handler.handle(request)


@fastapi_app.get("/slack/oauth_redirect")
async def oauth_redirect(request: Request):
    """Handle OAuth redirect"""
    return await slack_handler.handle(request)


@fastapi_app.get("/slack/install")
async def install(request: Request):
    """Start OAuth installation flow"""
    return await slack_handler.handle(request)


# ============================================================================
# Health Check Endpoints
# ============================================================================

@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "goose-query-expert-slackbot",
        "timestamp": datetime.utcnow().isoformat()
    }


@fastapi_app.get("/")
async def root():
    """Root endpoint with installation link"""
    install_url = f"https://slack.com/oauth/v2/authorize?client_id={settings.slack_client_id}&scope=app_mentions:read,channels:history,channels:read,chat:write,commands,users:read"
    
    return {
        "name": "Goose Query Expert Slackbot",
        "description": "AI-powered data analysis bot for Slack (channels only, no DMs)",
        "install_url": install_url,
        "scopes": [
            "app_mentions:read",
            "channels:history", 
            "channels:read",
            "chat:write",
            "commands",
            "users:read"
        ]
    }


# ============================================================================
# Signature Verification
# ============================================================================

def verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    """Verify Slack request signature"""
    
    # Check timestamp (prevent replay attacks)
    try:
        request_timestamp = int(timestamp)
        current_timestamp = int(time.time())
        
        if abs(current_timestamp - request_timestamp) > 300:  # 5 minutes
            logger.warning("Request timestamp too old", timestamp=timestamp)
            return False
    except ValueError:
        return False
    
    # Verify signature
    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    computed_signature = "v0=" + hmac.new(
        settings.slack_signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)


# ============================================================================
# Event Handlers
# ============================================================================

def setup_event_handlers(app: AsyncApp):
    """Setup Slack event handlers"""
    
    @app.event("app_mention")
    async def handle_app_mention(event, say, client):
        """Handle app mentions in channels"""
        await process_query_request(event, say, client)
    
    @app.action("refine_query")
    async def handle_refine_query(ack, body, client):
        """Handle refine query button"""
        await ack()
        # Implementation here
    
    @app.action("share_query")
    async def handle_share_query(ack, body, client):
        """Handle share query button"""
        await ack()
        # Implementation here
    
    @app.command("/goose-query")
    async def handle_slash_command(ack, command, say, client):
        """Handle slash command"""
        await ack()
        
        event = {
            "user": command["user_id"],
            "channel": command["channel_id"],
            "text": command["text"],
            "ts": str(time.time())
        }
        
        await process_query_request(event, say, client)


async def process_query_request(event, say, client):
    """Process a query request from user"""
    
    user_id = event["user"]
    channel_id = event["channel"]
    text = event.get("text", "")
    thread_ts = event.get("ts")
    
    # Remove bot mention
    text = text.replace(f"<@{client.auth_test()['user_id']}>", "").strip()
    
    if not text or len(text) < 5:
        await say(
            text="👋 Hi! I can help you analyze data. Ask me a question like:\n"
                 "• What was our revenue last month?\n"
                 "• Show me top customers by sales\n"
                 "• How many users signed up this week?",
            thread_ts=thread_ts
        )
        return
    
    try:
        # Send initial message
        thinking_response = await say(
            text="🤔 Let me search for the best way to answer that...",
            thread_ts=thread_ts
        )
        
        # Process with Goose Query Expert
        goose_client = GooseQueryExpertClient()
        user_context = UserContext(
            user_id=user_id,
            slack_user_id=user_id,
            permissions=["query_execute"]
        )
        
        # Execute query
        result = await goose_client.process_user_question(text, user_context)
        
        # Format and send results
        if result.success:
            # Format results (simplified for this example)
            await client.chat_update(
                channel=channel_id,
                ts=thinking_response["ts"],
                text=f"✅ Query completed!\n\n```\n{result.sql}\n```\n\nFound {result.row_count} rows in {result.execution_time:.2f}s"
            )
        else:
            await client.chat_update(
                channel=channel_id,
                ts=thinking_response["ts"],
                text=f"❌ Query failed: {result.error_message}"
            )
    
    except Exception as e:
        logger.error("Error processing query", error=str(e))
        await say(
            text=f"🚨 Something went wrong: {str(e)}",
            thread_ts=thread_ts
        )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "slack_bot_public:fastapi_app",
        host=settings.host,
        port=settings.port,
        reload=settings.auto_reload
    )
