# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based MCP (Model Context Protocol) server designed for web deployment using HTTPS and Server-Sent Events (SSE). It uses the FastMCP framework and provides example tools and resources for AI agents.

## Development Commands

### Setup and Dependencies
```bash
# Install project dependencies
uv sync

# Install dev dependencies
uv sync --all-extras
```

### Running the Server

**Local development (HTTP):**
```bash
# Run in HTTP mode locally
uv run python server.py

# Access at http://localhost:8899/sse
```

**Production (HTTPS):**
```bash
# Run with SSL enabled
SSL_ENABLED=true uv run python server.py

# Access at https://localhost:8443/sse
```

### Code Quality Commands
```bash
# Format code
uv run black server.py

# Type checking
uv run mypy server.py

# Linting
uv run flake8 server.py

# Run tests
uv run pytest
```

## Architecture

**Single-file architecture:**
- **server.py**: Main application with HTTPS/SSE web server
  - Tools: `add(a, b)` and `secret_word()`
  - Resources: `greeting://{name}` dynamic resource
  - SSE transport for real-time communication with Claude Code

## Key Configuration

- **MCP Version**: >=2.3.0 (supports SSE transport)
- **Python Version**: >=3.10
- **Package Manager**: uv with dependency locking
- **Dependencies**: mcp, uvicorn, python-dotenv

## Environment Variables

**Server Configuration:**
- `MCP_HOST`: Server host (default: "0.0.0.0")
- `MCP_PORT`: Server port (default: 8899 HTTP, 8443 HTTPS)

**SSL Configuration:**
- `SSL_ENABLED`: Enable HTTPS (default: false)
- `SSL_CERT_PATH`: SSL certificate path (default: "/etc/ssl/certs/cert.pem")
- `SSL_KEY_PATH`: SSL private key path (default: "/etc/ssl/private/key.pem")
- `DOMAIN_NAME`: Domain for automatic Let's Encrypt certificates

**Authentication:**
- `AUTH_ENABLED`: Enable API key authentication (default: false)
- `API_KEYS`: Comma-separated "user:key" pairs

## Web Deployment

### Docker Deployment
```bash
# Build and run locally (HTTP)
./scripts/build.sh
./scripts/run-local.sh

# Server available at http://localhost:8899/sse
```

### GCP Deployment
```bash
# HTTP deployment
export GCP_PROJECT_ID=your-project-id
./scripts/deploy-gcp.sh

# HTTPS deployment with SSL
export GCP_PROJECT_ID=your-project-id
export DOMAIN_NAME=your-domain.com
export SSL_EMAIL=admin@your-domain.com
./scripts/deploy-gcp.sh
```

### Testing Deployment
```bash
# Test HTTP endpoint
curl http://localhost:8899/sse

# Test HTTPS endpoint
curl https://your-domain.com:8443/sse
```

## Client Compatibility

This MCP server is designed for **Claude Code** which natively supports SSE transport over HTTPS. Claude Desktop is not supported as it only works with stdio transport.