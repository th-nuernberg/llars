"""
Evaluation Session Service.

Provides unified session management for all evaluation types (rating, ranking,
comparison, etc.). This service handles:
- Loading session data for a scenario
- Retrieving items to evaluate (threads, features, etc.)
- Saving evaluation results
- Progress tracking

SCHEMA GROUND TRUTH:
-------------------
Uses EvaluationType from unified schemas for evaluation type handling:
- Backend: app/schemas/evaluation_data_schemas.py
- Frontend: llars-frontend/src/schemas/evaluationSchemas.js
- Dokumentation: .claude/plans/evaluation-data-schemas.md
"""

import logging
from typing import Optional
from datetime import datetime
from collections import defaultdict

from sqlalchemy import func
from db.database import db
from db.models import (
    RatingScenarios, ScenarioThreads, ScenarioUsers,
    EmailThread, Feature, UserFeatureRating, UserFeatureRanking, Message,
    FeatureFunctionType, User
)
from db.models.scenario import ScenarioRoles, MembershipStatus
from schemas.evaluation_data_schemas import EvaluationType
# Both labeling flavours (7 classic, 9 conversation) run through this service's
# code paths; see services/evaluation/labeling_types.py for why this is one
# shared predicate instead of an 'or' bolted onto every branch.
from services.evaluation.labeling_types import is_labeling_type, is_span_labeling

logger = logging.getLogger(__name__)


