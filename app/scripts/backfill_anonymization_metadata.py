#!/usr/bin/env python3
"""
Backfill `anonymization_conversations.metadata_json`.

This is useful for conversations imported before metadata_json existed (models/courses
show up empty in the anonymization pipeline UI).

The script tries to locate the original source JSON file based on
`AnonymizationConversation.source_file_path` (supports `::conversation_<n>` suffix).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional


# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app  # noqa: E402
from db.database import db  # noqa: E402
from db.models import AnonymizationConversation  # noqa: E402
from services.anonymize.anonymization_pipeline_service import (  # noqa: E402
    AnonymizationPipelineService,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _parse_conversation_index(source_file_path: str) -> Optional[int]:
    marker = "::conversation_"
    if marker not in source_file_path:
        return None
    tail = source_file_path.split(marker, 1)[1].strip()
    return int(tail) if tail.isdigit() else None


def _base_source_path(source_file_path: str) -> str:
    marker = "::conversation_"
    return source_file_path.split(marker, 1)[0]


def _resolve_source_file_path(
    source_file_path: str, app_root: Path, search_dirs: list[Path]
) -> Optional[Path]:
    if not source_file_path:
        return None

    if source_file_path.startswith("upload://"):
        return None

    base_path = _base_source_path(source_file_path)

    candidate = Path(base_path)
    if candidate.exists():
        return candidate

    if base_path.startswith("/app/"):
        mapped = app_root / base_path.removeprefix("/app/")
        if mapped.exists():
            return mapped

    if not candidate.is_absolute():
        mapped = app_root / base_path
        if mapped.exists():
            return mapped

    basename = candidate.name
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        hits = list(search_dir.rglob(basename))
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            logger.warning("Ambiguous source file '%s' (found %s matches)", basename, len(hits))
            return None

    return None


def _normalize_payload(payload: Any) -> list[dict[str, Any]]:
    try:
        return AnonymizationPipelineService._normalize_payload(payload)  # type: ignore[attr-defined]
    except Exception:
        return []


def _select_raw_conversation(
    raw_conversations: list[dict[str, Any]],
    *,
    original_chat_id: Optional[str],
    index_hint: Optional[int],
) -> Optional[dict[str, Any]]:
    if not raw_conversations:
        return None

    if index_hint and 1 <= index_hint <= len(raw_conversations):
        return raw_conversations[index_hint - 1]

    if original_chat_id:
        matches: list[dict[str, Any]] = []
        for raw_conversation in raw_conversations:
            try:
                extracted = AnonymizationPipelineService._extract_conversation_id(raw_conversation)  # type: ignore[attr-defined]
            except Exception:
                extracted = None
            if extracted and str(extracted) == str(original_chat_id):
                matches.append(raw_conversation)

        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            logger.warning("Multiple matches for original_chat_id=%s (count=%s)", original_chat_id, len(matches))
            return None

    if len(raw_conversations) == 1:
        return raw_conversations[0]

    return None


def _build_metadata(raw_conversation: dict[str, Any]) -> Optional[dict[str, Any]]:
    message_source_key, raw_messages = AnonymizationPipelineService._extract_message_collection(raw_conversation)
    if not raw_messages:
        return None

    normalized_messages = AnonymizationPipelineService._normalize_messages(raw_messages)
    if not normalized_messages:
        return None

    return AnonymizationPipelineService._build_metadata(
        raw_conversation=raw_conversation,
        message_source_key=message_source_key or "messages",
        raw_messages=raw_messages,
        normalized_messages=normalized_messages,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill anonymization conversation metadata_json")
    parser.add_argument("--user-id", type=int, default=1, help="User ID to attribute update_by")
    parser.add_argument("--limit", type=int, default=500, help="Max conversations to process (0 = no limit)")
    parser.add_argument("--conversation-id", type=int, default=None, help="Process only one conversation ID")
    parser.add_argument("--force", action="store_true", help="Overwrite existing metadata_json")
    parser.add_argument("--dry-run", action="store_true", help="Compute but do not write to DB")
    parser.add_argument(
        "--search-dir",
        action="append",
        default=[],
        help="Additional directory to search for source JSON files (repeatable)",
    )
    args = parser.parse_args()

    app_root = Path(__file__).resolve().parent.parent
    search_dirs = [Path(p) for p in args.search_dir if p]
    default_search_dirs = [app_root / "data" / "chats"]
    search_dirs = [*default_search_dirs, *search_dirs]

    stats = {
        "scanned": 0,
        "updated": 0,
        "skipped": 0,
        "missing_source": 0,
        "missing_payload": 0,
        "errors": 0,
    }

    with app.app_context():
        query = AnonymizationConversation.query.order_by(AnonymizationConversation.imported_at.desc())
        if args.conversation_id:
            query = query.filter_by(id=args.conversation_id)
        elif not args.force:
            query = query.filter(AnonymizationConversation.metadata_json.is_(None))

        if args.limit and args.limit > 0:
            query = query.limit(args.limit)

        conversations = query.all()
        logger.info("Found %s conversation(s) to process", len(conversations))

        for idx, conversation in enumerate(conversations, start=1):
            stats["scanned"] += 1

            if conversation.metadata_json and not args.force:
                stats["skipped"] += 1
                continue

            index_hint = _parse_conversation_index(conversation.source_file_path or "")
            source_file = _resolve_source_file_path(conversation.source_file_path or "", app_root, search_dirs)
            if not source_file:
                stats["missing_source"] += 1
                logger.warning("(%s/%s) Missing source file for conversation id=%s (%s)", idx, len(conversations), conversation.id, conversation.source_file_path)
                continue

            try:
                payload = json.loads(source_file.read_text(encoding="utf-8"))
            except Exception as exc:
                stats["errors"] += 1
                logger.exception("Failed to read JSON from %s: %s", source_file, exc)
                continue

            raw_conversations = _normalize_payload(payload)
            raw_conversation = _select_raw_conversation(
                raw_conversations,
                original_chat_id=conversation.original_chat_id,
                index_hint=index_hint,
            )
            if not raw_conversation:
                stats["missing_payload"] += 1
                logger.warning(
                    "(%s/%s) Could not match payload for conversation id=%s original_chat_id=%s",
                    idx,
                    len(conversations),
                    conversation.id,
                    conversation.original_chat_id,
                )
                continue

            metadata_json = _build_metadata(raw_conversation)
            if not metadata_json:
                stats["missing_payload"] += 1
                logger.warning("(%s/%s) Could not build metadata for conversation id=%s", idx, len(conversations), conversation.id)
                continue

            if args.dry_run:
                stats["updated"] += 1
                continue

            conversation.metadata_json = metadata_json
            conversation.updated_by = args.user_id
            db.session.add(conversation)
            stats["updated"] += 1

            if stats["updated"] % 50 == 0:
                db.session.commit()
                logger.info("Committed %s updates", stats["updated"])

        if not args.dry_run:
            db.session.commit()

    logger.info("Done. Stats: %s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

