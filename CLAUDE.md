# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based MCP (Model Context Protocol) server that can be deployed both locally and as a web service. It uses the FastMCP framework and provides example tools and resources for AI agents.

## Development Commands

### Setup and Dependencies
```bash
# Install project dependencies
uv sync

# Install dev dependencies
uv sync --all-extras
```

### Running the Server

**Local development (stdio):**
```bash
# Default local mode
uv run python server.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector "uv" "run" "python" "server.py"
```

**Web mode (HTTP):**
```bash
# Run in HTTP mode locally
MCP_TRANSPORT=sse uv run python server.py

# Access at http://localhost:8899/sse
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
- **server.py**: Main application with environment-aware transport configuration
  - Tools: `add(a, b)` and `secret_word()`
  - Resources: `greeting://{name}` dynamic resource
  - Supports both stdio (local) and streamable-http (web) transports

## Key Configuration

- **MCP Version**: >=2.3.0 (supports streamable-http)
- **Python Version**: >=3.10
- **Package Manager**: uv with dependency locking
- **Dependencies**: mcp, anyio, typing-extensions, python-dotenv

## Environment Variables

Configure deployment with:
- `MCP_TRANSPORT`: "stdio" (default) or "sse" (for web)
- `MCP_HOST`: "0.0.0.0" (default for web)
- `MCP_PORT`: 8899 (HTTP) or 8443 (HTTPS)

**SSL Configuration:**
- `SSL_ENABLED`: Enable HTTPS (default: false)
- `SSL_CERT_PATH`: SSL certificate path
- `SSL_KEY_PATH`: SSL private key path
- `DOMAIN_NAME`: Domain for automatic Let's Encrypt certificates

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