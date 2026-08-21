"""
Dev-mode seeder for the referral / self-registration system.

Enables `referral_system_enabled` + `self_registration_enabled` and creates
a default campaign with a `vhb-test` link so developers can test the
referral signup flow at /join/vhb-test out of the box.

Idempotent: safe to run on every startup. Only flips the flags from their
factory defaults; if an admin has explicitly disabled self-registration
in dev, this will re-enable it (intended — dev convenience).
"""

import logging

logger = logging.getLogger(__name__)


def seed_dev_referral_defaults(db) -> None:
    """Enable self-registration and ensure the vhb-test referral link exists."""
    from db.models.system_settings import SystemSettings
    from db.models.referral import (
        ReferralCampaign,
        ReferralCampaignStatus,
        ReferralLink,
    )

    try:
        # 1. Make sure the SystemSettings row exists, enable both flags.
        settings = SystemSettings.query.get(1)
        if settings is None:
            settings = SystemSettings(id=1)
            db.session.add(settings)

        changed = False
        if not settings.referral_system_enabled:
            settings.referral_system_enabled = True
            changed = True
        if not settings.self_registration_enabled:
            settings.self_registration_enabled = True
            changed = True

        # 2. Ensure a default dev campaign exists.
        campaign = (
            ReferralCampaign.query.filter_by(name="Dev Test Campaign").first()
        )
        if campaign is None:
            campaign = ReferralCampaign(
                name="Dev Test Campaign",
                description="Auto-seeded campaign for local development.",
                status=ReferralCampaignStatus.ACTIVE.value,
                created_by="system",
            )
            db.session.add(campaign)
            db.session.flush()  # need campaign.id for the link
            changed = True
        elif campaign.status != ReferralCampaignStatus.ACTIVE.value:
            campaign.status = ReferralCampaignStatus.ACTIVE.value
            changed = True

        # 3. Ensure the /join/vhb-test link exists and is active.
        link = ReferralLink.query.filter_by(slug="vhb-test").first()
        if link is None:
            link = ReferralLink(
                campaign_id=campaign.id,
                slug="vhb-test",
                role_name="evaluator",
                label="vhb Test Link (dev)",
                is_active=True,
                created_by="system",
            )
            db.session.add(link)
            changed = True
        elif not link.is_active or link.campaign_id != campaign.id:
            link.is_active = True
            link.campaign_id = campaign.id
            changed = True

        # 4. Ensure the EMNLP Turing-Test link exists when a matching
        #    scenario is in the DB. The link auto-enrolls registrants as
        #    ASSESSOR on the named scenario so /join/human_comparison_emnlp
        #    drops them straight into the comparison flow.
        from db.models.scenario import RatingScenarios
        emnlp_scenario = (
            RatingScenarios.query
            .filter(
                RatingScenarios.function_type_id == 4,
                RatingScenarios.scenario_name.ilike('EMNLP%')
            )
            .order_by(RatingScenarios.id.desc())
            .first()
        )
        emnlp_link = ReferralLink.query.filter_by(slug="human_comparison_emnlp").first()
        if emnlp_scenario is not None:
            if emnlp_link is None:
                emnlp_link = ReferralLink(
                    campaign_id=campaign.id,
                    slug="human_comparison_emnlp",
                    role_name="evaluator",
                    label="EMNLP Counsellor-Pairs Pilot",
                    description=(
                        "Public pilot link for the EMNLP 2026 Turing-Test "
                        "study. Registrants are auto-enrolled as assessors "
                        "on the EMNLP comparison scenario."
                    ),
                    is_active=True,
                    target_scenario_id=emnlp_scenario.id,
                    created_by="system",
                )
                db.session.add(emnlp_link)
                changed = True
            else:
                # Keep target + active state in sync if the scenario id moved
                # (re-imports create new ids).
                if emnlp_link.target_scenario_id != emnlp_scenario.id:
                    emnlp_link.target_scenario_id = emnlp_scenario.id
                    changed = True
                if not emnlp_link.is_active or emnlp_link.campaign_id != campaign.id:
                    emnlp_link.is_active = True
                    emnlp_link.campaign_id = campaign.id
                    changed = True

        if changed:
            db.session.commit()
            extra = (
                f", link=/join/human_comparison_emnlp -> scenario {emnlp_scenario.id}"
                if emnlp_scenario is not None else ""
            )
            logger.info(
                "Dev referral defaults seeded: self_registration_enabled=True, "
                "link=/join/vhb-test" + extra
            )
    except Exception as exc:  # pragma: no cover - defensive
        db.session.rollback()
        logger.warning("Dev referral seeding skipped: %s", exc)
