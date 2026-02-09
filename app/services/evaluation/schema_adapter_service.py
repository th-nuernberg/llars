"""
Schema Adapter Service.

Provides backwards-compatible adapters for legacy endpoints while using
SchemaTransformer internally. This enables a gradual migration to the
unified EvaluationData schema.

Usage:
    from services.evaluation.schema_adapter_service import SchemaAdapter

    # Get ranking data in legacy format (for backwards compatibility)
    data = SchemaAdapter.get_ranking_thread_data(scenario, item_id, user_id)

    # Get rating data in legacy format
    data = SchemaAdapter.get_rating_thread_data(scenario, item_id, user_id)

    # Get new schema format directly
    schema = SchemaAdapter.get_schema_data(scenario, item_id)
"""

import logging
from typing import Optional, List, Dict, Any

from db.models import (
    RatingScenarios, EvaluationItem, Message, Feature,
    ScenarioItems, ScenarioUsers
)
from services.evaluation.schema_transformer_service import SchemaTransformer
from schemas.evaluation_data_schemas import (
    EvaluationData,
    EvaluationType,
    ContentType,
    SourceType,
)

logger = logging.getLogger(__name__)


class SchemaAdapter:
    """
    Adapter zwischen dem neuen EvaluationData Schema und Legacy-Formaten.

    Verwendet SchemaTransformer intern und konvertiert bei Bedarf
    in Legacy-Formate für Abwärtskompatibilität.
    """

    # =========================================================================
    # Public API: Schema Format (preferred)
    # =========================================================================

    @staticmethod
    def get_schema_data(
        scenario: RatingScenarios,
        item_id: int,
        include_ground_truth: bool = False
    ) -> EvaluationData:
        """
        Returns data in the new unified EvaluationData schema format.

        This is the preferred format for new frontend components.
        """
        return SchemaTransformer.transform_scenario_item(
            scenario=scenario,
            item_id=item_id,
            include_ground_truth=include_ground_truth
        )

    @staticmethod
    def get_schema_data_dict(
        scenario: RatingScenarios,
        item_id: int,
        include_ground_truth: bool = False
    ) -> Dict[str, Any]:
        """Returns schema data as dictionary (for JSON serialization)."""
        schema = SchemaAdapter.get_schema_data(scenario, item_id, include_ground_truth)
        return schema.model_dump()

    # =========================================================================
    # Legacy Adapters: Ranking
    # =========================================================================

    @staticmethod
    def get_ranking_thread_data(
        item_id: int,
        user_id: int,
        include_ranked_status: bool = True
    ) -> Dict[str, Any]:
        """
        Returns ranking thread data in legacy format for backwards compatibility.

        Legacy format:
        {
            'chat_id': int,
            'institut_id': int,
            'subject': str,
            'ranked': bool,
            'messages': [{message_id, sender, content, timestamp}],
            'features': [{model_name, type, content, feature_id}]
        }
        """
        eval_item = EvaluationItem.query.get(item_id)
        if not eval_item:
            return None

        messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()
        features = Feature.query.filter_by(item_id=item_id).all()

        # Check ranked status
        ranked = False
        if include_ranked_status:
            from services.ranking_service import RankingService
            ranked = RankingService.has_user_fully_ranked_thread(user_id, item_id)

        return {
            'chat_id': eval_item.chat_id,
            'institut_id': getattr(eval_item, 'institut_id', None),
            'subject': eval_item.subject,
            'ranked': ranked,
            'messages': [
                {
                    'message_id': msg.message_id,
                    'sender': msg.sender,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
                } for msg in messages
            ],
            'features': [
                {
                    'model_name': feature.llm.name if feature.llm else 'Unknown',
                    'type': feature.feature_type.name if feature.feature_type else 'Summary',
                    'content': feature.content,
                    'feature_id': feature.feature_id
                } for feature in features
            ]
        }

    @staticmethod
    def get_ranking_threads_list(
        items: List[EvaluationItem],
        user_id: int,
        include_ranked_status: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Returns list of ranking threads in legacy format.

        Legacy format:
        [{thread_id, chat_id, institut_id, subject, sender, ranked}]
        """
        from services.ranking_service import RankingService

        threads_list = []
        for item in items:
            ranked = False
            if include_ranked_status:
                ranked = RankingService.has_user_fully_ranked_thread(user_id, item.item_id)

            threads_list.append({
                'thread_id': item.item_id,
                'chat_id': item.chat_id,
                'institut_id': getattr(item, 'institut_id', None),
                'subject': item.subject,
                'sender': getattr(item, 'sender', None),
                'ranked': ranked
            })

        return threads_list

    # =========================================================================
    # Legacy Adapters: Rating
    # =========================================================================

    @staticmethod
    def get_rating_thread_data(
        item_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Returns rating thread data in legacy format.

        Legacy format:
        {
            'chat_id': int,
            'institut_id': int,
            'subject': str,
            'messages': [{message_id, sender, content, timestamp}],
            'features': [{model_name, type, content, feature_id}]
        }
        """
        eval_item = EvaluationItem.query.get(item_id)
        if not eval_item:
            return None

        messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()
        features = Feature.query.filter_by(item_id=item_id).all()

        return {
            'chat_id': eval_item.chat_id,
            'institut_id': getattr(eval_item, 'institut_id', None),
            'subject': eval_item.subject,
            'messages': [
                {
                    'message_id': msg.message_id,
                    'sender': msg.sender,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
                } for msg in messages
            ],
            'features': [
                {
                    'model_name': feature.llm.name if feature.llm else 'Unknown',
                    'type': feature.feature_type.name if feature.feature_type else 'Summary',
                    'content': feature.content,
                    'feature_id': feature.feature_id
                } for feature in features
            ]
        }

    # =========================================================================
    # Legacy Adapters: Mail Rating
    # =========================================================================

    @staticmethod
    def get_mail_rating_thread_data(
        item_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Returns mail rating thread data in legacy format.

        Legacy format:
        {
            'thread_id': int,
            'chat_id': int,
            'subject': str,
            'messages': [{message_id, sender, content, timestamp}]
        }
        """
        eval_item = EvaluationItem.query.get(item_id)
        if not eval_item:
            return None

        messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()

        return {
            'thread_id': item_id,
            'chat_id': eval_item.chat_id,
            'subject': eval_item.subject,
            'messages': [
                {
                    'message_id': msg.message_id,
                    'sender': msg.sender,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
                } for msg in messages
            ]
        }

    # =========================================================================
    # Legacy Adapters: Authenticity
    # =========================================================================

    @staticmethod
    def get_authenticity_thread_data(
        item_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Returns authenticity thread data in legacy format.

        Legacy format:
        {
            'thread_id': int,
            'chat_id': int,
            'subject': str,
            'messages': [{message_id, sender, content, timestamp}],
            'user_vote': {vote, confidence} or None
        }
        """
        from db.models import UserAuthenticityVote

        eval_item = EvaluationItem.query.get(item_id)
        if not eval_item:
            return None

        messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()

        # Get user's vote
        user_vote = None
        vote_record = UserAuthenticityVote.query.filter_by(
            item_id=item_id,
            user_id=user_id
        ).first()
        if vote_record:
            user_vote = {
                'vote': vote_record.vote,
                'confidence': vote_record.confidence
            }

        return {
            'thread_id': item_id,
            'chat_id': eval_item.chat_id,
            'subject': eval_item.subject,
            'messages': [
                {
                    'message_id': msg.message_id,
                    'sender': msg.sender,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
                } for msg in messages
            ],
            'user_vote': user_vote
        }

    # =========================================================================
    # Access Control Helpers
    # =========================================================================

    @staticmethod
    def check_scenario_access(item_id: int, user_id: int) -> Optional[RatingScenarios]:
        """
        Checks if user has access to an item via scenario membership.

        An item can belong to multiple scenarios. Checks all of them and
        returns the first scenario where the user has membership.

        Returns:
            RatingScenarios if access granted, None otherwise
        """
        scenario_items = ScenarioItems.query.filter_by(item_id=item_id).all()
        if not scenario_items:
            return None

        for scenario_item in scenario_items:
            scenario_user = ScenarioUsers.query.filter_by(
                scenario_id=scenario_item.scenario_id,
                user_id=user_id
            ).first()
            if scenario_user:
                return RatingScenarios.query.get(scenario_item.scenario_id)

        return None

    @staticmethod
    def get_scenario_for_item(item_id: int) -> Optional[RatingScenarios]:
        """Gets the scenario for an item (without access check)."""
        scenario_item = ScenarioItems.query.filter_by(item_id=item_id).first()
        if not scenario_item:
            return None
        return RatingScenarios.query.get(scenario_item.scenario_id)

    # =========================================================================
    # Schema to Legacy Conversion (for gradual migration)
    # =========================================================================

    @staticmethod
    def schema_to_legacy_ranking(schema_data: EvaluationData) -> Dict[str, Any]:
        """
        Converts EvaluationData schema to legacy ranking format.

        This allows endpoints to use SchemaTransformer internally
        while still returning legacy format for backwards compatibility.
        """
        # Extract reference content for messages
        messages = []
        if schema_data.reference:
            if schema_data.reference.type == ContentType.CONVERSATION:
                messages = [
                    {
                        'message_id': idx + 1,
                        'sender': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp
                    }
                    for idx, msg in enumerate(schema_data.reference.content or [])
                ]
            elif schema_data.reference.type == ContentType.TEXT:
                messages = [{
                    'message_id': 1,
                    'sender': 'source',
                    'content': schema_data.reference.content,
                    'timestamp': None
                }]

        # Extract features from items
        features = []
        for idx, item in enumerate(schema_data.items or []):
            features.append({
                'feature_id': idx + 1,
                'model_name': item.source.name if item.source and item.source.name else 'Unknown',
                'type': item.group or 'Summary',
                'content': item.content if isinstance(item.content, str) else str(item.content)
            })

        return {
            'chat_id': None,  # Not available in schema
            'institut_id': None,  # Not available in schema
            'subject': schema_data.reference.label if schema_data.reference else None,
            'ranked': False,  # Must be set externally
            'messages': messages,
            'features': features
        }
