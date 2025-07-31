"""
OAuth 2.0 implementation for MCP server using Google as the authentication provider.
"""
import os
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from urllib.parse import urlencode, urlparse

import jwt
import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, HTMLResponse
from authlib.integrations.httpx_client import AsyncOAuth2Client

logger = logging.getLogger(__name__)

# OAuth configuration
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 1

# Cache for Google's discovery document
_google_config_cache = None


async def get_google_config():
    """Fetch Google's OpenID configuration."""
    global _google_config_cache
    if _google_config_cache:
        return _google_config_cache
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(GOOGLE_DISCOVERY_URL)
            response.raise_for_status()
            _google_config_cache = response.json()
            return _google_config_cache
    except Exception as e:
        logger.error(f"Failed to fetch Google discovery document: {e}")
        raise


def create_jwt_token(user_info: Dict[str, Any]) -> str:
    """Create a JWT token for MCP access."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_info.get("sub"),  # Google user ID
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "picture": user_info.get("picture"),
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def validate_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate a JWT token and return the payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


def get_server_base_url(request: Request) -> str:
    """Get the base URL of the server from the request."""
    scheme = request.url.scheme
    host = request.headers.get("host", request.url.hostname)
    return f"{scheme}://{host}"


async def oauth_metadata(request: Request):
    """OAuth Authorization Server Metadata endpoint (RFC 8414)."""
    base_url = get_server_base_url(request)
    
    metadata = {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],  # Public client
        "scopes_supported": ["openid", "email", "profile"],
    }
    
    return JSONResponse(metadata)


async def authorize(request: Request):
    """OAuth authorization endpoint - redirects to Google."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return JSONResponse(
            {"error": "OAuth not configured - missing Google credentials"},
            status_code=500
        )
    
    if not OAUTH_REDIRECT_URI:
        return JSONResponse(
            {"error": "OAuth not configured - missing redirect URI"},
            status_code=500
        )
    
    # Get Google's authorization endpoint
    google_config = await get_google_config()
    auth_endpoint = google_config["authorization_endpoint"]
    
    # Build authorization URL
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": OAUTH_REDIRECT_URI,
        "state": request.query_params.get("state", ""),
        "access_type": "online",
        "prompt": "select_account"
    }
    
    # Support PKCE if provided
    code_challenge = request.query_params.get("code_challenge")
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = request.query_params.get("code_challenge_method", "S256")
    
    auth_url = f"{auth_endpoint}?{urlencode(params)}"
    return RedirectResponse(auth_url)


async def callback(request: Request):
    """OAuth callback endpoint - handles Google's response."""
    code = request.query_params.get("code")
    state = request.query_params.get("state", "")
    
    if not code:
        error = request.query_params.get("error", "Unknown error")
        return JSONResponse(
            {"error": f"OAuth callback error: {error}"},
            status_code=400
        )
    
    # Exchange code for tokens with Google
    google_config = await get_google_config()
    token_endpoint = google_config["token_endpoint"]
    
    client = AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=OAUTH_REDIRECT_URI
    )
    
    try:
        token = await client.fetch_token(
            token_endpoint,
            code=code,
            grant_type="authorization_code"
        )
        
        # Get user info from Google
        userinfo_endpoint = google_config["userinfo_endpoint"]
        client.token = token
        
        resp = await client.get(userinfo_endpoint)
        user_info = resp.json()
        
        # Create our JWT token
        jwt_token = create_jwt_token(user_info)
        
        # Return success page with token
        html = f"""
        <html>
        <head>
            <title>OAuth Success</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .container {{ max-width: 600px; margin: auto; text-align: center; }}
                .token {{ background: #f0f0f0; padding: 20px; border-radius: 5px; word-break: break-all; }}
                .success {{ color: green; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="success">Authentication Successful!</h1>
                <p>You have been authenticated as: <strong>{user_info.get('email', 'Unknown')}</strong></p>
                <p>Use this token to connect to the MCP server:</p>
                <div class="token">{jwt_token}</div>
                <p><small>This token expires in {JWT_EXPIRY_HOURS} hour(s)</small></p>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(html)
        
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        return JSONResponse(
            {"error": "Token exchange failed"},
            status_code=400
        )


async def token(request: Request):
    """OAuth token endpoint for public clients."""
    try:
        form = await request.form()
        grant_type = form.get("grant_type")
        code = form.get("code")
        
        if grant_type != "authorization_code" or not code:
            return JSONResponse(
                {"error": "invalid_request"},
                status_code=400
            )
        
        # For simplicity, we redirect token requests through our callback
        # In a real implementation, this would exchange the code directly
        return JSONResponse(
            {"error": "Use the callback endpoint for token exchange"},
            status_code=400
        )
        
    except Exception as e:
        logger.error(f"Token endpoint error: {e}")
        return JSONResponse(
            {"error": "server_error"},
            status_code=500
        )


def extract_bearer_token(authorization: str) -> Optional[str]:
    """Extract Bearer token from Authorization header."""
    if not authorization:
        return None
    
    if authorization.startswith("Bearer "):
        return authorization[7:]
    
    return None


def validate_request(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    """Validate the authorization header and return user info."""
    if not authorization:
        return None
    
    token = extract_bearer_token(authorization)
    if not token:
        return None
    
    return validate_jwt_token(token)


