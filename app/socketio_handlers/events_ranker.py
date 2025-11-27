"""
Socket.IO events for Ranker Statistics real-time updates.

Events:
    Client → Server:
        - ranker:subscribe: Subscribe to ranking statistics updates
        - ranker:unsubscribe: Unsubscribe from ranking statistics updates

    Server → Client:
        - ranker:stats_list: Initial statistics after subscribing
        - ranker:stats_updated: Statistics have been updated
"""

import logging
from flask_socketio import emit, join_room, leave_room
from flask import request

logger = logging.getLogger(__name__)

# Room name pattern for ranker subscriptions (per scenario)
RANKER_ROOM_PREFIX = "ranker_stats_"
RANKER_GLOBAL_ROOM = "ranker_stats_global"


def get_ranker_room(scenario_id: int = None) -> str:
    """Get room name for ranker statistics updates."""
    if scenario_id:
        return f"{RANKER_ROOM_PREFIX}{scenario_id}"
    return RANKER_GLOBAL_ROOM


def register_ranker_events(socketio):
    """Register Socket.IO events for ranker real-time updates."""

    @socketio.on('ranker:subscribe')
    def handle_subscribe_ranker(data=None):
        """
        Subscribe to ranking statistics updates.

        Expected data:
            - scenario_id: int (optional) - Subscribe to specific scenario stats
        """
        try:
            if data is None:
                data = {}

            scenario_id = data.get('scenario_id')
            room = get_ranker_room(scenario_id)
            join_room(room)

            logger.info(f"[Ranker Socket] Client {request.sid} subscribed to ranker stats (scenario: {scenario_id})")

            # Fetch and send current stats
            stats = _fetch_user_ranking_stats(scenario_id)

            emit('ranker:stats_list', {'stats': stats, 'scenario_id': scenario_id})
            emit('ranker:subscribed', {'room': room, 'scenario_id': scenario_id})

        except Exception as e:
            logger.error(f"[Ranker Socket] Error subscribing to ranker stats: {e}")
            emit('ranker:error', {'error': str(e)})

    @socketio.on('ranker:unsubscribe')
    def handle_unsubscribe_ranker(data=None):
        """Unsubscribe from ranking statistics updates."""
        try:
            if data is None:
                data = {}

            scenario_id = data.get('scenario_id')
            room = get_ranker_room(scenario_id)
            leave_room(room)

            logger.info(f"[Ranker Socket] Client {request.sid} unsubscribed from ranker stats (scenario: {scenario_id})")

        except Exception as e:
            logger.error(f"[Ranker Socket] Error unsubscribing from ranker stats: {e}")

    logger.info("[Ranker Socket] Events registered")


def _fetch_user_ranking_stats(scenario_id: int = None) -> list:
    """
    Fetch user ranking statistics from the database.

    Args:
        scenario_id: Optional scenario ID to filter stats

    Returns:
        List of user statistics dictionaries
    """
    from db.db import db
    from db.tables import User, EmailThread, Feature, UserFeatureRanking

    user_stats = []

    # Get total threads with function_type_id = 1 (Ranking)
    total_threads = db.session.query(EmailThread).filter_by(function_type_id=1).count()

    for user in User.query.all():
        ranked_threads_list = []
        unranked_threads_list = []
        total_ranked_threads = 0

        # Iterate over email threads with function_type_id = 1
        for thread in EmailThread.query.filter_by(function_type_id=1).all():
            total_features_in_thread = db.session.query(Feature).filter_by(thread_id=thread.thread_id).count()

            ranked_features_count = db.session.query(UserFeatureRanking).join(Feature).filter(
                UserFeatureRanking.user_id == user.id,
                Feature.thread_id == thread.thread_id
            ).count()

            thread_data = {
                'thread_id': thread.thread_id,
                'chat_id': thread.chat_id,
                'institut_id': thread.institut_id,
                'subject': thread.subject,
                'ranked_features_count': ranked_features_count,
                'total_features_in_thread': total_features_in_thread
            }

            if ranked_features_count == total_features_in_thread and total_features_in_thread > 0:
                total_ranked_threads += 1
                ranked_threads_list.append(thread_data)
            else:
                unranked_threads_list.append(thread_data)

        user_stats.append({
            'username': user.username,
            'ranked_threads_count': total_ranked_threads,
            'total_threads': total_threads,
            'ranked_threads': ranked_threads_list,
            'unranked_threads': unranked_threads_list
        })

    return user_stats


def emit_ranker_stats_updated(socketio, scenario_id: int = None, stats: list = None):
    """
    Emit ranking statistics update to all subscribed clients.

    Args:
        socketio: Flask-SocketIO instance
        scenario_id: Optional scenario ID for targeted updates
        stats: Optional pre-fetched stats (will fetch if None)
    """
    try:
        if stats is None:
            stats = _fetch_user_ranking_stats(scenario_id)

        room = get_ranker_room(scenario_id)
        socketio.emit('ranker:stats_updated', {'stats': stats, 'scenario_id': scenario_id}, room=room)
        logger.info(f"[Ranker Socket] Emitted stats update to {room}")

    except Exception as e:
        logger.error(f"[Ranker Socket] Error emitting stats update: {e}")


def emit_ranking_saved(socketio, user_id: int, thread_id: int, scenario_id: int = None):
    """
    Emit notification when a user saves a ranking.
    Triggers stats update for all subscribers.

    Args:
        socketio: Flask-SocketIO instance
        user_id: The ID of the user who saved the ranking
        thread_id: The ID of the thread that was ranked
        scenario_id: Optional scenario ID
    """
    try:
        # Emit full stats update
        emit_ranker_stats_updated(socketio, scenario_id)

        # Also emit a specific event for the ranking saved
        room = get_ranker_room(scenario_id)
        socketio.emit('ranker:ranking_saved', {
            'user_id': user_id,
            'thread_id': thread_id
        }, room=room)

        logger.info(f"[Ranker Socket] Emitted ranking saved by user {user_id} for thread {thread_id}")

    except Exception as e:
        logger.error(f"[Ranker Socket] Error emitting ranking saved: {e}")
