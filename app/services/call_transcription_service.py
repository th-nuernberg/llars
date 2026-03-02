"""
Call Transcription Service
Manages live transcript chunks, full transcript compilation, and post-call summarization.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from db.database import db
from db.models.messaging import MessagingCall

logger = logging.getLogger(__name__)


class CallTranscriptionService:
    """Service for managing call transcripts and AI summarization."""

    # In-memory buffer for live transcript chunks (keyed by room_name)
    _transcript_buffers: Dict[str, List[Dict]] = {}

    @classmethod
    def receive_transcript_chunk(
        cls,
        room_name: str,
        speaker: str,
        text: str,
        timestamp: float,
    ) -> Dict[str, Any]:
        """
        Receive a transcript chunk from the LiveKit agent.
        Stores in buffer and returns the chunk for Socket.IO broadcast.
        """
        chunk = {
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp,
        }

        if room_name not in cls._transcript_buffers:
            cls._transcript_buffers[room_name] = []

        cls._transcript_buffers[room_name].append(chunk)
        return chunk

    @classmethod
    def compile_transcript(cls, call_id: int) -> Optional[Dict[str, Any]]:
        """
        Compile all transcript chunks into a full transcript and save to DB.
        Called when a call ends.
        """
        call = MessagingCall.query.get(call_id)
        if not call or not call.livekit_room_name:
            return None

        room_name = call.livekit_room_name
        chunks = cls._transcript_buffers.pop(room_name, [])

        if not chunks:
            logger.info("No transcript chunks for call %d", call_id)
            return None

        # Sort by timestamp
        chunks.sort(key=lambda c: c.get("timestamp", 0))

        # Build full transcript
        transcript = {
            "call_id": call_id,
            "room_name": room_name,
            "chunks": chunks,
            "full_text": "\n".join(
                f"[{c['speaker']}]: {c['text']}" for c in chunks
            ),
            "compiled_at": datetime.utcnow().isoformat(),
        }

        call.transcript_json = transcript
        db.session.commit()

        logger.info(
            "Compiled transcript for call %d: %d chunks",
            call_id, len(chunks),
        )
        return transcript

    @classmethod
    def generate_call_summary(
        cls,
        call_id: int,
        model_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a summary of the call transcript using LLM.
        Auto-triggered when a call ends.
        """
        call = MessagingCall.query.get(call_id)
        if not call or not call.transcript_json:
            return None

        full_text = call.transcript_json.get("full_text", "")
        if not full_text or len(full_text.strip()) < 50:
            logger.info("Transcript too short for summarization (call %d)", call_id)
            return None

        try:
            from services.llm.llm_client_factory import LLMClientFactory

            client = LLMClientFactory.create(model_id=model_id)

            prompt = (
                "Summarize this call transcript concisely. "
                "Include key decisions, action items, and important discussion points.\n\n"
                f"{full_text}"
            )

            response = client.chat([{"role": "user", "content": prompt}])
            summary = response.get("content", "") if isinstance(response, dict) else str(response)

            call.summary_text = summary
            call.summary_model_id = model_id or "default"
            db.session.commit()

            logger.info("Generated summary for call %d", call_id)
            return summary

        except ImportError:
            logger.warning("LLMClientFactory not available for call summarization")
            return None
        except Exception as e:
            logger.error("Call summarization failed for call %d: %s", call_id, e)
            return None

    @classmethod
    def get_transcript(cls, call_id: int) -> Optional[Dict[str, Any]]:
        """Get the compiled transcript for a call."""
        call = MessagingCall.query.get(call_id)
        if not call:
            return None

        return {
            "call_id": call_id,
            "transcript": call.transcript_json,
            "summary": call.summary_text,
            "summary_model_id": call.summary_model_id,
        }
