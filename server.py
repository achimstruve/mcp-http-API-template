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


# Custom ASGI middleware for authentication
class AuthMiddleware:
    def __init__(self, app):
        self.app = app
        self.auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    
    async def __call__(self, scope, receive, send):
        if self.auth_enabled and scope["type"] == "http":
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
            
            # Store auth context for this session
            # In a real implementation, extract session ID from the request
            session_id = scope.get("path", "").split("/")[-1]  # Simple session extraction
            if session_id:
                session_auth_contexts[session_id] = auth_context
                logger.info(f"Authenticated user {auth_context.user_id} for session {session_id}")
        
        # Continue with the request
        await self.app(scope, receive, send)


# Start the server
if __name__ == "__main__":
    # Get configuration from environment variables
    transport = os.getenv("MCP_TRANSPORT", "sse")
    host = os.getenv("MCP_HOST", "0.0.0.0")  
    port = int(os.getenv("MCP_PORT", "8899"))
    
    # SSL configuration
    ssl_enabled = os.getenv("SSL_ENABLED", "false").lower() == "true"
    ssl_cert_path = os.getenv("SSL_CERT_PATH", "/etc/ssl/certs/cert.pem")
    ssl_key_path = os.getenv("SSL_KEY_PATH", "/etc/ssl/private/key.pem")
    
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
        
        # Wrap the app with auth middleware if enabled
        app = mcp.sse_app
        if auth_enabled:
            app = AuthMiddleware(app)
        
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