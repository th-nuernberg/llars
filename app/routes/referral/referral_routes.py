"""
Referral System API Routes.

Provides endpoints for:
- Public link validation and registration
- Admin campaign management
- Admin link management
- Analytics
"""

import hashlib
import re as _re
import secrets
from flask import Blueprint, jsonify, request, g
from datetime import datetime

from auth.decorators import authentik_required, public_endpoint
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, ValidationError, NotFoundError, ConflictError
)
from services.referral_service import ReferralService
from db.models.referral import ReferralCampaignStatus

referral_bp = Blueprint('referral', __name__, url_prefix='/api/referral')


def _sanitize_username(raw: str) -> str:
    """Keep only username-safe chars (alnum, _, -); fall back to a random demo id."""
    u = _re.sub(r'[^A-Za-z0-9_-]', '', raw or '')[:48]
    return u or ('demo-' + secrets.token_hex(4))


def _demo_username_from_email(email: str, link) -> str:
    """Deterministic demo username from email+link.

    The SAME email re-entering the SAME link maps to the SAME account, which is
    what lets the 'email' signup mode log a returning visitor back in (QR +
    email) without them ever knowing a password.
    """
    slug = (getattr(link, 'slug', None) or getattr(link, 'code', None) or 'demo')
    h = hashlib.sha1(f"{(email or '').strip().lower()}|{slug}".encode('utf-8')).hexdigest()[:10]
    return _sanitize_username(f"demo-{slug}-{h}")


def _demo_username_random(link) -> str:
    """Fresh anonymous demo username (used by the 'instant' signup mode)."""
    slug = (getattr(link, 'slug', None) or getattr(link, 'code', None) or 'demo')
    return _sanitize_username(f"demo-{slug}-{secrets.token_hex(4)}")


def _post_enroll_redirect(user) -> str:
    """Where to send a user right after (first) sign-in, based on how many
    evaluation scenarios they're an assessor in:

    - exactly 1  -> straight into that scenario's evaluation flow
    - more than 1 -> the evaluation hub (/evaluation) so they can pick
    - none        -> home

    This keeps multi-scenario participants (e.g. the IJCAI demo link → 7
    scenarios) from being dropped into an arbitrary single scenario.
    """
    try:
        from db.models.scenario import ScenarioUsers, MembershipStatus
        rows = ScenarioUsers.query.filter(
            ScenarioUsers.user_id == user.id,
            ScenarioUsers.evaluation_role == 'assessor',
            ScenarioUsers.membership_status != MembershipStatus.ARCHIVED,
        ).all()
        sids = list({r.scenario_id for r in rows})
        if len(sids) == 1:
            return f"/scenarios/{sids[0]}/evaluate"
        if len(sids) > 1:
            return "/evaluation"
    except Exception:
        pass
    return "/Home"


def _send_referral_signin_link(username: str, email: str, locale: str = 'en', link_id=None) -> None:
    """Email a one-time passwordless QUICK-LOGIN link to a RETURNING email-mode
    registrant.

    Closes the deterministic-username takeover: an existing account must prove
    control of the email (by clicking the emailed one-click link) before any
    login — instead of the server resetting the password and handing an
    auto-login token to whoever merely typed the address. The mail is the same
    passwordless /auto-login style as the welcome mail (no password-reset step),
    in the link's language.
    """
    import services.email_service as email_service
    email_service.send_magic_login_email(
        username=username,
        email=email,
        locale=locale,
        referral_link_id=link_id,
    )


def _is_study_link(link) -> bool:
    """Decide whether a referral link is part of the research study.

    A link counts as a study link — and therefore requires the GDPR study
    consent on the register form — when either:
      * its slug/label matches a known study pattern, OR
      * it is bound to a target scenario (every scenario-bound referral-join
        is a study participation, regardless of how the slug is spelled).

    Centralised so the public ``/validate`` hint and the ``/register`` hard
    gate never disagree.
    """
    slug = (getattr(link, 'slug', '') or '').lower()
    label = (getattr(link, 'label', '') or '').lower()
    return bool(
        slug.startswith('human_comparison_')
        or slug.startswith('study_')
        or slug.startswith('llars-study')
        or 'study' in label
        or getattr(link, 'target_scenario_id', None) is not None
    )


# ============================================================================
# Public Endpoints (No Auth Required)
# ============================================================================

@referral_bp.route('/system/status', methods=['GET'])
@public_endpoint
@handle_api_errors(logger_name='referral')
def get_referral_status():
    """
    Get public status of referral system.

    Returns only whether registration is enabled.
    Used by frontend to show/hide register button.
    """
    return jsonify({
        'success': True,
        'registration_enabled': (
            ReferralService.is_referral_enabled() and
            ReferralService.is_self_registration_enabled()
        )
    })


