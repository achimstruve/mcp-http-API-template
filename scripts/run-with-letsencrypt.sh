#!/bin/bash

# Script to run MCP server with Let's Encrypt certificate

DOMAIN_NAME=${DOMAIN_NAME:-"mcptemplate.agenovation.ai"}
SSL_EMAIL=${SSL_EMAIL:-"achim@agenovation.ai"}
AUTH_ENABLED=${AUTH_ENABLED:-"true"}
API_KEYS=${API_KEYS:-"demo:secret123,admin:admin456"}

echo "=== Starting MCP Server with Let's Encrypt ==="
echo "Domain: $DOMAIN_NAME"
echo "Email: $SSL_EMAIL"
echo "Auth enabled: $AUTH_ENABLED"

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
  --domain "$DOMAIN_NAME"

if [ $? -eq 0 ]; then
    echo "Certificate obtained successfully!"
    
    # Copy auth.py to make it available in container
    sudo cp auth.py /tmp/auth.py
    
    # Run the MCP server with SSL enabled
    echo "Starting MCP server with SSL and authentication..."
    sudo docker run -d \
      --name mcp-server-web \
      --restart unless-stopped \
      -p 8443:8443 \
      -v /etc/letsencrypt:/etc/letsencrypt:ro \
      -v /tmp/auth.py:/app/auth.py:ro \
      -e MCP_TRANSPORT=sse \
      -e MCP_HOST=0.0.0.0 \
      -e MCP_PORT=8443 \
      -e SSL_ENABLED=true \
      -e SSL_CERT_PATH="/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" \
      -e SSL_KEY_PATH="/etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem" \
      -e AUTH_ENABLED="$AUTH_ENABLED" \
      -e API_KEYS="$API_KEYS" \
      mcp-server-web:latest
    
    echo ""
    echo "=== Deployment Complete! ==="
    echo "Server URL: https://$DOMAIN_NAME:8443/sse"
    echo "Authentication: $AUTH_ENABLED"
    if [ "$AUTH_ENABLED" = "true" ]; then
        echo "Demo API key: demo:secret123"
        echo "Admin API key: admin:admin456"
        echo ""
        echo "Test connection:"
        echo "curl -H 'Authorization: Bearer secret123' https://$DOMAIN_NAME:8443/sse"
    fi
else
    echo "Failed to obtain certificate. Check domain and firewall settings."
    exit 1
fi