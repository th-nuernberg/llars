"""
Route Tests Configuration
==========================

Provides a Flask test app with REAL blueprints registered (unlike the parent
conftest which uses simplified test blueprints).

This allows us to test actual route handler functions through the HTTP layer,
exercising routes + services + decorators + auth simultaneously.
"""

import os
import sys
import pytest

# Ensure the app dir is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'app'))


def _import_all_models():
    """Import ALL models to ensure they are registered with SQLAlchemy metadata."""
    from db.models.user import User, UserGroup  # noqa
    from db.models.permission import (  # noqa
        Permission, Role, RolePermission, UserPermission, UserRole, PermissionAuditLog
    )
    from db.models.scenario import (  # noqa
        FeatureFunctionType, EmailThread, Message, FeatureType,
        ConsultingCategoryType, UserConsultingCategorySelection, Feature,
        UserFeatureRanking, UserFeatureRating, RatingScenarios, ScenarioUsers,
        ScenarioThreads, ScenarioThreadDistribution, UserMailHistoryRating,
        UserMessageRating, UserPrompt, UserPromptShare, PromptCommit,
        ComparisonSession, ComparisonMessage, ComparisonEvaluation
    )
    from db.models.chatbot import (  # noqa
        Chatbot, ChatbotPromptSettings, ChatbotUserAccess, ChatbotCollection,
        ChatbotConversation, ChatbotMessage
    )
    from db.models.rag import (  # noqa
        RAGCollection, RAGCollectionPermission, CollectionDocumentLink,
        RAGDocument, RAGDocumentChunk, RAGDocumentVersion, RAGRetrievalLog,
        RAGDocumentPermission, CollectionEmbedding, RAGProcessingQueue
    )
    from db.models.llm_model import LLMModel  # noqa
    from db.models.judge import (  # noqa
        PillarThread, JudgeSession, JudgeComparison, JudgeEvaluation, PillarStatistics
    )
    from db.models.analytics_settings import AnalyticsSettings  # noqa
    from db.models.system_settings import SystemSettings  # noqa
    from db.models.system_event import SystemEvent  # noqa
    from db.models.oncoco import (  # noqa
        OnCoCoAnalysis, OnCoCoSentenceLabel, OnCoCoPillarStatistics, OnCoCoTransitionMatrix
    )
    from db.models.markdown_collab import (  # noqa
        MarkdownWorkspace, MarkdownWorkspaceMember, MarkdownDocument, MarkdownCommit
    )
    from db.models.latex_collab import (  # noqa
        LatexWorkspace, LatexWorkspaceMember, LatexDocument, LatexAsset,
        LatexCommit, LatexCompileJob, LatexComment
    )
    from db.models.kaimo import (  # noqa
        KaimoCase, KaimoDocument, KaimoCategory, KaimoSubcategory, KaimoHint,
        KaimoCaseCategory, KaimoAIContent, KaimoUserAssessment, KaimoHintAssignment,
        KaimoCasePermission
    )
    from db.models.authenticity import AuthenticityConversation, UserAuthenticityVote  # noqa
    from db.models.zotero import ZoteroConnection, WorkspaceZoteroLibrary, ZoteroSyncLog  # noqa
    from db.models.prompt_template import PromptTemplate  # noqa
    from db.models.llm_usage_tracking import LLMUsageTracking, UserTokenBudget  # noqa
    from db.models.llm_task_result import LLMTaskResult  # noqa
    from db.models.conference import Conference, Paper, PaperAuthor  # noqa
    from db.models.referral import ReferralCampaign, ReferralLink, ReferralRegistration  # noqa
    from db.models.generation import GenerationJob, GeneratedOutput  # noqa
    from db.models.scenario_stats_cache import ScenarioStatsCache  # noqa
    from db.models.user_llm_provider import UserLLMProvider  # noqa
    try:
        from db.models.user_llm_provider import UserLLMProviderShare  # noqa
    except ImportError:
        pass
    from db.models.messaging import (  # noqa
        MessagingConversation, MessagingParticipant, MessagingMessage,
        MessagingAttachment, MessagingReaction, MessagingReadReceipt,
        MessagingEncryptionKey, MessagingAIKeyGrant,
        MessagingCall, MessagingCallParticipant, MessagingLinkPreview
    )


