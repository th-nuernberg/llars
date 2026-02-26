"""
Pipeline Database Models.

Models for the automated LLM evaluation pipeline that orchestrates:
Prompt Engineering -> Batch Generation -> LLM Evaluation -> Analysis -> Loop

Architecture:
    PipelineRun (1) --> (N) PipelineIteration

    PipelineRun tracks the overall pipeline configuration and state.
    PipelineIteration stores per-iteration data including prompts, scores,
    and references to existing GenerationJob and RatingScenarios.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import db

if TYPE_CHECKING:
    from db.models.generation import GenerationJob
    from db.models.scenario import RatingScenarios


# =============================================================================
# ENUMS
# =============================================================================


class PipelineStatus(Enum):
    """
    Status states for pipeline runs.

    Lifecycle:
        CREATED -> RUNNING -> COMPLETED
                     |
                   PAUSED -> RUNNING
                     |
                WAITING_FOR_REVIEW -> RUNNING / COMPLETED
                     |
                   FAILED / CANCELLED
    """
    CREATED = 'created'
    RUNNING = 'running'
    PAUSED = 'paused'
    WAITING_FOR_REVIEW = 'waiting_for_review'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class PipelineIterationPhase(Enum):
    """Phases within a single pipeline iteration."""
    PROMPT_GENERATION = 'prompt_generation'
    BATCH_GENERATION = 'batch_generation'
    EVALUATION = 'evaluation'
    ANALYSIS = 'analysis'


class PipelineIterationStatus(Enum):
    """Status of a single pipeline iteration."""
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


# =============================================================================
# PIPELINE RUN MODEL
# =============================================================================


class PipelineRun(db.Model):
    """
    An automated pipeline run that loops through prompt generation,
    batch generation, LLM evaluation, and convergence analysis.

    Reuses existing GenerationJob and RatingScenarios per iteration
    rather than duplicating data.

    Attributes:
        id: Primary key
        name: Human-readable name for the run
        description: Optional longer description
        status: Current pipeline status
        config_json: Full pipeline configuration (task spec, dimensions, thresholds)
        scenario_type: 'greenfield' or 'migration'
        reference_model_id: Optional model ID for migration comparison
        candidate_models: JSON list of model IDs to test
        source_scenario_id: FK to source scenario with domain data
        current_iteration: Current iteration number
        max_iterations: Safety limit for iterations
        budget_tokens_total: Total token budget
        budget_tokens_used: Tokens consumed so far
        best_config_json: Current best configuration (model + prompt + score)
        created_by: Username who created the run
        created_at: Creation timestamp
        started_at: When the run started
        completed_at: When the run completed
    """

    __tablename__ = 'pipeline_runs'

    # -------------------------------------------------------------------------
    # Primary Key
    # -------------------------------------------------------------------------

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    # -------------------------------------------------------------------------
    # Identification
    # -------------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False,
        comment="Human-readable pipeline name"
    )

    description: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Optional longer description"
    )

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------

    status: Mapped[PipelineStatus] = mapped_column(
        db.Enum(PipelineStatus),
        default=PipelineStatus.CREATED,
        nullable=False,
        index=True,
        comment="Current pipeline status"
    )

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    config_json: Mapped[Dict[str, Any]] = mapped_column(
        db.JSON,
        nullable=False,
        comment="Full pipeline config: task_spec, dimensions, thresholds, eval_model"
    )

    scenario_type: Mapped[str] = mapped_column(
        db.String(50),
        default='greenfield',
        nullable=False,
        comment="'greenfield' or 'migration'"
    )

    reference_model_id: Mapped[Optional[str]] = mapped_column(
        db.String(255),
        nullable=True,
        comment="Reference model ID for migration comparison"
    )

    candidate_models: Mapped[Dict[str, Any]] = mapped_column(
        db.JSON,
        nullable=False,
        comment="List of model IDs to test"
    )

    # -------------------------------------------------------------------------
    # Source Data
    # -------------------------------------------------------------------------

    source_scenario_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('rating_scenarios.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Source scenario with domain data items"
    )

    # -------------------------------------------------------------------------
    # Iteration Tracking
    # -------------------------------------------------------------------------

    current_iteration: Mapped[int] = mapped_column(
        db.Integer,
        default=0,
        nullable=False,
        comment="Current iteration number"
    )

    max_iterations: Mapped[int] = mapped_column(
        db.Integer,
        default=10,
        nullable=False,
        comment="Maximum iterations (safety limit)"
    )

    # -------------------------------------------------------------------------
    # Budget Tracking
    # -------------------------------------------------------------------------

    budget_tokens_total: Mapped[int] = mapped_column(
        db.Integer,
        default=500000,
        nullable=False,
        comment="Total token budget"
    )

    budget_tokens_used: Mapped[int] = mapped_column(
        db.Integer,
        default=0,
        nullable=False,
        comment="Tokens consumed so far"
    )

    # -------------------------------------------------------------------------
    # Best Configuration
    # -------------------------------------------------------------------------

    best_config_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        db.JSON,
        nullable=True,
        comment="Current best config: {model, prompt, scores, iteration}"
    )

    # -------------------------------------------------------------------------
    # Ownership
    # -------------------------------------------------------------------------

    created_by: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False,
        index=True,
        comment="Username who created the run"
    )

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When the run was created"
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime,
        nullable=True,
        comment="When the run started"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime,
        nullable=True,
        comment="When the run completed"
    )

    # -------------------------------------------------------------------------
    # Error Handling
    # -------------------------------------------------------------------------

    error_message: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Error message if run failed"
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------

    iterations: Mapped[List["PipelineIteration"]] = relationship(
        "PipelineIteration",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="PipelineIteration.iteration_number"
    )

    source_scenario: Mapped[Optional["RatingScenarios"]] = relationship(
        "RatingScenarios",
        foreign_keys=[source_scenario_id],
        backref="pipeline_runs_as_source"
    )

    # -------------------------------------------------------------------------
    # Table Configuration
    # -------------------------------------------------------------------------

    __table_args__ = (
        db.Index('ix_pipeline_runs_created_by_status', 'created_by', 'status'),
        db.Index('ix_pipeline_runs_created_at', 'created_at'),
    )

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def budget_percent(self) -> float:
        """Budget usage as percentage (0-100)."""
        if self.budget_tokens_total == 0:
            return 0.0
        return round((self.budget_tokens_used / self.budget_tokens_total) * 100, 1)

    @property
    def is_active(self) -> bool:
        """Check if run is currently active."""
        return self.status in (PipelineStatus.RUNNING, PipelineStatus.WAITING_FOR_REVIEW)

    @property
    def can_start(self) -> bool:
        """Check if run can be started."""
        return self.status in (PipelineStatus.CREATED, PipelineStatus.PAUSED)

    @property
    def can_pause(self) -> bool:
        """Check if run can be paused."""
        return self.status == PipelineStatus.RUNNING

    @property
    def can_cancel(self) -> bool:
        """Check if run can be cancelled."""
        return self.status in (
            PipelineStatus.CREATED,
            PipelineStatus.RUNNING,
            PipelineStatus.PAUSED,
            PipelineStatus.WAITING_FOR_REVIEW,
        )

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------

    def to_dict(self, include_iterations: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'config': self.config_json,
            'scenario_type': self.scenario_type,
            'reference_model_id': self.reference_model_id,
            'candidate_models': self.candidate_models,
            'source_scenario_id': self.source_scenario_id,
            'current_iteration': self.current_iteration,
            'max_iterations': self.max_iterations,
            'budget': {
                'tokens_total': self.budget_tokens_total,
                'tokens_used': self.budget_tokens_used,
                'percent': self.budget_percent,
            },
            'best_config': self.best_config_json,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'can_start': self.can_start,
            'can_pause': self.can_pause,
            'can_cancel': self.can_cancel,
        }

        if include_iterations:
            result['iterations'] = [it.to_dict() for it in self.iterations]

        return result

    def to_summary_dict(self) -> Dict[str, Any]:
        """Lightweight summary for list views."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'scenario_type': self.scenario_type,
            'current_iteration': self.current_iteration,
            'max_iterations': self.max_iterations,
            'budget_percent': self.budget_percent,
            'best_config': self.best_config_json,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'candidate_models': self.candidate_models,
        }

    @classmethod
    def get_runs_for_user(
        cls,
        username: str,
        *,
        status: Optional[PipelineStatus] = None,
        limit: int = 50,
    ) -> List["PipelineRun"]:
        """Get runs for a user with optional filtering."""
        query = cls.query.filter_by(created_by=username)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.created_at.desc()).limit(limit).all()

    def __repr__(self) -> str:
        return f"<PipelineRun {self.id}: {self.name} ({self.status.value})>"


