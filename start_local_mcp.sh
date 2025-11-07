#!/bin/bash

echo "🚀 Starting Local Goose Query Expert MCP Server"
echo ""
echo "This will:"
echo "  1. Start a local MCP server on port 8765"
echo "  2. Expose it via ngrok tunnel"
echo "  3. Give you a public URL to configure in Heroku"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found. Installing..."
    echo "Run: brew install ngrok"
    echo "Or download from: https://ngrok.com/download"
    exit 1
fi

# Check if goose is installed
if ! command -v goose &> /dev/null; then
    echo "❌ goose not found. Make sure Goose is installed."
    exit 1
fi

echo "✅ Prerequisites found"
echo ""

# Start the MCP server in background
echo "📡 Starting MCP server on port 8765..."
python3 mcp_server.py &
MCP_PID=$!

# Wait for server to start
sleep 3

# Start ngrok tunnel
echo "🌐 Starting ngrok tunnel..."
echo ""
ngrok http 8765

# Cleanup on exit
trap "kill $MCP_PID" EXIT
