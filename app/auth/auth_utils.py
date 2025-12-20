"""
Authentication Utilities Module

Provides centralized utilities for extracting user information from JWT tokens.
This eliminates code duplication across routes and ensures consistent token handling.
"""

from typing import Optional, Dict
from flask import request
from auth.oidc_validator import validate_token, get_token_from_request


class AuthUtils:
    """Centralized utilities for JWT token handling and user information extraction"""

    @staticmethod
    def extract_username_from_token() -> Optional[str]:
        """
        Extract the username from the JWT token in the request.

        Tries multiple claims in order of preference:
        1. preferred_username (standard OIDC)
        2. username (alternative)
        3. name (fallback)
        4. uid (Authentik user ID)
        5. sub (subject - first 16 chars)

        Returns:
            Username string if found, None otherwise

        Example:
            >>> from app.auth.auth_utils import AuthUtils
            >>> username = AuthUtils.extract_username_from_token()
            >>> if username:
            ...     print(f"User: {username}")
        """
        try:
            payload = validate_token(get_token_from_request())
            return (
                payload.get('preferred_username') or
                payload.get('username') or
                payload.get('name') or
                payload.get('uid') or
                payload.get('sub')[:16] if payload.get('sub') else None
            )
        except Exception:
            return None

    @staticmethod
    def get_user_info() -> Optional[Dict[str, any]]:
        """
        Extract all user information from the JWT token.

        Returns a dictionary with:
        - username: The user's username
        - email: The user's email address
        - groups: List of groups/roles the user belongs to
        - sub: The subject (unique user ID)

        Returns:
            Dictionary with user info if token is valid, None otherwise

        Example:
            >>> from app.auth.auth_utils import AuthUtils
            >>> user_info = AuthUtils.get_user_info()
            >>> if user_info:
            ...     print(f"User: {user_info['username']}")
            ...     print(f"Email: {user_info['email']}")
            ...     print(f"Groups: {user_info['groups']}")
        """
        try:
            payload = validate_token(get_token_from_request())
            return {
                'username': (
                    payload.get('preferred_username') or
                    payload.get('username') or
                    payload.get('name')
                ),
                'email': payload.get('email'),
                'groups': payload.get('groups', []),
                'sub': payload.get('sub')
            }
        except Exception:
            return None

    @staticmethod
    def extract_username_without_validation() -> Optional[str]:
        """
        Extract username from JWT token WITHOUT signature verification.

        WARNING: This should only be used in contexts where the token has already
        been validated by decorators (e.g., @require_permission).

        This is a compatibility method for routes that decode tokens without verification.
        Use extract_username_from_token() for new code instead.

        Returns:
            Username string if found, None otherwise
        """
        from flask import g

        # Check if already authenticated via System API Key (set by @require_permission)
        if getattr(g, 'is_system_api_key', False) and getattr(g, 'authentik_user', None):
            user = g.authentik_user
            return getattr(user, 'username', None) or 'admin'

        try:
            import jwt
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return None

            token = auth_header.split(' ')[1]
            decoded = jwt.decode(token, options={"verify_signature": False})

            return (
                decoded.get('preferred_username') or
                decoded.get('username') or
                decoded.get('name') or
                decoded.get('uid') or
                decoded.get('sub')
            )
        except Exception:
            return None
