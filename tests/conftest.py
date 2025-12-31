"""
LLARS Test Configuration
========================

Central pytest configuration with fixtures for all test types.
Provides app context, database, authentication mocks, and test clients.

IMPORTANT: This creates an isolated test Flask app that doesn't connect to
production services (Redis, MariaDB, etc.). It uses SQLite in-memory database.

Usage:
    pytest tests/                    # Run all tests
    pytest tests/unit/              # Run unit tests only
    pytest tests/integration/       # Run integration tests only
    pytest -v -x                    # Verbose, stop on first failure
"""

import os
import sys

# Add app directory to path FIRST (before any imports from app)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# Set test environment variables BEFORE any imports
os.environ['TESTING'] = 'true'
os.environ['FLASK_ENV'] = 'testing'
os.environ['AUTHENTIK_DISABLED'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SYSTEM_ADMIN_API_KEY'] = 'test-system-api-key-12345'
os.environ['ADMIN_REGISTRATION_KEY'] = 'test-admin-key'
os.environ['AUTHENTIK_ISSUER_URL'] = 'http://test-authentik:9000/application/o/llars-backend/'
os.environ['AUTHENTIK_BACKEND_CLIENT_ID'] = 'llars-backend'
os.environ['SECRET_KEY'] = 'test-secret-key-for-jwt-signing'
# Database env vars to prevent errors in configure_database
os.environ['MYSQL_ROOT_PASSWORD'] = 'test'
os.environ['MYSQL_DATABASE'] = 'test_db'
os.environ['MYSQL_USER'] = 'test_user'
os.environ['MYSQL_PASSWORD'] = 'test_password'


# =============================================================================
# CRITICAL: Patch MySQL types for SQLite BEFORE any model imports
# This must happen at module load time, before pytest collects fixtures
# =============================================================================

def _patch_mysql_types_for_sqlite():
    """Patch MySQL-specific types to work with SQLite for testing."""
    from sqlalchemy.dialects.sqlite import base as sqlite_base

    # Add visit methods for MySQL types to SQLite's type compiler
    # This allows SQLite to compile MySQL-specific types like LONGTEXT

    def visit_LONGTEXT(self, type_, **kw):
        return "TEXT"

    def visit_MEDIUMTEXT(self, type_, **kw):
        return "TEXT"

    def visit_TINYTEXT(self, type_, **kw):
        return "TEXT"

    def visit_LONGBLOB(self, type_, **kw):
        return "BLOB"

    def visit_MEDIUMBLOB(self, type_, **kw):
        return "BLOB"

    def visit_TINYBLOB(self, type_, **kw):
        return "BLOB"

    def visit_DOUBLE(self, type_, **kw):
        return "REAL"

    def visit_TINYINT(self, type_, **kw):
        return "INTEGER"

    # Patch the SQLite type compiler
    sqlite_base.SQLiteTypeCompiler.visit_LONGTEXT = visit_LONGTEXT
    sqlite_base.SQLiteTypeCompiler.visit_MEDIUMTEXT = visit_MEDIUMTEXT
    sqlite_base.SQLiteTypeCompiler.visit_TINYTEXT = visit_TINYTEXT
    sqlite_base.SQLiteTypeCompiler.visit_LONGBLOB = visit_LONGBLOB
    sqlite_base.SQLiteTypeCompiler.visit_MEDIUMBLOB = visit_MEDIUMBLOB
    sqlite_base.SQLiteTypeCompiler.visit_TINYBLOB = visit_TINYBLOB
    sqlite_base.SQLiteTypeCompiler.visit_DOUBLE = visit_DOUBLE
    sqlite_base.SQLiteTypeCompiler.visit_TINYINT = visit_TINYINT


# Apply the patch immediately at module load time
_patch_mysql_types_for_sqlite()


# =============================================================================
# Now it's safe to import everything else
# =============================================================================

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# =============================================================================
# TEST SECRET KEY FOR JWT SIGNING
# =============================================================================

TEST_JWT_SECRET = 'test-jwt-secret-key-for-testing-only'
TEST_JWT_ALGORITHM = 'HS256'


# =============================================================================
# FIXTURES: Application & Database
# =============================================================================

# Global reference to db instance to avoid import issues
_test_db_instance = None


def _get_db_instance():
    """
    Get the SQLAlchemy db instance from the db package.

    This uses importlib to avoid naming conflicts with db.db module.
    """
    import importlib
    db_package = importlib.import_module('db')
    return db_package.db


@pytest.fixture(scope='session')
def app():
    """
    Create an isolated test Flask application.

    This creates a minimal Flask app with SQLite database that doesn't
    require production dependencies like Redis, SocketIO, or MariaDB.
    """
    global _test_db_instance
    from flask import Flask

    # Create a new Flask app for testing
    test_app = Flask(__name__)
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_pre_ping': True,
        },
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': TEST_JWT_SECRET,
        'AUTHENTIK_DISABLED': True,
        'SYSTEM_ADMIN_API_KEY': 'test-system-api-key-12345',
    })

    # Get the actual db instance using importlib to avoid naming conflict
    _test_db_instance = _get_db_instance()
    _test_db_instance.init_app(test_app)

    # Store db on app for easy access
    test_app.db = _test_db_instance

    # Import all models to ensure they're registered
    with test_app.app_context():
        # Import models - they use the same db instance we just initialized
        from db.tables import User, Role, Permission, UserRole, RolePermission, UserPermission  # noqa: F401

        # Create all tables
        _test_db_instance.create_all()

    # Register blueprints for route testing
    _register_test_blueprints(test_app)

    return test_app


