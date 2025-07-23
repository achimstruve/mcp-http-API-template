# MCP Demo Server

This is a demonstration of a FastMCP server that provides simple API tools and resources.

## Features

- Addition tool: Adds two numbers together
- Secret word tool: Returns a predefined secret word
- Dynamic greeting resource: Provides personalized greetings

## Getting Started

### Prerequisites

- Python 3.10+
- uv (Ultra-fast Python package installer and resolver)

### Installation

1. Install uv if you haven't already:
   ```
   pip install uv
   ```

2. Clone or create your project directory and navigate into it:
   ```
   mkdir mcp-demo-server
   cd mcp-demo-server
   ```

3. Install dependencies using uv:
   ```
   uv sync
   ```

   This will create a virtual environment and install all dependencies defined in `pyproject.toml`.

### Running the Server

To start the server directly:
```
uv run python server.py
```

To test with MCP Inspector:
```
npx @modelcontextprotocol/inspector "uv" "run" "python" "server.py"
```

### Local Development

For local development and testing:

```bash
# Run the server in stdio mode (default)
uv run python server.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector "uv" "run" "python" "server.py"
```

## API Reference

### Tools

#### add(a: int, b: int) -> int

Adds two numbers together and returns the result.

Example usage:
```python
result = add(5, 7)  # Returns 12
```

#### secret_word() -> str

Returns the secret word.

Example usage:
```python
word = secret_word()  # Returns "ApplesAreRed998"
```

### Resources

#### greeting://{name}

Returns a personalized greeting for the provided name.

Example: `greeting://John` returns "Hello, John!"

## Web Deployment

This MCP server can be deployed as a web service accessible to AI agents over HTTP.

### Environment Variables

Configure the server using these environment variables:
- `MCP_TRANSPORT`: Transport type (`stdio` for local, `sse` for web)
- `MCP_HOST`: Host to bind to (default: `0.0.0.0`)
- `MCP_PORT`: Port to listen on (default: `8899` for HTTP, `8443` for HTTPS)

**SSL/HTTPS Configuration:**
- `SSL_ENABLED`: Enable HTTPS (`false` by default)
- `SSL_CERT_PATH`: Path to SSL certificate (default: `/etc/ssl/certs/cert.pem`)
- `SSL_KEY_PATH`: Path to SSL private key (default: `/etc/ssl/private/key.pem`)
- `DOMAIN_NAME`: Your domain name for automatic Let's Encrypt certificates

### Docker Deployment

1. **Build the Docker image:**
   ```bash
   ./scripts/build.sh
   ```

2. **Run locally with Docker:**
   ```bash
   ./scripts/run-local.sh
   ```
   The server will be available at `http://localhost:8899/sse`

### GCP VM Deployment

1. **Prerequisites:**
   - Install [gcloud CLI](https://cloud.google.com/sdk/docs/install)
   - Authenticate: `gcloud auth login`
   - Set project: `gcloud config set project YOUR_PROJECT_ID`
   - Enable Container Registry: `gcloud services enable containerregistry.googleapis.com`

2. **Deploy to GCP:**
   
   **HTTP deployment:**
   ```bash
   export GCP_PROJECT_ID=your-project-id
   ./scripts/deploy-gcp.sh
   ```
   
   **HTTPS deployment with Let's Encrypt (recommended):**
   ```bash
   export GCP_PROJECT_ID=your-project-id
   export DOMAIN_NAME=your-domain.com
   export SSL_EMAIL=admin@your-domain.com
   ./scripts/deploy-gcp.sh
   ```
   
   **HTTPS with self-signed certificate (testing only):**
   ```bash
   export GCP_PROJECT_ID=your-project-id
   export USE_SELF_SIGNED=true
   ./scripts/deploy-gcp.sh
   ```

3. **Access the server:**
   - **HTTP**: `http://EXTERNAL_IP:8899/sse`
   - **HTTPS with domain**: `https://your-domain.com:8443/sse`
   - **HTTPS with IP** (self-signed): `https://EXTERNAL_IP:8443/sse` ⚠️ Browser warnings

### Testing the Web API

Test the deployed server:
```bash
# Test SSE endpoint (HTTP)
curl http://YOUR_SERVER:8899/sse

# Test SSE endpoint (HTTPS)
curl https://your-domain.com:8443/sse

# The endpoint streams Server-Sent Events for MCP communication
```

### Security Considerations

⚠️ **Important**: For production use, consider additional security measures:
- **HTTPS**: Use the built-in SSL support with domain names
- **Authentication**: Add authentication middleware (OAuth2, JWT, API keys)
- **Rate limiting**: Implement rate limiting for API endpoints
- **Firewall**: Restrict access to specific IP ranges if needed
- **Monitoring**: Add logging and monitoring for security events

## Development

To contribute to this project:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[MIT](LICENSE)
