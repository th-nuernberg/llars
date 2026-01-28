"""
Schema Transformer Service.

Transformiert Datenbank-Modelle in das einheitliche EvaluationData Schema-Format.
Dies ermöglicht eine konsistente API-Schnittstelle für alle Evaluationstypen.

Verwendung:
    from services.evaluation.schema_transformer_service import SchemaTransformer

    # Einzelnes Item transformieren
    data = SchemaTransformer.transform_scenario_item(scenario, item_id)

    # Als JSON für API
    return jsonify(data.model_dump())
"""

import logging
from typing import Optional, List, Dict, Any

from db.models import (
    EvaluationItem, Message, Feature, RatingScenarios,
    ScenarioItems, FeatureType, LLM,
    AuthenticityConversation
)
from schemas.evaluation_data_schemas import (
    EvaluationData,
    EvaluationType,
    SchemaVersion,
    ContentType,
    SourceType,
    RankingMode,
    LabelingMode,
    LocalizedString,
    Source,
    Message as SchemaMessage,
    ConversationContent,
    Reference,
    Item,
    GroundTruth,
    Bucket,
    RankingGroup,
    SimpleRankingConfig,
    MultiGroupRankingConfig,
    Scale,
    Dimension,
    RatingConfig,
    MailRatingConfig,
    ComparisonConfig,
    AuthenticityOption,
    AuthenticityConfig,
    LabelOption,
    LabelingConfig,
    create_default_ranking_buckets,
    create_default_rating_dimensions,
    create_default_scale,
)

logger = logging.getLogger(__name__)


