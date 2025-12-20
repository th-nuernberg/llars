#!/bin/bash

#########################################
# LLARS User Provisioning Script
#########################################
# Creates project users via LLARS Admin API
# Can be run multiple times - existing users are skipped
#########################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

#########################################
# Configuration
#########################################

# Load from .env if available
if [ -f ".env" ]; then
    set -a  # Export all variables
    source .env
    set +a
fi

# API Base URL
PROJECT_URL="${PROJECT_URL:-http://localhost:55080}"
API_URL="${PROJECT_URL}/api"
AUTH_URL="${PROJECT_URL}/auth"

# Admin credentials (from .env)
ADMIN_USER="admin"
ADMIN_PASSWORD="${LLARS_ADMIN_PASSWORD:-admin123}"

# Default role for new users
DEFAULT_ROLE="researcher"

#########################################
# User Definitions
#########################################
# Format: username:display_name:email:password
# Passwords are pronounceable with special character at end

declare -A USERS=(
    ["ieb-stieler"]="Stieler:stieler@e-beratungsinstitut.de:Kaffee2024!"
    ["ieb-burghardt"]="Burghardt:burghardt@e-beratungsinstitut.de:Sommer2025#"
    ["ieb-franz"]="Franz:franz@e-beratungsinstitut.de:Winter2024@"
    ["ieb-bienlien"]="Bienlien:bienlien@e-beratungsinstitut.de:Herbst2025$"
    ["ieb-steigerwald"]="Steigerwald:steigerwald@e-beratungsinstitut.de:Fruehling2024%"
    ["ieb-test"]="Test User:test@e-beratungsinstitut.de:Testkonto2024&"
)

#########################################
# Functions
#########################################

get_auth_token() {
    print_info "Logging in as admin..." >&2

    RESPONSE=$(curl -s -X POST "${AUTH_URL}/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"${ADMIN_USER}\", \"password\": \"${ADMIN_PASSWORD}\"}")

    # Check for access_token in response (successful login)
    if echo "$RESPONSE" | grep -q '"access_token"'; then
        TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$TOKEN" ]; then
            print_success "Login successful" >&2
            echo "$TOKEN"
            return 0
        fi
    fi

    print_error "Login failed: $RESPONSE" >&2
    return 1
}

create_user() {
    local username="$1"
    local display_name="$2"
    local email="$3"
    local password="$4"
    local token="$5"

    print_info "Creating user: $username ($display_name)"

    # Build JSON body with proper escaping
    local json_body
    json_body=$(printf '{"username": "%s", "display_name": "%s", "email": "%s", "password": "%s", "is_active": true, "create_in_authentik": true, "role_names": ["%s"]}' \
        "$username" "$display_name" "$email" "$password" "$DEFAULT_ROLE")

    RESPONSE=$(curl -s -X POST "${API_URL}/admin/users" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${token}" \
        --data-raw "$json_body")

    if echo "$RESPONSE" | grep -q '"success":true'; then
        if echo "$RESPONSE" | grep -q '"warning"'; then
            WARNING=$(echo "$RESPONSE" | grep -o '"warning":"[^"]*"' | cut -d'"' -f4)
            print_warning "$username: $WARNING"
        else
            print_success "$username created successfully"
        fi
        return 0
    elif echo "$RESPONSE" | grep -q 'already exists'; then
        print_warning "$username already exists - skipping"
        return 0
    else
        print_error "Failed to create $username: $RESPONSE"
        return 1
    fi
}

#########################################
# Main
#########################################

echo ""
echo "======================================="
echo "  LLARS User Provisioning"
echo "======================================="
echo ""
echo "Project URL: $PROJECT_URL"
echo "Auth URL: $AUTH_URL"
echo "API URL: $API_URL"
echo "Default Role: $DEFAULT_ROLE"
echo ""

# Get auth token
TOKEN=$(get_auth_token) || true
if [ -z "$TOKEN" ]; then
    print_error "Could not obtain auth token. Exiting."
    exit 1
fi

echo ""
echo "---------------------------------------"
echo "  Creating Users"
echo "---------------------------------------"
echo ""

CREATED=0
SKIPPED=0
FAILED=0

for username in "${!USERS[@]}"; do
    IFS=':' read -r display_name email password <<< "${USERS[$username]}"

    if create_user "$username" "$display_name" "$email" "$password" "$TOKEN"; then
        CREATED=$((CREATED + 1))
    else
        FAILED=$((FAILED + 1))
    fi

    # Small delay to avoid rate limiting
    sleep 0.5
done

echo ""
echo "======================================="
echo "  Summary"
echo "======================================="
echo ""
echo "  Created/Updated: $CREATED"
echo "  Failed: $FAILED"
echo ""

# Print credentials table
echo "---------------------------------------"
echo "  User Credentials"
echo "---------------------------------------"
echo ""
printf "%-20s %-30s %s\n" "Username" "Email" "Password"
printf "%-20s %-30s %s\n" "--------" "-----" "--------"
for username in "${!USERS[@]}"; do
    IFS=':' read -r display_name email password <<< "${USERS[$username]}"
    printf "%-20s %-30s %s\n" "$username" "$email" "$password"
done
echo ""
echo "======================================="

if [ $FAILED -gt 0 ]; then
    exit 1
fi