@referral_bp.route('/validate/<code_or_slug>', methods=['GET'])
@public_endpoint
@handle_api_errors(logger_name='referral')
def validate_referral_link(code_or_slug: str):
    """
    Validate a referral code or slug.

    Public endpoint - no auth required.
    Used by registration form to validate codes before submission.
    """
    is_valid, link, error = ReferralService.validate_link(code_or_slug)

    if not is_valid:
        return jsonify({
            'success': False,
            'valid': False,
            'error': error
        }), 400

    # Count this page load as a visit/click for the admin funnel
    # ("X Aufrufe -> Y registriert"). Best-effort and atomic: a single
    # UPDATE ... SET click_count = click_count + 1 avoids read-modify-write
    # races, and any failure is swallowed so a tracking hiccup never breaks
    # link validation. One increment per validate call is the accepted unit —
    # bot / link-preview prefetches may inflate it slightly.
    ReferralService.increment_click_count(link.id)

    return jsonify({
        'success': True,
        'valid': True,
        'campaign_name': link.campaign.name,
        'role': link.role_name,
        'label': link.label,
        'slug': link.slug,
        # Form-shape hints. Defaults TRUE matches the pre-flag behaviour.
        'collect_email': bool(getattr(link, 'collect_email', True)),
        'collect_display_name': bool(getattr(link, 'collect_display_name', True)),
        # When email is collected, whether the field is optional (default
        # FALSE = required, matching the legacy behaviour).
        'collect_email_optional': bool(getattr(link, 'collect_email_optional', False)),
        # Registration friction variant the form must render:
        #   full    - username + password (+ email per collect flags)
        #   email   - only an email (username + password handled server-side)
        #   instant - one tap, nothing asked
        'signup_mode': (getattr(link, 'signup_mode', 'full') or 'full'),
        # Default UI language for this link — the /join page switches to it
        # pre-login and it's persisted to the new user's profile.
        'default_locale': (getattr(link, 'default_locale', 'de') or 'de'),
        # Whether this link participates in the research study and therefore
        # requires the data-protection / study consent on the register form.
        # Authoritative server-side signal (mirrors register_via_referral):
        # slug/label patterns OR any link bound to a target scenario — every
        # scenario-bound referral-join is a study participation. The frontend
        # used to guess this from the slug alone, which missed friendly slugs
        # like ``kann-ki-beratung-digi-sucht``.
        'is_study': _is_study_link(link),
        # Forwarded so the consent block can render for scenario-bound links
        # even when the slug carries no study keyword.
        'target_scenario_id': link.target_scenario_id,
    })


