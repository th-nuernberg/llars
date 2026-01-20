"""
Test Data Routes for Development.

Provides endpoints for downloading, transforming, and seeding test datasets.
These routes are only available in development mode.

Endpoints:
- GET  /api/dev/datasets              - List available datasets
- GET  /api/dev/datasets/<id>         - Get dataset info
- POST /api/dev/datasets/<id>/download - Download dataset
- GET  /api/dev/datasets/<id>/preview  - Preview transformed data
- POST /api/dev/datasets/<id>/transform - Transform to LLARS format
- POST /api/dev/scenarios/seed        - Seed a scenario with test data
"""

import os
import logging
from functools import wraps
from datetime import datetime

from flask import current_app, request, jsonify, g, abort

from . import bp
from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, ValidationError, NotFoundError
from decorators.permission_decorator import require_permission

logger = logging.getLogger(__name__)

# Lazy-loaded services (avoid import-time errors)
_downloader = None
_transformer = None


def get_downloader():
    """Get or create DatasetDownloader instance."""
    global _downloader
    if _downloader is None:
        from services.test_data.dataset_downloader import DatasetDownloader
        _downloader = DatasetDownloader()
    return _downloader


def get_transformer():
    """Get or create DatasetTransformer instance."""
    global _transformer
    if _transformer is None:
        from services.test_data.dataset_transformer import DatasetTransformer
        _transformer = DatasetTransformer()
    return _transformer


