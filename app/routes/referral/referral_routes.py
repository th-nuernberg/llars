"""
Referral System API Routes.

Provides endpoints for:
- Public link validation and registration
- Admin campaign management
- Admin link management
- Analytics
"""

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

    return jsonify({
        'success': True,
        'valid': True,
        'campaign_name': link.campaign.name,
        'role': link.role_name,
        'label': link.label
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

    # Validate required fields
    if not code:
        raise ValidationError("Einladungscode ist erforderlich")
    if not username:
        raise ValidationError("Benutzername ist erforderlich")
    if not email:
        raise ValidationError("E-Mail ist erforderlich")
    if not password or len(password) < 8:
        raise ValidationError("Passwort muss mindestens 8 Zeichen haben")

    # Validate username format
    if len(username) < 3:
        raise ValidationError("Benutzername muss mindestens 3 Zeichen haben")
    if not username.replace('_', '').replace('-', '').isalnum():
        raise ValidationError("Benutzername darf nur Buchstaben, Zahlen, _ und - enthalten")

    # Validate email format
    if '@' not in email or '.' not in email:
        raise ValidationError("Ungültige E-Mail-Adresse")

    # Validate referral link
    is_valid, link, error = ReferralService.validate_link(code)
    if not is_valid:
        raise ValidationError(error)

    # Create user in Authentik
    from services.authentik_admin_service import AuthentikAdminService

    success, error_msg, authentik_data = AuthentikAdminService.create_user(
        username=username,
        email=email,
        password=password,
        name=display_name or username,
        is_active=True
    )

    if not success:
        if "already exists" in (error_msg or "").lower():
            raise ConflictError(f"Benutzer '{username}' existiert bereits")
        raise ValidationError(f"Fehler beim Erstellen des Benutzers: {error_msg}")

    # Create LLARS user record
    from auth.decorators import get_or_create_user
    user = get_or_create_user(username)

    # Assign role from referral link
    from services.permission_service import PermissionService
    try:
        PermissionService.assign_role(
            username=username,
            role_name=link.role_name,
            admin_username='referral_system'
        )
    except Exception as e:
        # Log but don't fail - user is created, role assignment is best-effort
        import logging
        logging.getLogger('referral').warning(
            f"Failed to assign role {link.role_name} to {username}: {e}"
        )

    # Record registration for tracking
    ReferralService.register_user(
        link=link,
        username=username,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        metadata={'email': email, 'display_name': display_name}
    )

    return jsonify({
        'success': True,
        'message': 'Registrierung erfolgreich',
        'username': username,
        'role': link.role_name
    }), 201


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
        expires_at=expires_at
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

    link = ReferralService.update_link(
        link_id=link_id,
        role_name=data.get('role_name'),
        label=data.get('label'),
        is_active=data.get('is_active'),
        max_uses=data.get('max_uses'),
        expires_at=expires_at
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
