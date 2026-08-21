"""Password-reset token model for the self-service "forgot password" flow."""

import hashlib
import secrets
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Mapped, mapped_column

from db import db


def generate_reset_token() -> str:
    """Generate a URL-safe single-use reset token (plaintext, goes in the link)."""
    return secrets.token_urlsafe(32)


def hash_reset_token(raw: str) -> str:
    """
    Hash a reset token for at-rest storage (Pentest 2026-06-10, M6).

    Der Klartext-Token landet im Reset-Link (E-Mail); in der DB liegt nur sein
    SHA-256-Hash. So führt ein DB-Lesezugriff nicht mehr direkt zur Account-
    Übernahme über einen noch gültigen Token. Token sind hochentropisch (256 bit),
    daher genügt ein schneller Hash ohne Salt/KDF.
    """
    return hashlib.sha256((raw or "").encode("utf-8")).hexdigest()


class PasswordResetToken(db.Model):
    """
    A single-use, time-limited token tying a reset link to a username.

    The password write-through itself targets Authentik (LLARS keeps no
    usable ``password_hash`` for Authentik-backed users), so this row only
    tracks the LLARS-side token lifecycle: issued → (optionally) used. Keyed
    on ``username`` rather than a FK, mirroring ``ReferralRegistration``.
    """

    __tablename__ = 'password_reset_tokens'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    # Speichert den SHA-256-HASH des Tokens (64 hex chars), nie den Klartext (M6).
    token: Mapped[str] = mapped_column(
        db.String(64), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True, default=None)

    __table_args__ = (
        db.Index('ix_prt_expires', 'expires_at'),
    )

    @classmethod
    def create_for(cls, username: str, ttl_hours: int = 2) -> "PasswordResetToken":
        """Create (but do not commit) a fresh token for ``username``.

        TTL is deliberately short (2h) — reset links are higher-risk than
        registration confirmations.
        """
        now = datetime.utcnow()
        raw = generate_reset_token()
        row = cls(
            token=hash_reset_token(raw),
            username=username,
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
        )
        # Klartext-Token transient für den Aufrufer (Link-Erzeugung) — nicht persistiert.
        row.raw_token = raw
        return row

    @classmethod
    def find_by_raw(cls, raw_token: Optional[str]) -> "Optional[PasswordResetToken]":
        """Find a token row by its PLAINTEXT value (hashes, then looks up)."""
        if not raw_token:
            return None
        return cls.query.filter_by(token=hash_reset_token(raw_token)).first()

    def is_valid(self) -> bool:
        """True when the token is unused and not yet expired."""
        return self.used_at is None and datetime.utcnow() < self.expires_at

    def mark_used(self) -> None:
        """Stamp the token as consumed."""
        self.used_at = datetime.utcnow()
