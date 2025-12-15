"""
OIDC Token Validation Module (Authentik)
Validates JWT tokens issued by Authentik for the LLARS applications.
"""

import os
import jwt
import requests
from functools import lru_cache
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from urllib.parse import urlparse
from flask import request, jsonify


class OIDCConfig:
    """OIDC configuration (backed by Authentik) from environment variables"""

    def __init__(self):
        # Issuer URL points to the Authentik application OIDC endpoint
        self.issuer = os.environ.get(
            'AUTHENTIK_ISSUER_URL',
            'http://authentik-server:9000/application/o/llars-backend/'
        ).rstrip('/')
        self.client_id = os.environ.get('AUTHENTIK_BACKEND_CLIENT_ID', 'llars-backend')
        self.client_secret = os.environ.get('AUTHENTIK_BACKEND_CLIENT_SECRET', '')

        # Construct well-known URLs (Authentik exposes OIDC metadata per application)
        self.well_known_url = f"{self.issuer}/.well-known/openid-configuration"
        self.certs_url = f"{self.issuer}/jwks/"  # Authentik uses /jwks/ not /.well-known/jwks.json
        self.introspect_url = f"{self.issuer}/token/introspect"
        self.userinfo_url = f"{self.issuer}/userinfo"


oidc_config = OIDCConfig()


# Cache for JWKS with TTL
_jwks_cache = {}
_cache_timeout = timedelta(hours=1)


def _fetch_jwks() -> Dict:
    """
    Fetch JWKS from the OIDC issuer with 1-hour TTL cache

    Returns:
        JWKS dictionary from the issuer
    """
    # Check cache
    if 'jwks' in _jwks_cache:
        cached_jwks, cached_time = _jwks_cache['jwks']
        if datetime.now() - cached_time < _cache_timeout:
            return cached_jwks

    # Fetch fresh JWKS
    try:
        response = requests.get(oidc_config.certs_url, timeout=5)
        response.raise_for_status()
        jwks = response.json()

        # Cache for 1 hour
        _jwks_cache['jwks'] = (jwks, datetime.now())
        return jwks

    except Exception as e:
        print(f"Error fetching JWKS from OIDC issuer: {e}")
        # If cache exists (even expired), use it as fallback
        if 'jwks' in _jwks_cache:
            print("Using cached JWKS as fallback")
            cached_jwks, _ = _jwks_cache['jwks']
            return cached_jwks
        raise


def get_public_key(kid: Optional[str] = None) -> str:
    """
    Get public key for JWT validation

    Args:
        kid: Key ID from JWT header. If provided, finds matching key.
             If None, returns first available key (development fallback)

    Returns:
        Public key in PEM format

    Raises:
        ValueError: If kid specified but not found in JWKS
    """
    try:
        jwks = _fetch_jwks()

        if 'keys' not in jwks or len(jwks['keys']) == 0:
            raise ValueError("No keys found in JWKS")

        # If kid provided, find matching key
        if kid:
            for key_data in jwks['keys']:
                if key_data.get('kid') == kid:
                    return _convert_jwk_to_pem(key_data)

            # kid not found
            raise ValueError(f"Key with kid '{kid}' not found in JWKS. "
                           f"Available kids: {[k.get('kid') for k in jwks['keys']]}")

        # No kid provided - use first key (development fallback)
        key_data = jwks['keys'][0]
        print(f"Warning: No kid provided, using first key: {key_data.get('kid')}")
        return _convert_jwk_to_pem(key_data)

    except Exception as e:
        print(f"Error getting public key: {e}")
        raise


def _convert_jwk_to_pem(key_data: Dict) -> str:
    """
    Convert JWK to PEM format

    Args:
        key_data: JWK dictionary

    Returns:
        Public key in PEM format
    """
    from cryptography.hazmat.primitives import serialization
    from jwt.algorithms import RSAAlgorithm

    public_key = RSAAlgorithm.from_jwk(key_data)
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')


