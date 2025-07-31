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

# Import OAuth authentication
from oauth import (
    oauth_metadata, authorize, callback, token,
    validate_request, GOOGLE_CLIENT_ID
)
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

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


# OAuth-aware auth wrapper
class OAuthWrapper:
    def __init__(self, app):
        self.app = app
        self.auth_enabled = bool(GOOGLE_CLIENT_ID)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and self.auth_enabled:
            path = scope.get("path", "")
            
            # Skip auth for OAuth endpoints
            if path in ["/.well-known/oauth-authorization-server", "/authorize", "/callback", "/token"]:
                await self.app(scope, receive, send)
                return
            
            # Extract authorization header
            headers = dict(scope.get("headers", []))
            authorization = headers.get(b"authorization", b"").decode("utf-8")
            
            # Validate JWT token
            user_info = validate_request(authorization)
            
            if not user_info:
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
            
            logger.info(f"Authenticated user {user_info.get('email')}")
            
            # Store user info in scope for downstream use
            scope["user"] = user_info
        
        # Call the wrapped app
        await self.app(scope, receive, send)


# Start the server
if __name__ == "__main__":
    # Configuration
    host = os.getenv("MCP_HOST", "0.0.0.0")
    ssl_enabled = os.getenv("SSL_ENABLED", "false").lower() == "true"
    default_port = "8443" if ssl_enabled else "8899"
    port = int(os.getenv("MCP_PORT", default_port))
    auth_enabled = bool(GOOGLE_CLIENT_ID)
    
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
        print("Authentication: ENABLED (OAuth with Google)")
        print(f"OAuth redirect URI: {os.getenv('OAUTH_REDIRECT_URI', 'Not configured')}")
    else:
        print("Authentication: DISABLED")
        print("Warning: GOOGLE_CLIENT_ID not configured")
    
    import uvicorn
    
    # Create OAuth routes
    oauth_routes = [
        Route("/.well-known/oauth-authorization-server", oauth_metadata, methods=["GET"]),
        Route("/authorize", authorize, methods=["GET"]),
        Route("/callback", callback, methods=["GET"]),
        Route("/token", token, methods=["POST"]),
    ]
    
    # Create main app with OAuth endpoints
    mcp_app = mcp.sse_app()
    
    # Combine OAuth routes with MCP app
    routes = oauth_routes + [Mount("/", app=mcp_app)]
    
    # Create Starlette app with session middleware
    app = Starlette(
        routes=routes,
        middleware=[
            Middleware(SessionMiddleware, secret_key=os.getenv("JWT_SECRET_KEY", "change-this"))
        ]
    )
    
    # Wrap with OAuth authentication if enabled
    if auth_enabled:
        app = OAuthWrapper(app)
    
    # Configure SSL
    ssl_config = {}
    if ssl_enabled:
        ssl_config = {
            "ssl_certfile": ssl_cert_path,
            "ssl_keyfile": ssl_key_path,
        }
    
    uvicorn.run(app, host=host, port=port, log_level="info", **ssl_config)