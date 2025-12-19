#!/bin/bash

#########################################
# LLARS Authentik Manual Setup Script
#########################################
# This script manually configures Authentik with:
# - OAuth2 Providers (backend + frontend)
# - Applications
# - Authentication Flow
# - Test Users
#########################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Check if docker compose is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if authentik container is running (matches both "running" and "healthy")
if ! docker compose ps | grep -q "authentik-server.*\(running\|healthy\)"; then
    print_error "Authentik server is not running. Start it with: docker compose up -d"
    exit 1
fi

print_info "Starting Authentik setup for LLARS..."

#########################################
# 1. Create Authentication Flow
#########################################
print_section "1. Creating Authentication Flow"

docker compose exec -T authentik-server ak shell <<'EOF'
from authentik.flows.models import Flow, FlowStageBinding, FlowDesignation
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password.models import PasswordStage
from authentik.stages.user_login.models import UserLoginStage

print("[1/4] Creating authentication flow...")

# Create or get the flow
flow, created = Flow.objects.get_or_create(
    slug='llars-api-authentication',
    defaults={
        'name': 'LLARS API Authentication',
        'designation': FlowDesignation.AUTHENTICATION,
        'title': 'LLARS API Login'
    }
)

if created:
    print("  ✓ Created new flow: llars-api-authentication")
else:
    print("  ℹ Flow already exists: llars-api-authentication")

# Create identification stage
print("[2/4] Creating identification stage...")
id_stage, created = IdentificationStage.objects.get_or_create(
    name='llars-api-identification',
    defaults={
        'user_fields': [UserFields.USERNAME, UserFields.E_MAIL],
        'sources': []
    }
)
if created:
    print("  ✓ Created identification stage")
else:
    print("  ℹ Identification stage already exists")

# Create password stage
print("[3/4] Creating password stage...")
pw_stage, created = PasswordStage.objects.get_or_create(
    name='llars-api-password',
    defaults={
        'backends': ['authentik.core.auth.InbuiltBackend']
    }
)
if created:
    print("  ✓ Created password stage")
else:
    print("  ℹ Password stage already exists")

# Create user login stage
print("[4/4] Creating user login stage...")
login_stage, created = UserLoginStage.objects.get_or_create(
    name='llars-api-user-login',
    defaults={
        'session_duration': 'seconds=0'  # Use default session duration
    }
)
if created:
    print("  ✓ Created user login stage")
else:
    print("  ℹ User login stage already exists")

# Bind stages to flow (if not already bound)
existing_bindings = FlowStageBinding.objects.filter(target=flow).count()
if existing_bindings == 0:
    print("Binding stages to flow...")
    FlowStageBinding.objects.create(target=flow, stage=id_stage, order=10)
    FlowStageBinding.objects.create(target=flow, stage=pw_stage, order=20)
    FlowStageBinding.objects.create(target=flow, stage=login_stage, order=30)
    print("  ✓ Bound all stages to flow")
else:
    print(f"  ℹ Flow already has {existing_bindings} stage bindings")

print("\n✓ Authentication flow setup complete!")
EOF

print_success "Authentication flow created successfully"

#########################################
# 2. Create OAuth2 Providers
#########################################
print_section "2. Creating OAuth2 Providers"

docker compose exec -T authentik-server ak shell <<'EOF'
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping, ClientTypes
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow

print("[1/2] Creating backend OAuth2 provider (confidential)...")

# Get signing certificate
cert = CertificateKeyPair.objects.filter(name__icontains='self-signed').first()
if not cert:
    print("  ✗ ERROR: No self-signed certificate found!")
    exit(1)
print(f"  ✓ Using certificate: {cert.name}")

# Get authorization flow
auth_flow = Flow.objects.filter(slug='default-provider-authorization-implicit-consent').first()
if not auth_flow:
    auth_flow = Flow.objects.filter(designation='authorization').first()
if not auth_flow:
    print("  ✗ ERROR: No authorization flow found!")
    exit(1)
