"""
User Referral Routes.

Allows users with appropriate permissions to create and manage
their own referral/invitation links.
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime

from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, ValidationError, NotFoundError
)
from services.referral_service import ReferralService
from db.models.referral import ReferralLink, ReferralCampaignStatus

user_referral_bp = Blueprint('referrals', __name__, url_prefix='/referrals')


# Permission required for users to create their own referral links
REFERRAL_CREATE_PERMISSION = 'feature:referral:create_links'


def _get_user_campaign(user) -> int:
    """
    Get or create the user's personal referral campaign.

    Each user who can create links gets their own campaign.
    """
    from db.database import db
    from db.models.referral import ReferralCampaign

    # Look for existing user campaign
    campaign = ReferralCampaign.query.filter_by(
        created_by=user.username,
        config_json={'type': 'user_personal'}
    ).first()

    if not campaign:
        # Create user's personal campaign
        campaign = ReferralCampaign(
            name=f"Einladungen von {user.username}",
            description=f"Persönliche Einladungslinks von {user.username}",
            status=ReferralCampaignStatus.ACTIVE.value,
            created_by=user.username,
            config_json={'type': 'user_personal', 'owner_user_id': user.id}
        )
        db.session.add(campaign)
        db.session.commit()

    return campaign.id


@user_referral_bp.route('/can-create', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='user_referrals')
def check_can_create():
    """Check if the current user can create referral links."""
    from services.permission_service import PermissionService

    user = g.authentik_user
    can_create = PermissionService.check_permission(
        user.username, REFERRAL_CREATE_PERMISSION
    )

    # Also check if referral system is enabled
    referral_enabled = ReferralService.is_referral_enabled()

    return jsonify({
        'success': True,
        'can_create': can_create and referral_enabled,
        'referral_enabled': referral_enabled
    })


@user_referral_bp.route('', methods=['GET'])
@authentik_required
@require_permission(REFERRAL_CREATE_PERMISSION)
@handle_api_errors(logger_name='user_referrals')
def list_user_links():
    """List current user's referral links."""
    user = g.authentik_user

    # Get user's campaign
    campaign_id = _get_user_campaign(user)

    links = ReferralService.list_campaign_links(campaign_id)

    return jsonify({
        'success': True,
        'links': [link.to_dict(include_stats=True) for link in links]
    })


@user_referral_bp.route('', methods=['POST'])
@authentik_required
@require_permission(REFERRAL_CREATE_PERMISSION)
@handle_api_errors(logger_name='user_referrals')
def create_link():
    """Create a new referral link."""
    user = g.authentik_user
    data = request.get_json() or {}

    # Get user's campaign
    campaign_id = _get_user_campaign(user)

    # Validate optional fields
    slug = (data.get('slug') or '').strip().lower().replace(' ', '-')
    if slug and len(slug) < 3:
        raise ValidationError("Slug muss mindestens 3 Zeichen haben")

    # Parse expires_at if provided
    expires_at = None
    if data.get('expires_at'):
        try:
            expires_at = datetime.fromisoformat(
                data['expires_at'].replace('Z', '+00:00')
            )
        except ValueError:
            raise ValidationError("Ungültiges Ablaufdatum")

    # Users can only create links with 'evaluator' role (for security)
    # Admins can override this via the admin referral interface
    role_name = 'evaluator'

    link = ReferralService.create_link(
        campaign_id=campaign_id,
        created_by=user.username,
        role_name=role_name,
        slug=slug if slug else None,
        label=data.get('label'),
        max_uses=data.get('max_uses'),
        expires_at=expires_at
    )

    # Store owner user id on the link for tracking
    from db.database import db
    link.owner_user_id = user.id
    link.description = data.get('description')
    db.session.commit()

    return jsonify({
        'success': True,
        'link': link.to_dict(include_stats=True)
    }), 201


@user_referral_bp.route('/<int:link_id>', methods=['GET'])
@authentik_required
@require_permission(REFERRAL_CREATE_PERMISSION)
@handle_api_errors(logger_name='user_referrals')
def get_link(link_id: int):
    """Get a specific link with stats."""
    user = g.authentik_user

    link = ReferralService.get_link(link_id)
    if not link:
        raise NotFoundError("Link nicht gefunden")

    # Check ownership
    campaign_id = _get_user_campaign(user)
    if link.campaign_id != campaign_id:
        raise NotFoundError("Link nicht gefunden")

    stats = ReferralService.get_link_stats(link_id)

    return jsonify({
        'success': True,
        'link': stats
    })


