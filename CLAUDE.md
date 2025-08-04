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
uv run black server.py oauth.py

# Type checking
uv run mypy server.py oauth.py

# Linting
uv run flake8 server.py oauth.py

# Run tests
uv run pytest
```

## Architecture

**Main components:**
- **server.py**: Main application with HTTPS/SSE web server and comprehensive OAuth endpoints
  - Tools: `add(a, b)` and `secret_word()`
  - Resources: `greeting://{name}` dynamic resource
  - OAuth endpoints: `/.well-known/oauth-authorization-server`, `/.well-known/oauth-protected-resource`, `/register`, `/authorize`, `/callback`, `/token`
  - SSE transport for real-time communication with Claude Code
  - OAuth-aware authentication wrapper
- **oauth.py**: OAuth 2.1 + PKCE implementation with Google authentication
  - Dynamic Client Registration (RFC 7591)
  - OAuth Authorization Server Metadata (RFC 8414)
  - OAuth Protected Resource Metadata (RFC 8707) 
  - PKCE support (RFC 7636)
  - JWT token generation and validation
- **generate_token.py**: Manual token generation utility for headless environments

## Key Configuration

- **MCP Version**: >=2.3.0 (supports SSE transport)
- **Python Version**: >=3.10
- **Package Manager**: uv with dependency locking
- **Dependencies**: mcp, uvicorn, python-dotenv, authlib, httpx, pyjwt

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
- `MCP_AUTH_TOKEN`: Pre-generated JWT token for headless authentication (optional)

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

# Test OAuth metadata endpoint
curl https://your-domain.com:8443/.well-known/oauth-authorization-server

# Test HTTPS endpoint (requires JWT token)
curl -H "Authorization: Bearer your-jwt-token" https://your-domain.com:8443/sse
```

## Authentication

### OAuth 2.1 with PKCE
This server implements OAuth 2.1 with PKCE (Proof Key for Code Exchange) for secure authentication:

1. **Claude Code Integration**: Add the server and complete OAuth flow when prompted
2. **Manual Token Generation**: Use `./generate_token.py` for headless environments
3. **Environment Variable**: Set `MCP_AUTH_TOKEN` for pre-authenticated access

### Authentication Workflows

**Claude Code (Recommended - OAuth 2.1 + PKCE):**
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

**Manual Token Generation (for testing/headless):**
```bash
# Generate token manually
uv run python generate_token.py

# Use token with environment variable
export MCP_AUTH_TOKEN="eyJhbGciOiJIUzI1NiIs..."

# Or set in .env file
echo "MCP_AUTH_TOKEN=your-jwt-token" >> .env
```

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