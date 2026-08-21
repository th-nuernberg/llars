"""
Referral and Invitation System database models.

Provides models for:
- ReferralCampaign: Groups of invite links (e.g., "KI-Konferenz 2026")
- ReferralLink: Individual invite codes with custom slugs
- ReferralRegistration: Tracks user registrations via referral
"""

import json
import secrets
from enum import Enum
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from db import db


class ReferralCampaignStatus(Enum):
    """Campaign lifecycle status."""
    DRAFT = 'draft'           # Not yet active
    ACTIVE = 'active'         # Accepting registrations
    PAUSED = 'paused'         # Temporarily disabled
    EXPIRED = 'expired'       # Past end_date
    ARCHIVED = 'archived'     # Permanently disabled


def generate_referral_code() -> str:
    """Generate a unique 12-character referral code."""
    return secrets.token_urlsafe(9)  # 12 chars base64


class ReferralCampaign(db.Model):
    """
    A referral campaign groups multiple invite links under a theme.

    Examples: 'KI-Konferenz 2026', 'Hochschule Nuernberg Pilotprojekt'
    """
    __tablename__ = 'referral_campaigns'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    status: Mapped[str] = mapped_column(
        db.String(20),
        default=ReferralCampaignStatus.DRAFT.value,
        nullable=False,
        index=True
    )

    # Optional time boundaries
    start_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Optional registration limits
    max_registrations: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # Tracking
    created_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # Flexible metadata (e.g., custom fields, branding info)
    config_json: Mapped[Optional[dict]] = mapped_column(
        db.JSON, nullable=True,
        comment="Custom campaign settings"
    )

    # Relationships
    links = db.relationship(
        'ReferralLink',
        back_populates='campaign',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def to_dict(self, include_links: bool = False) -> dict:
        """Convert to dictionary for API responses."""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'max_registrations': self.max_registrations,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'config': self.config_json,
            'link_count': self.links.count() if self.links else 0
        }
        if include_links:
            result['links'] = [link.to_dict() for link in self.links.all()]
        return result


# Deterministic badge-color palette for referral links. Mirrors the frontend
# COLLAB_COLOR_PRESETS (llars-frontend/src/constants/colors.js) so an
# auto-assigned link color is identical whether resolved in Python or JS.
# Purple/violet is intentionally excluded (reserved for the AI assistant).
REFERRAL_LINK_COLOR_PALETTE = (
    '#b0ca97', '#98d4bb', '#88c4c8', '#D1BC8A', '#a8c5e2', '#f0b6c2',
    '#e8c87a', '#FF6B6B', '#4ECDC4', '#45B7D1', '#E67E22', '#27AE60',
)