print(f"  ✓ Using authorization flow: {auth_flow.slug}")

# Create backend provider (confidential)
backend_provider, created = OAuth2Provider.objects.update_or_create(
    name='llars-backend-provider',
    defaults={
        'client_id': 'llars-backend',
        'client_secret': 'llars-backend-secret-change-in-production',
        'client_type': ClientTypes.CONFIDENTIAL,
        'authorization_flow': auth_flow,
        'signing_key': cert,
        'redirect_uris': 'http://localhost:55080/auth/callback\nhttp://localhost:8081/auth/callback',
    }
)

# Add OAuth2 scopes to backend provider
scopes = ScopeMapping.objects.filter(managed__startswith='goauthentik.io/providers/oauth2/scope-')
backend_provider.property_mappings.set(scopes)
backend_provider.save()

if created:
    print(f"  ✓ Created backend provider: {backend_provider.name}")
else:
    print(f"  ℹ Updated existing backend provider: {backend_provider.name}")

print(f"    - Client ID: {backend_provider.client_id}")
print(f"    - Client Type: {backend_provider.client_type}")
print(f"    - Redirect URIs: {backend_provider.redirect_uris[:50]}...")

# Create frontend provider (public)
print("\n[2/2] Creating frontend OAuth2 provider (public)...")
frontend_provider, created = OAuth2Provider.objects.update_or_create(
    name='llars-frontend-provider',
    defaults={
        'client_id': 'llars-frontend',
        'client_type': ClientTypes.PUBLIC,
        'authorization_flow': auth_flow,
        'signing_key': cert,
        'redirect_uris': 'http://localhost:55080/\nhttp://localhost:55080/login',
    }
)

# Add OAuth2 scopes to frontend provider
frontend_provider.property_mappings.set(scopes)
frontend_provider.save()

if created:
    print(f"  ✓ Created frontend provider: {frontend_provider.name}")
else:
    print(f"  ℹ Updated existing frontend provider: {frontend_provider.name}")

print(f"    - Client ID: {frontend_provider.client_id}")
print(f"    - Client Type: {frontend_provider.client_type}")

print("\n✓ OAuth2 providers setup complete!")
EOF

print_success "OAuth2 providers created successfully"

#########################################
# 3. Create Applications
#########################################
print_section "3. Creating Applications"

docker compose exec -T authentik-server ak shell <<'EOF'
from authentik.core.models import Application
from authentik.providers.oauth2.models import OAuth2Provider

print("[1/2] Creating LLARS Backend application...")

backend_provider = OAuth2Provider.objects.get(name='llars-backend-provider')
backend_app, created = Application.objects.update_or_create(
    slug='llars-backend',
    defaults={
        'name': 'LLARS Backend',
        'provider': backend_provider,
    }
)

if created:
    print(f"  ✓ Created application: {backend_app.name}")
else:
    print(f"  ℹ Updated existing application: {backend_app.name}")

print("[2/2] Creating LLARS Frontend application...")

frontend_provider = OAuth2Provider.objects.get(name='llars-frontend-provider')
frontend_app, created = Application.objects.update_or_create(
    slug='llars-frontend',
    defaults={
        'name': 'LLARS Frontend',
        'provider': frontend_provider,
    }
)

if created:
    print(f"  ✓ Created application: {frontend_app.name}")
else:
    print(f"  ℹ Updated existing application: {frontend_app.name}")

print("\n✓ Applications setup complete!")
EOF

print_success "Applications created successfully"

#########################################
# 4. Create Users (environment-aware)
#########################################
print_section "4. Creating Users"

# Get environment variables
PROJECT_STATE="${PROJECT_STATE:-development}"
LLARS_ADMIN_PASSWORD="${LLARS_ADMIN_PASSWORD:-admin123}"

print_info "Environment: $PROJECT_STATE"

