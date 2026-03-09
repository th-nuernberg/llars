"""
Call Service
Manages voice/video calls via LiveKit.
Handles room creation, token generation, call lifecycle, and history.
"""

import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from db.database import db
from db.models.messaging import (
    CallStatus,
    CallType,
    MessagingCall,
    MessagingCallParticipant,
    MessagingConversation,
    MessagingMessage,
    MessagingParticipant,
    MessageType,
)

logger = logging.getLogger(__name__)


class CallService:
    """Service for managing voice/video calls via LiveKit."""

    @staticmethod
    def _get_livekit_api():
        """Get LiveKit API client. Returns None if not configured."""
        try:
            from livekit.api import LiveKitAPI

            api_url = os.getenv("LIVEKIT_API_URL", "http://livekit-service:7880")
            api_key = os.getenv("LIVEKIT_API_KEY", "")
            api_secret = os.getenv("LIVEKIT_API_SECRET", "")

            if not api_key or not api_secret:
                logger.warning("LiveKit API key/secret not configured")
                return None

            return LiveKitAPI(api_url, api_key, api_secret)
        except ImportError:
            logger.warning("livekit-server-sdk not installed")
            return None

    @staticmethod
    def _generate_token(room_name: str, username: str, call_type: str) -> Optional[str]:
        """Generate a LiveKit access token for a participant."""
        try:
            from livekit.api import AccessToken, VideoGrant

            api_key = os.getenv("LIVEKIT_API_KEY", "")
            api_secret = os.getenv("LIVEKIT_API_SECRET", "")

            if not api_key or not api_secret:
                return None

            grant = VideoGrant(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )

            token = AccessToken(api_key, api_secret)
            token.identity = username
            token.name = username
            token.add_grant(grant)
            token.ttl = 86400  # 24 hours

            return token.to_jwt()
        except ImportError:
            logger.warning("livekit-server-sdk not installed, generating placeholder token")
            return f"placeholder-token-{room_name}-{username}"
        except Exception as e:
            logger.error("Failed to generate LiveKit token: %s", e)
            return None

    @staticmethod
    def create_call(
        conversation_id: int,
        call_type: str,
        initiated_by: str,
        participant_usernames: List[str],
    ) -> Optional[Dict[str, Any]]:
        """Create a call, generate LiveKit room and tokens."""
        conv = MessagingConversation.query.get(conversation_id)
        if not conv:
            return None

        # Verify initiator is a participant
        initiator = MessagingParticipant.query.filter_by(
            conversation_id=conversation_id, username=initiated_by, is_active=True
        ).first()
        if not initiator:
            return None

        room_name = f"llars-call-{conversation_id}-{uuid.uuid4().hex[:8]}"

        call = MessagingCall(
            conversation_id=conversation_id,
            call_type=CallType(call_type),
            status=CallStatus.ringing,
            initiated_by=initiated_by,
            livekit_room_name=room_name,
        )
        db.session.add(call)
        db.session.flush()

        # Add participants
        tokens = {}
        for uname in participant_usernames:
            db.session.add(
                MessagingCallParticipant(call_id=call.id, username=uname)
            )
            token = CallService._generate_token(room_name, uname, call_type)
            if token:
                tokens[uname] = token

        # System message for call event
        db.session.add(
            MessagingMessage(
                conversation_id=conversation_id,
                sender_username=initiated_by,
                content=f"{initiated_by} started a {call_type} call",
                message_type=MessageType.call_event,
            )
        )

        db.session.commit()
        logger.info(
            "Call %d created in conversation %d by %s (room: %s)",
            call.id, conversation_id, initiated_by, room_name,
        )

        livekit_url = os.getenv("LIVEKIT_PUBLIC_URL", "ws://localhost:7881")

        result = call.to_dict()
        result["tokens"] = tokens
        result["livekit_url"] = livekit_url
        return result

    @staticmethod
    def end_call(call_id: int, ended_by: str) -> Optional[Dict[str, Any]]:
        """End an active call."""
        call = MessagingCall.query.get(call_id)
        if not call or call.status == CallStatus.ended:
            return None

        call.status = CallStatus.ended
        call.ended_at = datetime.utcnow()

        if call.started_at:
            call.duration_seconds = int(
                (call.ended_at - call.started_at).total_seconds()
            )

        db.session.commit()
        logger.info("Call %d ended by %s (duration: %ss)", call_id, ended_by, call.duration_seconds)
        return call.to_dict()

    @staticmethod
    def accept_call(call_id: int, username: str) -> Optional[Dict[str, Any]]:
        """Accept an incoming call."""
        call = MessagingCall.query.get(call_id)
        if not call or call.status not in (CallStatus.ringing, CallStatus.active):
            return None

        if call.status == CallStatus.ringing:
            call.status = CallStatus.active
            call.started_at = datetime.utcnow()

        # Update participant join time
        participant = MessagingCallParticipant.query.filter_by(
            call_id=call_id, username=username
        ).first()
        if participant:
            participant.joined_at = datetime.utcnow()

        db.session.commit()

        token = CallService._generate_token(
            call.livekit_room_name, username, call.call_type.value
        )
        livekit_url = os.getenv("LIVEKIT_PUBLIC_URL", "ws://localhost:7881")

        result = call.to_dict()
        result["token"] = token
        result["livekit_url"] = livekit_url
        return result

    @staticmethod
    def decline_call(call_id: int, username: str) -> bool:
        """Decline an incoming call."""
        call = MessagingCall.query.get(call_id)
        if not call or call.status != CallStatus.ringing:
            return False

        # If all participants decline, mark as missed
        participants = MessagingCallParticipant.query.filter_by(call_id=call_id).all()
        other_participants = [p for p in participants if p.username != call.initiated_by]

        if len(other_participants) <= 1:
            call.status = CallStatus.declined
            call.ended_at = datetime.utcnow()
        else:
            # Remove this participant
            participant = next((p for p in participants if p.username == username), None)
            if participant:
                participant.left_at = datetime.utcnow()

        db.session.commit()
        return True

    @staticmethod
    def generate_join_token(call_id: int, username: str) -> Optional[Dict[str, str]]:
        """Generate a token for a late joiner."""
        call = MessagingCall.query.get(call_id)
        if not call or call.status != CallStatus.active:
            return None

        token = CallService._generate_token(
            call.livekit_room_name, username, call.call_type.value
        )
        livekit_url = os.getenv("LIVEKIT_PUBLIC_URL", "ws://localhost:7881")

        return {
            "token": token,
            "livekit_url": livekit_url,
            "room_name": call.livekit_room_name,
        }

    @staticmethod
    def get_call_history(
        conversation_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get call history for a conversation."""
        calls = (
            MessagingCall.query.filter_by(conversation_id=conversation_id)
            .order_by(MessagingCall.created_at.desc())
            .limit(limit)
            .all()
        )
        return [c.to_dict() for c in calls]
