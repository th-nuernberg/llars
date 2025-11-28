"""LLM-as-Judge database models."""

from typing import Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column
from db import db


class JudgeSessionStatus(Enum):
    """Status states for judge evaluation sessions"""
    CREATED = 'created'
    QUEUED = 'queued'
    RUNNING = 'running'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    FAILED = 'failed'


class JudgeComparisonStatus(Enum):
    """Status states for individual pairwise comparisons"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class JudgeWinner(Enum):
    """Winner designation for evaluation results"""
    A = 'A'
    B = 'B'
    TIE = 'TIE'


class PillarThread(db.Model):
    """Maps email threads to KIA pillars (1-5) for structured evaluation"""
    __tablename__ = 'pillar_threads'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('email_threads.thread_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_number: Mapped[int] = mapped_column(db.Integer, nullable=False)
    pillar_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    thread = db.relationship('EmailThread', backref='pillar_assignments')

    __table_args__ = (
        db.UniqueConstraint('thread_id', 'pillar_number', name='unique_thread_pillar'),
        db.CheckConstraint('pillar_number >= 1 AND pillar_number <= 5', name='check_pillar_range'),
    )


class JudgeSession(db.Model):
    """LLM-as-Judge evaluation session orchestrating multiple comparisons"""
    __tablename__ = 'judge_sessions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    config_json: Mapped[dict] = mapped_column(db.JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        db.Enum(JudgeSessionStatus),
        default=JudgeSessionStatus.CREATED,
        nullable=False,
        index=True
    )
    total_comparisons: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    completed_comparisons: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    current_comparison_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    comparisons = db.relationship('JudgeComparison', backref='session', cascade='all, delete-orphan')
    statistics = db.relationship('PillarStatistics', backref='session', cascade='all, delete-orphan')


class JudgeComparison(db.Model):
    """Individual pairwise comparison of two email threads within a session"""
    __tablename__ = 'judge_comparisons'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('judge_sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    thread_a_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('email_threads.thread_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    thread_b_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('email_threads.thread_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_a: Mapped[int] = mapped_column(db.Integer, nullable=False)
    pillar_b: Mapped[int] = mapped_column(db.Integer, nullable=False)
    position_order: Mapped[int] = mapped_column(db.Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        db.Enum(JudgeComparisonStatus),
        default=JudgeComparisonStatus.PENDING,
        nullable=False,
        index=True
    )
    queue_position: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)
    worker_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    thread_a = db.relationship('EmailThread', foreign_keys=[thread_a_id], backref='comparisons_as_a')
    thread_b = db.relationship('EmailThread', foreign_keys=[thread_b_id], backref='comparisons_as_b')
    evaluations = db.relationship('JudgeEvaluation', backref='comparison', cascade='all, delete-orphan')

    __table_args__ = (
        db.CheckConstraint('pillar_a >= 1 AND pillar_a <= 5', name='check_pillar_a_range'),
        db.CheckConstraint('pillar_b >= 1 AND pillar_b <= 5', name='check_pillar_b_range'),
        db.CheckConstraint('position_order IN (1, 2)', name='check_position_order'),
    )


class JudgeEvaluation(db.Model):
    """LLM evaluation result for a single pairwise comparison"""
    __tablename__ = 'judge_evaluations'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    comparison_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('judge_comparisons.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True
    )

    raw_response: Mapped[str] = mapped_column(db.Text, nullable=False)
    evaluation_json: Mapped[dict] = mapped_column(db.JSON, nullable=False)
    winner: Mapped[str] = mapped_column(db.Enum(JudgeWinner), nullable=False, index=True)

    counsellor_coherence_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    client_coherence_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    quality_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    empathy_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    authenticity_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    solution_orientation_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)

    counsellor_coherence_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    client_coherence_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    quality_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    empathy_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    authenticity_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    solution_orientation_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)

    reasoning: Mapped[str] = mapped_column(db.Text, nullable=False)
    confidence: Mapped[float] = mapped_column(db.Float, nullable=False)
    position_variant: Mapped[int] = mapped_column(db.Integer, nullable=False)

    llm_latency_ms: Mapped[int] = mapped_column(db.Integer, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)


class PillarStatistics(db.Model):
    """Aggregated win/loss statistics for pillar-to-pillar comparisons"""
    __tablename__ = 'pillar_statistics'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('judge_sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_a: Mapped[int] = mapped_column(db.Integer, nullable=False)
    pillar_b: Mapped[int] = mapped_column(db.Integer, nullable=False)

    wins_a: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    wins_b: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    ties: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    avg_confidence: Mapped[float] = mapped_column(db.Float, default=0.0, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint('session_id', 'pillar_a', 'pillar_b', name='unique_session_pillar_pair'),
        db.CheckConstraint('pillar_a >= 1 AND pillar_a <= 5', name='check_stats_pillar_a_range'),
        db.CheckConstraint('pillar_b >= 1 AND pillar_b <= 5', name='check_stats_pillar_b_range'),
    )
