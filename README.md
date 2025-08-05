# MCP Server Template

A production-ready FastMCP server template with HTTPS support, authentication, and Docker deployment. This template provides a foundation for building secure, web-accessible MCP servers that can be used by Claude Code and other AI agents over HTTP/HTTPS with SSE transport.

## Features

- **🔒 OAuth 2.1 + PKCE**: Google OAuth 2.1 with PKCE for enhanced security
- **🔄 Dynamic Client Registration**: RFC 7591 compliant for Claude Code compatibility
- **🌐 HTTPS Support**: SSL/TLS encryption with Let's Encrypt integration
- **🐳 Docker Deployment**: Production-ready containerized deployment
- **⚡ FastMCP Integration**: Built on the modern FastMCP framework
- **🛡️ Security First**: JWT tokens, PKCE validation, and comprehensive OAuth endpoints
- **📊 Database Logging**: SQLite integration for tool usage tracking and analytics

### Example Tools & Resources

- **Addition tool**: Demonstrates basic tool functionality with database logging
- **Secret word tool**: Shows authenticated tool access with usage tracking
- **Dynamic greeting resource**: Example of parametrized resources
- **Usage statistics tool**: Admin tool to view database usage statistics

## Quick Start

### Prerequisites

- Python 3.10+
- Docker
- A domain name (for HTTPS deployment)
- Browser access (required for OAuth authentication)

### 1. Clone and Setup

```bash
git clone https://github.com/your-username/mcp-server-template.git
cd mcp-server-template

# Install dependencies
pip install uv
uv sync
```

### 2. Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `https://your-domain.com:8443/callback`

### 3. Configure Environment

Create a `.env` file:

```bash
# Server Configuration
SERVER_NAME=mcp-template       # Name for the MCP server, Docker image, and container

# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
OAUTH_REDIRECT_URI=https://your-domain.com:8443/callback
JWT_SECRET_KEY=your-secure-random-string-here

# SSL/HTTPS (for production)
SSL_ENABLED=true
DOMAIN_NAME=your-domain.com
SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem

# MCP Configuration
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8443

# Database Configuration (optional)
DATABASE_PATH=mcp_server.db    # SQLite database path
ENABLE_LOGGING=true             # Enable tool usage logging
```

### 4. Deploy

#### Local Development
```bash
# Run locally without SSL
MCP_TRANSPORT=sse SSL_ENABLED=false uv run python server.py
```

#### Production Deployment
```bash
# Build Docker image
./scripts/build.sh

# Deploy with HTTPS and Let's Encrypt
export DOMAIN_NAME=your-domain.com
export SSL_EMAIL=admin@your-domain.com
export GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
export GOOGLE_CLIENT_SECRET=your-google-client-secret
export OAUTH_REDIRECT_URI=https://your-domain.com:8443/callback
export JWT_SECRET_KEY=$(openssl rand -base64 32)
sudo -E ./scripts/run-with-letsencrypt.sh
```

Your server will be available at: `https://your-domain.com:8443/sse`

## Using This Template

### For Template Users

1. **Fork this repository**
2. **Update `server.py`**:
   - Replace example tools with your own tools
   - Update the server name in `FastMCP("YourServerName")`
   - Add your custom resources

3. **Update `pyproject.toml`**:
   - Change `name` to your project name
   - Update `description`
   - Add any additional dependencies

4. **Configure deployment**:
   - Set up Google OAuth credentials
   - Configure your domain name and OAuth redirect URI
   - Generate a secure JWT secret key

### Example Tool Implementation

```python
@mcp.tool()
def my_custom_tool(param1: str, param2: int) -> str:
    """Your custom tool description"""
    # Your tool logic here
    return f"Result: {param1} with {param2}"

@mcp.resource("my-resource://{id}")
def get_my_resource(id: str) -> str:
    """Your custom resource description"""
    # Your resource logic here
    return f"Resource data for {id}"
```

## Client Setup

### Claude Code (Supported)

Claude Code natively supports SSE transport over HTTPS with OAuth 2.1 + PKCE. Add your MCP server:

