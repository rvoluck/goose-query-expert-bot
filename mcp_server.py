"""
Local MCP Server for Query Expert
Exposes Query Expert tools via HTTP for the Slackbot to use
"""

import asyncio
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import subprocess
import structlog

logger = structlog.get_logger()

app = FastAPI(title="Goose Query Expert MCP Server")


class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any]


class MCPResponse(BaseModel):
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


async def call_goose_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call a Goose Query Expert tool via CLI
    This assumes you have goose installed and Query Expert extension enabled
    """
    try:
        # Build the goose command
        # Format: goose session run --tool <tool_name> --args '{"arg1": "value1"}'
        args_json = json.dumps(arguments)
        
        cmd = [
            "goose",
            "toolkit",
            "call",
            tool_name,
            "--args",
            args_json
        ]
        
        logger.info("Calling Goose tool", tool=tool_name, args=arguments)
        
        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error"
            logger.error("Goose tool failed", tool=tool_name, error=error_msg)
            raise Exception(f"Goose tool failed: {error_msg}")
        
        # Parse the output
        output = result.stdout.strip()
        
        # Try to parse as JSON
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            # If not JSON, return as text
            return {"output": output}
            
    except subprocess.TimeoutExpired:
        raise Exception("Goose tool timed out after 5 minutes")
    except Exception as e:
        logger.error("Error calling Goose tool", tool=tool_name, error=str(e))
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "goose-mcp-server"}


@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest) -> MCPResponse:
    """
    MCP endpoint that receives tool calls and forwards to Goose
    """
    try:
        if request.method != "tools/call":
            raise HTTPException(status_code=400, detail=f"Unsupported method: {request.method}")
        
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Missing tool name")
        
        logger.info("Received MCP request", tool=tool_name)
        
        # Call the Goose tool
        result = await call_goose_tool(tool_name, arguments)
        
        return MCPResponse(result=result)
        
    except Exception as e:
        logger.error("MCP request failed", error=str(e))
        return MCPResponse(error=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Goose Query Expert MCP Server",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp (POST)"
        },
        "supported_tools": [
            "queryexpert__find_table_meta_data",
            "queryexpert__query_expert_search",
            "queryexpert__execute_query"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Goose Query Expert MCP Server...")
    print("📡 This will expose your local Goose Query Expert to the Slackbot")
    print("🔒 Make sure Query Expert extension is enabled in your Goose config")
    print("")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8765,
        log_level="info"
    )