def _register_test_blueprints(app):
    """
    Register test blueprints for testing auth decorators.

    Instead of trying to import the real routes (which have complex dependencies),
    we create simple test routes that use the decorators we want to test.
    """
    from flask import Blueprint, jsonify, g

    # =========================================================================
    # Test API Blueprint - for testing auth decorators
    # =========================================================================
    test_api_bp = Blueprint('test_api', __name__)

    @test_api_bp.route('/health')
    def health():
        """Health check endpoint - no auth required."""
        return jsonify({'status': 'ok', 'message': 'Server is running'})

    @test_api_bp.route('/users/me')
    def get_me():
        """Protected route requiring authentik_required decorator."""
        try:
            from auth.decorators import authentik_required

            @authentik_required
            def _get_me():
                user = g.authentik_user
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                    }
                })
            return _get_me()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @test_api_bp.route('/admin/users')
    def admin_users():
        """Admin-only route for testing permission checks."""
        try:
            from auth.decorators import authentik_required
            from decorators.permission_decorator import require_permission

            @authentik_required
            @require_permission('admin:users:manage')
            def _admin_users():
                return jsonify({'success': True, 'users': []})
            return _admin_users()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Register the test blueprint
    app.register_blueprint(test_api_bp, url_prefix='/api')

    # =========================================================================
    # Test Auth Blueprint - for testing auth routes
    # =========================================================================
    test_auth_bp = Blueprint('test_auth', __name__)

    @test_auth_bp.route('/health_check')
    def auth_health_check():
        """Auth health check - no auth required."""
        return jsonify({'success': True, 'message': 'Auth service running'})

    @test_auth_bp.route('/login', methods=['POST'])
    def login():
        """Login endpoint placeholder."""
        from flask import request
        data = request.get_json() or {}
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password required'}), 400
        return jsonify({'success': True, 'message': 'Login endpoint (test)'})

    @test_auth_bp.route('/validate')
    def validate():
        """Token validation endpoint."""
        try:
            from auth.decorators import authentik_required

            @authentik_required
            def _validate():
                user = g.authentik_user
                return jsonify({'success': True, 'valid': True, 'username': user.username})
            return _validate()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @test_auth_bp.route('/admin-check')
    def admin_check():
        """Admin check endpoint."""
        try:
            from auth.decorators import authentik_required
            from decorators.permission_decorator import require_permission

            @authentik_required
            @require_permission('admin:users:manage')
            def _admin_check():
                return jsonify({'success': True, 'is_admin': True})
            return _admin_check()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Register auth blueprint at both paths for compatibility
    app.register_blueprint(test_auth_bp, url_prefix='/auth')

    # =========================================================================
    # Test Authentik Blueprint - /auth/authentik/* routes for integration tests
    # =========================================================================
    test_authentik_bp = Blueprint('test_authentik', __name__)

    @test_authentik_bp.route('/health_check')
    def authentik_health_check():
        """Authentik health check - no auth required."""
        return jsonify({'success': True, 'status': 'running', 'message': 'Authentik service running'})

    @test_authentik_bp.route('/login', methods=['POST'])
    def authentik_login():
        """Authentik login endpoint."""
        from flask import request
        data = request.get_json() if request.is_json else None
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        # In tests, always return success for valid inputs
        return jsonify({'success': True, 'message': 'Login successful (test)'})

    @test_authentik_bp.route('/me')
    def authentik_me():
        """Authentik user info endpoint - requires auth."""
        try:
            from auth.decorators import authentik_required

            @authentik_required
            def _me():
                user = g.authentik_user
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                    }
                })
            return _me()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @test_authentik_bp.route('/validate')
    def authentik_validate():
        """Authentik token validation endpoint."""
        try:
            from auth.decorators import authentik_required

            @authentik_required
            def _validate():
                user = g.authentik_user
                return jsonify({'success': True, 'valid': True, 'username': user.username})
            return _validate()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @test_authentik_bp.route('/admin/check')
    def authentik_admin_check():
        """Authentik admin check endpoint."""
        try:
            from auth.decorators import authentik_required
            from decorators.permission_decorator import require_permission

            @authentik_required
            @require_permission('admin:users:manage')
            def _admin_check():
                return jsonify({'success': True, 'is_admin': True})
            return _admin_check()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Register authentik blueprint
    app.register_blueprint(test_authentik_bp, url_prefix='/auth/authentik')

    # =========================================================================
    # Test Chatbot Blueprint
    # =========================================================================
    test_chatbot_bp = Blueprint('test_chatbots', __name__)

    @test_chatbot_bp.route('')
    @test_chatbot_bp.route('/')
    def list_chatbots():
        """List chatbots - requires auth."""
        try:
            from auth.decorators import authentik_required

            @authentik_required
            def _list():
                return jsonify({'success': True, 'chatbots': []})
            return _list()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    app.register_blueprint(test_chatbot_bp, url_prefix='/api/chatbots')

    # =========================================================================
    # Test RAG Blueprint
    # =========================================================================
    test_rag_bp = Blueprint('test_rag', __name__)

    @test_rag_bp.route('/collections')
    def list_collections():
        """List RAG collections - requires auth."""
        try:
            from auth.decorators import authentik_required

            @authentik_required
            def _list():
                return jsonify({'success': True, 'collections': []})
            return _list()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    app.register_blueprint(test_rag_bp, url_prefix='/api/rag')

    # =========================================================================
    # Test Ranking Blueprint
    # =========================================================================
    test_ranking_bp = Blueprint('test_rankings', __name__)

    @test_ranking_bp.route('/email_threads/rankings')
    def list_rankings():
        """List rankings - requires auth."""
        try:
            from auth.decorators import authentik_required

            @authentik_required
            def _list():
                return jsonify({'success': True, 'rankings': []})
            return _list()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    app.register_blueprint(test_ranking_bp, url_prefix='/api')

    # =========================================================================
    # Test Rating Blueprint
    # =========================================================================
    test_rating_bp = Blueprint('test_ratings', __name__)

    @test_rating_bp.route('/email_threads/ratings')
    def list_ratings():
        """List ratings - requires auth."""
        try:
            from auth.decorators import authentik_required

            @authentik_required
            def _list():
                return jsonify({'success': True, 'ratings': []})
            return _list()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    app.register_blueprint(test_rating_bp, url_prefix='/api')

    # =========================================================================
    # Debug Blueprint
    # =========================================================================
    debug_bp = Blueprint('test_debug', __name__)

    @debug_bp.route('/info')
    def debug_info():
        """Debug info - requires system API key."""
        from flask import request
        # Check both header and query param (matches system_api_key_required decorator)
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        expected_key = os.environ.get('SYSTEM_ADMIN_API_KEY', 'test-system-api-key-12345')
        if api_key != expected_key:
            return jsonify({'error': 'Invalid API key'}), 401
        return jsonify({'success': True, 'info': 'Debug endpoint'})

    app.register_blueprint(debug_bp, url_prefix='/debug')


