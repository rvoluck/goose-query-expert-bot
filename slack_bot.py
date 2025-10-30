"""
Main Slack Bot Implementation for Goose Query Expert Integration
Handles Slack events, user interactions, and query processing
"""

import asyncio
import json
import time
import csv
import io
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
import structlog

from config import get_settings
from goose_client import GooseQueryExpertClient, QueryResult, QueryStatus, UserContext
from database import (
    get_database_manager, UserSessionRepository, QueryHistoryRepository,
    UserMappingRepository, AuditLogRepository
)
from auth import AuthSystem, create_auth_system, UserContext as AuthUserContext

logger = structlog.get_logger(__name__)
settings = get_settings()


class SlackResultFormatter:
    """Formats query results for Slack display"""
    
    def __init__(self):
        self.max_inline_rows = settings.max_inline_rows
        self.max_result_rows = settings.max_result_rows
    
    def format_small_results(self, result: QueryResult) -> Dict[str, Any]:
        """Format small result sets as inline tables"""
        if result.row_count == 0:
            return {
                "text": "📊 Query completed successfully, but returned no results.",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```sql\n{result.sql}\n```"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"⏱️ Executed in {result.execution_time:.2f}s"
                            }
                        ]
                    }
                ]
            }
        
        # Create table format for small results
        table_text = self._create_ascii_table(result.columns, result.rows[:self.max_inline_rows])
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```\n{table_text}\n```"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏱️ Executed in {result.execution_time:.2f}s | 📄 {result.row_count} rows"
                    }
                ]
            }
        ]
        
        # Add SQL query section
        if len(result.sql) < 1000:  # Only show if not too long
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*SQL Query:*\n```sql\n{result.sql}\n```"
                }
            })
        
        # Add experts section if available
        if result.experts:
            expert_text = "\n".join([
                f"• *{expert['user_name']}*: {expert['reason']}" 
                for expert in result.experts[:3]
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Data Experts:*\n{expert_text}"
                }
            })
        
        # Add interactive buttons if enabled
        if settings.enable_interactive_buttons:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Refine Query"},
                        "action_id": "refine_query",
                        "value": result.query_id
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Share with Team"},
                        "action_id": "share_query",
                        "value": result.query_id
                    }
                ]
            })
        
        return {
            "text": f"📊 Query Results ({result.row_count} rows)",
            "blocks": blocks
        }
    
    def format_large_results(self, result: QueryResult) -> Dict[str, Any]:
        """Format large result sets with file attachment info"""
        summary = f"Found {result.row_count} rows in {result.execution_time:.2f} seconds"
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Query Summary:*\n{summary}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "📎 Full results will be uploaded as CSV file"
                }
            }
        ]
        
        # Add preview of first few rows
        if result.rows:
            preview_text = self._create_ascii_table(
                result.columns, 
                result.rows[:5]  # Show first 5 rows as preview
            )
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Preview (first 5 rows):*\n```\n{preview_text}\n```"
                }
            })
        
        # Add experts section if available
        if result.experts:
            expert_text = "\n".join([
                f"• *{expert['user_name']}*: {expert['reason']}" 
                for expert in result.experts[:3]
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Data Experts:*\n{expert_text}"
                }
            })
        
        # Add interactive buttons
        if settings.enable_interactive_buttons:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Refine Query"},
                        "action_id": "refine_query",
                        "value": result.query_id
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Share with Team"},
                        "action_id": "share_query",
                        "value": result.query_id
                    }
                ]
            })
        
        return {
            "text": f"📊 Large Query Results ({result.row_count} rows)",
            "blocks": blocks
        }
    
    def format_error(self, result: QueryResult) -> Dict[str, Any]:
        """Format error results"""
        error_msg = result.error_message or "Unknown error occurred"
        
        # Categorize common errors
        if "permission" in error_msg.lower():
            emoji = "🔒"
            title = "Permission Denied"
            suggestion = "You may need access to the requested data. Contact your data team."
        elif "timeout" in error_msg.lower():
            emoji = "⏰"
            title = "Query Timeout"
            suggestion = "Try a more specific query or contact support for optimization."
        elif "syntax" in error_msg.lower():
            emoji = "❌"
            title = "Query Syntax Error"
            suggestion = "There's an issue with the generated query. Try rephrasing your question."
        else:
            emoji = "🚨"
            title = "Query Failed"
            suggestion = "Please try again or contact support if the issue persists."
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *{title}*\n{error_msg}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"💡 *Suggestion:* {suggestion}"
                }
            }
        ]
        
        # Add SQL if available
        if result.sql:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Generated SQL:*\n```sql\n{result.sql}\n```"
                }
            })
        
        return {
            "text": f"{emoji} {title}",
            "blocks": blocks
        }
    
    def _create_ascii_table(self, columns: List[str], rows: List[List[Any]]) -> str:
        """Create ASCII table for small results"""
        if not rows:
            return "No data returned"
        
        # Convert all values to strings and handle None
        str_rows = []
        for row in rows:
            str_row = [str(cell) if cell is not None else "NULL" for cell in row]
            str_rows.append(str_row)
        
        # Calculate column widths
        col_widths = [len(col) for col in columns]
        for row in str_rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(cell))
        
        # Limit column width to prevent overly wide tables
        max_col_width = 20
        col_widths = [min(w, max_col_width) for w in col_widths]
        
        # Create table
        separator = "┼".join("─" * (w + 2) for w in col_widths)
        header_sep = f"├{separator}┤"
        top_border = f"┌{separator.replace('┼', '┬')}┐"
        bottom_border = f"└{separator.replace('┼', '┴')}┘"
        
        # Header
        header_cells = []
        for i, col in enumerate(columns):
            if len(col) > col_widths[i]:
                col = col[:col_widths[i]-3] + "..."
            header_cells.append(f" {col:<{col_widths[i]}} ")
        header = "│" + "│".join(header_cells) + "│"
        
        # Rows
        table_rows = []
        for row in str_rows:
            row_cells = []
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    if len(cell) > col_widths[i]:
                        cell = cell[:col_widths[i]-3] + "..."
                    row_cells.append(f" {cell:<{col_widths[i]}} ")
            table_rows.append("│" + "│".join(row_cells) + "│")
        
        return "\n".join([top_border, header, header_sep] + table_rows + [bottom_border])
    
    def create_csv_content(self, result: QueryResult) -> str:
        """Create CSV content for file upload"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(result.columns)
        
        # Write data rows
        for row in result.rows:
            # Handle None values and convert to strings
            clean_row = [str(cell) if cell is not None else "" for cell in row]
            writer.writerow(clean_row)
        
        return output.getvalue()


class GooseSlackBot:
    """Main Slack bot class"""
    
    def __init__(self):
        # Initialize Slack app
        self.app = AsyncApp(
            token=settings.slack_bot_token,
            signing_secret=settings.slack_signing_secret
        )
        
        # Initialize components
        self.goose_client = GooseQueryExpertClient()
        self.formatter = SlackResultFormatter()
        self.auth_system = None
        self.db_manager = None
        
        # Repositories
        self.session_repo = None
        self.query_repo = None
        self.user_repo = None
        self.audit_repo = None
        
        # Setup event handlers
        self._setup_event_handlers()
        
        # Active queries tracking
        self._active_queries = {}
    
    async def initialize(self):
        """Initialize database and auth system"""
        # Initialize database
        self.db_manager = await get_database_manager()
        
        # Initialize repositories
        self.session_repo = UserSessionRepository(self.db_manager)
        self.query_repo = QueryHistoryRepository(self.db_manager)
        self.user_repo = UserMappingRepository(self.db_manager)
        self.audit_repo = AuditLogRepository(self.db_manager)
        
        # Initialize auth system
        self.auth_system = await create_auth_system()
        
        logger.info("Slack bot initialized successfully")
    
    def _setup_event_handlers(self):
        """Setup Slack event handlers"""
        
        # Message events
        @self.app.event("message")
        async def handle_message(event, say, client):
            await self._handle_message_event(event, say, client)
        
        # App mention events
        @self.app.event("app_mention")
        async def handle_mention(event, say, client):
            await self._handle_mention_event(event, say, client)
        
        # Button interactions
        @self.app.action("refine_query")
        async def handle_refine_query(ack, body, client):
            await ack()
            await self._handle_refine_query(body, client)
        
        @self.app.action("share_query")
        async def handle_share_query(ack, body, client):
            await ack()
            await self._handle_share_query(body, client)
        
        # Slash commands
        @self.app.command("/goose-query")
        async def handle_slash_command(ack, body, client):
            await ack()
            await self._handle_slash_command(body, client)
        
        # Error handler
        @self.app.error
        async def handle_error(error, body, logger):
            await self._handle_error(error, body, logger)
    
    async def _handle_message_event(self, event, say, client):
        """Handle regular message events"""
        # Skip bot messages and threaded replies (unless it's a DM)
        if event.get("bot_id") or (event.get("thread_ts") and event.get("channel_type") != "im"):
            return
        
        # Only process direct messages or messages in channels where bot is mentioned
        channel_type = event.get("channel_type", "")
        text = event.get("text", "").lower()
        
        if channel_type == "im" or "query" in text or "data" in text:
            await self._process_query_request(event, say, client)
    
    async def _handle_mention_event(self, event, say, client):
        """Handle app mention events"""
        await self._process_query_request(event, say, client)
    
    async def _process_query_request(self, event, say, client):
        """Process a query request from user"""
        user_id = event["user"]
        channel_id = event["channel"]
        text = event.get("text", "")
        thread_ts = event.get("ts")
        
        # Remove bot mention from text
        text = text.replace(f"<@{self.app.client.auth_test()['user_id']}>", "").strip()
        
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
            # Authenticate user
            user_context = await self._authenticate_user(user_id, channel_id)
            if not user_context:
                await say(
                    text="🔒 You need to be authenticated to use this bot. "
                         "Please contact your admin to set up access.",
                    thread_ts=thread_ts
                )
                return
            
            # Check permissions
            if not user_context.has_permission("query_execute"):
                await say(
                    text="🔒 You don't have permission to execute queries. "
                         "Contact your admin for access.",
                    thread_ts=thread_ts
                )
                return
            
            # Log the request
            await self.audit_repo.log_event(
                event_type="query_request",
                user_id=user_context.user_id,
                slack_user_id=user_id,
                channel_id=channel_id,
                action="query_request",
                event_data={"question": text[:500]}  # Truncate for storage
            )
            
            # Process the query
            await self._execute_user_query(
                text, user_context, user_id, channel_id, thread_ts, say, client
            )
            
        except Exception as e:
            logger.error("Error processing query request", error=str(e), user_id=user_id)
            await say(
                text="🚨 Something went wrong processing your request. "
                     "Please try again or contact support.",
                thread_ts=thread_ts
            )
    
    async def _execute_user_query(
        self, question: str, user_context: AuthUserContext, 
        slack_user_id: str, channel_id: str, thread_ts: str,
        say, client
    ):
        """Execute user query through Goose Query Expert"""
        
        # Send initial "thinking" message
        thinking_response = await say(
            text="🤔 Let me search for the best way to answer that...",
            thread_ts=thread_ts
        )
        thinking_ts = thinking_response["ts"]
        
        # Create progress callback
        async def progress_callback(query_id: str, status: QueryStatus):
            status_messages = {
                QueryStatus.SEARCHING_TABLES: "🔍 Searching for relevant data tables...",
                QueryStatus.SEARCHING_QUERIES: "📊 Looking for similar queries from your team...",
                QueryStatus.GENERATING_SQL: "⚡ Generating optimized SQL query...",
                QueryStatus.EXECUTING: "🏃 Executing query against Snowflake...",
                QueryStatus.COMPLETED: "✅ Query completed successfully!",
                QueryStatus.FAILED: "❌ Query execution failed"
            }
            
            message = status_messages.get(status, f"Processing... ({status.value})")
            
            try:
                await client.chat_update(
                    channel=channel_id,
                    ts=thinking_ts,
                    text=message
                )
            except SlackApiError as e:
                logger.warning("Failed to update progress message", error=str(e))
        
        # Convert auth user context to goose user context
        goose_user_context = UserContext(
            user_id=user_context.user_id,
            slack_user_id=slack_user_id,
            email=user_context.email,
            permissions=user_context.permissions,
            ldap_id=user_context.ldap_id
        )
        
        # Execute query through Goose
        result = await self.goose_client.process_user_question(
            question, goose_user_context, progress_callback
        )
        
        # Get or create session
        session = await self.session_repo.get_session(user_context.user_id, channel_id)
        if not session:
            session_id = await self.session_repo.create_session(
                user_context.user_id, slack_user_id, channel_id
            )
        else:
            session_id = session["id"]
            await self.session_repo.update_session_activity(session_id)
        
        # Save query to history
        await self.query_repo.save_query(
            session_id=session_id,
            user_id=user_context.user_id,
            slack_user_id=slack_user_id,
            channel_id=channel_id,
            query_id=result.query_id,
            original_question=question,
            generated_sql=result.sql,
            query_result=result.to_dict() if result.success else None,
            execution_time=result.execution_time,
            row_count=result.row_count,
            success=result.success,
            error_message=result.error_message,
            metadata=result.metadata
        )
        
        # Format and send results
        if result.success:
            if result.row_count <= self.formatter.max_inline_rows:
                # Small results - show inline
                formatted_response = self.formatter.format_small_results(result)
                await client.chat_update(
                    channel=channel_id,
                    ts=thinking_ts,
                    **formatted_response
                )
            else:
                # Large results - show summary and upload file
                formatted_response = self.formatter.format_large_results(result)
                await client.chat_update(
                    channel=channel_id,
                    ts=thinking_ts,
                    **formatted_response
                )
                
                # Upload CSV file if enabled
                if settings.enable_file_uploads:
                    csv_content = self.formatter.create_csv_content(result)
                    filename = f"query_results_{result.query_id}.csv"
                    
                    try:
                        await client.files_upload_v2(
                            channel=channel_id,
                            thread_ts=thread_ts,
                            content=csv_content,
                            filename=filename,
                            title=f"Query Results - {question[:50]}..."
                        )
                    except SlackApiError as e:
                        logger.error("Failed to upload CSV file", error=str(e))
                        await say(
                            text="📎 Note: Could not upload CSV file due to size or permission limits.",
                            thread_ts=thread_ts
                        )
        else:
            # Error results
            formatted_response = self.formatter.format_error(result)
            await client.chat_update(
                channel=channel_id,
                ts=thinking_ts,
                **formatted_response
            )
        
        # Log completion
        await self.audit_repo.log_event(
            event_type="query_execute",
            user_id=user_context.user_id,
            slack_user_id=slack_user_id,
            channel_id=channel_id,
            action="query_complete",
            result="success" if result.success else "failure",
            resource=result.query_id,
            event_data={
                "question": question[:500],
                "execution_time": result.execution_time,
                "row_count": result.row_count
            },
            error_message=result.error_message
        )
    
    async def _authenticate_user(self, slack_user_id: str, channel_id: str) -> Optional[AuthUserContext]:
        """Authenticate Slack user"""
        try:
            return await self.auth_system.authenticate_user(slack_user_id)
        except Exception as e:
            logger.error("Authentication failed", error=str(e), user_id=slack_user_id)
            return None
    
    async def _handle_refine_query(self, body, client):
        """Handle refine query button click"""
        user_id = body["user"]["id"]
        query_id = body["actions"][0]["value"]
        
        # Get original query from history
        # This would open a modal for query refinement
        await client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "Refine Query"},
                "blocks": [
                    {
                        "type": "input",
                        "element": {
                            "type": "plain_text_input",
                            "multiline": True,
                            "placeholder": {"type": "plain_text", "text": "How would you like to modify your question?"}
                        },
                        "label": {"type": "plain_text", "text": "Refined Question"}
                    }
                ],
                "submit": {"type": "plain_text", "text": "Submit"},
                "private_metadata": query_id
            }
        )
    
    async def _handle_share_query(self, body, client):
        """Handle share query button click"""
        user_id = body["user"]["id"]
        query_id = body["actions"][0]["value"]
        channel_id = body["channel"]["id"]
        
        # Share query with team (could post to a data team channel)
        if settings.slack_admin_channel:
            await client.chat_postMessage(
                channel=settings.slack_admin_channel,
                text=f"📊 Query shared by <@{user_id}> from <#{channel_id}>",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Query ID: `{query_id}` has been shared for team reference."
                        }
                    }
                ]
            )
    
    async def _handle_slash_command(self, body, client):
        """Handle /goose-query slash command"""
        user_id = body["user_id"]
        channel_id = body["channel_id"]
        text = body.get("text", "")
        
        if not text:
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="Usage: `/goose-query What was our revenue last month?`"
            )
            return
        
        # Process as regular query
        event = {
            "user": user_id,
            "channel": channel_id,
            "text": text,
            "ts": str(time.time())
        }
        
        async def say(text=None, blocks=None, thread_ts=None):
            return await client.chat_postMessage(
                channel=channel_id,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts
            )
        
        await self._process_query_request(event, say, client)
    
    async def _handle_error(self, error, body, logger):
        """Handle application errors"""
        logger.error("Slack app error", error=str(error), body=body)
        
        # Send error to admin channel if configured
        if settings.slack_admin_channel:
            try:
                await self.app.client.chat_postMessage(
                    channel=settings.slack_admin_channel,
                    text=f"🚨 Bot error: {str(error)[:500]}"
                )
            except:
                pass  # Don't fail on error reporting
    
    async def start(self):
        """Start the Slack bot"""
        await self.initialize()
        
        if settings.is_development:
            # Use Socket Mode for development
            handler = AsyncSocketModeHandler(self.app, settings.slack_app_token)
            await handler.start_async()
        else:
            # Use Events API for production
            # This would require additional setup for webhook endpoints
            logger.info("Production mode - configure webhook endpoints")
            # Implementation would depend on your deployment setup
    
    async def stop(self):
        """Stop the Slack bot and cleanup resources"""
        if self.db_manager:
            await self.db_manager.close()
        
        if hasattr(self.goose_client.client, 'close'):
            await self.goose_client.client.close()
        
        logger.info("Slack bot stopped")


# Main application entry point
async def main():
    """Main application entry point"""
    bot = GooseSlackBot()
    
    try:
        logger.info("Starting Goose Slack Bot...")
        await bot.start()
        
        # Keep the application running
        if settings.is_development:
            logger.info("Bot is running in development mode...")
            while True:
                await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error("Application error", error=str(e))
    finally:
        await bot.stop()


if __name__ == "__main__":
    # Setup logging
    from config import setup_logging
    setup_logging()
    
    # Run the bot
    asyncio.run(main())
