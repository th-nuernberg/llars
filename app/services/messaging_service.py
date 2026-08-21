"""
Messaging Service
Handles conversations, messages, encryption keys, and AI key grants.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_

from db.database import db
from db.models.messaging import (
    ConversationType,
    MessageType,
    MessagingAIKeyGrant,
    MessagingAttachment,
    MessagingConversation,
    MessagingEncryptionKey,
    MessagingMessage,
    MessagingParticipant,
    MessagingReadReceipt,
    ParticipantRole,
)

logger = logging.getLogger(__name__)

MAX_ATTACHMENT_SIZE = 50 * 1024 * 1024  # 50 MB


class MessagingService:
    """Service for managing messaging conversations and messages."""

    # ── Conversations ──────────────────────────────────────────────

    @staticmethod
    def get_conversations(
        username: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List conversations for a user, ordered by last_message_at."""
        participant_ids = (
            db.session.query(MessagingParticipant.conversation_id)
            .filter(
                MessagingParticipant.username == username,
                MessagingParticipant.is_active == True,
            )
            .subquery()
        )

        conversations = (
            MessagingConversation.query.filter(
                MessagingConversation.id.in_(participant_ids)
            )
            .order_by(
                db.case(
                    (MessagingConversation.last_message_at.is_(None), 1),
                    else_=0
                ),
                MessagingConversation.last_message_at.desc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [c.to_dict(for_username=username) for c in conversations]

    @staticmethod
    def get_conversation(
        conversation_id: int, username: str
    ) -> Optional[Dict[str, Any]]:
        """Get a single conversation with access check."""
        conv = MessagingConversation.query.get(conversation_id)
        if not conv:
            return None

        participant = MessagingParticipant.query.filter_by(
            conversation_id=conversation_id, username=username, is_active=True
        ).first()
        if not participant:
            return None

        return conv.to_dict(for_username=username)

    @staticmethod
    def create_direct_conversation(
        creator: str, other_username: str
    ) -> Dict[str, Any]:
        """Create or return existing direct conversation between two users."""
        if creator == other_username:
            raise ValueError("Cannot create a conversation with yourself")

        # Check for existing direct conversation
        existing = (
            MessagingConversation.query.join(MessagingParticipant)
            .filter(
                MessagingConversation.conversation_type == ConversationType.direct,
                MessagingParticipant.username.in_([creator, other_username]),
                MessagingParticipant.is_active == True,
            )
            .all()
        )

        for conv in existing:
            usernames = {p.username for p in conv.participants if p.is_active}
            if usernames == {creator, other_username}:
                return conv.to_dict(for_username=creator)

        # Create new conversation
        conv = MessagingConversation(
            conversation_type=ConversationType.direct,
            created_by=creator,
        )
        db.session.add(conv)
        db.session.flush()

        for uname, role in [
            (creator, ParticipantRole.owner),
            (other_username, ParticipantRole.member),
        ]:
            db.session.add(
                MessagingParticipant(
                    conversation_id=conv.id,
                    username=uname,
                    role=role,
                )
            )

        db.session.commit()
        logger.info("Direct conversation %d created by %s with %s", conv.id, creator, other_username)
        return conv.to_dict(for_username=creator)

    @staticmethod
    def create_group_conversation(
        creator: str,
        name: str,
        member_usernames: List[str],
        description: str | None = None,
    ) -> Dict[str, Any]:
        """Create a new group conversation."""
        if not name or not name.strip():
            raise ValueError("Group name is required")

        members = list(set(member_usernames))
        if creator not in members:
            members.append(creator)

        conv = MessagingConversation(
            conversation_type=ConversationType.group,
            name=name.strip(),
            description=description,
            created_by=creator,
        )
        db.session.add(conv)
        db.session.flush()

        for uname in members:
            role = ParticipantRole.owner if uname == creator else ParticipantRole.member
            db.session.add(
                MessagingParticipant(
                    conversation_id=conv.id,
                    username=uname,
                    role=role,
                )
            )

        # System message
        db.session.add(
            MessagingMessage(
                conversation_id=conv.id,
                sender_username=creator,
                content=f"{creator} created the group \"{name}\"",
                message_type=MessageType.system,
            )
        )

        db.session.commit()
        logger.info("Group conversation %d '%s' created by %s", conv.id, name, creator)
        return conv.to_dict(for_username=creator)

    @staticmethod
    def update_group_info(
        conversation_id: int,
        username: str,
        name: str | None = None,
        description: str | None = None,
    ) -> Optional[Dict[str, Any]]:
        """Update group name / description. Requires admin or owner role."""
        conv = MessagingConversation.query.get(conversation_id)
        if not conv or conv.conversation_type != ConversationType.group:
            return None

        participant = MessagingParticipant.query.filter_by(
            conversation_id=conversation_id, username=username, is_active=True
        ).first()
        if not participant or participant.role not in (ParticipantRole.admin, ParticipantRole.owner):
            return None

        if name is not None:
            conv.name = name.strip()
        if description is not None:
            conv.description = description.strip() if description else None

        db.session.commit()
        return conv.to_dict(for_username=username)

    @staticmethod
    def add_group_member(
        conversation_id: int, username: str, added_by: str
    ) -> Optional[Dict[str, Any]]:
        """Add a member to a group conversation."""
        conv = MessagingConversation.query.get(conversation_id)
        if not conv or conv.conversation_type != ConversationType.group:
            return None

        adder = MessagingParticipant.query.filter_by(
            conversation_id=conversation_id, username=added_by, is_active=True
        ).first()
        if not adder or adder.role not in (ParticipantRole.admin, ParticipantRole.owner):
            return None

        existing = MessagingParticipant.query.filter_by(
            conversation_id=conversation_id, username=username
        ).first()

        if existing:
            if existing.is_active:
                return conv.to_dict(for_username=added_by)
            existing.is_active = True
            existing.role = ParticipantRole.member
        else:
            db.session.add(
                MessagingParticipant(
                    conversation_id=conversation_id,
                    username=username,
                    role=ParticipantRole.member,
                )
            )

        db.session.add(
            MessagingMessage(
                conversation_id=conversation_id,
                sender_username=added_by,
                content=f"{added_by} added {username}",
                message_type=MessageType.system,
            )
        )
        db.session.commit()
        logger.info("User %s added to conversation %d by %s", username, conversation_id, added_by)
        return conv.to_dict(for_username=added_by)

    @staticmethod
    def remove_group_member(
        conversation_id: int, username: str, removed_by: str
    ) -> bool:
        """Remove a member from a group. Owner cannot be removed."""
        conv = MessagingConversation.query.get(conversation_id)
        if not conv or conv.conversation_type != ConversationType.group:
            return False

        # Self-leave is always allowed; otherwise need admin/owner
        if username != removed_by:
            remover = MessagingParticipant.query.filter_by(
                conversation_id=conversation_id, username=removed_by, is_active=True
            ).first()
            if not remover or remover.role not in (ParticipantRole.admin, ParticipantRole.owner):
                return False

        target = MessagingParticipant.query.filter_by(
            conversation_id=conversation_id, username=username, is_active=True
        ).first()
        if not target:
            return False
        if target.role == ParticipantRole.owner:
            return False

        target.is_active = False
        db.session.add(
            MessagingMessage(
                conversation_id=conversation_id,
                sender_username=removed_by,
                content=f"{username} was removed" if username != removed_by else f"{username} left",
                message_type=MessageType.system,
            )
        )
        db.session.commit()
        return True

    @staticmethod
    def mute_conversation(conversation_id: int, username: str, mute: bool) -> bool:
        """Mute or unmute a conversation for a user."""
        p = MessagingParticipant.query.filter_by(
            conversation_id=conversation_id, username=username, is_active=True
        ).first()
        if not p:
            return False
        p.is_muted = mute
        db.session.commit()
        return True

    # ── Messages ───────────────────────────────────────────────────

    @staticmethod
    def get_messages(
        conversation_id: int,
        username: str,
        limit: int = 50,
        before_id: int | None = None,
    ) -> List[Dict[str, Any]]:
        """Get messages for a conversation (cursor-based pagination)."""
        participant = MessagingParticipant.query.filter_by(
            conversation_id=conversation_id, username=username, is_active=True
        ).first()
        if not participant:
            return []

        query = MessagingMessage.query.filter_by(conversation_id=conversation_id)
        if before_id:
            query = query.filter(MessagingMessage.id < before_id)

        messages = (
            query.order_by(MessagingMessage.id.desc())
            .limit(limit)
            .all()
        )

        return [m.to_dict() for m in reversed(messages)]

    @staticmethod
    def send_message(
        conversation_id: int,
        sender: str,
        content: str,
        message_type: str = "text",
        reply_to_id: int | None = None,
        encryption_metadata: dict | None = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a message to a conversation."""
        participant = MessagingParticipant.query.filter_by(
            conversation_id=conversation_id, username=sender, is_active=True
        ).first()
        if not participant:
            return None

        msg_type = MessageType(message_type) if message_type else MessageType.text

        msg = MessagingMessage(
            conversation_id=conversation_id,
            sender_username=sender,
            content=content,
            message_type=msg_type,
            is_encrypted=bool(encryption_metadata),
            encryption_metadata=encryption_metadata,
            reply_to_id=reply_to_id,
        )
        db.session.add(msg)
        db.session.flush()

        # Update conversation last_message
        conv = MessagingConversation.query.get(conversation_id)
        conv.last_message_at = msg.created_at
        if not msg.is_encrypted:
            conv.last_message_preview = (content or "")[:200]
        else:
            conv.last_message_preview = "[Encrypted]"

        # Increment unread for other participants
        MessagingParticipant.query.filter(
            MessagingParticipant.conversation_id == conversation_id,
            MessagingParticipant.username != sender,
            MessagingParticipant.is_active == True,
        ).update({"unread_count": MessagingParticipant.unread_count + 1})

        db.session.commit()
        return msg.to_dict()

    @staticmethod
    def edit_message(
        message_id: int, username: str, new_content: str
    ) -> Optional[Dict[str, Any]]:
        """Edit a message (sender only)."""
        msg = MessagingMessage.query.get(message_id)
        if not msg or msg.sender_username != username or msg.is_deleted:
            return None

        msg.content = new_content
        msg.is_edited = True
        msg.edited_at = datetime.utcnow()
        db.session.commit()
        return msg.to_dict()

    @staticmethod
    def delete_message(message_id: int, username: str) -> bool:
        """Soft-delete a message. Sender or group admin/owner can delete."""
        msg = MessagingMessage.query.get(message_id)
        if not msg or msg.is_deleted:
            return False

        if msg.sender_username != username:
            participant = MessagingParticipant.query.filter_by(
                conversation_id=msg.conversation_id,
                username=username,
                is_active=True,
            ).first()
            if not participant or participant.role not in (ParticipantRole.admin, ParticipantRole.owner):
                return False

        msg.is_deleted = True
        msg.content = None
        db.session.commit()
        return True

    @staticmethod
    def mark_as_read(
        conversation_id: int, username: str, up_to_message_id: int
    ) -> bool:
        """Mark messages as read up to a given message ID."""
        participant = MessagingParticipant.query.filter_by(
            conversation_id=conversation_id, username=username, is_active=True
        ).first()
        if not participant:
            return False

        participant.last_read_message_id = up_to_message_id
        participant.unread_count = 0
        db.session.commit()
        return True

    @staticmethod
    def get_unread_counts(username: str) -> Dict[str, Any]:
        """Get total and per-conversation unread counts."""
        participants = MessagingParticipant.query.filter_by(
            username=username, is_active=True
        ).all()

        per_conversation = {}
        total = 0
        for p in participants:
            if p.unread_count > 0:
                per_conversation[str(p.conversation_id)] = p.unread_count
                total += p.unread_count

        return {"total": total, "per_conversation": per_conversation}

    # ── Attachments ────────────────────────────────────────────────

    @staticmethod
    def add_attachment(
        message_id: int,
        username: str,
        filename: str,
        mime_type: str | None,
        file_data: bytes,
    ) -> Optional[Dict[str, Any]]:
        """Add an attachment to a message."""
        msg = MessagingMessage.query.get(message_id)
        if not msg or msg.sender_username != username:
            return None

        if len(file_data) > MAX_ATTACHMENT_SIZE:
            raise ValueError(f"File exceeds maximum size of {MAX_ATTACHMENT_SIZE // (1024 * 1024)} MB")

        attachment = MessagingAttachment(
            message_id=message_id,
            filename=filename,
            mime_type=mime_type,
            file_size=len(file_data),
            content=file_data,
        )
        db.session.add(attachment)
        msg.has_attachment = True
        db.session.commit()
        return attachment.to_dict()

    @staticmethod
    def get_attachment(attachment_id: int, username: str) -> Optional[MessagingAttachment]:
        """Get an attachment with access check."""
        attachment = MessagingAttachment.query.get(attachment_id)
        if not attachment:
            return None

        participant = MessagingParticipant.query.filter_by(
            conversation_id=attachment.message.conversation_id,
            username=username,
            is_active=True,
        ).first()
        if not participant:
            return None

        return attachment

    # ── Encryption Keys ────────────────────────────────────────────

    @staticmethod
    def store_key_bundle(username: str, key_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store or update a user's encryption key bundle."""
        existing = MessagingEncryptionKey.query.filter_by(username=username).first()
        if existing:
            existing.identity_public_key = key_data["identity_public_key"]
            existing.signed_prekey_public = key_data["signed_prekey_public"]
            existing.signed_prekey_id = key_data.get("signed_prekey_id", 0)
            existing.one_time_prekeys = key_data.get("one_time_prekeys")
        else:
            existing = MessagingEncryptionKey(
                username=username,
                identity_public_key=key_data["identity_public_key"],
                signed_prekey_public=key_data["signed_prekey_public"],
                signed_prekey_id=key_data.get("signed_prekey_id", 0),
                one_time_prekeys=key_data.get("one_time_prekeys"),
            )
            db.session.add(existing)

        db.session.commit()
        return existing.to_dict()

    @staticmethod
    def get_key_bundle(username: str) -> Optional[Dict[str, Any]]:
        """Get a user's encryption key bundle."""
        key = MessagingEncryptionKey.query.filter_by(username=username).first()
        return key.to_dict() if key else None

    @staticmethod
    def get_key_bundles(usernames: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get key bundles for multiple users."""
        keys = MessagingEncryptionKey.query.filter(
            MessagingEncryptionKey.username.in_(usernames)
        ).all()
        return {k.username: k.to_dict() for k in keys}

    # ── AI Key Grants ──────────────────────────────────────────────

    @staticmethod
    def grant_ai_access(
        username: str, conversation_id: int, encrypted_key: str
    ) -> bool:
        """Grant AI access to a conversation's E2E keys."""
        participant = MessagingParticipant.query.filter_by(
            conversation_id=conversation_id, username=username, is_active=True
        ).first()
        if not participant:
            return False

        existing = MessagingAIKeyGrant.query.filter_by(
            username=username, conversation_id=conversation_id
        ).first()

        if existing:
            existing.encrypted_key_for_ai = encrypted_key
            existing.revoked_at = None
            existing.granted_at = datetime.utcnow()
        else:
            db.session.add(
                MessagingAIKeyGrant(
                    username=username,
                    conversation_id=conversation_id,
                    encrypted_key_for_ai=encrypted_key,
                )
            )

        db.session.commit()
        return True

    @staticmethod
    def revoke_ai_access(username: str, conversation_id: int) -> bool:
        """Revoke AI access to a conversation."""
        grant = MessagingAIKeyGrant.query.filter_by(
            username=username, conversation_id=conversation_id
        ).first()
        if not grant:
            return False

        grant.revoked_at = datetime.utcnow()
        db.session.commit()
        return True
