"""
Authenticity (Fake/Echt) Admin Routes

Provides an import endpoint for dataset items in the format:
{
  "metadata": {...},
  "messages": [...]
}
"""

from __future__ import annotations

import hashlib
import json
import logging
import zlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from flask import jsonify, request
from flask import g

from auth.decorators import authentik_required, admin_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ConflictError
from decorators.permission_decorator import require_permission
from routes.auth import data_bp
from services.feature_service import FeatureService
from services.scenario_stats_service import get_authenticity_stats
from db.database import db
from db.models import EmailThread, Message, AuthenticityConversation


logger = logging.getLogger(__name__)


def _parse_int(value: Any, *, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _build_sample_key(metadata: Dict[str, Any]) -> str:
    """
    Create a stable unique key for the imported sample.

    We hash a normalized subset of metadata to keep key length small and stable.
    """
    normalized = {
        "format_version": metadata.get("format_version"),
        "conversation_id": metadata.get("conversation_id"),
        "augmentation_type": metadata.get("augmentation_type"),
        "replaced_positions": sorted(metadata.get("replaced_positions") or []),
        "num_replacements": metadata.get("num_replacements"),
        "total_messages": metadata.get("total_messages"),
        "saeule": metadata.get("saeule"),
        "split": metadata.get("split"),
        "model": metadata.get("model"),
        "model_short": metadata.get("model_short"),
        "generated_at": metadata.get("generated_at"),
    }
    raw = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    version = str(metadata.get("format_version") or "v6")
    return f"{version}:{digest}"


def _pick_chat_id(sample_key: str, *, institut_id: int, function_type_id: int) -> int:
    """
    Pick a chat_id that is stable for this sample_key and does not collide with existing rows.
    """
    base = zlib.crc32(sample_key.encode("utf-8")) & 0x7FFFFFFF
    if base == 0:
        base = 1

    for offset in range(0, 1000):
        chat_id = (base + offset) & 0x7FFFFFFF
        existing_thread = EmailThread.query.filter_by(
            chat_id=chat_id,
            institut_id=institut_id,
            function_type_id=function_type_id,
        ).first()

        if not existing_thread:
            return chat_id

        existing_meta = AuthenticityConversation.query.filter_by(thread_id=existing_thread.thread_id).first()
        if existing_meta and existing_meta.sample_key == sample_key:
            return chat_id

    raise ConflictError("Could not allocate unique chat_id for this dataset item")


def _validate_item(item: Any) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if not isinstance(item, dict):
        raise ValidationError("Item must be an object with keys: metadata, messages")

    metadata = item.get("metadata")
    messages = item.get("messages")

    if not isinstance(metadata, dict):
        raise ValidationError("metadata must be an object")
    if not isinstance(messages, list) or not all(isinstance(m, dict) for m in messages):
        raise ValidationError("messages must be a list of objects")
    if len(messages) == 0:
        raise ValidationError("messages must not be empty")

    return metadata, messages


@data_bp.route("/admin/authenticity/import", methods=["POST"])
@authentik_required
@require_permission("data:import")
@handle_api_errors(logger_name="authenticity")
def import_authenticity_dataset():
    """
    Import one or many authenticity samples.

    Body:
      - single item object, or
      - list of item objects
    """
    payload = request.get_json(silent=True)
    if payload is None:
        raise ValidationError("Invalid JSON body")

    items = payload if isinstance(payload, list) else [payload]
    if not items:
        raise ValidationError("No items provided")

    function_type = FeatureService.get_function_type_by_name("authenticity")
    if not function_type:
        raise NotFoundError("Authenticity function type not found")

    results = {
        "ok": True,
        "imported": 0,
        "skipped_existing": 0,
        "errors": [],
        "thread_ids": [],
    }

    for idx, item in enumerate(items):
        try:
            metadata, messages = _validate_item(item)

            sample_key = _build_sample_key(metadata)
            existing = AuthenticityConversation.query.filter_by(sample_key=sample_key).first()
            if existing:
                results["skipped_existing"] += 1
                results["thread_ids"].append(int(existing.thread_id))
                continue

            institut_id = _parse_int(metadata.get("saeule"), default=0)
            chat_id = _pick_chat_id(sample_key, institut_id=institut_id, function_type_id=function_type.function_type_id)

            generated_at = _parse_datetime(metadata.get("generated_at"))
            base_time = generated_at or (datetime.utcnow() - timedelta(seconds=len(messages)))

            # Create EmailThread (function_type_id=authenticity)
            thread = EmailThread(
                chat_id=chat_id,
                institut_id=institut_id,
                subject="Fake/Echt – Import",
                sender="LLARS Import",
                function_type_id=function_type.function_type_id,
            )
            db.session.add(thread)
            db.session.flush()  # assign thread_id

            thread.subject = f"Fake/Echt – Fall #{thread.thread_id}"

            # Create messages (with deduplication)
            is_fake = False
            seen_messages = set()  # Track (sender, content) to detect duplicates
            actual_msg_index = 0

            for i, m in enumerate(messages):
                role = str(m.get("role") or m.get("sender") or m.get("from") or "Unbekannt")
                content = m.get("content")
                if content is None:
                    raise ValidationError("Each message requires 'content'")
                content = str(content)

                # Skip duplicate messages (same sender + content)
                msg_key = (role, content)
                if msg_key in seen_messages:
                    logger.warning(f"Skipping duplicate message in thread {thread.thread_id}: {role[:20]}...")
                    continue
                seen_messages.add(msg_key)

                msg_is_synth = bool(m.get("is_synthetic", False))
                is_fake = is_fake or msg_is_synth

                generated_by = m.get("generated_by")
                if msg_is_synth:
                    generated_by = str(generated_by or metadata.get("model") or "Synthetic")
                else:
                    generated_by = "Human"

                ts = _parse_datetime(m.get("timestamp")) or (base_time + timedelta(seconds=actual_msg_index))
                actual_msg_index += 1

                db.session.add(
                    Message(
                        thread_id=thread.thread_id,
                        sender=role,
                        content=content,
                        timestamp=ts,
                        generated_by=generated_by,
                    )
                )

            # Fallback: trust metadata counters if present (definition: fake if >=1 replacement)
            if _parse_int(metadata.get("num_replacements"), default=0) > 0:
                is_fake = True

            # Persist metadata
            db.session.add(
                AuthenticityConversation(
                    thread_id=thread.thread_id,
                    sample_key=sample_key,
                    conversation_id=_parse_int(metadata.get("conversation_id"), default=0) or None,
                    augmentation_type=str(metadata.get("augmentation_type") or "") or None,
                    replaced_positions=metadata.get("replaced_positions") or None,
                    num_replacements=_parse_int(metadata.get("num_replacements"), default=0) or None,
                    total_messages=_parse_int(metadata.get("total_messages"), default=len(messages)) or None,
                    saeule=str(metadata.get("saeule") or "") or None,
                    split=str(metadata.get("split") or "") or None,
                    model=str(metadata.get("model") or "") or None,
                    model_short=str(metadata.get("model_short") or "") or None,
                    generated_at=generated_at,
                    format_version=str(metadata.get("format_version") or "") or None,
                    is_fake=bool(is_fake),
                    metadata_json=metadata,
                )
            )

            db.session.commit()

            results["imported"] += 1
            results["thread_ids"].append(int(thread.thread_id))

        except Exception as exc:
            db.session.rollback()
            results["ok"] = False
            results["errors"].append({"index": idx, "error": str(exc)})

    return jsonify(results), 200


@data_bp.route("/admin/scenario/<int:scenario_id>/user_stats", methods=["GET"])
@admin_required
@handle_api_errors(logger_name="authenticity")
def get_authenticity_scenario_stats(scenario_id: int):
    """
    Get comprehensive statistics for an authenticity scenario.

    Returns user progress, inter-rater reliability (Krippendorff's Alpha),
    accuracy against ground truth, and vote distribution.
    """
    stats = get_authenticity_stats(scenario_id)
    return jsonify(stats), 200
