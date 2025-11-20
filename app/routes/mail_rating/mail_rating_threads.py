"""
Mail Rating Thread Endpoints
Handles thread retrieval and listing for mail rating functionality.
"""

import logging
from flask import jsonify, g
from auth.decorators import keycloak_required
from db.db import db
from db.tables import (EmailThread, Message, FeatureFunctionType,
                       UserMailHistoryRating, ProgressionStatus)
from .. import data_blueprint
from ..HelperFunctions import get_user_threads


@data_blueprint.route('/email_threads/generations/<int:thread_id>', methods=['GET'])
@keycloak_required
def get_email_thread_details(thread_id):
    """Get detailed message content for an email thread"""
    try:
        # Authorization handled by @keycloak_required decorator
        user = g.keycloak_user

        # Hole den E-Mail-Thread basierend auf der thread_id
        email_thread = EmailThread.query.filter_by(thread_id=thread_id).first()
        if not email_thread:
            return jsonify({'error': 'Email thread not found'}), 404

        # Hole alle Nachrichten in diesem E-Mail-Thread
        messages = Message.query.filter_by(thread_id=email_thread.thread_id).all()

        if not messages:
            return jsonify({'error': 'No messages found for this thread'}), 404

        # Erstelle eine Liste von Nachrichten, die zurückgegeben werden soll
        messages_data = [
            {
                'message_id': msg.message_id,
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            } for msg in messages
        ]

        return jsonify({'messages': messages_data}), 200
    except Exception as e:
        logging.error(e)
        return jsonify({"error": "Internal Server Error"}), 500


@data_blueprint.route('/email_threads/mailhistory_ratings', methods=['GET'])
@keycloak_required
def list_email_threads_for_mail_ratings():
    """Get list of all threads assigned to user for mail rating with progression status"""
    try:
        # Authorization handled by @keycloak_required decorator
        user = g.keycloak_user

        # get function type
        mail_rating_function_type = FeatureFunctionType.query.filter_by(name='mail_rating').first().function_type_id
        if not mail_rating_function_type:
            return jsonify({'error': 'Mail Rating function type not found'}), 500

        # get all threads the user is supposed to see
        accessible_threads = get_user_threads(user.id, mail_rating_function_type)

        threads_list = []  # this is for returning
        seen_threads = set()  # Avoiding duplicate Threads
        for thread in accessible_threads:
            # check for duplicates
            if thread.thread_id in seen_threads:
                continue
            seen_threads.add(thread.thread_id)

            # Check for existing UserMailHistoryRating for the user and thread
            mail_rating = (
                db.session.query(UserMailHistoryRating)
                .filter_by(user_id=user.id, thread_id=thread.thread_id).order_by(
                UserMailHistoryRating.timestamp.desc()).first()
            )

            # Determine progression status
            status = mail_rating.status if mail_rating else ProgressionStatus.NOT_STARTED

            # Append thread details to the result list
            threads_list.append({
                'thread_id': thread.thread_id,
                'chat_id': thread.chat_id,
                'institut_id': thread.institut_id,
                'subject': thread.subject,
                'sender': thread.sender,
                'progression_status': status.value,
            })

        return jsonify({'threads': threads_list}), 200

    except Exception as e:
        logging.exception(e)
        return jsonify({'error': str(e)}), 500
