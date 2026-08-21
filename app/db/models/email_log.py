"""
Mail-Center database models — the audit foundation for *every* outbound mail.

Two tables back the Admin Mail-Center (see
``.claude/plans/admin-mail-center-concept.md``):

``email_log``
    One row per send attempt — automatic (welcome / password-reset) **and**
    manual (invitation / announcement). This is the single place where
    "everything comes together": who got a welcome mail, to whom a reset
    link went, who we invited, which announcements went out.

``referral_invitation``
    One row per invitation mail tied to a referral link. On registration via
    that link the row is matched by email and flipped to *accepted*, giving an
    honest invited → accepted → pending funnel per link.

Privacy / GDPR (deliberate design)
----------------------------------
- **Never store full mail bodies.** ``password_reset`` bodies carry a
  single-use token; persisting them would defeat the token's purpose. We keep
  only subject / type / recipient / status for every type. For
  ``invitation`` / ``announcement`` an optional short (<=280 char) text
  preview may live in ``meta_json`` so the admin can recognise a campaign in
  the log — never the rendered HTML, never reset tokens.
- Admin-only access (``feature:admin:mail``). Retention (auto-purge) is left
  as a future system-setting; documented in the concept, out of scope here.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from db import db


class MailType(str, Enum):
    """The four mail kinds that flow through the central logger."""
    WELCOME = 'welcome'
    PASSWORD_RESET = 'password_reset'
    INVITATION = 'invitation'
    ANNOUNCEMENT = 'announcement'


class MailStatus(str, Enum):
    """Outcome of a single send attempt.

    ``skipped`` is distinct from ``failed``: it means we deliberately did not
    send (no real inbox — empty or ``@noemail.invalid``), not that the SMTP
    handshake errored. Keeping the two apart stops synthetic referral signups
    from polluting the failure rate.
    """
    SENT = 'sent'
    FAILED = 'failed'
    SKIPPED = 'skipped'


# Max length of the optional human-readable body preview kept in meta_json for
# invitation / announcement rows. Long enough to recognise a campaign, short
# enough to stay clearly a *preview* and not a full-body store.
PREVIEW_MAX_CHARS = 280


class EmailLog(db.Model):
    """Append-only audit row for one outbound mail.

    Written by ``email_service.record_and_send`` (the thin wrapper around
    ``_send_sync``) so the call site only has to pass ``mail_type`` + context.
    """
    __tablename__ = 'email_log'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.now, nullable=False, index=True
    )

    # Stored as the enum *value* (str) so the column stays readable in raw SQL
    # and survives enum-member renames without a data migration.
    mail_type: Mapped[str] = mapped_column(db.String(32), nullable=False, index=True)
    recipient_email: Mapped[str] = mapped_column(db.String(320), nullable=False, index=True)
    recipient_user_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True
    )
    subject: Mapped[str] = mapped_column(db.String(512), nullable=False)
    status: Mapped[str] = mapped_column(db.String(16), nullable=False, index=True)
    error: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Who triggered a *manual* send; NULL for system mails (welcome / reset).
    triggered_by_user_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True
    )
    # Context joins — both nullable, set when known.
    referral_link_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('referral_links.id', ondelete='SET NULL'), nullable=True, index=True
    )
    scenario_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)

    # Extension bag. Holds the <=280-char body preview for invitation /
    # announcement, the announcement subject, etc. NEVER a reset token / body.
    meta_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    # --- Engagement tracking (Brevo transactional-event webhook) ------------
    # The provider (Brevo SMTP) returns a ``Message-ID`` header per send. We
    # store it so the ``POST /api/webhooks/brevo`` handler can match an
    # ``opened`` / ``click`` event back to the exact send row. When the
    # provider does not surface a usable id we fall back to matching by
    # (recipient_email + subject, most-recent). See app/routes/webhooks_routes.py.
    provider_message_id: Mapped[Optional[str]] = mapped_column(
        db.String(255), nullable=True, index=True
    )
    # First-occurrence-wins timestamps set by the webhook. NULL = not (yet)
    # opened / clicked. Open tracking only works when Brevo open-tracking is
    # enabled AND the recipient's client loads the tracking pixel/images.
    opened_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    clicked_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'mail_type': self.mail_type,
            'recipient_email': self.recipient_email,
            'recipient_user_id': self.recipient_user_id,
            'subject': self.subject,
            'status': self.status,
            'error': self.error,
            'triggered_by_user_id': self.triggered_by_user_id,
            'referral_link_id': self.referral_link_id,
            'scenario_id': self.scenario_id,
            'meta': self.meta_json,
            'provider_message_id': self.provider_message_id,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
        }


class ReferralInvitation(db.Model):
    """One invitation mail sent for a referral link; flips to *accepted* on signup.

    The honest caveat (documented in the concept and the UI): a registration
    can only be matched back to an invitation when the registrant supplied the
    *same* email. Email is optional on closed-network study links, so some
    "registered via this link" users will never match an invitation. We surface
    that gap rather than hide it (invited / accepted / pending + an unmatched
    note in the per-link stats).
    """
    __tablename__ = 'referral_invitation'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    referral_link_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey('referral_links.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    # Stored lower-cased so the registration-time match is case-insensitive.
    email: Mapped[str] = mapped_column(db.String(320), nullable=False, index=True)
    invited_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.now, nullable=False
    )
    email_log_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('email_log.id', ondelete='SET NULL'), nullable=True
    )
    accepted_user_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    __table_args__ = (
        # One open invitation per (link, email) — re-inviting the same address
        # updates the existing row instead of stacking duplicates.
        db.UniqueConstraint('referral_link_id', 'email', name='uq_referral_invitation_link_email'),
    )

    @property
    def status(self) -> str:
        """Derived funnel state."""
        return 'accepted' if self.accepted_user_id is not None else 'invited'

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'referral_link_id': self.referral_link_id,
            'email': self.email,
            'invited_at': self.invited_at.isoformat() if self.invited_at else None,
            'email_log_id': self.email_log_id,
            'accepted_user_id': self.accepted_user_id,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'status': self.status,
        }
