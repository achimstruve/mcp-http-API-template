# server.py
import os
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from typing import Optional
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import authentication
from auth import get_auth_context, require_auth, AuthContext

# Create an MCP server
mcp = FastMCP("SecretsKnower")



# MCP Tools
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
def secret_word() -> str:
    """Return the secret word"""
    return "OVPostWebExperts"


# MCP Resources
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Simple ASGI auth wrapper
class AuthWrapper:
    def __init__(self, app):
        self.app = app
        self.auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and self.auth_enabled:
            # Extract authorization header
            headers = dict(scope.get("headers", []))
            authorization = headers.get(b"authorization", b"").decode("utf-8")
            
            # Validate authentication
            auth_context = get_auth_context(authorization)
            
            if not auth_context:
                # Send 401 Unauthorized
                await send({
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": json.dumps({"error": "Unauthorized"}).encode(),
                })
                return
            
            logger.info(f"Authenticated user {auth_context.user_id}")
        
        # Call the wrapped app
        await self.app(scope, receive, send)


# Start the server
if __name__ == "__main__":
    # Configuration
    host = os.getenv("MCP_HOST", "0.0.0.0")
    ssl_enabled = os.getenv("SSL_ENABLED", "false").lower() == "true"
    default_port = "8443" if ssl_enabled else "8899"
    port = int(os.getenv("MCP_PORT", default_port))
    auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    
    # SSL configuration
    ssl_cert_path = os.getenv("SSL_CERT_PATH", "/etc/ssl/certs/cert.pem")
    ssl_key_path = os.getenv("SSL_KEY_PATH", "/etc/ssl/private/key.pem")
    
    # Check SSL certificates
    if ssl_enabled:
        import os.path
        if not (os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path)):
            print(f"Warning: SSL enabled but certificates not found. Falling back to HTTP.")
            print(f"  Cert path: {ssl_cert_path}")
            print(f"  Key path: {ssl_key_path}")
            ssl_enabled = False
    
    # Start server
    protocol = "https" if ssl_enabled else "http"
    print(f"Starting MCP server on {protocol}://{host}:{port}/sse")
    
    if auth_enabled:
        print("Authentication: ENABLED")
        api_keys = os.getenv("API_KEYS", "")
        if api_keys:
            print(f"Loaded {len(api_keys.split(','))} API key(s)")
        else:
            print("Warning: Using default demo API key")
    else:
        print("Authentication: DISABLED")
    
    import uvicorn
    
    # Configure app with optional auth wrapper
    app = AuthWrapper(mcp.sse_app()) if auth_enabled else mcp.sse_app()
    
    # Configure SSL
    ssl_config = {}
    if ssl_enabled:
        ssl_config = {
            "ssl_certfile": ssl_cert_path,
            "ssl_keyfile": ssl_key_path,
        }
    
    uvicorn.run(app, host=host, port=port, log_level="info", **ssl_config)