```bash
# Add the server (OAuth flow will start automatically)
claude mcp add --transport sse my-server https://your-domain.com:8443/sse
```

When you connect, Claude Code will:
1. Discover OAuth server capabilities
2. Register itself as a dynamic client (RFC 7591)
3. Open your browser for Google authentication
4. Complete PKCE flow and store token securely

⚠️ **Note**: Browser access is required for authentication. This server does not support headless authentication.

### Claude Desktop (Not Supported)

⚠️ **Note**: Claude Desktop only supports stdio transport and cannot connect to HTTP/HTTPS MCP servers. Use Claude Code instead for web-based MCP servers.

### Other MCP Clients

Configure your MCP client with:
- **Transport**: `sse` (Server-Sent Events)
- **URL**: `https://your-domain.com:8443/sse`
- **Authentication**: OAuth 2.0 with JWT tokens

### Testing Your Server

```bash
# Test connectivity
curl https://your-domain.com:8443/sse

# Test OAuth metadata endpoint
curl https://your-domain.com:8443/.well-known/oauth-authorization-server

# After OAuth authentication, test with JWT token
curl -H "Authorization: Bearer your-jwt-token" https://your-domain.com:8443/sse

# Test specific tools (requires MCP client)
# Your MCP client will be able to call tools like:
# - add(5, 3) -> 8
# - secret_word() -> "OVPostWebExperts"
# - get_usage_stats() -> {"total_users": 5, "total_calls": 42, ...}
# - greeting://John -> "Hello, John!"
```

## Architecture

### Files Structure

```
├── server.py              # Main MCP server implementation
├── oauth.py               # OAuth 2.0 authentication implementation
├── database.py            # SQLite database operations for usage logging
├── logging_decorator.py   # Tool logging decorator for automatic tracking
├── Dockerfile             # Production container setup
├── pyproject.toml         # Python dependencies and config
├── .env                   # Environment configuration
└── scripts/
    ├── build.sh           # Docker build script
    ├── run-local.sh       # Local development script
    └── run-with-letsencrypt.sh  # Production deployment
```

### Security Features

- **OAuth 2.1 + PKCE**: Enhanced security with Proof Key for Code Exchange
- **Dynamic Client Registration**: RFC 7591 compliant client registration
- **HTTPS Enforcement**: SSL/TLS encryption for all communications
- **JWT Token Validation**: Short-lived tokens (1 hour) for secure access
- **Comprehensive OAuth Endpoints**: Authorization server and protected resource metadata
- **Input Validation**: Type checking and parameter validation
- **Error Handling**: Secure error responses without information leakage
- **Let's Encrypt Integration**: Automatic SSL certificate management

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVER_NAME` | Name for the MCP server, Docker image, and container | `mcp-template` | No |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | - | For authentication |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | - | For authentication |
| `OAUTH_REDIRECT_URI` | OAuth callback URL | - | For authentication |
| `JWT_SECRET_KEY` | Secret for JWT signing | - | For authentication |
| `SSL_ENABLED` | Enable HTTPS | `false` | No |
| `DOMAIN_NAME` | Your domain name | - | For HTTPS |
| `SSL_CERT_PATH` | SSL certificate path | - | If SSL enabled |
| `SSL_KEY_PATH` | SSL private key path | - | If SSL enabled |
| `MCP_TRANSPORT` | Transport protocol | `sse` | No |
| `MCP_HOST` | Host to bind to | `0.0.0.0` | No |
| `MCP_PORT` | Port to listen on | `8443` (HTTPS) / `8899` (HTTP) | No |
| `DATABASE_PATH` | SQLite database file path | `mcp_server.db` | No |
| `ENABLE_LOGGING` | Enable tool usage logging | `true` | No |

### OAuth 2.1 + PKCE Configuration

Authentication uses OAuth 2.1 with PKCE for enhanced security. The server provides:
- **Dynamic Client Registration** (RFC 7591): Automatic client registration
- **OAuth Authorization Server Metadata** (RFC 8414): Endpoint discovery
- **OAuth Protected Resource Metadata** (RFC 8707): Resource server information
- **PKCE Support** (RFC 7636): Protection against code interception attacks

JWT tokens include:
- User's Google ID (`sub`)
- Email address
- Display name  
- Profile picture URL
- Token expiration (1 hour)

## Development

### Local Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run black server.py oauth.py

# Type checking
uv run mypy server.py oauth.py

# Lint code
uv run flake8 server.py oauth.py
```

