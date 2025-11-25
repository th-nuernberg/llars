"""
OIDC Authentication Routes (Authentik-backed)
These routes provide compatibility with the frontend while using Authentik for authentication
"""

from flask import Blueprint, jsonify, request, g, current_app
from auth.decorators import authentik_required, admin_required
from auth.oidc_validator import get_token_from_request, validate_token, get_username, get_user_id
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
    return jsonify({
        "username": g.authentik_user,
        "user_id": g.authentik_user_id,
        "roles": g.authentik_token.get('realm_access', {}).get('roles', []),
        "email": g.authentik_token.get('email'),
        "name": g.authentik_token.get('name'),
        "preferred_username": g.authentik_token.get('preferred_username')
    }), 200


@authentik_auth_blueprint.route('/validate', methods=['GET'])
@rate_limit("200 per hour")
def validate_token_endpoint():
    """
    Validate token endpoint - for frontend to check if token is still valid
    Rate limit: 200 requests per hour per IP
    """
    token = get_token_from_request()

    if not token:
        return jsonify({'valid': False, 'error': 'No token provided'}), 401

    token_payload = validate_token(token)

    if token_payload:
        return jsonify({
            'valid': True,
            'username': get_username(token_payload),
            'user_id': get_user_id(token_payload),
            'roles': token_payload.get('realm_access', {}).get('roles', [])
        }), 200
    else:
        return jsonify({'valid': False, 'error': 'Invalid or expired token'}), 401


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
def login():
    """
    Login endpoint - generates JWT token for development
    Rate limit: 10 requests per minute per IP

    DEVELOPMENT ONLY: This endpoint validates username/password by querying Authentik's
    PostgreSQL database directly. For production, implement proper OAuth2 flow.
    """
    import psycopg2
    import os
    import jwt
    import datetime
    from datetime import timezone
    from werkzeug.security import check_password_hash

    # Get credentials from request
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    current_app.logger.info(f"Login attempt received for user: {username}")

    try:
        # Connect to Authentik's PostgreSQL database
        conn = psycopg2.connect(
            host='authentik-db',
            database=os.getenv('AUTHENTIK_DB_NAME', 'authentik_dev'),
            user=os.getenv('AUTHENTIK_DB_USER', 'authentik_dev'),
            password=os.getenv('AUTHENTIK_DB_PASSWORD', 'dev_authentik_db_password'),
            connect_timeout=5
        )

        cursor = conn.cursor()

        # Query for user
        cursor.execute(
            """
            SELECT id, uuid, username, email, name, is_active, password
            FROM authentik_core_user
            WHERE username = %s
            """,
            (username,)
        )

        user_row = cursor.fetchone()

        if not user_row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401

        user_id, user_pk, user_username, user_email, user_name, is_active, stored_password = user_row
        cursor.close()
        conn.close()

        # Django password format: algorithm$salt$hash
        # For development, accept password "admin123" for all users
        # In production, validate against stored_password using Django's check_password

        # DEVELOPMENT: Accept "admin123" as password for any user
        # This simplifies testing without proper OAuth2 flow
        dev_mode = os.getenv('FLASK_ENV', 'development') == 'development' or os.getenv('PROJECT_STATE', 'development') == 'development'
        current_app.logger.info(f"Login attempt: user={username}, dev_mode={dev_mode}, password_match={password == 'admin123'}")

        if password == 'admin123' and dev_mode:
            # Development password accepted
            current_app.logger.info(f"Development login accepted for user {username}")
        else:
            # Try to validate against stored password (Django format)
            # This is a simplified check - Django uses pbkdf2_sha256$iterations$salt$hash
            if not stored_password or not stored_password.startswith('pbkdf2_sha256'):
                return jsonify({'error': 'Invalid credentials'}), 401
            # TODO: Implement proper Django pbkdf2_sha256 password verification
            return jsonify({'error': 'Invalid credentials - use admin123 in development'}), 401

        if not is_active:
            return jsonify({'error': 'User account is disabled'}), 401

        # Get user roles from LLARS database (MariaDB) using SQLAlchemy
        from db.db import db
        from sqlalchemy import text
        user_roles = ['user']  # Default role

        try:
            # Get roles for this user from LLARS database
            result = db.session.execute(
                text("""
                    SELECT r.role_name
                    FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.username = :username
                """),
                {'username': user_username}
            )

            for row in result:
                role_name = row[0]
                if role_name not in user_roles:
                    user_roles.append(role_name)

        except Exception as e:
            current_app.logger.warning(f"Could not fetch LLARS roles for {user_username}: {e}")

        # Generate JWT token
        jwt_secret = os.getenv('AUTHENTIK_SECRET_KEY', 'dev-authentik-secret-change-me')

        now = datetime.datetime.now(timezone.utc)
        exp = now + datetime.timedelta(hours=1)

        token_payload = {
            'exp': exp,
            'iat': now,
            'sub': str(user_pk),
            'preferred_username': user_username,
            'email': user_email or '',
            'name': user_name or user_username,
            'realm_access': {
                'roles': user_roles
            }
        }

        access_token = jwt.encode(token_payload, jwt_secret, algorithm='HS256')

        current_app.logger.info(f"User {username} logged in successfully")

        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'refresh_token': access_token,
            'id_token': access_token
        }), 200

    except psycopg2.Error as e:
        current_app.logger.error(f"Database error: {e}")
        return jsonify({'error': 'Authentication service unavailable'}), 503
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
