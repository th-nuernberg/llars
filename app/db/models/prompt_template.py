"""
Prompt Template Model for LLM Evaluator Prompts.

Stores customizable prompts for different evaluation task types.
Supports global defaults and scenario-specific overrides.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class PromptTemplate(db.Model):
    """
    Stores prompt templates for LLM evaluators.

    Features:
    - Global default prompts per task type
    - Scenario-specific overrides
    - Version tracking for reproducibility
    - Variable placeholders for dynamic content
    """

    __tablename__ = "prompt_templates"

    # Primary key
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # Identification
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    task_type: Mapped[str] = mapped_column(
        db.String(50),
        nullable=False,
        index=True,
        comment="ranking, rating, authenticity, mail_rating, comparison, text_classification"
    )
    version: Mapped[str] = mapped_column(db.String(20), nullable=False, default="1.0")

    # Prompt content
    system_prompt: Mapped[str] = mapped_column(db.Text, nullable=False)
    user_prompt_template: Mapped[str] = mapped_column(db.Text, nullable=False)

    # Configuration
    variables: Mapped[Optional[List]] = mapped_column(
        db.JSON,
        nullable=True,
        default=list,
        comment="List of placeholder variables: ['features', 'thread_content', ...]"
    )
    output_schema_version: Mapped[str] = mapped_column(
        db.String(20),
        nullable=False,
        default="1.0",
        comment="Version of the expected output schema"
    )

    # Flags
    is_default: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=False,
        comment="Is this the default template for the task type?"
    )
    is_active: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=True,
        comment="Is this template active and usable?"
    )

    # Ownership
    created_by: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Constraints
    __table_args__ = (
        # Only one default per task type
        db.Index(
            "ix_prompt_templates_task_default",
            "task_type",
            "is_default",
            unique=False  # Can have multiple, but only one with is_default=True
        ),
        db.Index("ix_prompt_templates_active", "is_active"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "version": self.version,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "variables": self.variables or [],
            "output_schema_version": self.output_schema_version,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_default_for_task(cls, task_type: str) -> Optional["PromptTemplate"]:
        """Get the default template for a task type."""
        return cls.query.filter_by(
            task_type=task_type,
            is_default=True,
            is_active=True
        ).first()

    @classmethod
    def get_active_for_task(cls, task_type: str) -> List["PromptTemplate"]:
        """Get all active templates for a task type."""
        return cls.query.filter_by(
            task_type=task_type,
            is_active=True
        ).order_by(cls.is_default.desc(), cls.name).all()

    def set_as_default(self) -> None:
        """Set this template as the default for its task type."""
        # Unset previous default
        cls = self.__class__
        cls.query.filter_by(
            task_type=self.task_type,
            is_default=True
        ).update({"is_default": False})

        # Set this as default
        self.is_default = True
        db.session.add(self)

    def __repr__(self) -> str:
        return f"<PromptTemplate {self.id}: {self.name} ({self.task_type})>"
