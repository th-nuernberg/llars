"""
LLARS demo cleanup — give every time-limited demo a defined end of life.

Two independent, idempotent jobs. Both are safe to run at any time and are
executed together by :func:`run_all` (``python -m scripts.demo_cleanup``):

1. ``cleanup_demo_memberships`` — the open ``/join/demo-*`` demo (scenario owner
   ``llars_demo``). Each visitor is enrolled as ASSESSOR/VIEWER in the demo
   scenarios; to make the demo "available for one week per account" this job
   ARCHIVEs demo ``ScenarioUsers`` rows older than 7 days. The access checks
   already treat ARCHIVED memberships as non-members
   (``auth.access_control.require_scenario_membership``), so no access-path
   change is needed — after 7 days the visitor simply loses access.

2. ``expire_ijcai_accounts`` — the IJCAI 2026 conference demo (scenario owner
   ``ijcai_demo``, link ``/join/ijcai``). 7 days after registration a conference
   account loses ALL permissions: every role is replaced by the empty
   ``demo_expired`` role and its demo memberships are archived. The account
   stays ACTIVE and can still LOG IN — by product decision the visitor should
   never hit a wall of "account locked", they just find an empty LLARS.

The demo scenario OWNERs' own memberships are never archived (they are the
system accounts holding the scenarios).

Run daily (systemd timer ``llars-cleanup.timer`` via
``scripts/server/llars_cleanup.sh``, plus the nightly CI job
``maintenance:demo-cleanup``):

    docker exec llars_flask_<color> python -m scripts.demo_cleanup
"""

import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

DEMO_OWNERS = ("llars_demo",)   # demo scenario owners whose visitor memberships expire
DEMO_TTL_DAYS = 7

# --- IJCAI 2026 conference demo ---------------------------------------------
IJCAI_OWNERS = ("ijcai_demo",)          # scenario owner of the 7 conference demo scenarios
IJCAI_LINK_SLUG = "ijcai"               # referral link the conference QR points at
IJCAI_USERNAME_PREFIX = "demo-ijcai-"   # auto-generated conference accounts (see referral_routes)
IJCAI_TTL_DAYS = 7

# Terminal role for expired demo accounts: seeded with ZERO permissions in
# db/seeders/permissions.py. See _expire_account for why an EMPTY role is used
# rather than simply dropping all roles.
EXPIRED_ROLE_NAME = "demo_expired"

# Actor recorded in the permission audit log / ScenarioUsers.archived_by so the
# origin of an expiry is obvious when someone inspects a demo account later.
CLEANUP_ACTOR = "demo_cleanup"


# ---------------------------------------------------------------------------
# Shared membership helpers
# ---------------------------------------------------------------------------

def _owner_scenario_ids(owner_usernames) -> list:
    """Ids of all scenarios created by one of ``owner_usernames``."""
    from db.models import RatingScenarios

    return [s.id for s in RatingScenarios.query
            .filter(RatingScenarios.created_by.in_(owner_usernames)).all()]


def _archive_memberships(scenario_ids, *, cutoff=None, user_ids=None,
                         exclude_user_ids=None) -> int:
    """ARCHIVE the matching non-archived ``ScenarioUsers`` rows. Does NOT commit.

    Shared by both cleanups so the "expired = archived membership" convention
    (and its metadata) exists in exactly one place:

    - ``cutoff``            — only rows created before this instant (age-based expiry)
    - ``user_ids``          — only these users (per-account expiry)
    - ``exclude_user_ids``  — never touch these users (the demo owner accounts)

    Membership age is read from ``invited_at`` — the row's creation timestamp
    (default ``utcnow``). ScenarioUsers has NO ``created_at`` column; an earlier
    version of this job filtered on one and therefore died with an
    AttributeError on every run. Rows with a NULL ``invited_at`` (age unknown)
    are deliberately NOT expired.

    Returns the number of rows archived. The caller commits, so a per-user
    expiry stays atomic together with its role changes.
    """
    from db.models import ScenarioUsers, MembershipStatus

    if not scenario_ids:
        return 0
    if user_ids is not None and not user_ids:
        return 0

    q = (ScenarioUsers.query
         .filter(ScenarioUsers.scenario_id.in_(scenario_ids),
                 ScenarioUsers.membership_status != MembershipStatus.ARCHIVED))
    if cutoff is not None:
        q = q.filter(ScenarioUsers.invited_at.isnot(None),
                     ScenarioUsers.invited_at < cutoff)
    if user_ids is not None:
        q = q.filter(ScenarioUsers.user_id.in_(user_ids))
    if exclude_user_ids:
        q = q.filter(~ScenarioUsers.user_id.in_(exclude_user_ids))

    now = datetime.utcnow()
    n = 0
    for su in q.all():
        su.membership_status = MembershipStatus.ARCHIVED
        su.archived_at = now
        su.archived_by = CLEANUP_ACTOR
        n += 1
    return n


