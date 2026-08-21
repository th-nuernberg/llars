"""
Deep scenario deletion — shared by the Scenario-Manager DELETE route and the
IJCAI demo seeder's ``--reset`` path.

Why this exists: ``db.session.delete(scenario)`` alone is NOT safe. Three
per-item evaluation relationships on ``RatingScenarios`` (``dimension_ratings``,
``labeling_evaluations``, ``comparison_item_evaluations``) carry no ORM cascade,
so SQLAlchemy tries to NULL their ``scenario_id`` on delete and MariaDB rejects
it (column is NOT NULL) — exactly the IntegrityError that broke the first
``--reset`` run on production (2026-08-16). On top of that, a naive delete
leaves the scenario's ``EvaluationItem`` rows behind as orphans, which the
import service then silently re-uses by ``chat_id`` on the next import (the
"scenario 10" incident documented on the DELETE route) — so re-seeding after a
naive delete would resurrect stale item content.

The deletion order below is the proven production path, extracted verbatim from
``sm_delete_scenario`` (scenario_manager_api): scenario-scoped relations first
(FK order matters), then the scenario, then every EvaluationItem that lost its
last scenario link — while items still shared with other scenarios are kept.
"""

import logging

from db.database import db

logger = logging.getLogger(__name__)


def delete_scenario_deep(scenario) -> int:
    """Delete a scenario, its scenario-scoped relations, and orphaned items.

    Does NOT commit — the caller owns the transaction (the route commits per
    request, the seeder groups several deletions before re-creating).

    Returns the number of orphaned EvaluationItems that were hard-deleted.
    """
    from db.tables import (
        ComparisonSession, Feature, Message, ScenarioThreadDistribution,
        ScenarioThreads, ScenarioUsers, UserFeatureRanking, UserFeatureRating,
        ItemDimensionRating,
    )
    from db.models.scenario import (
        EvaluationItem, ItemComparisonEvaluation, ItemLabelingEvaluation,
    )

    scenario_id = scenario.id

    # Snapshot the item ids linked to this scenario before we drop the link
    # table — used afterwards to find items that are no longer attached to
    # anything and can be hard-deleted with their messages, features and
    # per-item evaluations.
    linked_item_ids = [
        st.thread_id
        for st in ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
    ]

    # Drop scenario-scoped relations first so FK constraints don't fight
    # the cascade. Order matters: comparison sessions and item ratings
    # reference both the scenario and the item.
    ComparisonSession.query.filter_by(scenario_id=scenario_id).delete()
    ItemComparisonEvaluation.query.filter_by(scenario_id=scenario_id).delete()
    ItemLabelingEvaluation.query.filter_by(scenario_id=scenario_id).delete()
    ItemDimensionRating.query.filter_by(scenario_id=scenario_id).delete()
    ScenarioThreadDistribution.query.filter_by(scenario_id=scenario_id).delete()
    ScenarioThreads.query.filter_by(scenario_id=scenario_id).delete()
    ScenarioUsers.query.filter_by(scenario_id=scenario_id).delete()

    db.session.delete(scenario)
    db.session.flush()  # so the orphan check below sees scenario_threads gone

    # Cascade-delete EvaluationItems that lost their last scenario link.
    # We avoid hard-deleting items still shared with other scenarios — that
    # would corrupt their data. Each orphaned item gets its messages,
    # features, feature-rankings/ratings, and any remaining cross-scenario
    # evaluations dropped first to satisfy FK constraints.
    orphaned_count = 0
    if linked_item_ids:
        still_linked = {
            row.thread_id
            for row in ScenarioThreads.query.filter(
                ScenarioThreads.thread_id.in_(linked_item_ids)
            ).all()
        }
        orphans = [iid for iid in linked_item_ids if iid not in still_linked]
        if orphans:
            feature_ids = [
                row.feature_id
                for row in Feature.query.filter(Feature.item_id.in_(orphans)).all()
            ]
            if feature_ids:
                UserFeatureRanking.query.filter(
                    UserFeatureRanking.feature_id.in_(feature_ids)
                ).delete(synchronize_session=False)
                UserFeatureRating.query.filter(
                    UserFeatureRating.feature_id.in_(feature_ids)
                ).delete(synchronize_session=False)

            Feature.query.filter(Feature.item_id.in_(orphans)).delete(synchronize_session=False)
            Message.query.filter(Message.item_id.in_(orphans)).delete(synchronize_session=False)
            ItemComparisonEvaluation.query.filter(
                ItemComparisonEvaluation.item_id.in_(orphans)
            ).delete(synchronize_session=False)
            ItemLabelingEvaluation.query.filter(
                ItemLabelingEvaluation.item_id.in_(orphans)
            ).delete(synchronize_session=False)
            ItemDimensionRating.query.filter(
                ItemDimensionRating.item_id.in_(orphans)
            ).delete(synchronize_session=False)
            EvaluationItem.query.filter(
                EvaluationItem.item_id.in_(orphans)
            ).delete(synchronize_session=False)
            orphaned_count = len(orphans)

    logger.info(
        "Deep-deleted scenario %s (%d orphaned item(s) cleaned)",
        scenario_id, orphaned_count,
    )
    return orphaned_count
