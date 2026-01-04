import traceback
from venv import logger
import logging
from . import data_blueprint, auth_blueprint
from flask import Blueprint, jsonify, request, g
from werkzeug.security import check_password_hash
from werkzeug.exceptions import BadRequest
from auth.decorators import authentik_required, admin_required, roles_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError

from db.database import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating, UserMailHistoryRating, UserMessageRating, UserGroup,ConsultingCategoryType, UserConsultingCategorySelection,
                       UserGroup, UserPrompt, UserPromptShare,
                       ConsultingCategoryType, UserConsultingCategorySelection, RatingScenarios, ScenarioUsers, ScenarioThreadDistribution, ScenarioThreads, ScenarioRoles, ProgressionStatus)
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import joinedload
from uuid import uuid4
import uuid
from datetime import datetime
import json
import random


from .HelperFunctions import get_user_threads, can_access_thread
from services.feature_rating_service import FeatureRatingService


@data_blueprint.route('/email_threads/ratings/<int:thread_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_email_thread_for_ratings(thread_id):
    user = g.authentik_user

    # check if user can access thread
    if not can_access_thread(user.id, thread_id, 2):
        raise ValidationError('Access denied')

    rating_function_type = FeatureFunctionType.query.filter_by(name='rating').first()
    if not rating_function_type:
        raise NotFoundError('Rating function type not found')

    email_thread = EmailThread.query.filter_by(thread_id=thread_id,
                                               function_type_id=rating_function_type.function_type_id).first()
    if not email_thread:
        raise NotFoundError('Email thread not found or not for rating')

    rated = FeatureRatingService.has_user_fully_rated_thread(user.id, email_thread.thread_id)
    ratings_by_feature_id = FeatureRatingService.get_user_ratings_map_for_thread(user.id, email_thread.thread_id)

    thread_data = {
        'chat_id': email_thread.chat_id,
        'institut_id': email_thread.institut_id,
        'subject': email_thread.subject,
        'rated': rated,
        'messages': [
            {
                'message_id': msg.message_id,
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            } for msg in email_thread.messages
        ],
        'features': [
            {
                'model_name': feature.llm.name,
                'type': feature.feature_type.name,
                'content': feature.content,
                'user_rating': ratings_by_feature_id.get(feature.feature_id).rating_content
                if ratings_by_feature_id.get(feature.feature_id) else None,
                'feature_id': feature.feature_id  # Include the feature_id here
            } for feature in email_thread.features
        ]
    }

    return jsonify(thread_data), 200


@data_blueprint.route('/email_threads/ratings/<int:thread_id>/<int:feature_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_feature_and_messages(thread_id, feature_id):
    user = g.authentik_user

    # check if user can access thread
    if not can_access_thread(user.id, thread_id, 2):
        raise ValidationError('Access denied')

    # Get the feature by thread_id and feature_id
    feature = Feature.query.filter_by(thread_id=thread_id, feature_id=feature_id).first()
    if not feature:
        raise NotFoundError('Feature not found')

    # Get the messages for the thread_id
    messages = Message.query.filter_by(thread_id=thread_id).all()
    if not messages:
        raise NotFoundError('No messages found for the given thread_id')

    feature_data = {
        'model_name': feature.llm.name,
        'type': feature.feature_type.name,
        'content': feature.content,
        'feature_id': feature.feature_id
    }

    messages_data = [
        {
            'message_id': msg.message_id,
            'sender': msg.sender,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat()
        } for msg in messages
    ]

    response_data = {
        'feature': feature_data,
        'messages': messages_data
    }

    return jsonify(response_data), 200




@data_blueprint.route('/email_threads/ratings', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def list_email_threads_for_ratings():
    user = g.authentik_user

    rating_function_type = FeatureFunctionType.query.filter_by(name='rating').first()
    if not rating_function_type:
        raise NotFoundError('Rating function type not found')

    email_threads = get_user_threads(user.id, 2)

    threads_list = [
        {
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject,
            'rated': FeatureRatingService.has_user_fully_rated_thread(user.id, thread.thread_id)
        } for thread in email_threads
    ]

    return jsonify(threads_list), 200






@data_blueprint.route('/feature_type_mapping', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_feature_type_mapping():
    feature_types = FeatureType.query.all()

    if not feature_types:
        raise NotFoundError('No feature types found')

    mapping = {
        'by_name': {ft.name: ft.type_id for ft in feature_types},
        'by_id': {ft.type_id: ft.name for ft in feature_types}
    }

    return jsonify(mapping), 200

@data_blueprint.route('/feature_type_mapping/<identifier>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_feature_type(identifier):
    if identifier.isdigit():
        # Wenn der Identifier eine Zahl ist, gehe davon aus, dass es eine FeatureType-ID ist
        feature_type = FeatureType.query.filter_by(type_id=int(identifier)).first()
        if not feature_type:
            raise NotFoundError(f'Feature type ID {identifier} not found')
        return jsonify({'name': feature_type.name}), 200
    else:
        # Andernfalls gehe davon aus, dass es sich um einen FeatureType-Namen handelt
        feature_type = FeatureType.query.filter_by(name=identifier).first()
        if not feature_type:
            raise NotFoundError(f'Feature type name {identifier} not found')
        return jsonify({'type_id': feature_type.type_id}), 200

@data_blueprint.route('/save_rating/<int:thread_id>/<int:feature_id>', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='rating')
def save_rating(thread_id, feature_id):
    user = g.authentik_user

    # check if user can access thread
    if not can_access_thread(user.id, thread_id, 2):
        raise ValidationError('Access denied')
    data = request.get_json()
    rating_content = data.get('rating_content')
    edited_feature = data.get('edited_feature')

    if rating_content is None or edited_feature is None:
        raise ValidationError('Rating content and edited feature are required')

    # Find or create the feature rating
    feature_rating = UserFeatureRating.query.filter_by(user_id=user.id, feature_id=feature_id).first()

    if feature_rating:
        feature_rating.rating_content = rating_content
        feature_rating.edited_feature = edited_feature
    else:
        new_rating = UserFeatureRating(
            user_id=user.id,
            feature_id=feature_id,
            rating_content=rating_content,
            edited_feature=edited_feature
        )
        db.session.add(new_rating)

    db.session.commit()

    return jsonify({'status': 'Rating saved successfully'}), 201


@data_blueprint.route('/get_rating/<int:thread_id>/<int:feature_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_rating(thread_id, feature_id):
    user = g.authentik_user

    # check if user can access thread
    if not can_access_thread(user.id, thread_id, 2):
        raise ValidationError('Access denied')
    feature_rating = UserFeatureRating.query.filter_by(user_id=user.id, feature_id=feature_id).first()

    if not feature_rating:
        raise NotFoundError('Rating not found')

    rating_data = {
        'rating_content': feature_rating.rating_content,
        'edited_feature': feature_rating.edited_feature
    }

    return jsonify(rating_data), 200