class ReferralLink(db.Model):
    """
    Individual invite link within a campaign.

    Each link can have:
    - A unique code (auto-generated)
    - A custom slug for friendly URLs (e.g., 'ki-konferenz-2026')
    - Specific roles to assign upon registration
    - Usage limits and expiry dates
    """
    __tablename__ = 'referral_links'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('referral_campaigns.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Unique identifier for the link (auto-generated)
    code: Mapped[str] = mapped_column(
        db.String(64),
        unique=True,
        nullable=False,
        index=True,
        default=generate_referral_code
    )

    # Custom slug for friendly URLs (e.g., 'ki-konferenz-2026')
    slug: Mapped[Optional[str]] = mapped_column(
        db.String(100),
        unique=True,
        nullable=True,
        index=True
    )

    # Role to assign upon registration
    role_name: Mapped[str] = mapped_column(db.String(100), default='evaluator', nullable=False)

    # Optional label/description for this specific link
    label: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Welcome-mail routing for sign-ups/enrollments via this link:
    #   'standard' — generic LLARS welcome, auto-filled with name/study (default)
    #   'kkb'      — legacy "Kann KI Beratung?" study mail (that study only)
    #   'custom'   — welcome_subject/welcome_body below, with {placeholders}
    # The ijcai/demo-* slugs keep their dedicated mails (routed by slug).
    # Historically the KKB mail was the GLOBAL fallback, so joining any other
    # study produced a wrong-study welcome — hence this per-link routing.
    welcome_template: Mapped[str] = mapped_column(
        db.String(20), default='standard', nullable=False
    )
    # Custom template ({name}, {username}, {study}, {study_link}, {link_label});
    # only used when welcome_template == 'custom'. Body is plain text and gets
    # wrapped into the branded HTML shell at send time.
    welcome_subject: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    welcome_body: Mapped[Optional[str]] = mapped_column(db.TEXT, nullable=True)

    # Active/inactive status
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    # Visit/click counter: how often this link's /join landing page has been
    # opened. Incremented (best-effort, atomically) on every public
    # GET /api/referral/validate/<code_or_slug> hit so admins can compute a
    # funnel "X Aufrufe -> Y registriert" per org/link. NOT deduplicated by
    # visitor — a single validate call per page load is the accepted unit, and
    # bot/link-preview prefetches may inflate it (see route docstring caveat).
    click_count: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)

    # Optional usage limits per link
    max_uses: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # Expiry date (overrides campaign end_date if set)
    expires_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Tracking
    created_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    # User-created links support (NULL = admin-created)
    owner_user_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="User who owns this link (NULL = admin-created)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Additional description for the link"
    )

    # Auto-enroll target: when a user registers via this link, they're
    # also added to this scenario as an ACTIVE ASSESSOR. Used by purpose-
    # built study links (e.g. EMNLP Turing-Test) to send participants
    # straight into the right comparison flow without manual onboarding.
    target_scenario_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('rating_scenarios.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Auto-enroll registrants into this scenario as ASSESSOR"
    )

    # Multi-scenario auto-enroll (generalises target_scenario_id). When a user
    # registers via this link they're added as ACTIVE ASSESSOR to every scenario
    # in this list, AND given read-only manager VIEWER access on every scenario
    # in viewer_scenario_ids. Built for the IJCAI demo link: one QR -> evaluator
    # in one demo scenario per evaluation type, plus viewer on their analyses.
    # JSON list of ints; NULL = none. target_scenario_id stays for old links.
    target_scenario_ids: Mapped[Optional[list]] = mapped_column(
        db.JSON,
        nullable=True,
        comment="Auto-enroll registrants as ASSESSOR into all these scenarios (JSON list of ids)"
    )
    viewer_scenario_ids: Mapped[Optional[list]] = mapped_column(
        db.JSON,
        nullable=True,
        comment="Grant registrants read-only manager VIEWER access on these scenarios (JSON list of ids)"
    )

    # Demo-content provisioning: what a registrant of this link RECEIVES on top
    # of the scenario memberships above, as JSON text. Contract:
    #   {"clone_prompt_ids": [<UserPrompt.prompt_id>, ...],
    #    "share_job_ids":    [<GenerationJob.id>, ...]}
    # Prompts are CLONED (each user gets an own editable copy), generation jobs
    # are SHARED read-only (a GenerationJobShare row — no duplication of the
    # dozens of output rows). Both keys optional; NULL/absent = provision
    # nothing. Applied by ReferralService.provision_demo_content on register AND
    # redeem, idempotently. Built for the IJCAI conference QR link so a visitor
    # lands in an account with prompts to edit and finished generations to look
    # at. SECURITY: admin-trusted config (setting it requires
    # admin:referral:manage) — cloning copies the source prompt's content into
    # every registrant's account.
    # Text here, LONGTEXT in the DB (see
    # db/migrations/migrate_referral_link_provisioning.py) — plain JSON text
    # rather than db.JSON so the column stays trivially inspectable/editable in
    # SQL and the service keeps full control over parse-error handling.
    provision_json: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment='Demo content for registrants: {"clone_prompt_ids": [...], "share_job_ids": [...]}'
    )

    # Registration flow variant, controls how much the /join form asks for:
    #   'full'    - username + password + (email per collect_* flags)  [legacy default]
    #   'email'   - email only; username auto-generated; passwordless; re-entry via
    #               same email (or 'forgot password' to set one)
    #   'instant' - one tap, nothing asked; username + account fully auto-generated
    signup_mode: Mapped[str] = mapped_column(
        db.String(20),
        default='full',
        nullable=False,
        comment="Registration flow: full | email | instant"
    )

    # Default UI language for users who join via this link: applied on the /join
    # page (pre-login) AND persisted to the user's profile so re-login stays in
    # that language. Default 'de'; the IJCAI demo link sets 'en'.
    default_locale: Mapped[str] = mapped_column(
        db.String(5),
        default='de',
        nullable=False,
        comment="UI language for this link's registrants: 'de' | 'en'"
    )

    # Registration-form toggles. Defaults TRUE so existing links keep
    # collecting email + display name exactly as before. Set FALSE on
    # closed-network study links where counsellors should only have to
    # type username + password.
    collect_email: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True,
        nullable=False,
        comment="Whether the registration form shows + requires an email field"
    )
    collect_display_name: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True,
        nullable=False,
        comment="Whether the registration form shows the optional display-name field"
    )
    # Refines collect_email: when collect_email is TRUE the email field is
    # shown, and this flag decides whether it is required (FALSE, legacy) or
    # merely offered (TRUE — visible but skippable; the server synthesizes a
    # placeholder address when left blank). Default FALSE keeps existing
    # links' email field required.
    collect_email_optional: Mapped[bool] = mapped_column(
        db.Boolean,
        default=False,
        nullable=False,
        comment="When collect_email is TRUE, show the email field but do not require it"
    )

    # Badge/pill color for this link, shown wherever the link's origin surfaces
    # (scenario team pills, origin legends, admin list) so a color becomes
    # synonymous with a referral source LLARS-wide. NULL = use the deterministic
    # auto-color (see resolved_color); admins can override per link.
    color: Mapped[Optional[str]] = mapped_column(
        db.String(7),
        nullable=True,
        comment="Hex badge color (#rrggbb). NULL = deterministic auto-color by id."
    )

    # Relationships
    campaign = db.relationship('ReferralCampaign', back_populates='links')
    owner = db.relationship('User', backref='referral_links', lazy='selectin')
    registrations = db.relationship(
        'ReferralRegistration',
        back_populates='link',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        db.Index('ix_referral_links_code_active', 'code', 'is_active'),
    )

    def get_assessor_scenario_ids(self) -> list:
        """All scenario ids to enroll the registrant into as ASSESSOR.

        Merges the legacy single target_scenario_id with the new
        target_scenario_ids list, de-duplicated and order-preserving.
        """
        ids = []
        if self.target_scenario_id:
            ids.append(self.target_scenario_id)
        for sid in (self.target_scenario_ids or []):
            if sid and sid not in ids:
                ids.append(sid)
        return ids

    def get_viewer_scenario_ids(self) -> list:
        """Scenario ids on which the registrant gets read-only manager VIEWER access."""
        return [sid for sid in (self.viewer_scenario_ids or []) if sid]

    def get_provision_config(self) -> dict:
        """Parsed provision_json for DISPLAY (admin API), never for provisioning.

        Tolerant on purpose: a malformed column must not break the admin link
        list. The provisioning path deliberately parses the raw column itself so
        it can log the bad config — see
        ReferralService.provision_demo_content.
        """
        raw = (self.provision_json or '').strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    @property
    def resolved_color(self) -> str:
        """Badge color for this link: the admin-set ``color`` if present, else a
        stable auto-color picked from REFERRAL_LINK_COLOR_PALETTE by id. Keeping
        the resolution here (not in the caller) makes a link's color identical
        everywhere it is rendered without requiring a one-time backfill."""
        if self.color:
            return self.color
        palette = REFERRAL_LINK_COLOR_PALETTE
        return palette[(self.id or 0) % len(palette)]

    def to_dict(self, include_stats: bool = False) -> dict:
        """Convert to dictionary for API responses."""
        result = {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'code': self.code,
            'slug': self.slug,
            'role_name': self.role_name,
            'label': self.label,
            'welcome_template': self.welcome_template or 'standard',
            'welcome_subject': self.welcome_subject,
            'welcome_body': self.welcome_body,
            'description': self.description,
            'is_active': self.is_active,
            'max_uses': self.max_uses,
            # Page-load/visit counter for the funnel view (clicks -> registrations).
            'click_count': self.click_count or 0,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'owner_user_id': self.owner_user_id,
            'owner_username': self.owner.username if self.owner else None,
            'target_scenario_id': self.target_scenario_id,
            'target_scenario_ids': self.target_scenario_ids or [],
            'viewer_scenario_ids': self.viewer_scenario_ids or [],
            'signup_mode': self.signup_mode or 'full',
            'default_locale': self.default_locale or 'de',
            # Parsed provisioning config ({} when unset) — same shape the admin
            # create/update endpoints accept back, so the admin UI can round-trip
            # it. Only admin-facing endpoints render links with this field set;
            # user-created links never carry one.
            'provision_json': self.get_provision_config(),
            'collect_email': self.collect_email,
            'collect_display_name': self.collect_display_name,
            'collect_email_optional': self.collect_email_optional,
            # Resolved badge color (admin override or deterministic auto-color)
            # plus the raw override so the admin UI can show "auto" vs custom.
            'color': self.resolved_color,
            'color_custom': self.color,
            'url': f"/join/{self.slug or self.code}"
        }
        if include_stats:
            registration_count = self.registrations.count() if self.registrations else 0
            result['registrations'] = registration_count
            result['remaining_uses'] = self.max_uses - registration_count if self.max_uses else None
            # Funnel: clicks (page opens) -> registrations. conversion_rate is a
            # fraction in [0,1] (None when there were no clicks, to avoid a
            # misleading 0% on a link nobody has opened yet).
            clicks = self.click_count or 0
            result['conversion_rate'] = (
                (registration_count / clicks) if clicks > 0 else None
            )
        return result


class ReferralRegistration(db.Model):
    """
    Tracks each user registration via referral link.

    Records:
    - Which link was used
    - The registered username
    - Registration metadata (IP, user agent)
    """
    __tablename__ = 'referral_registrations'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    link_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('referral_links.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # The registered user
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)

    # Registration timestamp
    registered_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    # Client info for analytics (hashed/anonymized in production)
    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)  # IPv6 max length
    user_agent: Mapped[Optional[str]] = mapped_column(db.String(512), nullable=True)

    # Additional metadata (e.g., UTM params, email)
    metadata_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    # Relationship
    link = db.relationship('ReferralLink', back_populates='registrations')

    __table_args__ = (
        db.UniqueConstraint('username', name='uq_referral_registration_username'),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'link_id': self.link_id,
            'username': self.username,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'metadata': self.metadata_json
        }
