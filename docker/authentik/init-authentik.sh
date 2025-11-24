#!/bin/bash
set -e

echo "🔧 Authentik Auto-Configuration Script"
echo "======================================="

# Environment variables
AUTHENTIK_URL="${AUTHENTIK_URL:-http://authentik-server:9000}"
AUTHENTIK_BOOTSTRAP_EMAIL="${AUTHENTIK_BOOTSTRAP_EMAIL:-admin@example.com}"
AUTHENTIK_BOOTSTRAP_PASSWORD="${AUTHENTIK_BOOTSTRAP_PASSWORD:-admin123}"
FRONTEND_CLIENT_ID="${AUTHENTIK_FRONTEND_CLIENT_ID:-llars-frontend}"
BACKEND_CLIENT_ID="${AUTHENTIK_BACKEND_CLIENT_ID:-llars-backend}"
BACKEND_CLIENT_SECRET="${AUTHENTIK_BACKEND_CLIENT_SECRET:-llars-backend-secret-change-in-production}"
BASE_URL="${BASE_URL:-http://localhost:55080}"

# Wait for Authentik to be ready
echo "⏳ Waiting for Authentik to be ready..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
  if curl -sf "$AUTHENTIK_URL/-/health/ready/" > /dev/null 2>&1; then
    echo "✅ Authentik is ready!"
    break
  fi
  attempt=$((attempt + 1))
  if [ $attempt -eq $max_attempts ]; then
    echo "❌ Authentik did not become ready in time"
    exit 1
  fi
  echo "   Attempt $attempt/$max_attempts..."
  sleep 5
done

# Additional wait for full initialization
echo "⏳ Waiting for Authentik to complete initialization..."
sleep 10

# Get API token by logging in
echo "🔐 Authenticating as bootstrap admin..."
TOKEN_RESPONSE=$(curl -s -X POST "$AUTHENTIK_URL/api/v3/flows/executor/default-authentication-flow/" \
  -H "Content-Type: application/json" \
  -d "{\"uid_field\": \"$AUTHENTIK_BOOTSTRAP_EMAIL\", \"password\": \"$AUTHENTIK_BOOTSTRAP_PASSWORD\"}" \
  2>&1) || true

# Try to get an API token using basic auth (akadmin user)
# Authentik creates a default "akadmin" user, let's try that too
echo "🔑 Trying to get API token..."

# Method 1: Try to create a token via API
API_TOKEN=$(curl -s -X POST "$AUTHENTIK_URL/api/v3/core/tokens/" \
  -H "Content-Type: application/json" \
  -u "$AUTHENTIK_BOOTSTRAP_EMAIL:$AUTHENTIK_BOOTSTRAP_PASSWORD" \
  -d '{
    "identifier": "llars-setup-token",
    "intent": "api",
    "user": 1,
    "description": "LLARS Setup Token"
  }' 2>&1 | grep -o '"key":"[^"]*"' | cut -d'"' -f4) || true

if [ -z "$API_TOKEN" ]; then
  echo "⚠️  Could not obtain API token automatically"
  echo "📝 Authentik needs to be configured manually via web UI"
  echo ""
  echo "Please visit: http://localhost:55095"
  echo "Login with:"
  echo "  Email: $AUTHENTIK_BOOTSTRAP_EMAIL"
  echo "  Password: $AUTHENTIK_BOOTSTRAP_PASSWORD"
  echo ""
  echo "Then follow the steps in QUICK_START.md"
  exit 0
fi

echo "✅ API token obtained"

# Helper function to call Authentik API
call_api() {
  local method=$1
  local endpoint=$2
  local data=$3

  curl -s -X "$method" "$AUTHENTIK_URL$endpoint" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    ${data:+-d "$data"}
}

# Check if providers already exist
echo "🔍 Checking existing configuration..."
EXISTING_PROVIDERS=$(call_api GET "/api/v3/providers/oauth2/" | grep -o "\"name\":\"llars-" | wc -l) || true

if [ "$EXISTING_PROVIDERS" -gt 0 ]; then
  echo "ℹ️  Authentik is already configured (found existing providers)"
  echo "✅ Auto-configuration skipped"
  exit 0
fi

echo "🚀 Starting automatic configuration..."

