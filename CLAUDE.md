# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready Python MCP (Model Context Protocol) server with OAuth 2.1 + PKCE authentication, designed for web deployment using HTTPS and Server-Sent Events (SSE). It uses the FastMCP framework and provides comprehensive OAuth endpoints for secure client integration.

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
uv run black server.py oauth.py database.py logging_decorator.py

# Type checking
uv run mypy server.py oauth.py database.py logging_decorator.py

# Linting
uv run flake8 server.py oauth.py database.py logging_decorator.py

# Run tests
uv run pytest
```

## Architecture

**Main components:**
- **server.py**: Main application with HTTPS/SSE web server and comprehensive OAuth endpoints
  - Tools: `add(a, b)`, `secret_word()`, and `get_usage_stats()` (all with automatic logging)
  - Resources: `greeting://{name}` dynamic resource
  - OAuth endpoints: `/.well-known/oauth-authorization-server`, `/.well-known/oauth-protected-resource`, `/register`, `/authorize`, `/callback`, `/token`
  - SSE transport for real-time communication with Claude Code
  - OAuth-aware authentication wrapper with user context propagation
- **oauth.py**: OAuth 2.1 + PKCE implementation with Google authentication
  - Dynamic Client Registration (RFC 7591)
  - OAuth Authorization Server Metadata (RFC 8414)
  - OAuth Protected Resource Metadata (RFC 8707) 
  - PKCE support (RFC 7636)
  - JWT token generation and validation
- **database.py**: SQLite database operations for tool usage logging
  - Async SQLite support with aiosqlite
  - User tracking and tool usage logging
  - Database schema initialization
  - Usage statistics aggregation
- **logging_decorator.py**: Automatic tool logging decorator
  - Captures tool execution context, timing, and results
  - Integrates with OAuth user context
  - Error handling and rollback support

## Key Configuration

- **MCP Version**: >=2.3.0 (supports SSE transport)
- **Python Version**: >=3.10
- **Package Manager**: uv with dependency locking
- **Dependencies**: mcp, uvicorn, python-dotenv, authlib, httpx, pyjwt, aiosqlite

## Environment Variables

**Server Configuration:**
- `SERVER_NAME`: Name for the MCP server, Docker image, and container (default: "mcp-template")
- `MCP_HOST`: Server host (default: "0.0.0.0")
- `MCP_PORT`: Server port (default: 8899 HTTP, 8443 HTTPS)

**SSL Configuration:**
- `SSL_ENABLED`: Enable HTTPS (default: false)
- `SSL_CERT_PATH`: SSL certificate path (default: "/etc/ssl/certs/cert.pem")
- `SSL_KEY_PATH`: SSL private key path (default: "/etc/ssl/private/key.pem")
- `DOMAIN_NAME`: Domain for automatic Let's Encrypt certificates

**OAuth Authentication:**
- `GOOGLE_CLIENT_ID`: Google OAuth Client ID (required for authentication)
- `GOOGLE_CLIENT_SECRET`: Google OAuth Client Secret
- `OAUTH_REDIRECT_URI`: OAuth callback URL (e.g., https://your-domain.com:8443/callback)
- `JWT_SECRET_KEY`: Secret key for signing JWT tokens

**Database Configuration:**
- `DATABASE_PATH`: SQLite database file path (default: "mcp_server.db")
- `ENABLE_LOGGING`: Enable/disable tool usage logging (default: "true")

## Web Deployment

### Docker Deployment
```bash
# Build and run locally (HTTP)
./scripts/build.sh
./scripts/run-local.sh

# Server available at http://localhost:8899/sse
```

### HTTPS Deployment with Let's Encrypt
```bash
# Deploy with automatic SSL certificate generation
export SSL_EMAIL=admin@your-domain.com
sudo -E ./scripts/run-with-letsencrypt.sh
```

The `run-with-letsencrypt.sh` script automatically obtains SSL certificates from Let's Encrypt using certbot and deploys the server with HTTPS enabled. This script handles the complete SSL setup and certificate management for production deployments.

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

# Test OAuth metadata endpoint
curl https://your-domain.com:8443/.well-known/oauth-authorization-server

# Test HTTPS endpoint (requires JWT token)
curl -H "Authorization: Bearer your-jwt-token" https://your-domain.com:8443/sse
```

## Authentication

### OAuth 2.1 with PKCE
This server implements OAuth 2.1 with PKCE (Proof Key for Code Exchange) for secure authentication.

**Claude Code Integration (OAuth 2.1 + PKCE):**
```bash
# Add MCP server (OAuth flow starts automatically)
claude mcp add --transport sse my-server https://your-domain.com:8443/sse

# Claude Code will:
# 1. Discover OAuth server capabilities
# 2. Register as dynamic client (RFC 7591)
# 3. Initiate PKCE-enabled OAuth flow
# 4. Complete Google authentication in browser
# 5. Exchange authorization code with PKCE verifier
```

**Note**: Browser access is required for authentication. This server does not support headless authentication.

## OAuth 2.1 Endpoints

**Discovery Endpoints:**
- `/.well-known/oauth-authorization-server` - OAuth server metadata (RFC 8414)
- `/.well-known/oauth-protected-resource` - Protected resource metadata (RFC 8707)

**OAuth Flow Endpoints:**
- `/register` - Dynamic client registration (RFC 7591)
- `/authorize` - OAuth authorization endpoint  
- `/callback` - OAuth callback handler
- `/token` - Token exchange with PKCE validation

**MCP Endpoint:**
- `/sse` - MCP Server-Sent Events endpoint (requires authentication)

## Client Compatibility

This MCP server is designed for **Claude Code** which natively supports:
- SSE transport over HTTPS
- OAuth 2.1 with PKCE
- Dynamic client registration
- Automatic token management

Claude Desktop is not supported as it only works with stdio transport.

## Database Logging

The server includes automatic SQLite database logging for tool usage tracking:

**Features:**
- All MCP tools decorated with `@logged_tool` are automatically tracked
- Captures OAuth user information, tool arguments, results, and execution time
- Database operations are async to avoid blocking tool execution
- Statistics available via `get_usage_stats()` tool

**Database Tables:**
- `users`: Tracks OAuth users (id, email, name, first/last seen)
- `tool_usage_logs`: Records every tool call with full context

**Configuration:**
- Set `DATABASE_PATH` to specify database location
- Set `ENABLE_LOGGING=false` to disable logging
- Database is automatically initialized on server startup

**Template Pattern:**
This database integration serves as a template showing how to:
- Add persistent storage to MCP servers
- Track user activity and tool usage
- Implement async database operations
- Create reusable decorators for cross-cutting concerns