@pytest.fixture(scope='session')
def real_app():
    """
    Create a Flask test app with ALL real blueprints registered.

    This differs from the parent conftest's `app` fixture which only
    registers simplified test blueprints for testing decorators.
    """
    from flask import Flask

    # Patch MySQL types for SQLite BEFORE model imports
    from tests.conftest import _patch_mysql_types_for_sqlite, TEST_JWT_SECRET
    _patch_mysql_types_for_sqlite()

    from db.database import db as _db

    test_app = Flask(__name__)
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': {'pool_pre_ping': True},
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': TEST_JWT_SECRET,
        'AUTHENTIK_DISABLED': True,
        'SYSTEM_ADMIN_API_KEY': 'test-system-api-key-12345',
    })

    _db.init_app(test_app)
    test_app.db = _db

    with test_app.app_context():
        _import_all_models()
        _db.create_all()

    # Register ALL real blueprints
    from routes.registry import register_all_blueprints
    register_all_blueprints(test_app)

    return test_app


@pytest.fixture(scope='function')
def rdb(real_app):
    """Create fresh database tables for each test function (route test variant)."""
    _db = real_app.db

    with real_app.app_context():
        _db.drop_all()
        _import_all_models()
        _db.create_all()

        # Seed basic roles and permissions
        _seed_roles_and_permissions(_db)

        yield _db

        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()


def _seed_roles_and_permissions(db_instance):
    """Seed roles and permissions for route testing."""
    from db.models.permission import Permission, Role, RolePermission

    roles_data = [
        ('admin', 'Administrator', 'Administrator with full access'),
        ('researcher', 'Researcher', 'Researcher'),
        ('evaluator', 'Evaluator', 'Evaluator'),
        ('chatbot_manager', 'Chatbot Manager', 'Chatbot manager'),
    ]
    roles = {}
    for name, display, desc in roles_data:
        role = Role.query.filter_by(role_name=name).first()
        if not role:
            role = Role(role_name=name, display_name=display, description=desc)
            db_instance.session.add(role)
        roles[name] = role
    db_instance.session.commit()

    permissions_data = [
        ('feature:ranking:view', 'View Rankings', 'feature'),
        ('feature:ranking:edit', 'Edit Rankings', 'feature'),
        ('feature:ranking:evaluate', 'Evaluate Rankings', 'feature'),
        ('feature:rating:view', 'View Ratings', 'feature'),
        ('feature:rating:edit', 'Edit Ratings', 'feature'),
        ('feature:chatbots:view', 'View Chatbots', 'feature'),
        ('feature:chatbots:edit', 'Edit Chatbots', 'feature'),
        ('feature:chatbots:delete', 'Delete Chatbots', 'feature'),
        ('feature:chatbots:share', 'Share Chatbots', 'feature'),
        ('feature:rag:view', 'View RAG', 'feature'),
        ('feature:rag:edit', 'Edit RAG', 'feature'),
        ('feature:rag:delete', 'Delete RAG', 'feature'),
        ('feature:rag:share', 'Share RAG', 'feature'),
        ('feature:llm:view', 'View LLM', 'feature'),
        ('feature:generation:create', 'Create Generation', 'feature'),
        ('feature:generation:view', 'View Generation', 'feature'),
        ('feature:generation:manage', 'Manage Generation', 'feature'),
        ('feature:generation:export', 'Export Generation', 'feature'),
        ('feature:generation:to_scenario', 'Generation to Scenario', 'feature'),
        ('admin:permissions:manage', 'Manage Permissions', 'admin'),
        ('admin:users:manage', 'Manage Users', 'admin'),
        ('admin:system:configure', 'Configure System', 'admin'),
        ('admin:roles:manage', 'Manage Roles', 'admin'),
        ('data:manage_scenarios', 'Manage Scenarios', 'data'),
        ('data:import', 'Data Import', 'data'),
    ]
    permissions = {}
    for perm_key, display, category in permissions_data:
        perm = Permission.query.filter_by(permission_key=perm_key).first()
        if not perm:
            perm = Permission(
                permission_key=perm_key,
                display_name=display,
                category=category,
                description=display
            )
            db_instance.session.add(perm)
        permissions[perm_key] = perm
    db_instance.session.commit()

    # Admin gets all permissions
    admin_role = roles.get('admin')
    if admin_role:
        for perm in permissions.values():
            existing = RolePermission.query.filter_by(
                role_id=admin_role.id, permission_id=perm.id
            ).first()
            if not existing:
                db_instance.session.add(
                    RolePermission(role_id=admin_role.id, permission_id=perm.id)
                )

    # Researcher gets ranking + rating + scenarios + import
    researcher_role = roles.get('researcher')
    if researcher_role:
        for key in ['feature:ranking:view', 'feature:ranking:edit',
                     'feature:ranking:evaluate', 'feature:rating:view',
                     'feature:rating:edit', 'data:manage_scenarios',
                     'data:import']:
            perm = permissions.get(key)
            if perm:
                existing = RolePermission.query.filter_by(
                    role_id=researcher_role.id, permission_id=perm.id
                ).first()
                if not existing:
                    db_instance.session.add(
                        RolePermission(role_id=researcher_role.id, permission_id=perm.id)
                    )

    # Evaluator gets view permissions
    evaluator_role = roles.get('evaluator')
    if evaluator_role:
        for key in ['feature:ranking:view', 'feature:rating:view',
                     'feature:chatbots:view', 'feature:rag:view', 'feature:llm:view']:
            perm = permissions.get(key)
            if perm:
                existing = RolePermission.query.filter_by(
                    role_id=evaluator_role.id, permission_id=perm.id
                ).first()
                if not existing:
                    db_instance.session.add(
                        RolePermission(role_id=evaluator_role.id, permission_id=perm.id)
                    )

    # Chatbot Manager gets chatbot + RAG permissions
    chatbot_manager_role = roles.get('chatbot_manager')
    if chatbot_manager_role:
        for key in ['feature:chatbots:view', 'feature:chatbots:edit',
                     'feature:chatbots:delete', 'feature:chatbots:share',
                     'feature:rag:view', 'feature:rag:edit',
                     'feature:rag:delete', 'feature:rag:share',
                     'feature:llm:view']:
            perm = permissions.get(key)
            if perm:
                existing = RolePermission.query.filter_by(
                    role_id=chatbot_manager_role.id, permission_id=perm.id
                ).first()
                if not existing:
                    db_instance.session.add(
                        RolePermission(role_id=chatbot_manager_role.id, permission_id=perm.id)
                    )

    db_instance.session.commit()


