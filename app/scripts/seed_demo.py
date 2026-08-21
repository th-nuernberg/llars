"""
LLARS general demo seeder (de + en).

Builds one demo scenario per evaluation type (7) in BOTH German and English
(14 total), owned by the system account ``llars_demo``, plus two referral links:

    /join/demo-de  → German scenarios, German account/UI  (default_locale=de)
    /join/demo-en  → English scenarios, English account/UI (default_locale=en)

Reuses the IJCAI demo datasets + config builders (``scripts.seed_ijcai_demo``)
and just swaps the visible content language via ``_map_items(..., lang)``. On
signup the visitor is enrolled as ASSESSOR + VIEWER in the 7 scenarios of their
language (handled by the existing referral signup flow); a daily cleanup
(``scripts.demo_cleanup``) archives demo memberships older than 7 days, so each
demo account's scenarios stay available for one week.

Idempotent: re-running matches scenarios by name + creator and refreshes config
without recreating them — safe to run after every deploy.

Usage:
    docker exec llars_flask_<color> python -m scripts.seed_demo
    docker exec llars_flask_<color> python -m scripts.seed_demo --reset
"""

import json
import logging
import os
from datetime import datetime, timedelta

from scripts.seed_ijcai_demo import TYPES, _map_items, _load_dataset, _inject_task

logger = logging.getLogger(__name__)

OWNER_USERNAME = "llars_demo"
CAMPAIGN_NAME = "LLARS Demo"
# (lang, link slug, scenario-name suffix)
LANGS = (("de", "demo-de", "DE"), ("en", "demo-en", "EN"))


def _ensure_owner(db):
    from db.models import User
    user = User.query.filter_by(username=OWNER_USERNAME).first()
    if user:
        return user
    user = User(username=OWNER_USERNAME, group_id=1)
    if hasattr(user, "password_hash"):
        import secrets
        user.password_hash = secrets.token_urlsafe(24)
    db.session.add(user)
    db.session.flush()
    logger.info("Created owner user %s", OWNER_USERNAME)
    return user


def _seed_lang(db, lang, suffix, reset):
    """Seed the 7 demo scenarios for one language; returns their ids (in order)."""
    from db.models import RatingScenarios
    from schemas.api_v1.scenario_api import ScenarioCreateRequest
    from services.api_v1_scenario_service import create_scenario_one_shot, _build_config_json

    begin = datetime.utcnow()
    end = begin + timedelta(weeks=4)
    ids = []
    for eval_type, name, cfg_builder in TYPES:
        display_name = f"LLARS Demo · {name[lang]} ({suffix})"
        items = _map_items(eval_type, _load_dataset(eval_type), lang)
        payload = ScenarioCreateRequest(
            name=display_name,
            description=f"LLARS Demo ({suffix}) — {name[lang]}",
            eval_config=cfg_builder(),
            items={"items": items},
            assessors=[],  # visitors join via the referral link, not pre-assigned
            begin=begin,
            end=end,
        )
        existing = (RatingScenarios.query
                    .filter_by(scenario_name=display_name, created_by=OWNER_USERNAME)
                    .first())
        if existing and reset:
            db.session.delete(existing)
            db.session.commit()
            existing = None
        if existing:
            cj = _build_config_json(payload)
            _inject_task(cj, eval_type)
            existing.config_json = cj
            db.session.add(existing)
            db.session.commit()
            ids.append(existing.id)
            continue
        scenario = create_scenario_one_shot(payload, OWNER_USERNAME)
        cj = dict(scenario.config_json or {})
        _inject_task(cj, eval_type)
        scenario.config_json = cj
        db.session.add(scenario)
        db.session.commit()
        ids.append(scenario.id)
        logger.info("Created demo scenario '%s' (id=%s, %d items)", display_name, scenario.id, len(items))
    return ids


def _ensure_link(db, campaign_id, slug, lang, ids):
    from db.models.referral import ReferralLink
    link = ReferralLink.query.filter_by(slug=slug).first()
    if not link:
        link = ReferralLink(campaign_id=campaign_id, slug=slug, created_by=OWNER_USERNAME)
        db.session.add(link)
    link.campaign_id = campaign_id
    link.role_name = "evaluator"
    link.label = f"LLARS Demo ({lang.upper()})"
    link.is_active = True
    link.target_scenario_ids = ids
    link.viewer_scenario_ids = ids
    link.signup_mode = "email"
    link.default_locale = lang   # account + UI language for visitors of this link
    link.collect_email = True
    link.collect_email_optional = False
    link.collect_display_name = True
    db.session.commit()
    return link


def seed_demo(reset: bool = False) -> dict:
    from db import db
    from db.models import ReferralCampaign

    _ensure_owner(db)
    db.session.commit()

    campaign = ReferralCampaign.query.filter_by(name=CAMPAIGN_NAME).first()
    if not campaign:
        campaign = ReferralCampaign(name=CAMPAIGN_NAME, status="active", created_by=OWNER_USERNAME)
        db.session.add(campaign)
        db.session.flush()

    result = {}
    for lang, slug, suffix in LANGS:
        ids = _seed_lang(db, lang, suffix, reset)
        link = _ensure_link(db, campaign.id, slug, lang, ids)
        result[lang] = {"scenario_ids": ids, "join_url": f"/join/{link.slug or link.code}"}
    logger.info("LLARS demo seeded: %s", result)
    return result


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from main import app  # noqa: E402  (module-level app, no factory)
    logging.basicConfig(level=logging.INFO)
    with app.app_context():
        res = seed_demo(reset="--reset" in sys.argv)
        print("\nResult:", json.dumps(res, indent=2, ensure_ascii=False))
