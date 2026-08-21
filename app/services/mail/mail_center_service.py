"""
Mail-Center service — recipient resolution + send orchestration + log queries.

Sits between the Admin Mail-Center routes and the low-level
``email_service``. Owns three responsibilities:

1. **Recipient resolution** (``resolve_recipients``): turn a flexible
   ``recipient_spec`` (individual addresses, pasted/CSV text, ad-hoc list,
   by referral-link, by scenario+role) into a deduplicated, validated list of
   real inboxes. Synthetic ``@noemail.invalid`` and malformed addresses are
   skipped — never sent to, never counted.

2. **Send orchestration** (``send_invitations`` / ``send_announcement``):
   loop the resolved recipients through ``email_service``. Small lists send
   inline so the admin gets a truthful per-recipient result; larger lists send
   async (fire-and-forget) so the request returns promptly. A dedicated
   worker-queue for true mass sends is intentionally out of scope (documented
   in the concept) — noted in ``ASYNC_THRESHOLD`` below.

3. **Audit reads** (``query_log`` / ``link_invitation_stats``): paginated,
   filterable read of ``email_log`` and the invited→accepted funnel per link.

Email-source notes
------------------
- **Ref-link recipients** use the email captured at registration time in
  ``ReferralRegistration.metadata_json['email']`` — the LLARS-side source of
  truth, no Authentik round-trip needed.
- **Scenario/role recipients** have no email in the LLARS DB (it lives in
  Authentik), so we resolve per-username via ``AuthentikAdminService.find_user``
  — best-effort, skipping anyone without a real inbox.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Lists at or below this size send inline (blocking) so the UI can show a
# truthful sent/failed-per-recipient result. Above it we send async and log
# optimistically. A real mass-send belongs in a worker queue (out of scope).
ASYNC_THRESHOLD = 25

# Pragmatic email shape check — not full RFC 5322, just enough to drop garbage
# before we hand an address to SMTP.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_synthetic_or_blank(email: str) -> bool:
    """True for empty or non-deliverable ``@noemail.invalid`` placeholders."""
    addr = (email or "").strip().lower()
    return (not addr) or addr.endswith("@noemail.invalid")


def _valid_email(email: str) -> bool:
    addr = (email or "").strip()
    return bool(_EMAIL_RE.match(addr)) and not _is_synthetic_or_blank(addr)


def parse_address_blob(blob: str) -> List[str]:
    """Split a pasted/CSV/freeform blob into candidate addresses.

    Accepts commas, semicolons, whitespace and newlines as separators so a
    pasted CSV column or a comma-separated line both work.
    """
    if not blob:
        return []
    parts = re.split(r"[,;\s]+", blob.strip())
    return [p.strip() for p in parts if p.strip()]


class MailCenterService:
    """Stateless orchestration helpers for the Admin Mail-Center."""

    # ------------------------------------------------------------------ #
    # Recipient resolution
    # ------------------------------------------------------------------ #
    @staticmethod
    def resolve_recipients(spec: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
        """Resolve a recipient spec into a deduped, validated address list.

        ``spec`` may combine any of:
          - ``emails``: list[str]            — individual addresses
          - ``list_text``: str               — pasted / CSV blob
          - ``referral_link_id``: int        — users who registered via a link
          - ``scenario_id`` + ``role``       — scenario members (optional role
                                                filter: assessor/viewer/none)
          - ``role_name``: str               — all users with a system role

        Returns ``(addresses, info)`` where ``info`` reports the resolved
        count and how many were skipped (invalid / synthetic / duplicate),
        powering the "send to N recipients" preview before any send.
        """
        spec = spec or {}
        raw: List[str] = []

        # 1. Individual addresses + ad-hoc list.
        for addr in (spec.get('emails') or []):
            raw.append(str(addr))
        raw.extend(parse_address_blob(spec.get('list_text') or ''))

        # 2. By referral link — emails captured at registration time.
        if spec.get('referral_link_id'):
            raw.extend(MailCenterService._emails_for_referral_link(
                int(spec['referral_link_id'])
            ))

        # 3. By scenario (optionally filtered by evaluation role).
        if spec.get('scenario_id'):
            raw.extend(MailCenterService._emails_for_scenario(
                int(spec['scenario_id']), spec.get('role')
            ))

        # 4. By system role.
        if spec.get('role_name'):
            raw.extend(MailCenterService._emails_for_system_role(
                str(spec['role_name'])
            ))

        # Dedup (case-insensitive) + validate.
        seen = set()
        valid: List[str] = []
        skipped_invalid = 0
        skipped_dupe = 0
        for addr in raw:
            norm = (addr or '').strip()
            key = norm.lower()
            if not _valid_email(norm):
                skipped_invalid += 1
                continue
            if key in seen:
                skipped_dupe += 1
                continue
            seen.add(key)
            valid.append(norm)

        info = {
            'count': len(valid),
            'skipped_invalid': skipped_invalid,
            'skipped_duplicate': skipped_dupe,
            'total_candidates': len(raw),
        }
        return valid, info

    @staticmethod
    def _emails_for_referral_link(link_id: int) -> List[str]:
        """Registration-time emails for everyone who signed up via a link."""
        from db.models.referral import ReferralRegistration
        out: List[str] = []
        regs = ReferralRegistration.query.filter_by(link_id=link_id).all()
        for reg in regs:
            meta = reg.metadata_json or {}
            email = (meta.get('email') or '').strip()
            if email and not _is_synthetic_or_blank(email):
                out.append(email)
        return out

    @staticmethod
    def _emails_for_scenario(scenario_id: int, role: Optional[str]) -> List[str]:
        """Authentik emails of a scenario's members (optional eval-role filter)."""
        from db.models.scenario import ScenarioUsers
        from db.models.user import User

        q = ScenarioUsers.query.filter_by(scenario_id=scenario_id)
        if role:
            q = q.filter_by(evaluation_role=role)
        user_ids = [su.user_id for su in q.all() if su.user_id]
        usernames = [
            u.username for u in
            User.query.filter(User.id.in_(user_ids)).all()
        ] if user_ids else []
        return MailCenterService._emails_for_usernames(usernames)

    @staticmethod
    def _emails_for_system_role(role_name: str) -> List[str]:
        """Authentik emails of every user holding a given system role."""
        from db.models.permission import UserRole
        usernames = [
            ur.username for ur in
            UserRole.query.filter_by(role_name=role_name).all()
        ]
        return MailCenterService._emails_for_usernames(usernames)

    @staticmethod
    def _emails_for_usernames(usernames: List[str]) -> List[str]:
        """Best-effort Authentik email lookup per username.

        Authentik holds the authoritative email. We look up one-by-one (the
        admin API has no cheap bulk-by-username) and skip anyone Authentik
        can't resolve or who has no real inbox. Failures are swallowed so a
        flaky Authentik never aborts the whole resolve.
        """
        if not usernames:
            return []
        try:
            from services.authentik_admin_service import AuthentikAdminService
        except Exception:
            return []
        out: List[str] = []
        for username in usernames:
            try:
                rec = AuthentikAdminService.find_user(username)
            except Exception:
                rec = None
            email = ((rec or {}).get('email') or '').strip()
            if email and not _is_synthetic_or_blank(email):
                out.append(email)
        return out

    # ------------------------------------------------------------------ #
    # Send orchestration
    # ------------------------------------------------------------------ #
    @staticmethod
    def send_invitations(*, link, recipients: List[str],
                         intro: Optional[str] = None,
                         body_html: Optional[str] = None,
                         subject: Optional[str] = None,
                         triggered_by_user_id: Optional[int] = None) -> Dict[str, Any]:
        """Send branded invitations for ``link`` to ``recipients``.

        For each recipient: send the mail, then upsert a ``referral_invitation``
        row tied to the produced ``email_log`` row so the invited→accepted
        funnel can later be reconciled at registration time.

        ``body_html``/``subject``: optional override so the Mail-Center compose
        can send a chosen + edited per-org branded template instead of the
        generic invitation (still logged as type=invitation with this link).
        """
        from services import email_service
        from db.database import db
        from db.models.email_log import ReferralInvitation
        from services.referral_service import ReferralService

        link_url = MailCenterService._public_link_url(link)
        async_send = len(recipients) > ASYNC_THRESHOLD

        sent = failed = skipped = 0
        for email in recipients:
            result = email_service.send_invitation(
                to_email=email,
                link_url=link_url,
                label=link.label or link.code,
                intro=intro,
                body_html=body_html,
                subject=subject,
                referral_link_id=link.id,
                triggered_by_user_id=triggered_by_user_id,
                async_send=async_send,
            )
            status = result.get('status')
            if status == 'sent':
                sent += 1
            elif status == 'failed':
                failed += 1
            else:
                skipped += 1

            # Upsert the invitation row (one open invitation per link+email).
            try:
                norm = email.strip().lower()
                inv = ReferralInvitation.query.filter_by(
                    referral_link_id=link.id, email=norm
                ).first()
                if inv is None:
                    inv = ReferralInvitation(referral_link_id=link.id, email=norm)
                    db.session.add(inv)
                inv.email_log_id = result.get('log_id')
                db.session.commit()
            except Exception as exc:  # noqa: BLE001
                db.session.rollback()
                logger.warning("[mail-center] invitation row upsert failed: %s", exc)

        # Opportunistically reconcile already-registered users (an invite sent
        # AFTER someone signed up should still show as accepted).
        try:
            ReferralService  # touch to ensure import is intentional
            MailCenterService._reconcile_link_acceptances(link.id)
        except Exception:
            pass

        return {
            'requested': len(recipients),
            'sent': sent,
            'failed': failed,
            'skipped': skipped,
            'async': async_send,
            'link_url': link_url,
        }

    @staticmethod
    def send_announcement(*, subject: str, body: str, recipients: List[str],
                          scenario_id: Optional[int] = None,
                          triggered_by_user_id: Optional[int] = None) -> Dict[str, Any]:
        """Send a branded announcement to every resolved recipient."""
        from services import email_service

        async_send = len(recipients) > ASYNC_THRESHOLD
        sent = failed = skipped = 0
        for email in recipients:
            result = email_service.send_announcement(
                to_email=email,
                subject=subject,
                body=body,
                scenario_id=scenario_id,
                triggered_by_user_id=triggered_by_user_id,
                async_send=async_send,
            )
            status = result.get('status')
            if status == 'sent':
                sent += 1
            elif status == 'failed':
                failed += 1
            else:
                skipped += 1
        return {
            'requested': len(recipients),
            'sent': sent,
            'failed': failed,
            'skipped': skipped,
            'async': async_send,
        }

    @staticmethod
    def _public_link_url(link) -> str:
        """Absolute /join/<slug-or-code> URL for an invitation."""
        from services import email_service
        base = email_service._public_url()
        ident = link.slug or link.code
        return f"{base}/join/{ident}"

    # ------------------------------------------------------------------ #
    # Acceptance matching (called from registration + on (re)invite)
    # ------------------------------------------------------------------ #
    @staticmethod
    def match_invitation_on_registration(*, link_id: int, email: str,
                                         user_id: Optional[int]) -> bool:
        """Flip an open invitation to *accepted* when a matching email signs up.

        Honest about the optional-email gap: only matches when a real
        (non-synthetic) email was supplied at registration and an open
        invitation for that (link, email) exists. Returns True on a match.
        Best-effort — never raises into the registration flow.
        """
        if _is_synthetic_or_blank(email):
            return False
        try:
            from db.database import db
            from db.models.email_log import ReferralInvitation
            from datetime import datetime

            inv = ReferralInvitation.query.filter_by(
                referral_link_id=link_id, email=email.strip().lower()
            ).first()
            if inv is None or inv.accepted_user_id is not None:
                return False
            inv.accepted_user_id = user_id
            inv.accepted_at = datetime.now()
            db.session.commit()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("[mail-center] acceptance match failed: %s", exc)
            try:
                from db.database import db
                db.session.rollback()
            except Exception:
                pass
            return False

    @staticmethod
    def _reconcile_link_acceptances(link_id: int) -> int:
        """Match open invitations against existing registrations for a link.

        Covers the case where the invite is sent after the person already
        registered. Returns the number of newly-accepted invitations.
        """
        from db.database import db
        from db.models.email_log import ReferralInvitation
        from db.models.referral import ReferralRegistration
        from db.models.user import User
        from datetime import datetime

        open_invs = ReferralInvitation.query.filter_by(
            referral_link_id=link_id, accepted_user_id=None
        ).all()
        if not open_invs:
            return 0

        # Build email → username map from this link's registrations.
        reg_by_email: Dict[str, str] = {}
        for reg in ReferralRegistration.query.filter_by(link_id=link_id).all():
            email = ((reg.metadata_json or {}).get('email') or '').strip().lower()
            if email and not _is_synthetic_or_blank(email):
                reg_by_email[email] = reg.username

        matched = 0
        for inv in open_invs:
            username = reg_by_email.get(inv.email)
            if not username:
                continue
            user = User.query.filter_by(username=username).first()
            inv.accepted_user_id = user.id if user else None
            inv.accepted_at = datetime.now()
            matched += 1
        if matched:
            db.session.commit()
        return matched

    # ------------------------------------------------------------------ #
    # Audit reads
    # ------------------------------------------------------------------ #
    @staticmethod
    def query_log(*, mail_type: Optional[str] = None,
                  recipient: Optional[str] = None,
                  status: Optional[str] = None,
                  referral_link_id: Optional[int] = None,
                  scenario_id: Optional[int] = None,
                  date_from: Optional[str] = None,
                  date_to: Optional[str] = None,
                  limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Paginated, filterable read of the central ``email_log``."""
        from db.models.email_log import EmailLog
        from datetime import datetime

        q = EmailLog.query
        if mail_type:
            q = q.filter(EmailLog.mail_type == mail_type)
        if status:
            q = q.filter(EmailLog.status == status)
        if recipient:
            q = q.filter(EmailLog.recipient_email.ilike(f"%{recipient}%"))
        if referral_link_id:
            q = q.filter(EmailLog.referral_link_id == referral_link_id)
        if scenario_id:
            q = q.filter(EmailLog.scenario_id == scenario_id)
        if date_from:
            try:
                q = q.filter(EmailLog.created_at >= datetime.fromisoformat(date_from))
            except ValueError:
                pass
        if date_to:
            try:
                q = q.filter(EmailLog.created_at <= datetime.fromisoformat(date_to))
            except ValueError:
                pass

        total = q.count()
        rows = (
            q.order_by(EmailLog.created_at.desc())
            .limit(min(max(limit, 1), 200))
            .offset(max(offset, 0))
            .all()
        )
        return {
            'entries': [r.to_dict() for r in rows],
            'total': total,
            'limit': limit,
            'offset': offset,
        }

    # ------------------------------------------------------------------ #
    # Engagement tracking (Brevo open/click webhook)
    # ------------------------------------------------------------------ #
    @staticmethod
    def record_engagement_event(*, event: str,
                                provider_message_id: Optional[str] = None,
                                recipient_email: Optional[str] = None,
                                subject: Optional[str] = None,
                                event_ts: Optional[Any] = None) -> Dict[str, Any]:
        """Stamp ``opened_at`` / ``clicked_at`` on the matching ``email_log`` row.

        Called from the Brevo webhook (``POST /api/webhooks/brevo``) for the
        provider event types we care about:

        - ``opened`` / ``unique_opened`` → set ``opened_at``
        - ``click``                      → set ``clicked_at``

        Matching strategy (first that hits wins):
          1. by ``provider_message_id`` — the self-assigned ``Message-ID`` we
             stamped on the outgoing mail (deterministic, the common case).
          2. fallback: most-recent row with the same ``recipient_email`` (and
             ``subject`` when supplied) — used only when the provider strips /
             rewrites the Message-ID.

        **First occurrence wins**: a re-delivered event for an already-stamped
        row is a no-op, so the handler is idempotent. Returns a small status
        dict ``{matched: bool, action: str, log_id: int|None}`` for logging.
        Never raises — webhook handlers must always answer 200 quickly.
        """
        from db.database import db
        from db.models.email_log import EmailLog
        from datetime import datetime

        ev = (event or '').strip().lower()
        # Normalise the event to the column it should stamp.
        if ev in ('opened', 'unique_opened', 'open', 'first_opening'):
            column = 'opened_at'
        elif ev in ('click', 'clicked'):
            column = 'clicked_at'
        else:
            return {'matched': False, 'action': 'ignored_event', 'log_id': None}

        # Normalise the provider message-id: Brevo may send it wrapped in
        # angle brackets (<...>) or bare — match both shapes.
        row = None
        mid = (provider_message_id or '').strip()
        try:
            if mid:
                stripped = mid.strip('<>').strip()
                candidates = {mid, stripped, f'<{stripped}>'}
                row = (
                    EmailLog.query
                    .filter(EmailLog.provider_message_id.in_(list(candidates)))
                    .order_by(EmailLog.created_at.desc())
                    .first()
                )

            # Fallback: most-recent send to this recipient (+ subject if given).
            if row is None and recipient_email:
                q = EmailLog.query.filter(
                    EmailLog.recipient_email == recipient_email.strip()
                )
                if subject:
                    q = q.filter(EmailLog.subject == subject)
                row = q.order_by(EmailLog.created_at.desc()).first()

            if row is None:
                return {'matched': False, 'action': 'no_match', 'log_id': None}

            # First-occurrence-wins idempotency.
            current = getattr(row, column)
            if current is not None:
                return {'matched': True, 'action': 'already_set', 'log_id': row.id}

            # Use the event timestamp when provided, else "now".
            ts = None
            if isinstance(event_ts, datetime):
                ts = event_ts
            elif isinstance(event_ts, str) and event_ts.strip():
                try:
                    ts = datetime.fromisoformat(event_ts.strip().replace('Z', '+00:00'))
                except ValueError:
                    ts = None
            setattr(row, column, ts or datetime.now())
            db.session.commit()
            return {'matched': True, 'action': f'set_{column}', 'log_id': row.id}
        except Exception as exc:  # noqa: BLE001 — webhook must never 500 on a row
            logger.warning("[mail-center] engagement event failed: %s", exc)
            try:
                db.session.rollback()
            except Exception:
                pass
            return {'matched': False, 'action': 'error', 'log_id': None}

    @staticmethod
    def link_invitation_stats(link_id: int) -> Dict[str, Any]:
        """Invited / accepted / pending funnel for a referral link.

        Honest about the optional-email gap: ``registered_unmatched`` counts
        users who registered via the link but whose email could not be matched
        to an invitation (no email given, or a different address). Surfaced so
        the UI can show "+N Registrierungen ohne E-Mail-Zuordnung" instead of
        silently under-counting acceptance.
        """
        from db.models.email_log import ReferralInvitation
        from db.models.referral import ReferralRegistration

        invs = ReferralInvitation.query.filter_by(referral_link_id=link_id).all()
        invited = len(invs)
        accepted = sum(1 for i in invs if i.accepted_user_id is not None)
        pending = invited - accepted

        # Registrations via this link whose email did not match an invitation.
        invited_emails = {i.email for i in invs}
        accepted_emails = {i.email for i in invs if i.accepted_user_id is not None}
        registered_unmatched = 0
        total_registrations = 0
        for reg in ReferralRegistration.query.filter_by(link_id=link_id).all():
            total_registrations += 1
            email = ((reg.metadata_json or {}).get('email') or '').strip().lower()
            if (not email) or _is_synthetic_or_blank(email):
                registered_unmatched += 1
            elif email in invited_emails and email in accepted_emails:
                pass  # already counted as accepted
            elif email not in invited_emails:
                registered_unmatched += 1

        return {
            'link_id': link_id,
            'invited': invited,
            'accepted': accepted,
            'pending': pending,
            'total_registrations': total_registrations,
            'registered_unmatched': registered_unmatched,
            'invitations': [i.to_dict() for i in invs],
        }
