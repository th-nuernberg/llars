#!/usr/bin/env python3
"""
Authentik Auto-Configuration Script
Automatically configures Authentik with OAuth2 providers, applications, and test users
"""

import os
import sys
import time
import json
import requests
from typing import Optional, Dict, Any

# Configuration from environment variables
AUTHENTIK_URL = os.getenv("AUTHENTIK_URL", "http://authentik-server:9000")
AUTHENTIK_BOOTSTRAP_EMAIL = os.getenv("AUTHENTIK_BOOTSTRAP_EMAIL", "admin@example.com")
AUTHENTIK_BOOTSTRAP_PASSWORD = os.getenv("AUTHENTIK_BOOTSTRAP_PASSWORD", "admin123")
FRONTEND_CLIENT_ID = os.getenv("AUTHENTIK_FRONTEND_CLIENT_ID", "llars-frontend")
BACKEND_CLIENT_ID = os.getenv("AUTHENTIK_BACKEND_CLIENT_ID", "llars-backend")
BACKEND_CLIENT_SECRET = os.getenv("AUTHENTIK_BACKEND_CLIENT_SECRET", "llars-backend-secret-change-in-production")
BASE_URL = os.getenv("BASE_URL", "http://localhost:55080")

print("🔧 Authentik Auto-Configuration Script")
print("=" * 50)

def wait_for_authentik(max_attempts=60):
    """Wait for Authentik to be ready"""
    print("⏳ Waiting for Authentik to be ready...")
    for attempt in range(1, max_attempts + 1):
        try:
            # Try the root URL or API endpoint instead of health check (which returns 404)
            response = requests.get(f"{AUTHENTIK_URL}/api/v3/core/users/", timeout=5)
            if response.status_code in [200, 401, 403]:  # Any of these means server is up
                print("✅ Authentik is ready!")
                time.sleep(10)  # Additional wait for full initialization
                return True
        except requests.exceptions.RequestException:
            pass

        if attempt == max_attempts:
            print(f"❌ Authentik did not become ready in time")
            return False

        if attempt % 5 == 0:  # Print every 5 attempts to reduce noise
            print(f"   Attempt {attempt}/{max_attempts}...")
        time.sleep(5)

    return False

def create_api_token_via_shell():
    """Create API token using Django shell"""
    print("🔑 Creating API token via Django shell...")

    # Python code to run in Django shell
    python_code = """
import json
from authentik.core.models import User, Token, TokenIntents

# Get or create akadmin user
try:
    user = User.objects.get(username='akadmin')
except User.DoesNotExist:
    print(json.dumps({'error': 'akadmin user not found'}))
    exit(1)

# Create or get API token
token, created = Token.objects.get_or_create(
    user=user,
    identifier='llars-setup-token',
    defaults={
        'intent': TokenIntents.INTENT_API,
        'description': 'LLARS Auto-Setup Token',
        'expiring': False
    }
)

print(json.dumps({
    'token': token.key,
    'created': created,
    'user': user.username
}))
"""

    # Execute via docker exec
    import subprocess
    try:
        result = subprocess.run(
            ['docker', 'compose', 'exec', '-T', 'authentik-server',
             'python', 'manage.py', 'shell'],
            input=python_code.encode(),
            capture_output=True,
            timeout=30
        )

        # Parse output - look for JSON in the output
        output = result.stdout.decode()
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('{') and 'token' in line:
                data = json.loads(line)
                token = data.get('token')
                if token:
                    print(f"✅ API token {'created' if data.get('created') else 'retrieved'}")
                    return token

        print(f"⚠️  Could not parse token from output")
        return None

    except Exception as e:
        print(f"⚠️  Error creating token: {e}")
        return None