@pytest.fixture(scope='function')
def db(app):
    """Create database tables for each test function."""
    global _test_db_instance

    # Use the db instance stored on the app (avoids import issues with db.db module)
    _db = app.db

    with app.app_context():
        # Tables were created in app fixture, but we need to clean up between tests
        # Drop and recreate all tables for test isolation
        _db.drop_all()
        _db.create_all()

        # Seed basic roles for testing
        _seed_test_roles(_db)

        yield _db

        _db.session.remove()
        _db.drop_all()


def _seed_test_roles(db_instance):
    """Seed basic roles and permissions for testing."""
    from db.tables import Role, Permission, RolePermission

    # Create roles: (role_name, display_name, description)
    roles_data = [
        ('admin', 'Administrator', 'Administrator with full access'),
        ('researcher', 'Researcher', 'Researcher with evaluation access'),
        ('viewer', 'Viewer', 'Viewer with read-only access'),
        ('chatbot_manager', 'Chatbot Manager', 'Chatbot manager'),
    ]

    roles = {}
    for role_name, display_name, description in roles_data:
        existing = Role.query.filter_by(role_name=role_name).first()
        if not existing:
            role = Role(role_name=role_name, display_name=display_name, description=description)
            db_instance.session.add(role)
            roles[role_name] = role
        else:
            roles[role_name] = existing

    db_instance.session.commit()

    # Create permissions: (permission_key, display_name, category, description)
    permissions_data = [
        ('feature:ranking:view', 'View Rankings', 'feature', 'View rankings'),
        ('feature:ranking:edit', 'Edit Rankings', 'feature', 'Edit rankings'),
        ('feature:rating:view', 'View Ratings', 'feature', 'View ratings'),
        ('feature:rating:edit', 'Edit Ratings', 'feature', 'Edit ratings'),
        ('feature:chatbots:view', 'View Chatbots', 'feature', 'View chatbots'),
        ('feature:chatbots:edit', 'Edit Chatbots', 'feature', 'Edit chatbots'),
        ('feature:rag:view', 'View RAG', 'feature', 'View RAG'),
        ('feature:rag:edit', 'Edit RAG', 'feature', 'Edit RAG'),
        ('admin:permissions:manage', 'Manage Permissions', 'admin', 'Manage permissions'),
        ('admin:users:manage', 'Manage Users', 'admin', 'Manage users'),
        ('admin:system:configure', 'Configure System', 'admin', 'Configure system'),
    ]

    permissions = {}
    for perm_key, display_name, category, description in permissions_data:
        existing = Permission.query.filter_by(permission_key=perm_key).first()
        if not existing:
            perm = Permission(
                permission_key=perm_key,
                display_name=display_name,
                category=category,
                description=description
            )
            db_instance.session.add(perm)
            permissions[perm_key] = perm
        else:
            permissions[perm_key] = existing

    db_instance.session.commit()

    # Assign permissions to roles
    admin_role = roles.get('admin')
    researcher_role = roles.get('researcher')
    viewer_role = roles.get('viewer')

    # Admin gets all permissions
    if admin_role:
        for perm in permissions.values():
            existing = RolePermission.query.filter_by(
                role_id=admin_role.id, permission_id=perm.id
            ).first()
            if not existing:
                db_instance.session.add(RolePermission(
                    role_id=admin_role.id,
                    permission_id=perm.id
                ))

    # Researcher gets view + edit for evaluation
    if researcher_role:
        research_perms = ['feature:ranking:view', 'feature:ranking:edit',
                        'feature:rating:view', 'feature:rating:edit']
        for perm_name in research_perms:
            perm = permissions.get(perm_name)
            if perm:
                existing = RolePermission.query.filter_by(
                    role_id=researcher_role.id, permission_id=perm.id
                ).first()
                if not existing:
                    db_instance.session.add(RolePermission(
                        role_id=researcher_role.id,
                        permission_id=perm.id
                    ))

    # Viewer gets view permissions only
    if viewer_role:
        view_perms = ['feature:ranking:view', 'feature:rating:view',
                     'feature:chatbots:view', 'feature:rag:view']
        for perm_name in view_perms:
            perm = permissions.get(perm_name)
            if perm:
                existing = RolePermission.query.filter_by(
                    role_id=viewer_role.id, permission_id=perm.id
                ).first()
                if not existing:
                    db_instance.session.add(RolePermission(
                        role_id=viewer_role.id,
                        permission_id=perm.id
                    ))

    db_instance.session.commit()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def app_context(app, db):
    """Provide application context with database."""
    with app.app_context():
        yield