### Adding Custom Tools

1. Define your tool in `server.py` with automatic logging:
```python
@mcp.tool()
@logged_tool  # Add this decorator for automatic database logging
def your_tool_name(param: str) -> str:
    """Tool description for AI agents"""
    # Implement your logic
    return "result"
```

2. Add authentication checks if needed:
```python
@mcp.tool()
def protected_tool() -> str:
    """This tool requires authentication"""
    # Auth context is available in session_auth_contexts
    return "authenticated result"
```

3. Test your tool:
```bash
# Restart server to load changes
docker restart <your-server-name>

# Test via MCP client or direct HTTP calls
```

## Production Deployment

### Prerequisites

- Domain name pointing to your server
- Ports 80 (HTTP) and 8443 (HTTPS) open
- Docker installed

### Deployment Steps

1. **Configure DNS**: Point your domain to your server's IP
2. **Set environment variables**: Domain, email, OAuth credentials
3. **Run deployment script**: `./scripts/run-with-letsencrypt.sh`
4. **Verify**: Test HTTPS endpoint and authentication

### Monitoring

Check server logs:
```bash
docker logs <your-server-name>
```

Monitor certificate renewal:
```bash
# Certificates auto-renew, but you can check status
docker exec <your-server-name> ls -la /etc/letsencrypt/live/
```

### Database Usage Tracking

The template includes SQLite database integration for tracking tool usage:

**Features:**
- Automatic logging of all tool calls with user context
- Tracks execution time, arguments, and results
- User session tracking with OAuth information
- Built-in statistics tool for usage analytics

**Database Schema:**
- `users` table: OAuth user information and session tracking
- `tool_usage_logs` table: Detailed tool execution logs

**Access Database:**
```bash
# Copy database to local machine (if you have sqlite3 installed)
docker cp <your-server-name>:/app/mcp_server.db ./mcp_server_copy.db
sqlite3 mcp_server_copy.db

# Or use Python inside container to query database
# View all users:
docker exec <your-server-name> python -c "
import sqlite3
db = sqlite3.connect('mcp_server.db')
cur = db.cursor()
for row in cur.execute('SELECT * FROM users'):
    print(row)
"

# View recent tool usage:
docker exec <your-server-name> python -c "
import sqlite3
db = sqlite3.connect('mcp_server.db')
cur = db.cursor()
for row in cur.execute('SELECT tool_name, user_email, timestamp FROM tool_usage_logs ORDER BY timestamp DESC LIMIT 5'):
    print(row)
"
```

**Disable Logging:**
Set `ENABLE_LOGGING=false` in your `.env` file to disable database logging.

## Troubleshooting

### Common Issues

**SSL Certificate Errors**
- Ensure domain points to your server IP
- Check firewall allows ports 80 and 8443
- Verify Let's Encrypt rate limits aren't exceeded

**Authentication Failures**
- Verify Google OAuth credentials are correct
- Check OAuth redirect URI matches configuration
- Ensure JWT token hasn't expired (1 hour lifetime)
- Verify `Authorization: Bearer <jwt-token>` header format

**Connection Issues**
- Verify Docker container is running: `docker ps`
- Check server logs: `docker logs <your-server-name>`
- Test basic connectivity: `curl https://your-domain.com:8443/sse`

### Getting Help

1. Check server logs for specific error messages
2. Verify environment variables are set correctly
3. Test each component (SSL, auth, MCP protocol) separately
4. Review the MCP specification at [modelcontextprotocol.io](https://modelcontextprotocol.io)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

This template provides a solid foundation for building production-ready MCP servers. Customize it according to your specific needs and use cases.