def call_api(method: str, endpoint: str, token: str, data: Optional[Dict] = None) -> Optional[Dict]:
    """Call Authentik API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{AUTHENTIK_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"   API Error {response.status_code}: {response.text[:200]}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"   Request failed: {e}")
        return None

def check_existing_providers(token: str) -> bool:
    """Check if providers already exist"""
    print("🔍 Checking existing configuration...")
    result = call_api("GET", "/api/v3/providers/oauth2/", token)
    if result and 'results' in result:
        existing = [p['name'] for p in result['results'] if 'llars-' in p['name']]
        if existing:
            print(f"ℹ️  Found existing providers: {', '.join(existing)}")
            return True
    return False

def create_oauth_provider(token: str, name: str, client_id: str,
                         client_type: str = "public", client_secret: str = "") -> Optional[int]:
    """Create OAuth2/OIDC Provider"""
    print(f"📦 Creating {name}...")

    provider_data = {
        "name": name,
        "authorization_flow": "default-provider-authorization-explicit-consent",
        "client_type": client_type,
        "client_id": client_id,
        "redirect_uris": f"{BASE_URL}/*\nhttp://127.0.0.1:55080/*",
        "sub_mode": "hashed_user_id",
        "issuer_mode": "per_provider"
    }

    if client_type == "confidential":
        provider_data["client_secret"] = client_secret

    result = call_api("POST", "/api/v3/providers/oauth2/", token, provider_data)

    if result and 'pk' in result:
        print(f"✅ {name} created (PK: {result['pk']})")
        return result['pk']
    else:
        print(f"⚠️  Could not create {name}")
        return None

def create_application(token: str, name: str, slug: str, provider_pk: int,
                      launch_url: Optional[str] = None) -> bool:
    """Create Application"""
    print(f"📱 Creating application: {name}...")

    app_data = {
        "name": name,
        "slug": slug,
        "provider": provider_pk,
        "open_in_new_tab": False
    }

    if launch_url:
        app_data["launch_url"] = launch_url

    result = call_api("POST", "/api/v3/core/applications/", token, app_data)

    if result:
        print(f"✅ Application '{name}' created")
        return True
    else:
        print(f"⚠️  Could not create application '{name}'")
        return False

def create_provider_via_shell(name: str, client_id: str, client_type: str,
                             client_secret: str = "", redirect_uris: list = None) -> Optional[int]:
    """Create OAuth2 provider via Django shell with correct format"""
    print(f"📦 Creating {name} via Django shell...")

    if redirect_uris is None:
        redirect_uris = [f"{BASE_URL}/*", "http://127.0.0.1:55080/*"]

    # Build redirect_uris Python code
    redirect_uris_code = ",\n        ".join([
        f"RedirectURI(matching_mode=RedirectURIMatchingMode.STRICT, url='{uri}')"
        for uri in redirect_uris
    ])

    # Build provider defaults based on client type
    client_secret_field = f", 'client_secret': '{client_secret}'" if client_type == 'confidential' else ""

    python_code = f"""
import json
from authentik.providers.oauth2.models import OAuth2Provider, RedirectURI, RedirectURIMatchingMode
from authentik.flows.models import Flow

# Get flows
auth_flow = Flow.objects.get(slug='default-provider-authorization-explicit-consent')
invalid_flow = Flow.objects.get(slug='default-provider-invalidation-flow')

# Check if provider exists
try:
    provider = OAuth2Provider.objects.get(name='{name}')
    print(json.dumps({{'exists': True, 'pk': provider.pk, 'name': '{name}'}}))
except OAuth2Provider.DoesNotExist:
    # Create provider with correct redirect_uris format
    provider = OAuth2Provider.objects.create(
        name='{name}',
        authorization_flow=auth_flow,
        invalidation_flow=invalid_flow,
        client_type='{client_type}',
        client_id='{client_id}',
        redirect_uris=[
            {redirect_uris_code}
        ],
        sub_mode='hashed_user_id',
        issuer_mode='per_provider'{client_secret_field}
    )
    print(json.dumps({{'created': True, 'pk': provider.pk, 'name': '{name}'}}))
"""

    import subprocess
    try:
        result = subprocess.run(
            ['docker', 'compose', 'exec', '-T', 'authentik-server',
             'python', 'manage.py', 'shell'],
            input=python_code.encode(),
            capture_output=True,
            timeout=30
        )

        output = result.stdout.decode()
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('{') and ('pk' in line):
                data = json.loads(line)
                pk = data.get('pk')
                if pk:
                    print(f"✅ {name} {'exists' if data.get('exists') else 'created'} (PK: {pk})")
                    return pk

        print(f"⚠️  Could not parse provider PK from output")
        print(f"   Output: {output[:200]}")
        return None

    except Exception as e:
        print(f"⚠️  Error creating provider: {e}")
        return None

def create_application_via_shell(name: str, slug: str, provider_pk: int,
                                  launch_url: Optional[str] = None) -> bool:
    """Create Application via Django shell"""
    print(f"📱 Creating application: {name}...")

    launch_url_field = f", 'meta_launch_url': '{launch_url}'" if launch_url else ""

    python_code = f"""