@pytest.fixture
def rclient(real_app):
    """Test client backed by the real-app (with real blueprints)."""
    return real_app.test_client()


@pytest.fixture
def radmin(rdb, real_app):
    """Create admin user in the real-app DB."""
    from db.models.user import User
    from db.models.permission import Role, UserRole
    from datetime import datetime

    with real_app.app_context():
        user = User(
            username='admin',
            password_hash='test-hash',
            api_key='test-api-key-admin',
            collab_color='#33FF57',
            is_active=True
        )
        rdb.session.add(user)
        rdb.session.commit()

        admin_role = Role.query.filter_by(role_name='admin').first()
        if admin_role:
            rdb.session.add(UserRole(
                username='admin',
                role_id=admin_role.id,
                assigned_by='test',
                assigned_at=datetime.utcnow()
            ))
            rdb.session.commit()

        rdb.session.refresh(user)
        return user


@pytest.fixture
def ruser(rdb, real_app):
    """Create a basic evaluator user in the real-app DB."""
    from db.models.user import User
    from db.models.permission import Role, UserRole
    from datetime import datetime

    with real_app.app_context():
        user = User(
            username='testuser',
            password_hash='test-hash',
            api_key='test-api-key-eval',
            collab_color='#FF5733',
            avatar_seed='test-seed',
            is_active=True
        )
        rdb.session.add(user)
        rdb.session.commit()

        # Assign evaluator role so permission checks pass
        evaluator_role = Role.query.filter_by(role_name='evaluator').first()
        if evaluator_role:
            rdb.session.add(UserRole(
                username='testuser',
                role_id=evaluator_role.id,
                assigned_by='test',
                assigned_at=datetime.utcnow()
            ))
            rdb.session.commit()

        rdb.session.refresh(user)
        return user


