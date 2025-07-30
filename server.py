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

# Store auth contexts per session (in production, use proper session management)
session_auth_contexts: dict[str, AuthContext] = {}


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    # Example of checking auth context if needed
    # In a real implementation, you'd get the session ID from the request context
    return a + b


@mcp.tool()
def secret_word() -> str:
    """Return the secret word"""
    # This could check permissions based on auth context
    return f"OVPostWebExperts"


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    # Could personalize based on authenticated user
    return f"Hello, {name}!"


# Simple ASGI auth wrapper with OAuth metadata support
class AuthWrapper:
    def __init__(self, app):
        self.app = app
        self.auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            
            # Handle OAuth metadata endpoints for mcp-remote compatibility (NO AUTH REQUIRED)
            if path in ["/.well-known/oauth-authorization-server", "/.well-known/oauth-protected-resource"]:
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]],
                })
                # Get host from Host header or default
                headers = dict(scope.get("headers", []))
                host = headers.get(b"host", b"localhost").decode("utf-8")
                
                # Minimal OAuth metadata to satisfy mcp-remote
                if path == "/.well-known/oauth-authorization-server":
                    metadata = {
                        "issuer": f"https://{host}",
                        "authorization_endpoint": "https://not-used",
                        "token_endpoint": "https://not-used",
                        "response_types_supported": ["token"],
                        "grant_types_supported": ["client_credentials"],
                        "token_endpoint_auth_methods_supported": ["none"]
                    }
                else:  # oauth-protected-resource
                    metadata = {
                        "resource": f"https://{host}/sse",
                        "authorization_servers": [f"https://{host}"],
                        "scopes_supported": ["read", "write"],
                        "bearer_methods_supported": ["header"]
                    }
                
                await send({
                    "type": "http.response.body",
                    "body": json.dumps(metadata).encode(),
                })
                return
            
            # Regular auth check for other endpoints
            if self.auth_enabled:
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
        
        # Call the wrapped app correctly
        await self.app(scope, receive, send)


# Start the server
if __name__ == "__main__":
    # Get configuration from environment variables
    transport = os.getenv("MCP_TRANSPORT", "sse")
    host = os.getenv("MCP_HOST", "0.0.0.0")  
    # Default port based on SSL configuration
    default_port = "8443" if os.getenv("SSL_ENABLED", "false").lower() == "true" else "8899"
    port = int(os.getenv("MCP_PORT", default_port))
    
    # SSL configuration
    ssl_enabled = os.getenv("SSL_ENABLED", "false").lower() == "true"
    ssl_cert_path = os.getenv("SSL_CERT_PATH", "/etc/ssl/certs/cert.pem")
    ssl_key_path = os.getenv("SSL_KEY_PATH", "/etc/ssl/private/key.pem")
    
    # Check if SSL certificates exist and are readable
    if ssl_enabled:
        import os.path
        if not (os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path)):
            print(f"Warning: SSL enabled but certificates not found. Falling back to HTTP.")
            print(f"  Cert path: {ssl_cert_path}")
            print(f"  Key path: {ssl_key_path}")
            ssl_enabled = False
    
    # Authentication configuration
    auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    
    # Run with SSE transport
    if transport == "sse":
        protocol = "https" if ssl_enabled else "http"
        print(f"Starting MCP server on {protocol}://{host}:{port}/sse")
        if auth_enabled:
            print("Authentication is ENABLED")
            api_keys = os.getenv("API_KEYS", "")
            if api_keys:
                print(f"Loaded {len(api_keys.split(','))} API key(s)")
            else:
                print("Warning: Using default demo API key")
        else:
            print("Authentication is DISABLED")
        
        # For SSE transport, we need to use uvicorn to run the ASGI app
        import uvicorn
        
        # Get the base ASGI app and wrap with auth if needed
        if auth_enabled:
            app = AuthWrapper(mcp.sse_app())  # Call method to get ASGI app
        else:
            app = mcp.sse_app()  # Call method to get ASGI app
        
        # Configure SSL if enabled
        ssl_config = {}
        if ssl_enabled:
            ssl_config = {
                "ssl_certfile": ssl_cert_path,
                "ssl_keyfile": ssl_key_path,
            }
            
        uvicorn.run(
            app, 
            host=host, 
            port=port, 
            log_level="info",
            **ssl_config
        )
    else:
        # Default to stdio for local development
        print("Starting MCP server with stdio transport")
        mcp.run()