def dev_only(f):
    """
    Decorator that only allows access in development mode.

    Returns 404 in production to hide the route completely.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        is_dev = (
            current_app.debug or
            os.getenv('FLASK_ENV') == 'development' or
            os.getenv('FLASK_DEBUG') == '1'
        )
        if not is_dev:
            abort(404)
        return f(*args, **kwargs)
    return decorated


# =============================================================================
# Dataset Endpoints
# =============================================================================

@bp.route('/datasets', methods=['GET'])
@dev_only
@authentik_required
@handle_api_errors(logger_name='dev')
def list_datasets():
    """
    List all available test datasets.

    Returns:
        List of dataset info with download status.
    """
    datasets = get_downloader().list_available_datasets()
    return jsonify({
        'datasets': datasets,
        'count': len(datasets)
    }), 200


@bp.route('/datasets/<dataset_id>', methods=['GET'])
@dev_only
@authentik_required
@handle_api_errors(logger_name='dev')
def get_dataset(dataset_id: str):
    """
    Get information about a specific dataset.

    Args:
        dataset_id: The dataset identifier

    Returns:
        Dataset info including download status and metadata.
    """
    info = get_downloader().get_dataset_info(dataset_id)
    if not info:
        raise NotFoundError(f"Dataset not found: {dataset_id}")

    return jsonify(info), 200


@bp.route('/datasets/<dataset_id>/download', methods=['POST'])
@dev_only
@authentik_required
@handle_api_errors(logger_name='dev')
def download_dataset(dataset_id: str):
    """
    Download a dataset from HuggingFace.

    Args:
        dataset_id: The dataset identifier

    Request body:
        - sample_size: Number of samples to download (default: 100)
        - split: Dataset split to use (default: train)

    Returns:
        Download result with path and sample count.
    """
    data = request.get_json() or {}
    sample_size = data.get('sample_size', 100)
    split = data.get('split', 'train')

    # Validate sample size
    if sample_size < 1 or sample_size > 10000:
        raise ValidationError("sample_size must be between 1 and 10000")

    logger.info(f"Downloading dataset {dataset_id} (sample_size={sample_size})")

    result = get_downloader().download_dataset(
        dataset_id=dataset_id,
        sample_size=sample_size,
        split=split
    )

    return jsonify(result), 200


@bp.route('/datasets/<dataset_id>/transform', methods=['POST'])
@dev_only
@authentik_required
@handle_api_errors(logger_name='dev')
def transform_dataset(dataset_id: str):
    """
    Transform a downloaded dataset to LLARS format.

    Args:
        dataset_id: The dataset identifier

    Request body:
        - limit: Optional limit on items to transform

    Returns:
        Transformation result with item count and output path.
    """
    data = request.get_json() or {}
    limit = data.get('limit')

    logger.info(f"Transforming dataset {dataset_id}")

    result = get_transformer().transform_dataset(
        dataset_id=dataset_id,
        limit=limit
    )

    return jsonify(result), 200


@bp.route('/datasets/<dataset_id>/preview', methods=['GET'])
@dev_only
@authentik_required
@handle_api_errors(logger_name='dev')
def preview_dataset(dataset_id: str):
    """
    Preview transformed data from a dataset.

    Args:
        dataset_id: The dataset identifier

    Query params:
        - count: Number of items to preview (default: 5)

    Returns:
        Preview of transformed items in LLARS format.
    """
    count = request.args.get('count', 5, type=int)
    count = min(count, 20)  # Limit preview size

    # Check if transformed data exists
    items = get_transformer().get_transformed_items(dataset_id, limit=count)

    if items is None:
        # Try to get raw data and preview transformation
        raw_items = get_downloader().get_raw_samples(dataset_id)
        if raw_items is None:
            raise NotFoundError(f"Dataset not downloaded: {dataset_id}. Download first.")

        items = get_transformer().preview_transformation(dataset_id, raw_items, count)

    return jsonify({
        'dataset_id': dataset_id,
        'llars_format': True,
        'count': len(items),
        'samples': items
    }), 200


@bp.route('/datasets/<dataset_id>', methods=['DELETE'])
@dev_only
@authentik_required
@handle_api_errors(logger_name='dev')
def delete_dataset(dataset_id: str):
    """
    Delete a downloaded dataset.

    Args:
        dataset_id: The dataset identifier

    Returns:
        Deletion confirmation.
    """
    deleted = get_downloader().delete_dataset(dataset_id)
    if not deleted:
        raise NotFoundError(f"Dataset not found: {dataset_id}")

    return jsonify({
        'status': 'deleted',
        'dataset_id': dataset_id
    }), 200


# =============================================================================
# Scenario Seeding Endpoints
# =============================================================================

@bp.route('/scenarios/seed', methods=['POST'])
@dev_only
@authentik_required
@handle_api_errors(logger_name='dev')
def seed_scenario():
    """
    Create a scenario with test data.

    Request body:
        - name: Scenario name
        - dataset_id: Dataset to use
        - llars_type: Evaluation type (comparison, rating, labeling, authenticity)
        - item_count: Number of items to include (default: 20)
        - add_users: List of usernames to add (optional)

    Returns:
        Created scenario info.
    """
    from db.database import db
    from db.tables import (
        RatingScenarios, FeatureFunctionType, ScenarioUsers, User,
        EmailThread, Message, ScenarioThreads
    )

    data = request.get_json()
    if not data:
        raise ValidationError("Request body required")

    # Required fields
    name = data.get('name')
    dataset_id = data.get('dataset_id')

    if not name:
        raise ValidationError("name is required")
    if not dataset_id:
        raise ValidationError("dataset_id is required")

    # Optional fields
    llars_type = data.get('llars_type', 'rating')
    item_count = min(data.get('item_count', 20), 200)
    add_users = data.get('add_users', [])

    # Get transformed items
    items = get_transformer().get_transformed_items(dataset_id, limit=item_count)
    if not items:
        raise ValidationError(f"No transformed data for {dataset_id}. Download and transform first.")

    # Map llars_type to function_type_id (based on FeatureFunctionType table)
    type_map = {
        'ranking': 1,
        'rating': 2,
        'comparison': 4,
        'authenticity': 5,
        'labeling': 7  # labeling
    }
    function_type_id = type_map.get(llars_type)
    if not function_type_id:
        raise ValidationError(f"Unknown llars_type: {llars_type}")

    # Verify function type exists
    func_type = FeatureFunctionType.query.filter_by(function_type_id=function_type_id).first()
    if not func_type:
        raise ValidationError(f"Function type {function_type_id} not found in database")

    # Get current user
    user = g.authentik_user
    username = getattr(user, 'username', str(user))

    # Create scenario
    scenario = RatingScenarios(
        scenario_name=name,
        function_type_id=function_type_id,
        begin=datetime.utcnow(),
        created_by=username,
        config_json={
            'source_dataset': dataset_id,
            'llars_type': llars_type,
            'seeded_at': datetime.utcnow().isoformat()
        }
    )
    db.session.add(scenario)
    db.session.flush()  # Get scenario ID

    logger.info(f"Created test scenario {scenario.id}: {name}")

    # Create threads from transformed items
    threads_created = 0
    for item in items:
        # Create EmailThread (note: chat_id is an integer, don't use thread_id string)
        thread = EmailThread(
            subject=item.get('subject', f'Test Thread {threads_created + 1}')[:200],
            sender=item.get('messages', [{}])[0].get('sender', 'test'),
        )
        db.session.add(thread)
        db.session.flush()

        # Create messages
        for msg in item.get('messages', []):
            message = Message(
                thread_id=thread.thread_id,
                sender=msg.get('sender', 'unknown'),
                content=msg.get('content', ''),
                timestamp=datetime.utcnow()
            )
            db.session.add(message)

        # Link to scenario
        scenario_thread = ScenarioThreads(
            scenario_id=scenario.id,
            thread_id=thread.thread_id
        )
        db.session.add(scenario_thread)
        threads_created += 1

    # Add users if specified
    users_added = 0
    for username_to_add in add_users:
        db_user = User.query.filter_by(username=username_to_add).first()
        if db_user:
            su = ScenarioUsers(
                scenario_id=scenario.id,
                user_id=db_user.id,
                role='EVALUATOR'
            )
            db.session.add(su)
            users_added += 1

    db.session.commit()

    logger.info(f"Seeded scenario {scenario.id} with {threads_created} threads and {users_added} users")

    return jsonify({
        'status': 'success',
        'scenario_id': scenario.id,
        'scenario_name': name,
        'llars_type': llars_type,
        'threads_created': threads_created,
        'users_added': users_added
    }), 201


@bp.route('/quick-test', methods=['POST'])
@dev_only
@authentik_required
@handle_api_errors(logger_name='dev')
def quick_test():
    """
    Quick test: Download, transform, and seed in one step.

    Request body:
        - dataset_id: Dataset to use (default: sst2)
        - sample_size: Number of samples (default: 50)
        - scenario_name: Name for the scenario

    Returns:
        Complete test setup result.
    """
    data = request.get_json() or {}

    dataset_id = data.get('dataset_id', 'sst2')
    sample_size = min(data.get('sample_size', 50), 200)
    scenario_name = data.get('scenario_name', f'Test Scenario ({dataset_id})')

    results = {
        'dataset_id': dataset_id,
        'steps': []
    }

    # Step 1: Download
    try:
        download_result = get_downloader().download_dataset(
            dataset_id=dataset_id,
            sample_size=sample_size
        )
        results['steps'].append({
            'step': 'download',
            'status': 'success',
            'samples': download_result['samples_downloaded']
        })
    except Exception as e:
        results['steps'].append({
            'step': 'download',
            'status': 'error',
            'error': str(e)
        })
        return jsonify(results), 500

    # Step 2: Transform
    try:
        transform_result = get_transformer().transform_dataset(dataset_id)
        results['steps'].append({
            'step': 'transform',
            'status': 'success',
            'items': transform_result['items_transformed'],
            'llars_type': transform_result['llars_type']
        })
    except Exception as e:
        results['steps'].append({
            'step': 'transform',
            'status': 'error',
            'error': str(e)
        })
        return jsonify(results), 500

    # Step 3: Seed scenario
    # Reuse seed_scenario logic
    from db.database import db
    from db.tables import (
        RatingScenarios, FeatureFunctionType, ScenarioUsers, User,
        EmailThread, Message, ScenarioThreads
    )

    try:
        items = get_transformer().get_transformed_items(dataset_id)
        llars_type = transform_result['llars_type']

        type_map = {'ranking': 1, 'rating': 2, 'authenticity': 4, 'comparison': 5, 'labeling': 6}
        function_type_id = type_map.get(llars_type, 2)

        user = g.authentik_user
        username = getattr(user, 'username', str(user))

        scenario = RatingScenarios(
            scenario_name=scenario_name,
            function_type_id=function_type_id,
            begin=datetime.utcnow(),
            created_by=username,
            config_json={'source_dataset': dataset_id, 'llars_type': llars_type}
        )
        db.session.add(scenario)
        db.session.flush()

        threads_created = 0
        for item in items[:sample_size]:
            thread = EmailThread(
                subject=item.get('subject', f'Test {threads_created + 1}')[:200],
                sender='test',
            )
            db.session.add(thread)
            db.session.flush()

            for msg in item.get('messages', []):
                message = Message(
                    thread_id=thread.thread_id,
                    sender=msg.get('sender', 'unknown'),
                    content=msg.get('content', ''),
                    timestamp=datetime.utcnow()
                )
                db.session.add(message)

            scenario_thread = ScenarioThreads(scenario_id=scenario.id, thread_id=thread.thread_id)
            db.session.add(scenario_thread)
            threads_created += 1

        db.session.commit()

        results['steps'].append({
            'step': 'seed',
            'status': 'success',
            'scenario_id': scenario.id,
            'threads_created': threads_created
        })
        results['scenario_id'] = scenario.id

    except Exception as e:
        db.session.rollback()
        results['steps'].append({
            'step': 'seed',
            'status': 'error',
            'error': str(e)
        })
        return jsonify(results), 500

    return jsonify(results), 201
