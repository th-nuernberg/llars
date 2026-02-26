"""Unit tests for user referral route helpers."""

from db.models.referral import ReferralCampaign, ReferralCampaignStatus, ReferralLink
from routes.user_settings.user_referral_routes import _get_user_campaign


def test_REFERRAL_USER_CAMPAIGN_001_consolidates_duplicate_personal_campaigns(app, db, app_context, mock_user):
    """Duplicate personal campaigns should be merged so links stay visible."""
    # Ensure referral tables exist in the test schema.
    db.create_all()

    c1 = ReferralCampaign(
        name=f"Einladungen von {mock_user.username}",
        description="Primary campaign",
        status=ReferralCampaignStatus.ACTIVE.value,
        created_by=mock_user.username,
        config_json={"type": "user_personal", "owner_user_id": mock_user.id},
    )
    c2 = ReferralCampaign(
        name=f"Einladungen von {mock_user.username} (duplicate 1)",
        description="Duplicate campaign",
        status=ReferralCampaignStatus.ACTIVE.value,
        created_by=mock_user.username,
        config_json={"type": "user_personal", "owner_user_id": mock_user.id},
    )
    c3 = ReferralCampaign(
        name=f"Einladungen von {mock_user.username} (duplicate 2)",
        description="Duplicate campaign",
        status=ReferralCampaignStatus.ACTIVE.value,
        created_by=mock_user.username,
        config_json={"type": "user_personal", "owner_user_id": mock_user.id},
    )
    db.session.add_all([c1, c2, c3])
    db.session.commit()

    db.session.add_all([
        ReferralLink(campaign_id=c2.id, role_name="evaluator", created_by=mock_user.username),
        ReferralLink(campaign_id=c3.id, role_name="evaluator", created_by=mock_user.username),
    ])
    db.session.commit()

    campaign_id = _get_user_campaign(mock_user)
    assert campaign_id == c1.id

    remaining_campaigns = ReferralCampaign.query.filter_by(created_by=mock_user.username).all()
    assert len(remaining_campaigns) == 1
    assert remaining_campaigns[0].id == c1.id

    links = ReferralLink.query.order_by(ReferralLink.id.asc()).all()
    assert len(links) == 2
    assert all(link.campaign_id == c1.id for link in links)


def test_REFERRAL_USER_CAMPAIGN_002_backfills_owner_user_id_for_legacy_campaign(app, db, app_context, mock_user):
    """Legacy personal campaigns without owner_user_id should be normalized."""
    # Ensure referral tables exist in the test schema.
    db.create_all()

    legacy_campaign = ReferralCampaign(
        name=f"Einladungen von {mock_user.username}",
        description="Legacy campaign without owner",
        status=ReferralCampaignStatus.ACTIVE.value,
        created_by=mock_user.username,
        config_json={"type": "user_personal"},
    )
    db.session.add(legacy_campaign)
    db.session.commit()

    campaign_id = _get_user_campaign(mock_user)
    assert campaign_id == legacy_campaign.id

    db.session.refresh(legacy_campaign)
    assert isinstance(legacy_campaign.config_json, dict)
    assert legacy_campaign.config_json.get("type") == "user_personal"
    assert legacy_campaign.config_json.get("owner_user_id") == mock_user.id
