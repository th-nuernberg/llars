"""
Scenario Schema API

API-Endpoints für das einheitliche EvaluationData Schema-Format.

SCHEMA GROUND TRUTH:
-------------------
Die Schemas sind definiert in:
- Backend: app/schemas/evaluation_data_schemas.py (Pydantic Models)
- Frontend: llars-frontend/src/schemas/evaluationSchemas.ts (TypeScript + Zod)

Dokumentation: .claude/plans/evaluation-data-schemas.md

Diese Endpoints liefern Daten im standardisierten EvaluationData Format,
das von allen LLARS-Komponenten verwendet werden soll:
- Frontend Evaluation Views
- Batch Generation
- LLM Prompts
- Data Export/Import

Verwendung:
    # Einzelnes Item im Schema-Format
    GET /api/scenarios/{id}/items/{item_id}/schema

    # Szenario-Übersicht mit Item-IDs
    GET /api/scenarios/{id}/schema
"""

import logging
from flask import jsonify, request, g
from auth.decorators import authentik_required
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ForbiddenError
)
from db.models import (
    RatingScenarios, ScenarioItems, EvaluationItem
)
from services.evaluation.schema_transformer_service import SchemaTransformer
from schemas.evaluation_data_schemas import EvaluationType
from .. import data_blueprint

logger = logging.getLogger(__name__)


