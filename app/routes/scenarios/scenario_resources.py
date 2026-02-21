"""
Scenario Resource Endpoints
Provides reference data for scenarios (function types, users, threads).
"""

import logging
from flask import jsonify, g
from auth.decorators import admin_required
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)
from db.database import db
from db.tables import FeatureFunctionType, User, UserGroup, EmailThread
from .. import data_blueprint


FUNCTION_TYPE_UI_META = {
    "ranking": {"display_name": "Ranking", "emoji": "🏆"},
    "rating": {"display_name": "Rating", "emoji": "⭐️"},
    "mail_rating": {"display_name": "Verlaufsbewertung", "emoji": "✉️"},
    "comparison": {"display_name": "Gegenüberstellung", "emoji": "⚖️"},
    "authenticity": {"display_name": "Fake/Echt", "emoji": "🕵️"},
}


@data_blueprint.route('/admin/get_function_types', methods=['GET'])
@admin_required
@handle_api_errors(logger_name='scenarios')
def get_function_types():
    """Get all available function types for scenarios"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    feature_function_types = FeatureFunctionType.query.all()
    function_types = []
    for feature_function_type in feature_function_types:
        name = feature_function_type.name
        ui = FUNCTION_TYPE_UI_META.get(name, {})
        function_types.append({
            'function_type_id': feature_function_type.function_type_id,
            'name': name,
            'display_name': ui.get("display_name") or name,
            'emoji': ui.get("emoji") or '',
        })

    return jsonify(function_types), 200


@data_blueprint.route('/admin/get_users', methods=['GET'])
@admin_required
@handle_api_errors(logger_name='scenarios')
def get_users():
    """Get all users for scenario assignment"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    # Include admins as well (useful for demo/testing scenarios).
    db_users = (
        db.session.query(User)
        .join(UserGroup, User.group_id == UserGroup.id)
        .filter(User.is_ai == False)
        .all()
    )

    users = []
    for db_user in db_users:
        users.append({
            'id': db_user.id,
            'name': db_user.username,
        })
    return jsonify(users), 200


@data_blueprint.route('/admin/get_threads_from_function_type/<int:function_type_id>', methods=['GET'])
@admin_required
@handle_api_errors(logger_name='scenarios')
def get_threads(function_type_id):
    """Get all threads for a specific function type"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    validated_function_type = FeatureFunctionType.query.filter_by(function_type_id=function_type_id).first()

    if validated_function_type is None:
        raise NotFoundError('Function type not found')

    db_threads = EmailThread.query.filter_by(function_type_id=validated_function_type.function_type_id).all()
    threads = []
    for thread in db_threads:
        threads.append({
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject,
            'sender': thread.sender,
        })

    return jsonify(threads), 200
