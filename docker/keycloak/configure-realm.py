#!/usr/bin/env python3
"""
Keycloak Realm Configuration Script

This script generates the final realm-import.json from realm-import-template.json
by replacing placeholders with environment variables.

This ensures:
- No hardcoded secrets in Git
- Different configurations for dev/prod
- Secure secret management

Usage:
    python configure-realm.py

Environment Variables:
    PROJECT_STATE - development or production
    KEYCLOAK_SSL_REQUIRED - none, external, or all
    KEYCLOAK_VERIFY_EMAIL - true or false
    KEYCLOAK_REGISTRATION_ALLOWED - true or false
    KEYCLOAK_BRUTE_FORCE_PROTECTED - true or false
    KEYCLOAK_FAILURE_FACTOR - number of failures before lockout
    KEYCLOAK_MAX_FAILURE_WAIT_SECONDS - lockout duration
    KEYCLOAK_ACCESS_TOKEN_LIFESPAN - token lifespan in seconds
    KEYCLOAK_SSO_SESSION_IDLE_TIMEOUT - session idle timeout
    KEYCLOAK_SSO_SESSION_MAX_LIFESPAN - max session lifespan
    PROJECT_HOST - hostname for allowed origins
    KEYCLOAK_BACKEND_CLIENT_SECRET - backend client secret
"""

import os
import json
import sys


def get_env(key, default=None, required=False):
    """Get environment variable with optional default and required check"""
    value = os.environ.get(key, default)
    if required and not value:
        print(f"ERROR: Required environment variable {key} is not set")
        sys.exit(1)
    return value


def str_to_bool(value):
    """Convert string to boolean"""
    if isinstance(value, bool):
        return value
    return value.lower() in ('true', '1', 'yes', 'on')


def main():
    # Get configuration from environment
    project_state = get_env('PROJECT_STATE', 'development')
    is_production = project_state == 'production'

    print(f"Configuring Keycloak realm for: {project_state}")

    # Load template
    template_path = '/opt/keycloak/import-config/realm-import-template.json'
    output_path = '/opt/keycloak/data/import/realm-import.json'

    try:
        with open(template_path, 'r') as f:
            realm_config = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Template file not found: {template_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in template: {e}")
        sys.exit(1)

    # ============================================
    # Security Settings
    # ============================================
    realm_config['sslRequired'] = get_env('KEYCLOAK_SSL_REQUIRED', 'all' if is_production else 'none')
    realm_config['verifyEmail'] = str_to_bool(get_env('KEYCLOAK_VERIFY_EMAIL', 'true' if is_production else 'false'))
    realm_config['registrationAllowed'] = str_to_bool(get_env('KEYCLOAK_REGISTRATION_ALLOWED', 'false' if is_production else 'true'))

    # Brute force protection
    realm_config['bruteForceProtected'] = str_to_bool(get_env('KEYCLOAK_BRUTE_FORCE_PROTECTED', 'true'))
    realm_config['failureFactor'] = int(get_env('KEYCLOAK_FAILURE_FACTOR', '5' if is_production else '10'))
    realm_config['maxFailureWaitSeconds'] = int(get_env('KEYCLOAK_MAX_FAILURE_WAIT_SECONDS', '900' if is_production else '300'))

    # Token lifespans
    realm_config['accessTokenLifespan'] = int(get_env('KEYCLOAK_ACCESS_TOKEN_LIFESPAN', '300' if is_production else '1800'))
    realm_config['ssoSessionIdleTimeout'] = int(get_env('KEYCLOAK_SSO_SESSION_IDLE_TIMEOUT', '1800' if is_production else '36000'))
    realm_config['ssoSessionMaxLifespan'] = int(get_env('KEYCLOAK_SSO_SESSION_MAX_LIFESPAN', '36000'))

    # ============================================
    # CORS / Allowed Origins
    # ============================================
    project_host = get_env('PROJECT_HOST', 'localhost')

    # Update CORS origins for both clients
    if is_production:
        allowed_origins = [f"https://{project_host}"]
        redirect_uris = [
            f"https://{project_host}/*"
        ]
    else:
        # Development: Allow multiple origins
        allowed_origins = [
            f"http://{project_host}",
            f"http://{project_host}:55080",
            f"http://{project_host}:55173",
            "http://127.0.0.1",
            "http://127.0.0.1:55080",
            "http://127.0.0.1:55173"
        ]
        redirect_uris = [
            f"http://{project_host}/*",
            f"http://{project_host}:55080/*",
            f"http://{project_host}:55173/*",
            "http://127.0.0.1/*",
            "http://127.0.0.1:55080/*",
            "http://127.0.0.1:55173/*"
        ]

    # Update clients
    for client in realm_config.get('clients', []):
        if client['clientId'] == 'llars-frontend':
            client['webOrigins'] = allowed_origins
            client['redirectUris'] = redirect_uris
        elif client['clientId'] == 'llars-backend':
            client['webOrigins'] = allowed_origins
            client['redirectUris'] = redirect_uris[:3] if is_production else redirect_uris
            # Set backend client secret from environment
            backend_secret = get_env('KEYCLOAK_BACKEND_CLIENT_SECRET', required=True)
            client['secret'] = backend_secret

    # ============================================
    # Remove default admin user in production
    # ============================================
    if is_production:
        # Remove hardcoded users (admin will be created via KEYCLOAK_ADMIN env var)
        realm_config['users'] = []
        print("Production mode: Removed hardcoded users (use KEYCLOAK_ADMIN env vars)")
    else:
        # Development: Keep default admin user for convenience
        print("Development mode: Keeping default admin user")

    # ============================================
    # Security Headers
    # ============================================
    if 'browserSecurityHeaders' not in realm_config:
        realm_config['browserSecurityHeaders'] = {}

    if is_production:
        realm_config['browserSecurityHeaders'].update({
            'contentSecurityPolicy': "frame-src 'self'; frame-ancestors 'self'; object-src 'none';",
            'strictTransportSecurity': 'max-age=31536000; includeSubDomains',
            'xContentTypeOptions': 'nosniff',
            'xFrameOptions': 'SAMEORIGIN',
            'xXSSProtection': '1; mode=block',
            'xRobotsTag': 'none'
        })
    else:
        # Development: More permissive for testing
        realm_config['browserSecurityHeaders'].update({
            'contentSecurityPolicy': f"frame-src 'self' http://{project_host}:* http://127.0.0.1:*; frame-ancestors 'self' http://{project_host}:* http://127.0.0.1:*; object-src 'none';",
            'xContentTypeOptions': 'nosniff',
            'xFrameOptions': 'SAMEORIGIN',
            'xXSSProtection': '1; mode=block'
        })

    # ============================================
    # Save configured realm
    # ============================================
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        with open(output_path, 'w') as f:
            json.dump(realm_config, f, indent=2)
        print(f"Successfully generated realm configuration: {output_path}")
        print(f"  - SSL Required: {realm_config['sslRequired']}")
        print(f"  - Email Verification: {realm_config['verifyEmail']}")
        print(f"  - Registration Allowed: {realm_config['registrationAllowed']}")
        print(f"  - Access Token Lifespan: {realm_config['accessTokenLifespan']}s")
        print(f"  - Allowed Origins: {allowed_origins}")
    except Exception as e:
        print(f"ERROR: Failed to write realm configuration: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
