#!/bin/bash
set -e

echo "======================================="
echo "  Authentik Auto-Configuration Script"
echo "  Using 'ak shell' for reliable setup"
echo "======================================="

# Environment variables
BACKEND_CLIENT_ID="${AUTHENTIK_BACKEND_CLIENT_ID:-llars-backend}"
BACKEND_CLIENT_SECRET="${AUTHENTIK_BACKEND_CLIENT_SECRET:-llars-backend-secret-change-in-production}"
# Use LLARS_ADMIN_PASSWORD for LLARS users (admin, researcher, evaluator)
# Falls back to AUTHENTIK_BOOTSTRAP_PASSWORD for backwards compatibility
ADMIN_PASSWORD="${LLARS_ADMIN_PASSWORD:-${AUTHENTIK_BOOTSTRAP_PASSWORD:-admin123}}"
# IJCAI reviewer password (dev-only users)
IJCAI_REVIEWER_PASSWORD="${IJCAI_REVIEWER_PASSWORD:-ijcai_reviewer_123}"

MATOMO_CLIENT_ID="${AUTHENTIK_MATOMO_CLIENT_ID:-llars-matomo}"
MATOMO_CLIENT_SECRET="${AUTHENTIK_MATOMO_CLIENT_SECRET:-llars-matomo-secret-change-in-production}"
MATOMO_APP_SLUG="${AUTHENTIK_MATOMO_APP_SLUG:-llars-matomo}"

PROJECT_STATE="${PROJECT_STATE:-development}"
PROJECT_URL="${PROJECT_URL:-}"
PROJECT_HOST="${PROJECT_HOST:-localhost}"
NGINX_EXTERNAL_PORT="${NGINX_EXTERNAL_PORT:-80}"

AK_PYTHON="/ak-root/venv/bin/python"
if [ ! -x "$AK_PYTHON" ]; then
  echo "WARN: $AK_PYTHON not found, falling back to system python"
  AK_PYTHON="python"
fi

ak_shell() {
  "$AK_PYTHON" -m manage shell -c "$1"
}

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

ak_shell "
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

ak_shell "
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow, FlowDesignation
from authentik.core.models import Application
import time

def get_backend_auth_flow():
    # Backend login is server-to-server and cannot click consent.
    # Always prefer an implicit/non-interactive authorization flow.
    flow = Flow.objects.filter(slug='default-provider-authorization-implicit-consent').first()
    if flow:
        return flow

    flow = Flow.objects.filter(slug='llars-provider-authorization-implicit').first()
    if flow:
        return flow

    flow = Flow.objects.create(
        slug='llars-provider-authorization-implicit',
        name='LLARS Provider Authorization (Implicit)',
        designation=FlowDesignation.AUTHORIZATION,
        title='LLARS Authorization'
    )
    return flow

def get_default_scopes():
    scopes = ScopeMapping.objects.none()
    # Scope mappings may not be immediately available after Authentik bootstrap.
    for _ in range(15):
        scopes = ScopeMapping.objects.filter(managed__startswith='goauthentik.io/providers/oauth2/scope-')
        if scopes.exists():
            return scopes
        time.sleep(1)
    return scopes

cert = CertificateKeyPair.objects.filter(name__icontains='Self-signed').first()
if not cert:
    cert = CertificateKeyPair.objects.first()
if cert:
    print(f'  Using certificate: {cert.name}')
else:
    print('  Warning: No certificate found!')

auth_flow = get_backend_auth_flow()
print(f'  Using backend authorization flow: {auth_flow.slug}')

scopes = get_default_scopes()
if not scopes.exists():
    raise Exception('No OAuth2 scope mappings found for llars-backend')

desired_redirects = [
    {'matching_mode': 'strict', 'url': 'http://authentik-server:9000/'},
]

provider = OAuth2Provider.objects.filter(name='llars-backend').first()
if provider:
    provider.client_id = '$BACKEND_CLIENT_ID'
    provider.client_secret = '$BACKEND_CLIENT_SECRET'
    provider.client_type = 'confidential'
    provider.authorization_flow = auth_flow
    provider.signing_key = cert
    provider._redirect_uris = desired_redirects
    provider.save()
    print('  OAuth2 provider already exists, updated configuration')
else:
    provider = OAuth2Provider.objects.create(
        name='llars-backend',
        client_id='$BACKEND_CLIENT_ID',
        client_secret='$BACKEND_CLIENT_SECRET',
        client_type='confidential',
        authorization_flow=auth_flow,
        signing_key=cert,
        _redirect_uris=desired_redirects
    )
    print(f'  Created provider: {provider.name}')

provider.property_mappings.set(scopes)
provider.save()
print(f'  Added {scopes.count()} scope mappings')

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
    app.provider = provider
    app.save()
    print(f'  Updated application: {app.slug}')
"

echo "[4/7] Creating OAuth2 provider 'llars-matomo'..."

ak_shell "
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow, FlowDesignation
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
    auth_flow = Flow.objects.filter(designation=FlowDesignation.AUTHORIZATION).first()
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

ak_shell "
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
    echo "[6/7] Creating additional users (researcher, evaluator, chatbot_manager, ijcai_reviewer_1, ijcai_reviewer_2) - DEVELOPMENT MODE..."

    ak_shell "
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

# Evaluator user
evaluator, created = User.objects.get_or_create(
    username='evaluator',
    defaults={
        'name': 'Evaluator User',
        'email': 'evaluator@localhost',
        'is_active': True
    }
)
if created:
    evaluator.set_password('$ADMIN_PASSWORD')
    evaluator.save()
    print('  Created evaluator user')
