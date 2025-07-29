#!/bin/bash
# Deploy MCP server to GCP VM

# Set script to exit on error
set -e

# Configuration
IMAGE_NAME="mcp-server-web"
GCP_PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}"
GCR_HOSTNAME="${GCR_HOSTNAME:-gcr.io}"
INSTANCE_NAME="${INSTANCE_NAME:-mcp-server-vm}"
ZONE="${ZONE:-us-central1-a}"
USE_SELF_SIGNED="${USE_SELF_SIGNED:-false}"

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

echo "=== GCP Deployment Script ==="
echo "This script will help deploy the MCP server to a GCP VM"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Build the Docker image
echo "Step 1: Building Docker image..."
./scripts/build.sh

# Tag for GCR
echo "Step 2: Tagging image for Google Container Registry..."
docker tag ${IMAGE_NAME}:latest ${GCR_HOSTNAME}/${GCP_PROJECT_ID}/${IMAGE_NAME}:latest

# Push to GCR
echo "Step 3: Pushing image to GCR..."
echo "Note: You may need to authenticate with: gcloud auth configure-docker"
docker push ${GCR_HOSTNAME}/${GCP_PROJECT_ID}/${IMAGE_NAME}:latest

# Create startup script
cat > /tmp/mcp-startup-script.sh << 'EOF'
#!/bin/bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Configure Docker to start on boot
systemctl enable docker
systemctl start docker

# Setup SSL certificates
if [ -n "$DOMAIN_NAME" ]; then
    echo "Setting up Let's Encrypt SSL certificates for $DOMAIN_NAME..."
    
    # Install certbot
    apt-get update
    apt-get install -y certbot
    
    # Generate certificates
    certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email "${SSL_EMAIL:-admin@$DOMAIN_NAME}" \
        -d "$DOMAIN_NAME" \
        --preferred-challenges http
    
    # Setup certificate paths
    mkdir -p /etc/ssl/certs /etc/ssl/private
    ln -sf "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" "/etc/ssl/certs/cert.pem"
    ln -sf "/etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem" "/etc/ssl/private/key.pem"
    chmod 644 /etc/ssl/certs/cert.pem
    chmod 600 /etc/ssl/private/key.pem
    
    # Setup auto-renewal
    echo "0 */12 * * * root certbot renew --quiet --post-hook 'docker restart mcp-server 2>/dev/null || true'" > /etc/cron.d/certbot-renew
    
    # Run with HTTPS
    docker pull GCR_IMAGE_URL
    docker run -d \
        --name mcp-server \
        --restart always \
        -p 8443:8443 \
        -v /etc/ssl:/etc/ssl:ro \
        -e SSL_ENABLED=true \
        -e MCP_PORT=8443 \
        GCR_IMAGE_URL
elif [ "$USE_SELF_SIGNED" = "true" ]; then
    echo "Setting up self-signed SSL certificate for IP-based HTTPS..."
    
    # Install OpenSSL
    apt-get update
    apt-get install -y openssl
    
    # Get VM's external IP (will be available as metadata)
    EXTERNAL_IP=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip" -H "Metadata-Flavor: Google")
    
    # Generate self-signed certificate for IP
    mkdir -p /etc/ssl/certs /etc/ssl/private
    openssl genrsa -out /etc/ssl/private/key.pem 2048
    openssl req -new -x509 -key /etc/ssl/private/key.pem \
        -out /etc/ssl/certs/cert.pem \
        -days 365 \
        -subj "/C=US/ST=State/L=City/O=MCP-Server/CN=$EXTERNAL_IP" \
        -addext "subjectAltName=IP:$EXTERNAL_IP"
    
    chmod 644 /etc/ssl/certs/cert.pem
    chmod 600 /etc/ssl/private/key.pem
    
    # Run with HTTPS
    docker pull GCR_IMAGE_URL
    docker run -d \
        --name mcp-server \
        --restart always \
        -p 8443:8443 \
        -v /etc/ssl:/etc/ssl:ro \
        -e SSL_ENABLED=true \
        -e MCP_PORT=8443 \
        GCR_IMAGE_URL
else
    # Run with HTTP only
    docker pull GCR_IMAGE_URL
    docker run -d \
        --name mcp-server \
        --restart always \
        -p 8899:8899 \
        GCR_IMAGE_URL
fi
EOF