class SchemaTransformer:
    """
    Transformiert Datenbank-Modelle in das einheitliche EvaluationData Schema.

    Der Transformer konvertiert die verschiedenen DB-Strukturen (EvaluationItem,
    Message, Feature, etc.) in das standardisierte JSON-Schema für die API.
    """

    # =========================================================================
    # Öffentliche API
    # =========================================================================

    @staticmethod
    def transform_scenario_item(
        scenario: RatingScenarios,
        item_id: int,
        include_ground_truth: bool = False
    ) -> EvaluationData:
        """
        Transformiert ein Szenario-Item in das EvaluationData Schema-Format.

        Args:
            scenario: Das Szenario
            item_id: Die Item-ID (früher thread_id)
            include_ground_truth: Ground Truth einbeziehen (für Admin/Auswertung)

        Returns:
            EvaluationData im neuen Schema-Format

        Raises:
            ValueError: Bei unbekanntem Evaluationstyp
        """
        eval_type = SchemaTransformer._get_evaluation_type(scenario.function_type_id)

        if eval_type == EvaluationType.RANKING:
            return SchemaTransformer._transform_ranking(scenario, item_id, include_ground_truth)
        elif eval_type == EvaluationType.RATING:
            return SchemaTransformer._transform_rating(scenario, item_id, include_ground_truth)
        elif eval_type == EvaluationType.MAIL_RATING:
            return SchemaTransformer._transform_mail_rating(scenario, item_id, include_ground_truth)
        elif eval_type == EvaluationType.COMPARISON:
            return SchemaTransformer._transform_comparison(scenario, item_id, include_ground_truth)
        elif eval_type == EvaluationType.AUTHENTICITY:
            return SchemaTransformer._transform_authenticity(scenario, item_id, include_ground_truth)
        elif eval_type == EvaluationType.LABELING:
            return SchemaTransformer._transform_labeling(scenario, item_id, include_ground_truth)
        else:
            raise ValueError(f"Unknown evaluation type: {eval_type}")

    @staticmethod
    def get_evaluation_type_for_scenario(scenario: RatingScenarios) -> EvaluationType:
        """Gibt den EvaluationType für ein Szenario zurück."""
        return SchemaTransformer._get_evaluation_type(scenario.function_type_id)

    # =========================================================================
    # Typ-spezifische Transformationen
    # =========================================================================

    @staticmethod
    def _transform_ranking(
        scenario: RatingScenarios,
        item_id: int,
        include_ground_truth: bool
    ) -> EvaluationData:
        """Transformiert Ranking-Daten."""
        eval_item = EvaluationItem.query.get(item_id)
        messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()
        features = Feature.query.filter_by(item_id=item_id).all()

        # Reference: Original-Text oder Konversation
        reference = SchemaTransformer._build_reference(eval_item, messages)

        # Items: Features zum Ranken
        items = SchemaTransformer._build_items_from_features(features)

        # Config aus Szenario
        config = SchemaTransformer._build_ranking_config(scenario)

        # Ground Truth (optional)
        ground_truth = None
        if include_ground_truth and eval_item.ground_truth_label:
            ground_truth = GroundTruth(value=eval_item.ground_truth_label)

        return EvaluationData(
            schema_version=SchemaVersion.V1_0,
            type=EvaluationType.RANKING,
            reference=reference,
            items=items,
            config=config,
            ground_truth=ground_truth
        )

    @staticmethod
    def _transform_rating(
        scenario: RatingScenarios,
        item_id: int,
        include_ground_truth: bool
    ) -> EvaluationData:
        """Transformiert Rating-Daten (Multi-Dimensional)."""
        eval_item = EvaluationItem.query.get(item_id)
        messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()
        features = Feature.query.filter_by(item_id=item_id).all()

        # Reference: Kontext (z.B. Original-Artikel)
        reference = SchemaTransformer._build_reference(eval_item, messages)

        # Items: Was bewertet werden soll
        if features:
            items = SchemaTransformer._build_items_from_features(features)
        else:
            # Fallback: Messages als Items (z.B. für direkte Text-Bewertung)
            items = SchemaTransformer._build_items_from_messages(messages, eval_item)

        # Config aus Szenario
        config = SchemaTransformer._build_rating_config(scenario)

        return EvaluationData(
            schema_version=SchemaVersion.V1_0,
            type=EvaluationType.RATING,
            reference=reference,
            items=items,
            config=config
        )

    @staticmethod
    def _transform_mail_rating(
        scenario: RatingScenarios,
        item_id: int,
        include_ground_truth: bool
    ) -> EvaluationData:
        """Transformiert Mail-Rating-Daten (Beratungsverlauf)."""
        eval_item = EvaluationItem.query.get(item_id)
        messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()

        # Bei Mail Rating: Der gesamte Verlauf ist das Item
        # Reference ist optional (z.B. Richtlinien)
        reference = None

        # Item: Die Konversation selbst
        items = [
            Item(
                id="conversation_1",
                label=eval_item.subject or "Beratungsverlauf",
                source=Source(type=SourceType.HUMAN),
                content=ConversationContent(
                    type="conversation",
                    messages=[
                        SchemaMessage(
                            role=msg.sender,
                            content=msg.content,
                            timestamp=msg.timestamp.isoformat() if msg.timestamp else None
                        )
                        for msg in messages
                    ]
                )
            )
        ]

        # Config mit Mail-spezifischen Dimensionen
        config = SchemaTransformer._build_mail_rating_config(scenario)

        return EvaluationData(
            schema_version=SchemaVersion.V1_0,
            type=EvaluationType.MAIL_RATING,
            reference=reference,
            items=items,
            config=config
        )

    @staticmethod
    def _transform_comparison(
        scenario: RatingScenarios,
        item_id: int,
        include_ground_truth: bool
    ) -> EvaluationData:
        """Transformiert Comparison-Daten (A vs B)."""
        eval_item = EvaluationItem.query.get(item_id)
        messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()
        features = Feature.query.filter_by(item_id=item_id).all()

        # Reference: Kontext für Vergleich
        reference = SchemaTransformer._build_reference(eval_item, messages)

        # Items: Die beiden zu vergleichenden Elemente
        if len(features) >= 2:
            items = SchemaTransformer._build_items_from_features(features[:2])
        else:
            # Fallback: Generiere Items aus Messages
            items = SchemaTransformer._build_items_from_messages(messages, eval_item)[:2]

        # Config
        config = SchemaTransformer._build_comparison_config(scenario)

        return EvaluationData(
            schema_version=SchemaVersion.V1_0,
            type=EvaluationType.COMPARISON,
            reference=reference,
            items=items,
            config=config
        )

    @staticmethod
    def _transform_authenticity(
        scenario: RatingScenarios,
        item_id: int,
        include_ground_truth: bool
    ) -> EvaluationData:
        """Transformiert Authenticity-Daten (Echt/Fake)."""
        eval_item = EvaluationItem.query.get(item_id)
        messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()

        # Authenticity Metadata laden
        auth_conv = AuthenticityConversation.query.filter_by(item_id=item_id).first()

        # Reference ist None - der Kontext ist die Konversation selbst
        reference = None

        # Item: Die Konversation zur Bewertung
        source_type = SourceType.UNKNOWN
        source_name = None
        if auth_conv:
            if auth_conv.is_fake:
                source_type = SourceType.LLM
                source_name = auth_conv.model_short or auth_conv.model
            else:
                source_type = SourceType.HUMAN

        items = [
            Item(
                id="conversation_1",
                label=eval_item.subject or "Konversation",
                source=Source(type=source_type, name=source_name),
                content=ConversationContent(
                    type="conversation",
                    messages=[
                        SchemaMessage(
                            role=msg.sender,
                            content=msg.content,
                            timestamp=msg.timestamp.isoformat() if msg.timestamp else None
                        )
                        for msg in messages
                    ]
                )
            )
        ]

        # Config
        config = SchemaTransformer._build_authenticity_config(scenario)

        # Ground Truth (nur wenn angefordert)
        ground_truth = None
        if include_ground_truth and auth_conv:
            ground_truth = GroundTruth(
                value="fake" if auth_conv.is_fake else "human",
                source=Source(type=SourceType.HUMAN),
                confidence=1.0
            )

        return EvaluationData(
            schema_version=SchemaVersion.V1_0,
            type=EvaluationType.AUTHENTICITY,
            reference=reference,
            items=items,
            config=config,
            ground_truth=ground_truth
        )

    @staticmethod
    def _transform_labeling(
        scenario: RatingScenarios,
        item_id: int,
        include_ground_truth: bool
    ) -> EvaluationData:
        """Transformiert Labeling-Daten (Kategorisierung)."""
        eval_item = EvaluationItem.query.get(item_id)
        messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()
        features = Feature.query.filter_by(item_id=item_id).all()

        # Reference: Kontext
        reference = SchemaTransformer._build_reference(eval_item, messages)

        # Items: Was gelabelt werden soll
        if features:
            items = SchemaTransformer._build_items_from_features(features)
        else:
            items = SchemaTransformer._build_items_from_messages(messages, eval_item)

        # Config
        config = SchemaTransformer._build_labeling_config(scenario)

        # Ground Truth
        ground_truth = None
        if include_ground_truth and eval_item.ground_truth_label:
            ground_truth = GroundTruth(value=eval_item.ground_truth_label)

        return EvaluationData(
            schema_version=SchemaVersion.V1_0,
            type=EvaluationType.LABELING,
            reference=reference,
            items=items,
            config=config,
            ground_truth=ground_truth
        )

    # =========================================================================
    # Helper: Type Mapping
    # =========================================================================

    @staticmethod
    def _get_evaluation_type(function_type_id: int) -> EvaluationType:
        """Konvertiert function_type_id zu EvaluationType."""
        return EvaluationType.from_function_type_id(function_type_id)

    # =========================================================================
    # Helper: Reference Building
    # =========================================================================

    @staticmethod
    def _build_reference(
        eval_item: EvaluationItem,
        messages: List[Message]
    ) -> Optional[Reference]:
        """Baut Reference aus EvaluationItem und Messages."""
        if not messages:
            return None

        # Heuristik: Wenn nur eine Message mit speziellen Sender-Namen → Text
        source_senders = ('article', 'Original Article', 'source', 'original', 'text')
        if len(messages) == 1 and messages[0].sender in source_senders:
            return Reference(
                type=ContentType.TEXT,
                label=eval_item.subject or "Original",
                content=messages[0].content
            )

        # Mehrere Messages → Konversation
        return Reference(
            type=ContentType.CONVERSATION,
            label=eval_item.subject or "Konversation",
            content=[
                SchemaMessage(
                    role=msg.sender,
                    content=msg.content,
                    timestamp=msg.timestamp.isoformat() if msg.timestamp else None
                )
                for msg in messages
            ]
        )

    # =========================================================================
    # Helper: Items Building
    # =========================================================================

    @staticmethod
    def _build_items_from_features(features: List[Feature]) -> List[Item]:
        """Baut Items aus Features."""
        items = []
        for idx, feature in enumerate(features, 1):
            llm_name = feature.llm.name if feature.llm else None
            feature_type_name = feature.feature_type.name if feature.feature_type else "feature"

            # Source bestimmen
            if llm_name:
                source = Source(type=SourceType.LLM, name=llm_name)
            else:
                source = Source(type=SourceType.HUMAN)

            # Label: Generisch nummeriert (nie LLM-Namen!)
            label = f"{feature_type_name.capitalize()} {idx}"

            items.append(Item(
                id=f"item_{idx}",
                label=label,
                source=source,
                content=feature.content or "",
                group=feature_type_name if feature_type_name != "feature" else None
            ))

        return items

    @staticmethod
    def _build_items_from_messages(
        messages: List[Message],
        eval_item: EvaluationItem
    ) -> List[Item]:
        """Baut Items aus Messages (Fallback wenn keine Features)."""
        if not messages:
            return []

        # Einzelne Message → Ein Item
        if len(messages) == 1:
            msg = messages[0]
            source_type = SourceType.LLM if msg.generated_by and msg.generated_by != "Human" else SourceType.HUMAN

            return [Item(
                id="item_1",
                label=eval_item.subject or "Text",
                source=Source(
                    type=source_type,
                    name=msg.generated_by if source_type == SourceType.LLM else None
                ),
                content=msg.content
            )]

        # Mehrere Messages → Konversation als ein Item
        return [Item(
            id="item_1",
            label=eval_item.subject or "Konversation",
            source=Source(type=SourceType.HUMAN),
            content=ConversationContent(
                type="conversation",
                messages=[
                    SchemaMessage(
                        role=msg.sender,
                        content=msg.content,
                        timestamp=msg.timestamp.isoformat() if msg.timestamp else None
                    )
                    for msg in messages
                ]
            )
        )]

    # =========================================================================
    # Helper: Config Building
    # =========================================================================

    @staticmethod
    def _build_ranking_config(scenario: RatingScenarios) -> SimpleRankingConfig | MultiGroupRankingConfig:
        """Baut Ranking-Config aus Szenario."""
        config = scenario.config_json or {}
        eval_config = config.get('eval_config', {}).get('config', {})

        # Prüfe auf Multi-Group Modus
        if 'groups' in eval_config:
            return SchemaTransformer._build_multi_group_ranking_config(eval_config)

        # Simple Ranking
        buckets_data = eval_config.get('buckets', [])
        if buckets_data:
            buckets = [
                Bucket(
                    id=str(b.get('id', idx + 1)),
                    label=SchemaTransformer._to_localized_string(b.get('name', b.get('label', {}))),
                    color=b.get('color', '#cccccc'),
                    order=b.get('order', idx + 1)
                )
                for idx, b in enumerate(buckets_data)
            ]
        else:
            buckets = create_default_ranking_buckets()

        return SimpleRankingConfig(
            mode=RankingMode.SIMPLE,
            buckets=buckets,
            allow_ties=eval_config.get('allowTies', True),
            require_complete=True
        )

    @staticmethod
    def _build_multi_group_ranking_config(eval_config: dict) -> MultiGroupRankingConfig:
        """Baut Multi-Group Ranking Config."""
        groups_data = eval_config.get('groups', [])
        groups = []

        for group_data in groups_data:
            buckets_data = group_data.get('buckets', [])
            buckets = [
                Bucket(
                    id=str(b.get('id', idx + 1)),
                    label=SchemaTransformer._to_localized_string(b.get('name', b.get('label', {}))),
                    color=b.get('color', '#cccccc'),
                    order=b.get('order', idx + 1)
                )
                for idx, b in enumerate(buckets_data)
            ]

            # Fallback auf Default-Buckets wenn keine definiert
            if not buckets:
                buckets = create_default_ranking_buckets()

            groups.append(RankingGroup(
                id=group_data.get('id', f"group_{len(groups) + 1}"),
                label=SchemaTransformer._to_localized_string(group_data.get('label', {})),
                description=SchemaTransformer._to_localized_string(group_data.get('description', {})) if group_data.get('description') else None,
                buckets=buckets,
                allow_ties=group_data.get('allow_ties', True)
            ))

        return MultiGroupRankingConfig(
            mode=RankingMode.MULTI_GROUP,
            groups=groups,
            require_complete=eval_config.get('require_complete', True)
        )

    @staticmethod
    def _build_rating_config(scenario: RatingScenarios) -> RatingConfig:
        """Baut Rating-Config aus Szenario."""
        config = scenario.config_json or {}
        eval_config = config.get('eval_config', {}).get('config', config)

        # Scale
        scale = Scale(
            min=eval_config.get('min', 1),
            max=eval_config.get('max', 5),
            step=eval_config.get('step', 1),
            labels=SchemaTransformer._build_scale_labels(eval_config.get('labels', {}))
        )

        # Dimensions
        dimensions_data = eval_config.get('dimensions', [])
        if dimensions_data:
            dimensions = [
                Dimension(
                    id=d.get('id', f"dim_{idx}"),
                    label=SchemaTransformer._to_localized_string(d.get('name', d.get('label', {}))),
                    description=SchemaTransformer._to_localized_string(d.get('description', {})) if d.get('description') else None,
                    weight=d.get('weight', 0.25)
                )
                for idx, d in enumerate(dimensions_data)
            ]
        else:
            dimensions = create_default_rating_dimensions()

        return RatingConfig(
            scale=scale,
            dimensions=dimensions,
            show_overall=eval_config.get('showOverallScore', True)
        )

    @staticmethod
    def _build_mail_rating_config(scenario: RatingScenarios) -> MailRatingConfig:
        """Baut Mail-Rating-Config aus Szenario."""
        base_config = SchemaTransformer._build_rating_config(scenario)
        config = scenario.config_json or {}

        return MailRatingConfig(
            scale=base_config.scale,
            dimensions=base_config.dimensions,
            show_overall=base_config.show_overall,
            focus_role=config.get('focus_role', 'Berater')
        )

    @staticmethod
    def _build_comparison_config(scenario: RatingScenarios) -> ComparisonConfig:
        """Baut Comparison-Config aus Szenario."""
        config = scenario.config_json or {}
        eval_config = config.get('eval_config', {}).get('config', config)

        return ComparisonConfig(
            question=SchemaTransformer._to_localized_string(
                eval_config.get('question', {
                    'de': 'Welche Antwort ist besser?',
                    'en': 'Which response is better?'
                })
            ),
            criteria=eval_config.get('criteria'),
            allow_tie=eval_config.get('allowTie', True),
            show_source=eval_config.get('showSource', False)
        )

    @staticmethod
    def _build_authenticity_config(scenario: RatingScenarios) -> AuthenticityConfig:
        """Baut Authenticity-Config aus Szenario."""
        config = scenario.config_json or {}
        eval_config = config.get('eval_config', {}).get('config', config)

        options_data = eval_config.get('options', [])
        if options_data:
            options = [
                AuthenticityOption(
                    id=o.get('id', f"opt_{idx}"),
                    label=SchemaTransformer._to_localized_string(o.get('label', {}))
                )
                for idx, o in enumerate(options_data)
            ]
        else:
            # Default: Echt/Fake
            options = [
                AuthenticityOption(
                    id="human",
                    label=LocalizedString(de="Echt", en="Real")
                ),
                AuthenticityOption(
                    id="ai",
                    label=LocalizedString(de="KI-generiert", en="AI-generated")
                )
            ]

        return AuthenticityConfig(
            options=options,
            show_confidence=eval_config.get('showConfidence', True)
        )

    @staticmethod
    def _build_labeling_config(scenario: RatingScenarios) -> LabelingConfig:
        """Baut Labeling-Config aus Szenario."""
        config = scenario.config_json or {}
        eval_config = config.get('eval_config', {}).get('config', config)

        labels_data = eval_config.get('labels', eval_config.get('categories', []))
        labels = [
            LabelOption(
                id=l.get('id', f"label_{idx}"),
                label=SchemaTransformer._to_localized_string(l.get('name', l.get('label', {}))),
                description=SchemaTransformer._to_localized_string(l.get('description', {})) if l.get('description') else None,
                color=l.get('color')
            )
            for idx, l in enumerate(labels_data)
        ]

        mode_str = eval_config.get('mode', 'single')
        mode = LabelingMode.MULTI if mode_str == 'multi' else LabelingMode.SINGLE

        return LabelingConfig(
            mode=mode,
            labels=labels,
            allow_other=eval_config.get('allowOther', False),
            min_labels=eval_config.get('minLabels'),
            max_labels=eval_config.get('maxLabels')
        )

    # =========================================================================
    # Helper: Localization
    # =========================================================================

    @staticmethod
    def _to_localized_string(data: dict | str) -> LocalizedString:
        """Konvertiert verschiedene Formate zu LocalizedString."""
        if isinstance(data, str):
            return LocalizedString(de=data, en=data)

        return LocalizedString(
            de=data.get('de', data.get('name', '')),
            en=data.get('en', data.get('name', data.get('de', '')))
        )

    @staticmethod
    def _build_scale_labels(labels_data: dict) -> Optional[Dict[str, LocalizedString]]:
        """Baut Scale Labels."""
        if not labels_data:
            return None

        result = {}
        for key, value in labels_data.items():
            if isinstance(value, dict):
                result[str(key)] = LocalizedString(
                    de=value.get('de', ''),
                    en=value.get('en', value.get('de', ''))
                )
            else:
                result[str(key)] = LocalizedString(de=str(value), en=str(value))

        return result if result else None
