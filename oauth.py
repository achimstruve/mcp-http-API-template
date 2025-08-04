"""
OAuth 2.0 implementation for MCP server using Google as the authentication provider.
"""

import os
import json
import logging
import hashlib
import base64
import secrets
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

# In-memory storage for OAuth flow state (in production, use Redis or database)
_oauth_state_storage = {}
_authorization_codes = {}
_registered_clients = {}


def generate_code_verifier() -> str:
    """Generate a PKCE code verifier."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")


def generate_code_challenge(code_verifier: str) -> str:
    """Generate a PKCE code challenge from verifier."""
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def verify_code_challenge(code_verifier: str, code_challenge: str) -> bool:
    """Verify PKCE code verifier against challenge."""
    expected_challenge = generate_code_challenge(code_verifier)
    return expected_challenge == code_challenge


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
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
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


async def oauth_metadata(request: Request) -> JSONResponse:
    """OAuth Authorization Server Metadata endpoint (RFC 8414)."""
    base_url = get_server_base_url(request)

    metadata = {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],  # Public client
        "scopes_supported": ["openid", "email", "profile"],
        "pkce_required": True,
        "authorization_code_lifetime": 600,  # 10 minutes
        "registration_endpoint_auth_methods_supported": ["none"],
        "client_registration_types_supported": ["automatic"],
    }

    return JSONResponse(metadata)


async def oauth_protected_resource(request: Request) -> JSONResponse:
    """OAuth Protected Resource metadata endpoint (RFC 8707)."""
    base_url = get_server_base_url(request)

    metadata = {
        "resource": f"{base_url}/sse",
        "authorization_servers": [base_url],
        "scopes_supported": ["openid", "email", "profile"],
        "bearer_methods_supported": ["header"],
        "resource_documentation": f"{base_url}/sse",
    }

    return JSONResponse(metadata)


async def register(request: Request) -> JSONResponse:
    """Dynamic Client Registration endpoint (RFC 7591)."""
    try:
        # Parse registration request
        if request.method == "POST":
            registration_request = await request.json()
        else:
            # For GET requests, return registration information
            base_url = get_server_base_url(request)
            return JSONResponse(
                {
                    "registration_endpoint": f"{base_url}/register",
                    "registration_endpoint_auth_methods_supported": ["none"],
                    "client_registration_types_supported": ["automatic"],
                }
            )

        # Extract client metadata from request
        redirect_uris = registration_request.get("redirect_uris", [])
        client_name = registration_request.get("client_name", "Claude Code Client")
        grant_types = registration_request.get("grant_types", ["authorization_code"])
        response_types = registration_request.get("response_types", ["code"])

        # Validate the registration request
        if not redirect_uris:
            return JSONResponse(
                {
                    "error": "invalid_redirect_uri",
                    "error_description": "redirect_uris is required",
                },
                status_code=400,
            )

        if "authorization_code" not in grant_types:
            return JSONResponse(
                {
                    "error": "invalid_client_metadata",
                    "error_description": "authorization_code grant type is required",
                },
                status_code=400,
            )

        # Generate a unique client ID for this registration
        client_id = f"dynamic-{secrets.token_urlsafe(16)}"

        # Store client registration info
        client_info = {
            "client_id": client_id,
            "client_name": client_name,
            "redirect_uris": redirect_uris,
            "grant_types": grant_types,
            "response_types": response_types,
            "token_endpoint_auth_method": "none",
            "application_type": "native",
            "client_id_issued_at": int(datetime.now(timezone.utc).timestamp()),
            "scope": "openid email profile",
        }

        _registered_clients[client_id] = client_info

        logger.info(
            f"Registered dynamic client: {client_name} (ID: {client_id}) with redirect URIs: {redirect_uris}"
        )

        return JSONResponse(client_info, status_code=201)

    except Exception as e:
        logger.error(f"Client registration error: {e}")
        return JSONResponse(
            {"error": "server_error", "error_description": str(e)}, status_code=500
        )


async def authorize(request: Request) -> RedirectResponse:
    """OAuth authorization endpoint - redirects to Google."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return JSONResponse(
            {"error": "OAuth not configured - missing Google credentials"},
            status_code=500,
        )

    # Get parameters
    client_id = request.query_params.get("client_id")
    redirect_uri = request.query_params.get("redirect_uri")
    state = request.query_params.get("state", "")
    code_challenge = request.query_params.get("code_challenge")
    code_challenge_method = request.query_params.get("code_challenge_method", "S256")

    # Validate client_id
    if not client_id:
        return JSONResponse(
            {"error": "invalid_request", "error_description": "Missing client_id"},
            status_code=400,
        )

    # For dynamic clients, validate against registered clients
    if client_id.startswith("dynamic-"):
        client_info = _registered_clients.get(client_id)
        if not client_info:
            return JSONResponse(
                {"error": "invalid_client", "error_description": "Unknown client_id"},
                status_code=400,
            )

        # Validate redirect_uri
        if redirect_uri not in client_info["redirect_uris"]:
            return JSONResponse(
                {
                    "error": "invalid_request",
                    "error_description": "Invalid redirect_uri",
                },
                status_code=400,
            )

        # Use the dynamic client's redirect URI
        callback_redirect_uri = redirect_uri
    else:
        # Fall back to configured redirect URI for non-dynamic clients
        callback_redirect_uri = OAUTH_REDIRECT_URI or redirect_uri

    # Store PKCE challenge info and client info if provided (for Claude Code OAuth flow)
    if state and code_challenge:
        _oauth_state_storage[state] = {
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "client_id": client_id,
            "redirect_uri": callback_redirect_uri,
            "created_at": datetime.now(timezone.utc),
        }

    # Get Google's authorization endpoint
    google_config = await get_google_config()
    auth_endpoint = google_config["authorization_endpoint"]

    # Build authorization URL - always use our server's callback for Google
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": OAUTH_REDIRECT_URI,  # Always use server callback for Google
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }

    # Support PKCE if provided - forward Claude Code's PKCE to Google
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = code_challenge_method

    auth_url = f"{auth_endpoint}?{urlencode(params)}"
    return RedirectResponse(auth_url)


