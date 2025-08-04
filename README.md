# MCP Server Template

A production-ready FastMCP server template with HTTPS support, authentication, and Docker deployment. This template provides a foundation for building secure, web-accessible MCP servers that can be used by Claude Code and other AI agents over HTTP/HTTPS with SSE transport.

## Features

- **🔒 OAuth Authentication**: Google OAuth 2.0 integration for secure authentication
- **🌐 HTTPS Support**: SSL/TLS encryption with Let's Encrypt integration
- **🐳 Docker Deployment**: Production-ready containerized deployment
- **⚡ FastMCP Integration**: Built on the modern FastMCP framework
- **🛡️ Security First**: JWT tokens, input validation, and security headers

### Example Tools & Resources

- **Addition tool**: Demonstrates basic tool functionality
- **Secret word tool**: Shows authenticated tool access
- **Dynamic greeting resource**: Example of parametrized resources

## Quick Start

### Prerequisites

- Python 3.10+
- Docker
- A domain name (for HTTPS deployment)

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

Claude Code natively supports SSE transport over HTTPS with OAuth. Add your MCP server:

```bash
# Add the server (OAuth flow will start automatically)
claude mcp add my-server --transport sse https://your-domain.com:8443/sse
```

When you connect, Claude Code will:
1. Detect OAuth is required
2. Open your browser for Google authentication
3. Store the token securely for future connections

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
# - greeting://John -> "Hello, John!"
```

## Architecture

### Files Structure

```
├── server.py              # Main MCP server implementation
├── oauth.py               # OAuth 2.0 authentication implementation
├── Dockerfile             # Production container setup
├── pyproject.toml         # Python dependencies and config
├── .env                   # Environment configuration
└── scripts/
    ├── build.sh           # Docker build script
    ├── run-local.sh       # Local development script
    └── run-with-letsencrypt.sh  # Production deployment
```

### Security Features

- **OAuth 2.0 Authentication**: Google OAuth integration with JWT tokens
- **HTTPS Enforcement**: SSL/TLS encryption for all communications
- **JWT Token Validation**: Short-lived tokens (1 hour) for secure access
- **PKCE Support**: Protection against authorization code interception
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

### OAuth Configuration

Authentication is handled through Google OAuth. Users authenticate with their Google account and receive a JWT token for API access. The JWT token includes:
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

1. Define your tool in `server.py`:
```python
@mcp.tool()
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