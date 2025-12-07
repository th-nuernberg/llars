"""
LLM Model Configuration Database Model

Stores available LLM models with their capabilities and pricing.
Used for model selection in chatbots and other LLM-powered features.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from db import db


class LLMModel(db.Model):
    """
    Configuration for available LLM models.

    Stores model capabilities (vision, reasoning), pricing (input/output costs),
    and technical specifications (context window, max tokens).
    """
    __tablename__ = 'llm_models'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # Model identification
    model_id: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    provider: Mapped[str] = mapped_column(db.String(100), nullable=False)  # e.g., 'mistral', 'openai', 'anthropic'
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Capabilities
    supports_vision: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    supports_reasoning: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    supports_function_calling: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    supports_streaming: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    # Technical specifications
    context_window: Mapped[int] = mapped_column(db.Integer, nullable=False)  # in tokens
    max_output_tokens: Mapped[int] = mapped_column(db.Integer, nullable=False)

    # Pricing (per 1M tokens, in USD)
    input_cost_per_million: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)
    output_cost_per_million: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)

    # Default settings
    is_default: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False, index=True)

    # Recommended use cases
    recommended_for: Mapped[Optional[str]] = mapped_column(db.JSON, nullable=True)  # e.g., ['chat', 'rag', 'vision']

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<LLMModel {self.model_id}>"

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            'id': self.id,
            'model_id': self.model_id,
            'display_name': self.display_name,
            'provider': self.provider,
            'description': self.description,
            'supports_vision': self.supports_vision,
            'supports_reasoning': self.supports_reasoning,
            'supports_function_calling': self.supports_function_calling,
            'supports_streaming': self.supports_streaming,
            'context_window': self.context_window,
            'max_output_tokens': self.max_output_tokens,
            'input_cost_per_million': self.input_cost_per_million,
            'output_cost_per_million': self.output_cost_per_million,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'recommended_for': self.recommended_for,
        }

    @classmethod
    def get_default_model(cls) -> Optional['LLMModel']:
        """Get the default active model."""
        return cls.query.filter_by(is_default=True, is_active=True).first()

    @classmethod
    def get_vision_models(cls) -> list['LLMModel']:
        """Get all active models that support vision."""
        return cls.query.filter_by(supports_vision=True, is_active=True).all()

    @classmethod
    def get_by_model_id(cls, model_id: str) -> Optional['LLMModel']:
        """Get model by its model_id."""
        return cls.query.filter_by(model_id=model_id).first()


# Default models to seed into the database
DEFAULT_LLM_MODELS = [
    {
        'model_id': 'mistralai/Mistral-Small-3.2-24B-Instruct-2506',
        'display_name': 'Mistral Small 3.2 (24B)',
        'provider': 'mistral',
        'description': 'Schnelles und effizientes Modell für allgemeine Chat- und RAG-Anwendungen. Gute Balance zwischen Geschwindigkeit und Qualität.',
        'supports_vision': False,
        'supports_reasoning': False,
        'supports_function_calling': True,
        'supports_streaming': True,
        'context_window': 32768,
        'max_output_tokens': 8192,
        'input_cost_per_million': 0.1,
        'output_cost_per_million': 0.3,
        'is_default': True,
        'is_active': True,
        'recommended_for': ['chat', 'rag', 'general'],
    },
    {
        'model_id': 'mistralai/Magistral-Small-2509',
        'display_name': 'Magistral Small (Vision + Reasoning)',
        'provider': 'mistral',
        'description': 'Multimodales Modell mit Vision- und Reasoning-Fähigkeiten. Ideal für Bildanalyse und komplexe Schlussfolgerungen.',
        'supports_vision': True,
        'supports_reasoning': True,
        'supports_function_calling': True,
        'supports_streaming': True,
        'context_window': 131072,
        'max_output_tokens': 40960,
        'input_cost_per_million': 0.5,
        'output_cost_per_million': 1.5,
        'is_default': False,
        'is_active': True,
        'recommended_for': ['vision', 'reasoning', 'analysis', 'rag-images'],
    },
    {
        'model_id': 'llamaindex/vdr-2b-multi-v1',
        'display_name': 'VDR-2B Multi (Embedding)',
        'provider': 'llamaindex',
        'description': 'Multimodales Embedding-Modell für Text und Bilder. Verwendet für RAG-Pipeline und Dokumentensuche.',
        'supports_vision': True,
        'supports_reasoning': False,
        'supports_function_calling': False,
        'supports_streaming': False,
        'context_window': 8192,
        'max_output_tokens': 0,  # Embedding model, no text output
        'input_cost_per_million': 0.02,
        'output_cost_per_million': 0.0,
        'is_default': False,
        'is_active': True,
        'recommended_for': ['embedding', 'rag', 'similarity-search'],
    },
]


def seed_default_models():
    """
    Seed default LLM models into the database.
    Called during application startup.
    """
    from db.db import db

    for model_data in DEFAULT_LLM_MODELS:
        existing = LLMModel.query.filter_by(model_id=model_data['model_id']).first()
        if not existing:
            model = LLMModel(**model_data)
            db.session.add(model)
            print(f"  [LLM Models] Added: {model_data['display_name']}")
        else:
            # Update existing model with new data (except is_default if already set)
            for key, value in model_data.items():
                if key != 'is_default' or not existing.is_default:
                    setattr(existing, key, value)

    db.session.commit()