# Create Frontend Provider (Public)
echo "📦 Creating Frontend OAuth2 Provider..."
FRONTEND_PROVIDER=$(call_api POST "/api/v3/providers/oauth2/" '{
  "name": "llars-frontend-provider",
  "authentication_flow": null,
  "authorization_flow": "default-provider-authorization-explicit-consent",
  "client_type": "public",
  "client_id": "'$FRONTEND_CLIENT_ID'",
  "client_secret": "",
  "redirect_uris": "'$BASE_URL'/*\nhttp://127.0.0.1:55080/*",
  "sub_mode": "hashed_user_id",
  "issuer_mode": "per_provider",
  "signing_key": null
}')

FRONTEND_PROVIDER_PK=$(echo "$FRONTEND_PROVIDER" | grep -o '"pk":[0-9]*' | head -1 | cut -d':' -f2) || true

if [ -n "$FRONTEND_PROVIDER_PK" ]; then
  echo "✅ Frontend provider created (PK: $FRONTEND_PROVIDER_PK)"
else
  echo "⚠️  Could not create frontend provider"
fi

# Create Backend Provider (Confidential)
echo "📦 Creating Backend OAuth2 Provider..."
BACKEND_PROVIDER=$(call_api POST "/api/v3/providers/oauth2/" '{
  "name": "llars-backend-provider",
  "authentication_flow": null,
  "authorization_flow": "default-provider-authorization-explicit-consent",
  "client_type": "confidential",
  "client_id": "'$BACKEND_CLIENT_ID'",
  "client_secret": "'$BACKEND_CLIENT_SECRET'",
  "redirect_uris": "'$BASE_URL'/*",
  "sub_mode": "hashed_user_id",
  "issuer_mode": "per_provider"
}')

BACKEND_PROVIDER_PK=$(echo "$BACKEND_PROVIDER" | grep -o '"pk":[0-9]*' | head -1 | cut -d':' -f2) || true

if [ -n "$BACKEND_PROVIDER_PK" ]; then
  echo "✅ Backend provider created (PK: $BACKEND_PROVIDER_PK)"
else
  echo "⚠️  Could not create backend provider"
fi

# Create Frontend Application
if [ -n "$FRONTEND_PROVIDER_PK" ]; then
  echo "📱 Creating Frontend Application..."
  call_api POST "/api/v3/core/applications/" '{
    "name": "LLARS Frontend",
    "slug": "llars-frontend",
    "provider": '$FRONTEND_PROVIDER_PK',
    "launch_url": "'$BASE_URL'",
    "open_in_new_tab": false
  }' > /dev/null
  echo "✅ Frontend application created"
fi

# Create Backend Application
if [ -n "$BACKEND_PROVIDER_PK" ]; then
  echo "📱 Creating Backend Application..."
  call_api POST "/api/v3/core/applications/" '{
    "name": "LLARS Backend",
    "slug": "llars-backend",
    "provider": '$BACKEND_PROVIDER_PK'
  }' > /dev/null
  echo "✅ Backend application created"
fi

# Create test users
echo "👤 Creating test users..."

# Admin user (already exists as bootstrap, just ensure it's active)
echo "   - admin@llars.local"
call_api POST "/api/v3/core/users/" '{
  "username": "admin",
  "name": "Admin User",
  "email": "admin@llars.local",
  "is_active": true,
  "path": "users"
}' > /dev/null 2>&1 || echo "   (admin user may already exist)"

# Researcher user
echo "   - researcher@llars.local"
call_api POST "/api/v3/core/users/" '{
  "username": "researcher",
  "name": "Researcher User",
  "email": "researcher@llars.local",
  "is_active": true,
  "path": "users"
}' > /dev/null 2>&1 || true

# Viewer user
echo "   - viewer@llars.local"
call_api POST "/api/v3/core/users/" '{
  "username": "viewer",
  "name": "Viewer User",
  "email": "viewer@llars.local",
  "is_active": true,
  "path": "users"
}' > /dev/null 2>&1 || true

echo ""
echo "✅ Authentik auto-configuration complete!"
echo ""
echo "🎉 You can now log in to LLARS:"
echo "   URL: $BASE_URL"
echo "   Users:"
echo "     - admin@example.com (bootstrap admin)"
echo "     - admin@llars.local"
echo "     - researcher@llars.local"
echo "     - viewer@llars.local"
echo ""
echo "⚠️  Note: User passwords need to be set manually in Authentik admin UI"
echo "   Visit: http://localhost:55095/if/admin/"
echo ""
