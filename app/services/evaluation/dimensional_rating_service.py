"""
Dimensional Rating Service.

Provides business logic for multi-dimensional item ratings.
This service supports the new generalized rating system where items
are evaluated on multiple configurable dimensions (e.g., Coherence, Fluency, Relevance).

This is the base for both generic ratings and specialized types like mail_rating.
"""

import logging
from typing import Optional
from datetime import datetime

from flask import current_app
from db.database import db
from db.models import (
    RatingScenarios, ScenarioItems, ScenarioUsers, ScenarioItemDistribution,
    EvaluationItem, Message, ItemDimensionRating, ProgressionStatus,
    FeatureFunctionType, User, ScenarioRoles
)

logger = logging.getLogger(__name__)


# Default LLM-as-Judge dimensions (standard metrics)
DEFAULT_DIMENSIONS = [
    {
        'id': 'coherence',
        'name': {'de': 'Kohärenz', 'en': 'Coherence'},
        'description': {'de': 'Logischer Aufbau und Zusammenhang', 'en': 'Logical structure and flow'},
        'weight': 0.25
    },
    {
        'id': 'fluency',
        'name': {'de': 'Flüssigkeit', 'en': 'Fluency'},
        'description': {'de': 'Sprachliche Qualität und Lesbarkeit', 'en': 'Language quality and readability'},
        'weight': 0.25
    },
    {
        'id': 'relevance',
        'name': {'de': 'Relevanz', 'en': 'Relevance'},
        'description': {'de': 'Bezug zum Thema/Kontext', 'en': 'Topic and context relevance'},
        'weight': 0.25
    },
    {
        'id': 'consistency',
        'name': {'de': 'Konsistenz', 'en': 'Consistency'},
        'description': {'de': 'Widerspruchsfreiheit und Faktentreue', 'en': 'Factual consistency'},
        'weight': 0.25
    }
]

# Default scale labels (1-5 scale)
DEFAULT_LABELS = {
    '1': {'de': 'Sehr schlecht', 'en': 'Very poor'},
    '2': {'de': 'Schlecht', 'en': 'Poor'},
    '3': {'de': 'Akzeptabel', 'en': 'Acceptable'},
    '4': {'de': 'Gut', 'en': 'Good'},
    '5': {'de': 'Sehr gut', 'en': 'Very good'}
}