@referral_bp.route('/register', methods=['POST'])
@public_endpoint
@handle_api_errors(logger_name='referral')
def register_via_referral():
    """
    Register a new user via referral link.

    Creates user in Authentik and LLARS DB, assigns role,
    and records the registration for tracking.
    """
    data = request.get_json() or {}

    code = data.get('referral_code') or data.get('code')
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    display_name = (data.get('display_name') or data.get('name') or '').strip()
    # Optional opt-in: may we store the email to contact this user about
    # future studies (GDPR opt-in, default False). Coerced to a strict bool
    # below; only meaningful when a real email is actually provided, so we
    # persist it only on the real-email branch (never for synthetic
    # placeholder addresses). Accepts JSON true/false as well as the string
    # "true" defensively, in case a non-JSON client posts form-encoded data.
    store_email_consent_raw = data.get('store_email_consent', False)
    store_email_consent = (
        store_email_consent_raw is True
        or str(store_email_consent_raw).strip().lower() == 'true'
    )

    # Validate referral code present, then resolve the link FIRST — its
    # signup_mode decides how much the registration form has to ask for.
    if not code:
        raise ValidationError("Einladungscode ist erforderlich")
    is_valid, link, error = ReferralService.validate_link(code)
    if not is_valid:
        raise ValidationError(error)

    # Needed up here for the email-mode returning-user check (cached; also
    # imported again below for user creation).
    from services.authentik_admin_service import AuthentikAdminService

    # signup_mode controls the friction:
    #   full    - user types username + password (+ email per collect_* flags)
    #   email   - only an email; username derived deterministically (re-login by
    #             QR+email), password server-generated
    #   instant - one tap; everything auto-generated (anonymous account per scan)
    signup_mode = (getattr(link, 'signup_mode', 'full') or 'full').lower()
    collect_email = bool(getattr(link, 'collect_email', True))
    collect_email_optional = bool(getattr(link, 'collect_email_optional', False))
    collect_display_name = bool(getattr(link, 'collect_display_name', True))
    # Whether the persisted email is real (vs. a synthetic .invalid placeholder).
    has_real_email = bool(email)
    returning_user = False

    def _synthetic_email(_username: str) -> str:
        # RFC 6761 §6.4 .invalid TLD — guaranteed non-resolvable, never a real inbox.
        slug = (link.slug or 'noemail').lower().replace('/', '-')
        return f"{_username}+{slug}@noemail.invalid"

    if signup_mode == 'email':
        if not email or '@' not in email or '.' not in email:
            raise ValidationError("Gültige E-Mail-Adresse ist erforderlich")
        username = _demo_username_from_email(email, link)
        password = secrets.token_urlsafe(24)
        has_real_email = True
        # Same email re-entering -> same username -> log them back in below.
        returning_user = AuthentikAdminService.find_user(username) is not None
    elif signup_mode == 'instant':
        username = _demo_username_random(link)
        password = secrets.token_urlsafe(24)
        email = _synthetic_email(username)
        has_real_email = False
        display_name = display_name or username
    else:
        # 'full' (legacy): user-supplied username + password.
        if not username:
            raise ValidationError("Benutzername ist erforderlich")
        if not password or len(password) < 8:
            raise ValidationError("Passwort muss mindestens 8 Zeichen haben")
        if len(username) < 3:
            raise ValidationError("Benutzername muss mindestens 3 Zeichen haben")
        if not username.replace('_', '').replace('-', '').isalnum():
            raise ValidationError("Benutzername darf nur Buchstaben, Zahlen, _ und - enthalten")

        # Email per collect flags. Blank -> synthetic .invalid placeholder.
        # - collect_email=FALSE                                  → field hidden, optional
        # - collect_email=TRUE + collect_email_optional=TRUE     → shown, optional
        # - collect_email=TRUE + collect_email_optional=FALSE    → shown, required (legacy)
        if collect_email and not collect_email_optional:
            if not email:
                raise ValidationError("E-Mail ist erforderlich")
            if '@' not in email or '.' not in email:
                raise ValidationError("Ungültige E-Mail-Adresse")
        else:
            if email and ('@' not in email or '.' not in email):
                raise ValidationError("Ungültige E-Mail-Adresse")
            if not email:
                email = _synthetic_email(username)

    # Display-name handling: when the link disabled the field but something was
    # submitted anyway, ignore it.
    if not collect_display_name:
        display_name = ''

    # SECURITY: secure re-login for 'email' mode. An EXISTING account must prove
    # control of the email via a one-time link before any login — we must NOT
    # reset its password and hand an auto-login token to whoever merely typed the
    # (deterministically-derived) address. Email the sign-in link and stop here.
    if signup_mode == 'email' and returning_user:
        try:
            _send_referral_signin_link(
                username, email,
                locale=(getattr(link, 'default_locale', 'de') or 'de'),
                link_id=link.id,
            )
        except Exception:
            import logging as _lg
            _lg.getLogger('referral').warning(
                "Sign-in link send failed for returning user %s", username
            )
        # Neutral response either way (don't reveal whether the email exists).
        return jsonify({
            'success': True,
            'returning': True,
            'verification_sent': True,
            'message': (
                'Diese E-Mail ist bereits registriert. Wir haben dir einen '
                'Anmelde-Link geschickt. / This email is already registered — '
                'we sent you a sign-in link.'
            ),
        }), 200

    # Research study consent (GDPR Art. 6(1)(a) + Art. 9(2)(a)+(j) +
    # Art. 89(1) + Recital 33 + §27 Abs.1 BDSG + §22 Abs.2 BDSG).
    #
    # Single bundled consent for storage + pseudonymised analysis +
    # aggregated publication + reuse for topically related follow-up
    # studies at KIZ TH Nürnberg. NO row-level dataset release on
    # Zenodo / HuggingFace planned — text says so explicitly, so a
    # separate opt-in for that purpose isn't required under Art. 7(4).
    #
    # Append-only audit row carries:
    #   - consent_version           (e.g. study-consent-v3-2026-05)
    #   - consent_text_sha256       (digest of the exact text bytes shown)
    #   - granted_at_utc            (server-side timestamp)
    #   - granted_at_client         (browser timestamp from useStudyConsent)
    #   - ip_hash                   (SHA-256 of FLASK_SECRET_KEY + raw IP)
    #   - user_agent                (truncated to 512 chars)
    #   - referral_slug             (which study the user landed on)
    #   - language                  (DE/EN — which text version they saw)
    #   - participation             (always True if record exists)
    consent_in = data.get('consent') or {}
    is_study_link = _is_study_link(link)
    consent_record = None
    if is_study_link:
        # Single mandatory consent — older callers may still send the
        # legacy three-key shape; accept either as the trigger but only
        # require that *at least one* mandatory key is True. The label
        # the user clicked covers all three former purposes.
        legacy_mandatory_keys = [
            'study_participation',
            'data_storage_pseudonymized',
            'research_publication',
        ]
        granted = (
            bool(consent_in.get('participation'))
            or any(bool(consent_in.get(k)) for k in legacy_mandatory_keys)
        )
        if not granted:
            raise ValidationError(
                "Einwilligung zu Forschungszwecken erforderlich"
            )

        import hashlib
        import os
        # Hash the IP with a salt derived from FLASK_SECRET_KEY so the
        # raw IP is never persisted — we keep evidence of *which* network
        # consented without storing PII directly. The salt is stable per
        # deploy, which is enough for forensic IR ("did the same IP
        # consent twice?") without being a unique reverse-lookup key.
        salt = (os.environ.get('FLASK_SECRET_KEY') or 'llars-consent-salt')[:32]
        raw_ip = request.remote_addr or ''
        ip_hash = hashlib.sha256((salt + raw_ip).encode('utf-8')).hexdigest() if raw_ip else None

        # Resolve the SHA-256 of the canonical consent text bytes the
        # user saw, in the language they registered in. Stored in the
        # audit row so we can cryptographically prove later which exact
        # text was accepted, per BayLDA OH Einwilligung Rn. 118-124.
        try:
            from legal.consents import (
                CONSENT_VERSION as CANONICAL_VERSION,
                CONSENT_TEXT_SHA256_DE,
                CONSENT_TEXT_SHA256_EN,
            )
        except ImportError:
            CANONICAL_VERSION = 'study-consent-v3-2026-05'
            CONSENT_TEXT_SHA256_DE = ''
            CONSENT_TEXT_SHA256_EN = ''

        language = (data.get('locale') or 'en')[:2].lower()
        text_sha = (
            CONSENT_TEXT_SHA256_DE if language == 'de'
            else CONSENT_TEXT_SHA256_EN
        )

        consent_record = {
            'version': consent_in.get('version') or CANONICAL_VERSION,
            'consent_text_sha256': text_sha,
            'timestamp': datetime.now().isoformat(),
            'granted_at_client': consent_in.get('granted_at_client'),
            # Single bundled consent. Kept as `participation=True` here
            # and mirrored to the three legacy keys so downstream
            # analysis queries that filter on the old field names
            # continue to work without migration.
            'participation': True,
            'study_participation': True,
            'data_storage_pseudonymized': True,
            'research_publication': True,
            'language': language,
            'referral_slug': link.slug,
            'ip_hash': ip_hash,
            'user_agent': (request.headers.get('User-Agent') or '')[:512],
        }

    # Create the user in Authentik — or, for a returning demo visitor (email
    # mode: same email → same deterministic username), reset their password to
    # the freshly minted one so we can issue an auto-login token below. They
    # never know a password; re-entering the same email IS the identity proof.
    if returning_user:
        ok, set_err = AuthentikAdminService.set_password(username, password)
        if not ok:
            raise ValidationError(f"Re-Login fehlgeschlagen: {set_err}")
    else:
        success, error_msg, authentik_data = AuthentikAdminService.create_user(
            username=username,
            email=email,
            password=password,
            name=display_name or username,
            is_active=True
        )
        if not success:
            if "already exists" in (error_msg or "").lower():
                # In passwordless demo modes a collision just means the account
                # exists (race / re-entry) — adopt it by resetting the password
                # rather than 409-ing the visitor out.
                if signup_mode in ('email', 'instant'):
                    ok, set_err = AuthentikAdminService.set_password(username, password)
                    if not ok:
                        raise ConflictError(f"Konto existiert bereits: {username}")
                    returning_user = True
                else:
                    raise ConflictError(f"Benutzer '{username}' existiert bereits")
            else:
                raise ValidationError(f"Fehler beim Erstellen des Benutzers: {error_msg}")

    # Create LLARS user record
    from auth.decorators import get_or_create_user
    user = get_or_create_user(username)

    # Persist this link's default UI language to the user's profile so the app
    # stays in that language on every (re-)login — the IJCAI demo link is 'en',
    # all other links default to 'de'. Best-effort; a failure never blocks signup.
    try:
        _link_locale = (getattr(link, 'default_locale', 'de') or 'de')
        from db.database import db as _db
        prefs = dict(user.settings_json or {})
        prefs['language'] = _link_locale
        user.settings_json = prefs
        _db.session.add(user)
        _db.session.commit()
    except Exception:
        import logging as _lg
        _lg.getLogger('referral').warning("Could not persist language for %s", username)

    # Assign role from referral link.
    # SECURITY: this endpoint is public (@public_endpoint) and creates a real
    # account, so the role a referral link can confer MUST be allowlisted —
    # otherwise an admin-created link (or a compromised admin:referral:manage
    # actor) could grant 'admin' to anyone who self-registers, bypassing
    # admin:roles:manage. Anything outside the safe set falls back to evaluator.
    from services.permission_service import PermissionService
    from services.referral_service import ALLOWED_REFERRAL_ROLES
    import logging as _logging
    desired_role = (getattr(link, 'role_name', None) or 'evaluator')
    if desired_role not in ALLOWED_REFERRAL_ROLES:
        _logging.getLogger('referral').warning(
            "Referral link %s requested disallowed role '%s' — refusing, assigning 'evaluator'",
            getattr(link, 'id', '?'), desired_role,
        )
        desired_role = 'evaluator'
    try:
        PermissionService.assign_role(
            username=username,
            role_name=desired_role,
            admin_username='referral_system'
        )
    except Exception as e:
        # Log but don't fail - user is created, role assignment is best-effort
        _logging.getLogger('referral').warning(
            f"Failed to assign role {desired_role} to {username}: {e}"
        )

    # Record registration for tracking
    registration_metadata = {'email': email, 'display_name': display_name}
    if consent_record is not None:
        registration_metadata['consent'] = consent_record
    # Optional "store my email for future-study contact" opt-in. Only recorded
    # when a real email is present (synthetic placeholders are never
    # contactable). A future mailing can filter consenting users by querying
    # ReferralRegistration.metadata_json for email_contact_consent = true.
    if has_real_email:
        registration_metadata['email_contact_consent'] = store_email_consent
    ReferralService.register_user(
        link=link,
        username=username,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        metadata=registration_metadata
    )

    # Mail-Center: if this signup carried a real email that matches an open
    # admin invitation for this link, flip that invitation to "accepted".
    # Best-effort — registrations without an email (or with a different one)
    # simply stay unmatched, which the per-link stats surface honestly.
    # See app/services/mail/mail_center_service.py.
    try:
        from services.mail.mail_center_service import MailCenterService
        MailCenterService.match_invitation_on_registration(
            link_id=link.id, email=email, user_id=user.id,
        )
    except Exception:
        pass

    # Backwards-compat single id for the confirmation mail + response body
    # (first assessor scenario, or the legacy single target).
    _assessor_ids = link.get_assessor_scenario_ids()
    target_scenario_id = link.target_scenario_id or (_assessor_ids[0] if _assessor_ids else None)

    # Auto-enroll into the link's target scenario(s). Adds ScenarioUsers rows:
    # evaluation_role='assessor' for assessor scenarios and read-only
    # manager_role='viewer' for viewer scenarios (a scenario may be in both,
    # e.g. the IJCAI demo link). Logic lives in
    # ReferralService.enroll_user_in_link_scenarios so the authenticated redeem
    # flow shares the exact same enrollment shape — see that helper's docstring.
    if link.get_assessor_scenario_ids() or link.get_viewer_scenario_ids():
        try:
            ReferralService.enroll_user_in_link_scenarios(user, link)
        except Exception as e:
            import logging
            logging.getLogger('referral').warning(
                f"Auto-enroll into link {link.code} scenarios failed for {username}: {e}"
            )
            # Best-effort; user account exists either way.

    # Provision the demo content this link hands out (prompts cloned into the
    # new account, finished generation jobs shared read-only) — so a conference
    # visitor lands in a furnished account, not an empty one. Configured per
    # link via provision_json; a link without one is a no-op. The helper never
    # raises (see ReferralService.provision_demo_content), so no guard here: a
    # provisioning problem must never cost a visitor their account.
    ReferralService.provision_demo_content(user, link)

    # Auto-login: mint a fresh Authentik token so the freshly-registered
    # user lands directly in the scenario without a manual login screen.
    # The token is best-effort — if Authentik is briefly unreachable we
    # still return 201 so the account exists, and the frontend falls back
    # to the regular login redirect.
    auto_login_token = None
    try:
        from routes.authentik_routes import issue_authentik_token
        auto_login_token = issue_authentik_token(username, password)
    except Exception:
        auto_login_token = None

    # Best-effort confirmation email. Async-safe; never blocks the
    # registration response on SMTP latency or misconfiguration. The IJCAI demo
    # link gets a dedicated English welcome mail (product demo, international
    # audience); all other links get the German "Kann KI Beratung?" study mail.
    try:
        _slug = (link.slug or '').lower()
        if _slug == 'ijcai':
            from services.email_service import send_ijcai_welcome
            send_ijcai_welcome(
                username=username,
                email=email,
                referral_link_id=link.id,
                recipient_user_id=getattr(user, 'id', None),
            )
        elif _slug in ('demo-de', 'demo-en'):
            # General LLARS demo: language-specific welcome (account is de/en too).
            from services.email_service import send_demo_welcome
            send_demo_welcome(
                username=username,
                email=email,
                lang='en' if _slug == 'demo-en' else 'de',
                referral_link_id=link.id,
                recipient_user_id=getattr(user, 'id', None),
            )
        else:
            # Routed per link.welcome_template: custom > kkb > standard.
            # The standard mail is study-agnostic and auto-fills name/study —
            # the KKB study mail only goes out for links explicitly marked
            # 'kkb' (it used to be the global fallback: wrong-study welcomes).
            from services.email_service import send_link_welcome
            send_link_welcome(
                link=link,
                username=username,
                email=email,
                scenario_id=target_scenario_id,
                display_name=display_name or None,
                recipient_user_id=getattr(user, 'id', None),
            )
    except Exception:
        # Logged inside the service — never fail registration on email errors.
        pass

    response_body = {
        'success': True,
        'message': 'Registrierung erfolgreich',
        'username': username,
        'role': link.role_name,
        'target_scenario_id': target_scenario_id,
        # Where the frontend should land the user: single scenario -> straight
        # in; multiple -> the evaluation hub (/evaluation).
        'redirect_path': _post_enroll_redirect(user),
    }
    if auto_login_token:
        # Mirrors the /auth/login response shape: access_token, id_token,
        # expires_in, scope, token_type, llars_roles. Frontend Register.vue
        # consumes this directly and skips the explicit login step.
        response_body['auto_login'] = True
        response_body['token'] = auto_login_token

    return jsonify(response_body), 201


