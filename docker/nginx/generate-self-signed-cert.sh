#!/bin/bash
# ============================================
# Generate Self-Signed SSL Certificate
# ============================================
# FOR DEVELOPMENT/TESTING ONLY!
# DO NOT USE IN PRODUCTION!

set -e

CERT_DIR="./certs"
DOMAIN="${1:-localhost}"
DAYS=365

echo "============================================"
echo "Generating Self-Signed SSL Certificate"
echo "============================================"
echo "Domain: $DOMAIN"
echo "Validity: $DAYS days"
echo "Output: $CERT_DIR/"
echo "============================================"

# Create directory
mkdir -p "$CERT_DIR"

# Generate private key and certificate
openssl req -x509 -nodes -days $DAYS -newkey rsa:2048 \
    -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -subj "/C=DE/ST=Bavaria/L=Nuremberg/O=LLARS Development/CN=$DOMAIN"

# Set permissions
chmod 644 "$CERT_DIR/cert.pem"
chmod 600 "$CERT_DIR/key.pem"

echo ""
echo "✓ Certificate generated successfully!"
echo ""
echo "Files created:"
echo "  - $CERT_DIR/cert.pem (certificate)"
echo "  - $CERT_DIR/key.pem (private key)"
echo ""
echo "⚠️  WARNING: This is a SELF-SIGNED certificate!"
echo "    - Browsers will show security warnings"
echo "    - Only use for development/testing"
echo "    - Use Let's Encrypt for production"
echo ""
echo "To trust this certificate locally (macOS):"
echo "  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain $CERT_DIR/cert.pem"
echo ""
echo "============================================"
