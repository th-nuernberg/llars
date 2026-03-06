"""
Socket.IO events for real-time messaging.

Events:
    Client -> Server:
        - messaging:join             Join all user conversation rooms
        - messaging:join_chat        Join a specific conversation room
        - messaging:leave_chat       Leave a specific conversation room
        - messaging:send             Send a message
        - messaging:typing           Typing indicator
        - messaging:read             Mark messages as read
        - messaging:edit             Edit a message
        - messaging:delete           Delete a message

    Server -> Client:
        - messaging:new_message      New message in conversation
        - messaging:message_edited   Message was edited
        - messaging:message_deleted  Message was deleted
        - messaging:typing           User is typing
        - messaging:read_receipt     Read receipt update
        - messaging:unread_update    Unread count update
        - messaging:member_added     Member added to group
        - messaging:member_removed   Member removed from group
        - messaging:link_preview     Link preview metadata resolved
"""

import logging

from flask import request
from flask_socketio import emit, join_room, leave_room

from auth.oidc_validator import validate_token, get_username

logger = logging.getLogger(__name__)

CONV_ROOM_PREFIX = "messaging_conv_"
USER_ROOM_PREFIX = "messaging_user_"


def _require_authenticated_user() -> str | None:
    """Extract and validate the authenticated username from the JWT token.

    Returns the username on success, or None after emitting an error.
    Security: This MUST be used instead of trusting client-supplied usernames
    to prevent user impersonation.
    """
    token = str(request.args.get("token") or "").strip()
    payload = validate_token(token) if token else None
    if not payload:
        emit("messaging:error", {"error": "Unauthorized"})
        return None

    username = get_username(payload)
    if not username:
        emit("messaging:error", {"error": "Unauthorized"})
        return None

    return username


def _conv_room(conversation_id: int) -> str:
    return f"{CONV_ROOM_PREFIX}{conversation_id}"


def _user_room(username: str) -> str:
    return f"{USER_ROOM_PREFIX}{username}"


def _communication_disabled():
    """Check if communication is globally disabled. Returns True if disabled."""
    try:
        from services.system_settings_service import is_communication_enabled
        return not is_communication_enabled()
    except Exception:
        return False


def _fetch_link_previews(socketio_instance, message_id: int, conversation_id: int):
    """Background task: fetch link previews and emit update to conversation room."""
    try:
        from main import app

        with app.app_context():
            from services.link_preview_service import process_message_links
            previews = process_message_links(message_id)
            if previews:
                room = _conv_room(conversation_id)
                socketio_instance.emit("messaging:link_preview", {
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "link_previews": previews,
                }, room=room)
    except Exception as exc:
        logger.error("[Messaging Socket] Error fetching link previews for msg %s: %s", message_id, exc)


