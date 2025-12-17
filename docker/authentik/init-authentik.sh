#!/bin/bash
set -e

echo "======================================="
echo "  Authentik Auto-Configuration Script"
echo "  Using 'ak shell' for reliable setup"
echo "======================================="

# Environment variables
BACKEND_CLIENT_ID="${AUTHENTIK_BACKEND_CLIENT_ID:-llars-backend}"
BACKEND_CLIENT_SECRET="${AUTHENTIK_BACKEND_CLIENT_SECRET:-llars-backend-secret-change-in-production}"
ADMIN_PASSWORD="${AUTHENTIK_BOOTSTRAP_PASSWORD:-admin123}"

MATOMO_CLIENT_ID="${AUTHENTIK_MATOMO_CLIENT_ID:-llars-matomo}"
MATOMO_CLIENT_SECRET="${AUTHENTIK_MATOMO_CLIENT_SECRET:-llars-matomo-secret-change-in-production}"
MATOMO_APP_SLUG="${AUTHENTIK_MATOMO_APP_SLUG:-llars-matomo}"

PROJECT_STATE="${PROJECT_STATE:-development}"
PROJECT_URL="${PROJECT_URL:-}"
PROJECT_HOST="${PROJECT_HOST:-localhost}"
NGINX_EXTERNAL_PORT="${NGINX_EXTERNAL_PORT:-80}"

BASE_URL="${PROJECT_URL%/}"
if [ -z "$BASE_URL" ]; then
  if [ "$PROJECT_STATE" = "production" ]; then
    BASE_URL="https://${PROJECT_HOST}"
  else
    BASE_URL="http://${PROJECT_HOST}:${NGINX_EXTERNAL_PORT}"
  fi
fi

MATOMO_REDIRECT_URI_MATOMO="${BASE_URL}/matomo/index.php?module=RebelOIDC&action=callback&provider=oidc"
MATOMO_REDIRECT_URI_ANALYTICS="${BASE_URL}/analytics/index.php?module=RebelOIDC&action=callback&provider=oidc"

echo ""
echo "Configuration:"
echo "  Backend Client ID: $BACKEND_CLIENT_ID"
echo "  Matomo OIDC Client ID: $MATOMO_CLIENT_ID"
echo "  Matomo Redirect URIs:"
echo "    - $MATOMO_REDIRECT_URI_MATOMO"
echo "    - $MATOMO_REDIRECT_URI_ANALYTICS"
echo "  Admin Password: (set from env)"
echo ""

# Wait for database to be fully ready
echo "[1/7] Waiting for database connection..."
sleep 5

# Run all configuration via ak shell (Python Django shell)
echo "[2/7] Creating authentication flow 'llars-api-authentication'..."

ak shell -c "
from authentik.flows.models import Flow, FlowStageBinding, FlowDesignation
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password.models import PasswordStage
from authentik.stages.user_login.models import UserLoginStage

# Check if flow already exists
existing = Flow.objects.filter(slug='llars-api-authentication').first()
if existing:
    print('  Flow already exists, skipping creation')
else:
    # Create flow
    flow = Flow.objects.create(
        slug='llars-api-authentication',
        name='LLARS API Authentication',
        designation=FlowDesignation.AUTHENTICATION,
        title='LLARS API Login'
    )
    print(f'  Created flow: {flow.slug}')

    # Create or get stages
    id_stage, created = IdentificationStage.objects.get_or_create(
        name='llars-api-identification',
        defaults={'user_fields': [UserFields.USERNAME, UserFields.E_MAIL]}
    )
    print(f'  Identification stage: {\"created\" if created else \"exists\"}')

    pw_stage, created = PasswordStage.objects.get_or_create(
        name='llars-api-password',
        defaults={'backends': ['authentik.core.auth.InbuiltBackend']}
    )
    print(f'  Password stage: {\"created\" if created else \"exists\"}')

    login_stage, created = UserLoginStage.objects.get_or_create(
        name='llars-api-user-login',
        defaults={'session_duration': 'seconds=0'}
    )
    print(f'  User login stage: {\"created\" if created else \"exists\"}')

    # Create bindings
    FlowStageBinding.objects.create(target=flow, stage=id_stage, order=10)
    FlowStageBinding.objects.create(target=flow, stage=pw_stage, order=20)
    FlowStageBinding.objects.create(target=flow, stage=login_stage, order=30)
    print('  Stage bindings created')