if [ "$PROJECT_STATE" = "production" ]; then
    print_info "Production mode: Creating only admin user with secure password"

    # Validate password is not the default
    if [ "$LLARS_ADMIN_PASSWORD" = "admin123" ] || [ "$LLARS_ADMIN_PASSWORD" = "CHANGE_ME_STRONG_ADMIN_PASSWORD_24CHARS" ]; then
        print_error "LLARS_ADMIN_PASSWORD is not set or uses default value!"
        print_error "Please set a strong password in .env before running setup."
        exit 1
    fi

    docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T authentik-server ak shell <<EOF
import os
from authentik.core.models import User, Group

admin_password = "$LLARS_ADMIN_PASSWORD"

print("Creating production admin user...")

# Get or create authentik Admins group
admin_group, _ = Group.objects.get_or_create(
    name='authentik Admins',
    defaults={'is_superuser': True}
)

# Create only admin user in production
user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'name': 'Administrator',
        'email': 'admin@localhost',
        'is_active': True
    }
)

# Set password
user.set_password(admin_password)
user.save()

# Add to admin group
if admin_group not in user.ak_groups.all():
    user.ak_groups.add(admin_group)
    user.save()

if created:
    print(f"  ✓ Created admin user")
else:
    print(f"  ℹ Updated existing admin user")
print(f"    - Added to admin group")

print("\n✓ Production user setup complete!")
print("\nAdmin Credentials:")
print("  - Username: admin")
print("  - Password: (from LLARS_ADMIN_PASSWORD)")
EOF
else
    print_info "Development mode: Creating test users (admin, researcher, viewer)"

    docker compose exec -T authentik-server ak shell <<EOF
import os
from authentik.core.models import User, Group

admin_password = "$LLARS_ADMIN_PASSWORD"

print(f"Creating test users with password from LLARS_ADMIN_PASSWORD...")

# Get or create authentik Admins group
admin_group, _ = Group.objects.get_or_create(
    name='authentik Admins',
    defaults={'is_superuser': True}
)

users_data = [
    {
        'username': 'admin',
        'name': 'Admin User',
        'email': 'admin@localhost',
        'is_admin': True
    },
    {
        'username': 'researcher',
        'name': 'Researcher User',
        'email': 'researcher@localhost',
        'is_admin': False
    },
    {
        'username': 'viewer',
        'name': 'Viewer User',
        'email': 'viewer@localhost',
        'is_admin': False
    }
]

for user_data in users_data:
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults={
            'name': user_data['name'],
            'email': user_data['email'],
            'is_active': True
        }
    )

    # Set password
    user.set_password(admin_password)
    user.save()

    # Add admin users to admin group
    if user_data['is_admin']:
        if admin_group not in user.ak_groups.all():
            user.ak_groups.add(admin_group)
            user.save()

    if created:
        print(f"  ✓ Created user: {user.username} ({user.email})")
    else:
        print(f"  ℹ Updated existing user: {user.username}")

    if user_data['is_admin']:
        print(f"    - Added to admin group")

print("\n✓ Development users setup complete!")
print("\nTest Credentials:")
print(f"  - admin / {admin_password[:3]}*** (admin)")
print(f"  - researcher / {admin_password[:3]}*** (researcher)")
print(f"  - viewer / {admin_password[:3]}*** (viewer)")
EOF
fi

print_success "Users created successfully"

#########################################
# 5. Create Admin API Token
#########################################
print_section "5. Creating Admin API Token"

print_info "Creating API token for LLARS admin operations..."

