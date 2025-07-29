# MCP Server Template

A production-ready FastMCP server template with HTTPS support, authentication, and Docker deployment. This template provides a foundation for building secure, web-accessible MCP servers that can be used by AI agents over HTTP/HTTPS.

## Features

- **🔒 Authentication**: API key-based authentication with user context
- **🌐 HTTPS Support**: SSL/TLS encryption with Let's Encrypt integration
- **🐳 Docker Deployment**: Production-ready containerized deployment
- **⚡ FastMCP Integration**: Built on the modern FastMCP framework
- **🛡️ Security First**: Input validation, proper error handling, and security headers

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

### 2. Configure Environment

Create a `.env` file:

```bash
# Authentication
AUTH_ENABLED=true
API_KEYS="user1:your-secure-api-key-here"

# SSL/HTTPS (for production)
SSL_ENABLED=true
DOMAIN_NAME=your-domain.com
SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem

# Server Configuration
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8443
```

### 3. Deploy

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
export AUTH_ENABLED=true
export API_KEYS="admin:your-secure-api-key"
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
   - Set your domain name and API keys
   - Customize authentication logic in `auth.py` if needed

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

### Claude Code

Add your MCP server to Claude Code:

```bash
# With authentication
claude mcp add my-server --transport sse https://your-domain.com:8443/sse \
  --header "Authorization: Bearer your-api-key"

# Without authentication (development only)
claude mcp add my-server --transport sse https://your-domain.com:8443/sse
```

### Other MCP Clients

Configure your MCP client with:
- **Transport**: `sse` (Server-Sent Events)
- **URL**: `https://your-domain.com:8443/sse`
- **Authentication**: `Authorization: Bearer your-api-key` header

### Testing Your Server

```bash
# Test connectivity
curl https://your-domain.com:8443/sse

# Test with authentication
curl -H "Authorization: Bearer your-api-key" https://your-domain.com:8443/sse

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
├── auth.py                # Authentication middleware
├── Dockerfile             # Production container setup
├── pyproject.toml         # Python dependencies and config
├── .env                   # Environment configuration
└── scripts/
    ├── build.sh           # Docker build script
    ├── run-local.sh       # Local development script
    └── run-with-letsencrypt.sh  # Production deployment
```

### Security Features

- **API Key Authentication**: User-based access control
- **HTTPS Enforcement**: SSL/TLS encryption for all communications
- **Input Validation**: Type checking and parameter validation
- **Error Handling**: Secure error responses without information leakage
- **Let's Encrypt Integration**: Automatic SSL certificate management

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AUTH_ENABLED` | Enable API key authentication | `false` | No |
| `API_KEYS` | API keys in format `"user1:key1,user2:key2"` | - | If auth enabled |
| `SSL_ENABLED` | Enable HTTPS | `false` | No |
| `DOMAIN_NAME` | Your domain name | - | For HTTPS |
| `SSL_CERT_PATH` | SSL certificate path | - | If SSL enabled |
| `SSL_KEY_PATH` | SSL private key path | - | If SSL enabled |
| `MCP_TRANSPORT` | Transport protocol | `sse` | No |
| `MCP_HOST` | Host to bind to | `0.0.0.0` | No |
| `MCP_PORT` | Port to listen on | `8443` (HTTPS) / `8899` (HTTP) | No |

### API Key Format

API keys should be provided in the format: `username:api-key`

Example:
```bash
API_KEYS="admin:sk-admin-key-123,user1:sk-user1-key-456"
```

## Development

### Local Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run black server.py auth.py

# Type checking
uv run mypy server.py auth.py

# Lint code
uv run flake8 server.py auth.py
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
docker restart mcp-server-web

# Test via MCP client or direct HTTP calls
```

## Production Deployment

### Prerequisites

- Domain name pointing to your server
- Ports 80 (HTTP) and 8443 (HTTPS) open
- Docker installed

### Deployment Steps

1. **Configure DNS**: Point your domain to your server's IP
2. **Set environment variables**: Domain, email, API keys
3. **Run deployment script**: `./scripts/run-with-letsencrypt.sh`
4. **Verify**: Test HTTPS endpoint and authentication

### Monitoring

Check server logs:
```bash
docker logs mcp-server-web
```

Monitor certificate renewal:
```bash
# Certificates auto-renew, but you can check status
docker exec mcp-server-web ls -la /etc/letsencrypt/live/
```

## Troubleshooting

### Common Issues

**SSL Certificate Errors**
- Ensure domain points to your server IP
- Check firewall allows ports 80 and 8443
- Verify Let's Encrypt rate limits aren't exceeded

**Authentication Failures**
- Check API key format: `username:key`
- Verify `AUTH_ENABLED=true` in environment
- Ensure `Authorization: Bearer key` header format

**Connection Issues**
- Verify Docker container is running: `docker ps`
- Check server logs: `docker logs mcp-server-web`
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