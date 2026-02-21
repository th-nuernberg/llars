#!/usr/bin/env python3
"""
Import chat JSON files from /data/chats/ and process through anonymization pipeline.

Usage:
    python scripts/import_anonymization_dataset.py [--dir /path/to/chats] [--user-id 1] [--batch-size 10]
"""

from __future__ import annotations

print("[DEBUG] Script started - beginning imports...")

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from db.db import db
from db.models import (
    AnonymizationConversation,
    AnonymizationMessage,
    AnonymizationEntity,
)
from services.anonymize import AnonymizeService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnonymizationImporter:
    """Batch imports and processes chat conversations."""

    def __init__(self, user_id: int = 1):
        self.user_id = user_id
        self.stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_messages': 0,
            'total_entities': 0
        }

    def import_from_directory(self, directory: Path, batch_size: int = 10):
        """Import all JSON files from directory."""
        json_files = list(directory.glob('*.json'))
        # Also include subdirectories
        for subdir in directory.iterdir():
            if subdir.is_dir():
                json_files.extend(subdir.glob('*.json'))

        self.stats['total_files'] = len(json_files)

        logger.info(f"Found {len(json_files)} JSON files in {directory}")

        for i, file_path in enumerate(json_files, 1):
            logger.info(f"Processing file {i}/{len(json_files)}: {file_path.name}")

            try:
                # Check if already imported
                existing = AnonymizationConversation.query.filter_by(
                    source_file_path=str(file_path)
                ).first()

                if existing:
                    logger.info(f"  Skipped - already imported (ID: {existing.id})")
                    self.stats['skipped'] += 1
                    continue

                # Load and validate JSON
                with open(file_path, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)

                # Handle both single conversation and array of conversations
                conversations_to_process = chat_data if isinstance(chat_data, list) else [chat_data]

                for conv_data in conversations_to_process:
                    conversation = self._process_conversation(file_path, conv_data)

                    if conversation:
                        self.stats['successful'] += 1
                        logger.info(f"  Success - Conversation ID: {conversation.id}, "
                                  f"{conversation.message_count} messages, "
                                  f"{conversation.entity_count} entities")
                    else:
                        self.stats['failed'] += 1

                # Commit in batches
                if i % batch_size == 0:
                    db.session.commit()
                    logger.info(f"  Committed batch at {i} files")

            except Exception as e:
                logger.error(f"  Failed to process {file_path.name}: {e}")
                self.stats['failed'] += 1
                db.session.rollback()

        # Final commit
        db.session.commit()
        self._print_summary()

    def _process_conversation(
        self,
        file_path: Path,
        chat_data: Dict
    ) -> Optional[AnonymizationConversation]:
        """Process a single conversation and its messages."""
        try:
            # Extract messages
            messages = chat_data.get('learn_counselling_messages', [])
            if not messages:
                logger.warning(f"  No messages found in conversation {chat_data.get('id', 'unknown')}")
                return None

            # Create conversation record
            conversation = AnonymizationConversation(
                source_file_path=str(file_path),
                original_chat_id=str(chat_data.get('id', '')),
                title=chat_data.get('title', 'Untitled'),
                status='pending',
                original_created_at=self._parse_timestamp(chat_data.get('created_at')),
                persona_json=chat_data.get('persona'),
                imported_by=self.user_id,
                updated_by=self.user_id
            )

            db.session.add(conversation)
            db.session.flush()  # Get conversation.id

            # Process messages with shared entity mappings for consistency
            entity_count = 0
            conversation_entity_map = {}  # Shared map for all messages in this conversation
            date_shift_days = None  # Use same date shift for entire conversation

            for msg_data in messages:
                msg_entities, conversation_entity_map, date_shift_days = self._process_message(
                    conversation.id,
                    msg_data,
                    conversation_entity_map,
                    date_shift_days
                )
                entity_count += msg_entities

            # Update counts
            conversation.message_count = len(messages)
            conversation.entity_count = entity_count

            self.stats['total_messages'] += len(messages)
            self.stats['total_entities'] += entity_count

            return conversation

        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            raise

    def _process_message(
        self,
        conversation_id: int,
        msg_data: Dict,
        conversation_entity_map: Dict,
        date_shift_days: Optional[int]
    ) -> tuple[int, Dict, Optional[int]]:
        """
        Process a single message through anonymization service.

        Returns:
            (entities_created, updated_entity_map, date_shift_days)
        """
        original_content = msg_data.get('content', '')

        if not original_content.strip():
            logger.debug(f"  Skipping empty message #{msg_data.get('message_number', 0)}")
            return 0, conversation_entity_map, date_shift_days

        try:
            # Call anonymization service with conversation-wide entity mappings
            # This ensures consistent replacements across all messages
            result = AnonymizeService.pseudonymize(
                text=original_content,
                engine='offline',  # Don't use LLM for batch processing
                group_overrides=conversation_entity_map,
                date_shift_days=date_shift_days,
                action=None,
                name_origin=None,
                name_count=None
            )

            # Update conversation entity map with new entities from this message
            for group in result.get('groups', []):
                group_id = group.get('group_id')
                if group_id and group_id not in conversation_entity_map:
                    conversation_entity_map[group_id] = {
                        'replacement': group.get('replacement'),
                        'mode': group.get('mode')
                    }

            # Store date shift for consistency across conversation
            if date_shift_days is None:
                date_shift_days = result.get('date_shift_days')

            # Create message record
            message = AnonymizationMessage(
                conversation_id=conversation_id,
                message_number=msg_data.get('message_number', 0),
                author=msg_data.get('author', 'unknown'),
                original_content=original_content,
                anonymized_content=result.get('output_text', original_content),
                current_version=1,
                is_manually_edited=False
            )

            db.session.add(message)
            db.session.flush()  # Get message.id

            # Create entity records
            entities_created = 0
            for entity in result.get('entities', []):
                group_key = entity.get('group_id') or entity.get('group_key')
                entity_record = AnonymizationEntity(
                    message_id=message.id,
                    label=entity.get('label', 'MISC'),
                    original_text=entity.get('text', ''),
                    replacement_text=entity.get('replacement', ''),
                    start_pos=entity.get('start', entity.get('start_pos', 0)),
                    end_pos=entity.get('end', entity.get('end_pos', 0)),
                    group_key=group_key,
                    group_mode=self._extract_group_mode(result.get('groups', []), group_key),
                    db_hit=self._check_db_hit(result.get('groups', []), group_key)
                )
                db.session.add(entity_record)
                entities_created += 1

            return entities_created, conversation_entity_map, date_shift_days

        except Exception as e:
            logger.error(f"Error anonymizing message: {e}")
            # Still create message with original content if anonymization fails
            message = AnonymizationMessage(
                conversation_id=conversation_id,
                message_number=msg_data.get('message_number', 0),
                author=msg_data.get('author', 'unknown'),
                original_content=original_content,
                anonymized_content=original_content,  # Fallback to original
                current_version=1,
                is_manually_edited=False
            )
            db.session.add(message)
            return 0, conversation_entity_map, date_shift_days

    def _extract_group_mode(self, groups: List[Dict], group_key: Optional[str]) -> Optional[str]:
        """Extract group mode from groups list."""
        if not group_key:
            return None
        for group in groups:
            if (group.get('group_id') or group.get('group_key')) == group_key:
                return group.get('mode')
        return None

    def _check_db_hit(self, groups: List[Dict], group_key: Optional[str]) -> bool:
        """Check if entity was found in DB."""
        if not group_key:
            return False
        for group in groups:
            if (group.get('group_id') or group.get('group_key')) == group_key:
                return group.get('db_hit', False)
        return False

    def _parse_timestamp(self, ts_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO timestamp or return None."""
        if not ts_str:
            return None
        try:
            return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except Exception:
            return None

    def _print_summary(self):
        """Print import statistics."""
        logger.info("\n" + "="*60)
        logger.info("IMPORT SUMMARY")
        logger.info("="*60)
        logger.info(f"Total files found:     {self.stats['total_files']}")
        logger.info(f"Successfully imported: {self.stats['successful']}")
        logger.info(f"Failed:                {self.stats['failed']}")
        logger.info(f"Skipped (duplicate):   {self.stats['skipped']}")
        logger.info(f"Total messages:        {self.stats['total_messages']}")
        logger.info(f"Total entities:        {self.stats['total_entities']}")
        logger.info("="*60)


def main():
    print("\n" + "="*80)
    print("STARTING ANONYMIZATION IMPORT SCRIPT")
    print("="*80 + "\n")
    parser = argparse.ArgumentParser(description='Import anonymization dataset')
    parser.add_argument(
        '--dir',
        type=Path,
        default=Path('/app/data/chats'),
        help='Directory containing chat JSON files'
    )
    parser.add_argument(
        '--user-id',
        type=int,
        default=1,
        help='User ID to attribute import to'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Commit every N files'
    )

    args = parser.parse_args()

    if not args.dir.exists():
        logger.error(f"Directory not found: {args.dir}")
        sys.exit(1)

    # Use Flask app context (app is imported from main)
    with app.app_context():
        importer = AnonymizationImporter(user_id=args.user_id)
        importer.import_from_directory(args.dir, batch_size=args.batch_size)


if __name__ == '__main__':
    main()
