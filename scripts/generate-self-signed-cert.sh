#!/bin/bash
# Generate self-signed SSL certificate for IP address (testing only)

set -e

IP_ADDRESS="${1:-$(curl -s https://ipecho.net/plain)}"
CERT_DIR="/etc/ssl/certs"
KEY_DIR="/etc/ssl/private"

if [ -z "$IP_ADDRESS" ]; then
    echo "Usage: $0 <IP_ADDRESS>"
    echo "Example: $0 34.145.94.60"
    exit 1
fi

echo "=== Generating self-signed certificate for IP: $IP_ADDRESS ==="

# Create directories
mkdir -p "$CERT_DIR" "$KEY_DIR"

# Generate private key
openssl genrsa -out "${KEY_DIR}/key.pem" 2048

# Generate certificate with IP address in SAN
openssl req -new -x509 -key "${KEY_DIR}/key.pem" \
    -out "${CERT_DIR}/cert.pem" \
    -days 365 \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=${IP_ADDRESS}" \
    -addext "subjectAltName=IP:${IP_ADDRESS}"

# Set permissions
chmod 644 "${CERT_DIR}/cert.pem"
chmod 600 "${KEY_DIR}/key.pem"

echo "Self-signed certificate generated:"
echo "Certificate: ${CERT_DIR}/cert.pem"
echo "Private Key: ${KEY_DIR}/key.pem"
echo ""
echo "⚠️  WARNING: Self-signed certificates will show security warnings in browsers"
echo "⚠️  Only use for testing - not recommended for production"