def validate_token(token: str, verify_signature: bool = True) -> Optional[Dict]:
    """
    Validate a JWT token using RS256 algorithm (Authentik OIDC)

    Args:
        token: The JWT token string
        verify_signature: Whether to verify the token signature (default: True)

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        expected_aud = oidc_config.client_id

        if verify_signature:
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get('alg', 'RS256')
            kid = unverified_header.get('kid')

            # Only accept RS256 tokens from Authentik
            if alg != 'RS256':
                print(f"Unsupported token algorithm: {alg}. Only RS256 is accepted.")
                return None

            if not kid:
                print("Warning: Token has no 'kid' in header")

            public_key = get_public_key(kid)

            decoded = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iss': False,  # accept non-matching hostnames in dev
                    'verify_aud': False  # manual audience check below
                }
            )

            token_aud = decoded.get('aud') or decoded.get('azp')
            if expected_aud and token_aud and expected_aud not in ([token_aud] if isinstance(token_aud, str) else token_aud):
                print(f"Invalid audience. Expected: {expected_aud}, got: {token_aud}")
                return None

            token_iss = decoded.get('iss')
            if token_iss:
                # Accept different hostnames in proxy/dev setups, but ensure the issuer path matches.
                try:
                    expected_path = urlparse(f"{oidc_config.issuer.rstrip('/')}/").path.rstrip('/')
                    token_path = urlparse(f"{str(token_iss).rstrip('/')}/").path.rstrip('/')
                    if expected_path and token_path != expected_path:
                        print(f"Invalid issuer path. Expected: {expected_path}, got: {token_path}")
                        return None
                except Exception as e:
                    print(f"Invalid issuer. Could not parse issuer URL: {e}")
                    return None
        else:
            decoded = jwt.decode(token, options={'verify_signature': False})

        return decoded

    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidAudienceError:
        print(f"Invalid audience. Expected: {oidc_config.client_id}")
        return None
    except jwt.InvalidIssuerError:
        print(f"Invalid issuer. Expected: {oidc_config.issuer}")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None
    except ValueError as e:
        print(f"Key validation error: {e}")
        return None
    except Exception as e:
        print(f"Error validating token: {e}")
        return None


def introspect_token(token: str) -> Optional[Dict]:
    """
    Introspect token via the issuer's introspection endpoint
    This is the most secure method but requires a network call

    Args:
        token: The access token to introspect

    Returns:
        Introspection result if valid, None otherwise
    """
    try:
        response = requests.post(
            oidc_config.introspect_url,
            data={
                'token': token,
                'client_id': oidc_config.client_id,
                'client_secret': oidc_config.client_secret
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


def has_role(token_payload: Dict, role: str) -> bool:
    """
    Check if the token has a specific role.

    Supports multiple token formats:
    - Authentik: groups (array of group names)
    - Legacy Keycloak: realm_access.roles, resource_access.<client>.roles

    For Authentik, maps common group names to roles:
    - 'authentik Admins' -> 'admin'
    - 'admins' -> 'admin'
    - Group names are also checked directly

    Args:
        token_payload: Decoded JWT payload
        role: Role name to check

    Returns:
        True if user has the role, False otherwise
    """
    # === Authentik format (primär) ===
    # Authentik sends groups in the 'groups' claim (from profile scope)
    authentik_groups = token_payload.get('groups', [])

    # Map Authentik group names to standard role names
    authentik_group_to_role = {
        'authentik Admins': 'admin',
        'authentik admins': 'admin',
        'Admins': 'admin',
        'admins': 'admin',
        'Administrators': 'admin',
        'administrators': 'admin',
        'Researchers': 'researcher',
        'researchers': 'researcher',
        'Viewers': 'viewer',
        'viewers': 'viewer',
    }

    # Convert Authentik groups to roles
    authentik_roles = []
    for group in authentik_groups:
        # Add the mapped role if exists
        if group in authentik_group_to_role:
            authentik_roles.append(authentik_group_to_role[group])
        # Also add the group name directly (lowercase) as a role
        authentik_roles.append(group.lower())
        # And the original group name
        authentik_roles.append(group)

    # === Legacy Keycloak format (Kompatibilität) ===
    # Check realm_access.roles
    keycloak_roles = token_payload.get('realm_access', {}).get('roles', [])
    # Check resource_access.<client_id>.roles
    client_roles = token_payload.get('resource_access', {}).get(oidc_config.client_id, {}).get('roles', [])

    # Combine all roles from all sources
    all_roles = keycloak_roles + client_roles + authentik_roles

    # Check if the requested role is in any of the sources
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
    # Try standard OIDC claims first, then Authentik-specific, then fallback to uid
    return (token_payload.get('preferred_username') or
            token_payload.get('username') or
            token_payload.get('name') or
            token_payload.get('uid') or  # Authentik user ID
            token_payload.get('sub')[:16] if token_payload.get('sub') else None)  # Use first 16 chars of sub as last resort


def get_user_id(token_payload: Dict) -> Optional[str]:
    """
    Extract user ID (subject) from token payload

    Args:
        token_payload: Decoded JWT payload

    Returns:
        User ID string if found, None otherwise
    """
    return token_payload.get('sub')