@pytest.fixture
def rresearcher(rdb, real_app):
    """Create a researcher user in the real-app DB."""
    from db.models.user import User
    from db.models.permission import Role, UserRole
    from datetime import datetime

    with real_app.app_context():
        user = User(
            username='researcher',
            password_hash='test-hash',
            api_key='test-api-key-researcher',
            collab_color='#5733FF',
            is_active=True
        )
        rdb.session.add(user)
        rdb.session.commit()

        researcher_role = Role.query.filter_by(role_name='researcher').first()
        if researcher_role:
            rdb.session.add(UserRole(
                username='researcher',
                role_id=researcher_role.id,
                assigned_by='test',
                assigned_at=datetime.utcnow()
            ))
            rdb.session.commit()

        rdb.session.refresh(user)
        return user


@pytest.fixture
def rmock_token(real_app):
    """Mock OIDC token validation for the real-app."""
    import jwt
    from unittest.mock import patch
    from tests.conftest import TEST_JWT_SECRET, TEST_JWT_ALGORITHM

    def _mock_validate(token):
        try:
            return jwt.decode(token, TEST_JWT_SECRET, algorithms=[TEST_JWT_ALGORITHM],
                             audience='llars-backend')
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    patches = []
    # Patch everywhere validate_token is imported
    for target in (
        'auth.oidc_validator.validate_token',
        'auth.decorators.validate_token',
        'auth.auth_utils.validate_token',
    ):
        try:
            patches.append(patch(target, side_effect=_mock_validate))
        except Exception:
            pass

    for p in patches:
        p.start()
    yield
    for p in patches:
        p.stop()


# =============================================================================
# Authenticated Client Helpers
# =============================================================================

def _make_token(username, groups=None):
    """Create a test JWT for the given username and groups."""
    from tests.conftest import create_test_token
    if groups is None:
        groups = ['evaluator']
    return create_test_token(username, groups=groups)


class _AuthClient:
    """Thin wrapper adding Bearer token to every request."""

    def __init__(self, flask_client, token):
        self._c = flask_client
        self._h = {'Authorization': f'Bearer {token}'}

    def get(self, *a, **kw):
        kw.setdefault('headers', {}).update(self._h)
        return self._c.get(*a, **kw)

    def post(self, *a, **kw):
        kw.setdefault('headers', {}).update(self._h)
        return self._c.post(*a, **kw)

    def put(self, *a, **kw):
        kw.setdefault('headers', {}).update(self._h)
        return self._c.put(*a, **kw)

    def patch(self, *a, **kw):
        kw.setdefault('headers', {}).update(self._h)
        return self._c.patch(*a, **kw)

    def delete(self, *a, **kw):
        kw.setdefault('headers', {}).update(self._h)
        return self._c.delete(*a, **kw)


@pytest.fixture
def auth_admin(rclient, radmin, rmock_token):
    """Authenticated admin test client."""
    return _AuthClient(rclient, _make_token('admin', ['admin', 'authentik Admins']))


@pytest.fixture
def auth_user(rclient, ruser, rmock_token):
    """Authenticated evaluator test client."""
    return _AuthClient(rclient, _make_token('testuser', ['evaluator']))


@pytest.fixture
def auth_researcher(rclient, rresearcher, rmock_token):
    """Authenticated researcher test client."""
    return _AuthClient(rclient, _make_token('researcher', ['researcher']))


# =============================================================================
# Scenario helpers
# =============================================================================

@pytest.fixture
def seed_function_types(rdb, real_app):
    """Seed FeatureFunctionType rows needed by scenario routes."""
    from db.models.scenario import FeatureFunctionType

    with real_app.app_context():
        types_data = [
            (1, 'ranking'),
            (2, 'rating'),
            (3, 'mail_rating'),
            (4, 'comparison'),
            (5, 'authenticity'),
            (7, 'labeling'),
        ]
        for fid, name in types_data:
            if not FeatureFunctionType.query.filter_by(function_type_id=fid).first():
                rdb.session.add(FeatureFunctionType(function_type_id=fid, name=name))
        rdb.session.commit()
        return types_data
