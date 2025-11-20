"""
Keycloak Token Validation Module
Provides functions for validating JWT tokens issued by Keycloak
"""

import os
import jwt
import requests
from functools import lru_cache
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from flask import request, jsonify


class KeycloakConfig:
    """Keycloak configuration from environment variables"""

    def __init__(self):
        self.url = os.environ.get('KEYCLOAK_URL', 'http://keycloak-service:8080')
        self.realm = os.environ.get('KEYCLOAK_REALM', 'llars')
        self.client_id = os.environ.get('KEYCLOAK_CLIENT_ID', 'llars-backend')
        self.client_secret = os.environ.get('KEYCLOAK_CLIENT_SECRET', '')

        # Construct well-known URLs
        self.realm_url = f"{self.url}/realms/{self.realm}"
        self.well_known_url = f"{self.realm_url}/.well-known/openid-configuration"
        self.certs_url = f"{self.realm_url}/protocol/openid-connect/certs"
        self.introspect_url = f"{self.realm_url}/protocol/openid-connect/token/introspect"
        self.userinfo_url = f"{self.realm_url}/protocol/openid-connect/userinfo"


keycloak_config = KeycloakConfig()


@lru_cache(maxsize=1)
def get_public_key() -> str:
    """
    Fetch and cache the Keycloak public key for JWT validation
    Uses LRU cache to avoid repeated requests
    """
    try:
        response = requests.get(keycloak_config.certs_url, timeout=5)
        response.raise_for_status()
        jwks = response.json()

        # Get first key (Keycloak usually has one active key)
        if 'keys' in jwks and len(jwks['keys']) > 0:
            key_data = jwks['keys'][0]
            # Convert JWK to PEM format for PyJWT
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend
            from jwt.algorithms import RSAAlgorithm

            public_key = RSAAlgorithm.from_jwk(key_data)
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem.decode('utf-8')
        else:
            raise ValueError("No keys found in JWKS")

    except Exception as e:
        print(f"Error fetching Keycloak public key: {e}")
        raise


def validate_token(token: str, verify_signature: bool = True) -> Optional[Dict]:
    """
    Validate a Keycloak JWT token

    Args:
        token: The JWT token string
        verify_signature: Whether to verify the token signature (default: True)

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        # Get public key for signature verification
        if verify_signature:
            public_key = get_public_key()

            # Decode and validate token
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=keycloak_config.client_id,
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_aud': True
                }
            )
        else:
            # Decode without verification (use only for debugging!)
            decoded = jwt.decode(token, options={'verify_signature': False})

        return decoded

    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None
    except Exception as e:
        print(f"Error validating token: {e}")
        return None


def introspect_token(token: str) -> Optional[Dict]:
    """
    Introspect token via Keycloak's introspection endpoint
    This is the most secure method but requires a network call

    Args:
        token: The access token to introspect

    Returns:
        Introspection result if valid, None otherwise
    """
    try:
        response = requests.post(
            keycloak_config.introspect_url,
            data={
                'token': token,
                'client_id': keycloak_config.client_id,
                'client_secret': keycloak_config.client_secret
            },
            timeout=5
        )
        response.raise_for_status()
        result = response.json()

        if result.get('active', False):
            return result
        else:
            print("Token is not active")
            return None

    except Exception as e:
        print(f"Error introspecting token: {e}")
        return None


def get_token_from_request() -> Optional[str]:
    """
    Extract Bearer token from Authorization header

    Returns:
        Token string if found, None otherwise
    """
    auth_header = request.headers.get('Authorization', '')

    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix

    return None


def get_user_info(token: str) -> Optional[Dict]:
    """
    Fetch user information from Keycloak using the access token

    Args:
        token: The access token

    Returns:
        User information dict if successful, None otherwise
    """
    try:
        response = requests.get(
            keycloak_config.userinfo_url,
            headers={'Authorization': f'Bearer {token}'},
            timeout=5
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"Error fetching user info: {e}")
        return None


def has_role(token_payload: Dict, role: str) -> bool:
    """
    Check if the token has a specific realm role

    Args:
        token_payload: Decoded JWT payload
        role: Role name to check

    Returns:
        True if user has the role, False otherwise
    """
    roles = token_payload.get('realm_access', {}).get('roles', [])
    # Also check resource_access for client roles
    client_roles = token_payload.get('resource_access', {}).get(keycloak_config.client_id, {}).get('roles', [])

    all_roles = roles + client_roles
    return role in all_roles


def has_any_role(token_payload: Dict, required_roles: List[str]) -> bool:
    """
    Check if the token has any of the specified roles

    Args:
        token_payload: Decoded JWT payload
        required_roles: List of role names

    Returns:
        True if user has at least one of the roles, False otherwise
    """
    return any(has_role(token_payload, role) for role in required_roles)


def get_username(token_payload: Dict) -> Optional[str]:
    """
    Extract username from token payload

    Args:
        token_payload: Decoded JWT payload

    Returns:
        Username string if found, None otherwise
    """
    return token_payload.get('preferred_username') or token_payload.get('username')


def get_user_id(token_payload: Dict) -> Optional[str]:
    """
    Extract user ID (subject) from token payload

    Args:
        token_payload: Decoded JWT payload

    Returns:
        User ID string if found, None otherwise
    """
    return token_payload.get('sub')
