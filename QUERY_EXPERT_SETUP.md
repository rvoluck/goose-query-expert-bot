# 🚀 Query Expert Integration Setup

## Current Status
✅ Bot is now integrated with **real Goose Query Expert** (no more mock responses!)

## How It Works

When you ask the bot a question, it now:
1. **Searches for relevant tables** using Query Expert's table metadata
2. **Finds similar past queries** from your team's query history  
3. **Generates optimized SQL** based on context
4. **Executes the query** against Snowflake
5. **Returns formatted results** with insights and data experts

## Configuration Options

### Option 1: Mock Mode (Testing) - **CURRENTLY ACTIVE**
Perfect for testing without needing real Goose/Snowflake access.

**Heroku Config:**
```bash
heroku config:set MOCK_MODE=true -a goose-query-expert-bot
```

**What you get:**
- Simulated table searches
- Fake similar queries
- Mock SQL execution with sample data
- Fast responses (2 second delay)

### Option 2: Real Query Expert (Production)
Connect to actual Goose Query Expert and Snowflake.

**Required Heroku Config:**
```bash
# Disable mock mode
heroku config:set MOCK_MODE=false -a goose-query-expert-bot

# Goose MCP Server (where Query Expert runs)
heroku config:set GOOSE_MCP_SERVER_URL=https://your-goose-server.com -a goose-query-expert-bot
heroku config:set GOOSE_MCP_TIMEOUT=300 -a goose-query-expert-bot

# Snowflake credentials (for query execution)
heroku config:set SNOWFLAKE_ACCOUNT=your-account -a goose-query-expert-bot
heroku config:set SNOWFLAKE_WAREHOUSE=COMPUTE_WH -a goose-query-expert-bot
heroku config:set SNOWFLAKE_DATABASE=ANALYTICS -a goose-query-expert-bot
heroku config:set SNOWFLAKE_SCHEMA=PUBLIC -a goose-query-expert-bot
```

## Testing the Integration

### In Slack:
```
@goose query expert What was our revenue last month?
```

### Expected Response (Mock Mode):
```
📊 Query Analysis Results

Your Question: What was our revenue last month?

Relevant Tables Found:
• ANALYTICS.SALES.REVENUE_BY_CATEGORY - Daily revenue aggregated by product category
• ANALYTICS.SALES.CUSTOMER_METRICS - Customer acquisition and retention metrics

Similar Past Queries:
• "Revenue analysis by product category" (by john.doe)
• "Monthly revenue trends" (by jane.smith)

Generated SQL:
SELECT product_category, SUM(revenue) 
FROM ANALYTICS.SALES.REVENUE_BY_CATEGORY 
GROUP BY product_category

Results Summary:
• Found 4 rows
• Execution time: 2.34s

Sample Results:
Row 1: Electronics, 1250000.50, 15420
Row 2: Clothing, 890000.25, 22100
Row 3: Home & Garden, 675000.75, 8930

💡 Insights:
• Data experts available: john.doe, jane.smith
• Found 2 related tables
• Query executed successfully
```

## Current Deployment Status

**Bot Mode:** Socket Mode (simple, working)
**Query Expert:** Mock Mode (safe for testing)
**Database:** PostgreSQL (Heroku Postgres)
**Redis:** Redis Cloud (for caching)

## Next Steps

### To Deploy These Changes:
```bash
cd /Users/rleach/goose-slackbot
git push origin main
```

Then Heroku will automatically rebuild and restart with the new Query Expert integration!

### To Switch to Real Query Expert:
1. Set up a Goose MCP server (or get the URL from your team)
2. Configure Snowflake credentials
3. Update Heroku config vars (see Option 2 above)
4. Restart the Heroku dyno: `heroku restart -a goose-query-expert-bot`

## Troubleshooting

### Bot responds but with mock data?
- Check: `heroku config:get MOCK_MODE -a goose-query-expert-bot`
- Should be `false` for real Query Expert

### Bot returns errors about MCP server?
- Check: `heroku config:get GOOSE_MCP_SERVER_URL -a goose-query-expert-bot`
- Verify the MCP server is accessible from Heroku

### SQL execution fails?
- Check Snowflake credentials in Heroku config
- Verify warehouse/database/schema names are correct
- Check user permissions in Snowflake

### Check logs:
```bash
heroku logs --tail -a goose-query-expert-bot
```

Look for:
- `Processing question with Query Expert` - Query started
- `Query completed successfully` - Query finished
- `Query execution failed` - Error occurred

## Architecture

```
Slack User
    ↓
Slack Bot (Heroku)
    ↓
GooseQueryExpertClient
    ↓
GooseMCPClient (if MOCK_MODE=false)
    ↓
Query Expert MCP Server
    ↓
Snowflake
```

In mock mode, the GooseMCPClient is replaced with MockGooseClient.

---

**Ready to deploy?** Just push to GitHub and Heroku will handle the rest! 🚀
