"""
Scenario Statistics and Progress Tracking
Provides progress and completion statistics for scenarios.
"""

import logging
from flask import jsonify, g
from auth.decorators import admin_required, authentik_required
from decorators.error_handler import handle_api_errors
from decorators.permission_decorator import require_permission
from db.database import db
from db.tables import FeatureFunctionType
from services.scenario_stats_service import get_progress_stats
from ..HelperFunctions import get_user_threads
from .. import data_blueprint


@data_blueprint.route('/admin/scenario_progress_stats/<int:scenario_id>', methods=['GET'])
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenarios')
def get_scenario_user_progress_stats(scenario_id):
    """Get detailed progress statistics for all users in a scenario"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    stats = get_progress_stats(scenario_id)
    return jsonify(stats), 200


@data_blueprint.route('/evaluation/thread_counts', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenarios')
def get_user_thread_counts():
    """
    Get the count of assigned threads per function_type for the current user.
    Used by EvaluationHub to show which tools have scenarios available.

    Returns:
        {
            "counts": {
                "ranking": 3,
                "rating": 0,
                "mail_rating": 2,
                "comparison": 0,
                "authenticity": 1
            }
        }
    """
    user = g.authentik_user

    # Get all function types
    function_types = db.session.query(FeatureFunctionType).all()

    counts = {}
    for ft in function_types:
        threads = get_user_threads(user.id, ft.function_type_id)
        counts[ft.name] = len(threads)

    return jsonify({'counts': counts}), 200
