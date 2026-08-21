"""
Socket.IO events for scenario statistics updates.

Events:
    Client → Server:
        - scenario:subscribe: Subscribe to scenario stats updates
        - scenario:unsubscribe: Unsubscribe from scenario stats updates

    Server → Client:
        - scenario:stats: Initial stats payload after subscribing
        - scenario:stats_updated: Stats payload updated
"""

import logging

from flask import request
from flask_socketio import emit, join_room, leave_room

from services.scenario_stats_service import get_scenario_stats_payload
from socketio_handlers.socket_auth import socket_user, socket_authorize
from auth.access_control import require_scenario_membership

logger = logging.getLogger(__name__)

SCENARIO_ROOM_PREFIX = "scenario_stats_"
# Personal room, one per user. Carries "you were just given access to a
# scenario" pushes so the Evaluation hub can surface a new study live instead
# of only on the next page load.
INVITE_ROOM_PREFIX = "scenario_invites_"


def _scenario_room(scenario_id: int) -> str:
    return f"{SCENARIO_ROOM_PREFIX}{scenario_id}"


def _invite_room(username: str) -> str:
    return f"{INVITE_ROOM_PREFIX}{username}"


def register_scenarios_events(socketio):
    """Register Socket.IO events for scenario stats updates."""

    @socketio.on("scenario:subscribe")
    def handle_subscribe_scenario(data=None):
        try:
            if data is None:
                data = {}

            scenario_id = data.get("scenario_id")
            if not scenario_id:
                emit("scenario:error", {"error": "scenario_id is required"})
                return

            # AuthN + AuthZ: scenario stats (evaluator names, votes, progress) are
            # sensitive, so only scenario members (or admins) may subscribe. Uses the
            # SAME check as the HTTP routes via the shared socket_auth helpers, so
            # socket authz can never diverge from HTTP authz.
            user = socket_user("scenario:error")
            if user is None:
                return
            try:
                scenario_id = int(scenario_id)
            except (TypeError, ValueError):
                emit("scenario:error", {"error": "Invalid scenario_id"})
                return
            if not socket_authorize(
                require_scenario_membership, scenario_id, user, error_event="scenario:error"
            ):
                return

            room = _scenario_room(scenario_id)
            join_room(room)

            logger.info(
                "[Scenario Socket] Client %s subscribed to scenario stats (scenario: %s)",
                request.sid,
                scenario_id,
            )

            payload = get_scenario_stats_payload(int(scenario_id))
            emit("scenario:stats", payload)
            emit("scenario:subscribed", {"room": room, "scenario_id": scenario_id})

        except Exception as exc:
            logger.error("[Scenario Socket] Error subscribing to scenario stats: %s", exc)
            emit("scenario:error", {"error": str(exc)})

    @socketio.on("scenario:unsubscribe")
    def handle_unsubscribe_scenario(data=None):
        try:
            if data is None:
                data = {}

            scenario_id = data.get("scenario_id")
            if not scenario_id:
                emit("scenario:error", {"error": "scenario_id is required"})
                return

            room = _scenario_room(scenario_id)
            leave_room(room)

            logger.info(
                "[Scenario Socket] Client %s unsubscribed from scenario stats (scenario: %s)",
                request.sid,
                scenario_id,
            )

        except Exception as exc:
            logger.error("[Scenario Socket] Error unsubscribing from scenario stats: %s", exc)

    @socketio.on("scenario:subscribe_invites")
    def handle_subscribe_invites(_data=None):
        """Join the caller's own invite room.

        No resource authorization needed — and deliberately no room name taken
        from the payload: the room is derived from the authenticated identity,
        so a client cannot subscribe to somebody else's invitations.
        """
        try:
            user = socket_user("scenario:error")
            if user is None:
                return

            join_room(_invite_room(user.username))
            logger.info(
                "[Scenario Socket] %s subscribed to scenario invites (sid=%s)",
                user.username,
                request.sid,
            )
        except Exception as exc:
            logger.error("[Scenario Socket] Error subscribing to invites: %s", exc)

    @socketio.on("scenario:unsubscribe_invites")
    def handle_unsubscribe_invites(_data=None):
        try:
            user = socket_user("scenario:error")
            if user is None:
                return
            leave_room(_invite_room(user.username))
        except Exception as exc:
            logger.error("[Scenario Socket] Error unsubscribing from invites: %s", exc)

    logger.info("[Scenario Socket] Events registered")


def emit_scenario_access_granted(socketio, usernames, scenario_payload):
    """Push a freshly granted scenario to each recipient's personal room.

    Called after new members are committed (scenario_manager_api.add_scenario_users)
    so a rater sitting on the Evaluation hub sees the study appear immediately
    rather than after a manual reload.

    Best-effort by design: a socket failure must never roll back or fail the
    HTTP request that granted the access — the scenario shows up on the next
    fetch regardless.
    """
    if not socketio or not usernames or not scenario_payload:
        return

    for username in usernames:
        if not username:
            continue
        try:
            socketio.emit(
                "scenario:access_granted",
                {"scenario": scenario_payload},
                room=_invite_room(username),
            )
        except Exception as exc:
            logger.error(
                "[Scenario Socket] Could not notify %s about scenario access: %s",
                username,
                exc,
            )


def emit_scenario_stats_updated(socketio, scenario_id: int):
    """Mark stats as dirty and trigger background recompute.

    The background thread will push updated stats via Socket.IO when done.
    This avoids blocking the calling thread with expensive stats computation.
    """
    try:
        from services.scenario_stats_cache_service import mark_dirty
        mark_dirty(int(scenario_id))
        logger.info("[Scenario Socket] Marked stats dirty for scenario %s (background recompute triggered)", scenario_id)
    except Exception as exc:
        logger.error("[Scenario Socket] Error marking stats dirty: %s", exc)
