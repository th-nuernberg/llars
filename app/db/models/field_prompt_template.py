"""
Field Prompt Template Model for AI-Assisted Form Fields.

Stores customizable prompts for AI-assisted field generation across the application.
Each field_key corresponds to a specific form field (e.g., 'scenario.settings.name').
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class FieldPromptTemplate(db.Model):
    """
    Stores prompt templates for AI-assisted form field generation.

    Features:
    - Field-specific prompts with context variables
    - Configurable LLM parameters (temperature, max_tokens)
    - Admin-editable through the Admin Panel
    - Active/inactive toggle for prompt lifecycle
    """

    __tablename__ = "field_prompt_templates"

    # Primary key
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # Field identification
    field_key: Mapped[str] = mapped_column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique key: {module}.{entity}.{field}, e.g., 'scenario.settings.name'"
    )
    display_name: Mapped[str] = mapped_column(
        db.String(200),
        nullable=False,
        comment="Human-readable name for admin UI, e.g., 'Szenario-Name'"
    )
    description: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Help text explaining what this prompt generates"
    )

    # Prompt content
    system_prompt: Mapped[str] = mapped_column(
        db.Text,
        nullable=False,
        comment="System prompt for LLM context setting"
    )
    user_prompt_template: Mapped[str] = mapped_column(
        db.Text,
        nullable=False,
        comment="User prompt with {variable} placeholders"
    )

    # Context configuration
    context_variables: Mapped[Optional[List]] = mapped_column(
        db.JSON,
        nullable=True,
        default=list,
        comment="List of expected context variables: ['scenario_type', 'existing_name', ...]"
    )

    # LLM parameters
    max_tokens: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        default=200,
        comment="Maximum tokens for generation"
    )
    temperature: Mapped[float] = mapped_column(
        db.Float,
        nullable=False,
        default=0.7,
        comment="LLM temperature (0.0-1.0)"
    )

    # Flags
    is_active: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=True,
        comment="Is this prompt active and usable?"
    )

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

    # Indexes
    __table_args__ = (
        db.Index("ix_field_prompt_templates_active", "is_active"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "field_key": self.field_key,
            "display_name": self.display_name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "context_variables": self.context_variables or [],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_by_field_key(cls, field_key: str) -> Optional["FieldPromptTemplate"]:
        """Get the active prompt template for a field key."""
        return cls.query.filter_by(
            field_key=field_key,
            is_active=True
        ).first()

    @classmethod
    def get_all_active(cls) -> List["FieldPromptTemplate"]:
        """Get all active field prompt templates."""
        return cls.query.filter_by(
            is_active=True
        ).order_by(cls.field_key).all()

    def render_user_prompt(self, context: dict) -> str:
        """
        Render the user prompt template with context variables.

        Args:
            context: Dictionary of variable values

        Returns:
            Rendered prompt string with placeholders replaced
        """
        prompt = self.user_prompt_template
        for var in (self.context_variables or []):
            value = context.get(var, "")
            # Handle None values
            if value is None:
                value = ""
            prompt = prompt.replace(f"{{{var}}}", str(value))
        return prompt

    def __repr__(self) -> str:
        return f"<FieldPromptTemplate {self.id}: {self.field_key}>"
