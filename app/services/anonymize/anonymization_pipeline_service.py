"""Services for conversation import and NER processing in anonymization pipeline."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from decorators.error_handler import ValidationError
from db.database import db
from db.models import (
    AnonymizationConversation,
    AnonymizationEntity,
    AnonymizationMessage,
)
from services.anonymize.anonymize_service import AnonymizeService

logger = logging.getLogger(__name__)


class AnonymizationPipelineService:
    """Import and processing helpers for anonymization pipeline conversations."""

    MESSAGE_COLLECTION_KEYS = (
        "learn_counselling_messages",
        "messages",
        "conversation",
        "chat_messages",
        "thread",
    )
    MESSAGE_CONTENT_KEYS = (
        "content",
        "text",
        "message",
        "body",
        "edited_content",
        "original_content",
        "anonymized_content",
    )
    MESSAGE_AUTHOR_KEYS = ("author", "role", "sender", "speaker", "from")
    CONVERSATION_ID_KEYS = ("id", "conversation_id", "chat_id", "thread_id")
    CONVERSATION_TITLE_KEYS = ("title", "name", "subject")
    CONVERSATION_CREATED_AT_KEYS = ("created_at", "createdAt", "timestamp", "date")
    ENTITY_LABELS = {"PER", "LOC", "ORG", "DATE", "AGE", "PHONE", "MAIL", "AHV", "PLZ", "MISC"}

    ENTITY_LABEL_ALIASES = {
        "EMAIL": "MAIL",
        "E-MAIL": "MAIL",
        "PERSON": "PER",
        "NAME": "PER",
        "LOCATION": "LOC",
        "PLACE": "LOC",
        "ORGANISATION": "ORG",
        "ORGANIZATION": "ORG",
        "ZIP": "PLZ",
        "POSTAL_CODE": "PLZ",
        "POSTCODE": "PLZ",
        "SSN": "AHV",
        "SVN": "MISC",
        "IBAN": "MISC",
        "URL": "MISC",
        "TIME": "MISC",
        "STREET": "MISC",
    }

    @classmethod
    def import_conversations(
        cls,
        payload: Any,
        source_file_path: str,
        user_id: int,
        run_ner: bool = False,
    ) -> Dict[str, Any]:
        """Import one or many conversations from JSON payload."""
        raw_conversations = cls._normalize_payload(payload)
        if not raw_conversations:
            raise ValidationError("No conversation objects found in JSON payload")

        imported: List[AnonymizationConversation] = []
        failed: List[Dict[str, Any]] = []

        for index, raw_conversation in enumerate(raw_conversations, start=1):
            if not isinstance(raw_conversation, dict):
                failed.append({"index": index, "error": "Conversation entry must be an object"})
                continue

            conversation_source = (
                source_file_path
                if len(raw_conversations) == 1
                else f"{source_file_path}::conversation_{index}"
            )

            try:
                with db.session.begin_nested():
                    conversation = cls._create_conversation(
                        raw_conversation=raw_conversation,
                        source_file_path=conversation_source,
                        user_id=user_id,
                        run_ner=run_ner,
                    )
                imported.append(conversation)
            except ValidationError as exc:
                failed.append({"index": index, "error": str(exc)})
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to import conversation #%s", index)
                failed.append({"index": index, "error": str(exc)})

        if not imported:
            first_error = failed[0]["error"] if failed else "Unknown import error"
            raise ValidationError(f"Import failed: {first_error}")

        return {
            "imported_conversations": imported,
            "imported_count": len(imported),
            "failed_count": len(failed),
            "failed": failed,
        }

    @classmethod
    def rerun_ner(
        cls,
        conversation: AnonymizationConversation,
        user_id: int,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Run NER/pseudonymization for all messages of a conversation."""
        if not conversation:
            raise ValidationError("Conversation is required")

        messages = sorted(list(conversation.messages or []), key=lambda msg: msg.message_number)
        if not messages:
            raise ValidationError("Conversation has no messages")

        if not force and any(msg.is_manually_edited for msg in messages):
            raise ValidationError(
                "Conversation contains manually edited messages. Use force=true to re-run NER."
            )

        conversation.status = "in_progress"
        conversation.error_message = None
        conversation.updated_by = user_id
        conversation.updated_at = datetime.utcnow()

        for message in messages:
            for entity in list(message.entities):
                db.session.delete(entity)
            if force:
                for version in list(message.versions):
                    db.session.delete(version)

            message.anonymized_content = message.original_content or ""
            message.current_version = 1
            message.is_manually_edited = False

        db.session.flush()

        conversation_entity_map: Dict[str, Dict[str, Any]] = {}
        date_shift_days: Optional[int] = None
        total_entities = 0
        errors: List[str] = []

        for message in messages:
            text = (message.original_content or "").strip()
            if not text:
                message.anonymized_content = message.original_content or ""
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

                # Keep replacements consistent across the whole conversation.
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

                groups_by_id: Dict[str, Dict[str, Any]] = {}
                for group in result.get("groups", []):
                    group_id = group.get("group_id") or group.get("group_key")
                    if group_id:
                        groups_by_id[group_id] = group

                for entity in result.get("entities", []):
                    entity_record = cls._build_entity_record(
                        message_id=message.id,
                        entity=entity,
                        groups_by_id=groups_by_id,
                    )
                    if entity_record is None:
                        continue
                    db.session.add(entity_record)
                    total_entities += 1

            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("NER processing failed for conversation=%s message=%s", conversation.id, message.id)
                errors.append(f"message {message.message_number}: {exc}")
                message.anonymized_content = message.original_content or ""

        conversation.message_count = len(messages)
        conversation.entity_count = total_entities
        conversation.updated_by = user_id
        conversation.updated_at = datetime.utcnow()

        if errors:
            conversation.status = "error"
            conversation.error_message = "; ".join(errors[:3])
        else:
            conversation.status = "pending"
            conversation.error_message = None

        return {
            "conversation_id": conversation.id,
            "message_count": len(messages),
            "entity_count": total_entities,
            "errors": errors,
        }

    @classmethod
    def _normalize_payload(cls, payload: Any) -> List[Dict[str, Any]]:
        """Normalize payload to a list of conversation objects."""
        if isinstance(payload, list):
            return payload

        if isinstance(payload, dict):
            for key in ("conversations", "items", "data"):
                nested = payload.get(key)
                if isinstance(nested, list):
                    return nested
            return [payload]

        raise ValidationError("Uploaded JSON must be an object or array")

    @classmethod
    def _create_conversation(
        cls,
        raw_conversation: Dict[str, Any],
        source_file_path: str,
        user_id: int,
        run_ner: bool,
    ) -> AnonymizationConversation:
        """Create conversation + messages from one raw conversation object."""
        message_source_key, raw_messages = cls._extract_message_collection(raw_conversation)
        if not raw_messages:
            raise ValidationError(
                "No message collection found. Expected keys like 'learn_counselling_messages' or 'messages'."
            )

        normalized_messages = cls._normalize_messages(raw_messages)
        if not normalized_messages:
            raise ValidationError("No valid messages with textual content found")

        metadata_json = cls._build_metadata(
            raw_conversation=raw_conversation,
            message_source_key=message_source_key,
            raw_messages=raw_messages,
            normalized_messages=normalized_messages,
        )

        conversation = AnonymizationConversation(
            source_file_path=source_file_path,
            original_chat_id=cls._extract_conversation_id(raw_conversation),
            title=cls._extract_title(raw_conversation),
            status="pending",
            original_created_at=cls._extract_created_at(raw_conversation),
            persona_json=raw_conversation.get("persona") if isinstance(raw_conversation.get("persona"), dict) else None,
            metadata_json=metadata_json,
            imported_by=user_id,
            updated_by=user_id,
        )

        db.session.add(conversation)
        db.session.flush()

        for message in normalized_messages:
            db.session.add(
                AnonymizationMessage(
                    conversation_id=conversation.id,
                    message_number=message["message_number"],
                    author=message["author"],
                    original_content=message["content"],
                    anonymized_content=message["content"],
                    current_version=1,
                    is_manually_edited=False,
                )
            )

        conversation.message_count = len(normalized_messages)
        conversation.entity_count = 0

        if run_ner:
            db.session.flush()
            cls.rerun_ner(conversation=conversation, user_id=user_id, force=True)

        return conversation

    @classmethod
    def _extract_message_collection(
        cls,
        raw_conversation: Dict[str, Any],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Find best matching message list in a conversation object."""
        for key in cls.MESSAGE_COLLECTION_KEYS:
            value = raw_conversation.get(key)
            if cls._is_message_list(value):
                return key, value

        for key, value in raw_conversation.items():
            if cls._is_message_list(value):
                return key, value

        return "", []

    @classmethod
    def _is_message_list(cls, value: Any) -> bool:
        """Heuristic to identify list of messages."""
        if not isinstance(value, list) or not value:
            return False

        for entry in value:
            if not isinstance(entry, dict):
                continue
            if cls._extract_message_content(entry):
                return True
        return False

    @classmethod
    def _normalize_messages(cls, raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize heterogeneous message schemas to a shared shape."""
        normalized: List[Dict[str, Any]] = []

        for fallback_number, raw_message in enumerate(raw_messages, start=1):
            if not isinstance(raw_message, dict):
                continue

            content = cls._extract_message_content(raw_message)
            if not content:
                continue

            normalized.append(
                {
                    "message_number": cls._extract_message_number(raw_message, fallback_number),
                    "author": cls._extract_message_author(raw_message),
                    "content": content,
                }
            )

        if not normalized:
            return []

        # Enforce stable ordering and unique message_number sequence for DB unique constraint.
        normalized = sorted(normalized, key=lambda msg: msg["message_number"])
        for index, message in enumerate(normalized, start=1):
            message["message_number"] = index

        return normalized

    @classmethod
    def _extract_message_content(cls, message: Dict[str, Any]) -> str:
        """Extract message text from common content keys."""
        for key in cls.MESSAGE_CONTENT_KEYS:
            value = message.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return ""

    @classmethod
    def _extract_message_author(cls, message: Dict[str, Any]) -> str:
        """Extract author/role value from common keys."""
        for key in cls.MESSAGE_AUTHOR_KEYS:
            value = message.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return "unknown"

    @classmethod
    def _extract_message_number(cls, message: Dict[str, Any], fallback_number: int) -> int:
        """Extract numeric message order from common keys."""
        value = message.get("message_number")
        if isinstance(value, int) and value > 0:
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return fallback_number

    @classmethod
    def _extract_conversation_id(cls, raw_conversation: Dict[str, Any]) -> Optional[str]:
        """Extract original conversation ID from common keys."""
        for key in cls.CONVERSATION_ID_KEYS:
            value = raw_conversation.get(key)
            if value is not None and str(value).strip() != "":
                return str(value)
        return None

    @classmethod
    def _extract_title(cls, raw_conversation: Dict[str, Any]) -> str:
        """Extract conversation title from common keys."""
        for key in cls.CONVERSATION_TITLE_KEYS:
            value = raw_conversation.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:512]

        conversation_id = cls._extract_conversation_id(raw_conversation)
        if conversation_id:
            return f"Conversation {conversation_id}"
        return "Untitled Conversation"

    @classmethod
    def _extract_created_at(cls, raw_conversation: Dict[str, Any]) -> Optional[datetime]:
        """Extract datetime from common fields."""
        for key in cls.CONVERSATION_CREATED_AT_KEYS:
            parsed = cls._parse_datetime(raw_conversation.get(key))
            if parsed:
                return parsed
        return None

    @classmethod
    def _parse_datetime(cls, value: Any) -> Optional[datetime]:
        """Best-effort datetime parsing for common JSON formats."""
        if not value or not isinstance(value, str):
            return None

        normalized = value.strip()
        if not normalized:
            return None

        try:
            return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _maybe_parse_json(value: Any) -> Any:
        """Best-effort parsing of JSON strings for nested export fields."""
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if not normalized:
            return value

        if normalized[0] not in "{[":
            return value

        try:
            return json.loads(normalized)
        except (TypeError, ValueError, json.JSONDecodeError):
            return value

    @classmethod
    def _collect_llm_metadata(
        cls,
        raw_conversation: Dict[str, Any],
        raw_messages: List[Dict[str, Any]],
    ) -> Tuple[List[str], List[str]]:
        """Collect model/provider metadata from top-level and message-level llm_info."""
        models: set[str] = set()
        providers: set[str] = set()

        def _collect_from_llm_info(value: Any) -> None:
            llm_info = cls._maybe_parse_json(value)
            if not isinstance(llm_info, dict):
                return

            model = (
                llm_info.get("model")
                or llm_info.get("model_id")
                or llm_info.get("modelId")
                or llm_info.get("model_name")
                or llm_info.get("modelName")
            )
            provider = (
                llm_info.get("provider")
                or llm_info.get("provider_id")
                or llm_info.get("providerId")
                or llm_info.get("vendor")
            )

            if model is not None and str(model).strip():
                models.add(str(model).strip())
            if provider is not None and str(provider).strip():
                providers.add(str(provider).strip())

        for key in ("llm_info", "llmInfo", "llm"):
            _collect_from_llm_info(raw_conversation.get(key))

        for message in raw_messages:
            if not isinstance(message, dict):
                continue

            llm_candidates: List[Any] = []
            llm_candidates.append(message.get("llm_info"))
            llm_candidates.append(message.get("llmInfo"))

            additions = cls._maybe_parse_json(message.get("additions"))
            if isinstance(additions, dict):
                llm_candidates.append(additions.get("llm_info"))
                llm_candidates.append(additions.get("llmInfo"))

            message_metadata = cls._maybe_parse_json(message.get("metadata") or message.get("meta"))
            if isinstance(message_metadata, dict):
                llm_candidates.append(message_metadata.get("llm_info"))
                llm_candidates.append(message_metadata.get("llmInfo"))

            for llm_info in llm_candidates:
                _collect_from_llm_info(llm_info)

        return sorted(models), sorted(providers)

    @classmethod
    def _collect_course_names(cls, raw_conversation: Dict[str, Any]) -> List[str]:
        """Collect course names from common nested structures."""
        course_names: set[str] = set()

        def _collect_from_course(value: Any) -> None:
            course = cls._maybe_parse_json(value)
            if isinstance(course, dict):
                name = course.get("name") or course.get("course_name") or course.get("courseName") or course.get("title")
                if isinstance(name, str) and name.strip():
                    course_names.add(name.strip())
            elif isinstance(course, str) and course.strip():
                course_names.add(course.strip())

        for key in ("course", "courseInfo"):
            _collect_from_course(raw_conversation.get(key))

        course_member = cls._maybe_parse_json(raw_conversation.get("course_member") or raw_conversation.get("courseMember"))
        if isinstance(course_member, dict):
            _collect_from_course(course_member.get("course") or course_member.get("courseInfo"))

            name = course_member.get("course_name") or course_member.get("courseName")
            if isinstance(name, str) and name.strip():
                course_names.add(name.strip())

        course_name = raw_conversation.get("course_name") or raw_conversation.get("courseName")
        if isinstance(course_name, str) and course_name.strip():
            course_names.add(course_name.strip())

        return sorted(course_names)

    @classmethod
    def _build_metadata(
        cls,
        raw_conversation: Dict[str, Any],
        message_source_key: str,
        raw_messages: List[Dict[str, Any]],
        normalized_messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build metadata JSON with raw and derived fields."""
        raw_metadata = {
            key: value
            for key, value in raw_conversation.items()
            if key not in {message_source_key, "persona"}
        }

        models, providers = cls._collect_llm_metadata(raw_conversation, raw_messages)
        courses = cls._collect_course_names(raw_conversation)

        return {
            "source": {
                "message_collection_key": message_source_key,
            },
            "derived": {
                "models": models,
                "providers": providers,
                "courses": courses,
                "authors": sorted({msg["author"] for msg in normalized_messages}),
                "message_count": len(normalized_messages),
                "top_level_keys": sorted(list(raw_conversation.keys())),
            },
            "raw": raw_metadata,
        }

    @classmethod
    def _normalize_entity_label(cls, value: Any) -> str:
        """Map entity labels to DB-supported enum values."""
        label = str(value or "MISC").strip().upper()
        label = cls.ENTITY_LABEL_ALIASES.get(label, label)
        if label not in cls.ENTITY_LABELS:
            return "MISC"
        return label

    @classmethod
    def _safe_int(cls, value: Any, fallback: int = 0) -> int:
        """Convert to int with fallback."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    @classmethod
    def _build_entity_record(
        cls,
        message_id: int,
        entity: Dict[str, Any],
        groups_by_id: Dict[str, Dict[str, Any]],
    ) -> Optional[AnonymizationEntity]:
        """Build AnonymizationEntity model from service response entity payload."""
        group_key = entity.get("group_id") or entity.get("group_key")
        group_data = groups_by_id.get(group_key, {}) if group_key else {}

        start_pos = cls._safe_int(entity.get("output_start"), fallback=cls._safe_int(entity.get("start"), fallback=0))
        end_pos = cls._safe_int(entity.get("output_end"), fallback=cls._safe_int(entity.get("end"), fallback=start_pos))

        if end_pos <= start_pos:
            start_pos = cls._safe_int(entity.get("start"), fallback=0)
            end_pos = cls._safe_int(entity.get("end"), fallback=start_pos)

        if end_pos <= start_pos:
            return None

        return AnonymizationEntity(
            message_id=message_id,
            label=cls._normalize_entity_label(entity.get("label")),
            original_text=str(entity.get("text") or entity.get("original_text") or "")[:512],
            replacement_text=str(entity.get("replacement") or entity.get("replacement_text") or "")[:512],
            start_pos=start_pos,
            end_pos=end_pos,
            group_key=group_key,
            group_mode=group_data.get("mode"),
            db_hit=bool(group_data.get("db_hit", False)),
        )
