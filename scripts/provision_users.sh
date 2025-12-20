#!/bin/bash

#########################################
# LLARS User Provisioning Script
#########################################
# Creates project users via LLARS Admin API
# Loads user data from external YAML file
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

# Users file - can be passed as argument or via env var
USERS_FILE="${1:-${LLARS_USERS_FILE:-}}"

#########################################
# Validate Users File
#########################################

if [ -z "$USERS_FILE" ]; then
    print_error "No users file specified!"
    echo ""
    echo "Usage:"
    echo "  $0 <path-to-users.yaml>"
    echo ""
    echo "Or set environment variable:"
    echo "  export LLARS_USERS_FILE=/path/to/users.yaml"
    echo "  $0"
    echo ""
    echo "Expected file location:"
    echo "  /var/llars-seeder/users.yaml"
    echo ""
    exit 1
fi

if [ ! -f "$USERS_FILE" ]; then
    print_error "Users file not found: $USERS_FILE"
    echo ""
    echo "Make sure the llars-seeder repo is cloned:"
    echo "  cd /var && git clone git@git.informatik.fh-nuernberg.de:kiz-nlp/llars-seeder.git"
    echo ""
    exit 1
fi

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
    local role="$5"
    local token="$6"

    print_info "Creating user: $username ($display_name)"

    # Build JSON body with proper escaping
    local json_body
    json_body=$(printf '{"username": "%s", "display_name": "%s", "email": "%s", "password": "%s", "is_active": true, "create_in_authentik": true, "role_names": ["%s"]}' \
        "$username" "$display_name" "$email" "$password" "$role")

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
echo "Users File: $USERS_FILE"
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
FAILED=0

# Parse YAML and create users using Python (more reliable than bash YAML parsing)
python3 << EOF
import yaml
import subprocess
import sys
import os

with open("$USERS_FILE", "r") as f:
    data = yaml.safe_load(f)

default_role = data.get("default_role", "researcher")
users = data.get("users", {})

created = 0
failed = 0

for username, info in users.items():
    display_name = info.get("display_name", username)
    email = info.get("email", f"{username}@localhost")
    password = info.get("password", "")
    role = info.get("role", default_role)

    if not password:
        print(f"\033[0;31m[ERROR]\033[0m No password for {username} - skipping")
        failed += 1
        continue

    # Output in format that bash can parse
    print(f"USER:{username}:{display_name}:{email}:{password}:{role}")

# Write counts
print(f"COUNT:{len(users)}")
EOF

# Read the Python output and create users
TOTAL=0
while IFS= read -r line; do
    if [[ "$line" == USER:* ]]; then
        # Parse: USER:username:display_name:email:password:role
        line="${line#USER:}"
        IFS=':' read -r username display_name email password role <<< "$line"

        if create_user "$username" "$display_name" "$email" "$password" "$role" "$TOKEN"; then
            CREATED=$((CREATED + 1))
        else
            FAILED=$((FAILED + 1))
        fi

        # Small delay to avoid rate limiting
        sleep 0.5
    elif [[ "$line" == COUNT:* ]]; then
        TOTAL="${line#COUNT:}"
    fi
done < <(python3 << EOF
import yaml

with open("$USERS_FILE", "r") as f:
    data = yaml.safe_load(f)

default_role = data.get("default_role", "researcher")
users = data.get("users", {})

for username, info in users.items():
    display_name = info.get("display_name", username)
    email = info.get("email", f"{username}@localhost")
    password = info.get("password", "")
    role = info.get("role", default_role)

    if password:
        print(f"USER:{username}:{display_name}:{email}:{password}:{role}")

print(f"COUNT:{len(users)}")
EOF
)

echo ""
echo "======================================="
echo "  Summary"
echo "======================================="
echo ""
echo "  Total Users: $TOTAL"
echo "  Created/Updated: $CREATED"
echo "  Failed: $FAILED"
echo ""
echo "======================================="

if [ $FAILED -gt 0 ]; then
    exit 1
fi
