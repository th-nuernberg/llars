"""
Referral Service.

Handles all referral/invitation business logic including:
- Campaign CRUD operations
- Link generation and validation
- Registration tracking
- Analytics and statistics
"""

import logging
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
        expires_at: Optional[datetime] = None
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

        # Use default role if not specified
        if role_name is None:
            role_name = ReferralService.get_default_role()

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
            created_by=created_by
        )
        db.session.add(link)
        db.session.commit()
        logger.info(f"Created referral link {link.code} (slug={slug}) for campaign {campaign_id}")
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
        expires_at: Optional[datetime] = None
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

        Returns:
            Updated link or None if not found
        """
        link = ReferralLink.query.get(link_id)
        if not link:
            return None

        if role_name is not None:
            link.role_name = role_name
        if label is not None:
            link.label = label
        if is_active is not None:
            link.is_active = is_active
        if max_uses is not None:
            link.max_uses = max_uses
        if expires_at is not None:
            link.expires_at = expires_at

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
        registration = ReferralRegistration(
            link_id=link.id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent[:512] if user_agent else None,
            metadata_json=metadata
        )
        db.session.add(registration)
        db.session.commit()
        logger.info(f"Recorded referral registration for {username} via link {link.code}")
        return registration

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

        # Top performing links
        top_links = db.session.execute(
            select(
                ReferralLink.id,
                ReferralLink.code,
                ReferralLink.slug,
                ReferralLink.label,
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
                    'registrations': row.registrations
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

        return {
            'link_id': link_id,
            'code': link.code,
            'slug': link.slug,
            'label': link.label,
            'role_name': link.role_name,
            'is_active': link.is_active,
            'registrations': registrations,
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
