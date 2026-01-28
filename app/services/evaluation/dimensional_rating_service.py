"""
Dimensional Rating Service.

Provides business logic for multi-dimensional item ratings.
This service supports the new generalized rating system where items
are evaluated on multiple configurable dimensions (e.g., Coherence, Fluency, Relevance).

This is the base for both generic ratings and specialized types like mail_rating.
Supports variable Likert scales (0-1, 0-4, 1-5, 1-7, 0-9, 1-10, etc.).

SCHEMA GROUND TRUTH:
-------------------
Rating dimensions and scale configurations should align with:
- Backend: app/schemas/evaluation_data_schemas.py (RatingConfig, Dimension, Scale)
- Frontend: llars-frontend/src/schemas/evaluationSchemas.js
- Factory functions: create_default_rating_dimensions(), create_default_scale()
- Dokumentation: .claude/plans/evaluation-data-schemas.md
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from flask import current_app
from db.database import db
from db.models import (
    RatingScenarios, ScenarioItems, ScenarioUsers, ScenarioItemDistribution,
    EvaluationItem, Message, ItemDimensionRating, ProgressionStatus,
    FeatureFunctionType, User, ScenarioRoles
)
from schemas.evaluation_data_schemas import (
    EvaluationType,
    create_default_rating_dimensions,
    create_default_scale,
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

# Mail Rating dimensions (LLARS-specific for psychosocial online counseling)
# Original LLARS dimensions based on UserMailHistoryRating model
MAIL_RATING_DIMENSIONS = [
    {
        'id': 'counsellor_coherence',
        'name': {'de': 'Berater-Kohärenz', 'en': 'Counsellor Coherence'},
        'description': {'de': 'Logischer Zusammenhang und Konsistenz der Berater-Antworten', 'en': 'Logical connection and consistency of counsellor responses'},
        'weight': 0.25
    },
    {
        'id': 'client_coherence',
        'name': {'de': 'Klient-Kohärenz', 'en': 'Client Coherence'},
        'description': {'de': 'Verständlichkeit und Nachvollziehbarkeit der Klienten-Nachrichten', 'en': 'Comprehensibility and traceability of client messages'},
        'weight': 0.25
    },
    {
        'id': 'quality',
        'name': {'de': 'Qualität', 'en': 'Quality'},
        'description': {'de': 'Gesamtqualität der Beratungsinteraktion', 'en': 'Overall quality of the counseling interaction'},
        'weight': 0.25
    },
    {
        'id': 'overall',
        'name': {'de': 'Gesamtbewertung', 'en': 'Overall Rating'},
        'description': {'de': 'Zusammenfassende Bewertung des gesamten Verlaufs', 'en': 'Summary assessment of the entire conversation'},
        'weight': 0.25
    }
]

# Mail Rating scale labels
MAIL_RATING_LABELS = {
    '1': {'de': 'Unzureichend', 'en': 'Insufficient'},
    '2': {'de': 'Mangelhaft', 'en': 'Poor'},
    '3': {'de': 'Befriedigend', 'en': 'Satisfactory'},
    '4': {'de': 'Gut', 'en': 'Good'},
    '5': {'de': 'Sehr gut', 'en': 'Very good'}
}

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

        Supports variable Likert scales. If min/max not configured,
        uses sensible defaults based on the scale type or preset.

        For mail_rating scenarios (function_type_id=3), uses LLARS-specific
        dimensions (Empathie, Klarheit, Professionalität, etc.).

        Args:
            scenario_id: Scenario ID

        Returns:
            Configuration dictionary with dimensions and settings
        """
        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            return {'error': 'Scenario not found'}

        config = scenario.config_json or {}

        # Determine if this is a mail_rating scenario (function_type_id = 3)
        is_mail_rating = scenario.function_type_id == 3

        # Ensure dimensions are present (use type-specific defaults if not configured)
        if 'dimensions' not in config:
            if is_mail_rating:
                config['dimensions'] = MAIL_RATING_DIMENSIONS
            else:
                config['dimensions'] = DEFAULT_DIMENSIONS

        # Get scale settings from config - don't override if explicitly set
        # This allows for variable scales (0-1, 0-4, 1-7, 0-9, etc.)
        if 'min' not in config:
            config['min'] = 1  # Default to 1-based scale
        if 'max' not in config:
            config['max'] = 5  # Default to 5-point scale
        if 'step' not in config:
            config['step'] = 1

        config.setdefault('showOverallScore', True)
        config.setdefault('allowFeedback', True)

        # Generate default labels based on scale range if not configured
        if 'labels' not in config:
            if is_mail_rating:
                config['labels'] = MAIL_RATING_LABELS
            else:
                config['labels'] = DimensionalRatingService._generate_default_labels(
                    config['min'], config['max']
                )

        return config

    @staticmethod
    def _generate_default_labels(min_val: int, max_val: int) -> dict:
        """
        Generate default labels for a scale range.

        Args:
            min_val: Minimum scale value
            max_val: Maximum scale value

        Returns:
            Dictionary of labels
        """
        # Import here to avoid circular imports
        from services.evaluation.rating_prompt_generator import get_scale_labels_for_range

        labels_raw = get_scale_labels_for_range(min_val, max_val, 'de')

        # Convert to localized format
        labels = {}
        for value, label_de in labels_raw.items():
            labels[str(value)] = {'de': label_de, 'en': label_de}

        # If no preset found, use standard defaults
        if not labels:
            labels = DEFAULT_LABELS

        return labels

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
        scale_min = config.get('min', 1)
        scale_max = config.get('max', 5)

        # Calculate overall score with weights
        weights = {d['id']: d.get('weight', 1.0) for d in dimensions}
        overall_score = DimensionalRatingService._calculate_weighted_score(
            dimension_ratings, weights, scale_min, scale_max
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
    def _calculate_weighted_score(
        ratings: dict,
        weights: dict,
        scale_min: int = 1,
        scale_max: int = 5
    ) -> float:
        """
        Calculate weighted average from dimension ratings.

        Supports variable scale ranges for proper normalization.

        Args:
            ratings: Dict mapping dimension_id to score
            weights: Dict mapping dimension_id to weight
            scale_min: Minimum scale value (default 1)
            scale_max: Maximum scale value (default 5)

        Returns:
            Weighted average score (in the original scale range)
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
    def calculate_normalized_score(
        ratings: dict,
        weights: dict,
        scale_min: int = 1,
        scale_max: int = 5
    ) -> Optional[float]:
        """
        Calculate normalized score (0-1 range) from dimension ratings.

        Useful for comparing ratings across different scale ranges.

        Args:
            ratings: Dict mapping dimension_id to score
            weights: Dict mapping dimension_id to weight
            scale_min: Minimum scale value
            scale_max: Maximum scale value

        Returns:
            Normalized score (0.0 to 1.0) or None if no ratings
        """
        if not ratings:
            return None

        raw_score = DimensionalRatingService._calculate_weighted_score(
            ratings, weights, scale_min, scale_max
        )

        if scale_max == scale_min:
            return 1.0 if raw_score > 0 else 0.0

        normalized = (raw_score - scale_min) / (scale_max - scale_min)
        return round(max(0.0, min(1.0, normalized)), 4)

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

    @staticmethod
    def trigger_llm_evaluation(
        scenario_id: int,
        item_id: int,
        model_id: str,
        llm_user_id: int = None,
        locale: str = 'de'
    ) -> Dict[str, Any]:
        """
        Trigger LLM-based evaluation for an item.

        Uses the scenario's dimension configuration and scale settings
        to generate appropriate prompts and parse the LLM response.

        Args:
            scenario_id: Scenario ID
            item_id: Item ID to evaluate
            model_id: LLM model ID to use for evaluation
            llm_user_id: User ID to attribute the LLM rating to (optional)
            locale: Language locale for prompts

        Returns:
            Dictionary with evaluation results or error
        """
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator
        from services.llm.llm_client_factory import LLMClientFactory

        # Get scenario config
        config = DimensionalRatingService.get_scenario_config(scenario_id)
        if 'error' in config:
            return config

        # Get item content
        item = EvaluationItem.query.get(item_id)
        if not item:
            return {'error': 'Item not found'}

        # Get messages for the item
        messages = Message.query.filter_by(
            item_id=item_id
        ).order_by(Message.timestamp).all()

        # Build content text
        content = DimensionalRatingService._build_content_text([
            {
                'sender': msg.sender,
                'content': msg.content
            }
            for msg in messages
        ])

        dimensions = config.get('dimensions', DEFAULT_DIMENSIONS)
        scale_config = {
            'min': config.get('min', 1),
            'max': config.get('max', 5),
            'step': config.get('step', 1),
            'labels': config.get('labels', {})
        }

        # Generate prompts
        prompts = RatingPromptGenerator.generate_rating_prompt(
            dimensions=dimensions,
            scale_config=scale_config,
            content=content,
            locale=locale,
            content_type='Beratungskonversation' if locale == 'de' else 'Counseling conversation'
        )

        try:
            # Get LLM client and make request
            client = LLMClientFactory.get_client_for_model(model_id)
            completion = client.chat.completions.create(
                model=model_id,
                messages=[
                    {'role': 'system', 'content': prompts['system_prompt']},
                    {'role': 'user', 'content': prompts['user_prompt']}
                ],
                temperature=0.3,  # Lower temperature for consistent ratings
                max_tokens=2000
            )

            # Extract response content
            response_content = completion.choices[0].message.content if completion.choices else ''
            parsed = RatingPromptGenerator.parse_llm_rating_response(
                response_content, dimensions, scale_config
            )

            if not parsed['success']:
                return {
                    'error': 'Failed to parse LLM response',
                    'details': parsed['errors'],
                    'raw_response': response_content
                }

            # Optionally save the rating
            if llm_user_id:
                save_result = DimensionalRatingService.save_dimensional_rating(
                    scenario_id=scenario_id,
                    item_id=item_id,
                    user_id=llm_user_id,
                    dimension_ratings=parsed['ratings'],
                    feedback=parsed.get('summary'),
                    auto_complete=True
                )
                parsed['saved'] = save_result.get('success', False)

            parsed['model_id'] = model_id
            parsed['item_id'] = item_id
            parsed['scenario_id'] = scenario_id

            return parsed

        except Exception as e:
            logger.exception(f"Error during LLM evaluation: {e}")
            return {'error': f"LLM evaluation failed: {str(e)}"}

    @staticmethod
    def get_llm_evaluations(scenario_id: int) -> list:
        """
        Get all LLM evaluations for a scenario.

        Returns ratings that were created by LLM evaluators (identified
        by the user having is_llm_evaluator=True or special user IDs).

        Args:
            scenario_id: Scenario ID

        Returns:
            List of LLM evaluation records
        """
        # Get all ratings for this scenario
        ratings = ItemDimensionRating.query.filter_by(
            scenario_id=scenario_id
        ).all()

        # Filter for LLM evaluators
        llm_evaluations = []
        for rating in ratings:
            user = User.query.get(rating.user_id)
            if user and getattr(user, 'is_llm_evaluator', False):
                llm_evaluations.append(rating.to_dict())

        return llm_evaluations