# =============================================================================
# PIPELINE ITERATION MODEL
# =============================================================================


class PipelineIteration(db.Model):
    """
    A single iteration within a pipeline run.

    Each iteration goes through: prompt_generation -> batch_generation ->
    evaluation -> analysis. References existing GenerationJob and
    RatingScenarios rather than duplicating data.

    Attributes:
        id: Primary key
        run_id: FK to parent PipelineRun
        iteration_number: Sequential number (1, 2, 3...)
        phase: Current phase within the iteration
        status: Iteration status
        prompt_variants_json: Prompts tested in this iteration
        generation_job_id: FK to GenerationJob (reuse)
        eval_scenario_id: FK to RatingScenarios (reuse)
        scores_json: Results per model x prompt x dimension
        agent_reasoning: Agent's diagnosis/decision text
        delta_to_best: Score improvement vs previous best
        tokens_used: Tokens consumed in this iteration
        started_at: Iteration start timestamp
        completed_at: Iteration completion timestamp
    """

    __tablename__ = 'pipeline_iterations'

    # -------------------------------------------------------------------------
    # Primary Key
    # -------------------------------------------------------------------------

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    # -------------------------------------------------------------------------
    # Parent Reference
    # -------------------------------------------------------------------------

    run_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('pipeline_runs.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Parent pipeline run"
    )

    # -------------------------------------------------------------------------
    # Iteration Info
    # -------------------------------------------------------------------------

    iteration_number: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        comment="Sequential iteration number (1-based)"
    )

    phase: Mapped[PipelineIterationPhase] = mapped_column(
        db.Enum(PipelineIterationPhase),
        default=PipelineIterationPhase.PROMPT_GENERATION,
        nullable=False,
        comment="Current phase within the iteration"
    )

    status: Mapped[PipelineIterationStatus] = mapped_column(
        db.Enum(PipelineIterationStatus),
        default=PipelineIterationStatus.RUNNING,
        nullable=False,
        index=True,
        comment="Iteration status"
    )

    # -------------------------------------------------------------------------
    # Prompt Data
    # -------------------------------------------------------------------------

    prompt_variants_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        db.JSON,
        nullable=True,
        comment="Prompt variants tested in this iteration"
    )

    # -------------------------------------------------------------------------
    # References to Existing Resources (REUSE)
    # -------------------------------------------------------------------------

    generation_job_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('generation_jobs.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Linked GenerationJob"
    )

    eval_scenario_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('rating_scenarios.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Linked evaluation scenario"
    )

    # -------------------------------------------------------------------------
    # Results
    # -------------------------------------------------------------------------

    scores_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        db.JSON,
        nullable=True,
        comment="Scores per model x prompt x dimension"
    )

    agent_reasoning: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Agent diagnosis and decision text"
    )

    delta_to_best: Mapped[Optional[float]] = mapped_column(
        db.Float,
        nullable=True,
        comment="Score improvement vs previous best"
    )

    # -------------------------------------------------------------------------
    # Cost Tracking
    # -------------------------------------------------------------------------

    tokens_used: Mapped[int] = mapped_column(
        db.Integer,
        default=0,
        nullable=False,
        comment="Tokens consumed in this iteration"
    )

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------

    started_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Iteration start time"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime,
        nullable=True,
        comment="Iteration completion time"
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------

    run: Mapped["PipelineRun"] = relationship(
        "PipelineRun",
        back_populates="iterations"
    )

    generation_job: Mapped[Optional["GenerationJob"]] = relationship(
        "GenerationJob",
        foreign_keys=[generation_job_id],
        backref="pipeline_iterations"
    )

    eval_scenario: Mapped[Optional["RatingScenarios"]] = relationship(
        "RatingScenarios",
        foreign_keys=[eval_scenario_id],
        backref="pipeline_iterations"
    )

    # -------------------------------------------------------------------------
    # Table Configuration
    # -------------------------------------------------------------------------

    __table_args__ = (
        db.UniqueConstraint('run_id', 'iteration_number', name='uq_pipeline_iteration_number'),
        db.Index('ix_pipeline_iterations_run_status', 'run_id', 'status'),
    )

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'run_id': self.run_id,
            'iteration_number': self.iteration_number,
            'phase': self.phase.value if self.phase else None,
            'status': self.status.value if self.status else None,
            'prompt_variants': self.prompt_variants_json,
            'generation_job_id': self.generation_job_id,
            'eval_scenario_id': self.eval_scenario_id,
            'scores': self.scores_json,
            'agent_reasoning': self.agent_reasoning,
            'delta_to_best': self.delta_to_best,
            'tokens_used': self.tokens_used,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<PipelineIteration {self.id}: "
            f"run={self.run_id} iter={self.iteration_number} "
            f"phase={self.phase.value} status={self.status.value}>"
        )
