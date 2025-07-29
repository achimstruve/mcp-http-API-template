#!/bin/bash
# Setup SSL certificates using Let's Encrypt

set -e

# Configuration
DOMAIN_NAME="${DOMAIN_NAME:-}"
EMAIL="${SSL_EMAIL:-admin@${DOMAIN_NAME}}"
CERT_DIR="/etc/ssl/certs"
KEY_DIR="/etc/ssl/private"

if [ -z "$DOMAIN_NAME" ]; then
    echo "Error: DOMAIN_NAME environment variable is required"
    echo "Usage: DOMAIN_NAME=your-domain.com ./scripts/setup-ssl.sh"
    exit 1
fi

echo "=== Setting up SSL certificates for $DOMAIN_NAME ==="

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update
    apt-get install -y certbot
fi

# Stop any running MCP server temporarily
docker stop mcp-server-web 2>/dev/null || true

# Generate certificates using standalone mode
echo "Generating SSL certificate for $DOMAIN_NAME..."
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN_NAME" \
    --preferred-challenges http

# Copy certificates to expected locations
echo "Setting up certificate paths..."
mkdir -p "$CERT_DIR" "$KEY_DIR"

# Create symlinks to Let's Encrypt certificates
ln -sf "/etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem" "${CERT_DIR}/cert.pem"
ln -sf "/etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem" "${KEY_DIR}/key.pem"

# Set proper permissions
chmod 644 "${CERT_DIR}/cert.pem"
chmod 600 "${KEY_DIR}/key.pem"

# Setup automatic renewal
echo "Setting up automatic certificate renewal..."
cat > /etc/cron.d/certbot-renew << EOF
# Renew Let's Encrypt certificates twice daily
0 */12 * * * root certbot renew --quiet --post-hook "docker restart mcp-server-web 2>/dev/null || true"
EOF

echo "SSL certificates setup complete!"
echo "Certificate: ${CERT_DIR}/cert.pem"
echo "Private Key: ${KEY_DIR}/key.pem"
echo "Automatic renewal configured via cron"