"""
Chatbot Activity Service

Centralized logging service for all chatbot-related user activities.
Uses the SystemEvent table for persistent storage.

Activity Types:
    - chatbot.created       - New chatbot created
    - chatbot.updated       - Chatbot settings changed (name, color, icon, etc.)
    - chatbot.deleted       - Chatbot deleted
    - chatbot.duplicated    - Chatbot duplicated

    - wizard.started        - Chatbot wizard started
    - wizard.completed      - Chatbot wizard completed successfully
    - wizard.failed         - Chatbot wizard failed
    - wizard.cancelled      - Chatbot wizard cancelled

    - chat.created          - New chat/conversation started
    - chat.deleted          - Chat/conversation deleted
    - chat.message          - Message sent (optional, can be noisy)

    - collection.created    - RAG collection created
    - collection.updated    - RAG collection updated
    - collection.deleted    - RAG collection deleted

    - document.uploaded     - Document(s) uploaded
    - document.deleted      - Document deleted
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from flask import request, has_request_context

from db.database import db
from db.models.system_event import SystemEvent

logger = logging.getLogger(__name__)


class ChatbotActivityService:
    """Service for logging chatbot-related user activities."""

    # Activity type prefixes for filtering
    PREFIX_CHATBOT = 'chatbot'
    PREFIX_WIZARD = 'wizard'
    PREFIX_CHAT = 'chat'
    PREFIX_COLLECTION = 'collection'
    PREFIX_DOCUMENT = 'document'

    # All tracked prefixes
    TRACKED_PREFIXES = [PREFIX_CHATBOT, PREFIX_WIZARD, PREFIX_CHAT, PREFIX_COLLECTION, PREFIX_DOCUMENT]

    @classmethod
    def log_activity(
        cls,
        event_type: str,
        message: str,
        username: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        severity: str = 'info',
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[SystemEvent]:
        """
        Log a chatbot activity event.

        Args:
            event_type: Type of event (e.g., 'chatbot.created', 'chat.started')
            message: Human-readable description
            username: User who triggered the event
            entity_type: Type of entity (chatbot, collection, document, chat)
            entity_id: ID of the entity
            severity: Event severity (info, warning, error)
            details: Additional JSON details

        Returns:
            Created SystemEvent or None if failed
        """
        try:
            # Get request context if available
            request_path = None
            remote_addr = None
            user_agent = None

            if has_request_context():
                request_path = request.path
                remote_addr = request.remote_addr
                user_agent = request.headers.get('User-Agent', '')[:255]

            event = SystemEvent(
                event_type=event_type,
                severity=severity,
                message=message,
                username=username,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id else None,
                request_path=request_path,
                remote_addr=remote_addr,
                user_agent=user_agent,
                details=details,
                created_at=datetime.utcnow()
            )

            db.session.add(event)
            db.session.commit()

            logger.debug(f"[ChatbotActivity] Logged: {event_type} by {username}")
            return event

        except Exception as e:
            logger.error(f"[ChatbotActivity] Failed to log event: {e}")
            db.session.rollback()
            return None

    # ========== Chatbot Events ==========

    @classmethod
    def log_chatbot_created(
        cls,
        chatbot_id: int,
        chatbot_name: str,
        display_name: str,
        username: str,
        source_url: Optional[str] = None,
        via_wizard: bool = False
    ) -> Optional[SystemEvent]:
        """Log chatbot creation."""
        details = {
            'chatbot_name': chatbot_name,
            'display_name': display_name,
            'via_wizard': via_wizard
        }
        if source_url:
            details['source_url'] = source_url

        return cls.log_activity(
            event_type='chatbot.created',
            message=f"Chatbot '{display_name}' erstellt" + (" (via Wizard)" if via_wizard else ""),
            username=username,
            entity_type='chatbot',
            entity_id=chatbot_id,
            details=details
        )

    @classmethod
    def log_chatbot_updated(
        cls,
        chatbot_id: int,
        chatbot_name: str,
        username: str,
        changed_fields: Dict[str, Any]
    ) -> Optional[SystemEvent]:
        """Log chatbot update with changed fields."""
        # Format changed fields for message
        field_names = list(changed_fields.keys())
        if len(field_names) <= 3:
            fields_str = ', '.join(field_names)
        else:
            fields_str = f"{', '.join(field_names[:3])} (+{len(field_names) - 3})"

        return cls.log_activity(
            event_type='chatbot.updated',
            message=f"Chatbot '{chatbot_name}' aktualisiert: {fields_str}",
            username=username,
            entity_type='chatbot',
            entity_id=chatbot_id,
            details={'changed_fields': changed_fields}
        )

    @classmethod
    def log_chatbot_deleted(
        cls,
        chatbot_id: int,
        chatbot_name: str,
        username: str,
        with_collections: bool = False
    ) -> Optional[SystemEvent]:
        """Log chatbot deletion."""
        return cls.log_activity(
            event_type='chatbot.deleted',
            message=f"Chatbot '{chatbot_name}' gelöscht" + (" (inkl. Collections)" if with_collections else ""),
            username=username,
            entity_type='chatbot',
            entity_id=chatbot_id,
            severity='warning',
            details={'with_collections': with_collections}
        )

    @classmethod
    def log_chatbot_duplicated(
        cls,
        source_chatbot_id: int,
        new_chatbot_id: int,
        new_name: str,
        username: str
    ) -> Optional[SystemEvent]:
        """Log chatbot duplication."""
        return cls.log_activity(
            event_type='chatbot.duplicated',
            message=f"Chatbot dupliziert als '{new_name}'",
            username=username,
            entity_type='chatbot',
            entity_id=new_chatbot_id,
            details={'source_chatbot_id': source_chatbot_id}
        )

    # ========== Wizard Events ==========

    @classmethod
    def log_wizard_started(
        cls,
        chatbot_id: int,
        source_url: str,
        username: str
    ) -> Optional[SystemEvent]:
        """Log wizard start."""
        return cls.log_activity(
            event_type='wizard.started',
            message=f"Chatbot-Wizard gestartet für URL: {source_url[:50]}{'...' if len(source_url) > 50 else ''}",
            username=username,
            entity_type='chatbot',
            entity_id=chatbot_id,
            details={'source_url': source_url}
        )

    @classmethod
    def log_wizard_completed(
        cls,
        chatbot_id: int,
        chatbot_name: str,
        username: str,
        document_count: int = 0
    ) -> Optional[SystemEvent]:
        """Log successful wizard completion."""
        return cls.log_activity(
            event_type='wizard.completed',
            message=f"Chatbot-Wizard abgeschlossen: '{chatbot_name}' ({document_count} Dokumente)",
            username=username,
            entity_type='chatbot',
            entity_id=chatbot_id,
            severity='success',
            details={'document_count': document_count}
        )

    @classmethod
    def log_wizard_failed(
        cls,
        chatbot_id: int,
        username: str,
        error: str
    ) -> Optional[SystemEvent]:
        """Log wizard failure."""
        return cls.log_activity(
            event_type='wizard.failed',
            message=f"Chatbot-Wizard fehlgeschlagen: {error[:100]}",
            username=username,
            entity_type='chatbot',
            entity_id=chatbot_id,
            severity='error',
            details={'error': error}
        )

    @classmethod
    def log_wizard_cancelled(
        cls,
        chatbot_id: int,
        username: str
    ) -> Optional[SystemEvent]:
        """Log wizard cancellation."""
        return cls.log_activity(
            event_type='wizard.cancelled',
            message="Chatbot-Wizard abgebrochen",
            username=username,
            entity_type='chatbot',
            entity_id=chatbot_id,
            severity='warning'
        )

    # ========== Chat/Conversation Events ==========

    @classmethod
    def log_chat_created(
        cls,
        conversation_id: int,
        chatbot_id: int,
        chatbot_name: str,
        username: str
    ) -> Optional[SystemEvent]:
        """Log new chat/conversation started."""
        return cls.log_activity(
            event_type='chat.created',
            message=f"Neuer Chat gestartet mit '{chatbot_name}'",
            username=username,
            entity_type='conversation',
            entity_id=conversation_id,
            details={'chatbot_id': chatbot_id, 'chatbot_name': chatbot_name}
        )

    @classmethod
    def log_chat_deleted(
        cls,
        conversation_id: int,
        chatbot_id: int,
        chatbot_name: str,
        username: str,
        message_count: int = 0
    ) -> Optional[SystemEvent]:
        """Log chat/conversation deletion."""
        return cls.log_activity(
            event_type='chat.deleted',
            message=f"Chat mit '{chatbot_name}' gelöscht ({message_count} Nachrichten)",
            username=username,
            entity_type='conversation',
            entity_id=conversation_id,
            severity='warning',
            details={'chatbot_id': chatbot_id, 'message_count': message_count}
        )

    # ========== Collection Events ==========

    @classmethod
    def log_collection_created(
        cls,
        collection_id: int,
        collection_name: str,
        display_name: str,
        username: str,
        is_public: bool = True
    ) -> Optional[SystemEvent]:
        """Log collection creation."""
        return cls.log_activity(
            event_type='collection.created',
            message=f"Collection '{display_name}' erstellt",
            username=username,
            entity_type='collection',
            entity_id=collection_id,
            details={
                'collection_name': collection_name,
                'display_name': display_name,
                'is_public': is_public
            }
        )

    @classmethod
    def log_collection_updated(
        cls,
        collection_id: int,
        collection_name: str,
        username: str,
        changed_fields: Dict[str, Any]
    ) -> Optional[SystemEvent]:
        """Log collection update."""
        field_names = list(changed_fields.keys())
        fields_str = ', '.join(field_names[:3])
        if len(field_names) > 3:
            fields_str += f" (+{len(field_names) - 3})"

        return cls.log_activity(
            event_type='collection.updated',
            message=f"Collection '{collection_name}' aktualisiert: {fields_str}",
            username=username,
            entity_type='collection',
            entity_id=collection_id,
            details={'changed_fields': changed_fields}
        )

    @classmethod
    def log_collection_deleted(
        cls,
        collection_id: int,
        collection_name: str,
        username: str,
        document_count: int = 0,
        force: bool = False
    ) -> Optional[SystemEvent]:
        """Log collection deletion."""
        msg = f"Collection '{collection_name}' gelöscht"
        if document_count > 0:
            msg += f" (inkl. {document_count} Dokumente)"

        return cls.log_activity(
            event_type='collection.deleted',
            message=msg,
            username=username,
            entity_type='collection',
            entity_id=collection_id,
            severity='warning',
            details={'document_count': document_count, 'force': force}
        )

    # ========== Document Events ==========

    @classmethod
    def log_document_uploaded(
        cls,
        document_id: int,
        filename: str,
        username: str,
        collection_id: Optional[int] = None,
        collection_name: Optional[str] = None,
        file_size_bytes: int = 0,
        mime_type: Optional[str] = None
    ) -> Optional[SystemEvent]:
        """Log single document upload."""
        size_mb = round(file_size_bytes / (1024 * 1024), 2) if file_size_bytes else 0

        msg = f"Dokument '{filename}' hochgeladen ({size_mb} MB)"
        if collection_name:
            msg += f" → Collection '{collection_name}'"

        return cls.log_activity(
            event_type='document.uploaded',
            message=msg,
            username=username,
            entity_type='document',
            entity_id=document_id,
            details={
                'filename': filename,
                'file_size_bytes': file_size_bytes,
                'file_size_mb': size_mb,
                'mime_type': mime_type,
                'collection_id': collection_id,
                'collection_name': collection_name
            }
        )

    @classmethod
    def log_documents_uploaded(
        cls,
        document_ids: List[int],
        filenames: List[str],
        username: str,
        collection_id: Optional[int] = None,
        collection_name: Optional[str] = None,
        total_size_bytes: int = 0
    ) -> Optional[SystemEvent]:
        """Log multiple document uploads."""
        count = len(document_ids)
        size_mb = round(total_size_bytes / (1024 * 1024), 2) if total_size_bytes else 0

        msg = f"{count} Dokumente hochgeladen ({size_mb} MB)"
        if collection_name:
            msg += f" → Collection '{collection_name}'"

        return cls.log_activity(
            event_type='document.uploaded',
            message=msg,
            username=username,
            entity_type='document',
            entity_id=document_ids[0] if document_ids else None,
            details={
                'document_count': count,
                'document_ids': document_ids,
                'filenames': filenames[:10],  # Limit to first 10
                'total_size_bytes': total_size_bytes,
                'total_size_mb': size_mb,
                'collection_id': collection_id,
                'collection_name': collection_name
            }
        )

    @classmethod
    def log_document_deleted(
        cls,
        document_id: int,
        filename: str,
        username: str,
        collection_id: Optional[int] = None
    ) -> Optional[SystemEvent]:
        """Log document deletion."""
        return cls.log_activity(
            event_type='document.deleted',
            message=f"Dokument '{filename}' gelöscht",
            username=username,
            entity_type='document',
            entity_id=document_id,
            severity='warning',
            details={'filename': filename, 'collection_id': collection_id}
        )

    # ========== Query Methods ==========

    @classmethod
    def get_activities(
        cls,
        limit: int = 100,
        offset: int = 0,
        username: Optional[str] = None,
        event_type_prefix: Optional[str] = None,
        chatbot_id: Optional[int] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get chatbot activities with filters.

        Args:
            limit: Max number of results
            offset: Pagination offset
            username: Filter by username
            event_type_prefix: Filter by event type prefix (chatbot, wizard, chat, collection, document)
            chatbot_id: Filter by chatbot ID
            since: Filter events after this datetime

        Returns:
            List of activity dictionaries
        """
        from sqlalchemy import or_

        # Base query for chatbot-related events
        query = SystemEvent.query

        # Filter to only chatbot-related events
        if event_type_prefix:
            query = query.filter(SystemEvent.event_type.like(f"{event_type_prefix}.%"))
        else:
            # Filter to all tracked prefixes
            prefix_filters = [
                SystemEvent.event_type.like(f"{prefix}.%")
                for prefix in cls.TRACKED_PREFIXES
            ]
            query = query.filter(or_(*prefix_filters))

        # Apply filters
        if username:
            query = query.filter(SystemEvent.username == username)

        if chatbot_id:
            # Filter by entity_id for chatbot events, or details->chatbot_id for others
            query = query.filter(
                or_(
                    db.and_(
                        SystemEvent.entity_type == 'chatbot',
                        SystemEvent.entity_id == str(chatbot_id)
                    ),
                    SystemEvent.details['chatbot_id'].as_integer() == chatbot_id
                )
            )

        if since:
            query = query.filter(SystemEvent.created_at >= since)

        # Order by most recent first
        query = query.order_by(SystemEvent.created_at.desc())

        # Apply pagination
        query = query.offset(offset).limit(limit)

        events = query.all()

        return [cls._serialize_event(e) for e in events]

    @classmethod
    def get_activity_stats(
        cls,
        period_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get activity statistics for a time period.

        Args:
            period_hours: Time period in hours (default 24h)

        Returns:
            Statistics dictionary
        """
        from sqlalchemy import func, or_
        from datetime import timedelta

        since = datetime.utcnow() - timedelta(hours=period_hours)

        # Base filter for chatbot-related events
        prefix_filters = [
            SystemEvent.event_type.like(f"{prefix}.%")
            for prefix in cls.TRACKED_PREFIXES
        ]
        base_filter = or_(*prefix_filters)

        # Count by event type
        counts = db.session.query(
            SystemEvent.event_type,
            func.count(SystemEvent.id)
        ).filter(
            base_filter,
            SystemEvent.created_at >= since
        ).group_by(SystemEvent.event_type).all()

        # Count by user
        user_counts = db.session.query(
            SystemEvent.username,
            func.count(SystemEvent.id)
        ).filter(
            base_filter,
            SystemEvent.created_at >= since,
            SystemEvent.username.isnot(None)
        ).group_by(SystemEvent.username).order_by(
            func.count(SystemEvent.id).desc()
        ).limit(10).all()

        # Aggregate counts by category
        stats = {
            'period_hours': period_hours,
            'total_events': sum(c[1] for c in counts),
            'by_type': {c[0]: c[1] for c in counts},
            'by_category': {},
            'top_users': [{'username': u[0], 'count': u[1]} for u in user_counts]
        }

        # Group by category
        for event_type, count in counts:
            category = event_type.split('.')[0] if '.' in event_type else event_type
            stats['by_category'][category] = stats['by_category'].get(category, 0) + count

        return stats

    @classmethod
    def _serialize_event(cls, event: SystemEvent) -> Dict[str, Any]:
        """Serialize a SystemEvent to a dictionary."""
        return {
            'id': event.id,
            'event_type': event.event_type,
            'severity': event.severity,
            'message': event.message,
            'username': event.username,
            'entity_type': event.entity_type,
            'entity_id': event.entity_id,
            'details': event.details,
            'created_at': event.created_at.isoformat() if event.created_at else None
        }