import json
from authentik.core.models import Application
from authentik.providers.oauth2.models import OAuth2Provider

# Get provider
provider = OAuth2Provider.objects.get(pk={provider_pk})

# Check if app exists
try:
    app = Application.objects.get(slug='{slug}')
    print(json.dumps({{'exists': True, 'slug': '{slug}'}}))
except Application.DoesNotExist:
    # Create application
    app = Application.objects.create(
        name='{name}',
        slug='{slug}',
        provider=provider{launch_url_field}
    )
    print(json.dumps({{'created': True, 'slug': '{slug}'}}))
"""

    import subprocess
    try:
        result = subprocess.run(
            ['docker', 'compose', 'exec', '-T', 'authentik-server',
             'python', 'manage.py', 'shell'],
            input=python_code.encode(),
            capture_output=True,
            timeout=15
        )

        output = result.stdout.decode()
        if 'created' in output or 'exists' in output:
            print(f"✅ Application {name} ready")
            return True
        else:
            print(f"⚠️  Application creation unclear for {name}")
            return False

    except Exception as e:
        print(f"⚠️  Error creating application: {e}")
        return False

def create_user(token: str, username: str, email: str, password: str = "admin123") -> bool:
    """Create user via Django shell (password setting via API is complex)"""
    print(f"👤 Creating user: {username}...")

    python_code = f"""
import json
from authentik.core.models import User

# Check if user exists
try:
    user = User.objects.get(username='{username}')
    print(json.dumps({{'exists': True, 'username': '{username}'}}))
except User.DoesNotExist:
    # Create user
    user = User.objects.create(
        username='{username}',
        email='{email}',
        name='{username.capitalize()} User',
        is_active=True
    )
    user.set_password('{password}')
    user.save()
    print(json.dumps({{'created': True, 'username': '{username}'}}))
"""

    import subprocess
    try:
        result = subprocess.run(
            ['docker', 'compose', 'exec', '-T', 'authentik-server',
             'python', 'manage.py', 'shell'],
            input=python_code.encode(),
            capture_output=True,
            timeout=15
        )

        output = result.stdout.decode()
        if 'created' in output or 'exists' in output:
            print(f"✅ User {username} ready")
            return True
        else:
            print(f"⚠️  User creation unclear for {username}")
            return False

    except Exception as e:
        print(f"⚠️  Error with user {username}: {e}")
        return False

def configure_rs256_and_auth_flow():
    """Configure RS256 signing and API authentication flow"""
    print("🔐 Configuring RS256 signing and API authentication flow...")

    python_code = f"""
import json
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow, FlowStageBinding, FlowDesignation
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password.models import PasswordStage
from authentik.stages.user_login.models import UserLoginStage

# 1. Configure RS256 signing for all OAuth2 providers
cert = CertificateKeyPair.objects.filter(name__contains="Self-signed").first()
if cert:
    for provider in OAuth2Provider.objects.all():
        if provider.signing_key != cert:
            provider.signing_key = cert
            provider.save()
            print(f"RS256 configured for {{provider.name}}")
        else:
            print(f"RS256 already set for {{provider.name}}")
else:
    print("WARNING: Self-signed certificate not found")

# 2. Create API authentication flow (without MFA)
flow_slug = 'llars-api-authentication'
try:
    flow = Flow.objects.get(slug=flow_slug)
    print(f"Flow {{flow_slug}} already exists")