# =============================================================================
# FIXTURES: Test Users
# =============================================================================

@pytest.fixture
def mock_user(db, app):
    """Create a basic viewer user."""
    from db.tables import User

    with app.app_context():
        user = User(
            username='testuser',
            password_hash='test-password-hash',
            api_key='test-api-key-viewer',
            collab_color='#FF5733',
            avatar_seed='test-avatar-seed',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        # Refresh to ensure ID is loaded
        db.session.refresh(user)
        return user


@pytest.fixture
def admin_user(db, app):
    """Create an admin user with admin role."""
    from db.tables import User, Role, UserRole

    with app.app_context():
        user = User(
            username='admin',
            password_hash='test-password-hash',
            api_key='test-api-key-admin',
            collab_color='#33FF57',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        # Assign admin role
        admin_role = Role.query.filter_by(role_name='admin').first()
        if admin_role:
            user_role = UserRole(
                username='admin',
                role_id=admin_role.id,
                assigned_by='test',
                assigned_at=datetime.utcnow()
            )
            db.session.add(user_role)
            db.session.commit()

        db.session.refresh(user)
        return user


@pytest.fixture
def researcher_user(db, app):
    """Create a researcher user with researcher role."""
    from db.tables import User, Role, UserRole

    with app.app_context():
        user = User(
            username='researcher',
            password_hash='test-password-hash',
            api_key='test-api-key-researcher',
            collab_color='#5733FF',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        # Assign researcher role
        researcher_role = Role.query.filter_by(role_name='researcher').first()
        if researcher_role:
            user_role = UserRole(
                username='researcher',
                role_id=researcher_role.id,
                assigned_by='test',
                assigned_at=datetime.utcnow()
            )
            db.session.add(user_role)
            db.session.commit()

        db.session.refresh(user)
        return user


@pytest.fixture
def viewer_user(db, app):
    """Create a viewer user with viewer role."""
    from db.tables import User, Role, UserRole

    with app.app_context():
        user = User(
            username='viewer',
            password_hash='test-password-hash',
            api_key='test-api-key-viewer-role',
            collab_color='#7733FF',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        # Assign viewer role
        viewer_role = Role.query.filter_by(role_name='viewer').first()
        if viewer_role:
            user_role = UserRole(
                username='viewer',
                role_id=viewer_role.id,
                assigned_by='test',
                assigned_at=datetime.utcnow()
            )
            db.session.add(user_role)
            db.session.commit()

        db.session.refresh(user)
        return user


@pytest.fixture
def locked_user(db, app):
    """Create a locked/inactive user."""
    from db.tables import User

    with app.app_context():
        user = User(
            username='locked_user',
            password_hash='test-password-hash',
            api_key='test-api-key-locked',
            is_active=False
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture
def deleted_user(db, app):
    """Create a deleted user."""
    from db.tables import User

    with app.app_context():
        user = User(
            username='deleted_user',
            password_hash='test-password-hash',
            api_key='test-api-key-deleted',
            is_active=True,
            deleted_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


# =============================================================================
# FIXTURES: JWT Tokens
# =============================================================================

def create_test_token(username: str, groups: list = None, expired: bool = False,
                      extra_claims: dict = None) -> str:
    """Helper function to create test JWT tokens."""
    if groups is None:
        groups = ['viewer']

    exp_time = datetime.utcnow() - timedelta(hours=1) if expired else datetime.utcnow() + timedelta(hours=1)

    payload = {
        'sub': f'{username}-user-id',
        'preferred_username': username,
        'groups': groups,
        'exp': exp_time,
        'iat': datetime.utcnow(),
        'iss': os.environ.get('AUTHENTIK_ISSUER_URL', 'http://test-authentik:9000/application/o/llars-backend/'),
        'aud': 'llars-backend',
        'email': f'{username}@test.local',
        'name': username.title()
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)


@pytest.fixture
def valid_token():
    """Generate a valid viewer token."""
    return create_test_token('testuser', groups=['viewer'])


@pytest.fixture
def admin_token():
    """Generate an admin token."""
    return create_test_token('admin', groups=['admin', 'authentik Admins'])


@pytest.fixture
def researcher_token():
    """Generate a researcher token."""
    return create_test_token('researcher', groups=['researcher'])


@pytest.fixture
def expired_token():
    """Generate an expired token."""
    return create_test_token('testuser', groups=['viewer'], expired=True)


@pytest.fixture
def deleted_user_token():
    """Token for a deleted user."""
    return create_test_token('deleted_user', groups=['viewer'])


@pytest.fixture
def locked_user_token():
    """Token for a locked user."""
    return create_test_token('locked_user', groups=['viewer'])


# =============================================================================
# FIXTURES: Authenticated Clients
# =============================================================================

class AuthenticatedTestClient:
    """Wrapper for Flask test client with authentication headers."""

    def __init__(self, test_client, token):
        self._client = test_client
        self._token = token
        self._headers = {'Authorization': f'Bearer {token}'}

    def get(self, *args, **kwargs):
        kwargs.setdefault('headers', {}).update(self._headers)
        return self._client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        kwargs.setdefault('headers', {}).update(self._headers)
        return self._client.post(*args, **kwargs)

    def put(self, *args, **kwargs):
        kwargs.setdefault('headers', {}).update(self._headers)
        return self._client.put(*args, **kwargs)

    def patch(self, *args, **kwargs):
        kwargs.setdefault('headers', {}).update(self._headers)
        return self._client.patch(*args, **kwargs)

    def delete(self, *args, **kwargs):
        kwargs.setdefault('headers', {}).update(self._headers)
        return self._client.delete(*args, **kwargs)


@pytest.fixture
def authenticated_client(client, valid_token):
    """Client with valid viewer authentication."""
    return AuthenticatedTestClient(client, valid_token)


@pytest.fixture
def authenticated_client_admin(client, admin_token):
    """Client with admin authentication."""
    return AuthenticatedTestClient(client, admin_token)


@pytest.fixture
def authenticated_client_viewer(client, valid_token):
    """Alias for viewer client."""
    return AuthenticatedTestClient(client, valid_token)


@pytest.fixture
def authenticated_client_researcher(client, researcher_token):
    """Client with researcher authentication."""
    return AuthenticatedTestClient(client, researcher_token)


# =============================================================================
# FIXTURES: System API Key
# =============================================================================

@pytest.fixture
def system_api_key():
    """Return the test system API key."""
    return os.environ.get('SYSTEM_ADMIN_API_KEY', 'test-system-api-key-12345')


# =============================================================================
# FIXTURES: Token Validation Mocking
# =============================================================================

@pytest.fixture
def mock_token_validation(app):
    """
    Mock the OIDC token validation to accept test tokens.
    This is essential for testing auth decorators without real Authentik.
    """
    def _mock_validate(token):
        try:
            payload = jwt.decode(token, TEST_JWT_SECRET, algorithms=[TEST_JWT_ALGORITHM],
                               audience='llars-backend')
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # Try to patch both locations where validate_token might be imported
    patches = []

    try:
        patches.append(patch('auth.oidc_validator.validate_token', side_effect=_mock_validate))
    except Exception:
        pass

    try:
        patches.append(patch('auth.decorators.validate_token', side_effect=_mock_validate))
    except Exception:
        pass

    # Start all patches
    for p in patches:
        p.start()

    yield

    # Stop all patches
    for p in patches:
        p.stop()


# =============================================================================
# FIXTURES: Permission Service Mock
# =============================================================================

@pytest.fixture
def permission_service(app, db):
    """Create a permission service instance for testing."""
    from services.permission_service import PermissionService

    with app.app_context():
        return PermissionService()


# =============================================================================
# FIXTURES: Database Seeders (additional)
# =============================================================================

@pytest.fixture
def seed_roles(db, app):
    """Seed basic roles for testing (standalone fixture)."""
    from db.tables import Role

    with app.app_context():
        roles = []
        for role_name, display_name, desc in [
            ('admin', 'Administrator', 'Admin'),
            ('researcher', 'Researcher', 'Researcher'),
            ('viewer', 'Viewer', 'Viewer'),
            ('chatbot_manager', 'Chatbot Manager', 'CM')
        ]:
            existing = Role.query.filter_by(role_name=role_name).first()
            if existing:
                roles.append(existing)
            else:
                role = Role(role_name=role_name, display_name=display_name, description=desc)
                db.session.add(role)
                roles.append(role)
        db.session.commit()
        return roles


@pytest.fixture
def seed_permissions(db, app, seed_roles):
    """Seed basic permissions for testing (standalone fixture)."""
    from db.tables import Permission

    with app.app_context():
        permissions = []
        for perm_key, display_name, category, desc in [
            ('feature:ranking:view', 'View Rankings', 'feature', 'View'),
            ('feature:ranking:edit', 'Edit Rankings', 'feature', 'Edit'),
            ('admin:permissions:manage', 'Manage Permissions', 'admin', 'Manage'),
        ]:
            existing = Permission.query.filter_by(permission_key=perm_key).first()
            if existing:
                permissions.append(existing)
            else:
                perm = Permission(
                    permission_key=perm_key,
                    display_name=display_name,
                    category=category,
                    description=desc
                )
                db.session.add(perm)
                permissions.append(perm)
        db.session.commit()
        return permissions
