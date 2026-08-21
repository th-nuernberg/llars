"""
User Demographics Routes.

One-time demographic survey shown on first login (especially for users
arriving via referral links). Once submitted, the survey is never shown
again — `GET` returns `completed: true` and the frontend suppresses the
overlay.

Allowed values are validated server-side against fixed vocabularies so the
frontend can't smuggle arbitrary values into the analytics dataset.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request, g

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, ValidationError
from db.database import db
from db.models.user_demographics import UserDemographics

demographics_bp = Blueprint('demographics', __name__, url_prefix='/demographics')


# Controlled vocabularies. Keep in sync with
# llars-frontend/src/components/Onboarding/DemographicSurveyDialog.vue
_ALLOWED_GENDERS = {'female', 'male', 'non_binary', 'no_answer'}
_ALLOWED_AGE_RANGES = {'under_29', '30_49', '50_64', '65_plus', 'no_answer'}
_ALLOWED_EDUCATION = {
    'phd', 'master', 'bachelor', 'vocational',
    'abitur', 'realschule', 'no_formal', 'no_answer',
}
_PROFESSION_MAX_LEN = 255


def _validate_choice(value, allowed, field_name):
    """Return value if valid (or None), else raise ValidationError."""
    if value in (None, ''):
        return None
    if value not in allowed:
        raise ValidationError(f"Invalid value for '{field_name}': {value}")
    return value


def _resolve_user_email(username):
    """Best-effort lookup of the user's stored email for read-only display.

    The local User model has NO email column — the address lives in Authentik
    (source of truth), with a fallback to the referral-registration metadata
    for invite signups. Synthetic placeholders (``…@noemail.invalid``, set when
    a referral user gave no address) are treated as "no email on file" → None.
    """
    email = ''
    try:
        from services.authentik_admin_service import AuthentikAdminService
        ak_user = AuthentikAdminService.find_user(username)
        if ak_user:
            email = (ak_user.get('email') or '').strip()
    except Exception:
        email = ''
    if not email:
        try:
            from db.models.referral import ReferralRegistration
            reg = ReferralRegistration.query.filter_by(username=username).first()
            if reg and reg.metadata_json:
                email = (reg.metadata_json.get('email') or '').strip()
        except Exception:
            email = ''
    if email.endswith('@noemail.invalid'):
        email = ''
    return email or None


def _get_email_consent(username):
    """Read the email-contact consent flag from the user's referral registration
    (ReferralRegistration.metadata_json['email_contact_consent']). None when no
    referral registration exists (nothing to carry the flag)."""
    try:
        from db.models.referral import ReferralRegistration
        reg = ReferralRegistration.query.filter_by(username=username).first()
        if reg and reg.metadata_json:
            return bool(reg.metadata_json.get('email_contact_consent'))
    except Exception:
        pass
    return None


@demographics_bp.route('', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='user_demographics')
def get_demographics():
    """Return the current user's survey state.

    Response includes `should_show_survey`: True when the user has not yet
    completed the survey AND is part of a referral registration (i.e. came
    in via an invite link). Other users — admins, manually-created
    accounts — never see the overlay even if no record exists, to avoid
    spamming legacy users.
    """
    from db.models.referral import ReferralRegistration

    user = g.authentik_user
    record = UserDemographics.query.filter_by(user_id=user.id).first()
    completed = record is not None and record.completed_at is not None

    referral_reg = None
    if not completed:
        referral_reg = ReferralRegistration.query.filter_by(
            username=user.username
        ).first()

    should_show = (not completed) and referral_reg is not None
    referral_link_id = referral_reg.link_id if referral_reg else None

    return jsonify({
        'success': True,
        'completed': completed,
        'should_show_survey': should_show,
        'referral_link_id': referral_link_id,
        'demographics': record.to_dict() if record else None,
        # Read-only: the stored contact email (Authentik / referral metadata),
        # surfaced so users can review what address we have on file. None when
        # no real address is stored (anonymous / synthetic placeholder).
        'email': _resolve_user_email(user.username),
        # Whether the user consented to storing their email for future-study
        # contact (set at registration). Surfaced so the settings page can show
        # + REVOKE it (the consent text promises "jederzeit widerrufbar").
        # None when there's no referral registration to carry the flag.
        'email_contact_consent': _get_email_consent(user.username),
    })


@demographics_bp.route('', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='user_demographics')
def submit_demographics():
    """Save (or replace) the current user's demographic survey.

    Idempotent: re-submitting overwrites the previous answers but keeps
    the original `completed_at` so we don't reset the "already filled"
    signal that suppresses the overlay.
    """
    user = g.authentik_user
    data = request.get_json(silent=True) or {}

    gender = _validate_choice(data.get('gender'), _ALLOWED_GENDERS, 'gender')
    age_range = _validate_choice(data.get('age_range'), _ALLOWED_AGE_RANGES, 'age_range')
    education = _validate_choice(data.get('education'), _ALLOWED_EDUCATION, 'education')

    profession = data.get('profession')
    if profession is not None:
        profession = str(profession).strip() or None
        if profession and len(profession) > _PROFESSION_MAX_LEN:
            raise ValidationError(
                f"Profession too long (max {_PROFESSION_MAX_LEN} chars)"
            )

    referral_link_id = data.get('referral_link_id')
    if referral_link_id is not None:
        try:
            referral_link_id = int(referral_link_id)
        except (TypeError, ValueError):
            referral_link_id = None

    record = UserDemographics.query.filter_by(user_id=user.id).first()
    if record is None:
        record = UserDemographics(user_id=user.id)
        db.session.add(record)

    record.gender = gender
    record.age_range = age_range
    record.education = education
    record.profession = profession
    if referral_link_id is not None:
        record.referral_link_id = referral_link_id

    # Only set completed_at the first time so we don't lose the original
    # submission timestamp on later edits (e.g. via a settings page).
    if record.completed_at is None:
        record.completed_at = datetime.now()

    db.session.commit()

    return jsonify({
        'success': True,
        'completed': True,
        'demographics': record.to_dict(),
    })


@demographics_bp.route('/email-consent', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='user_demographics')
def update_email_consent():
    """Grant or REVOKE the email-contact consent ("jederzeit widerrufbar").

    Persists ``email_contact_consent`` in the user's referral-registration
    metadata. Body: ``{consent: bool}``. Returns the new value. 404-free no-op
    semantics: if the user has no referral registration there's nothing to carry
    the flag, so we report it as not-applicable rather than erroring.
    """
    from db.models.referral import ReferralRegistration

    user = g.authentik_user
    data = request.get_json(silent=True) or {}
    consent = bool(data.get('consent'))

    reg = ReferralRegistration.query.filter_by(username=user.username).first()
    if reg is None:
        return jsonify({'success': True, 'email_contact_consent': None,
                        'applicable': False})

    meta = dict(reg.metadata_json or {})
    meta['email_contact_consent'] = consent
    reg.metadata_json = meta
    # SQLAlchemy JSON columns need explicit reassignment to flag as dirty.
    db.session.commit()

    return jsonify({'success': True, 'email_contact_consent': consent,
                    'applicable': True})