# Replace placeholder with actual image URL
sed -i "s|GCR_IMAGE_URL|${GCR_HOSTNAME}/${GCP_PROJECT_ID}/${IMAGE_NAME}:latest|g" /tmp/mcp-startup-script.sh

# Create metadata with environment variables
METADATA="startup-script=/tmp/mcp-startup-script.sh"
if [ -n "$DOMAIN_NAME" ]; then
    METADATA="${METADATA},DOMAIN_NAME=${DOMAIN_NAME}"
    if [ -n "$SSL_EMAIL" ]; then
        METADATA="${METADATA},SSL_EMAIL=${SSL_EMAIL}"
    fi
fi

echo "Step 4: Creating/updating VM instance..."
gcloud compute instances create ${INSTANCE_NAME} \
    --project=${GCP_PROJECT_ID} \
    --zone=${ZONE} \
    --machine-type=e2-micro \
    --network-interface=network-tier=PREMIUM,subnet=default \
    --metadata="$METADATA" \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=default \
    --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
    --tags=http-server,mcp-server \
    --create-disk=auto-delete=yes,boot=yes,device-name=${INSTANCE_NAME},image=projects/debian-cloud/global/images/debian-11-bullseye-v20240415,mode=rw,size=10,type=projects/${GCP_PROJECT_ID}/zones/${ZONE}/diskTypes/pd-standard \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=app=mcp-server \
    --reservation-affinity=any || echo "VM already exists, updating..."

# Create firewall rules for both HTTP and HTTPS
echo "Step 5: Creating firewall rules..."
gcloud compute firewall-rules create allow-mcp-server-http \
    --project=${GCP_PROJECT_ID} \
    --allow tcp:8899 \
    --source-ranges 0.0.0.0/0 \
    --target-tags mcp-server \
    --description "Allow MCP server HTTP access on port 8899" || echo "HTTP firewall rule already exists"

gcloud compute firewall-rules create allow-mcp-server-https \
    --project=${GCP_PROJECT_ID} \
    --allow tcp:8443 \
    --source-ranges 0.0.0.0/0 \
    --target-tags mcp-server \
    --description "Allow MCP server HTTPS access on port 8443" || echo "HTTPS firewall rule already exists"

# Allow HTTP (port 80) for Let's Encrypt certificate validation
gcloud compute firewall-rules create allow-http-letsencrypt \
    --project=${GCP_PROJECT_ID} \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --target-tags mcp-server \
    --description "Allow HTTP for Let's Encrypt certificate validation" || echo "Let's Encrypt firewall rule already exists"

# Get the external IP
echo ""
echo "=== Deployment Complete ==="
echo "Getting VM external IP..."
EXTERNAL_IP=$(gcloud compute instances describe ${INSTANCE_NAME} \
    --project=${GCP_PROJECT_ID} \
    --zone=${ZONE} \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
if [ -n "$DOMAIN_NAME" ]; then
    echo "MCP server will be available at:"
    echo "  HTTPS: https://${DOMAIN_NAME}:8443/sse"
    echo "  HTTP:  http://${EXTERNAL_IP}:8899/sse (fallback)"
    echo ""
    echo "SSL certificates will be automatically generated for ${DOMAIN_NAME}"
    echo "Make sure ${DOMAIN_NAME} points to ${EXTERNAL_IP}"
elif [ "$USE_SELF_SIGNED" = "true" ]; then
    echo "MCP server will be available at:"
    echo "  HTTPS: https://${EXTERNAL_IP}:8443/sse (self-signed certificate)"
    echo "  HTTP:  http://${EXTERNAL_IP}:8899/sse (fallback)"
    echo ""
    echo "⚠️  WARNING: Self-signed certificate will show security warnings"
    echo "⚠️  Browsers will require you to accept the security risk"
    echo "⚠️  For production use, get a domain name and use Let's Encrypt"
else
    echo "MCP server will be available at: http://${EXTERNAL_IP}:8899/sse"
    echo ""
    echo "HTTPS deployment options:"
    echo "  1. With domain (recommended): export DOMAIN_NAME=your-domain.com && ./scripts/deploy-gcp.sh"
    echo "  2. Self-signed (testing only): export USE_SELF_SIGNED=true && ./scripts/deploy-gcp.sh"
fi
echo ""
echo "Note: It may take a few minutes for the server to start up"
echo ""
echo "To check server logs, SSH into the VM and run:"
echo "  gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE} --project=${GCP_PROJECT_ID}"
echo "  docker logs mcp-server"

# Clean up
rm -f /tmp/mcp-startup-script.sh