@user_referral_bp.route('/<int:link_id>', methods=['PUT'])
@authentik_required
@require_permission(REFERRAL_CREATE_PERMISSION)
@handle_api_errors(logger_name='user_referrals')
def update_link(link_id: int):
    """Update a referral link."""
    user = g.authentik_user
    data = request.get_json() or {}

    link = ReferralService.get_link(link_id)
    if not link:
        raise NotFoundError("Link nicht gefunden")

    # Check ownership
    campaign_id = _get_user_campaign(user)
    if link.campaign_id != campaign_id:
        raise NotFoundError("Link nicht gefunden")

    # Parse expires_at if provided
    expires_at = None
    if 'expires_at' in data:
        if data['expires_at']:
            try:
                expires_at = datetime.fromisoformat(
                    data['expires_at'].replace('Z', '+00:00')
                )
            except ValueError:
                raise ValidationError("Ungültiges Ablaufdatum")

    # Users cannot change the role_name (security)
    updated = ReferralService.update_link(
        link_id=link_id,
        label=data.get('label'),
        is_active=data.get('is_active'),
        max_uses=data.get('max_uses'),
        expires_at=expires_at
    )

    if not updated:
        raise NotFoundError("Link nicht gefunden")

    # Update description if provided
    if 'description' in data:
        from db.database import db
        updated.description = data['description']
        db.session.commit()

    return jsonify({
        'success': True,
        'link': updated.to_dict(include_stats=True)
    })


@user_referral_bp.route('/<int:link_id>', methods=['DELETE'])
@authentik_required
@require_permission(REFERRAL_CREATE_PERMISSION)
@handle_api_errors(logger_name='user_referrals')
def delete_link(link_id: int):
    """Delete a referral link."""
    user = g.authentik_user

    link = ReferralService.get_link(link_id)
    if not link:
        raise NotFoundError("Link nicht gefunden")

    # Check ownership
    campaign_id = _get_user_campaign(user)
    if link.campaign_id != campaign_id:
        raise NotFoundError("Link nicht gefunden")

    success = ReferralService.delete_link(link_id)
    if not success:
        raise NotFoundError("Link nicht gefunden")

    return jsonify({'success': True})


@user_referral_bp.route('/<int:link_id>/deactivate', methods=['POST'])
@authentik_required
@require_permission(REFERRAL_CREATE_PERMISSION)
@handle_api_errors(logger_name='user_referrals')
def deactivate_link(link_id: int):
    """Deactivate a referral link."""
    user = g.authentik_user

    link = ReferralService.get_link(link_id)
    if not link:
        raise NotFoundError("Link nicht gefunden")

    # Check ownership
    campaign_id = _get_user_campaign(user)
    if link.campaign_id != campaign_id:
        raise NotFoundError("Link nicht gefunden")

    success = ReferralService.deactivate_link(link_id)
    if not success:
        raise NotFoundError("Link nicht gefunden")

    return jsonify({'success': True})


@user_referral_bp.route('/stats', methods=['GET'])
@authentik_required
@require_permission(REFERRAL_CREATE_PERMISSION)
@handle_api_errors(logger_name='user_referrals')
def get_user_stats():
    """Get statistics for current user's referral links."""
    user = g.authentik_user

    # Get user's campaign
    campaign_id = _get_user_campaign(user)
    stats = ReferralService.get_campaign_stats(campaign_id)

    return jsonify({
        'success': True,
        'stats': stats
    })


@user_referral_bp.route('/registrations', methods=['GET'])
@authentik_required
@require_permission(REFERRAL_CREATE_PERMISSION)
@handle_api_errors(logger_name='user_referrals')
def list_registrations():
    """List registrations from user's referral links."""
    user = g.authentik_user

    # Get user's campaign
    campaign_id = _get_user_campaign(user)

    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    registrations, total = ReferralService.list_registrations(
        campaign_id=campaign_id,
        limit=min(limit, 50),
        offset=offset
    )

    return jsonify({
        'success': True,
        'registrations': registrations,
        'total': total,
        'limit': limit,
        'offset': offset
    })
