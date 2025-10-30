#!/usr/bin/env python3
"""
Mock Demo of Goose Query Expert Slackbot
Demonstrates the complete workflow without requiring Slack or external dependencies
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


class MockGooseClient:
    """Mock Goose Query Expert client"""
    
    async def find_table_metadata(self, question: str) -> Dict[str, Any]:
        """Simulate table metadata search"""
        await asyncio.sleep(1)  # Simulate API call
        
        return {
            "tables": [
                {
                    "table_name": "ANALYTICS.SALES.REVENUE_BY_CATEGORY",
                    "description": "Daily revenue aggregated by product category",
                    "columns": ["date", "product_category", "revenue", "transaction_count"],
                    "verification_status": "VERIFIED",
                    "total_users_recent": 25,
                    "score": 0.95
                },
                {
                    "table_name": "ANALYTICS.SALES.CUSTOMER_METRICS",
                    "description": "Customer acquisition and retention metrics",
                    "columns": ["customer_id", "acquisition_date", "ltv", "churn_risk"],
                    "verification_status": "VERIFIED",
                    "total_users_recent": 18,
                    "score": 0.87
                }
            ]
        }
    
    async def search_similar_queries(self, question: str) -> Dict[str, Any]:
        """Simulate similar query search"""
        await asyncio.sleep(1)  # Simulate API call
        
        return {
            "queries": [
                {
                    "query_text": "SELECT product_category, SUM(revenue) as total_revenue, COUNT(*) as transaction_count FROM ANALYTICS.SALES.REVENUE_BY_CATEGORY WHERE date_month = '2024-01' GROUP BY product_category ORDER BY total_revenue DESC",
                    "user_name": "john.doe",
                    "query_description": "Revenue analysis by product category",
                    "similarity_score": 0.95
                },
                {
                    "query_text": "SELECT DATE_TRUNC('month', date) as month, SUM(revenue) FROM ANALYTICS.SALES.REVENUE_BY_CATEGORY GROUP BY month",
                    "user_name": "jane.smith",
                    "query_description": "Monthly revenue trends",
                    "similarity_score": 0.87
                }
            ]
        }
    
    async def execute_query(self, sql: str) -> Dict[str, Any]:
        """Simulate query execution"""
        await asyncio.sleep(2)  # Simulate query execution
        
        return {
            "columns": ["product_category", "total_revenue", "transaction_count"],
            "rows": [
                ["Electronics", 1250000.50, 15420],
                ["Clothing", 890000.25, 22100],
                ["Home & Garden", 675000.75, 8930],
                ["Books", 234000.00, 12500]
            ],
            "row_count": 4,
            "execution_time": 2.34
        }


class MockSlackFormatter:
    """Format results for display"""
    
    def format_table(self, columns: List[str], rows: List[List[Any]]) -> str:
        """Create ASCII table"""
        if not rows:
            return "No data returned"
        
        # Convert to strings
        str_rows = [[str(cell) if cell is not None else "NULL" for cell in row] for row in rows]
        
        # Calculate widths
        col_widths = [len(col) for col in columns]
        for row in str_rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))
        
        # Limit width
        col_widths = [min(w, 20) for w in col_widths]
        
        # Create table
        separator = "┼".join("─" * (w + 2) for w in col_widths)
        header_sep = f"├{separator}┤"
        top_border = f"┌{separator.replace('┼', '┬')}┐"
        bottom_border = f"└{separator.replace('┼', '┴')}┘"
        
        # Header
        header_cells = [f" {col[:col_widths[i]]:<{col_widths[i]}} " for i, col in enumerate(columns)]
        header = "│" + "│".join(header_cells) + "│"
        
        # Rows
        table_rows = []
        for row in str_rows:
            row_cells = [f" {cell[:col_widths[i]]:<{col_widths[i]}} " for i, cell in enumerate(row)]
            table_rows.append("│" + "│".join(row_cells) + "│")
        
        return "\n".join([top_border, header, header_sep] + table_rows + [bottom_border])


async def simulate_query_workflow(question: str):
    """Simulate the complete query workflow"""
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}🤖 GOOSE QUERY EXPERT SLACKBOT - MOCK DEMO{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")
    
    # User question
    print(f"{Colors.BOLD}{Colors.CYAN}👤 User asks:{Colors.END}")
    print(f"   \"{question}\"\n")
    
    client = MockGooseClient()
    formatter = MockSlackFormatter()
    
    # Step 1: Initial response
    print(f"{Colors.YELLOW}🤔 Bot: Let me search for the best way to answer that...{Colors.END}")
    await asyncio.sleep(0.5)
    
    # Step 2: Search for tables
    print(f"{Colors.YELLOW}🔍 Bot: Searching for relevant data tables...{Colors.END}")
    table_results = await client.find_table_metadata(question)
    
    print(f"{Colors.GREEN}   ✓ Found {len(table_results['tables'])} relevant tables{Colors.END}")
    for table in table_results['tables'][:2]:
        print(f"     • {table['table_name']} (score: {table['score']:.2f})")
    print()
    
    # Step 3: Search for similar queries
    print(f"{Colors.YELLOW}📊 Bot: Looking for similar queries from your team...{Colors.END}")
    query_results = await client.search_similar_queries(question)
    
    print(f"{Colors.GREEN}   ✓ Found {len(query_results['queries'])} similar queries{Colors.END}")
    for query in query_results['queries'][:2]:
        print(f"     • By {query['user_name']}: {query['query_description']}")
    print()
    
    # Step 4: Generate SQL
    print(f"{Colors.YELLOW}⚡ Bot: Generating optimized SQL query...{Colors.END}")
    await asyncio.sleep(1)
    
    sql = query_results['queries'][0]['query_text']
    print(f"{Colors.GREEN}   ✓ SQL generated{Colors.END}\n")
    
    # Step 5: Execute query
    print(f"{Colors.YELLOW}🏃 Bot: Executing query against Snowflake...{Colors.END}")
    result = await client.execute_query(sql)
    
    print(f"{Colors.GREEN}   ✓ Query completed successfully!{Colors.END}\n")
    
    # Step 6: Display results
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}📊 QUERY RESULTS ({result['row_count']} rows){Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    # Show table
    table = formatter.format_table(result['columns'], result['rows'])
    print(table)
    
    # Show SQL
    print(f"\n{Colors.BOLD}SQL Query:{Colors.END}")
    print(f"{Colors.CYAN}```sql")
    print(sql)
    print(f"```{Colors.END}")
    
    # Show metadata
    print(f"\n{Colors.BOLD}Execution Details:{Colors.END}")
    print(f"⏱️  Executed in {result['execution_time']:.2f}s")
    print(f"📄 {result['row_count']} rows returned")
    
    # Show experts
    print(f"\n{Colors.BOLD}Data Experts:{Colors.END}")
    for query in query_results['queries'][:2]:
        print(f"• {Colors.GREEN}{query['user_name']}{Colors.END}: {query['query_description']}")
    
    # Show similar tables
    print(f"\n{Colors.BOLD}Other Relevant Tables:{Colors.END}")
    for table in table_results['tables'][:2]:
        print(f"• {Colors.GREEN}{table['table_name']}{Colors.END}")
        print(f"  {table['description']}")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}✅ Query completed successfully!{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'='*80}{Colors.END}\n")


async def demo_multiple_queries():
    """Demo multiple query scenarios"""
    
    queries = [
        "What was our revenue last month by product category?",
        "Show me top customers by sales",
        "How many users signed up this week?"
    ]
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}🎬 RUNNING MULTIPLE QUERY DEMOS{Colors.END}\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n{Colors.BOLD}Demo {i} of {len(queries)}{Colors.END}")
        await simulate_query_workflow(query)
        
        if i < len(queries):
            print(f"\n{Colors.YELLOW}Press Enter to continue to next demo...{Colors.END}")
            input()


def show_architecture():
    """Display system architecture"""
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}🏗️  SYSTEM ARCHITECTURE{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")
    
    architecture = """
