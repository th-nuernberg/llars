"""
Referral Service.

Handles all referral/invitation business logic including:
- Campaign CRUD operations
- Link generation and validation
- Registration tracking
- Analytics and statistics
"""

import copy
import json
import logging
import re
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, or_

from db.database import db
from db.models.referral import (
    ReferralCampaign,
    ReferralCampaignStatus,
    ReferralLink,
    ReferralRegistration,
)
from db.models import User
from services.system_settings_service import get_setting
from services.user_profile_service import serialize_user_brief

logger = logging.getLogger(__name__)


def _anonymize_ip(ip: Optional[str]) -> Optional[str]:
    """Truncate a client IP to its network prefix for privacy-preserving storage.

    IPv4 -> /24 (last octet zeroed), IPv6 -> /48 (first 3 hextets kept). Returns
    None for empty/malformed input. We never persist the full address: the
    referral_registrations row only needs coarse origin for abuse analysis, and
    the model documents the value as anonymized.
    """
    if not ip:
        return None
    ip = ip.strip()
    if ':' in ip:  # IPv6 -> /48
        hextets = ip.split(':')
        return ':'.join(hextets[:3]) + '::'
    parts = ip.split('.')  # IPv4 -> /24
    if len(parts) == 4:
        return '.'.join(parts[:3] + ['0'])
    return None


# SECURITY: roles a PUBLIC referral self-registration link is allowed to grant.
# Referral registration is unauthenticated and creates a real account, so this
# path must never confer an elevated/privileged role. 'admin' (and any future
# admin:* bearing role) is deliberately excluded — granting admin must go
# through admin:roles:manage, not a shareable link. Enforced both at link
# create/update time (below) and as a final fence in register_via_referral.
#
# 'ijcai_reviewer' is safe here despite being "more" than evaluator: it is a
# purpose-built demo role whose permission set (see app/db/seeders/permissions.py)
# is exclusively feature-scoped — prompt engineering view/edit, batch generation
# (view/create/manage/export/to_scenario), feature:llm:view, the five evaluation
# type view/edit pairs, feature:chatbots:view, plus data:import and
# data:manage_scenarios. It carries NO admin:* permission, so a holder can build
# and evaluate their own demo content but cannot touch users, roles, referral
# links or system configuration. 'researcher' was rejected for the public IJCAI
# QR link precisely because it additionally grants referral link creation,
# Kaimo and anonymization access.
ALLOWED_REFERRAL_ROLES = frozenset({
    'evaluator', 'researcher', 'chatbot_manager', 'viewer', 'ijcai_reviewer',
})


def _validate_referral_role(role_name: Optional[str]) -> None:
    """Raise ValidationError if ``role_name`` may not be granted via a referral link."""
    if role_name is None:
        return
    if role_name not in ALLOWED_REFERRAL_ROLES:
        from decorators.error_handler import ValidationError
        raise ValidationError(
            f"Role '{role_name}' cannot be assigned via a referral link. "
            f"Allowed: {', '.join(sorted(ALLOWED_REFERRAL_ROLES))}."
        )


_HEX_COLOR_RE = re.compile(r'^#?[0-9a-fA-F]{6}$')


def _normalize_hex_color(value: Optional[str]) -> Optional[str]:
    """Validate + normalize a referral-link badge color to ``#rrggbb``.

    Returns None for None/blank input — for an update that means "clear the
    override and fall back to the deterministic auto-color". Raises
    ValidationError on a malformed value so a bad admin input surfaces instead
    of silently dropping the color.
    """
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None  # explicit clear -> auto-color
    if not _HEX_COLOR_RE.match(value):
        from decorators.error_handler import ValidationError
        raise ValidationError(f"Invalid color '{value}', expected a hex value like #b0ca97")
    if not value.startswith('#'):
        value = '#' + value
    return value.lower()


# Keys a link's provision_json may carry. Deliberately a closed set: the value
# is applied verbatim to freshly-registered accounts, so an unknown key is far
# more likely to be a typo (silently provisioning nothing) than a feature.
PROVISION_JSON_KEYS = ('clone_prompt_ids', 'share_job_ids')


def _normalize_provision_json(value: Any) -> Optional[str]:
    """Validate an admin-supplied provisioning config and return it as JSON text.

    Accepts the dict contract ``{"clone_prompt_ids": [int, ...],
    "share_job_ids": [int, ...]}`` (both keys optional), or that same object as
    a JSON string. ``None`` / ``{}`` / an all-empty config normalize to None,
    which clears the column — "this link provisions nothing".

    SECURITY / TRUST MODEL: the referenced prompt and job IDs are
    admin-trusted configuration — setting them requires ``admin:referral:manage``
    (see the create/update link routes). They are NOT validated for ownership
    here on purpose: an admin wiring a demo link is explicitly deciding that the
    source prompt's CONTENT gets copied into every registrant's account and that
    the source job's outputs become visible to them. Never expose this field on
    a self-service (user-owned) link path.

    Raises ValidationError on anything else so a malformed admin payload
    surfaces as a 400 instead of silently disabling provisioning.
    """
    from decorators.error_handler import ValidationError

    if value is None:
        return None
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            value = json.loads(raw)
        except (ValueError, TypeError):
            raise ValidationError("provision_json must be valid JSON")
    if not isinstance(value, dict):
        raise ValidationError(
            "provision_json must be an object like "
            '{"clone_prompt_ids": [1], "share_job_ids": [2]}'
        )

    unknown = sorted(set(value) - set(PROVISION_JSON_KEYS))
    if unknown:
        raise ValidationError(
            f"provision_json contains unknown key(s): {', '.join(unknown)}. "
            f"Allowed: {', '.join(PROVISION_JSON_KEYS)}."
        )

    normalized: Dict[str, List[int]] = {}
    for key in PROVISION_JSON_KEYS:
        if key not in value:
            continue
        ids = value[key]
        if not isinstance(ids, list):
            raise ValidationError(f"provision_json.{key} must be a list of integers")
        # bool is an int subclass — reject it explicitly, `true` is never an id.
        if any(not isinstance(i, int) or isinstance(i, bool) for i in ids):
            raise ValidationError(f"provision_json.{key} must be a list of integers")
        if ids:
            normalized[key] = ids

    if not normalized:
        return None  # nothing to provision -> store NULL, not an empty object
    return json.dumps(normalized)


