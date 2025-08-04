#!/usr/bin/env python3
"""
Manual token generation script for headless environments.
This script allows you to generate a JWT token by manually completing OAuth in a browser.
"""

import os
import sys
import webbrowser
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, parse_qs, urlparse
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "1"))


def create_jwt_token(user_info):
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


def main():
    if not GOOGLE_CLIENT_ID:
        print("Error: GOOGLE_CLIENT_ID not configured")
        print("Please set the environment variable or add it to .env file")
        sys.exit(1)

    if not OAUTH_REDIRECT_URI:
        print("Error: OAUTH_REDIRECT_URI not configured")
        print("Please set the environment variable or add it to .env file")
        sys.exit(1)

    print("Manual Token Generation for MCP Server")
    print("=" * 40)
    print()
    print("This script will help you generate a JWT token for your MCP server.")
    print("You'll need to complete OAuth authentication in your browser.")
    print()

    # Build authorization URL
    auth_url = f"https://accounts.google.com/o/oauth2/auth?" + urlencode(
        {
            "client_id": GOOGLE_CLIENT_ID,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": OAUTH_REDIRECT_URI,
            "access_type": "online",
            "prompt": "select_account",
        }
    )

    print("Step 1: Open the following URL in your browser:")
    print(f"  {auth_url}")
    print()

    # Try to open browser automatically
    try:
        webbrowser.open(auth_url)
        print("Browser opened automatically.")
    except:
        print(
            "Could not open browser automatically. Please copy and paste the URL above."
        )

    print()
    print("Step 2: Complete the OAuth flow in your browser")
    print("Step 3: After authentication, you'll see a success page with a JWT token")
    print("Step 4: Copy that token and use it with your MCP client")
    print()
    print("The token will be valid for {} hour(s)".format(JWT_EXPIRY_HOURS))
    print()
    print("To use the token with Claude Code:")
    print(
        "1. Add your MCP server with: claude mcp add --transport sse my-server https://your-domain:8443/sse"
    )
    print("2. When prompted for authentication, use the JWT token as Bearer token")
    print()
    print("Alternatively, set the token as an environment variable:")
    print("export MCP_AUTH_TOKEN='your-jwt-token-here'")


if __name__ == "__main__":
    main()
