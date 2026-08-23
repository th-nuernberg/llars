"""Token model backing BOTH the self-service "forgot password" flow and the
passwordless "magic login" sign-in links (see ``purpose`` below)."""

import hashlib
import secrets
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Mapped, mapped_column

from db import db


# --- Token purposes -------------------------------------------------------
# The two flows share this table but have DELIBERATELY different lifecycles:
#
#   'reset' — a password-RESET link. A single-use credential for CHANGING a
#             password, so it is consumed (``used_at`` stamped) the moment it
#             is redeemed. Short TTL (2h).
#   'magic' — a passwordless SIGN-IN link mailed after a QR join / on re-entry.
#             Deliberately RE-USABLE within its validity window (product
#             decision): a participant scans the QR once and clicks the same
#             mailed link whenever they come back, for up to 7 days. It is NOT
#             consumed on use; its bounds are the TTL, hashing at rest, and
#             being superseded when a newer magic link is minted.
#
# The column exists so the two can never be swapped: a magic link must not be
# usable to CHANGE a password, and a reset link must not sign anyone in.
# Rows written before the column existed read as NULL and count as 'reset'
# (the stricter, single-use side).
PURPOSE_RESET = 'reset'
PURPOSE_MAGIC = 'magic'


def generate_reset_token() -> str:
    """Generate a URL-safe reset/magic token (plaintext, goes in the link)."""
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
    A time-limited, hashed-at-rest token tying an emailed link to a username.

    Two flows share the table, told apart by ``purpose``:

    - ``'reset'`` — single-use password-reset link (consumed on redemption).
    - ``'magic'`` — passwordless sign-in link, **multi-use** inside its TTL.

    The password write-through itself targets Authentik (LLARS keeps no
    usable ``password_hash`` for Authentik-backed users), so this row only
    tracks the LLARS-side token lifecycle: issued → (optionally) retired.
    Keyed on ``username`` rather than a FK, mirroring ``ReferralRegistration``.

    ``used_at`` means "retired", not "seen": a reset token stamps it on
    redemption, a magic token only ever gets it stamped when a NEWER magic
    link supersedes it. Every consumer must additionally gate on ``purpose``
    so the two link types can never be used for each other's flow.
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
    # 'reset' | 'magic' — see the PURPOSE_* constants above for the lifecycle
    # split. Kept nullable on the ORM side even though the migration adds the
    # column NOT NULL DEFAULT 'reset': rows that predate the column (or are
    # written by an older node mid-deploy) must still load, and every gate
    # normalises NULL to the stricter 'reset'.
    purpose: Mapped[Optional[str]] = mapped_column(
        db.String(16), nullable=True, default=PURPOSE_RESET,
        server_default=PURPOSE_RESET, index=True,
    )

    __table_args__ = (
        db.Index('ix_prt_expires', 'expires_at'),
    )

    @classmethod
    def create_for(cls, username: str, ttl_hours: int = 2,
                   purpose: str = PURPOSE_RESET) -> "PasswordResetToken":
        """Create (but do not commit) a fresh token for ``username``.

        The default TTL is deliberately short (2h) and the default purpose is
        the stricter ``'reset'`` — callers minting a sign-in link must opt in
        explicitly via ``purpose='magic'`` (and a longer ``ttl_hours``).
        """
        now = datetime.utcnow()
        raw = generate_reset_token()
        row = cls(
            token=hash_reset_token(raw),
            username=username,
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
            purpose=purpose or PURPOSE_RESET,
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

    @property
    def effective_purpose(self) -> str:
        """Purpose with the legacy NULL normalised to the stricter 'reset'."""
        return self.purpose or PURPOSE_RESET

    def is_for(self, purpose: str) -> bool:
        """True when this row belongs to ``purpose`` (NULL counts as 'reset')."""
        return self.effective_purpose == purpose

    def is_valid(self) -> bool:
        """True when the token is not retired and not yet expired.

        For ``'reset'`` rows "not retired" means "not yet redeemed"; for
        ``'magic'`` rows it means "not yet superseded by a newer magic link"
        — a magic token stays valid across repeated sign-ins (see PURPOSE_*).
        """
        return self.used_at is None and datetime.utcnow() < self.expires_at

    def mark_used(self) -> None:
        """Stamp the token as retired (consumed / superseded)."""
        self.used_at = datetime.utcnow()
