#!/bin/bash
# Run MCP server locally in Docker

# Set script to exit on error
set -e

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Check if .env file exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    ENV_FILE_ARG="--env-file .env"
else
    echo "No .env file found, using default environment variables"
    ENV_FILE_ARG=""
fi

# Check if SSL is enabled in environment
SSL_ENABLED=$(grep -E "^SSL_ENABLED=" .env 2>/dev/null | cut -d'=' -f2 || echo "false")

if [ "$SSL_ENABLED" = "true" ]; then
    echo "Starting MCP server on https://localhost:8443/sse"
    echo "Note: Ensure SSL certificates are available at /etc/ssl/certs/cert.pem and /etc/ssl/private/key.pem"
    docker run --rm -it \
        --name mcp-server-web \
        -p 8443:8443 \
        -v /etc/ssl:/etc/ssl:ro \
        $ENV_FILE_ARG \
        mcp-server-web:latest
else
    echo "Starting MCP server on http://localhost:8899/sse"
    docker run --rm -it \
        --name mcp-server-web \
        -p 8899:8899 \
        $ENV_FILE_ARG \
        mcp-server-web:latest
fi

echo "Server stopped"