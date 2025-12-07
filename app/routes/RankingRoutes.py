import traceback
import logging

logger = logging.getLogger(__name__)
from . import data_blueprint, auth_blueprint
from flask import Blueprint, jsonify, request, g
from werkzeug.security import check_password_hash
from werkzeug.exceptions import BadRequest
from auth.decorators import authentik_required, admin_required, roles_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError

from db.db import db
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

# Import service layer
from services.user_service import UserService
from services.thread_service import ThreadService
from services.ranking_service import RankingService
from services.feature_service import FeatureService

from .HelperFunctions import get_user_threads, can_access_thread



@data_blueprint.route('/email_threads/rankings', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='ranking')
def list_email_threads_for_rankings():
    user = g.authentik_user

    # Use FeatureService to get function type
    ranking_function_type = FeatureService.get_function_type_by_name('ranking')
    if not ranking_function_type:
        raise NotFoundError('Ranking function type not found')

    # Use ThreadService to get user threads
    email_threads = ThreadService.get_threads_for_user(user.id, ranking_function_type.function_type_id)

    threads_list = []
    for thread in email_threads:
        # Use RankingService to check if user has ranked this thread
        ranked = RankingService.has_user_ranked_thread(user.id, thread.thread_id)

        threads_list.append({
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject,
            'sender': thread.sender,
            'ranked': ranked
        })

    return jsonify(threads_list), 200

@data_blueprint.route('/email_threads/feature_ranking_list', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='ranking')
def list_ranking_threads():
    user = g.authentik_user

    # Use FeatureService to get function type
    ranking_function_type = FeatureService.get_function_type_by_name('ranking')
    if not ranking_function_type:
        raise NotFoundError('Ranking function type not found')

    # Use ThreadService to get user threads
    email_threads = ThreadService.get_threads_for_user(user.id, ranking_function_type.function_type_id)

    threads_list = [
        {
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject
        } for thread in email_threads
    ]

    return jsonify(threads_list), 200

@data_blueprint.route('/email_threads/rankings/<int:thread_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='ranking')
def get_email_thread_for_rankings(thread_id):
    user = g.authentik_user

    # Use FeatureService to get function type
    ranking_function_type = FeatureService.get_function_type_by_name('ranking')
    if not ranking_function_type:
        raise NotFoundError('Ranking function type not found')

    # Use ThreadService to check access
    if not ThreadService.can_user_access_thread(user.id, thread_id, 1):
        raise ValidationError('Access denied')

    # Use ThreadService to get thread by id
    email_thread = ThreadService.get_thread_by_id(thread_id, ranking_function_type.function_type_id)
    if not email_thread:
        raise NotFoundError('Email thread not found or not for ranking')

    # Use RankingService to check if user has ranked this thread
    ranked = RankingService.has_user_ranked_thread(user.id, email_thread.thread_id)

    thread_data = {
        'chat_id': email_thread.chat_id,
        'institut_id': email_thread.institut_id,
        'subject': email_thread.subject,
        'ranked': ranked,
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
                'feature_id': feature.feature_id
            } for feature in email_thread.features
        ]
    }

    return jsonify(thread_data), 200


@data_blueprint.route('/email_threads/<int:thread_id>/current_ranking', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='ranking')
def get_current_ranking(thread_id):
    user = g.authentik_user

    # Use ThreadService to check access
    if not ThreadService.can_user_access_thread(user.id, thread_id, 1):
        raise ValidationError('Access denied')

    # Use RankingService to get current rankings organized by type
    rankings_data = RankingService.get_current_rankings_by_type(user.id, thread_id)

    # Format the output as expected by frontend
    formatted_rankings = [
        {
            "type": feature_type,
            "goodList": data["goodList"],
            "averageList": data["averageList"],
            "badList": data["badList"],
            "neutralList": data["neutralList"]
        }
        for feature_type, data in rankings_data.items()
    ]

    return jsonify(formatted_rankings), 200




@data_blueprint.route('/save_ranking/<int:thread_id>', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='ranking')
def save_ranking(thread_id):
    user = g.authentik_user

    # Use ThreadService to check access
    if not ThreadService.can_user_access_thread(user.id, thread_id, 1):
        raise ValidationError('Access denied')

    data = request.get_json()

    for feature_type in data:
        type_name = feature_type['type']
        for detail in feature_type['details']:
            model_name = detail['model_name']
            content = detail['content']
            position = detail['position']
            bucket = detail['bucket']

            # Use FeatureService to find the FeatureType
            feature_type_entry = FeatureService.get_feature_type_by_name(type_name)
            if not feature_type_entry:
                raise NotFoundError(f'Feature type {type_name} not found')

            # Use FeatureService to find the LLM
            llm_entry = FeatureService.get_llm_by_name(model_name)
            if not llm_entry:
                raise NotFoundError(f'LLM {model_name} not found')

            # Use FeatureService to find the feature
            feature = FeatureService.get_feature_by_attributes(
                thread_id=thread_id,
                type_id=feature_type_entry.type_id,
                llm_id=llm_entry.llm_id,
                content=content
            )

            if feature:
                # Use RankingService to save the ranking
                success, error_msg = RankingService.save_ranking(
                    user_id=user.id,
                    thread_id=thread_id,
                    feature_id=feature.feature_id,
                    type_id=feature_type_entry.type_id,
                    llm_id=llm_entry.llm_id,
                    position=position,
                    bucket=bucket
                )

                if not success:
                    raise ValidationError(error_msg)

    return jsonify({'status': 'Ranking saved successfully'}), 201



@data_blueprint.route('/admin/user_ranking_stats', methods=['GET'])
@admin_required
@handle_api_errors(logger_name='ranking')
def get_user_ranking_stats():
    # Use RankingService to get user ranking stats

    # Use RankingService to get user ranking stats
    user_stats = RankingService.get_user_ranking_stats_for_all_users()

    return jsonify(user_stats), 200

