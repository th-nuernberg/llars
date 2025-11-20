import traceback
from venv import logger
import logging
from . import data_blueprint, auth_blueprint
from flask import Blueprint, jsonify, request, g
from werkzeug.security import check_password_hash
from werkzeug.exceptions import BadRequest
from auth.decorators import keycloak_required, admin_required, roles_required

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


from .HelperFunctions import get_user_threads, can_access_thread



@data_blueprint.route('/email_threads/rankings', methods=['GET'])
@keycloak_required
def list_email_threads_for_rankings():
    # Authorization handled by @keycloak_required decorator
    user = g.keycloak_user

    ranking_function_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    if not ranking_function_type:
        return jsonify({'error': 'Ranking function type not found'}), 404

    email_threads = get_user_threads(user.id, ranking_function_type.function_type_id)

    threads_list = []
    for thread in email_threads:
        # Check if the user has ranked features in this thread
        user_rankings = UserFeatureRanking.query.filter_by(user_id=user.id).join(Feature).filter(
            Feature.thread_id == thread.thread_id
        ).first()

        ranked = True if user_rankings else False

        threads_list.append({
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject,
            'sender': thread.sender,  # Hier wird der Sender hinzugefügt
            'ranked': ranked
        })

    return jsonify(threads_list), 200