class EvaluationSessionService:
    """Service for managing evaluation sessions."""

    @staticmethod
    def get_session_data(scenario_id: int, user_id: int) -> dict:
        """
        Get session data for a scenario including items to evaluate.

        Args:
            scenario_id: Scenario ID
            user_id: Current user ID

        Returns:
            Dictionary with scenario info, config, and items
        """
        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            return {'error': 'Scenario not found'}

        # Check user access. Admin role gets a free pass — without this an
        # admin who didn't author the scenario and isn't listed in
        # scenario_users gets locked out (e.g. a fresh Authentik account
        # logging into a scenario owned by `researcher`).
        scenario_user = ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            user_id=user_id
        ).first()

        if not scenario_user and not EvaluationSessionService._is_owner(scenario, user_id):
            from services.permission_service import PermissionService
            user = User.query.get(user_id)
            if not user or not PermissionService.user_has_role(user.username, 'admin'):
                return {'error': 'User does not have access to this scenario'}

        # Get function type
        function_type = FeatureFunctionType.query.filter_by(
            function_type_id=scenario.function_type_id
        ).first()
        function_type_name = function_type.name if function_type else 'unknown'

        # Get items based on function type
        items = EvaluationSessionService._get_items_for_scenario(
            scenario_id, user_id, function_type_name
        )

        # Parse config
        config = scenario.config_json
        if isinstance(config, str):
            import json
            try:
                config = json.loads(config)
            except (json.JSONDecodeError, TypeError):
                config = {}

        # Scenario parts (labeling phases): assessors must not learn that the
        # scenario is partitioned — strip the parts section (item_ids/locked/
        # copilot flags) AND the copilot internals (hidden_control_salt/ratio
        # would make the covert control subset computable client-side) from
        # the delivered config. Owners/managers keep the full config.
        if is_labeling_type(function_type_name) and isinstance(config, dict):
            from services.evaluation.scenario_parts_service import ScenarioPartsService
            try:
                is_manager = ScenarioPartsService.is_manager(scenario, user_id)
            except Exception as exc:
                # Fail CLOSED: if the role can't be determined, treat the
                # viewer as assessor and strip — never leak the partition.
                logger.warning("[Parts] Manager check failed for scenario %s: %s",
                               scenario_id, exc)
                is_manager = False
            if not is_manager:
                config = ScenarioPartsService.sanitize_config_for_assessor(config)

        # Description may be in config_json (new scenarios) or doesn't exist
        description = None
        if isinstance(config, dict):
            description = config.get('description')

        # Determine if user can evaluate (active assessor with evaluation_role='assessor')
        # Archived users or eval-viewers are always read-only
        from db.models.scenario import EvaluationRole
        can_evaluate = (
            scenario_user is not None
            and scenario_user.membership_status == MembershipStatus.ACTIVE
            and scenario_user.evaluation_role == EvaluationRole.ASSESSOR.value
        )

        return {
            'scenario': {
                'id': scenario.id,
                'name': scenario.scenario_name,
                'description': description,
                'function_type': function_type_name,
                'function_type_id': scenario.function_type_id,
                'created_at': scenario.timestamp.isoformat() if scenario.timestamp else None,
                'is_owner': EvaluationSessionService._is_owner(scenario, user_id),
                'can_evaluate': can_evaluate
            },
            'config': config or {},
            'items': items
        }

    @staticmethod
    def _is_owner(scenario: RatingScenarios, user_id: int) -> bool:
        """Check if user is the scenario owner."""
        if not scenario.created_by:
            return False
        # Look up user to compare username with created_by
        user = User.query.get(user_id)
        if not user:
            return False
        return user.username == scenario.created_by

    @staticmethod
    def _get_items_for_scenario(scenario_id: int, user_id: int, function_type: str) -> list:
        """
        Get evaluation items for a scenario.
        Optimized: batch-loads counts and statuses instead of per-item queries.
        """
        # Get threads assigned to this scenario
        scenario_threads = ScenarioThreads.query.filter_by(
            scenario_id=scenario_id
        ).all()

        thread_ids = [st.thread_id for st in scenario_threads]
        if not thread_ids:
            return []

        # Scenario parts (labeling phases): when active, the parts config
        # dictates BOTH visibility (locked parts are simply absent for
        # assessors — indistinguishable from "items not imported yet") and
        # delivery order (part order, within a part sequential/random).
        # parts_order=None → parts inactive → today's behaviour (thread_id asc,
        # identical for every user) stays untouched.
        parts_order = None
        if is_labeling_type(function_type):
            from services.evaluation.scenario_parts_service import ScenarioPartsService
            scenario_obj = RatingScenarios.query.get(scenario_id)
            if scenario_obj is not None:
                parts_order = ScenarioPartsService.session_item_order(
                    scenario_obj, user_id, thread_ids
                )
        if parts_order is not None:
            thread_ids = parts_order
            if not thread_ids:
                return []

        threads = EmailThread.query.filter(
            EmailThread.thread_id.in_(thread_ids)
        ).order_by(EmailThread.thread_id).all()
        if parts_order is not None:
            # Re-order to the parts-defined delivery order; the frontend
            # renders items in array order, so this IS the rater's order.
            threads_by_id = {t.thread_id: t for t in threads}
            threads = [threads_by_id[tid] for tid in thread_ids if tid in threads_by_id]

        # Batch count messages per thread
        message_counts = dict(
            db.session.query(Message.thread_id, func.count(Message.message_id))
            .filter(Message.thread_id.in_(thread_ids))
            .group_by(Message.thread_id)
            .all()
        )

        # Batch count features per thread
        feature_counts = dict(
            db.session.query(Feature.thread_id, func.count(Feature.feature_id))
            .filter(Feature.thread_id.in_(thread_ids))
            .group_by(Feature.thread_id)
            .all()
        )

        # Batch-load a short preview per thread so the items overview can
        # render a meaningful body snippet instead of falling back to the
        # generic "Klicken zum Öffnen" placeholder. We pick the *last*
        # message (highest message_id) because that's the most-recent
        # client turn in a Berater/Klient conversation — exactly what
        # the rater needs to scan to decide which item to open first.
        first_message_rows = (
            db.session.query(Message.item_id, Message.content)
            .filter(Message.item_id.in_(thread_ids))
            .order_by(Message.item_id, Message.message_id.desc())
            .all()
        )
        preview_map: dict[int, str] = {}
        for item_id, content in first_message_rows:
            if item_id not in preview_map and content:
                # Strip the markdown asterisk-escape we apply at import
                # time so the preview reads naturally.
                preview_map[item_id] = content.replace('\\*', '*')[:200]

        # Batch-load evaluation statuses
        status_map = EvaluationSessionService._batch_get_evaluation_statuses(
            thread_ids, user_id, function_type, scenario_id
        )

        # Batch-load the user's SAVED evaluation values so an interface can
        # pre-fill on reload (e.g. labeling re-selects the chosen category).
        saved_eval_map = EvaluationSessionService._batch_get_saved_evaluations(
            thread_ids, user_id, function_type, scenario_id
        )

        # Co-pilot suggestions (labeling only). The map is filtered SERVER-SIDE:
        # hidden-control items are simply absent, indistinguishable from a failed
        # generation - the anchoring control subset must never leak to the client.
        # Failures fall back to "no suggestions"; labeling itself is never blocked.
        copilot_map = {}
        if is_labeling_type(function_type):
            try:
                from services.evaluation.labeling_copilot_service import LabelingCopilotService
                scenario_obj = RatingScenarios.query.get(scenario_id)
                if scenario_obj is not None:
                    copilot_map = LabelingCopilotService.get_visible_suggestions_map(
                        scenario_obj, user_id, thread_ids
                    )
            except Exception as exc:
                logger.warning("[Copilot] Suggestion delivery failed for scenario %s: %s",
                               scenario_id, exc)

        items = []
        for thread in threads:
            tid = thread.thread_id
            status = status_map.get(tid, 'pending')
            items.append({
                'id': tid,
                'thread_id': tid,
                'subject': thread.subject,
                'chat_id': thread.chat_id,
                'status': status,
                'evaluated': status == 'done',
                # Saved evaluation (when present) so the interface pre-fills it
                # on reload — None when the user hasn't evaluated this item yet.
                'evaluation': saved_eval_map.get(tid),
                # Labeling co-pilot suggestions (None = no suggestion: disabled,
                # not yet generated, generation failed OR hidden control item -
                # the client cannot tell these apart by design).
                'copilot_suggestion': copilot_map.get(tid),
                'message_count': message_counts.get(tid, 0),
                'feature_count': feature_counts.get(tid, 0),
                # Last message content (truncated). Drives the body
                # snippet on the EvaluationItemsOverview cards.
                'preview': preview_map.get(tid, ''),
                # Per-item research metadata (EvaluationItem.metadata_json).
                # Needed by EvaluationSession.vue so {{variable}} placeholders
                # in the briefing template (e.g. {{channel_label}}) can be
                # substituted from the current item's metadata.
                'metadata_json': thread.metadata_json or {}
            })

        return items

    @staticmethod
    def _batch_get_saved_evaluations(thread_ids: list, user_id: int, function_type: str, scenario_id: int) -> dict:
        """Batch-load the user's SAVED evaluation values for pre-fill on reload.

        Returns {item_id: {...}} with the values an interface needs to restore
        its inputs. Currently labeling (the interface reads item.evaluation =
        {category_id, is_unsure, feedback}); other types prefill via their own
        endpoints and return {} here.
        """
        if not thread_ids:
            return {}
        if is_labeling_type(function_type):
            from db.models.scenario import ItemLabelingEvaluation
            rows = ItemLabelingEvaluation.query.filter(
                ItemLabelingEvaluation.user_id == user_id,
                ItemLabelingEvaluation.scenario_id == scenario_id,
                ItemLabelingEvaluation.item_id.in_(thread_ids),
            ).all()

            if is_span_labeling(function_type):
                # Conversation labeling has MANY rows per item — one per span.
                # The payload is keyed by span so the interface can restore a
                # half-finished conversation exactly where the rater left it,
                # which at ~92 spans and ~20 minutes per item is the difference
                # between resuming and starting over.
                per_item: dict = {}
                for r in rows:
                    per_item.setdefault(r.item_id, {})[r.span_id or ''] = {
                        'category_id': r.category_id,
                        'is_unsure': bool(r.is_unsure),
                        'feedback': getattr(r, 'feedback', None) or '',
                    }
                return {item_id: {'spans': spans} for item_id, spans in per_item.items()}

            return {
                r.item_id: {
                    'category_id': r.category_id,
                    'is_unsure': bool(r.is_unsure),
                    'feedback': getattr(r, 'feedback', None) or '',
                }
                for r in rows
            }
        return {}

    @staticmethod
    def _batch_get_evaluation_statuses(thread_ids: list, user_id: int, function_type: str, scenario_id: int) -> dict:
        """
        Batch-load evaluation statuses for all thread_ids at once.
        Returns dict: {thread_id: 'done'|'in_progress'|'pending'}
        """
        if not thread_ids:
            return {}

        status_map = {tid: 'pending' for tid in thread_ids}

        if function_type in ('rating', 'mail_rating'):
            status_map = EvaluationSessionService._batch_status_rating(
                thread_ids, user_id, scenario_id
            )

        elif function_type == 'ranking':
            status_map = EvaluationSessionService._batch_status_ranking(
                thread_ids, user_id
            )

        elif function_type == 'authenticity':
            from db.models import UserAuthenticityVote
            votes = UserAuthenticityVote.query.filter(
                UserAuthenticityVote.user_id == user_id,
                UserAuthenticityVote.item_id.in_(thread_ids)
            ).all()
            voted_ids = {v.item_id for v in votes if v.vote is not None}
            status_map = {
                tid: ('done' if tid in voted_ids else 'pending')
                for tid in thread_ids
            }

        elif is_span_labeling(function_type):
            # Conversation labeling: an item is done only when EVERY span in it
            # has a decision, and it has a real intermediate state (one
            # conversation is ~92 spans / ~20 minutes of work).
            from services.evaluation.span_progress_service import item_status_map
            status_map = item_status_map(scenario_id, user_id, thread_ids)
            for tid in thread_ids:
                status_map.setdefault(tid, 'pending')

        elif is_labeling_type(function_type):
            from db.models.scenario import ItemLabelingEvaluation
            evals = ItemLabelingEvaluation.query.filter(
                ItemLabelingEvaluation.user_id == user_id,
                ItemLabelingEvaluation.scenario_id == scenario_id,
                ItemLabelingEvaluation.item_id.in_(thread_ids)
            ).all()
            done_ids = {e.item_id for e in evals if e.category_id is not None or e.is_unsure}
            status_map = {
                tid: ('done' if tid in done_ids else 'pending')
                for tid in thread_ids
            }

        elif function_type in ('comparison', 'communication_comparison'):
            # Comm-Comparison shares the comparison persistence layer
            # (ItemComparisonEvaluation rows), so a single query handles
            # both function types — only the rater UI shell differs.
            from db.models.scenario import ItemComparisonEvaluation
            evals = ItemComparisonEvaluation.query.filter(
                ItemComparisonEvaluation.user_id == user_id,
                ItemComparisonEvaluation.scenario_id == scenario_id,
                ItemComparisonEvaluation.item_id.in_(thread_ids)
            ).all()
            done_ids = {e.item_id for e in evals if e.choice is not None}
            status_map = {
                tid: ('done' if tid in done_ids else 'pending')
                for tid in thread_ids
            }

        return status_map

    @staticmethod
    def _batch_status_rating(thread_ids: list, user_id: int, scenario_id: int) -> dict:
        """Batch-load rating/mail_rating statuses using dimensional ratings."""
        from db.models import ItemDimensionRating
        from db.models.scenario import ProgressionStatus

        status_map = {tid: 'pending' for tid in thread_ids}

        # Load all dimensional ratings for this user+scenario in one query
        dim_ratings = ItemDimensionRating.query.filter(
            ItemDimensionRating.user_id == user_id,
            ItemDimensionRating.scenario_id == scenario_id,
            ItemDimensionRating.item_id.in_(thread_ids)
        ).all()

        # Build lookup
        dim_by_item = {dr.item_id: dr for dr in dim_ratings}

        # Get dimensions config once (not per-item)
        dimensions = []
        scenario = RatingScenarios.query.get(scenario_id)
        if scenario and scenario.config_json:
            import json
            config = scenario.config_json
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except (json.JSONDecodeError, TypeError):
                    config = {}
            eval_config = config.get('eval_config', {})
            if not isinstance(eval_config, dict):
                eval_config = {}
            eval_config_inner = eval_config.get('config', {})
            if not isinstance(eval_config_inner, dict):
                eval_config_inner = {}
            dimensions = config.get('dimensions', [])
            if not dimensions:
                dimensions = eval_config.get('dimensions', [])
            if not dimensions:
                dimensions = eval_config_inner.get('dimensions', [])

        required_dims = [d.get('id') for d in dimensions if d.get('id')] if dimensions else []

        # Items with dimensional ratings
        rated_item_ids = set()
        for tid in thread_ids:
            dr = dim_by_item.get(tid)
            if dr:
                if dr.status == ProgressionStatus.DONE:
                    status_map[tid] = 'done'
                    rated_item_ids.add(tid)
                elif required_dims and dr.dimension_ratings:
                    all_rated = all(
                        dim_id in dr.dimension_ratings and
                        dr.dimension_ratings.get(dim_id) is not None
                        for dim_id in required_dims
                    )
                    if all_rated:
                        status_map[tid] = 'done'
                        rated_item_ids.add(tid)
                    else:
                        status_map[tid] = 'in_progress'
                        rated_item_ids.add(tid)
                elif dr.dimension_ratings:
                    status_map[tid] = 'in_progress'
                    rated_item_ids.add(tid)

        # For items without dimensional ratings, check legacy feature-based ratings
        unrated = [tid for tid in thread_ids if tid not in rated_item_ids]
        if unrated:
            # Batch: get feature counts per thread
            feature_counts = dict(
                db.session.query(Feature.thread_id, func.count(Feature.feature_id))
                .filter(Feature.thread_id.in_(unrated))
                .group_by(Feature.thread_id)
                .all()
            )
            # Batch: get user rating counts per thread
            rating_counts = dict(
                db.session.query(Feature.thread_id, func.count(UserFeatureRating.rating_id))
                .join(UserFeatureRating, UserFeatureRating.feature_id == Feature.feature_id)
                .filter(
                    Feature.thread_id.in_(unrated),
                    UserFeatureRating.user_id == user_id
                )
                .group_by(Feature.thread_id)
                .all()
            )
            for tid in unrated:
                total = feature_counts.get(tid, 0)
                rated = rating_counts.get(tid, 0)
                if total == 0:
                    status_map[tid] = 'pending'
                elif rated >= total:
                    status_map[tid] = 'done'
                elif rated > 0:
                    status_map[tid] = 'in_progress'

        return status_map

    @staticmethod
    def _batch_status_ranking(thread_ids: list, user_id: int) -> dict:
        """Batch-load ranking statuses."""
        status_map = {tid: 'pending' for tid in thread_ids}

        # Batch: feature counts per thread
        feature_counts = dict(
            db.session.query(Feature.thread_id, func.count(Feature.feature_id))
            .filter(Feature.thread_id.in_(thread_ids))
            .group_by(Feature.thread_id)
            .all()
        )

        # Batch: ranked feature counts per thread for this user
        ranked_counts = dict(
            db.session.query(Feature.thread_id, func.count(UserFeatureRanking.ranking_id))
            .join(UserFeatureRanking, UserFeatureRanking.feature_id == Feature.feature_id)
            .filter(
                Feature.thread_id.in_(thread_ids),
                UserFeatureRanking.user_id == user_id
            )
            .group_by(Feature.thread_id)
            .all()
        )

        for tid in thread_ids:
            total = feature_counts.get(tid, 0)
            ranked = ranked_counts.get(tid, 0)
            if total == 0:
                status_map[tid] = 'pending'
            elif ranked >= total:
                status_map[tid] = 'done'
            elif ranked > 0:
                status_map[tid] = 'in_progress'

        return status_map

    @staticmethod
    def _get_thread_evaluation_status(thread_id: int, user_id: int, function_type: str, scenario_id: int = None) -> str:
        """
        Get the evaluation status for a thread.

        Args:
            thread_id: Thread/item ID
            user_id: User ID
            function_type: Type of evaluation (rating, ranking, etc.)
            scenario_id: Scenario ID (needed for dimensional ratings)

        Returns:
            'done' - fully evaluated
            'in_progress' - partially evaluated
            'pending' - not started
        """
        if function_type == 'rating' or function_type == 'mail_rating':
            # First check dimensional ratings (new system)
            from db.models import ItemDimensionRating, RatingScenarios
            from db.models.scenario import ProgressionStatus
            dim_rating = ItemDimensionRating.query.filter_by(
                user_id=user_id,
                item_id=thread_id,
                scenario_id=scenario_id
            ).first()

            if dim_rating:
                # Check if status is DONE
                if dim_rating.status == ProgressionStatus.DONE:
                    return 'done'

                # Fallback: Check if all dimensions are actually rated
                # (in case status wasn't properly set)
                scenario = RatingScenarios.query.get(scenario_id)
                if scenario and scenario.config_json:
                    import json
                    config = scenario.config_json
                    if isinstance(config, str):
                        try:
                            config = json.loads(config)
                        except (json.JSONDecodeError, TypeError):
                            config = {}

                    # Dimensions can be at multiple locations:
                    # 1. config.dimensions (direct)
                    # 2. config.eval_config.dimensions (nested in eval_config)
                    # 3. config.eval_config.config.dimensions (from wizard)
                    eval_config = config.get('eval_config', {})
                    if not isinstance(eval_config, dict):
                        eval_config = {}
                    eval_config_inner = eval_config.get('config', {})
                    if not isinstance(eval_config_inner, dict):
                        eval_config_inner = {}

                    dimensions = config.get('dimensions', [])
                    if not dimensions:
                        dimensions = eval_config.get('dimensions', [])
                    if not dimensions:
                        dimensions = eval_config_inner.get('dimensions', [])

                    if dimensions and dim_rating.dimension_ratings:
                        required_dims = [d.get('id') for d in dimensions if d.get('id')]
                        all_rated = all(
                            dim_id in dim_rating.dimension_ratings and
                            dim_rating.dimension_ratings.get(dim_id) is not None
                            for dim_id in required_dims
                        )
                        if all_rated:
                            return 'done'

                # Has some ratings but not complete
                if dim_rating.dimension_ratings:
                    return 'in_progress'
                return 'pending'

            # Fallback: Check feature-based ratings (legacy system)
            from services.feature_rating_service import FeatureRatingService

            total_features = db.session.query(Feature).filter_by(thread_id=thread_id).count()
            if total_features == 0:
                return 'pending'

            ratings = FeatureRatingService.get_user_ratings_for_thread(user_id, thread_id)
            rated_count = len(ratings)

            if rated_count == 0:
                return 'pending'
            elif rated_count >= total_features:
                return 'done'
            else:
                return 'in_progress'

        elif function_type == 'authenticity':
            # Check authenticity votes
            from db.models import UserAuthenticityVote
            vote = UserAuthenticityVote.query.filter_by(
                user_id=user_id,
                item_id=thread_id
            ).first()
            if vote is not None and vote.vote is not None:
                return 'done'
            return 'pending'

        elif function_type == 'ranking':
            # Check ranking evaluations via RankingService
            from services.ranking_service import RankingService

            # Check if fully ranked (all features in buckets)
            if RankingService.has_user_fully_ranked_thread(user_id, thread_id):
                return 'done'
            # Check if partially ranked (at least one feature in a bucket)
            if RankingService.has_user_ranked_thread(user_id, thread_id):
                return 'in_progress'
            return 'pending'

        elif function_type in ('comparison', 'communication_comparison'):
            from db.models.scenario import ItemComparisonEvaluation
            comp_eval = ItemComparisonEvaluation.query.filter_by(
                user_id=user_id,
                item_id=thread_id,
                scenario_id=scenario_id
            ).first()
            if comp_eval is not None and comp_eval.choice is not None:
                return 'done'
            return 'pending'

        elif is_span_labeling(function_type):
            # Conversation labeling: done means every span decided.
            from services.evaluation.span_progress_service import item_status_map
            return item_status_map(scenario_id, user_id, [thread_id]).get(
                thread_id, 'pending'
            )

        elif is_labeling_type(function_type):
            # Check labeling evaluations
            from db.models.scenario import ItemLabelingEvaluation
            labeling_eval = ItemLabelingEvaluation.query.filter_by(
                user_id=user_id,
                item_id=thread_id,
                scenario_id=scenario_id
            ).first()
            if labeling_eval is not None and (labeling_eval.category_id is not None or labeling_eval.is_unsure):
                return 'done'
            return 'pending'

        # Default: pending
        return 'pending'

    @staticmethod
    def _is_thread_evaluated(thread_id: int, user_id: int, function_type: str) -> bool:
        """Check if user has fully evaluated a thread (backward compatibility)."""
        status = EvaluationSessionService._get_thread_evaluation_status(
            thread_id, user_id, function_type
        )
        return status == 'done'

    @staticmethod
    def get_thread_features(scenario_id: int, thread_id: int, user_id: int) -> dict:
        """
        Get features for a specific thread in evaluation session.

        Args:
            scenario_id: Scenario ID (for access control)
            thread_id: Thread ID
            user_id: User ID for rating status

        Returns:
            Dictionary with features and messages
        """
        thread = EmailThread.query.get(thread_id)
        if not thread:
            return {'error': 'Thread not found'}

        # Get messages
        messages = Message.query.filter_by(thread_id=thread_id).order_by(
            Message.timestamp
        ).all()

        messages_data = [
            {
                'message_id': msg.message_id,
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
            }
            for msg in messages
        ]

        # Get features. Deterministic order (A = first, B = second) so the
        # comparison UI's A/B slots line up with the results export, which orders
        # option authors by feature_id (see option_a_source/option_b_source in
        # scenario_manager_api.py). Without this the A/B↔author mapping would rely
        # on implicit SQL order.
        features = Feature.query.filter_by(thread_id=thread_id).order_by(Feature.feature_id).all()

        # Get user's existing ratings
        ratings_map = {}
        user_ratings = UserFeatureRating.query.filter(
            UserFeatureRating.user_id == user_id,
            UserFeatureRating.feature_id.in_([f.feature_id for f in features])
        ).all()
        for rating in user_ratings:
            ratings_map[rating.feature_id] = rating

        # Get unique feature types
        feature_types = list(set([
            f.feature_type.name if f.feature_type else 'other'
            for f in features
        ]))

        features_data = []
        for feature in features:
            existing_rating = ratings_map.get(feature.feature_id)
            features_data.append({
                'id': feature.feature_id,
                'feature_id': feature.feature_id,
                'model_name': feature.model_id or 'Unknown',
                'feature_type': feature.feature_type.name if feature.feature_type else 'other',
                'content': feature.content,
                'evaluated': existing_rating is not None,
                'rating': existing_rating.rating_content if existing_rating else None,
                'edited_content': existing_rating.edited_feature if existing_rating else None
            })

        # Include existing comparison evaluation if present
        existing_comparison = None
        try:
            from db.models.scenario import ItemComparisonEvaluation
            comp_eval = ItemComparisonEvaluation.query.filter_by(
                user_id=user_id,
                item_id=thread_id,
                scenario_id=scenario_id
            ).first()
            if comp_eval:
                existing_comparison = comp_eval.to_dict()
        except Exception as e:
            logger.warning("Failed to load comparison evaluation for user=%s item=%s: %s", user_id, thread_id, e)

        return {
            'thread_id': thread_id,
            'subject': thread.subject,
            'messages': messages_data,
            'features': features_data,
            'feature_types': feature_types,
            'existing_comparison': existing_comparison,
            'metadata_json': thread.metadata_json or {}
        }

    @staticmethod
    def save_feature_rating(
        scenario_id: int,
        feature_id: int,
        user_id: int,
        rating: int,
        thread_id: int,
        edited_content: Optional[str] = None,
        comment: Optional[str] = None
    ) -> dict:
        """
        Save a rating for a feature.

        Args:
            scenario_id: Scenario ID
            feature_id: Feature ID being rated
            user_id: User ID
            rating: Rating value
            thread_id: Thread ID (for context/validation)
            edited_content: Optional edited text
            comment: Optional comment

        Returns:
            Dictionary with result status
        """
        # Validate feature exists
        feature = Feature.query.get(feature_id)
        if not feature:
            return {'error': 'Feature not found'}

        # Find or create rating
        existing_rating = UserFeatureRating.query.filter_by(
            user_id=user_id,
            feature_id=feature_id
        ).first()

        if existing_rating:
            existing_rating.rating_content = rating
            existing_rating.edited_feature = edited_content or existing_rating.edited_feature
        else:
            new_rating = UserFeatureRating(
                user_id=user_id,
                feature_id=feature_id,
                rating_content=rating,
                edited_feature=edited_content or ''
            )
            db.session.add(new_rating)

        db.session.commit()

        return {
            'success': True,
            'evaluation': {
                'feature_id': feature_id,
                'rating': rating,
                'edited_content': edited_content
            }
        }

    @staticmethod
    def mark_thread_complete(
        scenario_id: int,
        thread_id: int,
        user_id: int
    ) -> dict:
        """
        Mark a thread as complete for a user.

        Args:
            scenario_id: Scenario ID
            thread_id: Thread ID
            user_id: User ID

        Returns:
            Dictionary with result status
        """
        # For rating scenarios, this is implicit when all features are rated
        # Just return success - the actual completion check happens in get_session_data
        return {
            'success': True,
            'thread_id': thread_id,
            'status': 'completed'
        }


def emit_evaluation_update(scenario_id: int, item_id: int, user_id: int):
    """
    Emit Socket.IO update when an evaluation is saved.

    Args:
        scenario_id: Scenario ID
        item_id: Item that was evaluated
        user_id: User who made the evaluation
    """
    from flask import current_app

    socketio = current_app.extensions.get('socketio')
    if not socketio:
        return

    try:
        socketio.emit(
            'evaluation:item_evaluated',
            {
                'scenario_id': scenario_id,
                'item_id': item_id,
                'user_id': user_id
            },
            room=f'scenario_{scenario_id}'
        )
    except Exception as e:
        logger.warning(f'Failed to emit evaluation update: {e}')
