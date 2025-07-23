# server.py
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Create an MCP server
mcp = FastMCP("SecretsKnower")

# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def secret_word() -> str:
    """Return the secret word"""
    return f"OVPostWebExperts"

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

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
    
    # Run with SSE transport
    if transport == "sse":
        protocol = "https" if ssl_enabled else "http"
        print(f"Starting MCP server on {protocol}://{host}:{port}/sse")
        
        # For SSE transport, we need to use uvicorn to run the ASGI app
        import uvicorn
        
        # Configure SSL if enabled
        ssl_config = {}
        if ssl_enabled:
            ssl_config = {
                "ssl_certfile": ssl_cert_path,
                "ssl_keyfile": ssl_key_path,
            }
            
        uvicorn.run(
            mcp.sse_app, 
            host=host, 
            port=port, 
            log_level="info",
            **ssl_config
        )
    else:
        # Default to stdio for local development
        print("Starting MCP server with stdio transport")
        mcp.run()
