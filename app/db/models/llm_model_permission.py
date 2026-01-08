"""
LLM Model Permission

Defines per-user or per-role visibility for LLM models.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class LLMModelPermission(db.Model):
    """Allowlist entries for LLM model visibility."""

    __tablename__ = 'llm_model_permissions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    llm_model_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('llm_models.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    permission_type: Mapped[str] = mapped_column(db.String(20), nullable=False)  # user, role
    target_identifier: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)  # username or role

    granted_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            'llm_model_id', 'permission_type', 'target_identifier',
            name='unique_llm_model_permission'
        ),
    )
