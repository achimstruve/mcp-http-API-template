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
docker build -t mcp-server-web:latest .

echo "Build complete! Image tagged as mcp-server-web:latest"

# Clean up intermediate images
echo "Cleaning up intermediate build layers..."
docker image prune -f --filter "label!=mcp-server-web"

# Show disk usage after cleanup
echo "Docker disk usage after cleanup:"
docker system df