@data_blueprint.route('/scenarios/<int:scenario_id>/schema', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_schema')
def get_scenario_schema_overview(scenario_id: int):
    """
    Liefert Szenario-Metadaten und Liste der Item-IDs im Schema-Format.

    Diese Endpoint gibt einen Überblick über das Szenario und die verfügbaren
    Items, ohne die vollständigen Item-Daten zu laden (für Performance).

    Path params:
        scenario_id: Szenario-ID

    Query params:
        include_ground_truth: bool - Ground Truth einbeziehen (nur für Owner)

    Returns:
        JSON mit:
        - scenario_id: Szenario-ID
        - name: Szenario-Name
        - type: EvaluationType (ranking, rating, etc.)
        - schema_version: Schema-Version (z.B. "1.0")
        - item_ids: Liste der Item-IDs
        - config: Szenario-Konfiguration
        - total_items: Anzahl Items

    Beispiel Response:
    ```json
    {
        "scenario_id": 123,
        "name": "News Summary Ranking",
        "type": "ranking",
        "schema_version": "1.0",
        "item_ids": [1, 2, 3, 4, 5],
        "config": {
            "mode": "simple",
            "buckets": [...],
            "allow_ties": true
        },
        "total_items": 5
    }
    ```

    SCHEMA REFERENZ: app/schemas/evaluation_data_schemas.py
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Evaluation Type bestimmen
    eval_type = SchemaTransformer.get_evaluation_type_for_scenario(scenario)

    # Items laden
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [si.item_id for si in scenario_items]

    # Config extrahieren (vereinfacht für Übersicht)
    config = scenario.config_json or {}
    eval_config = config.get('eval_config', {}).get('config', config)

    return jsonify({
        'scenario_id': scenario_id,
        'name': scenario.scenario_name,
        'type': eval_type.value,
        'schema_version': '1.0',
        'item_ids': item_ids,
        'config': eval_config,
        'total_items': len(item_ids),
        '_schema_reference': 'app/schemas/evaluation_data_schemas.py'
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/items/<int:item_id>/schema', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_schema')
def get_item_schema_data(scenario_id: int, item_id: int):
    """
    Liefert Item-Daten im einheitlichen EvaluationData Schema-Format.

    Dieser Endpoint transformiert die DB-Daten in das standardisierte
    JSON-Schema, das von allen LLARS-Komponenten verwendet wird.

    Path params:
        scenario_id: Szenario-ID
        item_id: Item-ID (früher thread_id)

    Query params:
        include_ground_truth: bool - Ground Truth einbeziehen (nur für Owner/Admin)

    Returns:
        JSON im EvaluationData Schema-Format:
        ```json
        {
            "schema_version": "1.0",
            "type": "ranking",
            "reference": {
                "type": "text",
                "label": "Original-Artikel",
                "content": "..."
            },
            "items": [
                {
                    "id": "item_1",
                    "label": "Zusammenfassung 1",
                    "source": {"type": "llm", "name": "..."},
                    "content": "..."
                }
            ],
            "config": {
                "mode": "simple",
                "buckets": [...],
                "allow_ties": true
            },
            "ground_truth": null
        }
        ```

    WICHTIG:
    - Item.id ist IMMER technisch (z.B. "item_1", "item_2")
    - Item.label ist für UI-Anzeige (NIEMALS LLM-Namen!)
    - Item.source enthält die tatsächliche Herkunft (human/llm/unknown)

    SCHEMA REFERENZ: app/schemas/evaluation_data_schemas.py
    """
    # Verify scenario exists
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Verify item is in this scenario
    scenario_item = ScenarioItems.query.filter_by(
        scenario_id=scenario_id,
        item_id=item_id
    ).first()

    if not scenario_item:
        raise NotFoundError(f'Item {item_id} is not part of scenario {scenario_id}')

    # Ground Truth nur für Owner/Admin
    include_ground_truth = request.args.get('include_ground_truth', 'false').lower() == 'true'
    if include_ground_truth:
        # TODO: Check if user is owner/admin
        pass

    # Transform to schema format
    try:
        schema_data = SchemaTransformer.transform_scenario_item(
            scenario=scenario,
            item_id=item_id,
            include_ground_truth=include_ground_truth
        )
    except ValueError as e:
        raise ValidationError(f'Schema transformation failed: {str(e)}')

    # Return as JSON
    return jsonify(schema_data.model_dump()), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/items/schema/batch', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='scenario_schema')
def get_items_schema_batch(scenario_id: int):
    """
    Batch-Endpoint: Liefert mehrere Items im Schema-Format.

    Für Performance bei größeren Szenarien - lädt mehrere Items
    in einem Request.

    Path params:
        scenario_id: Szenario-ID

    Request body:
        ```json
        {
            "item_ids": [1, 2, 3],
            "include_ground_truth": false
        }
        ```

    Returns:
        ```json
        {
            "items": [
                {...},  // EvaluationData für item 1
                {...},  // EvaluationData für item 2
                {...}   // EvaluationData für item 3
            ],
            "failed": [],
            "scenario_id": 123
        }
        ```

    SCHEMA REFERENZ: app/schemas/evaluation_data_schemas.py
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    data = request.get_json() or {}
    item_ids = data.get('item_ids', [])
    include_ground_truth = data.get('include_ground_truth', False)

    if not item_ids:
        raise ValidationError('item_ids is required')

    if len(item_ids) > 100:
        raise ValidationError('Maximum 100 items per batch request')

    results = []
    failed = []

    for item_id in item_ids:
        # Verify item is in scenario
        scenario_item = ScenarioItems.query.filter_by(
            scenario_id=scenario_id,
            item_id=item_id
        ).first()

        if not scenario_item:
            failed.append({'item_id': item_id, 'error': 'Not in scenario'})
            continue

        try:
            schema_data = SchemaTransformer.transform_scenario_item(
                scenario=scenario,
                item_id=item_id,
                include_ground_truth=include_ground_truth
            )
            results.append(schema_data.model_dump())
        except Exception as e:
            logger.warning(f'Failed to transform item {item_id}: {e}')
            failed.append({'item_id': item_id, 'error': str(e)})

    return jsonify({
        'items': results,
        'failed': failed,
        'scenario_id': scenario_id,
        '_schema_reference': 'app/schemas/evaluation_data_schemas.py'
    }), 200


@data_blueprint.route('/schemas/evaluation/types', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_schema')
def get_evaluation_types():
    """
    Liefert alle verfügbaren Evaluationstypen.

    Dieser Endpoint dient als Referenz für die unterstützten
    Evaluationstypen und ihre function_type_id Mappings.

    Returns:
        ```json
        {
            "types": [
                {
                    "id": "ranking",
                    "function_type_id": 1,
                    "name": {"de": "Ranking", "en": "Ranking"},
                    "description": {"de": "Items sortieren", "en": "Sort items"}
                },
                ...
            ],
            "schema_version": "1.0"
        }
        ```

    SCHEMA REFERENZ: app/schemas/evaluation_data_schemas.py
    """
    types = [
        {
            'id': 'ranking',
            'function_type_id': 1,
            'name': {'de': 'Ranking', 'en': 'Ranking'},
            'description': {
                'de': 'Items in Kategorien sortieren (Buckets)',
                'en': 'Sort items into categories (Buckets)'
            }
        },
        {
            'id': 'rating',
            'function_type_id': 2,
            'name': {'de': 'Rating', 'en': 'Rating'},
            'description': {
                'de': 'Multi-dimensionale Bewertung (LLM-as-Judge)',
                'en': 'Multi-dimensional rating (LLM-as-Judge)'
            }
        },
        {
            'id': 'mail_rating',
            'function_type_id': 3,
            'name': {'de': 'Mail-Bewertung', 'en': 'Mail Rating'},
            'description': {
                'de': 'Bewertung von Beratungsverläufen',
                'en': 'Rating of counseling conversations'
            }
        },
        {
            'id': 'comparison',
            'function_type_id': 4,
            'name': {'de': 'Vergleich', 'en': 'Comparison'},
            'description': {
                'de': 'Paarweiser Vergleich (A vs B)',
                'en': 'Pairwise comparison (A vs B)'
            }
        },
        {
            'id': 'authenticity',
            'function_type_id': 5,
            'name': {'de': 'Authentizität', 'en': 'Authenticity'},
            'description': {
                'de': 'Echt/Fake Bewertung',
                'en': 'Real/Fake assessment'
            }
        },
        {
            'id': 'labeling',
            'function_type_id': 7,
            'name': {'de': 'Labeling', 'en': 'Labeling'},
            'description': {
                'de': 'Kategorien zuweisen',
                'en': 'Assign categories'
            }
        }
    ]

    return jsonify({
        'types': types,
        'schema_version': '1.0',
        '_schema_reference': 'app/schemas/evaluation_data_schemas.py'
    }), 200


@data_blueprint.route('/schemas/evaluation/validate', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='scenario_schema')
def validate_evaluation_data():
    """
    Validiert Daten gegen das EvaluationData Schema.

    Nützlich für:
    - Import-Validierung
    - Debugging
    - Externe Integrationen

    Request body:
        JSON im EvaluationData Format

    Returns:
        ```json
        {
            "valid": true,
            "errors": [],
            "warnings": []
        }
        ```

    oder bei Fehlern:
        ```json
        {
            "valid": false,
            "errors": [
                {"field": "items[0].id", "message": "Field required"}
            ],
            "warnings": []
        }
        ```

    SCHEMA REFERENZ: app/schemas/evaluation_data_schemas.py
    """
    from schemas.evaluation_data_schemas import EvaluationData
    from pydantic import ValidationError as PydanticValidationError

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    errors = []
    warnings = []

    try:
        # Validate against Pydantic model
        EvaluationData.model_validate(data)
        valid = True
    except PydanticValidationError as e:
        valid = False
        for error in e.errors():
            errors.append({
                'field': '.'.join(str(x) for x in error['loc']),
                'message': error['msg'],
                'type': error['type']
            })

    # Additional semantic validations
    if valid:
        # Check for empty items
        if not data.get('items'):
            warnings.append({
                'field': 'items',
                'message': 'Items list is empty'
            })

        # Check for LLM names in labels (should not happen)
        for idx, item in enumerate(data.get('items', [])):
            label = item.get('label', '')
            source_name = item.get('source', {}).get('name', '')
            if source_name and source_name.lower() in label.lower():
                warnings.append({
                    'field': f'items[{idx}].label',
                    'message': 'Label should not contain source name (use generic labels)'
                })

    return jsonify({
        'valid': valid,
        'errors': errors,
        'warnings': warnings,
        '_schema_reference': 'app/schemas/evaluation_data_schemas.py'
    }), 200
