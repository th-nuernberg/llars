"""
Referral and Invitation System database models.

Provides models for:
- ReferralCampaign: Groups of invite links (e.g., "KI-Konferenz 2026")
- ReferralLink: Individual invite codes with custom slugs
- ReferralRegistration: Tracks user registrations via referral
"""

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

    # Active/inactive status
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

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

    def to_dict(self, include_stats: bool = False) -> dict:
        """Convert to dictionary for API responses."""
        result = {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'code': self.code,
            'slug': self.slug,
            'role_name': self.role_name,
            'label': self.label,
            'description': self.description,
            'is_active': self.is_active,
            'max_uses': self.max_uses,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'owner_user_id': self.owner_user_id,
            'owner_username': self.owner.username if self.owner else None,
            'url': f"/join/{self.slug or self.code}"
        }
        if include_stats:
            registration_count = self.registrations.count() if self.registrations else 0
            result['registrations'] = registration_count
            result['remaining_uses'] = self.max_uses - registration_count if self.max_uses else None
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