def _active_membership_count(scenario_ids, user_id) -> int:
    """How many non-archived memberships ``user_id`` still holds in those scenarios."""
    from db.models import ScenarioUsers, MembershipStatus

    if not scenario_ids:
        return 0
    return (ScenarioUsers.query
            .filter(ScenarioUsers.user_id == user_id,
                    ScenarioUsers.scenario_id.in_(scenario_ids),
                    ScenarioUsers.membership_status != MembershipStatus.ARCHIVED)
            .count())


# ---------------------------------------------------------------------------
# 1. Open demo (/join/demo-*, owner llars_demo)
# ---------------------------------------------------------------------------

def cleanup_demo_memberships(ttl_days: int = DEMO_TTL_DAYS) -> dict:
    """Archive demo ScenarioUsers rows older than ``ttl_days``. Idempotent."""
    from db import db
    from db.models import User

    # ScenarioUsers.invited_at is written with datetime.utcnow (see the model),
    # so the cutoff must use the same clock.
    cutoff = datetime.utcnow() - timedelta(days=ttl_days)

    scenario_ids = _owner_scenario_ids(DEMO_OWNERS)
    if not scenario_ids:
        return {"archived": 0, "scenarios": 0}

    # Never expire the owner's own rows (system account holding the scenarios).
    owner_ids = [u.id for u in User.query.filter(User.username.in_(DEMO_OWNERS)).all()]

    n = _archive_memberships(scenario_ids, cutoff=cutoff, exclude_user_ids=owner_ids)
    db.session.commit()
    logger.info("Demo cleanup: archived %d expired memberships across %d demo scenarios",
                n, len(scenario_ids))
    return {"archived": n, "scenarios": len(scenario_ids)}


# ---------------------------------------------------------------------------
# 2. IJCAI conference demo (/join/ijcai, owner ijcai_demo)
# ---------------------------------------------------------------------------

def _role_names_of(username: str) -> list:
    """Role names currently assigned to ``username`` (skips dangling role ids)."""
    from db import db
    from db.models import Role, UserRole

    return [row[0] for row in db.session.query(Role.role_name)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.username == username).all()]


def _is_already_expired(username: str, user_id: int, scenario_ids) -> bool:
    """True when this account is already in the terminal expired state.

    Terminal state = exactly the ``demo_expired`` role and no active membership
    left in the conference scenarios. Checked so a daily re-run reports those
    accounts separately instead of re-writing (and re-logging) them forever.
    """
    if set(_role_names_of(username)) != {EXPIRED_ROLE_NAME}:
        return False
    return _active_membership_count(scenario_ids, user_id) == 0


def _expire_account(user, scenario_ids) -> int:
    """Move ONE demo account into the terminal ``demo_expired`` state.

    Returns the number of memberships archived. Commits on success; raises on
    failure so the caller can roll back just this account.

    ORDER MATTERS — assign first, remove afterwards:
    ``auth.decorators._ensure_default_evaluator_role`` auto-grants ``evaluator``
    to any user that has NO ``user_roles`` row at all. Stripping the roles first
    would leave a role-less window, and the visitor's very next login would
    silently hand them back a working evaluator account. Keeping exactly one
    (permission-less) role at all times closes that hole permanently — that is
    the entire reason the empty ``demo_expired`` role exists.

    The account itself is deliberately left untouched: ``is_active`` stays True,
    nothing is deleted. Logging in must keep working; there is just nothing left
    to use (deny-by-default + a role with zero permissions).
    """
    from db import db
    from db.models import Role, UserRole
    from services.permission_service import PermissionService

    # assign_role is idempotent and seeds the role if the permission seeder has
    # not run yet (_resolve_role(..., seed_missing=True)). A False return means
    # the role could not be resolved at all — abort BEFORE removing anything,
    # never strip a user down to no role (see docstring).
    if not PermissionService.assign_role(user.username, EXPIRED_ROLE_NAME, CLEANUP_ACTOR):
        raise RuntimeError(f"role '{EXPIRED_ROLE_NAME}' could not be assigned")

    expired_role = Role.query.filter_by(role_name=EXPIRED_ROLE_NAME).first()

    # Remove every other role by name so the change lands in the permission
    # audit log (PermissionService._log_permission_change).
    for role_name in _role_names_of(user.username):
        if role_name == EXPIRED_ROLE_NAME:
            continue
        PermissionService.unassign_role(user.username, role_name, CLEANUP_ACTOR)

    # Defensive sweep: unassign_role resolves roles by NAME and aliases the
    # legacy 'viewer' to 'evaluator', so a legacy viewer assignment would
    # survive the loop above. Anything still attached that is not demo_expired
    # is deleted directly — a single leftover role would keep granting
    # permissions, which is exactly what must not happen here.
    leftovers = [ur for ur in UserRole.query.filter_by(username=user.username).all()
                 if not expired_role or ur.role_id != expired_role.id]
    for ur in leftovers:
        logger.warning("IJCAI expiry: force-removing leftover role_id=%s from %s",
                       ur.role_id, user.username)
        db.session.delete(ur)

    archived = _archive_memberships(scenario_ids, user_ids=[user.id])
    db.session.commit()
    return archived