# ============================================================================
# Authenticated Endpoint - Redeem code as an existing user
# ============================================================================

@referral_bp.route('/redeem', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='referral')
def redeem_referral():
    """Let an ALREADY-registered, logged-in user join a study via a referral code.

    The public ``/register`` flow only enrolls people at signup time. This
    endpoint is the missing counterpart: an existing user (any role) pastes a
    referral code/slug — e.g. ``kann-ki-beratung-test`` — and is enrolled into
    the link's target scenario and attributed to the referral campaign exactly
    like a fresh referral signup, WITHOUT touching their account otherwise.

    Body: ``{ "code": "<code-or-slug>" }``.

    SECURITY / ROLE HANDLING — deliberate difference from /register:
    The public register endpoint assigns the link's role to a brand-new account.
    Here the caller is an established user, so we DO NOT call
    PermissionService.assign_role. Re-applying the link role would DOWNGRADE a
    researcher/admin who redeems an evaluator-scoped study code, silently
    stripping permissions. We only ever ADD scenario access + campaign
    attribution; the user's global role/permissions are left untouched.

    Idempotent: redeeming the same code twice succeeds with no duplicate
    enrollment (enrollment + attribution are both idempotent — see
    ReferralService.enroll_user_in_scenario / register_user).
    """
    data = request.get_json() or {}
    code = (data.get('code') or data.get('referral_code') or '').strip()
    if not code:
        raise ValidationError("Einladungscode ist erforderlich")

    # Reuse the exact same lookup + state checks as the register form so an
    # inactive / expired / paused / over-limit link is rejected identically.
    is_valid, link, error = ReferralService.validate_link(code)
    if not is_valid:
        # validate_link returns human-readable reasons; "Ungültiger
        # Einladungscode" is a genuine not-found, everything else is a state
        # problem (inactive/expired/limit) → surface as a 400 ValidationError.
        if error and 'Ungültig' in error:
            raise NotFoundError(error)
        raise ValidationError(error or "Ungültiger Einladungscode")

    user = g.authentik_user
    username = user.username

    # Resolve the user's email from Authentik. The local User model has NO
    # email column — the address lives only in Authentik — so we look it up by
    # username. Used both for mail-center invitation matching AND for the study
    # welcome mail on first enroll below. Best-effort: if Authentik is briefly
    # unreachable or the user has no address on file, we fall back to '' and
    # simply skip the email-dependent steps (matching + welcome mail).
    user_email = ''
    try:
        from services.authentik_admin_service import AuthentikAdminService
        ak_user = AuthentikAdminService.find_user(username)
        if ak_user:
            user_email = (ak_user.get('email') or '').strip()
    except Exception:
        user_email = ''

    # Enroll into the target scenario(s) (idempotent). Multi-scenario aware:
    # assessor + read-only viewer per the link's lists (IJCAI demo). enrolled is
    # True only when a NEW membership row was created this redeem; already_enrolled
    # stays True on a repeat redeem so the frontend can route the user straight to
    # the study instead of showing a misleading "newly joined" message.
    enroll_summary = ReferralService.enroll_user_in_link_scenarios(user, link)
    enrolled = enroll_summary['created'] > 0
    already_enrolled = (
        not enrolled
        and bool(link.get_assessor_scenario_ids() or link.get_viewer_scenario_ids())
    )

    # Same demo-content provisioning as /register (cloned prompts + shared
    # generation jobs), so an EXISTING account that redeems the demo code ends
    # up with exactly the material a fresh sign-up gets. Idempotent and
    # exception-safe by contract — see ReferralService.provision_demo_content.
    ReferralService.provision_demo_content(user, link)

    # Backwards-compat single id for the welcome mail + response routing. Multi-
    # scenario links set target_scenario_id=NULL, so fall back to the first
    # assessor scenario — otherwise the frontend can't route the user into a study.
    _assessor_ids = link.get_assessor_scenario_ids()
    target_scenario_id = link.target_scenario_id or (_assessor_ids[0] if _assessor_ids else None)

    # Attribute to the campaign. register_user is idempotent and re-attributes
    # an existing username rather than 500-ing on the UNIQUE constraint, so a
    # repeat redeem (or a user who originally signed up via a different link)
    # is handled cleanly. We pass the user's stored email when known so the
    # mail-center invitation matching below can find an open invite.
    ReferralService.register_user(
        link=link,
        username=username,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        metadata={'email': user_email, 'redeemed_by_existing_user': True},
    )

    # Mail-Center: if an open admin invitation for this link matches the user's
    # email, flip it to "accepted" — mirrors register_via_referral. Best-effort;
    # email-less users (or a non-matching address) simply stay unmatched.
    try:
        from services.mail.mail_center_service import MailCenterService
        MailCenterService.match_invitation_on_registration(
            link_id=link.id, email=user_email, user_id=user.id,
        )
    except Exception:
        pass

    # Study welcome mail — same branded mail fresh sign-ups get from
    # /register, so an existing user who joins via a code receives an identical
    # welcome (username already in subject + body). ONLY on a first NEW
    # enrollment: `enrolled` is True / `already_enrolled` False. A repeat redeem
    # (user already in the scenario) must NOT resend → no welcome spam.
    # Best-effort / fire-and-forget: a mail failure must never fail the redeem.
    # Email-less users are skipped (send_registration_confirmation no-ops for an
    # empty address, but we guard here too so we don't even queue a send).
    if enrolled and not already_enrolled and user_email:
        try:
            if (link.slug or '').lower() == 'ijcai':
                from services.email_service import send_ijcai_welcome
                send_ijcai_welcome(
                    username=username,
                    email=user_email,
                    referral_link_id=link.id,
                    recipient_user_id=getattr(user, 'id', None),
                )
            else:
                # Same per-link routing as /register (custom > kkb > standard).
                from services.email_service import send_link_welcome
                send_link_welcome(
                    link=link,
                    username=username,
                    email=user_email,
                    scenario_id=target_scenario_id,
                    display_name=getattr(user, 'display_name', None),
                    recipient_user_id=getattr(user, 'id', None),
                )
        except Exception:
            # Logged inside the service — never fail redeem on email errors.
            pass

    return jsonify({
        'success': True,
        'target_scenario_id': target_scenario_id,
        'redirect_path': _post_enroll_redirect(user),
        'role': link.role_name,
        # already_enrolled reflects scenario membership specifically; True means
        # "you were already in this study", which the frontend treats as success.
        'already_enrolled': already_enrolled and not enrolled,
    })


