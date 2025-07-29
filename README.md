# MCP Demo Server - Web Version

This is a demonstration of a FastMCP server deployed as a web service with HTTPS support, providing simple API tools and resources accessible to AI agents over HTTP/HTTPS.

## Features

- **Addition tool**: Adds two numbers together
- **Secret word tool**: Returns a predefined secret word
- **Dynamic greeting resource**: Provides personalized greetings
- **HTTPS support**: Secure communication with SSL/TLS encryption
- **Optional authentication**: API key-based authentication for production use

## Prerequisites

- Python 3.10+
- uv (Ultra-fast Python package installer and resolver)
- Docker (for containerized deployment)
- Google Cloud SDK (for GCP deployment)

## Installation

1. Install uv if you haven't already:
   ```bash
   pip install uv
   ```

2. Clone the repository and navigate into it:
   ```bash
   git clone https://github.com/your-username/mcp-python-testing.git
   cd mcp-python-testing
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

## Web Deployment

This MCP server is designed to run as a web service accessible over HTTPS.

### Environment Variables

- `MCP_TRANSPORT`: Set to `sse` for web deployment
- `MCP_HOST`: Host to bind to (default: `0.0.0.0`)
- `MCP_PORT`: Port to listen on (default: `8443` for HTTPS)
- `SSL_ENABLED`: Enable HTTPS (default: `true`)
- `SSL_CERT_PATH`: Path to SSL certificate
- `SSL_KEY_PATH`: Path to SSL private key
- `DOMAIN_NAME`: Your domain name for automatic Let's Encrypt certificates
- `AUTH_ENABLED`: Enable API key authentication (default: `false`)
- `API_KEYS`: API keys in format `"user1:key1,user2:key2"`

### Local Testing with Docker

1. **Build the Docker image:**
   ```bash
   ./scripts/build.sh
   ```

2. **Run locally:**
   ```bash
   ./scripts/run-local.sh
   ```
   
   The server will be available at `http://localhost:8899/sse`

### Production Deployment on GCP

1. **Set up GCP:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud services enable containerregistry.googleapis.com
   ```

2. **Deploy with HTTPS:**
   ```bash
   export GCP_PROJECT_ID=your-project-id
   export DOMAIN_NAME=your-domain.com
   export SSL_EMAIL=admin@your-domain.com
   ./scripts/deploy-gcp.sh
   ```

3. **Access the server:**
   - HTTPS: `https://your-domain.com:8443/sse`

### Using Let's Encrypt for SSL Certificates

The server includes automatic Let's Encrypt certificate generation:

```bash
./scripts/run-with-letsencrypt.sh
```

This script will:
- Generate SSL certificates for your domain
- Configure the server to use HTTPS
- Automatically renew certificates

## Connecting to the Server

### Using Claude Code

Connect to the deployed MCP server:

```bash
# Without authentication
claude mcp add demo-server-web --transport sse https://your-domain.com:8443/sse

# With authentication
claude mcp add demo-server-web --transport sse https://your-domain.com:8443/sse \
  --header "Authorization: Bearer your-api-key"
```

### Testing the Connection

```bash
# Test SSE endpoint
curl https://your-domain.com:8443/sse

# Test with authentication
curl -H "Authorization: Bearer your-api-key" https://your-domain.com:8443/sse
```

## API Reference

### Tools

#### add(a: int, b: int) -> int
Adds two numbers together and returns the result.

Example:
```python
result = add(5, 7)  # Returns 12
```

#### secret_word() -> str
Returns the secret word.

Example:
```python
word = secret_word()  # Returns "OVPostWebExperts"
```

### Resources

#### greeting://{name}
Returns a personalized greeting for the provided name.

Example: `greeting://John` returns "Hello, John!"

## Authentication

### Enabling Authentication

1. Set environment variables:
   ```bash
   export AUTH_ENABLED=true
   export API_KEYS="user1:secret-key-1,user2:secret-key-2"
   ```

2. Deploy with authentication:
   ```bash
   ./scripts/deploy-gcp.sh
   ```

### Authentication Flow

1. Client sends Authorization header: `Authorization: Bearer your-api-key`
2. Server validates API key and creates user context
3. Tools can access user information for permission checks

## Security Best Practices

- **Always use HTTPS** in production with valid SSL certificates
- **Enable authentication** for production deployments
- **Implement rate limiting** for API endpoints
- **Use firewall rules** to restrict access if needed
- **Monitor logs** for security events

## Development Commands

### Code Quality
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

### Local Development
```bash
# Run in web mode locally
MCP_TRANSPORT=sse uv run python server.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector "uv" "run" "python" "server.py"
```

## Troubleshooting

- **Connection timeouts**: Ensure firewall rules allow port 8443
- **SSL certificate warnings**: Use valid certificates from Let's Encrypt
- **Authentication errors**: Check API key format and AUTH_ENABLED setting
- **"Transport not supported"**: Ensure client supports SSE transport

## License

[MIT](LICENSE)