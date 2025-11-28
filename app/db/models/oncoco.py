"""OnCoCo Analysis database models."""

from typing import Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column
from db import db


class OnCoCoAnalysisStatus(Enum):
    """Status states for OnCoCo analysis jobs"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class OnCoCoAnalysis(db.Model):
    """OnCoCo analysis job tracking and configuration"""
    __tablename__ = 'oncoco_analyses'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        db.Enum(OnCoCoAnalysisStatus),
        default=OnCoCoAnalysisStatus.PENDING,
        nullable=False,
        index=True
    )
    config_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)  # pillars, granularity etc.

    # Progress tracking
    total_threads: Mapped[int] = mapped_column(db.Integer, default=0)
    processed_threads: Mapped[int] = mapped_column(db.Integer, default=0)
    total_sentences: Mapped[int] = mapped_column(db.Integer, default=0)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Relationships
    sentence_labels = db.relationship('OnCoCoSentenceLabel', backref='analysis', cascade='all, delete-orphan')
    pillar_statistics = db.relationship('OnCoCoPillarStatistics', backref='analysis', cascade='all, delete-orphan')
    transition_matrices = db.relationship('OnCoCoTransitionMatrix', backref='analysis', cascade='all, delete-orphan')


class OnCoCoSentenceLabel(db.Model):
    """Individual sentence classifications from OnCoCo model"""
    __tablename__ = 'oncoco_sentence_labels'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('oncoco_analyses.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    thread_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('email_threads.thread_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    message_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('messages.message_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_number: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)

    # Sentence info
    sentence_index: Mapped[int] = mapped_column(db.Integer, nullable=False)
    sentence_text: Mapped[str] = mapped_column(db.Text, nullable=False)
    role: Mapped[str] = mapped_column(db.String(20), nullable=False)  # 'Counselor' or 'Client'

    # Classification result
    label: Mapped[str] = mapped_column(db.String(50), nullable=False, index=True)
    label_level2: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True, index=True)  # Aggregated label
    confidence: Mapped[float] = mapped_column(db.Float, nullable=False)
    top_3_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)  # Top 3 predictions

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    # Relationships
    thread = db.relationship('EmailThread', backref='oncoco_labels')
    message = db.relationship('Message', backref='oncoco_labels')


class OnCoCoPillarStatistics(db.Model):
    """Aggregated statistics per pillar for an analysis"""
    __tablename__ = 'oncoco_pillar_statistics'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('oncoco_analyses.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_number: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)

    # Counts
    total_threads: Mapped[int] = mapped_column(db.Integer, default=0)
    total_messages: Mapped[int] = mapped_column(db.Integer, default=0)
    total_sentences: Mapped[int] = mapped_column(db.Integer, default=0)
    counselor_sentences: Mapped[int] = mapped_column(db.Integer, default=0)
    client_sentences: Mapped[int] = mapped_column(db.Integer, default=0)

    # Label distributions (JSON: {label: count, ...})
    label_distribution_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    label_distribution_level2_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    # Computed scores
    impact_factor_ratio: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    mi_score: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)  # Motivational Interviewing
    resource_activation_score: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    avg_confidence: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)

    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('analysis_id', 'pillar_number', name='unique_analysis_pillar'),
    )


class OnCoCoTransitionMatrix(db.Model):
    """Transition matrices between labels for conversation flow analysis"""
    __tablename__ = 'oncoco_transition_matrices'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('oncoco_analyses.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_number: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)  # NULL = all pillars
    level: Mapped[int] = mapped_column(db.Integer, default=2, nullable=False)  # Aggregation level (2-5)

    # Matrix data: {from_label: {to_label: count, ...}, ...}
    matrix_counts_json: Mapped[dict] = mapped_column(db.JSON, nullable=False)
    matrix_probs_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)  # Normalized probabilities

    # Statistics
    total_transitions: Mapped[int] = mapped_column(db.Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('analysis_id', 'pillar_number', 'level', name='unique_analysis_pillar_level'),
    )