# ============================================================================
# Admin Endpoints - Campaign Management
# ============================================================================

@referral_bp.route('/admin/campaigns', methods=['GET'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def list_campaigns():
    """List all referral campaigns."""
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    campaigns = ReferralService.list_campaigns(include_archived=include_archived)

    return jsonify({
        'success': True,
        'campaigns': [c.to_dict() for c in campaigns]
    })


@referral_bp.route('/admin/campaigns/<int:campaign_id>', methods=['GET'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def get_campaign(campaign_id: int):
    """Get a specific campaign with its links."""
    campaign = ReferralService.get_campaign(campaign_id)
    if not campaign:
        raise NotFoundError(f"Kampagne {campaign_id} nicht gefunden")

    return jsonify({
        'success': True,
        'campaign': campaign.to_dict(include_links=True)
    })


@referral_bp.route('/admin/campaigns', methods=['POST'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def create_campaign():
    """Create a new referral campaign."""
    data = request.get_json() or {}

    name = (data.get('name') or '').strip()
    if not name:
        raise ValidationError("Kampagnenname ist erforderlich")

    # Parse dates
    start_date = None
    end_date = None
    if data.get('start_date'):
        try:
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError("Ungültiges Startdatum")
    if data.get('end_date'):
        try:
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError("Ungültiges Enddatum")

    campaign = ReferralService.create_campaign(
        name=name,
        created_by=g.authentik_user.username,
        description=data.get('description'),
        start_date=start_date,
        end_date=end_date,
        max_registrations=data.get('max_registrations'),
        config=data.get('config')
    )

    return jsonify({
        'success': True,
        'campaign': campaign.to_dict()
    }), 201


@referral_bp.route('/admin/campaigns/<int:campaign_id>', methods=['PUT'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def update_campaign(campaign_id: int):
    """Update a referral campaign."""
    data = request.get_json() or {}

    # Parse dates if provided
    start_date = None
    end_date = None
    if 'start_date' in data:
        if data['start_date']:
            try:
                start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError("Ungültiges Startdatum")
    if 'end_date' in data:
        if data['end_date']:
            try:
                end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError("Ungültiges Enddatum")

    campaign = ReferralService.update_campaign(
        campaign_id=campaign_id,
        name=data.get('name'),
        description=data.get('description'),
        start_date=start_date,
        end_date=end_date,
        max_registrations=data.get('max_registrations'),
        config=data.get('config')
    )

    if not campaign:
        raise NotFoundError(f"Kampagne {campaign_id} nicht gefunden")

    return jsonify({
        'success': True,
        'campaign': campaign.to_dict()
    })


@referral_bp.route('/admin/campaigns/<int:campaign_id>/status', methods=['PATCH'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def update_campaign_status(campaign_id: int):
    """Update campaign status."""
    data = request.get_json() or {}
    status_str = data.get('status')

    if not status_str:
        raise ValidationError("Status ist erforderlich")

    try:
        status = ReferralCampaignStatus(status_str)
    except ValueError:
        valid_statuses = [s.value for s in ReferralCampaignStatus]
        raise ValidationError(f"Ungültiger Status: {status_str}. Erlaubt: {valid_statuses}")

    success = ReferralService.update_campaign_status(campaign_id, status)
    if not success:
        raise NotFoundError(f"Kampagne {campaign_id} nicht gefunden")

    return jsonify({'success': True, 'status': status.value})


@referral_bp.route('/admin/campaigns/<int:campaign_id>', methods=['DELETE'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def delete_campaign(campaign_id: int):
    """Delete a campaign and all its links."""
    success = ReferralService.delete_campaign(campaign_id)
    if not success:
        raise NotFoundError(f"Kampagne {campaign_id} nicht gefunden")

    return jsonify({'success': True})


# ============================================================================
# Admin Endpoints - Link Management
# ============================================================================

@referral_bp.route('/admin/campaigns/<int:campaign_id>/links', methods=['GET'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def list_campaign_links(campaign_id: int):
    """List all links for a campaign."""
    campaign = ReferralService.get_campaign(campaign_id)
    if not campaign:
        raise NotFoundError(f"Kampagne {campaign_id} nicht gefunden")

    links = ReferralService.list_campaign_links(campaign_id)

    return jsonify({
        'success': True,
        'links': [link.to_dict(include_stats=True) for link in links]
    })


@referral_bp.route('/admin/campaigns/<int:campaign_id>/links', methods=['POST'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def create_link(campaign_id: int):
    """Create a new referral link for a campaign."""
    data = request.get_json() or {}

    # Parse expiry date if provided
    expires_at = None
    if data.get('expires_at'):
        try:
            expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError("Ungültiges Ablaufdatum")

    link = ReferralService.create_link(
        campaign_id=campaign_id,
        created_by=g.authentik_user.username,
        role_name=data.get('role_name'),
        slug=data.get('slug'),
        label=data.get('label'),
        max_uses=data.get('max_uses'),
        expires_at=expires_at,
        target_scenario_id=data.get('target_scenario_id'),
        collect_email=bool(data['collect_email']) if 'collect_email' in data else True,
        collect_display_name=bool(data['collect_display_name']) if 'collect_display_name' in data else True,
        collect_email_optional=bool(data.get('collect_email_optional', False)),
        color=data.get('color'),
        welcome_template=data.get('welcome_template') or 'standard',
        welcome_subject=data.get('welcome_subject'),
        welcome_body=data.get('welcome_body'),
        # Demo-content provisioning: {"clone_prompt_ids": [...],
        # "share_job_ids": [...]}. Validated in the service (400 on anything
        # else). SECURITY: these ids are admin-trusted config — this endpoint
        # is gated on admin:referral:manage, and setting clone_prompt_ids
        # deliberately exposes the source prompt's CONTENT to everyone who
        # registers through the link. That is the point for a demo link; never
        # accept this field on a self-service link path.
        provision_json=data.get('provision_json'),
    )

    return jsonify({
        'success': True,
        'link': link.to_dict(include_stats=True)
    }), 201


@referral_bp.route('/admin/links/<int:link_id>', methods=['GET'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def get_link(link_id: int):
    """Get a specific link with stats."""
    stats = ReferralService.get_link_stats(link_id)
    if not stats:
        raise NotFoundError(f"Link {link_id} nicht gefunden")

    return jsonify({
        'success': True,
        'link': stats
    })


@referral_bp.route('/admin/links/<int:link_id>', methods=['PUT'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def update_link(link_id: int):
    """Update a referral link."""
    data = request.get_json() or {}

    # Parse expiry date if provided
    expires_at = None
    if 'expires_at' in data:
        if data['expires_at']:
            try:
                expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError("Ungültiges Ablaufdatum")

    # Demo-content provisioning, same absent-vs-empty semantics as color:
    # key absent -> leave unchanged (None); present with null/{} -> clear;
    # present with a config -> validated in the service (400 on junk).
    # SECURITY: admin-trusted ids — see the create_link comment above; cloning a
    # prompt copies its content into every registrant's account.
    provision_json = None
    if 'provision_json' in data:
        provision_json = data['provision_json'] if data['provision_json'] is not None else {}

    link = ReferralService.update_link(
        link_id=link_id,
        role_name=data.get('role_name'),
        label=data.get('label'),
        is_active=data.get('is_active'),
        max_uses=data.get('max_uses'),
        expires_at=expires_at,
        target_scenario_id=data.get('target_scenario_id'),
        collect_email=data.get('collect_email'),
        collect_display_name=data.get('collect_display_name'),
        collect_email_optional=data.get('collect_email_optional'),
        # Key absent -> leave unchanged (None); present (incl. null/empty) ->
        # '' clears the override and reverts to the deterministic auto-color.
        color=(data.get('color') or '') if 'color' in data else None,
        # Welcome-mail routing (standard|kkb|custom) + custom template fields;
        # same absent-vs-empty semantics as color.
        welcome_template=data.get('welcome_template') if 'welcome_template' in data else None,
        welcome_subject=(data.get('welcome_subject') or '') if 'welcome_subject' in data else None,
        welcome_body=(data.get('welcome_body') or '') if 'welcome_body' in data else None,
        provision_json=provision_json,
    )

    if not link:
        raise NotFoundError(f"Link {link_id} nicht gefunden")

    return jsonify({
        'success': True,
        'link': link.to_dict(include_stats=True)
    })


@referral_bp.route('/admin/links/<int:link_id>', methods=['DELETE'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def delete_link(link_id: int):
    """Delete a referral link."""
    success = ReferralService.delete_link(link_id)
    if not success:
        raise NotFoundError(f"Link {link_id} nicht gefunden")

    return jsonify({'success': True})


@referral_bp.route('/admin/links/<int:link_id>/deactivate', methods=['POST'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def deactivate_link(link_id: int):
    """Deactivate a referral link."""
    success = ReferralService.deactivate_link(link_id)
    if not success:
        raise NotFoundError(f"Link {link_id} nicht gefunden")

    return jsonify({'success': True})


# ============================================================================
# Admin Endpoints - Analytics
# ============================================================================

@referral_bp.route('/admin/analytics/overview', methods=['GET'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def get_analytics_overview():
    """Get overall referral system analytics."""
    return jsonify({
        'success': True,
        'data': ReferralService.get_system_overview()
    })


@referral_bp.route('/admin/analytics/campaigns/<int:campaign_id>', methods=['GET'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def get_campaign_analytics(campaign_id: int):
    """Get analytics for a specific campaign."""
    stats = ReferralService.get_campaign_stats(campaign_id)
    if not stats:
        raise NotFoundError(f"Kampagne {campaign_id} nicht gefunden")

    return jsonify({
        'success': True,
        'data': stats
    })


@referral_bp.route('/admin/registrations', methods=['GET'])
@authentik_required
@require_permission('admin:referral:manage')
@handle_api_errors(logger_name='referral')
def list_registrations():
    """
    List all referral registrations.

    Query params:
        campaign_id: Filter by campaign (optional)
        link_id: Filter by link (optional)
        limit: Max results (default 50)
        offset: Offset for pagination
    """
    campaign_id = request.args.get('campaign_id', type=int)
    link_id = request.args.get('link_id', type=int)
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    registrations, total = ReferralService.list_registrations(
        campaign_id=campaign_id,
        link_id=link_id,
        limit=min(limit, 100),  # Max 100 per request
        offset=offset
    )

    return jsonify({
        'success': True,
        'registrations': registrations,
        'total': total,
        'limit': limit,
        'offset': offset
    })
