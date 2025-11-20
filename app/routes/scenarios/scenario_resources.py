"""
Scenario Resource Endpoints
Provides reference data for scenarios (function types, users, threads).
"""

import logging
from flask import jsonify, g
from auth.decorators import admin_required
from db.db import db
from db.tables import FeatureFunctionType, User, UserGroup, EmailThread
from .. import data_blueprint


@data_blueprint.route('/admin/get_function_types', methods=['GET'])
@admin_required
def get_function_types():
    """Get all available function types for scenarios"""
    try:
        # Authorization handled by @admin_required decorator
        # Current user available in g.keycloak_user

        feature_function_types = FeatureFunctionType.query.all()
        function_types = []
        for feature_function_type in feature_function_types:
            function_types.append({
                'function_type_id': feature_function_type.function_type_id,
                'name': feature_function_type.name,
            })

        return jsonify(function_types), 200

    except Exception as e:
        logging.error(e)
        return jsonify({'error': 'Internal Server Error'}), 500


@data_blueprint.route('/admin/get_users', methods=['GET'])
@admin_required
def get_users():
    """Get all non-admin users for scenario assignment"""
    try:
        # Authorization handled by @admin_required decorator
        # Current user available in g.keycloak_user

        db_users = (db.session.query(User).join(UserGroup, User.group_id == UserGroup.id)
                    .filter(UserGroup.name != "Admin").all())

        users = []
        for db_user in db_users:
            users.append({
                'id': db_user.id,
                'name': db_user.username,
            })
        return jsonify(users), 200

    except Exception as e:
        logging.error(e)
        return jsonify({'error': 'Internal Server Error'}), 500


@data_blueprint.route('/admin/get_threads_from_function_type/<int:function_type_id>', methods=['GET'])
@admin_required
def get_threads(function_type_id):
    """Get all threads for a specific function type"""
    try:
        # Authorization handled by @admin_required decorator
        # Current user available in g.keycloak_user

        validated_function_type = FeatureFunctionType.query.filter_by(function_type_id=function_type_id).first()

        if validated_function_type is None:
            return jsonify({'error': 'Function type not found'}), 404

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
    except Exception as e:
        logging.error(e)
        return jsonify({'error': 'Internal Server Error'}), 500