class ReferralService:
    """Service for managing referral campaigns, links, and registrations."""

    # ==================== System Settings ====================

    @staticmethod
    def is_referral_enabled() -> bool:
        """Check if the referral system is enabled."""
        return bool(get_setting('referral_system_enabled', False))

    @staticmethod
    def is_self_registration_enabled() -> bool:
        """Check if self-registration via referral is enabled."""
        return bool(get_setting('self_registration_enabled', False))

    @staticmethod
    def get_default_role() -> str:
        """Get the default role for new referral registrations."""
        return get_setting('default_referral_role', 'evaluator')

    # ==================== Campaign Management ====================

    @staticmethod
    def create_campaign(
        name: str,
        created_by: str,
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_registrations: Optional[int] = None,
        config: Optional[Dict] = None
    ) -> ReferralCampaign:
        """
        Create a new referral campaign.

        Args:
            name: Campaign name
            created_by: Username of creator
            description: Optional description
            start_date: Optional start date
            end_date: Optional end date
            max_registrations: Optional max registrations
            config: Optional JSON config

        Returns:
            Created ReferralCampaign instance
        """
        campaign = ReferralCampaign(
            name=name,
            description=description,
            status=ReferralCampaignStatus.DRAFT.value,
            start_date=start_date,
            end_date=end_date,
            max_registrations=max_registrations,
            created_by=created_by,
            config_json=config
        )
        db.session.add(campaign)
        db.session.commit()
        logger.info(f"Created referral campaign '{name}' (id={campaign.id}) by {created_by}")
        return campaign

    @staticmethod
    def get_campaign(campaign_id: int) -> Optional[ReferralCampaign]:
        """Get a campaign by ID."""
        return ReferralCampaign.query.get(campaign_id)

    @staticmethod
    def list_campaigns(include_archived: bool = False) -> List[ReferralCampaign]:
        """
        List all campaigns.

        Args:
            include_archived: Include archived campaigns

        Returns:
            List of ReferralCampaign instances
        """
        query = ReferralCampaign.query
        if not include_archived:
            query = query.filter(
                ReferralCampaign.status != ReferralCampaignStatus.ARCHIVED.value
            )
        return query.order_by(ReferralCampaign.created_at.desc()).all()

    @staticmethod
    def update_campaign(
        campaign_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_registrations: Optional[int] = None,
        config: Optional[Dict] = None
    ) -> Optional[ReferralCampaign]:
        """
        Update a campaign.

        Args:
            campaign_id: Campaign ID
            name: New name (optional)
            description: New description (optional)
            start_date: New start date (optional)
            end_date: New end date (optional)
            max_registrations: New max registrations (optional)
            config: New config (optional)

        Returns:
            Updated campaign or None if not found
        """
        campaign = ReferralCampaign.query.get(campaign_id)
        if not campaign:
            return None

        if name is not None:
            campaign.name = name
        if description is not None:
            campaign.description = description
        if start_date is not None:
            campaign.start_date = start_date
        if end_date is not None:
            campaign.end_date = end_date
        if max_registrations is not None:
            campaign.max_registrations = max_registrations
        if config is not None:
            campaign.config_json = config

        db.session.commit()
        logger.info(f"Updated referral campaign {campaign_id}")
        return campaign

    @staticmethod
    def update_campaign_status(
        campaign_id: int,
        status: ReferralCampaignStatus
    ) -> bool:
        """
        Update campaign status.

        Args:
            campaign_id: Campaign ID
            status: New status

        Returns:
            True if successful, False if campaign not found
        """
        campaign = ReferralCampaign.query.get(campaign_id)
        if not campaign:
            return False
        campaign.status = status.value
        db.session.commit()
        logger.info(f"Updated campaign {campaign_id} status to {status.value}")
        return True

    @staticmethod
    def delete_campaign(campaign_id: int) -> bool:
        """
        Delete a campaign and all its links.

        Args:
            campaign_id: Campaign ID

        Returns:
            True if successful, False if not found
        """
        campaign = ReferralCampaign.query.get(campaign_id)
        if not campaign:
            return False
        db.session.delete(campaign)
        db.session.commit()
        logger.info(f"Deleted referral campaign {campaign_id}")
        return True

    # ==================== Link Management ====================

    @staticmethod
    def create_link(
        campaign_id: int,
        created_by: str,
        role_name: Optional[str] = None,
        slug: Optional[str] = None,
        label: Optional[str] = None,
        max_uses: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        target_scenario_id: Optional[int] = None,
        collect_email: bool = True,
        collect_display_name: bool = True,
        collect_email_optional: bool = False,
        color: Optional[str] = None,
        welcome_template: str = 'standard',
        welcome_subject: Optional[str] = None,
        welcome_body: Optional[str] = None,
        provision_json: Any = None,
    ) -> ReferralLink:
        """
        Create a new referral link for a campaign.

        Args:
            campaign_id: Campaign ID
            created_by: Username of creator
            role_name: Role to assign (default: system default)
            slug: Optional custom slug for friendly URLs
            label: Optional label/description
            max_uses: Optional max uses
            expires_at: Optional expiry date
            provision_json: Optional demo-content provisioning config
                ({"clone_prompt_ids": [...], "share_job_ids": [...]}); see
                _normalize_provision_json for the trust model

        Returns:
            Created ReferralLink instance

        Raises:
            ValidationError: If campaign not found or slug already exists
        """
        from decorators.error_handler import ValidationError, ConflictError

        # Validate campaign exists
        campaign = ReferralCampaign.query.get(campaign_id)
        if not campaign:
            raise ValidationError(f"Campaign {campaign_id} not found")

        # Resolve role. SECURITY (referral self-registration is public):
        # - an EXPLICIT caller role outside the allowlist (e.g. 'admin') is a
        #   hard error — never silently downgrade what an admin explicitly asked
        #   for, surface the mistake.
        # - a misconfigured/non-allowlisted DEFAULT must never grant something
        #   unsafe, but should not crash link creation — fall back to evaluator.
        explicit_role = role_name is not None
        if not explicit_role:
            role_name = ReferralService.get_default_role()
        if explicit_role:
            _validate_referral_role(role_name)
        elif role_name not in ALLOWED_REFERRAL_ROLES:
            logger.warning(
                "default_referral_role %r is not allowlisted for referral links; using 'evaluator'",
                role_name,
            )
            role_name = 'evaluator'

        # Validate slug uniqueness if provided
        if slug:
            slug = slug.strip().lower().replace(' ', '-')
            existing = ReferralLink.query.filter_by(slug=slug).first()
            if existing:
                raise ConflictError(f"Slug '{slug}' already exists")

        link = ReferralLink(
            campaign_id=campaign_id,
            role_name=role_name,
            slug=slug,
            label=label,
            max_uses=max_uses,
            expires_at=expires_at,
            created_by=created_by,
            target_scenario_id=target_scenario_id,
            collect_email=collect_email,
            collect_display_name=collect_display_name,
            collect_email_optional=collect_email_optional,
            color=_normalize_hex_color(color),
            welcome_template=(
                welcome_template if welcome_template in ('standard', 'kkb', 'custom')
                else 'standard'
            ),
            welcome_subject=(welcome_subject or '').strip() or None,
            welcome_body=(welcome_body or '').strip() or None,
            provision_json=_normalize_provision_json(provision_json),
        )
        db.session.add(link)
        db.session.commit()
        logger.info(
            f"Created referral link {link.code} (slug={slug}) for campaign {campaign_id}"
            + (f", target_scenario={target_scenario_id}" if target_scenario_id else "")
        )
        return link

    @staticmethod
    def get_link(link_id: int) -> Optional[ReferralLink]:
        """Get a link by ID."""
        return ReferralLink.query.get(link_id)

    @staticmethod
    def get_link_by_code(code: str) -> Optional[ReferralLink]:
        """Get a link by its code."""
        return ReferralLink.query.filter_by(code=code).first()

    @staticmethod
    def get_link_by_slug(slug: str) -> Optional[ReferralLink]:
        """Get a link by its custom slug."""
        return ReferralLink.query.filter_by(slug=slug.lower()).first()

    @staticmethod
    def list_campaign_links(campaign_id: int) -> List[ReferralLink]:
        """Get all links for a campaign."""
        return ReferralLink.query.filter_by(campaign_id=campaign_id).order_by(
            ReferralLink.created_at.desc()
        ).all()

    @staticmethod
    def update_link(
        link_id: int,
        role_name: Optional[str] = None,
        label: Optional[str] = None,
        is_active: Optional[bool] = None,
        max_uses: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        target_scenario_id: Optional[int] = None,
        collect_email: Optional[bool] = None,
        collect_display_name: Optional[bool] = None,
        collect_email_optional: Optional[bool] = None,
        color: Optional[str] = None,
        welcome_template: Optional[str] = None,
        welcome_subject: Optional[str] = None,
        welcome_body: Optional[str] = None,
        provision_json: Any = None,
    ) -> Optional[ReferralLink]:
        """
        Update a referral link.

        Args:
            link_id: Link ID
            role_name: New role (optional)
            label: New label (optional)
            is_active: New active status (optional)
            max_uses: New max uses (optional)
            expires_at: New expiry date (optional)
            provision_json: New demo-content provisioning config. None leaves it
                unchanged; ``{}`` clears it (same absent-vs-empty semantics as
                ``color``)

        Returns:
            Updated link or None if not found
        """
        link = ReferralLink.query.get(link_id)
        if not link:
            return None

        if role_name is not None:
            # SECURITY: same allowlist as create_link — never let an update turn
            # a public link into an admin-granting one.
            _validate_referral_role(role_name)
            link.role_name = role_name
        if label is not None:
            link.label = label
        if is_active is not None:
            link.is_active = is_active
        if max_uses is not None:
            link.max_uses = max_uses
        if expires_at is not None:
            link.expires_at = expires_at
        if target_scenario_id is not None:
            # Allow explicit clear via 0/-1 from caller? We treat any
            # falsy non-None value the same as setting NULL on DB.
            link.target_scenario_id = target_scenario_id or None
        if collect_email is not None:
            link.collect_email = bool(collect_email)
        if collect_display_name is not None:
            link.collect_display_name = bool(collect_display_name)
        if collect_email_optional is not None:
            link.collect_email_optional = bool(collect_email_optional)
        if color is not None:
            # None = leave unchanged; '' = clear override (revert to auto-color);
            # a valid hex = set the override. _normalize_hex_color enforces this.
            link.color = _normalize_hex_color(color)
        if welcome_template is not None:
            if welcome_template not in ('standard', 'kkb', 'custom'):
                raise ValueError(
                    "welcome_template must be 'standard', 'kkb' or 'custom'"
                )
            link.welcome_template = welcome_template
        if welcome_subject is not None:
            # '' clears the custom subject (falls back to a generic one)
            link.welcome_subject = welcome_subject.strip() or None
        if welcome_body is not None:
            link.welcome_body = welcome_body.strip() or None
        if provision_json is not None:
            # None = leave unchanged; {} (or an all-empty config) = clear, i.e.
            # the link stops provisioning demo content for new registrants.
            link.provision_json = _normalize_provision_json(provision_json)

        db.session.commit()
        logger.info(f"Updated referral link {link_id}")
        return link

    @staticmethod
    def deactivate_link(link_id: int) -> bool:
        """
        Deactivate a referral link.

        Args:
            link_id: Link ID

        Returns:
            True if successful, False if not found
        """
        link = ReferralLink.query.get(link_id)
        if not link:
            return False
        link.is_active = False
        db.session.commit()
        logger.info(f"Deactivated referral link {link_id}")
        return True

    @staticmethod
    def delete_link(link_id: int) -> bool:
        """
        Delete a referral link.

        Args:
            link_id: Link ID

        Returns:
            True if successful, False if not found
        """
        link = ReferralLink.query.get(link_id)
        if not link:
            return False
        db.session.delete(link)
        db.session.commit()
        logger.info(f"Deleted referral link {link_id}")
        return True

    # ==================== Link Validation ====================

    @staticmethod
    def validate_link(code_or_slug: str) -> Tuple[bool, Optional[ReferralLink], Optional[str]]:
        """
        Validate a referral code or slug for registration.

        Args:
            code_or_slug: Referral code or custom slug

        Returns:
            Tuple of (is_valid, link, error_message)
        """
        # Check system enabled
        if not ReferralService.is_referral_enabled():
            return False, None, "Das Referral-System ist deaktiviert"

        if not ReferralService.is_self_registration_enabled():
            return False, None, "Die Selbst-Registrierung ist deaktiviert"

        # Find link by code or slug
        link = ReferralLink.query.filter(
            or_(
                ReferralLink.code == code_or_slug,
                ReferralLink.slug == code_or_slug.lower()
            )
        ).first()

        if not link:
            return False, None, "Ungültiger Einladungscode"

        if not link.is_active:
            return False, None, "Dieser Einladungslink ist nicht mehr aktiv"

        # Check campaign status
        campaign = link.campaign
        if campaign.status != ReferralCampaignStatus.ACTIVE.value:
            return False, None, "Diese Kampagne ist derzeit nicht aktiv"

        # Check campaign dates
        now = datetime.now()
        if campaign.start_date and now < campaign.start_date:
            return False, None, "Diese Kampagne hat noch nicht begonnen"
        if campaign.end_date and now > campaign.end_date:
            return False, None, "Diese Kampagne ist beendet"

        # Check link expiry
        if link.expires_at and now > link.expires_at:
            return False, None, "Dieser Einladungslink ist abgelaufen"

        # Check usage limits
        if link.max_uses:
            current_uses = ReferralRegistration.query.filter_by(link_id=link.id).count()
            if current_uses >= link.max_uses:
                return False, None, "Dieser Einladungslink hat sein Nutzungslimit erreicht"

        # Check campaign registration limit
        if campaign.max_registrations:
            total_regs = db.session.execute(
                select(func.count(ReferralRegistration.id))
                .join(ReferralLink)
                .filter(ReferralLink.campaign_id == campaign.id)
            ).scalar()
            if total_regs >= campaign.max_registrations:
                return False, None, "Diese Kampagne hat ihr Registrierungslimit erreicht"

        return True, link, None

    @staticmethod
    def increment_click_count(link_id: int) -> None:
        """Atomically bump a link's visit/click counter (best-effort).

        Called on every public ``GET /api/referral/validate/<code_or_slug>``
        hit (i.e. a /join page load) to feed the admin funnel
        "X Aufrufe -> Y registriert". Uses a single atomic
        ``UPDATE ... SET click_count = click_count + 1`` so concurrent visitors
        never lose increments to a read-modify-write race.

        Best-effort by design: any failure is logged and swallowed so a
        tracking glitch can never break link validation. Not deduplicated by
        visitor — one increment per validate call is the accepted unit, and
        bot / link-preview prefetches may inflate the count slightly.
        """
        try:
            db.session.execute(
                db.update(ReferralLink)
                .where(ReferralLink.id == link_id)
                .values(click_count=ReferralLink.click_count + 1)
            )
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            logger.warning("Failed to increment click_count for link %s: %s", link_id, exc)

    # ==================== Registration ====================

    @staticmethod
    def register_user(
        link: ReferralLink,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ReferralRegistration:
        """
        Record a user registration via referral link.

        Note: This does NOT create the user in Authentik - that happens separately.
        This only records the registration for tracking purposes.

        Args:
            link: The referral link used
            username: The registered username
            ip_address: Client IP (optional)
            user_agent: Client user agent (optional)
            metadata: Additional metadata (optional)

        Returns:
            Created ReferralRegistration instance
        """
        from sqlalchemy.exc import IntegrityError

        ua = user_agent[:512] if user_agent else None
        # Privacy: never persist the raw client IP (the model documents the value
        # as anonymized). Truncate to the network prefix — IPv4 /24, IPv6 /48 —
        # which keeps coarse origin info for abuse analysis without storing a
        # device-identifying address.
        anon_ip = _anonymize_ip(ip_address)

        def _apply(reg: ReferralRegistration) -> None:
            reg.link_id = link.id
            reg.ip_address = anon_ip
            reg.user_agent = ua
            reg.metadata_json = metadata

        # Idempotent: a username may already have a registration row — e.g. a
        # re-used or orphaned name after an account deletion (referral_registrations
        # is keyed on username with a UNIQUE constraint and has no FK to users, so
        # it survives a user delete). It is also the normal case when an already
        # registered user redeems a code via POST /api/referral/redeem. Re-attribute
        # the existing row to the new link instead of violating the constraint and
        # 500-ing the registration.
        existing = ReferralRegistration.query.filter_by(username=username).first()
        if existing is not None:
            _apply(existing)
            db.session.commit()
            logger.info(f"Re-attributed referral registration for {username} -> link {link.code}")
            return existing

        registration = ReferralRegistration(
            link_id=link.id,
            username=username,
            ip_address=ip_address,
            user_agent=ua,
            metadata_json=metadata
        )
        db.session.add(registration)
        try:
            db.session.commit()
        except IntegrityError:
            # Race: a concurrent request inserted the same username between the
            # check above and this commit. Roll back and update the existing row.
            db.session.rollback()
            existing = ReferralRegistration.query.filter_by(username=username).first()
            if existing is None:
                raise
            _apply(existing)
            db.session.commit()
            logger.info(f"Referral registration race for {username} — updated existing -> link {link.code}")
            return existing
        logger.info(f"Recorded referral registration for {username} via link {link.code}")
        return registration

    @staticmethod
    def enroll_user_in_scenario(user, link) -> Tuple[bool, bool]:
        """Enroll a user into a referral link's target scenario as an assessor.

        Shared by both the public registration flow (register_via_referral) and
        the authenticated redeem flow (POST /api/referral/redeem) so the
        enrollment shape — a ScenarioUsers row with evaluation_role='assessor',
        is_assessor=True and an ACTIVE membership — stays byte-identical between
        the two paths and is defined in exactly one place.

        Idempotent: if the user already has a ScenarioUsers row for the target
        scenario, nothing is created and their existing role is left untouched.
        This is what lets a researcher redeem a study code without being
        downgraded — we only ever ADD scenario access, never rewrite an existing
        membership.

        Args:
            user: The LLARS User object (needs .id, .username).
            link: The ReferralLink. Only acts when link.target_scenario_id is set.

        Returns:
            (enrolled, already_enrolled):
              - enrolled=True  → a new ScenarioUsers row was created
              - already_enrolled=True → the user was already a member (no-op)
              - both False → link had no target scenario, or the scenario is gone
        """
        target_scenario_id = getattr(link, 'target_scenario_id', None)
        if not target_scenario_id:
            return False, False

        # Imported lazily to keep the service import-light and avoid a circular
        # import with the scenario models at module load time.
        from db.models.scenario import (
            ScenarioUsers, RatingScenarios, MembershipStatus, ScenarioRoles,
        )

        scenario = RatingScenarios.query.get(target_scenario_id)
        if scenario is None:
            return False, False

        already = ScenarioUsers.query.filter_by(
            scenario_id=target_scenario_id,
            user_id=user.id,
        ).first()
        if already is not None:
            return False, True

        su = ScenarioUsers(
            scenario_id=target_scenario_id,
            user_id=user.id,
            manager_role='none',
            evaluation_role='assessor',
            is_viewer=False,
            is_assessor=True,
            membership_status=MembershipStatus.ACTIVE,
            role=ScenarioRoles.ASSESSOR,
        )
        db.session.add(su)
        db.session.commit()
        logger.info(
            f"Enrolled {user.username} into scenario {target_scenario_id} via link {link.code}"
        )
        return True, False

    @staticmethod
    def enroll_user_in_link_scenarios(user, link) -> dict:
        """Enroll a user into ALL scenarios a link points at, in one pass.

        Generalises enroll_user_in_scenario for the IJCAI demo link, which sends
        a registrant into one demo scenario per evaluation type as an ASSESSOR
        and additionally grants read-only manager VIEWER access so they can watch
        the live aggregated analysis. A scenario can appear in both lists (the
        demo case): the row then carries evaluation_role='assessor' AND
        manager_role='viewer'.

        Mirrors enroll_user_in_scenario's contract EXACTLY: we only ever ADD a
        brand-new ScenarioUsers row, and NEVER rewrite an existing membership —
        not even to upgrade it. This preserves the "redeeming a code never
        changes a role you already have" guarantee (see REDEEM_008). For the
        IJCAI demo this is sufficient: a fresh participant has no prior
        memberships, so all 7 rows are created with the combined assessor +
        viewer roles; a returning participant already has those rows, so the
        idempotent skip is correct.

        A scenario present in both lists gets a single row carrying
        evaluation_role='assessor' AND manager_role='viewer'.

        Returns a summary dict: {'assessor': [ids...], 'viewer': [ids...],
        'created': n, 'already': n}.
        """
        from db.models.scenario import (
            ScenarioUsers, RatingScenarios, MembershipStatus, ScenarioRoles,
        )

        assessor_ids = link.get_assessor_scenario_ids()
        viewer_ids = link.get_viewer_scenario_ids()
        all_ids = list(dict.fromkeys(assessor_ids + viewer_ids))  # ordered union
        if not all_ids:
            return {'assessor': [], 'viewer': [], 'created': 0, 'already': 0}

        created = already = 0
        done_assessor, done_viewer = [], []

        for sid in all_ids:
            if RatingScenarios.query.get(sid) is None:
                continue
            want_eval = 'assessor' if sid in assessor_ids else 'none'
            want_mgr = 'viewer' if sid in viewer_ids else 'none'

            row = ScenarioUsers.query.filter_by(scenario_id=sid, user_id=user.id).first()
            if row is not None:
                # Already a member — never rewrite an existing membership.
                already += 1
                continue

            db.session.add(ScenarioUsers(
                scenario_id=sid,
                user_id=user.id,
                manager_role=want_mgr,
                evaluation_role=want_eval,
                is_viewer=(want_mgr == 'viewer' and want_eval != 'assessor'),
                is_assessor=(want_eval == 'assessor'),
                membership_status=MembershipStatus.ACTIVE,
                role=ScenarioRoles.ASSESSOR,
            ))
            created += 1
            if want_eval == 'assessor':
                done_assessor.append(sid)
            if want_mgr == 'viewer':
                done_viewer.append(sid)

        if created:
            db.session.commit()
            logger.info(
                f"Enrolled {user.username} via link {link.code}: "
                f"assessor={done_assessor} viewer={done_viewer} "
                f"(created={created}, already={already})"
            )

        return {
            'assessor': done_assessor,
            'viewer': done_viewer,
            'created': created,
            'already': already,
        }

    @staticmethod
    def provision_demo_content(user, link) -> dict:
        """Give a user the demo content a link is configured to hand out.

        Second post-registration hook next to enroll_user_in_link_scenarios:
        where that one hands out SCENARIO memberships, this one hands out
        WORKING MATERIAL, so an IJCAI conference visitor who scans the QR code
        lands in an account that already has something to look at and edit:

        - ``clone_prompt_ids`` — each source UserPrompt is COPIED into the
          registrant's account (own row, own prompt_id), because a demo visitor
          must be able to edit and re-run "their" prompt without mutating the
          shared demo original. Two tiny rows per user is cheap.
        - ``share_job_ids`` — each GenerationJob is SHARED (GenerationJobShare),
          not copied: a completed matrix job carries dozens of output rows, and
          duplicating those per visitor would blow up the table for no gain.
          Read-only sharing is exactly the intended "look at real results".

        Idempotent, so it is safe on every register AND on every redeem of the
        same link (the redeem path is how an existing account gets the demo
        material, and how an already-provisioned visitor re-entering via the QR
        code is handled):
        - clone: skipped when the user already has a prompt of the same name —
          name is the identity we can match on, and it deliberately does NOT
          overwrite a copy the visitor has since edited.
        - share: skipped when a share row exists, and when the user IS the job's
          creator (sharing a job with its owner is meaningless).

        NEVER RAISES. Registration happens while a visitor stands at a
        conference booth; a missing prompt id, a renamed table or a DB hiccup
        must cost them a demo prompt, never their account. Every failure path
        logs and returns — same defensive contract as (and stricter than)
        enroll_user_in_link_scenarios, which the callers wrap in try/except.

        Attribution note: cloned content keeps whatever the source prompt
        carries (``collaboration_attribution``, per-block ``author`` fields) —
        those credit the original demo author and are correct to preserve on a
        copy.

        Returns a summary dict for logging:
        ``{'prompts_cloned': n, 'prompts_skipped': n, 'jobs_shared': n,
        'jobs_skipped': n, 'errors': n}``.
        """
        summary = {
            'prompts_cloned': 0,
            'prompts_skipped': 0,
            'jobs_shared': 0,
            'jobs_skipped': 0,
            'errors': 0,
        }

        try:
            raw = (getattr(link, 'provision_json', None) or '').strip()
            if not raw:
                return summary  # link provisions nothing — the normal case

            # Tolerate garbage in the column (hand-edited DB row, half-written
            # migration): warn loudly, provision nothing, never abort signup.
            try:
                config = json.loads(raw)
            except (ValueError, TypeError) as exc:
                logger.warning(
                    "Link %s has invalid provision_json (%s) — skipping provisioning",
                    getattr(link, 'code', '?'), exc,
                )
                return summary
            if not isinstance(config, dict):
                logger.warning(
                    "Link %s provision_json is %s, expected an object — skipping provisioning",
                    getattr(link, 'code', '?'), type(config).__name__,
                )
                return summary

            # Imported lazily (like enroll_user_in_link_scenarios) to keep this
            # service import-light and clear of circular model imports.
            from db.models.scenario import UserPrompt
            from db.models.generation import GenerationJob, GenerationJobShare

            created = 0

            for prompt_id in (config.get('clone_prompt_ids') or []):
                source = UserPrompt.query.get(prompt_id)
                if source is None:
                    summary['prompts_skipped'] += 1
                    logger.warning(
                        "Link %s references unknown prompt %s — skipped",
                        getattr(link, 'code', '?'), prompt_id,
                    )
                    continue
                exists = UserPrompt.query.filter_by(
                    user_id=user.id, name=source.name
                ).first()
                if exists is not None:
                    summary['prompts_skipped'] += 1
                    continue
                db.session.add(UserPrompt(
                    user_id=user.id,
                    name=source.name,
                    # Deep copy: the JSON column hands out a live structure, so
                    # a shallow copy would let a visitor's edits leak into the
                    # source prompt (and into every later clone).
                    content=copy.deepcopy(source.content),
                    # rendered_content carries the {{var}} plain-text blocks the
                    # generation pipeline substitutes against — a clone without
                    # it would look right but generate wrong.
                    rendered_content=copy.deepcopy(source.rendered_content),
                ))
                summary['prompts_cloned'] += 1
                created += 1

            for job_id in (config.get('share_job_ids') or []):
                job = GenerationJob.query.get(job_id)
                if job is None:
                    summary['jobs_skipped'] += 1
                    logger.warning(
                        "Link %s references unknown generation job %s — skipped",
                        getattr(link, 'code', '?'), job_id,
                    )
                    continue
                if (job.created_by or '') == user.username:
                    summary['jobs_skipped'] += 1  # owner already sees the job
                    continue
                exists = GenerationJobShare.query.filter_by(
                    job_id=job.id, shared_with_user_id=user.id
                ).first()
                if exists is not None:
                    summary['jobs_skipped'] += 1
                    continue
                db.session.add(GenerationJobShare(
                    job_id=job.id,
                    shared_with_user_id=user.id,
                ))
                summary['jobs_shared'] += 1
                created += 1

            if created:
                db.session.commit()
                logger.info(
                    "Provisioned %s via link %s: %s prompt(s) cloned, %s job(s) shared "
                    "(skipped: %s prompt(s), %s job(s))",
                    user.username, getattr(link, 'code', '?'),
                    summary['prompts_cloned'], summary['jobs_shared'],
                    summary['prompts_skipped'], summary['jobs_skipped'],
                )
        except Exception as exc:
            # Blanket catch by design — see the NEVER RAISES note above.
            summary['errors'] += 1
            try:
                db.session.rollback()
            except Exception:
                pass
            logger.error(
                "Demo provisioning failed for %s via link %s: %s",
                getattr(user, 'username', '?'), getattr(link, 'code', '?'), exc,
                exc_info=True,
            )

        return summary

    @staticmethod
    def get_registration_by_username(username: str) -> Optional[ReferralRegistration]:
        """Get registration record by username."""
        return ReferralRegistration.query.filter_by(username=username).first()

    # ==================== Analytics ====================

    @staticmethod
    def get_campaign_stats(campaign_id: int) -> Dict[str, Any]:
        """
        Get statistics for a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Dict with campaign statistics
        """
        campaign = ReferralCampaign.query.get(campaign_id)
        if not campaign:
            return {}

        # Count total links
        total_links = ReferralLink.query.filter_by(campaign_id=campaign_id).count()
        active_links = ReferralLink.query.filter_by(
            campaign_id=campaign_id, is_active=True
        ).count()

        # Count registrations
        total_registrations = db.session.execute(
            select(func.count(ReferralRegistration.id))
            .join(ReferralLink)
            .filter(ReferralLink.campaign_id == campaign_id)
        ).scalar()

        # Registrations per day (last 30 days)
        daily_stats = db.session.execute(
            select(
                func.date(ReferralRegistration.registered_at).label('date'),
                func.count(ReferralRegistration.id).label('count')
            )
            .join(ReferralLink)
            .filter(ReferralLink.campaign_id == campaign_id)
            .group_by(func.date(ReferralRegistration.registered_at))
            .order_by(func.date(ReferralRegistration.registered_at).desc())
            .limit(30)
        ).all()

        # Total page opens (clicks) across all links in the campaign.
        total_clicks = db.session.execute(
            select(func.coalesce(func.sum(ReferralLink.click_count), 0))
            .filter(ReferralLink.campaign_id == campaign_id)
        ).scalar() or 0

        # Top performing links
        top_links = db.session.execute(
            select(
                ReferralLink.id,
                ReferralLink.code,
                ReferralLink.slug,
                ReferralLink.label,
                ReferralLink.click_count.label('clicks'),
                func.count(ReferralRegistration.id).label('registrations')
            )
            .outerjoin(ReferralRegistration)
            .filter(ReferralLink.campaign_id == campaign_id)
            .group_by(ReferralLink.id)
            .order_by(func.count(ReferralRegistration.id).desc())
            .limit(10)
        ).all()

        return {
            'campaign_id': campaign_id,
            'campaign_name': campaign.name,
            'status': campaign.status,
            'total_links': total_links,
            'active_links': active_links,
            'total_registrations': total_registrations,
            # Funnel: total page opens vs registrations across the campaign.
            'total_clicks': int(total_clicks),
            'conversion_rate': (total_registrations / int(total_clicks)) if total_clicks else None,
            'max_registrations': campaign.max_registrations,
            'daily_registrations': [
                {'date': str(row.date), 'count': row.count}
                for row in daily_stats
            ],
            'top_links': [
                {
                    'id': row.id,
                    'code': row.code,
                    'slug': row.slug,
                    'label': row.label,
                    'clicks': row.clicks or 0,
                    'registrations': row.registrations,
                    'conversion_rate': (
                        (row.registrations / row.clicks) if row.clicks else None
                    ),
                }
                for row in top_links
            ]
        }

    @staticmethod
    def get_link_stats(link_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific link.

        Args:
            link_id: Link ID

        Returns:
            Dict with link statistics
        """
        link = ReferralLink.query.get(link_id)
        if not link:
            return {}

        registrations = ReferralRegistration.query.filter_by(link_id=link_id).count()

        # Recent registrations
        recent = ReferralRegistration.query.filter_by(link_id=link_id).order_by(
            ReferralRegistration.registered_at.desc()
        ).limit(10).all()

        clicks = link.click_count or 0
        return {
            'link_id': link_id,
            'code': link.code,
            'slug': link.slug,
            'label': link.label,
            'role_name': link.role_name,
            'is_active': link.is_active,
            'registrations': registrations,
            # Funnel: page opens (clicks) vs registrations.
            'click_count': clicks,
            'conversion_rate': (registrations / clicks) if clicks > 0 else None,
            'max_uses': link.max_uses,
            'remaining_uses': link.max_uses - registrations if link.max_uses else None,
            'recent_registrations': [reg.to_dict() for reg in recent]
        }

    @staticmethod
    def list_registrations(
        campaign_id: Optional[int] = None,
        link_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """
        List registrations with optional filtering.

        Args:
            campaign_id: Filter by campaign (optional)
            link_id: Filter by link (optional)
            limit: Max results
            offset: Offset for pagination

        Returns:
            Tuple of (list of registration dicts, total count)
        """
        query = ReferralRegistration.query

        if link_id:
            query = query.filter_by(link_id=link_id)
        elif campaign_id:
            # Get all links for campaign
            link_ids = [l.id for l in ReferralLink.query.filter_by(campaign_id=campaign_id).all()]
            query = query.filter(ReferralRegistration.link_id.in_(link_ids))

        total = query.count()
        registrations = query.order_by(
            ReferralRegistration.registered_at.desc()
        ).offset(offset).limit(limit).all()

        usernames = sorted({reg.username for reg in registrations if reg.username})
        user_lookup = {}
        if usernames:
            user_lookup = {u.username: u for u in User.query.filter(User.username.in_(usernames)).all()}

        # Build response with link/campaign info
        result = []
        for reg in registrations:
            link = reg.link
            campaign = link.campaign if link else None
            avatar = serialize_user_brief(user_lookup.get(reg.username))
            result.append({
                'id': reg.id,
                'username': reg.username,
                'avatar_seed': avatar.get('avatar_seed'),
                'avatar_url': avatar.get('avatar_url'),
                'registered_at': reg.registered_at.isoformat() if reg.registered_at else None,
                'ip_address': reg.ip_address,
                'user_agent': reg.user_agent,
                'link_id': reg.link_id,
                'link_code': link.code if link else None,
                'link_slug': link.slug if link else None,
                'link_label': link.label if link else None,
                'role_assigned': link.role_name if link else None,
                'campaign_id': campaign.id if campaign else None,
                'campaign_name': campaign.name if campaign else None
            })

        return result, total

    @staticmethod
    def get_system_overview() -> Dict[str, Any]:
        """
        Get overall referral system statistics.

        Returns:
            Dict with system-wide statistics
        """
        total_campaigns = ReferralCampaign.query.count()
        active_campaigns = ReferralCampaign.query.filter_by(
            status=ReferralCampaignStatus.ACTIVE.value
        ).count()
        total_links = ReferralLink.query.count()
        active_links = ReferralLink.query.filter_by(is_active=True).count()
        total_registrations = ReferralRegistration.query.count()

        # System-wide page opens (clicks) across all links, for the
        # top-level funnel "X Aufrufe -> Y registriert".
        total_clicks = db.session.execute(
            select(func.coalesce(func.sum(ReferralLink.click_count), 0))
        ).scalar() or 0

        # Registrations in last 7 days
        from datetime import timedelta
        week_ago = datetime.now() - timedelta(days=7)
        recent_registrations = ReferralRegistration.query.filter(
            ReferralRegistration.registered_at >= week_ago
        ).count()

        # Top campaigns by registrations
        top_campaigns = db.session.execute(
            select(
                ReferralCampaign.id,
                ReferralCampaign.name,
                func.count(ReferralRegistration.id).label('registrations')
            )
            .outerjoin(ReferralLink, ReferralLink.campaign_id == ReferralCampaign.id)
            .outerjoin(ReferralRegistration, ReferralRegistration.link_id == ReferralLink.id)
            .group_by(ReferralCampaign.id)
            .order_by(func.count(ReferralRegistration.id).desc())
            .limit(5)
        ).all()

        return {
            'referral_enabled': ReferralService.is_referral_enabled(),
            'self_registration_enabled': ReferralService.is_self_registration_enabled(),
            'default_role': ReferralService.get_default_role(),
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'total_links': total_links,
            'active_links': active_links,
            'total_registrations': total_registrations,
            # Funnel: total page opens (clicks) vs registrations system-wide.
            'total_clicks': int(total_clicks),
            'conversion_rate': (
                (total_registrations / int(total_clicks)) if total_clicks else None
            ),
            'registrations_last_7_days': recent_registrations,
            'top_campaigns': [
                {
                    'id': row.id,
                    'name': row.name,
                    'registrations': row.registrations
                }
                for row in top_campaigns
            ]
        }
