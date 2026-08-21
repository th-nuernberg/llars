"""
Admin Mail-Center routes — invitations, announcements, preview, and the
central mail log.

Auth model
----------
EVERY endpoint here is gated by ``@require_permission('feature:admin:mail')``.
That decorator accepts EITHER:
  * the System Admin API key via the ``X-API-Key`` header (same mechanism as
    the ``/api/v1/*`` routes — see ``decorators/permission_decorator``: a valid
    key bypasses the per-user check and acts as ``admin``), OR
  * an authenticated OIDC user (Authentik bearer token) who holds the
    ``feature:admin:mail`` permission — by default only the ``admin`` role.

In other words: ONLY admins (or the system API key) can reach these routes.
Mounted on ``data_bp`` (``/api`` prefix), giving:

  POST /api/admin/mail/invite
  POST /api/admin/mail/announce
  POST /api/admin/mail/preview
  GET  /api/admin/mail/templates
  GET  /api/admin/mail/log
  GET  /api/admin/referral/links/<id>/invitations

See app/services/mail/mail_center_service.py for resolution + send logic and
.claude/plans/admin-mail-center-concept.md for the design.
"""

import logging

from flask import jsonify, request, g

from decorators.error_handler import (
    handle_api_errors, ValidationError, NotFoundError,
)
from decorators.permission_decorator import require_permission
from routes.auth import data_bp
from services.mail.mail_center_service import MailCenterService

logger = logging.getLogger(__name__)

MAIL_ADMIN_PERMISSION = 'feature:admin:mail'


def _triggered_by_user_id():
    """Resolve the acting admin's user id for the audit trail (None for API key)."""
    user = getattr(g, 'authentik_user', None)
    return getattr(user, 'id', None) if user else None


def _get_link_or_404(link_id: int):
    from db.models.referral import ReferralLink
    link = ReferralLink.query.get(link_id)
    if link is None:
        raise NotFoundError(f"Einladungslink {link_id} nicht gefunden")
    return link


@data_bp.post('/admin/mail/invite')
@require_permission(MAIL_ADMIN_PERMISSION)
@handle_api_errors(logger_name='mail_admin')
def mail_invite():
    """Send a branded invitation (with the link embedded) to each recipient.

    Body: ``{referral_link_id, recipients[], intro?}`` — ``recipients`` is an
    ad-hoc address list; it is normalised/validated/deduped by the resolver.
    Logs each send as ``email_log`` (type=invitation, referral_link_id set) and
    upserts ``referral_invitation`` rows for the accept-funnel.
    """
    data = request.get_json() or {}
    link_id = data.get('referral_link_id')
    if not link_id:
        raise ValidationError("referral_link_id ist erforderlich")
    link = _get_link_or_404(int(link_id))

    recipients, info = MailCenterService.resolve_recipients(
        {'emails': data.get('recipients') or [], 'list_text': data.get('list_text') or ''}
    )
    if not recipients:
        raise ValidationError("Keine gültigen Empfänger nach Validierung")

    result = MailCenterService.send_invitations(
        link=link,
        recipients=recipients,
        intro=(data.get('intro') or None),
        # Optional per-org branded template the admin picked + edited in the
        # compose UI; sent verbatim instead of the generic invitation.
        body_html=(data.get('body_html') or None),
        subject=(data.get('subject') or None),
        triggered_by_user_id=_triggered_by_user_id(),
    )
    return jsonify({'success': True, 'result': result, 'resolution': info})


@data_bp.post('/admin/mail/announce')
@require_permission(MAIL_ADMIN_PERMISSION)
@handle_api_errors(logger_name='mail_admin')
def mail_announce():
    """Send a branded announcement (custom subject + Markdown/text body).

    Body: ``{subject, body, recipient_spec}`` where ``recipient_spec`` may
    combine individual addresses, a pasted list, a referral link, a scenario
    (+role) and/or a system role (see resolver). Logs each as
    ``email_log`` (type=announcement).
    """
    data = request.get_json() or {}
    subject = (data.get('subject') or '').strip()
    body = data.get('body') or ''
    if not subject:
        raise ValidationError("subject ist erforderlich")
    if not body.strip():
        raise ValidationError("body ist erforderlich")

    spec = data.get('recipient_spec') or {}
    recipients, info = MailCenterService.resolve_recipients(spec)
    if not recipients:
        raise ValidationError("Keine gültigen Empfänger nach Validierung")

    result = MailCenterService.send_announcement(
        subject=subject,
        body=body,
        recipients=recipients,
        scenario_id=spec.get('scenario_id'),
        triggered_by_user_id=_triggered_by_user_id(),
    )
    return jsonify({'success': True, 'result': result, 'resolution': info})


