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
    """Handle @mentions - Query Expert style"""
    print(f"📨 Got app_mention event: {event}")
    
    user = event["user"]
    text = re.sub(r'<@[A-Z0-9]+>', '', event.get("text", "")).strip()
    
    # Send initial "thinking" message
    await say(
        text=f"🔍 Analyzing your question: _{text}_\n\nSearching for relevant tables and similar queries...",
        thread_ts=event.get("ts")
    )
    
    # Simulate Query Expert response
    await say(
        text=f"📊 *Query Analysis Results*\n\n"
             f"*Your Question:* {text}\n\n"
             f"*Relevant Tables Found:*\n"
             f"• `analytics.revenue_daily` - Daily revenue aggregations\n"
             f"• `analytics.customers` - Customer dimension table\n"
             f"• `analytics.transactions` - Transaction fact table\n\n"
             f"*Similar Past Queries:*\n"
             f"• \"Show me revenue trends\" (executed 3 days ago)\n"
             f"• \"What was last month's revenue\" (executed 1 week ago)\n\n"
             f"*Generated SQL:*\n"
             f"```sql\n"
             f"SELECT \n"
             f"    DATE_TRUNC('month', transaction_date) AS month,\n"
             f"    SUM(amount) AS total_revenue,\n"
             f"    COUNT(DISTINCT customer_id) AS unique_customers\n"
             f"FROM analytics.transactions\n"
             f"WHERE transaction_date >= DATEADD(month, -6, CURRENT_DATE)\n"
             f"GROUP BY 1\n"
             f"ORDER BY 1 DESC;\n"
             f"```\n\n"
             f"*Results Summary:*\n"
             f"• Found 6 rows\n"
             f"• Execution time: 1.2s\n"
             f"• Total revenue (last 6 months): $2,450,000\n"
             f"• Average monthly revenue: $408,333\n\n"
             f"💡 *Insights:*\n"
             f"• Revenue trending up 15% month-over-month\n"
             f"• Customer base growing steadily\n"
             f"• Peak revenue in most recent month\n\n"
             f"_Would you like me to refine this query or analyze a different aspect?_",
        thread_ts=event.get("ts")
    )
    print("✅ Sent Query Expert-style response!")

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