# Create token and capture it
API_TOKEN=$(docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import Token, User
admin = User.objects.filter(username='akadmin').first()
if admin:
    Token.objects.filter(identifier='llars-admin-api-token').delete()
    token = Token.objects.create(identifier='llars-admin-api-token', user=admin, intent='api', expiring=False, description='LLARS Admin API Token')
    print(token.key)
" 2>/dev/null | grep -v "^{" | tail -1)

if [ -n "$API_TOKEN" ] && [ "$API_TOKEN" != "None" ]; then
    print_success "API token created: ${API_TOKEN:0:20}..."

    # Update .env file if it exists
    ENV_FILE=".env"
    if [ -f "$ENV_FILE" ]; then
        # Remove old token if exists
        sed -i.bak '/^AUTHENTIK_API_TOKEN=/d' "$ENV_FILE" 2>/dev/null || true
        # Add new token
        echo "AUTHENTIK_API_TOKEN=$API_TOKEN" >> "$ENV_FILE"
        print_success "Token added to $ENV_FILE"
        print_warning "Restart Flask service to apply: docker restart llars_flask_service"
    else
        print_warning ".env file not found. Add this to your .env:"
        echo "  AUTHENTIK_API_TOKEN=$API_TOKEN"
    fi
else
    print_warning "Could not create API token. User creation in admin panel may not work with Authentik."
fi

#########################################
# 6. Verify Setup
#########################################
print_section "6. Verifying Setup"

docker compose exec -T authentik-server ak shell <<'EOF'
from authentik.flows.models import Flow
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.core.models import Application, User

print("Checking configuration...")

# Check flow
flows = Flow.objects.filter(slug='llars-api-authentication').count()
print(f"  ✓ Authentication flows: {flows}")

# Check providers
providers = OAuth2Provider.objects.filter(name__icontains='llars').count()
print(f"  ✓ OAuth2 providers: {providers}")

# Check applications
apps = Application.objects.filter(slug__icontains='llars').count()
print(f"  ✓ Applications: {apps}")

# Check users
users = User.objects.filter(username__in=['admin', 'akadmin', 'researcher', 'viewer']).count()
print(f"  ✓ Test users: {users}")

print("\n✓ Verification complete!")
EOF

print_success "Setup verification completed"

#########################################
# Summary
#########################################
print_section "Setup Complete!"

echo ""
echo -e "${GREEN}Authentik has been configured with:${NC}"
echo ""
echo -e "${BLUE}Authentication Flow:${NC}"
echo "  • llars-api-authentication (Identification → Password → Login)"
echo ""
echo -e "${BLUE}OAuth2 Providers:${NC}"
echo "  • llars-backend-provider (confidential, RS256)"
echo "    - Client ID: llars-backend"
echo "  • llars-frontend-provider (public, RS256)"
echo "    - Client ID: llars-frontend"
echo ""
echo -e "${BLUE}Applications:${NC}"
echo "  • LLARS Backend (linked to backend provider)"
echo "  • LLARS Frontend (linked to frontend provider)"
echo ""
echo -e "${BLUE}Users (Environment: $PROJECT_STATE):${NC}"
if [ "$PROJECT_STATE" = "production" ]; then
    echo "  • admin / (LLARS_ADMIN_PASSWORD) - Administrator"
    echo ""
    echo -e "${YELLOW}Production Mode Active:${NC}"
    echo "  • Only admin user created"
    echo "  • Password set from LLARS_ADMIN_PASSWORD environment variable"
else
    echo "  • admin / (LLARS_ADMIN_PASSWORD) - Administrator"
    echo "  • researcher / (LLARS_ADMIN_PASSWORD) - Researcher"
    echo "  • viewer / (LLARS_ADMIN_PASSWORD) - Viewer"
    echo ""
    echo -e "${YELLOW}Development Mode Active:${NC}"
    echo "  • All test users created with same password"
    echo "  • Default password: admin123"
fi
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
if [ "$PROJECT_STATE" = "production" ]; then
    echo "  1. Test login at your production URL"
    echo "  2. Login with: admin / (your LLARS_ADMIN_PASSWORD)"
else
    echo "  1. Access Authentik UI: http://localhost:55095"
    echo "  2. Login with: admin / admin123"
    echo "  3. Verify providers in: Applications → Providers"
    echo "  4. Test LLARS login: http://localhost:55080/login"
fi
echo ""

print_success "Authentik setup completed successfully!"
