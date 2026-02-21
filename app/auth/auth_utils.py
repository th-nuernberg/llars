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
         Extract username from JWT token, preferring already-validated context.

        Security model:
        1. FIRST: Check if user was already authenticated by decorators (@require_permission,
           @authentik_required) - these set g.authentik_user with validated user info
        2. FALLBACK: If no validated context exists, decode token WITHOUT signature verification
           This is only safe because this method should ONLY be called from routes that
           are already protected by authentication decorators.

        WARNING: Do NOT use this method in unprotected routes. Always ensure the route
        has @authentik_required or @require_permission decorator applied.

        Returns:
            Username string if found, None otherwise
        """
        from flask import g
        import logging

        logger = logging.getLogger(__name__)

        # PREFERRED: Use already-validated user from authentication decorators
        # This is set by @authentik_required and @require_permission decorators
        if hasattr(g, 'authentik_user') and g.authentik_user is not None:
            user = g.authentik_user
            username = getattr(user, 'username', None)
            if username:
                return username

        # Check if authenticated via System API Key
        if getattr(g, 'is_system_api_key', False):
            # API key auth - return admin or the user set by decorator
            if hasattr(g, 'authentik_user') and g.authentik_user:
                return getattr(g.authentik_user, 'username', None) or 'admin'
            return 'admin'

        # FALLBACK: Decode token without verification
        # This path should rarely be hit if routes are properly decorated
        # Log a warning to help identify routes that need proper decoration
        try:
            import jwt
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return None

            token = auth_header.split(' ')[1]

            # Log warning about unvalidated token extraction
            logger.warning(
                "extract_username_without_validation() falling back to unverified token decode. "
                "Ensure the calling route has @authentik_required or @require_permission decorator."
            )

            decoded = jwt.decode(token, options={"verify_signature": False})

            sub = decoded.get('sub')
            return (
                decoded.get('preferred_username') or
                decoded.get('username') or
                decoded.get('name') or
                decoded.get('uid') or
                (sub[:16] if sub else None)
            )
        except Exception as e:
            logger.debug(f"Failed to extract username from token: {e}")
            return None
