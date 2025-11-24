"""
Mail Rating Message Endpoints
Handles individual message ratings within email threads.
"""

import logging
from flask import jsonify, request, g
from sqlalchemy import func
from auth.decorators import authentik_required
from db.db import db
from db.tables import UserMessageRating
from .. import data_blueprint
from ..HelperFunctions import can_access_thread


@data_blueprint.route('/email_threads/message_ratings/<int:thread_id>', methods=['GET'])
@authentik_required
def get_email_thread_message_ratings(thread_id):
    """Get the most recent ratings for all messages in a thread"""
    try:
        # Authorization handled by @authentik_required decorator
        user = g.authentik_user

        # check if user can access thread
        if not can_access_thread(user.id, thread_id, 3):
            return jsonify({'error': 'Access denied'}), 401

        # Load Ratings of messages
        # Unterabfrage, um den neuesten Timestamp pro message_id zu ermitteln
        subquery = db.session.query(
            UserMessageRating.message_id,
            func.max(UserMessageRating.timestamp).label('latest_timestamp')
        ).filter_by(
            user_id=user.id,
            thread_id=thread_id
        ).group_by(
            UserMessageRating.message_id
        ).subquery()

        # Hauptabfrage, die den entsprechenden Datensatz für jede message_id mit dem neuesten Timestamp auswählt
        msg_ratings = db.session.query(UserMessageRating).join(
            subquery,
            (UserMessageRating.message_id == subquery.c.message_id) &
            (UserMessageRating.timestamp == subquery.c.latest_timestamp)
        ).filter(
            UserMessageRating.user_id == user.id,
            UserMessageRating.thread_id == thread_id
        ).all()

        rating_list = [
            {
                'message_id': msg_rating.message_id,
                'rating': msg_rating.rating,
            } for msg_rating in msg_ratings
        ]

        return jsonify(rating_list), 200

    except Exception as e:
        logging.error(e)
        return jsonify({"error": "Internal Server Error"}), 500


@data_blueprint.route('/email_threads/save_message_ratings/<int:thread_id>', methods=['POST'])
@authentik_required
def save_message_ratings(thread_id):
    """Save ratings for individual messages (thumbs up/down)"""
    try:
        # Authorization handled by @authentik_required decorator
        user = g.authentik_user

        # check if user can access thread
        if not can_access_thread(user.id, thread_id, 3):
            return jsonify({'error': 'Access denied'}), 401

        # retrieve data send from user
        data = request.get_json()
        message_ratings = data.get('message_ratings', [])

        # Loop through all message ratings send from user
        for rating_data in message_ratings:
            message_id = rating_data.get('message_id')
            rating = rating_data.get('rating')

            # check if the most recent message rating of this user is equal to the one send (avoiding duplicates in the db)
            existing_message_rating = (
                UserMessageRating.query
                .filter_by(user_id=user.id, thread_id=thread_id, message_id=message_id)
                .order_by(UserMessageRating.timestamp.desc())
                .first()
            )

            if existing_message_rating:
                # check if the new message rating is a duplicate of the most recent in db. If yes skip this message (applies for null values too)
                if existing_message_rating.rating == rating:
                    continue
            elif rating is None:  # if message didnt get ratet and no rating for this message existed in the db --> skip
                continue

            # either first rating for the message, or a change occured.
            # create and safe new entry into the db with current time stamp
            new_message_rating = UserMessageRating(
                user_id=user.id,
                thread_id=thread_id,
                message_id=message_id,
                rating=rating
            )
            db.session.add(new_message_rating)

        # commit all changes to the db
        db.session.commit()
        return jsonify({'status': 'Message ratings saved successfully'}), 201
    except Exception as e:
        logging.error(e)
        return jsonify({"error": "Internal Server Error"}), 500
