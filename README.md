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
word = secret_word()  # Returns "OVPostWebExperts"
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

## Connecting MCP Clients

### Method 1: Direct SSE Connection (Recommended for Web-Deployed Servers)

Claude Code and other MCP clients that support SSE transport can connect directly to your deployed server:

```bash
# For Claude Code
claude mcp add demo-server --transport sse https://YOUR_SERVER:8443/sse

# Example with your deployed server
claude mcp add demo-server --transport sse https://34.145.94.60:8443/sse
```

**Note**: This method requires MCP clients that support SSE transport. Claude Desktop currently only supports stdio transport for local servers.

### Method 2: Local Server Connection

For clients that only support stdio transport (like Claude Desktop):

#### Option A: Run Server Locally

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-python-testing.git
cd mcp-python-testing

# Install dependencies
uv sync

# For Claude Code
claude mcp add demo-server -- uv run python server.py

# For Claude Desktop, add to claude_desktop_config.json:
{
  "mcpServers": {
    "demo-server": {
      "command": "uv",
      "args": ["run", "python", "/path/to/server.py"]
    }
  }
}
```

#### Option B: Local Proxy to Web Server (Advanced)

Create a local proxy that bridges stdio to your web-deployed server:

1. **Create proxy.py:**
```python
#!/usr/bin/env python3
import sys
import json
import asyncio
import aiohttp
from aiohttp_sse_client import client as sse_client

SERVER_URL = "https://34.145.94.60:8443/sse"

async def stdio_to_sse_proxy():
    # Connect to SSE endpoint
    async with aiohttp.ClientSession() as session:
        async with sse_client.EventSource(
            SERVER_URL, 
            session=session,
            ssl=False  # Set to True for production with valid certs
        ) as event_source:
            
            # Handle bidirectional communication
            async def read_stdin():
                while True:
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, sys.stdin.readline
                    )
                    if not line:
                        break
                    # Send to SSE server
                    await session.post(SERVER_URL, data=line)
            
            async def read_sse():
                async for event in event_source:
                    # Forward SSE events to stdout
                    sys.stdout.write(json.dumps({
                        "event": event.type,
                        "data": event.data
                    }) + "\n")
                    sys.stdout.flush()
            
            # Run both tasks concurrently
            await asyncio.gather(read_stdin(), read_sse())

if __name__ == "__main__":
    asyncio.run(stdio_to_sse_proxy())
```

2. **Install proxy dependencies:**
```bash
pip install aiohttp aiohttp-sse-client
```

3. **Configure Claude Desktop:**
```json
{
  "mcpServers": {
    "demo-server-remote": {
      "command": "python",
      "args": ["/path/to/proxy.py"]
    }
  }
}
```

### Testing Your Connection

#### Test with MCP Inspector (Local)
```bash
npx @modelcontextprotocol/inspector "uv" "run" "python" "server.py"
```

#### Test SSE Endpoint (Web)
```bash
# Basic connectivity test
curl -k https://YOUR_SERVER:8443/sse

# Stream events (shows SSE communication)
curl -k -N https://YOUR_SERVER:8443/sse
```

### Available Tools and Resources

Once connected, you'll have access to:

**Tools:**
- `add(a, b)` - Adds two numbers
- `secret_word()` - Returns the secret word "OVPostWebExperts"

**Resources:**
- `greeting://{name}` - Returns personalized greetings

### Troubleshooting

1. **Connection timeouts**: Ensure firewall rules allow port 8443
2. **SSL certificate warnings**: Expected with self-signed certificates
3. **"Transport not supported"**: Client doesn't support SSE; use local mode
4. **Authentication errors**: This template doesn't include auth; add as needed

## Development

To contribute to this project:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[MIT](LICENSE)
