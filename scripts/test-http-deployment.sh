#!/bin/bash

# Test script to run MCP server in HTTP mode for Claude Code testing

echo "Starting MCP server in HTTP mode for testing..."

# Run with HTTP (no SSL)
docker run -d \
  --name mcp-demo-server-http \
  -p 8899:8899 \
  -e MCP_TRANSPORT=sse \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8899 \
  -e SSL_ENABLED=false \
  mcp-demo-server:latest

echo "Server should be available at http://$(curl -s ifconfig.me):8899/sse"
echo ""
echo "To add to Claude Code:"
echo "claude mcp add demo-server --transport sse http://$(curl -s ifconfig.me):8899/sse"
echo ""
echo "To stop: docker stop mcp-demo-server-http && docker rm mcp-demo-server-http"