except Flow.DoesNotExist:
    flow = Flow.objects.create(
        name='LLARS API Authentication',
        slug=flow_slug,
        designation=FlowDesignation.AUTHENTICATION,
        title='LLARS API Login'
    )
    print(f"Created flow {{flow_slug}}")

    # Create stages
    # Identification Stage
    id_stage, _ = IdentificationStage.objects.get_or_create(
        name='llars-api-identification',
        defaults={{
            'user_fields': [UserFields.USERNAME, UserFields.EMAIL],
            'show_source_labels': False
        }}
    )

    # Password Stage
    pwd_stage, _ = PasswordStage.objects.get_or_create(
        name='llars-api-password',
        defaults={{}}
    )

    # Login Stage (use existing default)
    login_stage = UserLoginStage.objects.filter(name='default-authentication-login').first()
    if not login_stage:
        login_stage, _ = UserLoginStage.objects.get_or_create(
            name='llars-api-login',
            defaults={{}}
        )

    # Bind stages to flow
    FlowStageBinding.objects.get_or_create(
        target=flow, stage=id_stage, defaults={{'order': 10}}
    )
    FlowStageBinding.objects.get_or_create(
        target=flow, stage=pwd_stage, defaults={{'order': 20}}
    )
    FlowStageBinding.objects.get_or_create(
        target=flow, stage=login_stage, defaults={{'order': 30}}
    )
    print(f"Stages bound to flow")

# 3. Update redirect URIs to include internal URL for backend
for provider in OAuth2Provider.objects.filter(name__contains='backend'):
    from authentik.providers.oauth2.models import RedirectURI, RedirectURIMatchingMode
    internal_uri = 'http://authentik-server:9000/'
    existing_uris = [r.url for r in provider.redirect_uris]
    if internal_uri not in existing_uris:
        provider.redirect_uris.append(
            RedirectURI(matching_mode=RedirectURIMatchingMode.STRICT, url=internal_uri)
        )
        provider.save()
        print(f"Added internal redirect URI to {{provider.name}}")

print(json.dumps({{'success': True}}))
"""

    import subprocess
    try:
        result = subprocess.run(
            ['docker', 'compose', 'exec', '-T', 'authentik-server',
             'python', 'manage.py', 'shell'],
            input=python_code.encode(),
            capture_output=True,
            timeout=60
        )

        output = result.stdout.decode()
        if 'success' in output:
            print("✅ RS256 and API auth flow configured")
            return True
        else:
            print(f"⚠️  Configuration output: {output[:500]}")
            return False

    except Exception as e:
        print(f"⚠️  Error configuring RS256/flow: {e}")
        return False

def main():
    # Wait for Authentik
    if not wait_for_authentik():
        sys.exit(1)

    # Get API token
    api_token = create_api_token_via_shell()
    if not api_token:
        print("❌ Could not obtain API token")
        print("📝 Please configure Authentik manually via web UI")
        print(f"   URL: {AUTHENTIK_URL}")
        print(f"   User: akadmin")
        print(f"   Password: {AUTHENTIK_BOOTSTRAP_PASSWORD}")
        sys.exit(0)  # Exit gracefully, not an error

    # Check if already configured
    if check_existing_providers(api_token):
        print("✅ Authentik providers already exist")
        # Still configure RS256 and auth flow
        configure_rs256_and_auth_flow()
        sys.exit(0)

    print("🚀 Starting automatic configuration...")

    # Create Frontend Provider (Public)
    frontend_provider_pk = create_provider_via_shell(
        "llars-frontend-provider",
        FRONTEND_CLIENT_ID,
        "public"
    )

    # Create Backend Provider (Confidential)
    backend_provider_pk = create_provider_via_shell(
        "llars-backend-provider",
        BACKEND_CLIENT_ID,
        "confidential",
        BACKEND_CLIENT_SECRET
    )

    # Create Applications
    if frontend_provider_pk:
        create_application_via_shell("LLARS Frontend", "llars-frontend",
                                    frontend_provider_pk, BASE_URL)

    if backend_provider_pk:
        create_application_via_shell("LLARS Backend", "llars-backend",
                                    backend_provider_pk)

    # Create test users
    print("\n👥 Creating test users...")
    create_user(api_token, "admin", "admin@llars.local")
    create_user(api_token, "researcher", "researcher@llars.local")
    create_user(api_token, "viewer", "viewer@llars.local")

    print("\n" + "=" * 50)
    print("✅ Authentik auto-configuration complete!")
    print(f"\n🎉 You can now log in to LLARS:")
    print(f"   URL: {BASE_URL}")
    print(f"   Authentik Admin: http://localhost:55095")
    print(f"\n   Users (all with password 'admin123'):")
    print(f"   - akadmin (Authentik admin)")
    print(f"   - admin@llars.local")
    print(f"   - researcher@llars.local")
    print(f"   - viewer@llars.local")
    print("=" * 50)

if __name__ == "__main__":
    main()
