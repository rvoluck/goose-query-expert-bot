# Frequently Asked Questions (FAQ)

Common questions and answers about the Goose Slackbot.

## 📋 Table of Contents

1. [General Questions](#general-questions)
2. [Getting Started](#getting-started)
3. [Using the Bot](#using-the-bot)
4. [Query Questions](#query-questions)
5. [Results and Data](#results-and-data)
6. [Permissions and Access](#permissions-and-access)
7. [Technical Questions](#technical-questions)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)
10. [Administration](#administration)

## 🤔 General Questions

### What is Goose Slackbot?

Goose Slackbot is an AI-powered data assistant that allows you to query your data warehouse using natural language directly in Slack. It uses Goose Query Expert to understand your questions and generate SQL queries automatically.

### How does it work?

1. You ask a question in natural language (e.g., "What was our revenue last month?")
2. Goose Query Expert analyzes your question and your data schema
3. It generates an optimized SQL query
4. The query is executed against your data warehouse (Snowflake)
5. Results are formatted and displayed in Slack

### Is it secure?

Yes! The bot includes:
- Enterprise authentication (LDAP integration)
- Role-based access control
- Complete audit logging
- Data encryption at rest and in transit
- Rate limiting to prevent abuse

See [SECURITY.md](SECURITY.md) for detailed security information.

### What data sources are supported?

Currently supported:
- ✅ Snowflake (primary)
- 🔄 BigQuery (coming soon)
- 🔄 Redshift (coming soon)
- 🔄 PostgreSQL (coming soon)

### How much does it cost?

The Goose Slackbot itself is open source and free. However, you'll need:
- Snowflake account (charges apply for query execution)
- Infrastructure to host the bot (cloud hosting costs)
- Slack workspace (free or paid plan)

## 🚀 Getting Started

### How do I access the bot?

1. Find `@goose-bot` in your Slack workspace
2. Send it a direct message or mention it in a channel
3. You can also use the `/goose-query` slash command

### Do I need special permissions?

Yes, you need the `query_execute` permission. Contact your admin if you don't have access:
```
@admin I need access to the Goose Slackbot for data queries
```

### How do I know if I have access?

Try sending a simple message to the bot:
```
@goose-bot hello
```

If you get a response, you have access. If you get a permission error, contact your admin.

### What's the best way to learn?

1. Start with simple questions: "Show me a sample of sales data"
2. Look at the [USER_MANUAL.md](USER_MANUAL.md) for examples
3. Learn from colleagues' queries in shared channels
4. Experiment with different question formats

## 💬 Using the Bot

### How do I ask a question?

You can interact with the bot in three ways:

**1. Direct Message:**
```
What was our revenue last month?
```

**2. Channel Mention:**
```
@goose-bot Show me top 10 customers by sales
```

**3. Slash Command:**
```
/goose-query How many new users signed up this week?
```

### What kind of questions can I ask?

You can ask about:
- **Metrics**: "What was our revenue last month?"
- **Trends**: "Show me daily sales for the past 30 days"
- **Comparisons**: "Compare Q3 vs Q4 revenue"
- **Top/Bottom**: "Who are our top 10 customers?"
- **Aggregations**: "What's the average order value?"
- **Filters**: "Show me sales in California"

### Can I ask follow-up questions?

Yes! Ask follow-up questions in the same thread:
```
Initial: "What was our revenue last month?"
Follow-up: "How does that compare to the previous month?"
Follow-up: "Which products contributed most?"
```

### How specific should my questions be?

More specific = better results:

**Good:**
```
What was our total revenue from mobile app purchases in December 2023?
```

**Less effective:**
```
Show me some revenue
```

### Can I see the SQL query that was generated?

Yes! The bot shows the generated SQL with the results. This helps you:
- Understand what data was queried
- Learn SQL patterns
- Verify the query is correct
- Debug unexpected results

## 📊 Query Questions

### How long do queries take?

- **Simple queries**: 1-5 seconds
- **Complex queries**: 5-30 seconds
- **Very large datasets**: 30-300 seconds

You'll see progress updates while the query runs.

### Is there a query timeout?

Yes, queries timeout after 5 minutes (300 seconds) by default. If your query times out:
- Make it more specific
- Reduce the date range
- Contact your admin about increasing the timeout

### Can I run multiple queries at once?

Yes, you can have multiple queries running simultaneously. Each query runs independently in its own thread.

### What if my query fails?

The bot will show an error message with:
- What went wrong
- Suggestions for fixing it
- The SQL that was generated (if applicable)

Common fixes:
- Check your spelling
- Be more specific about time periods
- Verify the data exists
- Try rephrasing your question

### Can I save queries for later?

Query history is automatically saved. You can:
- View your past queries
- Re-run previous queries
- Share queries with team members
- Reference query IDs for support

### How do I refine a query?

Click the "Refine Query" button on any result to:
- Modify your question
- Add filters
- Change time periods
- Adjust grouping or sorting

## 📈 Results and Data

### How are results displayed?

**Small results (≤10 rows):**
- Displayed as formatted tables in Slack
- Easy to read inline

**Large results (>10 rows):**
- Summary and preview shown
- Full results available as CSV download
- First 5 rows displayed as preview

### How do I download large result sets?

Large results are automatically provided as CSV files:
1. Look for the 📎 attachment in the bot's response
2. Click to download the CSV file
3. Open in Excel, Google Sheets, or other tools

### What's the maximum number of results?

- Default maximum: 10,000 rows
- Inline display: 10 rows
- CSV downloads: Up to 10,000 rows

Need more? Contact your admin about increasing limits.

### How fresh is the data?

Data freshness depends on your data warehouse:
- Most data: Updated daily (overnight)
- Real-time data: Updated continuously
- Historical data: Static

Ask your data team about specific table update schedules.

### Can I export results?

Yes, several ways:
- **CSV Download**: For large results
- **Copy/Paste**: From inline tables
- **Share**: Use the "Share with Team" button
- **Screenshot**: Take a screenshot of results

### What if results look wrong?

1. **Verify your question**: Check if you asked what you intended
2. **Check the SQL**: Review the generated SQL query
3. **Compare with known data**: Verify against other sources
4. **Ask for help**: Mention the query ID when asking for support
5. **Report issues**: Contact your data team if data seems incorrect

## 🔐 Permissions and Access

### What permissions do I need?

Common permissions:
- `query_execute`: Run queries
- `query_share`: Share results with team
- `query_history`: View your query history
- `query_export`: Download large result sets

### How do I request access?

Contact your admin:
```
@admin I need query_execute permission for the Goose Slackbot
```

Include:
- What you need access for
- Your role/team
- Any specific data you need to access

### Can I access all data?

No, access is controlled by:
- Your Snowflake permissions
- Your Goose Slackbot role
- Your team's data access policies

You can only query data you have permission to access.

### How do I know what data I can access?

Ask the bot:
```
What data do I have access to?
What tables are available?
Show me a sample of [table_name]
```

### Can I share results with non-users?

Results can be shared:
- ✅ In public channels (if data is not sensitive)
- ✅ In private channels (with appropriate members)
- ✅ As screenshots or exports
- ❌ Don't share sensitive data inappropriately

Always follow your organization's data sharing policies.

## 🔧 Technical Questions

### What technology powers the bot?

- **AI Engine**: Goose Query Expert
- **Platform**: Slack Bolt Python framework
- **Database**: PostgreSQL (for bot data)
- **Cache**: Redis
- **Data Warehouse**: Snowflake
- **Language**: Python 3.9+

### Can I integrate it with other tools?

Yes! The bot provides:
- RESTful APIs for integrations
- Webhook support for events
- Export capabilities
- Admin APIs for management

See [API.md](API.md) for integration details.

### Is there an API?

Yes, comprehensive APIs are available:
- Query execution API
- User management API
- Query history API
- Admin APIs

See [API.md](API.md) for documentation.

### Can I run it on-premises?

Yes! Deployment options:
- Docker containers
- Kubernetes
- Traditional servers
- Cloud platforms (AWS, GCP, Azure)

See [DEPLOYMENT.md](DEPLOYMENT.md) for details.

### What are the system requirements?

**Minimum:**
- Python 3.9+
- 2GB RAM
- PostgreSQL 12+
- Redis 6+

**Recommended:**
- Python 3.11+
- 4GB RAM
- PostgreSQL 14+
- Redis 7+

### How does it handle high load?

- Horizontal scaling (multiple instances)
- Connection pooling
- Caching with Redis
- Rate limiting
- Queue management

## 🔍 Troubleshooting

### Bot isn't responding

**Check:**
1. Is the bot online? (Check status in Slack)
2. Did you mention the bot correctly? (@goose-bot)
3. Are you in a supported channel?
4. Do you have permissions?

**Try:**
```
@goose-bot hello
```

If no response, contact your admin.

### "Permission denied" error

**Cause**: You don't have the required permissions

**Solution**:
1. Contact your admin
2. Request `query_execute` permission
3. Explain what you need access for

### "No data found" error

**Possible causes:**
- Date range too narrow
- Filters too restrictive
- Data doesn't exist
- Typo in question

**Try:**
- Broader date range
- Fewer filters
- Verify data availability
- Check spelling

### Query is taking too long

**If query is still running:**
- Wait for progress updates
- Check if it's a complex query
- Consider making it more specific

**If query times out:**
- Reduce date range
- Be more specific
- Add filters to reduce data volume
- Contact admin about timeout limits

### Results don't match expectations

**Steps:**
1. Review the generated SQL
2. Check your question for ambiguity
3. Verify data freshness
4. Compare with known results
5. Ask for clarification from data team

### Can't download CSV file

**Check:**
- File size limits in Slack
- Your download permissions
- Browser settings
- Network connection

**Alternative:**
- Ask for results to be emailed
- Request smaller date range
- Use query history to re-run

## 🎓 Advanced Usage

### Can I use SQL functions?

The bot understands many SQL concepts:
```
Show me the average, min, and max order values
Calculate the median customer age
Show me the 90th percentile of response times
```

### Can I do complex analysis?

Yes! Examples:
```
Compare revenue between Q3 and Q4 2023 by product category
Show me year-over-year growth for each region
Calculate customer retention rate for the past 12 months
```

### Can I create visualizations?

Currently:
- ✅ Tabular results
- ✅ CSV exports for external visualization
- 🔄 Built-in charts (coming soon)

Export to Excel/Google Sheets for charts.

### Can I schedule queries?

Not yet, but coming soon:
- 🔄 Scheduled queries
- 🔄 Automated reports
- 🔄 Alerts and notifications

### Can I create custom functions?

Contact your admin about:
- Custom query templates
- Saved queries
- Query shortcuts
- Team-specific functions

### How do I optimize query performance?

**Tips:**
- Be specific about date ranges
- Use filters to reduce data volume
- Request only needed columns
- Avoid very large result sets
- Use aggregations when possible

## 👨‍💼 Administration

### How do I add users?

Admins can add users via:
```python
python scripts/add_user.py \
  --slack-id U1234567890 \
  --email user@company.com \
  --permissions query_execute
```

See [ADMIN_GUIDE.md](ADMIN_GUIDE.md) for details.

### How do I manage permissions?

**Via Admin API:**
```bash
curl -X PUT https://your-domain.com/api/admin/users/{user_id} \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"permissions": ["query_execute", "query_share"]}'
```

**Via Database:**
```sql
UPDATE users 
SET permissions = ARRAY['query_execute', 'query_share']
WHERE slack_user_id = 'U1234567890';
```

### How do I monitor usage?

**Metrics available:**
- Query volume
- Active users
- Query success rate
- Average execution time
- Error rates

**Access via:**
- `/metrics` endpoint (Prometheus format)
- Admin dashboard
- Query history reports

### How do I troubleshoot issues?

**Check:**
1. Application logs
2. Health endpoints
3. Database connections
4. Redis connectivity
5. Goose server status

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed guide.

### How do I update the bot?

**Docker:**
```bash
docker pull goose-slackbot:latest
docker-compose up -d
```

**Kubernetes:**
```bash
kubectl set image deployment/goose-slackbot \
  goose-slackbot=goose-slackbot:v1.1.0
```

**Manual:**
```bash
git pull
pip install -r requirements.txt
python migrations.py
systemctl restart goose-slackbot
```

### How do I backup data?

**Database backup:**
```bash
pg_dump goose_slackbot > backup_$(date +%Y%m%d).sql
```

**Automated backups:**
```bash
# Add to crontab
0 2 * * * pg_dump goose_slackbot > /backups/backup_$(date +\%Y\%m\%d).sql
```

## 📞 Still Have Questions?

### Documentation
- [README.md](README.md) - Overview
- [SETUP.md](SETUP.md) - Setup guide
- [USER_MANUAL.md](USER_MANUAL.md) - User guide
- [ADMIN_GUIDE.md](ADMIN_GUIDE.md) - Admin guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Troubleshooting
- [API.md](API.md) - API documentation

### Support Channels
- **Slack**: #data-support channel
- **Email**: data-team@company.com
- **GitHub**: Open an issue
- **Admin**: Contact your workspace admin

### Quick Help
Ask the bot:
```
@goose-bot help
@goose-bot what can you do?
@goose-bot how do I use you?
```

---

**Can't find your answer? Ask in #data-support or contact the data team!** 💬