else:
    print('  Evaluator user already exists')

# Chatbot Manager user
chatbot_manager, created = User.objects.get_or_create(
    username='chatbot_manager',
    defaults={
        'name': 'Chatbot Manager',
        'email': 'chatbot_manager@localhost',
        'is_active': True
    }
)
if created:
    chatbot_manager.set_password('$ADMIN_PASSWORD')
    chatbot_manager.save()
    print('  Created chatbot_manager user')
else:
    print('  Chatbot Manager user already exists')

# IJCAI Reviewer 1
ijcai_reviewer_1, created = User.objects.get_or_create(
    username='ijcai_reviewer_1',
    defaults={
        'name': 'IJCAI Reviewer 1',
        'email': 'ijcai_reviewer_1@localhost',
        'is_active': True
    }
)
ijcai_reviewer_1.set_password('$IJCAI_REVIEWER_PASSWORD')
ijcai_reviewer_1.save()
if created:
    print('  Created ijcai_reviewer_1 user')
else:
    print('  Updated ijcai_reviewer_1 password')

# IJCAI Reviewer 2
ijcai_reviewer_2, created = User.objects.get_or_create(
    username='ijcai_reviewer_2',
    defaults={
        'name': 'IJCAI Reviewer 2',
        'email': 'ijcai_reviewer_2@localhost',
        'is_active': True
    }
)
ijcai_reviewer_2.set_password('$IJCAI_REVIEWER_PASSWORD')
ijcai_reviewer_2.save()
if created:
    print('  Created ijcai_reviewer_2 user')
else:
    print('  Updated ijcai_reviewer_2 password')
"
else
    echo "[6/7] Skipping dev users (researcher, evaluator, chatbot_manager, ijcai_reviewer_1, ijcai_reviewer_2) - PRODUCTION MODE"
fi

echo "[7/8] Creating Admin API Token for LLARS..."

# Use predefined token from env if available (for reproducible setups)
PREDEFINED_TOKEN="${AUTHENTIK_API_TOKEN:-}"

ak_shell "
from authentik.core.models import Token, User

# Get the akadmin (bootstrap admin) user
admin = User.objects.filter(username='akadmin').first()
if not admin:
    admin = User.objects.filter(username='admin').first()

if admin:
    # Delete old token if exists
    Token.objects.filter(identifier='llars-admin-api-token').delete()

    # Create new API token (with predefined key if provided)
    predefined_key = '$PREDEFINED_TOKEN' if '$PREDEFINED_TOKEN' else None
    if predefined_key:
        token = Token.objects.create(
            identifier='llars-admin-api-token',
            user=admin,
            intent='api',
            expiring=False,
            key=predefined_key,
            description='LLARS Admin API Token for user management'
        )
        print(f'  Token created with predefined key')
    else:
        token = Token.objects.create(
            identifier='llars-admin-api-token',
            user=admin,
            intent='api',
            expiring=False,
            description='LLARS Admin API Token for user management'
        )
        print(f'  Token created: {token.key}')
        print(f'  Add to .env: AUTHENTIK_API_TOKEN={token.key}')
else:
    print('  ERROR: No admin user found')
"

echo "[8/8] Verifying configuration..."

ak_shell "
from authentik.flows.models import Flow
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.core.models import User, Application

# Verify flow
flow = Flow.objects.filter(slug='llars-api-authentication').first()
print(f'  Flow llars-api-authentication: {\"OK\" if flow else \"MISSING\"}')"

ak_shell "
from authentik.providers.oauth2.models import OAuth2Provider
provider = OAuth2Provider.objects.filter(name='llars-backend').first()
print(f'  OAuth2 Provider llars-backend: {\"OK\" if provider else \"MISSING\"}')"

ak_shell "
from authentik.providers.oauth2.models import OAuth2Provider
provider = OAuth2Provider.objects.filter(name='llars-matomo').first()
print(f'  OAuth2 Provider llars-matomo: {\"OK\" if provider else \"MISSING\"}')"

ak_shell "
from authentik.core.models import Application
app = Application.objects.filter(slug='llars-backend').first()
print(f'  Application llars-backend: {\"OK\" if app else \"MISSING\"}')"

ak_shell "
from authentik.core.models import Application
app = Application.objects.filter(slug='$MATOMO_APP_SLUG').first()
print(f'  Application $MATOMO_APP_SLUG: {\"OK\" if app else \"MISSING\"}')"

ak_shell "
from authentik.core.models import User
admin = User.objects.filter(username='admin').first()
print(f'  User admin: {\"OK\" if admin else \"MISSING\"}')"

echo ""
echo "======================================="
echo "  Authentik Configuration Complete!"
echo "  Mode: $PROJECT_STATE"
echo "======================================="
echo ""
echo "Seeded login accounts:"
echo "  Username: admin (password from LLARS_ADMIN_PASSWORD env var)"
if [ "$PROJECT_STATE" = "development" ]; then
echo ""
echo "  Username: researcher (password from LLARS_ADMIN_PASSWORD env var)"
echo ""
echo "  Username: evaluator (password from LLARS_ADMIN_PASSWORD env var)"
echo ""
echo "  Username: chatbot_manager (password from LLARS_ADMIN_PASSWORD env var)"
echo ""
echo "  Username: ijcai_reviewer_1 (password from IJCAI_REVIEWER_PASSWORD env var)"
echo ""
echo "  Username: ijcai_reviewer_2 (password from IJCAI_REVIEWER_PASSWORD env var)"
fi
echo ""
echo "Authentik Admin UI: http://localhost:55095"
echo ""