"

echo "[3/7] Creating OAuth2 provider 'llars-backend'..."

ak shell -c "
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.core.models import Application

# Check if provider already exists
existing = OAuth2Provider.objects.filter(name='llars-backend').first()
if existing:
    print('  OAuth2 provider already exists, skipping creation')
else:
    # Get signing certificate (self-signed)
    cert = CertificateKeyPair.objects.filter(name__icontains='Self-signed').first()
    if not cert:
        cert = CertificateKeyPair.objects.first()
    if cert:
        print(f'  Using certificate: {cert.name}')
    else:
        print('  Warning: No certificate found!')

    # Get authorization flow (implicit consent = no extra click)
    auth_flow = Flow.objects.filter(slug='default-provider-authorization-implicit-consent').first()
    if not auth_flow:
        auth_flow = Flow.objects.filter(slug='default-provider-authorization-explicit-consent').first()
    if auth_flow:
        print(f'  Using authorization flow: {auth_flow.slug}')

    # Create provider with authorization flow
    if not auth_flow:
        print('  ERROR: No authorization flow found! Login will not work.')
        raise Exception('No authorization flow found')

    provider = OAuth2Provider.objects.create(
        name='llars-backend',
        client_id='$BACKEND_CLIENT_ID',
        client_secret='$BACKEND_CLIENT_SECRET',
        client_type='confidential',
        authorization_flow=auth_flow,
        signing_key=cert
    )
    print(f'  Created provider: {provider.name}')

    # Add scope mappings
    scopes = ScopeMapping.objects.filter(managed__startswith='goauthentik.io/providers/oauth2/scope-')
    provider.property_mappings.set(scopes)
    provider.save()
    print(f'  Added {scopes.count()} scope mappings')

    # Create application linked to provider
    app, created = Application.objects.get_or_create(
        slug='llars-backend',
        defaults={
            'name': 'LLARS Backend',
            'provider': provider
        }
    )
    if created:
        print(f'  Created application: {app.slug}')
    else:
        # Link existing app to new provider
        app.provider = provider
        app.save()
        print(f'  Updated application: {app.slug}')
"

echo "[4/7] Creating OAuth2 provider 'llars-matomo'..."

ak shell -c "
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.core.models import Application

existing = OAuth2Provider.objects.filter(name='llars-matomo').first()
cert = CertificateKeyPair.objects.filter(name__icontains='Self-signed').first()
if not cert:
    cert = CertificateKeyPair.objects.first()
if cert:
    print(f'  Using certificate: {cert.name}')

auth_flow = Flow.objects.filter(slug='default-provider-authorization-implicit-consent').first()
if not auth_flow:
    auth_flow = Flow.objects.filter(slug='default-provider-authorization-explicit-consent').first()
if not auth_flow:
    print('  ERROR: No authorization flow found!')
    raise Exception('No authorization flow found')

desired_redirects = [
    {'matching_mode': 'strict', 'url': '$MATOMO_REDIRECT_URI_MATOMO'},
    {'matching_mode': 'strict', 'url': '$MATOMO_REDIRECT_URI_ANALYTICS'},
]

if existing:
    existing.client_id = '$MATOMO_CLIENT_ID'
    existing.client_secret = '$MATOMO_CLIENT_SECRET'
    existing.client_type = 'confidential'
    existing.authorization_flow = auth_flow
    existing.signing_key = cert
    existing._redirect_uris = desired_redirects
    existing.save()
    provider = existing
    print('  OAuth2 provider already exists, updated redirect URIs')
else:
    provider = OAuth2Provider.objects.create(
        name='llars-matomo',
        client_id='$MATOMO_CLIENT_ID',
        client_secret='$MATOMO_CLIENT_SECRET',
        client_type='confidential',
        authorization_flow=auth_flow,
        signing_key=cert,
        _redirect_uris=desired_redirects
    )
    print(f'  Created provider: {provider.name}')

scopes = ScopeMapping.objects.filter(managed__startswith='goauthentik.io/providers/oauth2/scope-')
provider.property_mappings.set(scopes)
provider.save()
print(f'  Added {scopes.count()} scope mappings')

