"""
Anonymization Pipeline Worker.

Processes NER/pseudonymization for conversations in a background thread,
emitting Socket.IO events for real-time progress tracking.

Architecture:
    AnonymizationWorker
        ├── Fetches pending messages for a conversation
        ├── Runs NER via AnonymizeService.pseudonymize()
        ├── Stores entities in DB
        ├── Emits Socket.IO progress events per message
        └── Handles errors gracefully

Usage:
    from services.anonymize.anonymization_worker import AnonymizationWorker

    worker = AnonymizationWorker(
        conversation_ids=[1, 2, 3],
        user_id=42,
        socketio=socketio,
        force=False,
    )
    worker.run()  # Blocks until all conversations processed
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.anonymize.socket_rooms import (
    ANONYMIZATION_OVERVIEW_ROOM,
    anonymization_conversation_room,
)

logger = logging.getLogger(__name__)


class AnonymizationWorker:
    """Background worker for NER processing of anonymization conversations."""

    def __init__(
        self,
        conversation_ids: List[int],
        user_id: int,
        socketio: Any = None,
        force: bool = False,
    ):
        self.conversation_ids = conversation_ids
        self.user_id = user_id
        self.socketio = socketio
        self.force = force

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Process all queued conversations sequentially."""
        total = len(self.conversation_ids)
        completed = 0
        failed = 0

        self._emit_event("anonymization:batch:started", {
            "conversation_ids": self.conversation_ids,
            "total": total,
        })

        for conversation_id in self.conversation_ids:
            try:
                self._process_conversation(conversation_id, completed, total)
                completed += 1
            except Exception as exc:
                logger.exception(
                    "[AnonymizationWorker] Failed to process conversation %s: %s",
                    conversation_id, exc,
                )
                failed += 1
                self._mark_conversation_error(conversation_id, str(exc))
                self._emit_event("anonymization:conversation:ner_failed", {
                    "conversation_id": conversation_id,
                    "error": str(exc),
                })

            self._emit_event("anonymization:batch:progress", {
                "completed": completed,
                "failed": failed,
                "total": total,
                "percent": round((completed + failed) / total * 100) if total else 100,
            })

        self._emit_event("anonymization:batch:completed", {
            "completed": completed,
            "failed": failed,
            "total": total,
        })

    @classmethod
    def start_async(
        cls,
        conversation_ids: List[int],
        user_id: int,
        socketio: Any = None,
        force: bool = False,
    ) -> None:
        """Start the worker in a background daemon thread."""
        def _run():
            try:
                from main import app
                with app.app_context():
                    worker = cls(
                        conversation_ids=conversation_ids,
                        user_id=user_id,
                        socketio=socketio,
                        force=force,
                    )
                    worker.run()
            except Exception as exc:
                logger.exception("[AnonymizationWorker] Async run failed: %s", exc)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _process_conversation(self, conversation_id: int, batch_index: int, batch_total: int) -> None:
        """Run NER for a single conversation with per-message progress events."""
        from db.database import db
        from db.models import (
            AnonymizationConversation,
            AnonymizationEntity,
        )
        from services.anonymize.anonymize_service import AnonymizeService

        conversation = AnonymizationConversation.query.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        messages = sorted(list(conversation.messages or []), key=lambda m: m.message_number)
        if not messages:
            raise ValueError(f"Conversation {conversation_id} has no messages")

        # Skip manually edited check if force
        if not self.force and any(msg.is_manually_edited for msg in messages):
            raise ValueError("Contains manually edited messages. Use force=true.")

        # Set status to in_progress
        conversation.status = "in_progress"
        conversation.error_message = None
        conversation.updated_by = self.user_id
        conversation.updated_at = datetime.utcnow()
        db.session.flush()

        self._emit_conversation_event("anonymization:conversation:ner_started", {
            "conversation_id": conversation_id,
            "total_messages": len(messages),
            "title": conversation.title,
        })

        # Clear old entities
        for message in messages:
            for entity in list(message.entities):
                db.session.delete(entity)
            if self.force:
                for version in list(message.versions):
                    db.session.delete(version)
            message.anonymized_content = message.original_content or ""
            message.current_version = 1
            message.is_manually_edited = False

        db.session.flush()

        # Process messages
        conversation_entity_map: Dict[str, Dict[str, Any]] = {}
        date_shift_days: Optional[int] = None
        total_entities = 0
        errors: List[str] = []
        total_messages = len(messages)

        for idx, message in enumerate(messages, start=1):
            text = (message.original_content or "").strip()
            if not text:
                message.anonymized_content = message.original_content or ""
                self._emit_conversation_event("anonymization:conversation:ner_progress", {
                    "conversation_id": conversation_id,
                    "message_number": idx,
                    "total_messages": total_messages,
                    "percent": round(idx / total_messages * 100),
                })
                continue

            try:
                result = AnonymizeService.pseudonymize(
                    text=message.original_content,
                    engine="offline",
                    group_overrides=conversation_entity_map,
                    date_shift_days=date_shift_days,
                    action=None,
                    name_origin=None,
                    name_count=None,
                )

                # Keep replacements consistent across conversation
                for group in result.get("groups", []):
                    group_id = group.get("group_id") or group.get("group_key")
                    if group_id and group_id not in conversation_entity_map:
                        conversation_entity_map[group_id] = {
                            "replacement": group.get("replacement"),
                            "mode": group.get("mode"),
                        }

                if date_shift_days is None:
                    date_shift_days = result.get("date_shift_days")

                message.anonymized_content = result.get("output_text", message.original_content)
                message.updated_at = datetime.utcnow()

                # Build entity records
                groups_by_id: Dict[str, Dict[str, Any]] = {}
                for group in result.get("groups", []):
                    gid = group.get("group_id") or group.get("group_key")
                    if gid:
                        groups_by_id[gid] = group

                for entity in result.get("entities", []):
                    entity_record = self._build_entity_record(
                        message_id=message.id,
                        entity=entity,
                        groups_by_id=groups_by_id,
                    )
                    if entity_record:
                        db.session.add(entity_record)
                        total_entities += 1

            except Exception as exc:
                logger.exception(
                    "NER failed for conversation=%s message=%s",
                    conversation_id, message.id,
                )
                errors.append(f"message {message.message_number}: {exc}")
                message.anonymized_content = message.original_content or ""

            self._emit_conversation_event("anonymization:conversation:ner_progress", {
                "conversation_id": conversation_id,
                "message_number": idx,
                "total_messages": total_messages,
                "percent": round(idx / total_messages * 100),
                "entities_found": total_entities,
            })

        # Finalize
        conversation.message_count = total_messages
        conversation.entity_count = total_entities
        conversation.updated_by = self.user_id
        conversation.updated_at = datetime.utcnow()

        if errors:
            conversation.status = "error"
            conversation.error_message = "; ".join(errors[:3])
        else:
            conversation.status = "pending"
            conversation.error_message = None

        db.session.commit()

        self._emit_conversation_event("anonymization:conversation:ner_completed", {
            "conversation_id": conversation_id,
            "entity_count": total_entities,
            "message_count": total_messages,
            "status": conversation.status,
            "errors": errors[:3],
        })

    def _mark_conversation_error(self, conversation_id: int, error_msg: str) -> None:
        """Mark conversation as error status."""
        try:
            from db.database import db
            from db.models import AnonymizationConversation

            conversation = AnonymizationConversation.query.get(conversation_id)
            if conversation:
                conversation.status = "error"
                conversation.error_message = error_msg[:500]
                conversation.updated_at = datetime.utcnow()
                db.session.commit()
        except Exception:
            logger.exception("Could not mark conversation %s as error", conversation_id)

    # ------------------------------------------------------------------
    # Entity building (mirrors AnonymizationPipelineService logic)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_entity_record(
        message_id: int,
        entity: Dict[str, Any],
        groups_by_id: Dict[str, Dict[str, Any]],
    ) -> Optional[Any]:
        from db.models import AnonymizationEntity

        ENTITY_LABELS = {"PER", "LOC", "ORG", "DATE", "AGE", "PHONE", "MAIL", "AHV", "PLZ", "MISC"}
        ENTITY_LABEL_ALIASES = {
            "EMAIL": "MAIL", "E-MAIL": "MAIL", "PERSON": "PER", "NAME": "PER",
            "LOCATION": "LOC", "PLACE": "LOC", "ORGANISATION": "ORG", "ORGANIZATION": "ORG",
            "ZIP": "PLZ", "POSTAL_CODE": "PLZ", "POSTCODE": "PLZ", "SSN": "AHV",
            "SVN": "MISC", "IBAN": "MISC", "URL": "MISC", "TIME": "MISC", "STREET": "MISC",
        }

        group_key = entity.get("group_id") or entity.get("group_key")
        group_data = groups_by_id.get(group_key, {}) if group_key else {}

        def safe_int(v, fallback=0):
            try:
                return int(v)
            except (TypeError, ValueError):
                return fallback

        start_pos = safe_int(entity.get("output_start"), safe_int(entity.get("start"), 0))
        end_pos = safe_int(entity.get("output_end"), safe_int(entity.get("end"), start_pos))

        if end_pos <= start_pos:
            start_pos = safe_int(entity.get("start"), 0)
            end_pos = safe_int(entity.get("end"), start_pos)

        if end_pos <= start_pos:
            return None

        raw_label = str(entity.get("label") or "MISC").strip().upper()
        label = ENTITY_LABEL_ALIASES.get(raw_label, raw_label)
        if label not in ENTITY_LABELS:
            label = "MISC"

        return AnonymizationEntity(
            message_id=message_id,
            label=label,
            original_text=str(entity.get("text") or entity.get("original_text") or "")[:512],
            replacement_text=str(entity.get("replacement") or entity.get("replacement_text") or "")[:512],
            start_pos=start_pos,
            end_pos=end_pos,
            group_key=group_key,
            group_mode=group_data.get("mode"),
            db_hit=bool(group_data.get("db_hit", False)),
        )

    # ------------------------------------------------------------------
    # Socket.IO emission
    # ------------------------------------------------------------------

    def _emit_event(self, event: str, data: Dict[str, Any]) -> None:
        """Emit event to the overview room."""
        if not self.socketio:
            return
        try:
            self.socketio.emit(event, data, namespace="/", room=ANONYMIZATION_OVERVIEW_ROOM)
            logger.info("[AnonymizationWorker] Emitted %s to overview", event)
        except Exception as exc:
            logger.warning("[AnonymizationWorker] Failed to emit %s: %s", event, exc)

    def _emit_conversation_event(self, event: str, data: Dict[str, Any]) -> None:
        """Emit event to both conversation-specific room and overview room."""
        if not self.socketio:
            return
        try:
            conversation_id = data.get("conversation_id")
            if conversation_id:
                room = anonymization_conversation_room(conversation_id)
                self.socketio.emit(event, data, namespace="/", room=room)

            # Mirror to overview for list-level updates
            self.socketio.emit(event, data, namespace="/", room=ANONYMIZATION_OVERVIEW_ROOM)

            if "progress" not in event:
                logger.info("[AnonymizationWorker] Emitted %s for conversation %s", event, conversation_id)
        except Exception as exc:
            logger.warning("[AnonymizationWorker] Failed to emit %s: %s", event, exc)