def expire_ijcai_accounts(ttl_days: int = IJCAI_TTL_DAYS) -> dict:
    """Strip all permissions from IJCAI demo accounts older than ``ttl_days``.

    Selection uses a DOUBLE SAFETY FENCE — an account must BOTH
    (a) carry the auto-generated conference username pattern
        ``demo-ijcai-%`` and
    (b) have a ``referral_registrations`` row for the ``ijcai`` link.
    Condition (b) alone is not enough: an already existing, real LLARS user who
    merely REDEEMED the conference code also gets a registration row for this
    link (see ReferralService.register_user), and such an account must never be
    stripped of its permissions. Condition (a) alone is not enough either — it
    would catch a hand-made account that happens to match the pattern.

    Idempotent: accounts already in the terminal state are counted as
    ``already_expired`` and skipped without further writes or log noise. One
    broken account never aborts the run (per-account try/except + rollback).
    """
    from db import db
    from db.models import User
    from db.models.referral import ReferralLink, ReferralRegistration

    summary = {"candidates": 0, "expired": 0, "already_expired": 0,
               "missing_user": 0, "failed": 0, "memberships_archived": 0}

    link = ReferralLink.query.filter_by(slug=IJCAI_LINK_SLUG).first()
    if not link:
        logger.info("IJCAI expiry: no referral link '%s' — nothing to do", IJCAI_LINK_SLUG)
        return summary

    # ReferralRegistration.registered_at is written with the model default
    # datetime.now (LOCAL container time, TZ=Europe/Berlin) — NOT utcnow. The
    # cutoff must use the same clock or the TTL silently shifts by the UTC
    # offset. Same convention as ReferralService.validate_link, which compares
    # link.expires_at against datetime.now().
    cutoff = datetime.now() - timedelta(days=ttl_days)

    registrations = (ReferralRegistration.query
                     .filter(ReferralRegistration.link_id == link.id,
                             ReferralRegistration.registered_at < cutoff,
                             ReferralRegistration.username.like(f"{IJCAI_USERNAME_PREFIX}%"))
                     .all())
    usernames = sorted({r.username for r in registrations})
    summary["candidates"] = len(usernames)
    if not usernames:
        logger.info("IJCAI expiry: no account older than %d day(s)", ttl_days)
        return summary

    scenario_ids = _owner_scenario_ids(IJCAI_OWNERS)

    for username in usernames:
        user = User.query.filter_by(username=username).first()
        if not user:
            # Registration row without an account (user deleted) — nothing to do.
            summary["missing_user"] += 1
            continue
        try:
            if _is_already_expired(username, user.id, scenario_ids):
                summary["already_expired"] += 1
                continue
            summary["memberships_archived"] += _expire_account(user, scenario_ids)
            summary["expired"] += 1
        except Exception as exc:
            # One broken account must not abort the run for the others.
            db.session.rollback()
            summary["failed"] += 1
            logger.warning("IJCAI expiry failed for %s: %s", username, exc)

    logger.info(
        "IJCAI expiry: %d candidate(s) older than %dd — %d newly expired "
        "(%d membership(s) archived), %d already expired, %d without account, %d failed",
        summary["candidates"], ttl_days, summary["expired"],
        summary["memberships_archived"], summary["already_expired"],
        summary["missing_user"], summary["failed"],
    )
    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_all() -> dict:
    """Run every demo-lifecycle job. Entry point of the daily maintenance run.

    Each job is isolated: a failure in one must never keep the other from
    running (they cover different demos and different users).
    """
    from db import db

    results = {}
    for name, job in (("demo_memberships", cleanup_demo_memberships),
                      ("ijcai_accounts", expire_ijcai_accounts)):
        try:
            results[name] = job()
        except Exception as exc:
            db.session.rollback()
            logger.exception("Demo cleanup job '%s' failed", name)
            results[name] = {"error": str(exc)}
    return results


if __name__ == "__main__":
    import sys
    import json
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from main import app  # noqa: E402
    logging.basicConfig(level=logging.INFO)
    with app.app_context():
        print(json.dumps(run_all(), indent=2))
