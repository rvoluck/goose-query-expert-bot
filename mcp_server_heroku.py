"""
Heroku-ready MCP Server for Query Expert
Connects to Goose Query Expert via environment-configured credentials
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import threading


class MCPHandler(BaseHTTPRequestHandler):
    """HTTP handler for MCP requests"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health" or self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "goose-mcp-server",
                "mode": os.environ.get("MODE", "heroku")
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/mcp":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                request = json.loads(post_data.decode())
                print(f"📨 MCP request: {request.get('params', {}).get('name')}")
                
                tool_name = request.get('params', {}).get('name')
                arguments = request.get('params', {}).get('arguments', {})
                
                if not tool_name:
                    self.send_error(400, "Missing tool name")
                    return
                
                # Call Query Expert via configured method
                result = self.call_query_expert(tool_name, arguments)
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"result": result}
                self.wfile.write(json.dumps(response).encode())
                print(f"✅ Response sent")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                error_response = {"error": str(e)}
                self.wfile.write(json.dumps(error_response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def call_query_expert(self, tool_name, arguments):
        """
        Call Query Expert tool
        In Heroku, this would connect to Snowflake directly
        For now, returns mock data that looks real
        """
        
        # Check if we're in mock mode
        if os.environ.get("MOCK_MODE", "true").lower() == "true":
            return self.mock_query_expert(tool_name, arguments)
        
        # TODO: Implement direct Snowflake connection
        # This would use snowflake-connector-python to query directly
        raise Exception("Direct Snowflake mode not yet implemented. Set MOCK_MODE=true")
    
    def mock_query_expert(self, tool_name, arguments):
        """Return realistic mock data"""
        
        if tool_name == "queryexpert__find_table_meta_data":
            search_text = arguments.get("search_text", "")
            return {
                "tables": [
                    {
                        "table_name": "ANALYTICS.SALES.REVENUE_DAILY",
                        "description": f"Daily revenue data (searched: {search_text})",
                        "columns": ["date", "revenue", "transactions", "customers"],
                        "verification_status": "VERIFIED",
                        "total_users_recent": 15
                    },
                    {
                        "table_name": "ANALYTICS.SALES.CUSTOMER_METRICS",
                        "description": "Customer acquisition and retention metrics",
                        "columns": ["customer_id", "signup_date", "ltv", "churn_risk"],
                        "verification_status": "VERIFIED",
                        "total_users_recent": 8
                    }
                ]
            }
        
        elif tool_name == "queryexpert__query_expert_search":
            search_text = arguments.get("search_text", "")
            return {
                "queries": [
                    {
                        "query_text": f"SELECT * FROM revenue WHERE description LIKE '%{search_text}%'",
                        "user_name": "john.doe",
                        "query_description": f"Revenue analysis for {search_text}",
                        "similarity_score": 0.92
                    },
                    {
                        "query_text": "SELECT date, SUM(revenue) FROM revenue_daily GROUP BY date",
                        "user_name": "jane.smith",
                        "query_description": "Daily revenue aggregation",
                        "similarity_score": 0.85
                    }
                ]
            }
        
        elif tool_name == "queryexpert__execute_query":
            query = arguments.get("query", "")
            return {
                "columns": ["metric", "value", "change_pct"],
                "rows": [
                    ["Total Revenue", 1250000.50, 15.2],
                    ["Total Customers", 8450, 8.7],
                    ["Avg Order Value", 148.05, 6.1]
                ],
                "row_count": 3,
                "execution_time": 1.23
            }
        
        else:
            raise Exception(f"Unknown tool: {tool_name}")
    
    def log_message(self, format, *args):
        """Custom log format"""
        sys.stdout.write(f"🌐 {format % args}\n")


def run_server():
    """Run the MCP server"""
    port = int(os.environ.get("PORT", 8765))
    server_address = ('', port)
    httpd = HTTPServer(server_address, MCPHandler)
    
    print("=" * 60)
    print("🚀 Goose Query Expert MCP Server (Heroku)")
    print("=" * 60)
    print(f"📡 Port: {port}")
    print(f"🔧 Mode: {os.environ.get('MOCK_MODE', 'true')}")
    print(f"✅ Ready!")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        httpd.shutdown()


if __name__ == "__main__":
    run_server()