async def callback(request: Request) -> JSONResponse | HTMLResponse:
    """OAuth callback endpoint - handles Google's response."""
    code = request.query_params.get("code")
    state = request.query_params.get("state", "")

    if not code:
        error = request.query_params.get("error", "Unknown error")
        return JSONResponse(
            {"error": f"OAuth callback error: {error}"}, status_code=400
        )

    # Check if this is from Claude Code (has state parameter) or direct browser access
    if state and state in _oauth_state_storage:
        # This is from Claude Code - redirect back to the client's callback URL
        oauth_state = _oauth_state_storage.get(state)
        if oauth_state:
            client_redirect_uri = oauth_state.get("redirect_uri")

            # Store authorization code with associated PKCE challenge and client info
            auth_code_data = {
                "code": code,
                "code_challenge": oauth_state.get("code_challenge"),
                "code_challenge_method": oauth_state.get("code_challenge_method"),
                "client_id": oauth_state.get("client_id"),
                "created_at": datetime.now(timezone.utc),
                "used": False,
            }
            _authorization_codes[code] = auth_code_data

            # Clean up state
            del _oauth_state_storage[state]

            # If this is a dynamic client, redirect back to Claude Code's callback URL
            if client_redirect_uri and client_redirect_uri.startswith(
                "http://localhost"
            ):
                redirect_params = {"code": code, "state": state}
                redirect_url = f"{client_redirect_uri}?{urlencode(redirect_params)}"
                return RedirectResponse(redirect_url)
            else:
                return JSONResponse(
                    {
                        "message": "Authorization code received. Use the token endpoint to exchange for access token."
                    }
                )

    # Direct browser access - exchange code immediately and show token
    # Exchange code for tokens with Google
    google_config = await get_google_config()
    token_endpoint = google_config["token_endpoint"]

    client = AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=OAUTH_REDIRECT_URI,
    )

    try:
        token = await client.fetch_token(
            token_endpoint, code=code, grant_type="authorization_code"
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
        return JSONResponse({"error": "Token exchange failed"}, status_code=400)


async def token(request: Request) -> JSONResponse:
    """OAuth token endpoint for public clients with PKCE."""
    try:
        form = await request.form()
        grant_type = str(form.get("grant_type", ""))
        code = str(form.get("code", ""))
        code_verifier = str(form.get("code_verifier", ""))
        client_id = str(form.get("client_id", ""))

        # Validate request parameters
        if grant_type != "authorization_code":
            return JSONResponse(
                {
                    "error": "unsupported_grant_type",
                    "error_description": "Grant type must be authorization_code",
                },
                status_code=400,
            )

        if not code:
            return JSONResponse(
                {
                    "error": "invalid_request",
                    "error_description": "Missing authorization code",
                },
                status_code=400,
            )

        if not code_verifier:
            return JSONResponse(
                {
                    "error": "invalid_request",
                    "error_description": "Missing code_verifier (PKCE required)",
                },
                status_code=400,
            )

        # Look up the authorization code
        auth_code_data = _authorization_codes.get(code)
        if not auth_code_data or auth_code_data["used"]:
            return JSONResponse(
                {
                    "error": "invalid_grant",
                    "error_description": "Invalid or expired authorization code",
                },
                status_code=400,
            )

        # Validate client_id matches the one used in authorization
        if client_id and auth_code_data.get("client_id") != client_id:
            return JSONResponse(
                {"error": "invalid_client", "error_description": "Client ID mismatch"},
                status_code=400,
            )

        # Check code expiration (10 minutes)
        created_at = auth_code_data["created_at"]
        if isinstance(created_at, datetime) and datetime.now(
            timezone.utc
        ) - created_at > timedelta(minutes=10):
            return JSONResponse(
                {
                    "error": "invalid_grant",
                    "error_description": "Authorization code expired",
                },
                status_code=400,
            )

        # Verify PKCE challenge
        code_challenge = auth_code_data.get("code_challenge")
        if code_challenge and not verify_code_challenge(code_verifier, code_challenge):
            return JSONResponse(
                {
                    "error": "invalid_grant",
                    "error_description": "Invalid code_verifier",
                },
                status_code=400,
            )

        # Mark code as used
        auth_code_data["used"] = True

        # For dynamic clients, we don't need to exchange with Google again
        # The authorization code was already received from Google in our callback
        # We'll create a JWT token directly based on the user's Google OAuth session

        # Since we already have the authorization code from Google,
        # we need to exchange it with Google to get user info
        google_config = await get_google_config()
        token_endpoint = google_config["token_endpoint"]

        # Exchange the authorization code with Google using the PKCE verifier from Claude Code
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": auth_code_data["code"],
            "grant_type": "authorization_code",
            "redirect_uri": OAUTH_REDIRECT_URI,
            "code_verifier": code_verifier,  # Use Claude Code's code verifier
        }

        async with httpx.AsyncClient() as http_client:
            token_response = await http_client.post(token_endpoint, data=token_data)

            if token_response.status_code != 200:
                logger.error(
                    f"Google token exchange failed: {token_response.status_code} {token_response.text}"
                )
                return JSONResponse(
                    {
                        "error": "server_error",
                        "error_description": "Failed to exchange authorization code with Google",
                    },
                    status_code=500,
                )

            token = token_response.json()

        # Get user info from Google using the access token
        userinfo_endpoint = google_config["userinfo_endpoint"]
        access_token = token.get("access_token")

        if not access_token:
            return JSONResponse(
                {
                    "error": "server_error",
                    "error_description": "No access token received from Google",
                },
                status_code=500,
            )

        async with httpx.AsyncClient() as http_client:
            user_response = await http_client.get(
                userinfo_endpoint, headers={"Authorization": f"Bearer {access_token}"}
            )

            if user_response.status_code != 200:
                logger.error(
                    f"Google userinfo failed: {user_response.status_code} {user_response.text}"
                )
                return JSONResponse(
                    {
                        "error": "server_error",
                        "error_description": "Failed to get user info from Google",
                    },
                    status_code=500,
                )

            user_info = user_response.json()

        # Create our JWT access token
        jwt_access_token = create_jwt_token(user_info)

        # Return OAuth 2.0 token response
        return JSONResponse(
            {
                "access_token": jwt_access_token,
                "token_type": "Bearer",
                "expires_in": JWT_EXPIRY_HOURS * 3600,
                "scope": "openid email profile",
            }
        )

    except Exception as e:
        logger.error(f"Token endpoint error: {e}")
        return JSONResponse(
            {"error": "server_error", "error_description": str(e)}, status_code=500
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
        # Check for environment variable fallback
        env_token = os.getenv("MCP_AUTH_TOKEN")
        if env_token:
            return validate_jwt_token(env_token)
        return None

    token = extract_bearer_token(authorization)
    if not token:
        return None

    return validate_jwt_token(token)