app, created = Application.objects.get_or_create(
    slug='$MATOMO_APP_SLUG',
    defaults={
        'name': 'LLARS Matomo',
        'provider': provider
    }
)
if created:
    print(f'  Created application: {app.slug}')
else:
    app.provider = provider
    app.save()
    print(f'  Updated application: {app.slug}')
"

echo "[5/7] Creating admin user..."

ak shell -c "
from authentik.core.models import User, Group

# Create or update admin user
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'name': 'Admin User',
        'email': 'admin@localhost',
        'is_active': True
    }
)

if created:
    print('  Created admin user')
else:
    print('  Admin user already exists')

# Set password
admin.set_password('$ADMIN_PASSWORD')
admin.save()
print('  Password set for admin user')

# Add to admin group
admin_group = Group.objects.filter(name='authentik Admins').first()
if admin_group:
    admin.ak_groups.add(admin_group)
    admin.save()
    print('  Added admin to authentik Admins group')
else:
    print('  Warning: authentik Admins group not found')
"

if [ "$PROJECT_STATE" = "development" ]; then
    echo "[6/7] Creating additional users (researcher, viewer) - DEVELOPMENT MODE..."

    ak shell -c "
from authentik.core.models import User

# Researcher user
researcher, created = User.objects.get_or_create(
    username='researcher',
    defaults={
        'name': 'Researcher User',
        'email': 'researcher@localhost',
        'is_active': True
    }
)
if created:
    researcher.set_password('$ADMIN_PASSWORD')
    researcher.save()
    print('  Created researcher user')
else:
    print('  Researcher user already exists')

# Viewer user
viewer, created = User.objects.get_or_create(
    username='viewer',
    defaults={
        'name': 'Viewer User',
        'email': 'viewer@localhost',
        'is_active': True
    }
)
if created:
    viewer.set_password('$ADMIN_PASSWORD')
    viewer.save()
    print('  Created viewer user')
else:
    print('  Viewer user already exists')
"
else
    echo "[6/7] Skipping dev users (researcher, viewer) - PRODUCTION MODE"
fi

echo "[7/7] Verifying configuration..."

ak shell -c "
from authentik.flows.models import Flow
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.core.models import User, Application

# Verify flow
flow = Flow.objects.filter(slug='llars-api-authentication').first()
print(f'  Flow llars-api-authentication: {\"OK\" if flow else \"MISSING\"}')"

ak shell -c "
from authentik.providers.oauth2.models import OAuth2Provider
provider = OAuth2Provider.objects.filter(name='llars-backend').first()
print(f'  OAuth2 Provider llars-backend: {\"OK\" if provider else \"MISSING\"}')"

ak shell -c "
from authentik.providers.oauth2.models import OAuth2Provider
provider = OAuth2Provider.objects.filter(name='llars-matomo').first()
print(f'  OAuth2 Provider llars-matomo: {\"OK\" if provider else \"MISSING\"}')"

ak shell -c "
from authentik.core.models import Application
app = Application.objects.filter(slug='llars-backend').first()
print(f'  Application llars-backend: {\"OK\" if app else \"MISSING\"}')"

ak shell -c "
from authentik.core.models import Application
app = Application.objects.filter(slug='$MATOMO_APP_SLUG').first()
print(f'  Application $MATOMO_APP_SLUG: {\"OK\" if app else \"MISSING\"}')"

ak shell -c "
from authentik.core.models import User
admin = User.objects.filter(username='admin').first()
print(f'  User admin: {\"OK\" if admin else \"MISSING\"}')"

echo ""
echo "======================================="
echo "  Authentik Configuration Complete!"
echo "  Mode: $PROJECT_STATE"
echo "======================================="
echo ""
echo "Login credentials:"
echo "  Username: admin"
echo "  Password: $ADMIN_PASSWORD"
if [ "$PROJECT_STATE" = "development" ]; then
echo ""
echo "  Username: researcher"
echo "  Password: $ADMIN_PASSWORD"
echo ""
echo "  Username: viewer"
echo "  Password: $ADMIN_PASSWORD"
fi
echo ""
echo "Authentik Admin UI: http://localhost:55095"
echo ""