class DimensionalRatingService:
    """Service for managing multi-dimensional item ratings."""

    @staticmethod
    def get_scenario_config(scenario_id: int) -> dict:
        """
        Get the rating configuration for a scenario.

        Args:
            scenario_id: Scenario ID

        Returns:
            Configuration dictionary with dimensions and settings
        """
        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            return {'error': 'Scenario not found'}

        config = scenario.config_json or {}

        # Ensure dimensions are present (use defaults if not configured)
        if 'dimensions' not in config:
            config['dimensions'] = DEFAULT_DIMENSIONS

        # Ensure scale settings
        config.setdefault('min', 1)
        config.setdefault('max', 5)
        config.setdefault('step', 1)
        config.setdefault('showOverallScore', True)
        config.setdefault('allowFeedback', True)

        # Default labels
        config.setdefault('labels', DEFAULT_LABELS)

        return config

    @staticmethod
    def get_items_for_user(scenario_id: int, user_id: int) -> list:
        """
        Get all items assigned to a user for rating in a scenario.

        Args:
            scenario_id: Scenario ID
            user_id: User ID

        Returns:
            List of items with evaluation status
        """
        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            return []

        # Check user access
        scenario_user = ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            user_id=user_id
        ).first()

        if not scenario_user:
            # Check if user is owner
            user = User.query.get(user_id)
            if not user or scenario.created_by != user.username:
                return []

        # Get distributed items or all items
        config = scenario.config_json or {}
        distribution_mode = config.get('distribution_mode', 'all')

        if distribution_mode == 'distributed' and scenario_user:
            # Get only distributed items
            distributions = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario_id,
                scenario_user_id=scenario_user.id
            ).all()
            scenario_item_ids = [d.scenario_item_id for d in distributions]
            scenario_items = ScenarioItems.query.filter(
                ScenarioItems.id.in_(scenario_item_ids)
            ).all()
        else:
            # Get all items in scenario
            scenario_items = ScenarioItems.query.filter_by(
                scenario_id=scenario_id
            ).all()

        item_ids = [si.item_id for si in scenario_items]
        if not item_ids:
            return []

        items = EvaluationItem.query.filter(
            EvaluationItem.item_id.in_(item_ids)
        ).order_by(EvaluationItem.item_id).all()

        # Get existing ratings for this user
        existing_ratings = ItemDimensionRating.query.filter(
            ItemDimensionRating.user_id == user_id,
            ItemDimensionRating.scenario_id == scenario_id,
            ItemDimensionRating.item_id.in_(item_ids)
        ).all()

        ratings_map = {r.item_id: r for r in existing_ratings}

        result = []
        for item in items:
            rating = ratings_map.get(item.item_id)

            # Get message count
            message_count = Message.query.filter_by(item_id=item.item_id).count()

            result.append({
                'id': item.item_id,
                'item_id': item.item_id,
                'thread_id': item.item_id,  # Backward compatibility
                'subject': item.subject,
                'sender': item.sender,
                'chat_id': item.chat_id,
                'message_count': message_count,
                'evaluated': rating is not None and rating.status == ProgressionStatus.DONE,
                'status': rating.status.value if rating else ProgressionStatus.NOT_STARTED.value,
                'overall_score': rating.overall_score if rating else None
            })

        return result

    @staticmethod
    def get_item_with_content(
        scenario_id: int,
        item_id: int,
        user_id: int
    ) -> dict:
        """
        Get item content with messages for rating.

        Args:
            scenario_id: Scenario ID
            item_id: Item ID
            user_id: User ID

        Returns:
            Dictionary with item content, messages, and existing rating
        """
        item = EvaluationItem.query.get(item_id)
        if not item:
            return {'error': 'Item not found'}

        # Get messages
        messages = Message.query.filter_by(
            item_id=item_id
        ).order_by(Message.timestamp).all()

        messages_data = [
            {
                'message_id': msg.message_id,
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                'generated_by': msg.generated_by
            }
            for msg in messages
        ]

        # Get existing rating
        existing_rating = ItemDimensionRating.query.filter_by(
            user_id=user_id,
            item_id=item_id,
            scenario_id=scenario_id
        ).first()

        rating_data = None
        if existing_rating:
            rating_data = existing_rating.to_dict()

        # Get scenario config for dimensions
        config = DimensionalRatingService.get_scenario_config(scenario_id)

        return {
            'item': {
                'id': item.item_id,
                'item_id': item.item_id,
                'subject': item.subject,
                'sender': item.sender,
                'chat_id': item.chat_id
            },
            'messages': messages_data,
            'content': DimensionalRatingService._build_content_text(messages_data),
            'existing_rating': rating_data,
            'config': config
        }

    @staticmethod
    def _build_content_text(messages: list) -> str:
        """
        Build a combined text from messages for display.

        Args:
            messages: List of message dictionaries

        Returns:
            Combined text content
        """
        parts = []
        for msg in messages:
            sender = msg.get('sender', 'Unknown')
            content = msg.get('content', '')
            parts.append(f"[{sender}]\n{content}")
        return '\n\n'.join(parts)

    @staticmethod
    def save_dimensional_rating(
        scenario_id: int,
        item_id: int,
        user_id: int,
        dimension_ratings: dict,
        feedback: str = None,
        auto_complete: bool = True
    ) -> dict:
        """
        Save multi-dimensional rating for an item.

        Args:
            scenario_id: Scenario ID
            item_id: Item ID
            user_id: User ID
            dimension_ratings: Dict mapping dimension_id to score
            feedback: Optional user feedback
            auto_complete: Auto-mark as DONE if all dimensions rated

        Returns:
            Dictionary with result and saved rating
        """
        # Validate item exists
        item = EvaluationItem.query.get(item_id)
        if not item:
            return {'error': 'Item not found'}

        # Get scenario config for weight calculation
        config = DimensionalRatingService.get_scenario_config(scenario_id)
        dimensions = config.get('dimensions', DEFAULT_DIMENSIONS)

        # Calculate overall score with weights
        weights = {d['id']: d.get('weight', 1.0) for d in dimensions}
        overall_score = DimensionalRatingService._calculate_weighted_score(
            dimension_ratings, weights
        )

        # Determine status
        required_dimensions = [d['id'] for d in dimensions]
        all_rated = all(
            dim_id in dimension_ratings and dimension_ratings[dim_id] is not None
            for dim_id in required_dimensions
        )

        if all_rated and auto_complete:
            status = ProgressionStatus.DONE
        elif dimension_ratings:
            status = ProgressionStatus.PROGRESSING
        else:
            status = ProgressionStatus.NOT_STARTED

        # Find or create rating
        existing_rating = ItemDimensionRating.query.filter_by(
            user_id=user_id,
            item_id=item_id,
            scenario_id=scenario_id
        ).first()

        was_done_before = existing_rating and existing_rating.status == ProgressionStatus.DONE
        became_done = status == ProgressionStatus.DONE and not was_done_before

        if existing_rating:
            existing_rating.dimension_ratings = dimension_ratings
            existing_rating.overall_score = overall_score
            existing_rating.feedback = feedback if feedback is not None else existing_rating.feedback
            existing_rating.status = status
            existing_rating.updated_at = datetime.utcnow()
            saved_rating = existing_rating
        else:
            new_rating = ItemDimensionRating(
                user_id=user_id,
                item_id=item_id,
                scenario_id=scenario_id,
                dimension_ratings=dimension_ratings,
                overall_score=overall_score,
                feedback=feedback,
                status=status
            )
            db.session.add(new_rating)
            saved_rating = new_rating

        db.session.commit()

        # Log completion event
        if became_done:
            DimensionalRatingService._log_completion_event(
                scenario_id, item_id, user_id
            )

        # Emit real-time update
        DimensionalRatingService._emit_rating_update(
            scenario_id, item_id, user_id, status.value
        )

        return {
            'success': True,
            'rating': saved_rating.to_dict(),
            'became_done': became_done
        }

    @staticmethod
    def _calculate_weighted_score(ratings: dict, weights: dict) -> float:
        """
        Calculate weighted average from dimension ratings.

        Args:
            ratings: Dict mapping dimension_id to score
            weights: Dict mapping dimension_id to weight

        Returns:
            Weighted average score
        """
        if not ratings:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for dim_id, score in ratings.items():
            if score is not None:
                weight = weights.get(dim_id, 1.0)
                weighted_sum += score * weight
                total_weight += weight

        return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0

    @staticmethod
    def get_user_progress(scenario_id: int, user_id: int) -> dict:
        """
        Get user's progress for a scenario.

        Args:
            scenario_id: Scenario ID
            user_id: User ID

        Returns:
            Progress statistics
        """
        items = DimensionalRatingService.get_items_for_user(scenario_id, user_id)

        total = len(items)
        completed = sum(1 for item in items if item.get('evaluated', False))
        in_progress = sum(
            1 for item in items
            if item.get('status') == ProgressionStatus.PROGRESSING.value
        )

        return {
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'not_started': total - completed - in_progress,
            'percent': round((completed / total) * 100, 1) if total > 0 else 0
        }

    @staticmethod
    def _log_completion_event(scenario_id: int, item_id: int, user_id: int):
        """Log item completion to system events."""
        try:
            from services.system_event_service import SystemEventService

            user = User.query.get(user_id)
            username = user.username if user else f'user_{user_id}'

            SystemEventService.log_event(
                event_type="rating.item_completed",
                severity="info",
                username=username,
                entity_type="item",
                entity_id=str(item_id),
                message=f"User '{username}' completed item {item_id} (dimensional rating)",
                details={
                    'item_id': item_id,
                    'scenario_id': scenario_id,
                    'function_type': 'rating'
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log completion event: {e}")

    @staticmethod
    def _emit_rating_update(
        scenario_id: int,
        item_id: int,
        user_id: int,
        status: str
    ):
        """Emit Socket.IO update when a rating is saved."""
        socketio = current_app.extensions.get('socketio')
        if not socketio:
            return

        try:
            socketio.emit(
                'rating:item_updated',
                {
                    'scenario_id': scenario_id,
                    'item_id': item_id,
                    'user_id': user_id,
                    'status': status
                },
                room=f'scenario_{scenario_id}'
            )
        except Exception as e:
            logger.warning(f"Failed to emit rating update: {e}")

    @staticmethod
    def get_scenario_statistics(scenario_id: int) -> dict:
        """
        Get statistics for a scenario's dimensional ratings.

        Args:
            scenario_id: Scenario ID

        Returns:
            Dictionary with statistics
        """
        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            return {'error': 'Scenario not found'}

        # Get all ratings for this scenario
        ratings = ItemDimensionRating.query.filter_by(
            scenario_id=scenario_id,
            status=ProgressionStatus.DONE
        ).all()

        if not ratings:
            return {
                'total_ratings': 0,
                'unique_users': 0,
                'unique_items': 0,
                'average_overall_score': None,
                'dimension_averages': {}
            }

        # Calculate statistics
        user_ids = set()
        item_ids = set()
        overall_scores = []
        dimension_scores = {}

        config = DimensionalRatingService.get_scenario_config(scenario_id)
        dimensions = config.get('dimensions', DEFAULT_DIMENSIONS)
        for dim in dimensions:
            dimension_scores[dim['id']] = []

        for rating in ratings:
            user_ids.add(rating.user_id)
            item_ids.add(rating.item_id)
            if rating.overall_score is not None:
                overall_scores.append(rating.overall_score)

            for dim_id, score in (rating.dimension_ratings or {}).items():
                if score is not None and dim_id in dimension_scores:
                    dimension_scores[dim_id].append(score)

        dimension_averages = {}
        for dim_id, scores in dimension_scores.items():
            if scores:
                dimension_averages[dim_id] = round(sum(scores) / len(scores), 2)

        return {
            'total_ratings': len(ratings),
            'unique_users': len(user_ids),
            'unique_items': len(item_ids),
            'average_overall_score': round(sum(overall_scores) / len(overall_scores), 2) if overall_scores else None,
            'dimension_averages': dimension_averages
        }