def register_messaging_events(socketio):
    """Register Socket.IO events for messaging."""

    @socketio.on("messaging:join")
    def handle_join(data=None):
        """Join all user's conversation rooms on connect."""
        try:
            if _communication_disabled():
                emit("messaging:error", {"error": "Communication is disabled"})
                return

            username = _require_authenticated_user()
            if not username:
                return

            # Join personal notification room
            join_room(_user_room(username))

            # Join all active conversation rooms
            from db.models.messaging import MessagingParticipant

            participants = MessagingParticipant.query.filter_by(
                username=username, is_active=True
            ).all()

            for p in participants:
                join_room(_conv_room(p.conversation_id))

            logger.info(
                "[Messaging Socket] Client %s joined %d rooms for user %s",
                request.sid, len(participants), username,
            )
            emit("messaging:joined", {"success": True, "rooms": len(participants)})

        except Exception as exc:
            logger.error("[Messaging Socket] Error joining rooms: %s", exc)
            emit("messaging:error", {"error": str(exc)})

    @socketio.on("messaging:join_chat")
    def handle_join_chat(data=None):
        """Join a specific conversation room."""
        try:
            if _communication_disabled():
                return
            if data is None:
                data = {}
            conversation_id = data.get("conversation_id")
            if not conversation_id:
                emit("messaging:error", {"error": "conversation_id is required"})
                return

            join_room(_conv_room(conversation_id))
            logger.info(
                "[Messaging Socket] Client %s joined conversation %s",
                request.sid, conversation_id,
            )
        except Exception as exc:
            logger.error("[Messaging Socket] Error joining chat: %s", exc)
            emit("messaging:error", {"error": str(exc)})

    @socketio.on("messaging:leave_chat")
    def handle_leave_chat(data=None):
        """Leave a specific conversation room."""
        try:
            if _communication_disabled():
                return
            if data is None:
                data = {}
            conversation_id = data.get("conversation_id")
            if not conversation_id:
                return
            leave_room(_conv_room(conversation_id))
        except Exception as exc:
            logger.error("[Messaging Socket] Error leaving chat: %s", exc)

    @socketio.on("messaging:send")
    def handle_send(data=None):
        """Handle sending a message via Socket.IO."""
        try:
            if _communication_disabled():
                emit("messaging:error", {"error": "Communication is disabled"})
                return
            if data is None:
                data = {}

            sender = _require_authenticated_user()
            if not sender:
                return

            conversation_id = data.get("conversation_id")
            content = data.get("content")

            if not conversation_id or not content:
                emit("messaging:error", {"error": "conversation_id and content are required"})
                return

            from services.messaging_service import MessagingService

            msg = MessagingService.send_message(
                conversation_id=conversation_id,
                sender=sender,
                content=content,
                message_type=data.get("message_type", "text"),
                reply_to_id=data.get("reply_to_id"),
                encryption_metadata=data.get("encryption_metadata"),
            )

            if not msg:
                emit("messaging:error", {"error": "Failed to send message"})
                return

            # Broadcast to conversation room
            room = _conv_room(conversation_id)
            socketio.emit("messaging:new_message", msg, room=room)

            # Fetch link previews in the background
            msg_id = msg.get("id")
            is_encrypted = msg.get("is_encrypted", False)
            if msg_id and not is_encrypted:
                socketio.start_background_task(
                    _fetch_link_previews, socketio, msg_id, conversation_id
                )

            # Send unread updates to other participants
            from db.models.messaging import MessagingParticipant

            participants = MessagingParticipant.query.filter(
                MessagingParticipant.conversation_id == conversation_id,
                MessagingParticipant.username != sender,
                MessagingParticipant.is_active == True,
            ).all()

            for p in participants:
                unread = MessagingService.get_unread_counts(p.username)
                socketio.emit("messaging:unread_update", unread, room=_user_room(p.username))

        except Exception as exc:
            logger.error("[Messaging Socket] Error sending message: %s", exc)
            emit("messaging:error", {"error": str(exc)})

    @socketio.on("messaging:typing")
    def handle_typing(data=None):
        """Broadcast typing indicator to conversation room."""
        try:
            if _communication_disabled():
                return
            if data is None:
                data = {}

            username = _require_authenticated_user()
            if not username:
                return

            conversation_id = data.get("conversation_id")
            is_typing = data.get("is_typing", True)

            if not conversation_id:
                return

            room = _conv_room(conversation_id)
            socketio.emit(
                "messaging:typing",
                {"username": username, "is_typing": is_typing, "conversation_id": conversation_id},
                room=room,
                include_self=False,
            )
        except Exception as exc:
            logger.error("[Messaging Socket] Error with typing indicator: %s", exc)

    @socketio.on("messaging:read")
    def handle_read(data=None):
        """Handle read receipt."""
        try:
            if _communication_disabled():
                return
            if data is None:
                data = {}

            username = _require_authenticated_user()
            if not username:
                return

            conversation_id = data.get("conversation_id")
            up_to_message_id = data.get("up_to_message_id")

            if not conversation_id or not up_to_message_id:
                return

            from services.messaging_service import MessagingService

            MessagingService.mark_as_read(conversation_id, username, up_to_message_id)

            room = _conv_room(conversation_id)
            socketio.emit(
                "messaging:read_receipt",
                {
                    "username": username,
                    "conversation_id": conversation_id,
                    "up_to_message_id": up_to_message_id,
                },
                room=room,
            )
        except Exception as exc:
            logger.error("[Messaging Socket] Error with read receipt: %s", exc)

    @socketio.on("messaging:edit")
    def handle_edit(data=None):
        """Handle message edit via Socket.IO."""
        try:
            if _communication_disabled():
                emit("messaging:error", {"error": "Communication is disabled"})
                return
            if data is None:
                data = {}

            username = _require_authenticated_user()
            if not username:
                return

            message_id = data.get("message_id")
            content = data.get("content")

            if not message_id or not content:
                emit("messaging:error", {"error": "message_id and content are required"})
                return

            from services.messaging_service import MessagingService

            msg = MessagingService.edit_message(message_id, username, content)
            if not msg:
                emit("messaging:error", {"error": "Failed to edit message"})
                return

            room = _conv_room(msg["conversation_id"])
            socketio.emit(
                "messaging:message_edited",
                {
                    "message_id": msg["id"],
                    "conversation_id": msg["conversation_id"],
                    "content": msg["content"],
                    "edited_at": msg["edited_at"],
                },
                room=room,
            )

            # Re-fetch link previews (URLs may have changed)
            if not msg.get("is_encrypted", False):
                socketio.start_background_task(
                    _fetch_link_previews, socketio, msg["id"], msg["conversation_id"]
                )

        except Exception as exc:
            logger.error("[Messaging Socket] Error editing message: %s", exc)
            emit("messaging:error", {"error": str(exc)})

    @socketio.on("messaging:delete")
    def handle_delete(data=None):
        """Handle message delete via Socket.IO."""
        try:
            if _communication_disabled():
                emit("messaging:error", {"error": "Communication is disabled"})
                return
            if data is None:
                data = {}

            username = _require_authenticated_user()
            if not username:
                return

            message_id = data.get("message_id")
            conversation_id = data.get("conversation_id")

            if not message_id:
                emit("messaging:error", {"error": "message_id is required"})
                return

            from services.messaging_service import MessagingService

            success = MessagingService.delete_message(message_id, username)
            if not success:
                emit("messaging:error", {"error": "Failed to delete message"})
                return

            if conversation_id:
                room = _conv_room(conversation_id)
                socketio.emit(
                    "messaging:message_deleted",
                    {"message_id": message_id, "conversation_id": conversation_id},
                    room=room,
                )
        except Exception as exc:
            logger.error("[Messaging Socket] Error deleting message: %s", exc)
            emit("messaging:error", {"error": str(exc)})

    # ── Reaction Events ─────────────────────────────────────────────

    @socketio.on("messaging:react")
    def handle_react(data=None):
        """Toggle an emoji reaction on a message."""
        try:
            if _communication_disabled():
                emit("messaging:error", {"error": "Communication is disabled"})
                return
            if data is None:
                data = {}

            username = _require_authenticated_user()
            if not username:
                return

            message_id = data.get("message_id")
            emoji = data.get("emoji")

            if not message_id or not emoji:
                emit("messaging:error", {"error": "message_id and emoji are required"})
                return

            from db.models.messaging import MessagingMessage, MessagingReaction
            from db import db as _db

            msg = MessagingMessage.query.get(message_id)
            if not msg:
                emit("messaging:error", {"error": "Message not found"})
                return

            # Toggle: remove if exists, create if not
            existing = MessagingReaction.query.filter_by(
                message_id=message_id, username=username, emoji=emoji,
            ).first()

            if existing:
                _db.session.delete(existing)
            else:
                reaction = MessagingReaction(
                    message_id=message_id, username=username, emoji=emoji,
                )
                _db.session.add(reaction)

            _db.session.commit()

            # Re-fetch aggregated reactions for the message
            all_reactions = MessagingReaction.query.filter_by(message_id=message_id).all()
            emoji_map = {}
            for r in all_reactions:
                if r.emoji not in emoji_map:
                    emoji_map[r.emoji] = []
                emoji_map[r.emoji].append(r.username)

            aggregated = [
                {"emoji": em, "count": len(unames), "usernames": unames}
                for em, unames in emoji_map.items()
            ]

            room = _conv_room(msg.conversation_id)
            socketio.emit("messaging:reaction_updated", {
                "message_id": message_id,
                "reactions": aggregated,
            }, room=room)

        except Exception as exc:
            logger.error("[Messaging Socket] Error toggling reaction: %s", exc)
            emit("messaging:error", {"error": str(exc)})

    # ── Call Events ────────────────────────────────────────────────

    @socketio.on("messaging:call_initiate")
    def handle_call_initiate(data=None):
        """Initiate a voice/video call."""
        try:
            if _communication_disabled():
                emit("messaging:error", {"error": "Communication is disabled"})
                return
            if data is None:
                data = {}

            initiated_by = _require_authenticated_user()
            if not initiated_by:
                return

            conversation_id = data.get("conversation_id")
            call_type = data.get("call_type", "voice")

            if not conversation_id:
                emit("messaging:error", {"error": "conversation_id is required"})
                return

            from services.call_service import CallService
            from db.models.messaging import MessagingParticipant

            # Get all active participants
            participants = MessagingParticipant.query.filter(
                MessagingParticipant.conversation_id == conversation_id,
                MessagingParticipant.is_active == True,
            ).all()
            usernames = [p.username for p in participants]

            result = CallService.create_call(
                conversation_id, call_type, initiated_by, usernames
            )

            if not result:
                emit("messaging:error", {"error": "Failed to create call"})
                return

            # Send token to initiator
            initiator_token = result.get("tokens", {}).get(initiated_by)
            emit("messaging:call_token", {
                "call_id": result["id"],
                "token": initiator_token,
                "livekit_url": result.get("livekit_url"),
                "room_name": result.get("livekit_room_name"),
            })

            # Send incoming call to other participants
            for uname in usernames:
                if uname != initiated_by:
                    participant_token = result.get("tokens", {}).get(uname)
                    socketio.emit("messaging:call_incoming", {
                        "call_id": result["id"],
                        "conversation_id": conversation_id,
                        "call_type": call_type,
                        "initiated_by": initiated_by,
                        "token": participant_token,
                        "livekit_url": result.get("livekit_url"),
                    }, room=_user_room(uname))

        except Exception as exc:
            logger.error("[Messaging Socket] Error initiating call: %s", exc)
            emit("messaging:error", {"error": str(exc)})

    @socketio.on("messaging:call_accept")
    def handle_call_accept(data=None):
        """Accept an incoming call."""
        try:
            if _communication_disabled():
                return

            username = _require_authenticated_user()
            if not username:
                return

            if data is None:
                data = {}
            call_id = data.get("call_id")

            if not call_id:
                return

            from services.call_service import CallService

            result = CallService.accept_call(call_id, username)
            if result:
                conv_id = result.get("conversation_id")
                room = _conv_room(conv_id) if conv_id else None
                if room:
                    socketio.emit("messaging:call_accepted", {
                        "call_id": call_id,
                        "username": username,
                    }, room=room)

        except Exception as exc:
            logger.error("[Messaging Socket] Error accepting call: %s", exc)

    @socketio.on("messaging:call_decline")
    def handle_call_decline(data=None):
        """Decline an incoming call."""
        try:
            if _communication_disabled():
                return

            username = _require_authenticated_user()
            if not username:
                return

            if data is None:
                data = {}
            call_id = data.get("call_id")

            if not call_id:
                return

            from services.call_service import CallService

            CallService.decline_call(call_id, username)

        except Exception as exc:
            logger.error("[Messaging Socket] Error declining call: %s", exc)

    @socketio.on("messaging:call_end")
    def handle_call_end(data=None):
        """End an active call."""
        try:
            if _communication_disabled():
                return

            username = _require_authenticated_user()
            if not username:
                return

            if data is None:
                data = {}
            call_id = data.get("call_id")
            conversation_id = data.get("conversation_id")

            if not call_id:
                return

            from services.call_service import CallService

            result = CallService.end_call(call_id, username)
            if result and conversation_id:
                room = _conv_room(conversation_id)
                socketio.emit("messaging:call_ended", {
                    "call_id": call_id,
                    "duration": result.get("duration_seconds"),
                }, room=room)

        except Exception as exc:
            logger.error("[Messaging Socket] Error ending call: %s", exc)
