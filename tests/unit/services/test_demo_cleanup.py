"""
Unit tests for scripts/demo_cleanup.py — the demo end-of-life job.

Covers WP8 of the IJCAI conference demo: 7 days after registration a
``demo-ijcai-*`` account must lose ALL permissions (empty ``demo_expired`` role,
archived memberships) while staying active and able to log in.

Test IDs use the DEMOX_ prefix (demo expiry).
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cleanup_module():
    """Import the script module (app/ is on sys.path via tests/conftest.py)."""
    import importlib
    return importlib.import_module('scripts.demo_cleanup')


def _make_user(db, username, *, active=True):
    from db.models import User
    user = User(
        username=username,
        password_hash='x',
        api_key=f'key-{username}',
        is_active=active,
    )
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    return user


def _make_role(db, role_name, *, permission_keys=()):
    """Create a Role, optionally with real permissions attached."""
    from db.models import Permission, Role, RolePermission
    role = Role.query.filter_by(role_name=role_name).first()
    if role is None:
        role = Role(role_name=role_name, display_name=role_name.title())
        db.session.add(role)
        db.session.commit()
        db.session.refresh(role)
    for key in permission_keys:
        perm = Permission.query.filter_by(permission_key=key).first()
        if perm is None:
            perm = Permission(permission_key=key, display_name=key, category='feature')
            db.session.add(perm)
            db.session.commit()
            db.session.refresh(perm)
        link_exists = RolePermission.query.filter_by(
            role_id=role.id, permission_id=perm.id
        ).first()
        if link_exists is None:
            db.session.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db.session.commit()
    return role


def _assign_role(db, username, role_name):
    from db.models import Role, UserRole
    role = Role.query.filter_by(role_name=role_name).first()
    db.session.add(UserRole(username=username, role_id=role.id, assigned_by='test'))
    db.session.commit()


def _role_names(username):
    from db.models import Role, UserRole
    return sorted(
        r.role_name for r in Role.query
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.username == username).all()
    )


def _make_link(db, slug='ijcai'):
    from db.models.referral import ReferralCampaign, ReferralLink
    campaign = ReferralCampaign.query.filter_by(name='Demo expiry').first()
    if campaign is None:
        campaign = ReferralCampaign(name='Demo expiry', status='active', created_by='admin')
        db.session.add(campaign)
        db.session.commit()
        db.session.refresh(campaign)
    link = ReferralLink(
        campaign_id=campaign.id,
        slug=slug,
        code=f'code-{slug}',
        role_name='ijcai_reviewer',
        created_by='admin',
    )
    db.session.add(link)
    db.session.commit()
    db.session.refresh(link)
    return link


def _register(db, username, link, *, days_ago):
    from db.models.referral import ReferralRegistration
    reg = ReferralRegistration(
        link_id=link.id,
        username=username,
        registered_at=datetime.now() - timedelta(days=days_ago),
    )
    db.session.add(reg)
    db.session.commit()
    return reg


def _make_scenario(db, created_by='ijcai_demo', name='IJCAI Demo Rating'):
    from db.models import RatingScenarios
    scenario = RatingScenarios(scenario_name=name, created_by=created_by)
    db.session.add(scenario)
    db.session.commit()
    db.session.refresh(scenario)
    return scenario


def _make_membership(db, scenario, user, *, days_ago=0):
    from db.models import MembershipStatus, ScenarioUsers
    su = ScenarioUsers(
        scenario_id=scenario.id,
        user_id=user.id,
        evaluation_role='assessor',
        membership_status=MembershipStatus.ACTIVE,
        invited_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.session.add(su)
    db.session.commit()
    db.session.refresh(su)
    return su


def _setup_ijcai(db, *, username='demo-ijcai-abc123', days_ago=10, roles=('ijcai_reviewer',)):
    """Standard fixture: expired-role + reviewer-role, one account, one scenario."""
    _make_role(db, 'demo_expired')
    _make_role(db, 'ijcai_reviewer', permission_keys=['feature:rating:view'])
    link = _make_link(db, slug='ijcai')
    user = _make_user(db, username)
    for role_name in roles:
        _assign_role(db, username, role_name)
    _register(db, username, link, days_ago=days_ago)
    scenario = _make_scenario(db)
    membership = _make_membership(db, scenario, user)
    return link, user, scenario, membership


# ===========================================================================
# TTL boundary
# ===========================================================================

class TestTtlBoundary:
    """Only accounts older than the TTL are touched."""

    def test_DEMOX_001_young_account_is_untouched(self, app, db, app_context):
        """[DEMOX-001] A 3-day-old account keeps its role and membership."""
        from db.models import MembershipStatus
        mod = _cleanup_module()

        _, user, _, membership = _setup_ijcai(db, days_ago=3)

        summary = mod.expire_ijcai_accounts(ttl_days=7)

        assert summary['candidates'] == 0
        assert summary['expired'] == 0
        assert _role_names(user.username) == ['ijcai_reviewer']
        assert membership.membership_status == MembershipStatus.ACTIVE

    def test_DEMOX_002_account_exactly_over_ttl_is_expired(self, app, db, app_context):
        """[DEMOX-002] Registered 7 days + 1 minute ago -> expired."""
        mod = _cleanup_module()

        from db.models.referral import ReferralRegistration
        _, user, _, _ = _setup_ijcai(db, days_ago=0)
        reg = ReferralRegistration.query.filter_by(username=user.username).one()
        reg.registered_at = datetime.now() - timedelta(days=7, minutes=1)
        db.session.commit()

        summary = mod.expire_ijcai_accounts(ttl_days=7)

        assert summary['expired'] == 1
        assert _role_names(user.username) == ['demo_expired']

    def test_DEMOX_003_custom_ttl_is_honoured(self, app, db, app_context):
        """[DEMOX-003] ttl_days is a real parameter, not a hardcoded 7."""
        mod = _cleanup_module()

        _, user, _, _ = _setup_ijcai(db, days_ago=3)

        assert mod.expire_ijcai_accounts(ttl_days=7)['expired'] == 0
        assert mod.expire_ijcai_accounts(ttl_days=1)['expired'] == 1


# ===========================================================================
# Full expiry effect
# ===========================================================================

class TestExpiryEffect:
    """What an expired account looks like afterwards."""

    def test_DEMOX_010_only_demo_expired_role_remains(self, app, db, app_context):
        """[DEMOX-010] Every other role is removed, demo_expired is assigned."""
        mod = _cleanup_module()

        _make_role(db, 'evaluator', permission_keys=['feature:ranking:view'])
        _, user, _, _ = _setup_ijcai(db, roles=('ijcai_reviewer', 'evaluator'))

        mod.expire_ijcai_accounts(ttl_days=7)

        assert _role_names(user.username) == ['demo_expired']

    def test_DEMOX_011_expired_role_grants_zero_permissions(self, app, db, app_context):
        """[DEMOX-011] The end state really is permission-less (deny-by-default)."""
        from services.permission_service import PermissionService
        mod = _cleanup_module()

        _, user, _, _ = _setup_ijcai(db)
        assert PermissionService.check_permission(user.username, 'feature:rating:view')

        mod.expire_ijcai_accounts(ttl_days=7)

        assert not PermissionService.check_permission(user.username, 'feature:rating:view')

    def test_DEMOX_012_memberships_are_archived(self, app, db, app_context):
        """[DEMOX-012] Demo scenario memberships are archived with metadata."""
        from db.models import MembershipStatus
        mod = _cleanup_module()

        _, _, _, membership = _setup_ijcai(db)

        summary = mod.expire_ijcai_accounts(ttl_days=7)

        db.session.refresh(membership)
        assert summary['memberships_archived'] == 1
        assert membership.membership_status == MembershipStatus.ARCHIVED
        assert membership.archived_by == mod.CLEANUP_ACTOR
        assert membership.archived_at is not None

    def test_DEMOX_013_account_stays_active_and_present(self, app, db, app_context):
        """[DEMOX-013] Login must keep working: is_active untouched, no delete."""
        from db.models import User
        mod = _cleanup_module()

        _, user, _, _ = _setup_ijcai(db)

        mod.expire_ijcai_accounts(ttl_days=7)

        still_there = User.query.filter_by(username=user.username).first()
        assert still_there is not None
        assert still_there.is_active is True
        assert still_there.deleted_at is None

    def test_DEMOX_014_never_leaves_the_user_role_less(self, app, db, app_context):
        """[DEMOX-014] Regression: a role-less user gets 'evaluator' back on login."""
        from db.models import UserRole
        mod = _cleanup_module()

        _, user, _, _ = _setup_ijcai(db)

        mod.expire_ijcai_accounts(ttl_days=7)

        assert UserRole.query.filter_by(username=user.username).count() == 1

    def test_DEMOX_015_legacy_viewer_role_is_swept(self, app, db, app_context):
        """[DEMOX-015] unassign_role aliases 'viewer'->'evaluator'; the sweep still removes it."""
        mod = _cleanup_module()

        _make_role(db, 'evaluator')
        _make_role(db, 'viewer', permission_keys=['feature:ranking:view'])
        _, user, _, _ = _setup_ijcai(db, roles=('viewer',))

        mod.expire_ijcai_accounts(ttl_days=7)

        assert _role_names(user.username) == ['demo_expired']

    def test_DEMOX_016_other_owners_scenarios_are_untouched(self, app, db, app_context):
        """[DEMOX-016] Only ijcai_demo-owned memberships are archived."""
        from db.models import MembershipStatus
        mod = _cleanup_module()

        _, user, _, _ = _setup_ijcai(db)
        foreign = _make_scenario(db, created_by='researcher', name='Real study')
        foreign_membership = _make_membership(db, foreign, user)

        mod.expire_ijcai_accounts(ttl_days=7)

        db.session.refresh(foreign_membership)
        assert foreign_membership.membership_status == MembershipStatus.ACTIVE


# ===========================================================================
# Idempotency
# ===========================================================================

class TestIdempotency:
    """A daily re-run must be a no-op for already expired accounts."""

    def test_DEMOX_020_second_run_counts_already_expired(self, app, db, app_context):
        """[DEMOX-020] Run twice: 1 expired, then 1 already_expired / 0 expired."""
        mod = _cleanup_module()

        _setup_ijcai(db)

        first = mod.expire_ijcai_accounts(ttl_days=7)
        second = mod.expire_ijcai_accounts(ttl_days=7)

        assert (first['expired'], first['already_expired']) == (1, 0)
        assert (second['expired'], second['already_expired']) == (0, 1)
        assert second['memberships_archived'] == 0

    def test_DEMOX_021_second_run_changes_nothing(self, app, db, app_context):
        """[DEMOX-021] No extra audit-log churn / role rewrites on re-runs."""
        from db.models import PermissionAuditLog
        mod = _cleanup_module()

        _, user, _, _ = _setup_ijcai(db)

        mod.expire_ijcai_accounts(ttl_days=7)
        log_count = PermissionAuditLog.query.count()

        mod.expire_ijcai_accounts(ttl_days=7)

        assert PermissionAuditLog.query.count() == log_count
        assert _role_names(user.username) == ['demo_expired']

    def test_DEMOX_022_partially_expired_account_is_completed(self, app, db, app_context):
        """[DEMOX-022] Right role but a stale ACTIVE membership -> finish the job."""
        from db.models import MembershipStatus, Role, UserRole
        mod = _cleanup_module()

        _, user, _, membership = _setup_ijcai(db)
        # Simulate a half-finished previous run: role already swapped, membership not.
        UserRole.query.filter_by(username=user.username).delete()
        expired_role = Role.query.filter_by(role_name='demo_expired').one()
        db.session.add(UserRole(username=user.username, role_id=expired_role.id))
        db.session.commit()

        summary = mod.expire_ijcai_accounts(ttl_days=7)

        db.session.refresh(membership)
        assert summary['expired'] == 1
        assert membership.membership_status == MembershipStatus.ARCHIVED


# ===========================================================================
# Safety fences
# ===========================================================================

class TestSafetyFences:
    """The double fence: username pattern AND a registration on the ijcai link."""

    def test_DEMOX_030_real_user_who_redeemed_the_code_is_untouched(self, app, db, app_context):
        """[DEMOX-030] A registration row alone must never expire a real account."""
        mod = _cleanup_module()

        _make_role(db, 'demo_expired')
        _make_role(db, 'researcher', permission_keys=['feature:rating:view'])
        link = _make_link(db, slug='ijcai')
        real = _make_user(db, 'prof.mueller')
        _assign_role(db, 'prof.mueller', 'researcher')
        _register(db, 'prof.mueller', link, days_ago=30)

        summary = mod.expire_ijcai_accounts(ttl_days=7)

        assert summary['candidates'] == 0
        assert _role_names(real.username) == ['researcher']

    def test_DEMOX_031_matching_username_without_registration_is_untouched(self, app, db, app_context):
        """[DEMOX-031] The username pattern alone must not be enough either."""
        mod = _cleanup_module()

        _make_role(db, 'demo_expired')
        _make_role(db, 'ijcai_reviewer', permission_keys=['feature:rating:view'])
        _make_link(db, slug='ijcai')
        impostor = _make_user(db, 'demo-ijcai-handmade')
        _assign_role(db, 'demo-ijcai-handmade', 'ijcai_reviewer')

        summary = mod.expire_ijcai_accounts(ttl_days=7)

        assert summary['candidates'] == 0
        assert _role_names(impostor.username) == ['ijcai_reviewer']

    def test_DEMOX_032_registration_via_another_link_is_untouched(self, app, db, app_context):
        """[DEMOX-032] Only registrations on the 'ijcai' link count."""
        mod = _cleanup_module()

        _make_role(db, 'demo_expired')
        _make_role(db, 'ijcai_reviewer', permission_keys=['feature:rating:view'])
        _make_link(db, slug='ijcai')
        other_link = _make_link(db, slug='demo-emnlp')
        other = _make_user(db, 'demo-ijcai-fromelsewhere')
        _assign_role(db, other.username, 'ijcai_reviewer')
        _register(db, other.username, other_link, days_ago=30)

        summary = mod.expire_ijcai_accounts(ttl_days=7)

        assert summary['candidates'] == 0
        assert _role_names(other.username) == ['ijcai_reviewer']

    def test_DEMOX_033_missing_link_is_a_no_op(self, app, db, app_context):
        """[DEMOX-033] No 'ijcai' link seeded yet -> clean zero summary, no crash."""
        mod = _cleanup_module()

        summary = mod.expire_ijcai_accounts(ttl_days=7)

        assert summary['candidates'] == 0
        assert summary['expired'] == 0

    def test_DEMOX_034_registration_without_account_is_counted(self, app, db, app_context):
        """[DEMOX-034] Orphaned registration row (user deleted) is skipped, not fatal."""
        mod = _cleanup_module()

        _make_role(db, 'demo_expired')
        link = _make_link(db, slug='ijcai')
        _register(db, 'demo-ijcai-ghost', link, days_ago=30)

        summary = mod.expire_ijcai_accounts(ttl_days=7)

        assert summary['candidates'] == 1
        assert summary['missing_user'] == 1
        assert summary['expired'] == 0


# ===========================================================================
# Robustness
# ===========================================================================

class TestRobustness:
    """One broken account must not take the whole run down."""

    def test_DEMOX_040_one_broken_account_does_not_abort(self, app, db, app_context):
        """[DEMOX-040] The failing account is counted, the others still expire."""
        mod = _cleanup_module()

        _make_role(db, 'demo_expired')
        _make_role(db, 'ijcai_reviewer', permission_keys=['feature:rating:view'])
        link = _make_link(db, slug='ijcai')
        scenario = _make_scenario(db)
        for name in ('demo-ijcai-aaa', 'demo-ijcai-bbb', 'demo-ijcai-ccc'):
            user = _make_user(db, name)
            _assign_role(db, name, 'ijcai_reviewer')
            _register(db, name, link, days_ago=30)
            _make_membership(db, scenario, user)

        real_expire = mod._expire_account

        def _flaky(user, scenario_ids):
            if user.username == 'demo-ijcai-bbb':
                raise RuntimeError('boom')
            return real_expire(user, scenario_ids)

        with patch.object(mod, '_expire_account', side_effect=_flaky):
            summary = mod.expire_ijcai_accounts(ttl_days=7)

        assert summary['expired'] == 2
        assert summary['failed'] == 1
        assert _role_names('demo-ijcai-aaa') == ['demo_expired']
        assert _role_names('demo-ijcai-ccc') == ['demo_expired']
        assert _role_names('demo-ijcai-bbb') == ['ijcai_reviewer']

    def test_DEMOX_041_missing_expired_role_aborts_before_stripping(self, app, db, app_context):
        """[DEMOX-041] SAFETY: if demo_expired cannot be assigned, roles stay put."""
        mod = _cleanup_module()

        _make_role(db, 'ijcai_reviewer', permission_keys=['feature:rating:view'])
        link = _make_link(db, slug='ijcai')
        user = _make_user(db, 'demo-ijcai-noroleavail')
        _assign_role(db, user.username, 'ijcai_reviewer')
        _register(db, user.username, link, days_ago=30)

        with patch('services.permission_service.PermissionService.assign_role', return_value=False):
            summary = mod.expire_ijcai_accounts(ttl_days=7)

        assert summary['failed'] == 1
        assert summary['expired'] == 0
        assert _role_names(user.username) == ['ijcai_reviewer']

    def test_DEMOX_042_run_all_isolates_job_failures(self, app, db, app_context):
        """[DEMOX-042] A crashing membership job must not skip the IJCAI job."""
        mod = _cleanup_module()

        _setup_ijcai(db)

        with patch.object(mod, 'cleanup_demo_memberships', side_effect=RuntimeError('nope')):
            results = mod.run_all()

        assert 'error' in results['demo_memberships']
        assert results['ijcai_accounts']['expired'] == 1


# ===========================================================================
# Existing llars_demo membership cleanup (regression after the refactor)
# ===========================================================================

class TestDemoMembershipCleanup:
    """cleanup_demo_memberships still works and now uses a column that exists."""

    def test_DEMOX_050_old_demo_membership_is_archived(self, app, db, app_context):
        """[DEMOX-050] Membership older than the TTL is archived."""
        from db.models import MembershipStatus
        mod = _cleanup_module()

        scenario = _make_scenario(db, created_by='llars_demo', name='Open demo')
        visitor = _make_user(db, 'demo-open-1')
        membership = _make_membership(db, scenario, visitor, days_ago=10)

        summary = mod.cleanup_demo_memberships(ttl_days=7)

        db.session.refresh(membership)
        assert summary['archived'] == 1
        assert membership.membership_status == MembershipStatus.ARCHIVED

    def test_DEMOX_051_young_membership_and_owner_are_kept(self, app, db, app_context):
        """[DEMOX-051] Young rows and the llars_demo owner's own row survive."""
        from db.models import MembershipStatus
        mod = _cleanup_module()

        scenario = _make_scenario(db, created_by='llars_demo', name='Open demo')
        owner = _make_user(db, 'llars_demo')
        visitor = _make_user(db, 'demo-open-2')
        owner_row = _make_membership(db, scenario, owner, days_ago=90)
        young_row = _make_membership(db, scenario, visitor, days_ago=1)

        summary = mod.cleanup_demo_memberships(ttl_days=7)

        db.session.refresh(owner_row)
        db.session.refresh(young_row)
        assert summary['archived'] == 0
        assert owner_row.membership_status == MembershipStatus.ACTIVE
        assert young_row.membership_status == MembershipStatus.ACTIVE


