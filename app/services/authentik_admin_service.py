"""
Authentik Admin Service

Provides administrative operations for Authentik user management.
Uses Authentik's Core API v3 to create, update, and manage users.

Authentication methods (in order of preference):
1. API Token (AUTHENTIK_API_TOKEN env var) - most reliable
2. Flow-based authentication using bootstrap credentials - fallback
"""

import logging
import os
from typing import Optional, Dict, Any, Tuple

import requests

logger = logging.getLogger(__name__)


class AuthentikAdminService:
    """Service for managing users in Authentik via the Admin API."""

    _token: Optional[str] = None
    _token_expires: float = 0

    @classmethod
    def _get_config(cls) -> Dict[str, str]:
        """Get Authentik configuration from environment."""
        return {
            "base_url": os.getenv("AUTHENTIK_INTERNAL_URL", "http://authentik-server:9000"),
            "api_token": os.getenv("AUTHENTIK_API_TOKEN", ""),
            "admin_email": os.getenv("AUTHENTIK_BOOTSTRAP_EMAIL", "admin@example.com"),
            "admin_password": os.getenv("AUTHENTIK_BOOTSTRAP_PASSWORD", "admin123"),
        }

    @classmethod
    def _get_admin_token(cls) -> Optional[str]:
        """
        Get an admin token for Authentik API.

        Priority:
        1. Static API token from environment (AUTHENTIK_API_TOKEN)
        2. Flow-based authentication using bootstrap credentials
        """
        import time

        config = cls._get_config()

        # Priority 1: Use static API token if available
        if config["api_token"]:
            logger.debug("Using static API token from AUTHENTIK_API_TOKEN")
            return config["api_token"]

        # Priority 2: Return cached token if still valid (with 60s buffer)
        if cls._token and cls._token_expires > time.time() + 60:
            return cls._token

        # Priority 3: Try to get token via LLARS authentication flow
        base_url = config["base_url"]

        try:
            session = requests.Session()

            # Use the LLARS-specific authentication flow
            flow_slug = "llars-api-authentication"
            flow_url = f"{base_url}/api/v3/flows/executor/{flow_slug}/"

            logger.info(f"Attempting Authentik admin auth via flow: {flow_slug}")

            # Get initial flow state
            flow_response = session.get(
                flow_url,
                headers={"Accept": "application/json"},
                timeout=10
            )

            if flow_response.status_code != 200:
                # Try default flow as fallback
                flow_slug = "default-authentication-flow"
                flow_url = f"{base_url}/api/v3/flows/executor/{flow_slug}/"
                flow_response = session.get(
                    flow_url,
                    headers={"Accept": "application/json"},
                    timeout=10
                )

            if flow_response.status_code != 200:
                logger.error(f"Failed to start Authentik flow: {flow_response.status_code}")
                return None

            flow_data = flow_response.json()
            logger.debug(f"Flow stage: {flow_data.get('component')}")

            # Submit identification (email/username)
            if flow_data.get("component") == "ak-stage-identification":
                flow_response = session.post(
                    flow_url,
                    json={"uid_field": config["admin_email"]},
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    timeout=10
                )
                if flow_response.status_code != 200:
                    logger.error(f"Authentik identification failed: {flow_response.status_code}")
                    return None
                flow_data = flow_response.json()
                logger.debug(f"After identification, stage: {flow_data.get('component')}")

            # Submit password
            if flow_data.get("component") == "ak-stage-password":
                flow_response = session.post(
                    flow_url,
                    json={"password": config["admin_password"]},
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    timeout=10
                )
                if flow_response.status_code != 200:
                    logger.error(f"Authentik password stage failed: {flow_response.status_code}")
                    return None
                flow_data = flow_response.json()
                logger.debug(f"After password, response type: {flow_data.get('type')}")

            # Check for successful authentication - extract session token
            if flow_data.get("type") == "redirect" or "to" in flow_data:
                # The session now has auth cookies, try to create an API token
                token_response = session.post(
                    f"{base_url}/api/v3/core/tokens/",
                    json={
                        "identifier": "llars-admin-temp-token",
                        "intent": "api",
                        "expiring": True,
                        "description": "Temporary token for LLARS admin operations"
                    },
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    timeout=10
                )

                if token_response.status_code in [200, 201]:
                    token_data = token_response.json()
                    cls._token = token_data.get("key")
                    # Token expires in 30 minutes by default
                    cls._token_expires = time.time() + 1800
                    logger.info("Successfully created Authentik admin API token")
                    return cls._token

                # If token creation fails, try using the session directly
                logger.warning(f"Could not create API token: {token_response.status_code}")

                # Try to verify session works by fetching current user
                me_response = session.get(
                    f"{base_url}/api/v3/core/users/me/",
                    headers={"Accept": "application/json"},
                    timeout=10
                )

                if me_response.status_code == 200:
                    # Session auth works, we can use session cookies
                    cls._session = session
                    cls._token = "SESSION_AUTH"
                    cls._token_expires = time.time() + 600
                    logger.info("Using session-based authentication for Authentik")
                    return cls._token

            logger.error("Could not obtain Authentik admin token - authentication flow completed but no token obtained")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentik connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting Authentik token: {e}")
            return None

    _session: Optional[requests.Session] = None

    @classmethod
    def _get_auth_headers(cls) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        token = cls._get_admin_token()
        if token and token != "SESSION_AUTH":
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        return {
            "Content-Type": "application/json",
        }

    @classmethod
    def _make_request(cls, method: str, url: str, **kwargs) -> requests.Response:
        """Make an authenticated request to Authentik API."""
        token = cls._get_admin_token()

        if token == "SESSION_AUTH" and cls._session:
            # Use session-based auth
            kwargs.setdefault("headers", {})
            kwargs["headers"]["Accept"] = "application/json"
            if method.upper() == "GET":
                return cls._session.get(url, **kwargs)
            elif method.upper() == "POST":
                return cls._session.post(url, **kwargs)
            elif method.upper() == "PATCH":
                return cls._session.patch(url, **kwargs)
            elif method.upper() == "DELETE":
                return cls._session.delete(url, **kwargs)

        # Use token-based auth
        headers = cls._get_auth_headers()
        headers["Accept"] = "application/json"
        kwargs["headers"] = headers
        return getattr(requests, method.lower())(url, **kwargs)

    @classmethod
    def create_user(
        cls,
        username: str,
        email: str,
        password: str,
        name: str = "",
        is_active: bool = True
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Create a new user in Authentik.

        Args:
            username: The username for the new user
            email: Email address
            password: Initial password
            name: Display name (optional, defaults to username)
            is_active: Whether the user should be active

        Returns:
            Tuple of (success, error_message, user_data)
        """
        token = cls._get_admin_token()
        if not token:
            return False, "Could not authenticate with Authentik", None

        config = cls._get_config()
        api_url = f"{config['base_url']}/api/v3"

        try:
            # Check if user already exists
            check_response = cls._make_request(
                "GET",
                f"{api_url}/core/users/",
                params={"username": username},
                timeout=10
            )

            if check_response.status_code == 200:
                results = check_response.json().get("results", [])
                for user in results:
                    if user.get("username") == username:
                        return False, f"User '{username}' already exists in Authentik", None

            # Create user
            user_data = {
                "username": username,
                "name": name or username,
                "email": email,
                "is_active": is_active,
                "path": "users",
                "type": "internal",
            }

            create_response = cls._make_request(
                "POST",
                f"{api_url}/core/users/",
                json=user_data,
                timeout=10
            )

            if create_response.status_code not in [200, 201]:
                error_detail = create_response.json() if create_response.text else {}
                error_msg = error_detail.get("detail", create_response.text or "Unknown error")
                logger.error(f"Failed to create Authentik user: {create_response.status_code} - {error_msg}")
                return False, f"Authentik error: {error_msg}", None

            created_user = create_response.json()
            user_pk = created_user.get("pk")

            logger.info(f"Created Authentik user '{username}' with PK: {user_pk}")

            # Set password
            password_response = cls._make_request(
                "POST",
                f"{api_url}/core/users/{user_pk}/set_password/",
                json={"password": password},
                timeout=10
            )

            if password_response.status_code not in [200, 204]:
                logger.warning(f"Failed to set password for user '{username}': {password_response.status_code}")
                # User was created, but password setting failed
                return True, "User created but password could not be set", created_user

            logger.info(f"Password set for Authentik user '{username}'")
            return True, None, created_user

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentik API error: {e}")
            return False, f"Connection error: {str(e)}", None
        except Exception as e:
            logger.error(f"Unexpected error creating Authentik user: {e}")
            return False, f"Unexpected error: {str(e)}", None

    @classmethod
    def update_user_status(cls, username: str, is_active: bool) -> Tuple[bool, Optional[str]]:
        """
        Update user's active status in Authentik.

        Args:
            username: The username to update
            is_active: New active status

        Returns:
            Tuple of (success, error_message)
        """
        token = cls._get_admin_token()
        if not token:
            return False, "Could not authenticate with Authentik"

        config = cls._get_config()
        api_url = f"{config['base_url']}/api/v3"

        try:
            # Find user by username
            search_response = cls._make_request(
                "GET",
                f"{api_url}/core/users/",
                params={"username": username},
                timeout=10
            )

            if search_response.status_code != 200:
                return False, "Could not search for user"

            results = search_response.json().get("results", [])
            user_pk = None
            for user in results:
                if user.get("username") == username:
                    user_pk = user.get("pk")
                    break

            if not user_pk:
                return False, f"User '{username}' not found in Authentik"

            # Update user status
            update_response = cls._make_request(
                "PATCH",
                f"{api_url}/core/users/{user_pk}/",
                json={"is_active": is_active},
                timeout=10
            )

            if update_response.status_code not in [200, 204]:
                return False, f"Failed to update user: {update_response.status_code}"

            logger.info(f"Updated Authentik user '{username}' is_active={is_active}")
            return True, None

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentik API error: {e}")
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error updating Authentik user: {e}")
            return False, f"Unexpected error: {str(e)}"

    @classmethod
    def check_connection(cls) -> Tuple[bool, Optional[str]]:
        """
        Check if Authentik is reachable and we can authenticate.

        Returns:
            Tuple of (success, error_message)
        """
        config = cls._get_config()
        base_url = config["base_url"]

        try:
            # Check health endpoint
            response = requests.get(
                f"{base_url}/-/health/ready/",
                timeout=5
            )

            if response.status_code != 200:
                return False, "Authentik health check failed"

            # Try to get admin token
            token = cls._get_admin_token()
            if not token:
                return False, "Could not authenticate with Authentik"

            return True, None

        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