┌─────────────────────────────────────────────────────────────────┐
│                        SLACK WORKSPACE                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   User A    │  │   User B    │  │   User C    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Socket Mode / Events API
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                 SLACK BOT APPLICATION                           │
│  • Event handling    • Authentication    • Result formatting    │
│  • Query processing  • Session management • Error handling      │
└─────────────────────┬───────────────────────────────────────────┘
                      │ MCP Protocol
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│              GOOSE QUERY EXPERT                                 │
│  • Table metadata search   • Similar query discovery            │
│  • SQL generation          • Query execution                    │
│  • Permission checking     • Result processing                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Snowflake Connector
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    SNOWFLAKE                                    │
│  • Data warehouses  • Analytics tables  • Security policies    │
└─────────────────────────────────────────────────────────────────┘
"""
    
    print(architecture)
    
    print(f"\n{Colors.BOLD}Key Components:{Colors.END}")
    print(f"  {Colors.GREEN}✓{Colors.END} Slack Integration - Handles user interactions")
    print(f"  {Colors.GREEN}✓{Colors.END} Query Processing - Natural language to SQL")
    print(f"  {Colors.GREEN}✓{Colors.END} Goose Query Expert - Table discovery & query generation")
    print(f"  {Colors.GREEN}✓{Colors.END} Snowflake - Live data execution")
    print(f"  {Colors.GREEN}✓{Colors.END} Security Layer - Authentication & permissions")
    print(f"  {Colors.GREEN}✓{Colors.END} Monitoring - Health checks & metrics")


def show_features():
    """Display key features"""
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}✨ KEY FEATURES{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")
    
    features = [
        ("Natural Language Queries", "Ask questions in plain English"),
        ("Intelligent Table Discovery", "Automatically finds relevant data"),
        ("SQL Generation", "Creates optimized queries"),
        ("Real-time Execution", "Runs against live Snowflake data"),
        ("Team Collaboration", "Share queries and learn from experts"),
        ("Security & Permissions", "Role-based access control"),
        ("Query History", "Track and replay past queries"),
        ("Interactive Results", "Refine and drill down"),
        ("Expert Identification", "Find data experts on your team"),
        ("Production Ready", "Auto-scaling, monitoring, alerts")
    ]
    
    for feature, description in features:
        print(f"  {Colors.GREEN}✓{Colors.END} {Colors.BOLD}{feature}{Colors.END}")
        print(f"    {description}\n")


def show_next_steps():
    """Display next steps"""
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}🚀 NEXT STEPS TO DEPLOY FOR REAL{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")
    
    print(f"{Colors.BOLD}To deploy this with real Slack integration:{Colors.END}\n")
    
    print(f"{Colors.CYAN}1. Create Slack App (10 minutes){Colors.END}")
    print(f"   • Go to https://api.slack.com/apps")
    print(f"   • Create new app in Block workspace")
    print(f"   • Get bot token, app token, signing secret")
    print(f"   • See DEPLOY_NOW.md for detailed steps\n")
    
    print(f"{Colors.CYAN}2. Configure Environment{Colors.END}")
    print(f"   • Copy env.example to .env")
    print(f"   • Add your Slack credentials")
    print(f"   • Configure Goose Query Expert URL\n")
    
    print(f"{Colors.CYAN}3. Deploy{Colors.END}")
    print(f"   • Run: make setup")
    print(f"   • Run: make deploy-dev")
    print(f"   • Invite bot to Slack channels\n")
    
    print(f"{Colors.CYAN}4. Test & Use{Colors.END}")
    print(f"   • Ask questions in Slack")
    print(f"   • Share with your team")
    print(f"   • Monitor usage and performance\n")
    
    print(f"{Colors.BOLD}Documentation:{Colors.END}")
    print(f"  • Quick Start: {Colors.GREEN}QUICK_START.md{Colors.END}")
    print(f"  • Full Setup: {Colors.GREEN}SETUP.md{Colors.END}")
    print(f"  • User Manual: {Colors.GREEN}USER_MANUAL.md{Colors.END}")
    print(f"  • Deployment: {Colors.GREEN}DEPLOY_NOW.md{Colors.END}\n")


async def main():
    """Main demo function"""
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}   GOOSE QUERY EXPERT SLACKBOT - INTERACTIVE DEMO{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")
    
    print(f"{Colors.BOLD}This demo shows how the Slackbot works without requiring:{Colors.END}")
    print(f"  • Slack credentials")
    print(f"  • Database setup")
    print(f"  • Docker installation")
    print(f"  • External dependencies\n")
    
    print(f"{Colors.YELLOW}What would you like to see?{Colors.END}\n")
    print(f"  1. Single query demo")
    print(f"  2. Multiple query demos")
    print(f"  3. System architecture")
    print(f"  4. Key features")
    print(f"  5. Next steps to deploy")
    print(f"  6. Run all demos")
    print(f"  0. Exit\n")
    
    choice = input(f"{Colors.BOLD}Enter your choice (1-6, 0 to exit): {Colors.END}")
    
    if choice == "1":
        question = input(f"\n{Colors.BOLD}Enter your question (or press Enter for default): {Colors.END}")
        if not question:
            question = "What was our revenue last month by product category?"
        await simulate_query_workflow(question)
    
    elif choice == "2":
        await demo_multiple_queries()
    
    elif choice == "3":
        show_architecture()
    
    elif choice == "4":
        show_features()
    
    elif choice == "5":
        show_next_steps()
    
    elif choice == "6":
        await simulate_query_workflow("What was our revenue last month by product category?")
        show_architecture()
        show_features()
        show_next_steps()
    
    elif choice == "0":
        print(f"\n{Colors.GREEN}Thanks for checking out the demo!{Colors.END}\n")
        return
    
    else:
        print(f"\n{Colors.RED}Invalid choice. Please try again.{Colors.END}")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}Demo complete! Check out the documentation for next steps.{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'='*80}{Colors.END}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Demo interrupted. Goodbye!{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}\n")
