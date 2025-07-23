#!/bin/bash
# Build Docker image for MCP server

# Set script to exit on error
set -e

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Build the Docker image
echo "Building MCP server Docker image..."
docker build -t mcp-demo-server:latest .

echo "Build complete! Image tagged as mcp-demo-server:latest"