@data_bp.post('/admin/mail/send-template')
@require_permission(MAIL_ADMIN_PERMISSION)
@handle_api_errors(logger_name='mail_admin')
def mail_send_template():
    """Quick-send: dispatch a chosen template (as shown in the "Vorlagen" tab) to
    a single entered address — the Mail-Center "Schnellversand".

    Body: ``{email, type?, subject?, body_html?}``. Pass ``type``
    (``welcome``|``password_reset``|``invitation``) to send a standard
    transactional template with its sample data, OR ``subject`` + ``body_html``
    to send a bundled branded template verbatim. Renders byte-identical to the
    preview, sends synchronously (truthful per-send result) and logs one
    ``email_log`` row (variant ``quick_send``).
    """
    from services import email_service

    data = request.get_json() or {}
    raw_email = (data.get('email') or '').strip()
    if not raw_email:
        raise ValidationError("email ist erforderlich")
    # Reuse the resolver to normalise + validate the single address (drops
    # malformed / synthetic @noemail.invalid addresses).
    recipients, _info = MailCenterService.resolve_recipients({'emails': [raw_email]})
    if not recipients:
        raise ValidationError("Keine gültige E-Mail-Adresse")
    to_email = recipients[0]

    tpl_type = (data.get('type') or '').strip()
    # Treat whitespace-only HTML as absent so the validation below is honest
    # (an empty body_html is "not provided", not a valid template to send).
    body_html = (data.get('body_html') or '').strip() or None
    triggered_by = _triggered_by_user_id()

    if tpl_type:
        try:
            result = email_service.send_standard_template(
                template_type=tpl_type,
                to_email=to_email,
                triggered_by_user_id=triggered_by,
                async_send=False,
            )
        except ValueError as exc:
            raise ValidationError(str(exc))
    elif body_html:
        result = email_service.send_quick_html(
            to_email=to_email,
            subject=(data.get('subject') or '').strip(),
            body_html=body_html,
            triggered_by_user_id=triggered_by,
            async_send=False,
        )
    else:
        raise ValidationError("type oder body_html ist erforderlich")

    return jsonify({'success': True, 'result': {**result, 'email': to_email}})


@data_bp.post('/admin/mail/preview')
@require_permission(MAIL_ADMIN_PERMISSION)
@handle_api_errors(logger_name='mail_admin')
def mail_preview():
    """Render the mail and resolve recipient count WITHOUT sending.

    Body: ``{mode: 'invitation'|'announcement', ...}``. For invitation also
    accepts ``referral_link_id`` + ``intro``; for announcement ``subject`` +
    ``body``. ``recipient_spec`` (or ``recipients``) is resolved to a count.
    Returns the rendered ``subject``/``html`` plus the resolved recipient info.
    """
    from services import email_service

    data = request.get_json() or {}
    mode = (data.get('mode') or 'announcement').strip()

    if mode == 'invitation':
        link_id = data.get('referral_link_id')
        if not link_id:
            raise ValidationError("referral_link_id ist erforderlich")
        link = _get_link_or_404(int(link_id))
        link_url = MailCenterService._public_link_url(link)
        body_html = data.get('body_html') or None
        if body_html:
            # The admin picked + edited a per-org branded template: preview it
            # verbatim (what will actually be sent), no generic re-render.
            rendered = {
                'subject': (data.get('subject') or 'Kann KI Beratung?').strip(),
                'body_html': body_html,
                'body_text': '',
            }
        else:
            rendered = email_service.render_invitation(
                link_url=link_url,
                label=link.label or link.code,
                intro=(data.get('intro') or None),
            )
        spec = {'emails': data.get('recipients') or [],
                'list_text': data.get('list_text') or ''}
    else:
        subject = (data.get('subject') or '').strip()
        body = data.get('body') or ''
        if not subject:
            raise ValidationError("subject ist erforderlich")
        rendered = email_service.render_announcement(subject=subject, body=body)
        spec = data.get('recipient_spec') or {}

    _, info = MailCenterService.resolve_recipients(spec)
    return jsonify({
        'success': True,
        'subject': rendered['subject'],
        'html': rendered['body_html'],
        'text': rendered['body_text'],
        'recipients': info,
    })


@data_bp.get('/admin/mail/templates')
@require_permission(MAIL_ADMIN_PERMISSION)
@handle_api_errors(logger_name='mail_admin')
def mail_templates():
    """Render the standard transactional templates with SAMPLE data (no send).

    The three automatic mails (welcome / password_reset / invitation) are
    otherwise only ever sent — this lets an admin preview exactly what users
    receive. Sample data is clearly fake (e.g. username "Max Mustermann").

    Query: optional ``type`` (``welcome``|``password_reset``|``invitation``) to
    render a single template; without it all three are returned. Each entry
    carries ``{type, subject, html, text, description, variables}``.
    """
    from services import email_service

    mail_type = request.args.get('type')
    if mail_type:
        try:
            template = email_service.render_standard_template(mail_type)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return jsonify({'success': True, 'templates': [template]})

    return jsonify({
        'success': True,
        'templates': email_service.render_standard_templates(),
    })


@data_bp.get('/admin/mail/log')
@require_permission(MAIL_ADMIN_PERMISSION)
@handle_api_errors(logger_name='mail_admin')
def mail_log():
    """Paginated, filterable read of the central mail log.

    Query params: ``type`` (mail_type), ``recipient``, ``status``,
    ``referral_link_id``, ``scenario_id``, ``date_from``, ``date_to`` (ISO),
    ``limit`` (<=200), ``offset``.
    """
    result = MailCenterService.query_log(
        mail_type=request.args.get('type'),
        recipient=request.args.get('recipient'),
        status=request.args.get('status'),
        referral_link_id=request.args.get('referral_link_id', type=int),
        scenario_id=request.args.get('scenario_id', type=int),
        date_from=request.args.get('date_from'),
        date_to=request.args.get('date_to'),
        limit=request.args.get('limit', 50, type=int),
        offset=request.args.get('offset', 0, type=int),
    )
    return jsonify({'success': True, **result})


@data_bp.get('/admin/referral/links/<int:link_id>/invitations')
@require_permission(MAIL_ADMIN_PERMISSION)
@handle_api_errors(logger_name='mail_admin')
def referral_link_invitations(link_id: int):
    """Invited / accepted / pending funnel for a referral link.

    Includes an honest ``registered_unmatched`` count for link sign-ups whose
    email could not be matched to an invitation (optional-email gap).
    """
    _get_link_or_404(link_id)
    stats = MailCenterService.link_invitation_stats(link_id)
    return jsonify({'success': True, 'stats': stats})