# ===========================================================================
# The demo_expired role itself
# ===========================================================================

class TestDemoExpiredRoleSeed:
    """db/seeders/permissions.py must register the role — empty and unreachable."""

    def test_DEMOX_060_role_is_seeded_without_permissions(self, app, db, app_context):
        """[DEMOX-060] initialize_permissions creates demo_expired with 0 permissions."""
        from db.models import Role, RolePermission
        from db.seeders.permissions import initialize_permissions

        initialize_permissions(db)

        role = Role.query.filter_by(role_name='demo_expired').first()
        assert role is not None
        assert RolePermission.query.filter_by(role_id=role.id).count() == 0

    def test_DEMOX_061_role_is_not_referral_grantable(self, app, db, app_context):
        """[DEMOX-061] SECURITY: no referral link may hand out demo_expired."""
        from services.referral_service import ALLOWED_REFERRAL_ROLES

        assert 'demo_expired' not in ALLOWED_REFERRAL_ROLES


# ===========================================================================
# Seeder constant
# ===========================================================================

class TestLinkExpiry:
    """The /join/ijcai link must die on 2026-08-29."""

    def test_DEMOX_070_seeder_constant_is_end_of_2026_08_29(self, app, db, app_context):
        """[DEMOX-070] Naive local time, matching validate_link's datetime.now()."""
        import importlib
        seeder = importlib.import_module('scripts.seed_ijcai_demo')

        assert seeder.LINK_EXPIRES_AT == datetime(2026, 8, 29, 23, 59, 59)
        assert seeder.LINK_EXPIRES_AT.tzinfo is None

    def test_DEMOX_072_scenario_window_outlives_every_account(self, app, db, app_context):
        """[DEMOX-072] Scenario end (UTC) covers link expiry + account TTL.

        An ended scenario is 'completed' and the EvaluationHub hides it from
        non-owners — the original relative "+8 weeks" window expired
        mid-August and blanked the demo. The fixed date must stay after the
        last possible account activity: link death + IJCAI_TTL_DAYS.
        """
        import importlib
        seeder = importlib.import_module('scripts.seed_ijcai_demo')
        from scripts.demo_cleanup import IJCAI_TTL_DAYS

        assert seeder.SCENARIO_END_AT.tzinfo is None
        assert seeder.SCENARIO_END_AT >= (
            seeder.LINK_EXPIRES_AT + timedelta(days=IJCAI_TTL_DAYS)
        )

    def test_DEMOX_071_validate_link_rejects_an_expired_link(self, app, db, app_context):
        """[DEMOX-071] Contract check: expires_at in the past blocks registration."""
        from services.referral_service import ReferralService

        link = _make_link(db, slug='ijcai')
        link.expires_at = datetime.now() - timedelta(seconds=1)
        db.session.commit()

        with patch.object(ReferralService, 'is_referral_enabled', return_value=True), \
             patch.object(ReferralService, 'is_self_registration_enabled', return_value=True):
            ok, resolved, error = ReferralService.validate_link('ijcai')

        assert ok is False
        assert 'abgelaufen' in (error or '')
