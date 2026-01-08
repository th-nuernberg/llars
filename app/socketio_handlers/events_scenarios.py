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

logger = logging.getLogger(__name__)

SCENARIO_ROOM_PREFIX = "scenario_stats_"


def _scenario_room(scenario_id: int) -> str:
    return f"{SCENARIO_ROOM_PREFIX}{scenario_id}"


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

    logger.info("[Scenario Socket] Events registered")


def emit_scenario_stats_updated(socketio, scenario_id: int):
    """Emit scenario stats update to all subscribed clients."""
    try:
        payload = get_scenario_stats_payload(int(scenario_id))
        room = _scenario_room(scenario_id)
        socketio.emit("scenario:stats_updated", payload, room=room)
        logger.info("[Scenario Socket] Emitted stats update to %s", room)
    except Exception as exc:
        logger.error("[Scenario Socket] Error emitting stats update: %s", exc)
