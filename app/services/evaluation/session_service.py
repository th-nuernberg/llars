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
from db.models.scenario import ScenarioRoles
from schemas.evaluation_data_schemas import EvaluationType

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

        # Check user access
        scenario_user = ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            user_id=user_id
        ).first()

        if not scenario_user and not EvaluationSessionService._is_owner(scenario, user_id):
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

        # Description may be in config_json (new scenarios) or doesn't exist
        description = None
        if isinstance(config, dict):
            description = config.get('description')

        # Determine if user can evaluate (OWNER and EVALUATOR roles)
        can_evaluate = (
            scenario_user is not None
            and scenario_user.role in (ScenarioRoles.EVALUATOR, ScenarioRoles.OWNER)
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

        threads = EmailThread.query.filter(
            EmailThread.thread_id.in_(thread_ids)
        ).order_by(EmailThread.thread_id).all()

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

        # Batch-load evaluation statuses
        status_map = EvaluationSessionService._batch_get_evaluation_statuses(
            thread_ids, user_id, function_type, scenario_id
        )

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
                'message_count': message_counts.get(tid, 0),
                'feature_count': feature_counts.get(tid, 0)
            })

        return items

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

        elif function_type == 'labeling':
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

        elif function_type == 'comparison':
            # Comparison is per-session, not per-item; fallback to per-item
            for tid in thread_ids:
                status_map[tid] = EvaluationSessionService._get_thread_evaluation_status(
                    tid, user_id, function_type, scenario_id
                )

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

        elif function_type == 'comparison':
            # Comparison uses ComparisonSession -> ComparisonMessage -> ComparisonEvaluation
            # For now, check if any evaluation exists for this session
            try:
                from db.models import ComparisonSession, ComparisonEvaluation
                session = ComparisonSession.query.filter_by(
                    scenario_id=thread_id  # thread_id is used as scenario_id in comparison
                ).first()
                if session:
                    # Check if user has made any evaluations
                    eval_count = db.session.query(ComparisonEvaluation).join(
                        ComparisonSession.messages
                    ).filter(
                        ComparisonSession.id == session.id
                    ).count()
                    if eval_count > 0:
                        return 'done'
                return 'pending'
            except Exception:
                return 'pending'

        elif function_type == 'labeling':
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

        # Get features
        features = Feature.query.filter_by(thread_id=thread_id).all()

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
                'model_name': feature.llm.name if feature.llm else 'Unknown',
                'feature_type': feature.feature_type.name if feature.feature_type else 'other',
                'content': feature.content,
                'evaluated': existing_rating is not None,
                'rating': existing_rating.rating_content if existing_rating else None,
                'edited_content': existing_rating.edited_feature if existing_rating else None
            })

        return {
            'thread_id': thread_id,
            'subject': thread.subject,
            'messages': messages_data,
            'features': features_data,
            'feature_types': feature_types
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
