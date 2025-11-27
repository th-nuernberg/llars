#!/usr/bin/env python3
"""
Authentik Auto-Configuration Script (API-based)
Automatically configures Authentik with OAuth2 providers, applications, flows and test users.
Uses Authentik's REST API instead of Django shell for reliability.
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

print("🔧 Authentik Auto-Configuration Script (API-based)")
print("=" * 50)


def wait_for_authentik(max_attempts=60):
    """Wait for Authentik to be ready"""
    print("⏳ Waiting for Authentik to be ready...")
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(f"{AUTHENTIK_URL}/api/v3/core/users/", timeout=5)
            if response.status_code in [200, 401, 403]:
                print("✅ Authentik is ready!")
                time.sleep(10)  # Additional wait for full initialization
                return True
        except requests.exceptions.RequestException:
            pass

        if attempt == max_attempts:
            print(f"❌ Authentik did not become ready in time")
            return False

        if attempt % 5 == 0:
            print(f"   Attempt {attempt}/{max_attempts}...")
        time.sleep(5)

    return False


def get_api_token_via_flow():
    """
    Authenticate as akadmin using the default flow and get an API token.
    Uses the same flow-based authentication that the LLARS backend uses.
    """
    print("🔑 Authenticating as akadmin to get API token...")

    try:
        # Create session to maintain cookies
        session = requests.Session()

        # Use the default authentication flow
        flow_slug = 'default-authentication-flow'
        flow_url = f"{AUTHENTIK_URL}/api/v3/flows/executor/{flow_slug}/"

        # Step 1: Start flow
        flow_response = session.get(
            flow_url,
            headers={'Accept': 'application/json'},
            timeout=10
        )

        if flow_response.status_code != 200:
            print(f"   ⚠️  Failed to start flow: {flow_response.status_code}")
            return None

        flow_data = flow_response.json()

        # Step 2: Submit username
        if flow_data.get('component') == 'ak-stage-identification':
            flow_response = session.post(
                flow_url,
                json={'uid_field': 'akadmin'},
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                timeout=10
            )

            if flow_response.status_code != 200:
                print(f"   ⚠️  Identification failed: {flow_response.status_code}")
                return None

            flow_data = flow_response.json()

        # Step 3: Submit password
        if flow_data.get('component') == 'ak-stage-password':
            flow_response = session.post(
                flow_url,
                json={'password': AUTHENTIK_BOOTSTRAP_PASSWORD},
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                timeout=10
            )

            if flow_response.status_code != 200:
                print(f"   ⚠️  Password validation failed: {flow_response.status_code}")
                return None

            flow_data = flow_response.json()

        # Flow completed successfully, we now have an authenticated session
        # Create an API token using the authenticated session
        token_response = session.post(
            f"{AUTHENTIK_URL}/api/v3/core/tokens/",
            json={
                'identifier': 'llars-setup-token',
                'intent': 'api',
                'description': 'LLARS Auto-Setup Token',
                'expiring': False
            },
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            timeout=10
        )

        if token_response.status_code in [200, 201]:
            token_data = token_response.json()
            token = token_data.get('key')
            if token:
                print(f"✅ API token obtained")
                return token

        # Try to get existing token
        tokens_response = session.get(
            f"{AUTHENTIK_URL}/api/v3/core/tokens/",
            headers={'Accept': 'application/json'},
            timeout=10
        )

        if tokens_response.status_code == 200:
            tokens = tokens_response.json().get('results', [])
            for t in tokens:
                if t.get('identifier') == 'llars-setup-token':
                    print(f"✅ Using existing API token")
                    return t.get('key')

        print(f"   ⚠️  Could not create or find API token")
        return None

    except Exception as e:
        print(f"   ⚠️  Error getting API token: {e}")
        return None


def call_api(method: str, endpoint: str, token: str, data: Optional[Dict] = None) -> Optional[Dict]:
    """Call Authentik API with proper error handling"""
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
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 400:
            # Check if it's a "unique constraint" error (already exists)
            error_detail = response.json()
            if isinstance(error_detail, dict) and any(
                'already exists' in str(v).lower() or 'unique' in str(v).lower()
                for v in error_detail.values()
            ):
                print(f"   ℹ️  Resource already exists")
                return {'already_exists': True}

        print(f"   API Error {response.status_code}: {response.text[:200]}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"   Request failed: {e}")
        return None


def get_or_create_flow(token: str, slug: str, name: str) -> Optional[str]:
    """Get or create authentication flow"""
    print(f"📋 Configuring flow: {name}...")

    # Check if flow exists
    result = call_api("GET", f"/api/v3/flows/instances/{slug}/", token)
    if result and 'pk' in result:
        print(f"   ℹ️  Flow already exists")
        return result['slug']

    # Create flow
    flow_data = {
        'name': name,
        'slug': slug,
        'designation': 'authentication',
        'title': name
    }

    result = call_api("POST", "/api/v3/flows/instances/", token, flow_data)
    if result and ('pk' in result or result.get('already_exists')):
        print(f"✅ Flow configured")
        return slug

    print(f"⚠️  Could not create flow")
    return None


def create_flow_stages(token: str, flow_slug: str) -> bool:
    """Create and bind stages to the API authentication flow"""
    print(f"🔗 Configuring stages for {flow_slug}...")

    try:
        # Get flow
        flow = call_api("GET", f"/api/v3/flows/instances/{flow_slug}/", token)
        if not flow or 'pk' not in flow:
            print(f"   ⚠️  Flow not found")
            return False

        flow_pk = flow['pk']

        # Create identification stage
        id_stage_data = {
            'name': 'llars-api-identification',
            'user_fields': ['username', 'email'],
            'show_source_labels': False
        }
        id_stage = call_api("POST", "/api/v3/stages/identification/", token, id_stage_data)

        # Create password stage
        pwd_stage_data = {
            'name': 'llars-api-password',
            'backends': ['django.contrib.auth.backends.ModelBackend']
        }
        pwd_stage = call_api("POST", "/api/v3/stages/password/", token, pwd_stage_data)

        # Create user login stage
        login_stage_data = {
            'name': 'llars-api-user-login',
            'session_duration': 'seconds=0'
        }
        login_stage = call_api("POST", "/api/v3/stages/user_login/", token, login_stage_data)

        # Bind stages to flow
        if id_stage and 'pk' in id_stage:
            binding_data = {
                'target': flow_pk,
                'stage': id_stage['pk'],
                'order': 10
            }
            call_api("POST", "/api/v3/flows/bindings/", token, binding_data)

        if pwd_stage and 'pk' in pwd_stage:
            binding_data = {
                'target': flow_pk,
                'stage': pwd_stage['pk'],
                'order': 20
            }
            call_api("POST", "/api/v3/flows/bindings/", token, binding_data)

        if login_stage and 'pk' in login_stage:
            binding_data = {
                'target': flow_pk,
                'stage': login_stage['pk'],
                'order': 30
            }
            call_api("POST", "/api/v3/flows/bindings/", token, binding_data)

        print(f"✅ Stages configured")
        return True

    except Exception as e:
        print(f"   ⚠️  Error configuring stages: {e}")
        return False


def get_certificate_pk(token: str) -> Optional[int]:
    """Get the self-signed certificate for RS256 signing"""
    result = call_api("GET", "/api/v3/crypto/certificatekeypairs/", token)
    if result and 'results' in result:
        for cert in result['results']:
            if 'self-signed' in cert.get('name', '').lower():
                return cert['pk']
    return None


def get_default_auth_flow_pk(token: str) -> Optional[str]:
    """Get the default authorization flow"""
    result = call_api("GET", "/api/v3/flows/instances/", token)
    if result and 'results' in result:
        for flow in result['results']:
            if flow.get('slug') == 'default-provider-authorization-implicit-consent':
                return flow['pk']
    return None


def create_oauth_provider(token: str, name: str, client_id: str,
                         client_type: str = "public", client_secret: str = "") -> Optional[int]:
    """Create OAuth2/OIDC Provider"""
    print(f"📦 Creating provider: {name}...")

    # Get required resources
    cert_pk = get_certificate_pk(token)
    auth_flow_pk = get_default_auth_flow_pk(token)

    if not cert_pk:
        print(f"   ⚠️  Self-signed certificate not found")
        return None

    if not auth_flow_pk:
        print(f"   ⚠️  Default authorization flow not found")
        return None

    # Check if provider exists
    result = call_api("GET", "/api/v3/providers/oauth2/", token)
    if result and 'results' in result:
        for provider in result['results']:
            if provider.get('name') == name or provider.get('client_id') == client_id:
                print(f"   ℹ️  Provider already exists (PK: {provider['pk']})")
                return provider['pk']

    # Create provider
    provider_data = {
        "name": name,
        "authorization_flow": auth_flow_pk,
        "client_type": client_type,
        "client_id": client_id,
        "redirect_uris": [
            {"matching_mode": "strict", "url": f"{BASE_URL}/*"},
            {"matching_mode": "strict", "url": "http://127.0.0.1:55080/*"},
            {"matching_mode": "strict", "url": f"{AUTHENTIK_URL}/"}
        ],
        "sub_mode": "hashed_user_id",
        "issuer_mode": "per_provider",
        "signing_key": cert_pk
    }

    if client_type == "confidential":
        provider_data["client_secret"] = client_secret

    result = call_api("POST", "/api/v3/providers/oauth2/", token, provider_data)

    if result and ('pk' in result or result.get('already_exists')):
        pk = result.get('pk')
        print(f"✅ Provider created (PK: {pk})")

        # Add scope mappings
        scopes_result = call_api("GET", "/api/v3/propertymappings/scope/", token)
        if scopes_result and 'results' in scopes_result:
            scope_pks = [s['pk'] for s in scopes_result['results']]
            if scope_pks and pk:
                # Update provider with scopes
                update_data = {"property_mappings": scope_pks}
                call_api("PATCH", f"/api/v3/providers/oauth2/{pk}/", token, update_data)
                print(f"   ✅ Added {len(scope_pks)} scope mappings")

        return pk
    else:
        print(f"⚠️  Could not create provider")
        return None


def create_application(token: str, name: str, slug: str, provider_pk: int,
                      launch_url: Optional[str] = None) -> bool:
    """Create Application"""
    print(f"📱 Creating application: {name}...")

    # Check if app exists
    result = call_api("GET", f"/api/v3/core/applications/{slug}/", token)
    if result and 'pk' in result:
        print(f"   ℹ️  Application already exists")
        return True

    # Create application
    app_data = {
        "name": name,
        "slug": slug,
        "provider": provider_pk
    }

    if launch_url:
        app_data["meta_launch_url"] = launch_url

    result = call_api("POST", "/api/v3/core/applications/", token, app_data)

    if result and ('pk' in result or result.get('already_exists')):
        print(f"✅ Application created")
        return True
    else:
        print(f"⚠️  Could not create application")
        return False


def create_user(token: str, username: str, email: str, password: str = "admin123") -> bool:
    """Create user via API and set password"""
    print(f"👤 Creating user: {username}...")

    # Note: User creation with password via API is tricky because
    # Authentik API doesn't accept password in the user creation endpoint
    # We need to use recovery flow or Django shell for password setting
    # For now, we'll create the user and log a warning

    user_data = {
        "username": username,
        "name": f"{username.capitalize()} User",
        "email": email,
        "is_active": True
    }

    result = call_api("POST", "/api/v3/core/users/", token, user_data)

    if result and ('pk' in result or result.get('already_exists')):
        print(f"✅ User created (password must be set via admin UI or recovery)")
        return True
    else:
        print(f"⚠️  Could not create user")
        return False


def main():
    # Wait for Authentik
    if not wait_for_authentik():
        sys.exit(1)

    # Get API token
    api_token = get_api_token_via_flow()
    if not api_token:
        print("❌ Could not obtain API token")
        print("📝 Please configure Authentik manually via web UI")
        print(f"   URL: {AUTHENTIK_URL}")
        print(f"   User: akadmin")
        print(f"   Password: {AUTHENTIK_BOOTSTRAP_PASSWORD}")
        sys.exit(0)  # Exit gracefully

    print("\n🚀 Starting automatic configuration...")

    # Create API authentication flow
    api_flow_slug = get_or_create_flow(
        api_token,
        'llars-api-authentication',
        'LLARS API Authentication'
    )

    if api_flow_slug:
        create_flow_stages(api_token, api_flow_slug)

    # Create Backend Provider (Confidential) - MUST match client_id expected by backend
    backend_provider_pk = create_oauth_provider(
        api_token,
        "llars-backend",  # Name matches client_id
        BACKEND_CLIENT_ID,
        "confidential",
        BACKEND_CLIENT_SECRET
    )

    # Create Frontend Provider (Public)
    frontend_provider_pk = create_oauth_provider(
        api_token,
        "llars-frontend",  # Name matches client_id
        FRONTEND_CLIENT_ID,
        "public"
    )

    # Create Applications
    if backend_provider_pk:
        create_application(api_token, "LLARS Backend", "llars-backend",
                         backend_provider_pk)

    if frontend_provider_pk:
        create_application(api_token, "LLARS Frontend", "llars-frontend",
                         frontend_provider_pk, BASE_URL)

    # Create test users (password must be set manually or via Django shell)
    print("\n👥 Creating test users...")
    create_user(api_token, "admin", "admin@llars.local")
    create_user(api_token, "researcher", "researcher@llars.local")
    create_user(api_token, "viewer", "viewer@llars.local")

    print("\n" + "=" * 50)
    print("✅ Authentik auto-configuration complete!")
    print(f"\n🎉 You can now log in to LLARS:")
    print(f"   URL: {BASE_URL}")
    print(f"   Authentik Admin: {AUTHENTIK_URL}")
    print(f"\n   Default user: akadmin")
    print(f"   Password: {AUTHENTIK_BOOTSTRAP_PASSWORD}")
    print(f"\n   ⚠️  Test users (admin, researcher, viewer) were created")
    print(f"   but passwords must be set via Authentik admin UI or recovery flow")
    print("=" * 50)


if __name__ == "__main__":
    main()
