"""
Simple MCP Server for Query Expert (No FastAPI required!)
Uses only Python standard library
"""

import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys


class MCPHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for MCP requests"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        elif self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "service": "Goose Query Expert MCP Server",
                "status": "running",
                "supported_tools": [
                    "queryexpert__find_table_meta_data",
                    "queryexpert__query_expert_search",
                    "queryexpert__execute_query"
                ]
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/mcp":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request = json.loads(post_data.decode())
                print(f"📨 Received MCP request: {request.get('params', {}).get('name')}")
                
                # Extract tool name and arguments
                tool_name = request.get('params', {}).get('name')
                arguments = request.get('params', {}).get('arguments', {})
                
                if not tool_name:
                    self.send_error(400, "Missing tool name")
                    return
                
                # Call Goose tool
                result = self.call_goose_tool(tool_name, arguments)
                
                # Send response
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"result": result}
                self.wfile.write(json.dumps(response).encode())
                print(f"✅ Sent response")
                
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
    
    def call_goose_tool(self, tool_name, arguments):
        """Call a Goose Query Expert tool"""
        try:
            # Build command
            args_json = json.dumps(arguments)
            cmd = ["goose", "toolkit", "call", tool_name, "--args", args_json]
            
            print(f"🔧 Calling: {' '.join(cmd[:4])}...")
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                error = result.stderr or "Unknown error"
                print(f"❌ Goose error: {error}")
                raise Exception(f"Goose tool failed: {error}")
            
            # Parse output
            output = result.stdout.strip()
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return {"output": output}
                
        except subprocess.TimeoutExpired:
            raise Exception("Goose tool timed out after 5 minutes")
        except FileNotFoundError:
            raise Exception("Goose command not found. Is Goose installed?")
        except Exception as e:
            raise Exception(f"Error calling Goose: {str(e)}")
    
    def log_message(self, format, *args):
        """Custom log format"""
        sys.stdout.write(f"🌐 {self.address_string()} - {format % args}\n")


def run_server(port=8765):
    """Run the MCP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MCPHandler)
    
    print("=" * 60)
    print("🚀 Goose Query Expert MCP Server")
    print("=" * 60)
    print(f"📡 Listening on: http://0.0.0.0:{port}")
    print(f"🔍 Health check: http://localhost:{port}/health")
    print(f"📬 MCP endpoint: http://localhost:{port}/mcp")
    print("")
    print("✅ Ready to receive requests from Slackbot!")
    print("💡 Make sure Goose Query Expert extension is enabled")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print("")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    run_server(port)
