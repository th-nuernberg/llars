"""Messaging database models (conversations, messages, participants, encryption, calls)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import LONGBLOB, LONGTEXT

from db import db


# ── Enums ──────────────────────────────────────────────────────────────

class ConversationType(Enum):
    direct = "direct"
    group = "group"


class ParticipantRole(Enum):
    member = "member"
    admin = "admin"
    owner = "owner"


class MessageType(Enum):
    text = "text"
    system = "system"
    file = "file"
    call_event = "call_event"


class CallType(Enum):
    voice = "voice"
    video = "video"


class CallStatus(Enum):
    ringing = "ringing"
    active = "active"
    ended = "ended"
    missed = "missed"
    declined = "declined"


# ── Conversations ──────────────────────────────────────────────────────

class MessagingConversation(db.Model):
    __tablename__ = "messaging_conversations"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    conversation_type: Mapped[ConversationType] = mapped_column(
        db.Enum(ConversationType),
        nullable=False,
        default=ConversationType.direct,
    )
    name: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    avatar_seed: Mapped[Optional[str]] = mapped_column(db.String(64), nullable=True)
    encryption_enabled: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True, index=True)
    last_message_preview: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )

    participants = db.relationship(
        "MessagingParticipant",
        backref=db.backref("conversation", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    messages = db.relationship(
        "MessagingMessage",
        backref=db.backref("conversation", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def to_dict(self, for_username: str | None = None) -> dict:
        """Serialize conversation. Optionally include per-user fields."""
        data = {
            "id": self.id,
            "conversation_type": self.conversation_type.value,
            "name": self.name,
            "description": self.description,
            "avatar_seed": self.avatar_seed,
            "encryption_enabled": self.encryption_enabled,
            "created_by": self.created_by,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "last_message_preview": self.last_message_preview,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "participants": [p.to_dict() for p in (self.participants or [])],
        }
        if for_username:
            p = next((x for x in (self.participants or []) if x.username == for_username), None)
            if p:
                data["unread_count"] = p.unread_count
                data["is_muted"] = p.is_muted
        return data


# ── Participants ───────────────────────────────────────────────────────

class MessagingParticipant(db.Model):
    __tablename__ = "messaging_participants"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("messaging_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    role: Mapped[ParticipantRole] = mapped_column(
        db.Enum(ParticipantRole),
        nullable=False,
        default=ParticipantRole.member,
    )
    key_bundle_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    last_read_message_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    unread_count: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    is_muted: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    joined_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("conversation_id", "username", name="unique_messaging_participant"),
    )

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "username": self.username,
            "role": self.role.value,
            "last_read_message_id": self.last_read_message_id,
            "unread_count": self.unread_count,
            "is_muted": self.is_muted,
            "is_active": self.is_active,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }
        # Enrich with avatar data from User model
        try:
            from db.models.user import User
            user = User.query.filter_by(username=self.username).first()
            if user:
                data["avatar_seed"] = user.get_avatar_seed()
                if user.avatar_public_id:
                    data["avatar_url"] = f"/api/users/avatar/{user.avatar_public_id}"
        except Exception:
            pass
        return data


# ── Messages ──────────────────────────────────────────────────────────

class MessagingMessage(db.Model):
    __tablename__ = "messaging_messages"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("messaging_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    content: Mapped[Optional[str]] = mapped_column(LONGTEXT, nullable=True)
    message_type: Mapped[MessageType] = mapped_column(
        db.Enum(MessageType),
        nullable=False,
        default=MessageType.text,
    )
    is_encrypted: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    encryption_metadata: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    reply_to_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("messaging_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    has_attachment: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    link_previews: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    is_edited: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    is_deleted: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    edited_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    reply_to = db.relationship("MessagingMessage", remote_side=[id], lazy="selectin")
    attachments = db.relationship(
        "MessagingAttachment",
        backref=db.backref("message", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reactions = db.relationship(
        "MessagingReaction",
        backref=db.backref("message", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender_username": self.sender_username,
            "content": self.content if not self.is_deleted else None,
            "message_type": self.message_type.value,
            "is_encrypted": self.is_encrypted,
            "encryption_metadata": self.encryption_metadata,
            "reply_to_id": self.reply_to_id,
            "has_attachment": self.has_attachment,
            "is_edited": self.is_edited,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "link_previews": self.link_previews,
        }
        if self.reply_to and not self.reply_to.is_deleted:
            data["reply_to_preview"] = {
                "id": self.reply_to.id,
                "sender_username": self.reply_to.sender_username,
                "content": (self.reply_to.content or "")[:120],
            }
        if self.attachments:
            data["attachments"] = [a.to_dict() for a in self.attachments]
        # Aggregate reactions by emoji
        if self.reactions:
            emoji_map = {}
            for r in self.reactions:
                if r.emoji not in emoji_map:
                    emoji_map[r.emoji] = []
                emoji_map[r.emoji].append(r.username)
            data["reactions"] = [
                {"emoji": emoji, "count": len(usernames), "usernames": usernames}
                for emoji, usernames in emoji_map.items()
            ]
        return data


# ── Attachments ───────────────────────────────────────────────────────

class MessagingAttachment(db.Model):
    __tablename__ = "messaging_attachments"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("messaging_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    file_size: Mapped[int] = mapped_column(db.BigInteger, nullable=False, default=0)
    content: Mapped[bytes] = mapped_column(LONGBLOB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Reactions ─────────────────────────────────────────────────────────

class MessagingReaction(db.Model):
    __tablename__ = "messaging_reactions"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("messaging_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(db.String(150), nullable=False)
    emoji: Mapped[str] = mapped_column(db.String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("message_id", "username", "emoji", name="unique_messaging_reaction"),
    )


# ── Read Receipts ─────────────────────────────────────────────────────

class MessagingReadReceipt(db.Model):
    __tablename__ = "messaging_read_receipts"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("messaging_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    read_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("message_id", "username", name="unique_messaging_read_receipt"),
    )


# ── Encryption Keys ──────────────────────────────────────────────────

class MessagingEncryptionKey(db.Model):
    __tablename__ = "messaging_encryption_keys"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, unique=True, index=True)
    identity_public_key: Mapped[str] = mapped_column(db.Text, nullable=False)
    signed_prekey_public: Mapped[str] = mapped_column(db.Text, nullable=False)
    signed_prekey_id: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    one_time_prekeys: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "identity_public_key": self.identity_public_key,
            "signed_prekey_public": self.signed_prekey_public,
            "signed_prekey_id": self.signed_prekey_id,
            "one_time_prekeys": self.one_time_prekeys,
        }


# ── AI Key Grants ────────────────────────────────────────────────────

class MessagingAIKeyGrant(db.Model):
    __tablename__ = "messaging_ai_key_grants"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    conversation_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("messaging_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    encrypted_key_for_ai: Mapped[str] = mapped_column(db.Text, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("username", "conversation_id", name="unique_messaging_ai_key_grant"),
    )


# ── Calls ─────────────────────────────────────────────────────────────

class MessagingCall(db.Model):
    __tablename__ = "messaging_calls"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("messaging_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    call_type: Mapped[CallType] = mapped_column(db.Enum(CallType), nullable=False)
    status: Mapped[CallStatus] = mapped_column(
        db.Enum(CallStatus), nullable=False, default=CallStatus.ringing,
    )
    initiated_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    livekit_room_name: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, unique=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    transcript_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    summary_text: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    summary_model_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    call_participants = db.relationship(
        "MessagingCallParticipant",
        backref=db.backref("call", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "call_type": self.call_type.value,
            "status": self.status.value,
            "initiated_by": self.initiated_by,
            "livekit_room_name": self.livekit_room_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "summary_text": self.summary_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "participants": [p.to_dict() for p in (self.call_participants or [])],
        }


class MessagingCallParticipant(db.Model):
    __tablename__ = "messaging_call_participants"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    call_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("messaging_calls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(db.String(255), nullable=False)
    joined_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    left_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("call_id", "username", name="unique_call_participant"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "call_id": self.call_id,
            "username": self.username,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
        }


# ── Link Preview Cache ───────────────────────────────────────────────

class MessagingLinkPreview(db.Model):
    __tablename__ = "messaging_link_previews"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    url_hash: Mapped[str] = mapped_column(db.String(64), nullable=False, unique=True, index=True)
    url: Mapped[str] = mapped_column(db.String(2000), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(db.String(300), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(db.String(2000), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(db.String(2000), nullable=True)
    site_name: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    fetch_error: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
