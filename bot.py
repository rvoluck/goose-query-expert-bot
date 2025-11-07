"""
Ultra-simple Slack bot - Socket Mode
No database, no OAuth, just pure bot token
Now with REAL Goose Query Expert integration!
"""

import os
import asyncio
import re
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from aiohttp import web
from goose_client import GooseQueryExpertClient
import structlog

# Initialize logger
logger = structlog.get_logger()

# Get tokens
BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
APP_TOKEN = os.environ["SLACK_APP_TOKEN"]

print(f"🚀 Starting bot...")
print(f"Bot token: {BOT_TOKEN[:20]}...")
print(f"App token: {APP_TOKEN[:20]}...")

# Initialize Goose Query Expert client
goose_client = GooseQueryExpertClient()

# Create app with single-workspace authorization (no OAuth)
# This bypasses the installation store completely
async def authorize(enterprise_id, team_id, user_id):
    """Simple authorization - just return the bot token"""
    from slack_bolt.authorization import AuthorizeResult
    return AuthorizeResult(
        enterprise_id=enterprise_id,
        team_id=team_id,
        bot_token=BOT_TOKEN,
    )

app = AsyncApp(
    authorize=authorize,
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET", ""),
    process_before_response=True
)

@app.event("app_mention")
async def mention_handler(event, say):
    """Handle @mentions - REAL Query Expert integration"""
    print(f"📨 Got app_mention event: {event}")
    
    user = event["user"]
    text = re.sub(r'<@[A-Z0-9]+>', '', event.get("text", "")).strip()
    
    # Send initial "thinking" message
    thinking_msg = await say(
        text=f"🔍 Analyzing your question: _{text}_\n\nSearching for relevant tables and similar queries...",
        thread_ts=event.get("ts")
    )
    
    try:
        # Create user context
        from goose_client import UserContext
        user_context = UserContext(
            user_id=user,
            slack_user_id=user,
            email=None,
            permissions=["query_execute"]
        )
        
        # Process the question through Query Expert
        logger.info("Processing question with Query Expert", query=text)
        result = await goose_client.process_user_question(
            question=text,
            user_context=user_context
        )
        
        # Format the response based on result
        if result.success:
            # Extract data from result
            sql = result.sql
            rows = result.rows
            execution_time = result.execution_time
            
            # Format tables
            tables = result.metadata.get("table_search", {}).get("tables", [])
            table_list = "\n".join([
                f"• `{t.get('table_name', 'unknown')}` - {t.get('description', 'No description')}"
                for t in tables[:5]
            ]) if tables else "• No specific tables found"
            
            # Format similar queries
            similar_queries = result.metadata.get("similar_queries", {}).get("queries", [])
            similar_list = "\n".join([
                f"• \"{q.get('query_description', q.get('query_text', '')[:60])}...\" "
                f"(by {q.get('user_name', 'unknown')})"
                for q in similar_queries[:3]
            ]) if similar_queries else "• No similar queries found"
            
            # Build results summary
            results_summary = f"• Found {result.row_count} rows\n• Execution time: {execution_time:.2f}s"
            
            # Format first few rows as preview
            if rows and len(rows) > 0:
                preview_rows = rows[:3]  # Show first 3 rows
                preview = "\n".join([
                    f"Row {i+1}: {', '.join(str(v) for v in row)}"
                    for i, row in enumerate(preview_rows)
                ])
                results_summary += f"\n\n*Sample Results:*\n```\n{preview}\n```"
            
            # Extract insights from experts and similar tables
            insights = []
            if result.experts:
                insights.append(f"Data experts available: {', '.join([e['user_name'] for e in result.experts[:3]])}")
            if result.similar_tables:
                insights.append(f"Found {len(result.similar_tables)} related tables")
            insights.append("Query executed successfully")
            
            insights_text = "\n".join([f"• {i}" for i in insights])
            
            response = (
                f"📊 *Query Analysis Results*\n\n"
                f"*Your Question:* {text}\n\n"
                f"*Relevant Tables Found:*\n{table_list}\n\n"
                f"*Similar Past Queries:*\n{similar_list}\n\n"
                f"*Generated SQL:*\n```sql\n{sql}\n```\n\n"
                f"*Results Summary:*\n{results_summary}\n\n"
                f"💡 *Insights:*\n{insights_text}\n\n"
                f"_Would you like me to refine this query or analyze a different aspect?_"
            )
        else:
            # Error case
            error_msg = result.error_message or "Unknown error"
            response = (
                f"❌ *Error Processing Query*\n\n"
                f"*Your Question:* {text}\n\n"
                f"*Error:* {error_msg}\n\n"
                f"_Please try rephrasing your question or contact support if the issue persists._"
            )
        
        await say(text=response, thread_ts=event.get("ts"))
        print("✅ Sent real Query Expert response!")
        
    except Exception as e:
        logger.error("Error processing query", error=str(e), exc_info=True)
        await say(
            text=f"❌ Sorry, I encountered an error processing your question:\n```{str(e)}```\n\n"
                 f"Please try again or contact support if the issue persists.",
            thread_ts=event.get("ts")
        )
        print(f"❌ Error: {e}")

@app.event("message")
async def message_handler(event, say):
    """Handle ALL messages to test if Socket Mode is working"""
    print(f"📝 Got message event: {event}")
    
    # Don't respond to bot messages
    if event.get("bot_id"):
        return
    
    # Only respond in channels where bot is mentioned
    if "bot" in event.get("text", "").lower():
        await say(f"🤖 I see you mentioned 'bot'! Socket Mode is working!")
        print("✅ Sent test response!")

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
