#!/bin/bash

#########################################
# LLARS Authentik Verification Script
#########################################
# Quick script to verify Authentik setup
#########################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_check() {
    local name=$1
    local expected=$2
    local actual=$3

    if [ "$actual" -eq "$expected" ]; then
        echo -e "${GREEN}✓${NC} $name: $actual/$expected"
        return 0
    else
        echo -e "${RED}✗${NC} $name: $actual/$expected (FAILED)"
        return 1
    fi
}

echo -e "${BLUE}Verifying Authentik Setup...${NC}\n"

# Check if Authentik is running
if ! docker compose ps | grep -q "authentik-server.*running"; then
    echo -e "${RED}✗ Authentik server is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Authentik server is running"

# Run verification checks
RESULT=$(docker compose exec -T authentik-server ak shell <<'EOF'
from authentik.flows.models import Flow, FlowStageBinding
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.core.models import Application, User, Group

# Count objects
flow_count = Flow.objects.filter(slug='llars-api-authentication').count()
flow_stages = FlowStageBinding.objects.filter(target__slug='llars-api-authentication').count()
provider_count = OAuth2Provider.objects.filter(name__icontains='llars').count()
app_count = Application.objects.filter(slug__icontains='llars').count()
user_count = User.objects.filter(username__in=['admin', 'akadmin', 'researcher', 'evaluator']).count()
admin_count = User.objects.filter(username__in=['admin', 'akadmin'], ak_groups__name='authentik Admins').count()

# Check specific objects
backend_provider = OAuth2Provider.objects.filter(name='llars-backend-provider').first()
frontend_provider = OAuth2Provider.objects.filter(name='llars-frontend-provider').first()

# Print results (parsed by bash)
print(f"FLOWS:{flow_count}")
print(f"STAGES:{flow_stages}")
print(f"PROVIDERS:{provider_count}")
print(f"APPS:{app_count}")
print(f"USERS:{user_count}")
print(f"ADMINS:{admin_count}")
print(f"BACKEND_CLIENT_ID:{backend_provider.client_id if backend_provider else 'MISSING'}")
print(f"BACKEND_TYPE:{backend_provider.client_type if backend_provider else 'MISSING'}")
print(f"FRONTEND_CLIENT_ID:{frontend_provider.client_id if frontend_provider else 'MISSING'}")
print(f"FRONTEND_TYPE:{frontend_provider.client_type if frontend_provider else 'MISSING'}")
EOF
)

# Parse results
FLOWS=$(echo "$RESULT" | grep "^FLOWS:" | cut -d: -f2)
STAGES=$(echo "$RESULT" | grep "^STAGES:" | cut -d: -f2)
PROVIDERS=$(echo "$RESULT" | grep "^PROVIDERS:" | cut -d: -f2)
APPS=$(echo "$RESULT" | grep "^APPS:" | cut -d: -f2)
USERS=$(echo "$RESULT" | grep "^USERS:" | cut -d: -f2)
ADMINS=$(echo "$RESULT" | grep "^ADMINS:" | cut -d: -f2)
BACKEND_CLIENT_ID=$(echo "$RESULT" | grep "^BACKEND_CLIENT_ID:" | cut -d: -f2)
BACKEND_TYPE=$(echo "$RESULT" | grep "^BACKEND_TYPE:" | cut -d: -f2)
FRONTEND_CLIENT_ID=$(echo "$RESULT" | grep "^FRONTEND_CLIENT_ID:" | cut -d: -f2)
FRONTEND_TYPE=$(echo "$RESULT" | grep "^FRONTEND_TYPE:" | cut -d: -f2)

# Print results
echo ""
echo -e "${BLUE}Configuration:${NC}"
print_check "Authentication flows" 1 "$FLOWS"
print_check "Flow stages" 3 "$STAGES"
print_check "OAuth2 providers" 2 "$PROVIDERS"
print_check "Applications" 2 "$APPS"
print_check "Test users" 4 "$USERS"
print_check "Admin users" 2 "$ADMINS"

echo ""
echo -e "${BLUE}Provider Details:${NC}"
if [ "$BACKEND_CLIENT_ID" = "llars-backend" ]; then
    echo -e "${GREEN}✓${NC} Backend provider client_id: $BACKEND_CLIENT_ID"
else
    echo -e "${RED}✗${NC} Backend provider client_id: $BACKEND_CLIENT_ID (expected: llars-backend)"
fi

if [ "$BACKEND_TYPE" = "confidential" ]; then
    echo -e "${GREEN}✓${NC} Backend provider type: $BACKEND_TYPE"
else
    echo -e "${RED}✗${NC} Backend provider type: $BACKEND_TYPE (expected: confidential)"
fi

if [ "$FRONTEND_CLIENT_ID" = "llars-frontend" ]; then
    echo -e "${GREEN}✓${NC} Frontend provider client_id: $FRONTEND_CLIENT_ID"
else
    echo -e "${RED}✗${NC} Frontend provider client_id: $FRONTEND_CLIENT_ID (expected: llars-frontend)"
fi

if [ "$FRONTEND_TYPE" = "public" ]; then
    echo -e "${GREEN}✓${NC} Frontend provider type: $FRONTEND_TYPE"
else
    echo -e "${RED}✗${NC} Frontend provider type: $FRONTEND_TYPE (expected: public)"
fi

# Check URLs
echo ""
echo -e "${BLUE}Service URLs:${NC}"
echo "  Authentik UI:   http://localhost:55095"
echo "  LLARS Login:    http://localhost:55080/login"
echo "  Backend API:    http://localhost:55080/api"

# Test if ports are accessible
echo ""
echo -e "${BLUE}Port Status:${NC}"
if curl -s http://localhost:55095 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Authentik UI accessible (port 55095)"
else
    echo -e "${RED}✗${NC} Authentik UI not accessible (port 55095)"
fi

if curl -s http://localhost:55080 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} LLARS frontend accessible (port 55080)"
else
    echo -e "${RED}✗${NC} LLARS frontend not accessible (port 55080)"
fi

# Summary
echo ""
echo -e "${BLUE}Test Credentials:${NC}"
echo "  admin      / admin123 (admin)"
echo "  akadmin    / admin123 (admin)"
echo "  researcher / admin123 (user)"
echo "  evaluator  / admin123 (user)"

echo ""
echo -e "${GREEN}Verification complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Access Authentik UI: http://localhost:55095"
echo "  2. Login with: akadmin / admin123"
echo "  3. Test LLARS login: http://localhost:55080/login"
