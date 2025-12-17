"""
OIDC Authentication Routes (Authentik-backed)
These routes provide compatibility with the frontend while using Authentik for authentication.
Uses Authentik's OAuth2/OIDC endpoints for proper token issuance and validation.
"""

from flask import Blueprint, jsonify, request, g, current_app
from auth.decorators import authentik_required, admin_required
from auth.oidc_validator import get_token_from_request, validate_token, get_username, get_user_id
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, UnauthorizedError
from functools import wraps

# Create blueprint for Authentik-specific routes
authentik_auth_blueprint = Blueprint('authentik_auth', __name__)


def rate_limit(limit_string):
    """Custom rate limit decorator that works with blueprints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Rate limiting wird durch Flask-Limiter auf App-Level gehandhabt
            # Hier nur als Dokumentation der Limits
            return f(*args, **kwargs)
        decorated_function._rate_limit = limit_string
        return decorated_function
    return decorator


@authentik_auth_blueprint.route('/health_check', methods=['GET'])
def health_check():
    """Health check endpoint - no authentication required"""
    return jsonify({"message": "Server is running with Authentik authentication"}), 200


@authentik_auth_blueprint.route('/me', methods=['GET'])
@authentik_required
@rate_limit("100 per hour")
def get_current_user():
    """
    Get current authenticated user information
    Uses Authentik token to return user details
    Rate limit: 100 requests per hour per IP
    """
    # g.authentik_user is now a User object after decorators.py fix
    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)
    user_id = user.id if hasattr(user, 'id') else g.authentik_user_id

    return jsonify({
        "username": username,
        "user_id": user_id,
        "roles": g.authentik_token.get('realm_access', {}).get('roles', []),
        "email": g.authentik_token.get('email'),
        "name": g.authentik_token.get('name'),
        "preferred_username": g.authentik_token.get('preferred_username')
    }), 200


@authentik_auth_blueprint.route('/validate', methods=['GET'])
@rate_limit("200 per hour")
@handle_api_errors(logger_name='authentik')
def validate_token_endpoint():
    """
    Validate token endpoint - for frontend to check if token is still valid
    Rate limit: 200 requests per hour per IP
    """
    token = get_token_from_request()

    if not token:
        raise UnauthorizedError('No token provided')

    token_payload = validate_token(token)

    if token_payload:
        return jsonify({
            'valid': True,
            'username': get_username(token_payload),
            'user_id': get_user_id(token_payload),
            'roles': token_payload.get('realm_access', {}).get('roles', [])
        }), 200
    else:
        raise UnauthorizedError('Invalid or expired token')


@authentik_auth_blueprint.route('/admin/check', methods=['GET'])
@admin_required
def check_admin():
    """
    Admin check endpoint - returns 200 if user is admin, 403 otherwise
    """
    return jsonify({
        "message": "User has admin privileges",
        "username": g.authentik_user
    }), 200


@authentik_auth_blueprint.route('/login', methods=['POST'])
@rate_limit("10 per minute")
@handle_api_errors(logger_name='authentik')
def login():
    """
    Login endpoint - authenticates via Authentik Flow Executor API
    Rate limit: 10 requests per minute per IP

    Uses Authentik's Flow Executor API to authenticate users via the
    llars-api-authentication flow, then exchanges the session for an OAuth2 token.
    Returns RS256 signed JWT tokens from Authentik.
    """
    import os
    import requests as http_requests
    import uuid

    # Get credentials from request
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        raise ValidationError('Username and password required')

    current_app.logger.info(f"Login attempt received for user: {username}")

    try:
        # Authentik configuration
        authentik_base_url = os.getenv('AUTHENTIK_INTERNAL_URL', 'http://authentik-server:9000')
        flow_slug = 'llars-api-authentication'
        client_id = os.getenv('AUTHENTIK_BACKEND_CLIENT_ID', 'llars-backend')
        client_secret = os.getenv('AUTHENTIK_BACKEND_CLIENT_SECRET', 'llars-backend-secret-change-in-production')

        # Create a session to maintain cookies (Authentik browser session)
        session = http_requests.Session()

        # Step 1: Start the authentication flow
        flow_url = f"{authentik_base_url}/api/v3/flows/executor/{flow_slug}/"
        current_app.logger.info(f"Starting Authentik flow for {username}")

        # Get initial flow state
        flow_response = session.get(
            flow_url,
            headers={'Accept': 'application/json'},
            timeout=10
        )

        if flow_response.status_code != 200:
            current_app.logger.error(f"Failed to start flow: {flow_response.status_code} - {flow_response.text}")
            raise ValidationError('Authentication service error')

        flow_data = flow_response.json()
        current_app.logger.debug(f"Flow response: {flow_data}")

        # Step 2: Submit username to identification stage
        if flow_data.get('component') == 'ak-stage-identification':
            flow_response = session.post(
                flow_url,
                json={'uid_field': username},
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                timeout=10
            )

            if flow_response.status_code != 200:
                current_app.logger.error(f"Identification failed: {flow_response.status_code}")
                raise UnauthorizedError('Invalid credentials')

            flow_data = flow_response.json()
            current_app.logger.debug(f"After identification: {flow_data}")

        # Step 3: Submit password to password stage
        if flow_data.get('component') == 'ak-stage-password':
            flow_response = session.post(
                flow_url,
                json={'password': password},
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                timeout=10
            )

            if flow_response.status_code != 200:
                current_app.logger.warning(f"Password validation failed for {username}")
                raise UnauthorizedError('Invalid credentials')

            flow_data = flow_response.json()
            current_app.logger.debug(f"After password: {flow_data}")

        # Check if authentication was successful
        # Flow executor returns redirect_to on success, or component for next stage
        if flow_data.get('type') == 'redirect' or 'to' in flow_data:
            current_app.logger.info(f"User {username} authenticated successfully via flow")

            # Step 4: Now use the authenticated session to get an OAuth2 token
            # We need to initiate an OAuth2 authorization flow
            state = str(uuid.uuid4())
            nonce = str(uuid.uuid4())

            # Get authorization code using implicit consent flow
            auth_url = f"{authentik_base_url}/application/o/authorize/"
            auth_params = {
                'response_type': 'code',
                'client_id': client_id,
                'redirect_uri': f"{authentik_base_url}/",  # Placeholder, we intercept
                'scope': 'openid profile email',
                'state': state,
                'nonce': nonce
            }

            auth_response = session.get(
                auth_url,
                params=auth_params,
                allow_redirects=False,  # We want to capture the redirect
                timeout=10
            )

            # Check for authorization code in redirect
            if auth_response.status_code in [302, 303]:
                location = auth_response.headers.get('Location', '')
                current_app.logger.debug(f"Auth redirect: {location}")

                # Extract code from redirect URL
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(location)
                params = parse_qs(parsed.query)

                if 'code' in params:
                    auth_code = params['code'][0]

                    # Step 5: Exchange authorization code for tokens
                    token_url = f"{authentik_base_url}/application/o/token/"
                    token_response = http_requests.post(
                        token_url,
                        data={
                            'grant_type': 'authorization_code',
                            'code': auth_code,
                            'redirect_uri': f"{authentik_base_url}/",
                            'client_id': client_id,
                            'client_secret': client_secret
                        },
                        headers={'Content-Type': 'application/x-www-form-urlencoded'},
                        timeout=10
                    )

                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        current_app.logger.info(f"User {username} logged in successfully")

                        # Enrich with LLARS roles
                        _enrich_token_with_roles(token_data, username)

                        response = jsonify(token_data)

                        # Optional but important for real SSO:
                        # If the user later opens another OIDC-protected app (e.g., Matomo),
                        # Authentik will only skip the login prompt if the browser has an
                        # Authentik session cookie. Our login is server-side, so we propagate
                        # the Authentik session cookie to the browser here.
                        authentik_session_cookie = session.cookies.get('authentik_session')
                        if authentik_session_cookie:
                            forwarded_proto = request.headers.get('X-Forwarded-Proto', request.scheme)
                            response.set_cookie(
                                'authentik_session',
                                authentik_session_cookie,
                                httponly=True,
                                secure=(forwarded_proto == 'https'),
                                samesite='Lax',
                                path='/'
                            )

                        return response, 200
                    else:
                        current_app.logger.error(f"Token exchange failed: {token_response.text}")

            # If we can't get OAuth token, authentication failed
            current_app.logger.error(f"Could not obtain OAuth token for {username}")
            raise ValidationError('Could not obtain access token')

        # Authentication failed - check for error messages
        if flow_data.get('response_errors'):
            errors = flow_data.get('response_errors', {})
            current_app.logger.warning(f"Authentication failed for {username}: {errors}")
            raise UnauthorizedError('Invalid credentials')

        # Unknown state
        current_app.logger.error(f"Unexpected flow state: {flow_data}")
        raise ValidationError('Authentication error')

    except http_requests.exceptions.ConnectionError as e:
        current_app.logger.error(f"Cannot connect to Authentik: {e}")
        raise ValidationError('Authentication service unavailable')
    except http_requests.exceptions.Timeout as e:
        current_app.logger.error(f"Authentik request timeout: {e}")
        raise ValidationError('Authentication service timeout')


def _enrich_token_with_roles(token_data: dict, username: str) -> None:
    """Add LLARS-specific roles from MariaDB to the token response"""
    try:
        from db.db import db
        from sqlalchemy import text
        user_roles = ['user']

        result = db.session.execute(
            text("""
                SELECT r.role_name
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.username = :username
            """),
            {'username': username}
        )

        for row in result:
            role_name = row[0]
            if role_name not in user_roles:
                user_roles.append(role_name)

        token_data['llars_roles'] = user_roles

    except Exception as e:
        from flask import current_app
        current_app.logger.warning(f"Could not fetch LLARS roles for {username}: {e}")
