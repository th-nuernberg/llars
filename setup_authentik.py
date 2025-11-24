#!/usr/bin/env python3
"""
Authentik Setup Script for LLARS
Creates applications, providers, and test users for Authentik OIDC authentication
"""

import requests
import time
import sys
import os
from typing import Optional

# Configuration from environment variables
AUTHENTIK_URL = os.getenv('AUTHENTIK_URL', 'http://localhost:55090')
AUTHENTIK_BOOTSTRAP_EMAIL = os.getenv('AUTHENTIK_BOOTSTRAP_EMAIL', 'admin@example.com')
AUTHENTIK_BOOTSTRAP_PASSWORD = os.getenv('AUTHENTIK_BOOTSTRAP_PASSWORD', 'admin123')
FRONTEND_CLIENT_ID = os.getenv('AUTHENTIK_FRONTEND_CLIENT_ID', 'llars-frontend')
BACKEND_CLIENT_ID = os.getenv('AUTHENTIK_BACKEND_CLIENT_ID', 'llars-backend')
BACKEND_CLIENT_SECRET = os.getenv('AUTHENTIK_BACKEND_CLIENT_SECRET', 'llars-backend-secret-change-in-production')

class AuthentikSetup:
    def __init__(self):
        self.base_url = AUTHENTIK_URL
        self.api_url = f"{self.base_url}/api/v3"
        self.token = None
        self.session = requests.Session()

    def wait_for_authentik(self, max_retries=30, delay=5):
        """Wait for Authentik to be ready"""
        print(f"⏳ Waiting for Authentik at {self.base_url}...")

        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/-/health/ready/", timeout=5)
                if response.status_code == 200:
                    print("✅ Authentik is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass

            if i < max_retries - 1:
                print(f"   Retry {i+1}/{max_retries}... waiting {delay}s")
                time.sleep(delay)

        print("❌ Authentik did not become ready in time")
        return False

    def get_admin_token(self):
        """Get API token using bootstrap credentials"""
        print("\n🔑 Logging in as admin...")

        try:
            response = self.session.post(
                f"{self.api_url}/flows/executor/default-authentication-flow/",
                json={
                    "uid_field": AUTHENTIK_BOOTSTRAP_EMAIL,
                    "password": AUTHENTIK_BOOTSTRAP_PASSWORD
                },
                headers={"Content-Type": "application/json"}
            )

            # Try alternative token endpoint
            token_response = self.session.post(
                f"{self.base_url}/application/o/token/",
                data={
                    "grant_type": "password",
                    "username": AUTHENTIK_BOOTSTRAP_EMAIL,
                    "password": AUTHENTIK_BOOTSTRAP_PASSWORD,
                    "client_id": "authentik",
                    "scope": "openid email profile"
                }
            )

            if token_response.status_code == 200:
                data = token_response.json()
                self.token = data.get('access_token')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                })
                print("✅ Admin login successful!")
                return True
            else:
                print(f"❌ Login failed: {token_response.status_code}")
                print(f"   Response: {token_response.text}")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def create_oauth_provider(self, name: str, client_id: str, client_type: str = "public") -> Optional[str]:
        """Create OAuth2/OIDC Provider"""
        print(f"\n🔧 Creating OAuth2 Provider '{name}'...")

        provider_data = {
            "name": name,
            "authentication_flow": None,  # Use default
            "authorization_flow": "default-provider-authorization-explicit-consent",
            "client_type": client_type,
            "client_id": client_id,
            "client_secret": BACKEND_CLIENT_SECRET if client_type == "confidential" else "",
            "access_code_validity": "minutes=1",
            "access_token_validity": "minutes=10",
            "refresh_token_validity": "days=30",
            "include_claims_in_id_token": True,
            "signing_key": None,  # Use default
            "redirect_uris": "http://localhost:55080/*\nhttp://127.0.0.1:55080/*",
            "sub_mode": "hashed_user_id",
            "issuer_mode": "per_provider"
        }

        try:
            # Check if provider exists
            response = self.session.get(f"{self.api_url}/providers/oauth2/")
            if response.status_code == 200:
                providers = response.json().get('results', [])
                for provider in providers:
                    if provider.get('client_id') == client_id:
                        print(f"   Provider '{name}' already exists")
                        return provider.get('pk')

            # Create provider
            response = self.session.post(
                f"{self.api_url}/providers/oauth2/",
                json=provider_data
            )

            if response.status_code in [200, 201]:
                provider_id = response.json().get('pk')
                print(f"✅ Provider '{name}' created with ID: {provider_id}")
                return provider_id
            else:
                print(f"⚠️  Failed to create provider: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error creating provider: {e}")
            return None

    def create_application(self, name: str, slug: str, provider_id: str) -> bool:
        """Create Application"""
        print(f"\n📱 Creating Application '{name}'...")

        app_data = {
            "name": name,
            "slug": slug,
            "provider": provider_id,
            "meta_launch_url": "http://localhost:55080",
            "policy_engine_mode": "any",
            "open_in_new_tab": False
        }

        try:
            # Check if application exists
            response = self.session.get(f"{self.api_url}/core/applications/")
            if response.status_code == 200:
                apps = response.json().get('results', [])
                for app in apps:
                    if app.get('slug') == slug:
                        print(f"   Application '{name}' already exists")
                        return True

            # Create application
            response = self.session.post(
                f"{self.api_url}/core/applications/",
                json=app_data
            )

            if response.status_code in [200, 201]:
                print(f"✅ Application '{name}' created")
                return True
            else:
                print(f"⚠️  Failed to create application: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error creating application: {e}")
            return False

    def create_test_user(self, username: str, email: str, password: str, name: str = "") -> bool:
        """Create test user"""
        print(f"\n👤 Creating test user '{username}'...")

        user_data = {
            "username": username,
            "name": name or username,
            "email": email,
            "is_active": True,
            "path": "users",
            "type": "internal"
        }

        try:
            # Check if user exists
            response = self.session.get(f"{self.api_url}/core/users/")
            if response.status_code == 200:
                users = response.json().get('results', [])
                for user in users:
                    if user.get('username') == username:
                        print(f"   User '{username}' already exists")
                        return True

            # Create user
            response = self.session.post(
                f"{self.api_url}/core/users/",
                json=user_data
            )

            if response.status_code in [200, 201]:
                user_id = response.json().get('pk')
                print(f"✅ User '{username}' created with ID: {user_id}")

                # Set password
                password_response = self.session.post(
                    f"{self.api_url}/core/users/{user_id}/set_password/",
                    json={"password": password}
                )

                if password_response.status_code in [200, 204]:
                    print(f"✅ Password set for user '{username}'")
                    return True
                else:
                    print(f"⚠️  Failed to set password: {password_response.status_code}")
                    return False
            else:
                print(f"⚠️  Failed to create user: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return False

    def setup_all(self):
        """Run complete setup"""
        print("=" * 60)
        print("🚀 LLARS Authentik Setup")
        print("=" * 60)

        # Wait for Authentik
        if not self.wait_for_authentik():
            print("\n❌ Setup failed: Authentik not ready")
            return False

        # Login as admin
        if not self.get_admin_token():
            print("\n❌ Setup failed: Could not login as admin")
            print("\n💡 Manual setup required:")
            print(f"   1. Open {self.base_url}")
            print(f"   2. Login with: {AUTHENTIK_BOOTSTRAP_EMAIL} / {AUTHENTIK_BOOTSTRAP_PASSWORD}")
            print("   3. Follow manual setup instructions")
            return False

        # Create providers
        frontend_provider_id = self.create_oauth_provider(
            name=f"{FRONTEND_CLIENT_ID}-provider",
            client_id=FRONTEND_CLIENT_ID,
            client_type="public"
        )

        backend_provider_id = self.create_oauth_provider(
            name=f"{BACKEND_CLIENT_ID}-provider",
            client_id=BACKEND_CLIENT_ID,
            client_type="confidential"
        )

        if not frontend_provider_id or not backend_provider_id:
            print("\n⚠️  Provider creation incomplete - manual configuration needed")
            return False

        # Create applications
        self.create_application(
            name="LLARS Frontend",
            slug=FRONTEND_CLIENT_ID,
            provider_id=frontend_provider_id
        )

        self.create_application(
            name="LLARS Backend",
            slug=BACKEND_CLIENT_ID,
            provider_id=backend_provider_id
        )

        # Create test users
        self.create_test_user(
            username="admin",
            email="admin@llars.local",
            password="admin123",
            name="Admin User"
        )

        self.create_test_user(
            username="researcher",
            email="researcher@llars.local",
            password="researcher123",
            name="Researcher User"
        )

        self.create_test_user(
            username="viewer",
            email="viewer@llars.local",
            password="viewer123",
            name="Viewer User"
        )

        print("\n" + "=" * 60)
        print("✅ Setup completed!")
        print("=" * 60)
        print("\n📝 Test Credentials:")
        print("   Admin:      admin / admin123")
        print("   Researcher: researcher / researcher123")
        print("   Viewer:     viewer / viewer123")
        print("\n🌐 URLs:")
        print(f"   Authentik Admin: {self.base_url}")
        print("   LLARS Frontend:  http://localhost:55080")
        print("\n💡 Next Steps:")
        print("   1. Open http://localhost:55080")
        print("   2. Click Login")
        print("   3. Use one of the test credentials above")
        print("=" * 60)

        return True

def main():
    setup = AuthentikSetup()

    try:
        success = setup.setup_all()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