@data_blueprint.route('/email_threads/feature_ranking_list', methods=['GET'])
@keycloak_required
def list_ranking_threads():
    # Authorization handled by @keycloak_required decorator
    user = g.keycloak_user

    # Hole alle Threads mit function_type_id = 1 (Ranking)
    ranking_function_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    if not ranking_function_type:
        return jsonify({'error': 'Ranking function type not found'}), 404

    # Nur Ranking-Threads zurückgeben
    #email_threads = EmailThread.query.filter_by(function_type_id=ranking_function_type.function_type_id).all()
    email_threads = get_user_threads(user.id, ranking_function_type.function_type_id)

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
@keycloak_required
def get_email_thread_for_rankings(thread_id):
    # Authorization handled by @keycloak_required decorator
    user = g.keycloak_user

    ranking_function_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    if not ranking_function_type:
        return jsonify({'error': 'Ranking function type not found'}), 404

    # check if user can access thread
    if not can_access_thread(user.id, thread_id, 1):
            return jsonify({'error': 'Access denied'}), 401

    email_thread = EmailThread.query.filter_by(thread_id=thread_id,
                                               function_type_id=ranking_function_type.function_type_id).first()
    if not email_thread:
        return jsonify({'error': 'Email thread not found or not for ranking'}), 404

    # Überprüfe, ob der Benutzer bereits Rankings für diesen Thread hat
    user_rankings = UserFeatureRanking.query.filter_by(user_id=user.id).join(Feature).filter(
        Feature.thread_id == email_thread.thread_id
    ).first()

    ranked = True if user_rankings else False

    thread_data = {
        'chat_id': email_thread.chat_id,
        'institut_id': email_thread.institut_id,
        'subject': email_thread.subject,
        'ranked': ranked,  # Füge den Ranked-Status hinzu
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
@keycloak_required
def get_current_ranking(thread_id):
    # Authorization handled by @keycloak_required decorator
    user = g.keycloak_user

    # check if user can access thread
    if not can_access_thread(user.id, thread_id, 1):
        return jsonify({'error': 'Access denied'}), 401

    # Holen Sie alle Rankings für den gegebenen Thread und Benutzer
    rankings = UserFeatureRanking.query.filter_by(user_id=user.id).join(Feature).filter(
        Feature.thread_id == thread_id).all()

    # Holen Sie alle Feature-Typen aus der Datenbank
    feature_types = FeatureType.query.all()

    # Dynamisch die Datenstruktur für die Rankings basierend auf den Feature-Typen aufbauen
    rankings_data = {feature_type.name: {"goodList": [], "averageList": [], "badList": [], "neutralList": []} for feature_type in feature_types}

    # Iteriere durch die Rankings und sortiere sie in die entsprechenden Buckets
    for ranking in rankings:
        feature_data = {
            'model_name': ranking.llm.name,
            'content': ranking.feature.content,
            'feature_id': ranking.feature_id,
            'position': int(ranking.ranking_content),
            'minimized': True  # Beispielwert, du kannst dies nach Bedarf ändern
        }

        # Bestimme den Feature-Typ (dynamisch basierend auf dem Ranking)
        feature_type = ranking.feature_type.name

        # Ordne die Feature-Daten dem richtigen Bucket und Typ zu
        if feature_type in rankings_data:
            if ranking.bucket == 'Gut':
                rankings_data[feature_type]['goodList'].append(feature_data)
            elif ranking.bucket == 'Mittel':
                rankings_data[feature_type]['averageList'].append(feature_data)
            elif ranking.bucket == 'Schlecht':
                rankings_data[feature_type]['badList'].append(feature_data)
            else:
                rankings_data[feature_type]['neutralList'].append(feature_data)

    # Holen Sie alle Features für den Thread, die noch nicht vom Benutzer gerankt wurden
    ranked_feature_ids = [ranking.feature_id for ranking in rankings]
    all_features = Feature.query.filter_by(thread_id=thread_id).all()

    for feature in all_features:
        if feature.feature_id not in ranked_feature_ids:
            feature_data = {
                'model_name': feature.llm.name,
                'content': feature.content,
                'feature_id': feature.feature_id,
                'position': None,  # Ungerankte Features haben keine Position
                'minimized': True  # Beispielwert, du kannst dies nach Bedarf ändern
            }

            # Ordne das Feature dem neutralen Bucket des entsprechenden Feature-Typs zu
            feature_type = feature.feature_type.name
            if feature_type in rankings_data:
                rankings_data[feature_type]['neutralList'].append(feature_data)

    # Sortiere die Listen innerhalb der Buckets nach der Position
    for feature_type, data in rankings_data.items():
        data['goodList'] = sorted(data['goodList'], key=lambda x: x['position'] if x['position'] is not None else float('inf'))
        data['averageList'] = sorted(data['averageList'], key=lambda x: x['position'] if x['position'] is not None else float('inf'))
        data['badList'] = sorted(data['badList'], key=lambda x: x['position'] if x['position'] is not None else float('inf'))
        data['neutralList'] = sorted(data['neutralList'], key=lambda x: x['position'] if x['position'] is not None else float('inf'))

    # Die finale Ausgabe im dynamischen Format
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
@keycloak_required
def save_ranking(thread_id):
    # Authorization handled by @keycloak_required decorator
    user = g.keycloak_user

    # check if user can access thread
    if not can_access_thread(user.id, thread_id, 1):
        return jsonify({'error': 'Access denied'}), 401

    data = request.get_json()

    for feature_type in data:
        type_name = feature_type['type']
        for detail in feature_type['details']:
            model_name = detail['model_name']
            content = detail['content']
            position = detail['position']
            bucket = detail['bucket']  # Bucket Information

            # Find the FeatureType ID
            feature_type_entry = FeatureType.query.filter_by(name=type_name).first()
            if not feature_type_entry:
                return jsonify({'error': f'Feature type {type_name} not found'}), 404

            # Find the LLM ID
            llm_entry = LLM.query.filter_by(name=model_name).first()
            if not llm_entry:
                return jsonify({'error': f'LLM {model_name} not found'}), 404

            # Find the feature_id for the given thread_id, feature_type_id, and llm_id
            feature = Feature.query.filter_by(
                thread_id=thread_id,
                type_id=feature_type_entry.type_id,
                llm_id=llm_entry.llm_id,
                content=content
            ).first()

            if feature:
                # Check if the ranking already exists
                existing_ranking = UserFeatureRanking.query.filter_by(
                    user_id=user.id,
                    feature_id=feature.feature_id,
                    type_id=feature_type_entry.type_id,  # Stelle sicher, dass der Typ jetzt auch gespeichert wird
                    llm_id=llm_entry.llm_id
                ).first()

                if existing_ranking:
                    # Update the ranking content and bucket if it exists
                    existing_ranking.ranking_content = position
                    existing_ranking.bucket = bucket
                else:
                    # Create a new ranking entry with the bucket information
                    new_ranking = UserFeatureRanking(
                        user_id=user.id,
                        feature_id=feature.feature_id,
                        ranking_content=position,
                        bucket=bucket,  # Save the bucket
                        type_id=feature_type_entry.type_id,  # Speichere den Feature-Typ
                        llm_id=llm_entry.llm_id
                    )
                    db.session.add(new_ranking)

    db.session.commit()

    return jsonify({'status': 'Ranking saved successfully'}), 201



@data_blueprint.route('/admin/user_ranking_stats', methods=['GET'])
@admin_required
def get_user_ranking_stats():
    # Authorization handled by @admin_required decorator
    # Current user available in g.keycloak_user

    user_stats = []

    # Hole die Anzahl der gesamten Email Threads mit function_type_id = 1
    total_threads = db.session.query(EmailThread).filter_by(function_type_id=1).count()

    for user in User.query.all():
        ranked_threads_list = []
        unranked_threads_list = []
        total_ranked_threads = 0

        # Iteriere nur über die Email Threads mit function_type_id = 1
        for thread in EmailThread.query.filter_by(function_type_id=1).all():
            # Zähle alle Features in diesem Thread
            total_features_in_thread = db.session.query(Feature).filter_by(thread_id=thread.thread_id).count()

            # Zähle die Anzahl der vom Benutzer gerankten Features in diesem Thread
            ranked_features_count = db.session.query(UserFeatureRanking).join(Feature).filter(
                UserFeatureRanking.user_id == user.id,
                Feature.thread_id == thread.thread_id
            ).count()

            if ranked_features_count == total_features_in_thread and total_features_in_thread > 0:
                # Wenn alle Features eines Threads gerankt wurden, zähle den Thread als vollständig gerankt
                total_ranked_threads += 1
                ranked_threads_list.append({
                    'thread_id': thread.thread_id,
                    'chat_id': thread.chat_id,
                    'institut_id': thread.institut_id,
                    'subject': thread.subject,
                    'ranked_features_count': ranked_features_count,
                    'total_features_in_thread': total_features_in_thread
                })
            else:
                # Wenn der Benutzer diesen Thread noch nicht vollständig gerankt hat
                unranked_threads_list.append({
                    'thread_id': thread.thread_id,
                    'chat_id': thread.chat_id,
                    'institut_id': thread.institut_id,
                    'subject': thread.subject,
                    'ranked_features_count': ranked_features_count,
                    'total_features_in_thread': total_features_in_thread
                })

        # Füge die Statistiken für diesen Benutzer hinzu
        user_stats.append({
            'username': user.username,
            'ranked_threads_count': total_ranked_threads,  # Anzahl der vollständig gerankten Threads
            'total_threads': total_threads,  # Gesamtzahl der relevanten Threads (mit function_type_id = 1)
            'ranked_threads': ranked_threads_list,  # Liste der vollständig gerankten Threads
            'unranked_threads': unranked_threads_list  # Liste der unvollständig gerankten/unbearbeiteten Threads
        })

    return jsonify(user_stats), 200

