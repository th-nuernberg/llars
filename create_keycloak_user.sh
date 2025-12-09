#!/bin/bash

# DEPRECATED: Keycloak wird nicht mehr verwendet (Authentik ersetzt die Authentifizierung).
# Skript bleibt nur für Archivzwecke bestehen.

# Legacy helper: Create a test user in Keycloak using kcadm.sh (nicht mehr produktiv genutzt)
# Usage: ./create_keycloak_user.sh <username> <password> <email> <firstname> <lastname>

USERNAME="${1:-testuser}"
PASSWORD="${2:-Test123!}"
EMAIL="${3:-${USERNAME}@example.com}"
FIRSTNAME="${4:-Test}"
LASTNAME="${5:-User}"

echo "Creating legacy Keycloak user (deprecated)..."
echo "Username: $USERNAME"
echo "Email: $EMAIL"
echo ""

# Configure kcadm credentials
echo "1. Configuring kcadm credentials..."
docker exec llars_keycloak_service /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password admin_secure_password_123 > /dev/null 2>&1

if [ $? -ne 0 ]; then
  echo "❌ Failed to configure kcadm credentials"
  echo "   Make sure legacy Keycloak container is running: docker ps | grep keycloak"
  exit 1
fi

echo "✓ kcadm configured"
echo ""

# Create user
echo "2. Creating user in legacy Keycloak..."
USER_ID=$(docker exec llars_keycloak_service /opt/keycloak/bin/kcadm.sh create users \
  -r llars \
  -s username="$USERNAME" \
  -s email="$EMAIL" \
  -s firstName="$FIRSTNAME" \
  -s lastName="$LASTNAME" \
  -s enabled=true \
  -s emailVerified=true 2>&1)

if [ $? -eq 0 ]; then
  echo "✓ User created successfully!"
  echo "  User ID: $USER_ID"
else
  if echo "$USER_ID" | grep -q "User exists"; then
    echo "⚠ User already exists"
    echo ""
    echo "Try logging in with:"
    echo "Username: $USERNAME"
    echo "Password: (existing password)"
    echo ""
    echo "To reset password, run:"
    echo "docker exec llars_keycloak_service /opt/keycloak/bin/kcadm.sh set-password -r llars --username $USERNAME --new-password YOUR_PASSWORD"
    exit 0
  else
    echo "❌ Failed to create user"
    echo "$USER_ID"
    exit 1
  fi
fi

echo ""
echo "3. Setting password..."
docker exec llars_keycloak_service /opt/keycloak/bin/kcadm.sh set-password \
  -r llars \
  --username "$USERNAME" \
  --new-password "$PASSWORD" > /dev/null 2>&1

if [ $? -eq 0 ]; then
  echo "✓ Password set"
else
  echo "❌ Failed to set password"
  exit 1
fi

echo ""
echo "4. Assigning 'rater' role..."
docker exec llars_keycloak_service /opt/keycloak/bin/kcadm.sh add-roles \
  -r llars \
  --uusername "$USERNAME" \
  --rolename rater > /dev/null 2>&1

if [ $? -eq 0 ]; then
  echo "✓ Role assigned"
else
  echo "⚠ Failed to assign role (user might still be usable)"
fi

echo ""
echo "=========================================="
echo "Login Credentials:"
echo "=========================================="
echo "URL:      http://localhost:55173"
echo "Username: $USERNAME"
echo "Password: $PASSWORD"
echo "=========================================="
echo ""
echo "Done! You can now log in at http://localhost:55173"
