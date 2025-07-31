#!/bin/bash

# Script to run MCP server with Let's Encrypt certificate

# Source .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

DOMAIN_NAME=${DOMAIN_NAME:-"example.com"}
SSL_EMAIL=${SSL_EMAIL:-"admin@example.com"}
# OAuth configuration
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-""}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:-""}
OAUTH_REDIRECT_URI=${OAUTH_REDIRECT_URI:-"https://$DOMAIN_NAME:8443/callback"}
JWT_SECRET_KEY=${JWT_SECRET_KEY:-$(openssl rand -base64 32 2>/dev/null || echo "change-this-secret")}

echo "=== Starting MCP Server with Let's Encrypt ==="
echo "Domain: $DOMAIN_NAME"
echo "Email: $SSL_EMAIL"
echo "OAuth enabled: $([ -n "$GOOGLE_CLIENT_ID" ] && echo "Yes" || echo "No")"

# Create directories for certificates
sudo mkdir -p /etc/letsencrypt
sudo mkdir -p /var/lib/letsencrypt

# Stop any existing container
sudo docker stop mcp-server-web 2>/dev/null || true
sudo docker rm mcp-server-web 2>/dev/null || true

# Get Let's Encrypt certificate using certbot in a container
echo "Getting Let's Encrypt certificate..."
sudo docker run --rm \
  -p 80:80 \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot \
  certonly --standalone \
  --email "$SSL_EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  --keep-until-expiring \
  --domain "$DOMAIN_NAME"

if [ $? -eq 0 ]; then
    echo "Certificate obtained successfully!"
    
    # Copy oauth.py to make it available in container
    sudo cp oauth.py /tmp/oauth.py
    
    # Run the MCP server with SSL enabled
    echo "Starting MCP server with SSL and authentication..."
    sudo docker run -d \
      --name mcp-server-web \
      --restart unless-stopped \
      -p 8443:8443 \
      -v /etc/letsencrypt:/etc/letsencrypt:ro \
      -v /tmp/oauth.py:/app/oauth.py:ro \
      -e MCP_HOST=0.0.0.0 \
      -e MCP_PORT=8443 \
      -e SSL_ENABLED=true \
      -e SSL_CERT_PATH="/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" \
      -e SSL_KEY_PATH="/etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem" \
      -e GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
      -e GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
      -e OAUTH_REDIRECT_URI="$OAUTH_REDIRECT_URI" \
      -e JWT_SECRET_KEY="$JWT_SECRET_KEY" \
      mcp-server-web:latest
    
    echo ""
    echo "=== Deployment Complete! ==="
    echo "Server URL: https://$DOMAIN_NAME:8443/sse"
    if [ -n "$GOOGLE_CLIENT_ID" ]; then
        echo "OAuth Authentication: Enabled"
        echo "OAuth Redirect URI: $OAUTH_REDIRECT_URI"
        echo ""
        echo "Test OAuth metadata:"
        echo "curl https://$DOMAIN_NAME:8443/.well-known/oauth-authorization-server"
    else
        echo "Authentication: Disabled (no Google Client ID configured)"
    fi
else
    echo "Failed to obtain certificate. Check domain and firewall settings."
    exit 1
fi