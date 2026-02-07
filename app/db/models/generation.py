"""
Batch Generation Database Models.

Models for orchestrating batch LLM generation jobs that connect
Prompt Engineering with Evaluation through generated outputs.

Architecture:
    GenerationJob (1) ──→ (N) GeneratedOutput

    GenerationJob orchestrates the batch process, tracking overall progress.
    GeneratedOutput stores individual generated items with full provenance
    (which prompt, which LLM, which source item produced this output).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import db

if TYPE_CHECKING:
    from db.models.scenario import EvaluationItem, RatingScenarios
    from db.models.prompt_template import PromptTemplate
    from db.models.llm_model import LLMModel


# =============================================================================
# ENUMS
# =============================================================================


class GenerationJobStatus(Enum):
    """
    Status states for batch generation jobs.

    Lifecycle:
        CREATED → QUEUED → RUNNING → COMPLETED
                    ↓         ↓
                 CANCELLED  PAUSED → RUNNING
                              ↓
                           FAILED
    """
    CREATED = 'created'      # Job erstellt, noch nicht gestartet
    QUEUED = 'queued'        # In der Warteschlange
    RUNNING = 'running'      # Aktiv in Bearbeitung
    PAUSED = 'paused'        # Pausiert (kann fortgesetzt werden)
    COMPLETED = 'completed'  # Erfolgreich abgeschlossen
    FAILED = 'failed'        # Fehlgeschlagen
    CANCELLED = 'cancelled'  # Vom Benutzer abgebrochen


class GeneratedOutputStatus(Enum):
    """
    Status states for individual generated outputs.

    Lifecycle:
        PENDING → PROCESSING → COMPLETED
                      ↓
                   FAILED → RETRYING → COMPLETED
                              ↓
                           FAILED (max retries)
    """
    PENDING = 'pending'        # Wartet auf Verarbeitung
    PROCESSING = 'processing'  # Wird gerade generiert
    COMPLETED = 'completed'    # Erfolgreich generiert
    FAILED = 'failed'          # Fehlgeschlagen
    RETRYING = 'retrying'      # Wird erneut versucht
    SKIPPED = 'skipped'        # Übersprungen (z.B. Budget-Limit)


# =============================================================================
# GENERATION JOB MODEL
# =============================================================================


class GenerationJob(db.Model):
    """
    A batch generation job that applies prompts to items using LLMs.

    The job orchestrates the generation process:
    1. Takes source items (from scenario or direct selection)
    2. Applies one or more prompt templates
    3. Uses one or more LLM models
    4. Produces GeneratedOutputs
    5. Optionally creates an evaluation scenario from outputs

    Example config_json:
    {
        "mode": "matrix",  # All combinations of items × prompts × models
        "sources": {
            "type": "scenario",
            "scenario_id": 123
        },
        "prompts": [
            {"template_id": 1, "variant_name": "Standard"},
            {"template_id": 2, "variant_name": "Kurz", "variables": {"max_length": "50"}}
        ],
        "llm_models": ["gpt-4", "claude-3-sonnet"],
        "generation_params": {
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "output": {
            "create_scenario": true,
            "scenario_name": "Zusammenfassungs-Vergleich",
            "evaluation_type": "ranking"
        }
    }

    Attributes:
        id: Primary key
        name: Human-readable name for the job
        description: Optional longer description
        status: Current job status (see GenerationJobStatus)
        config_json: Full job configuration (see example above)
        source_scenario_id: Optional source scenario for items
        target_scenario_id: Optional target scenario for outputs
        total_items: Total number of outputs to generate
        completed_items: Successfully completed outputs
        failed_items: Failed outputs
        total_tokens: Total tokens used across all outputs
        total_cost_usd: Estimated total cost in USD
        created_by: Username who created the job
        created_at: Creation timestamp
        started_at: When processing started
        completed_at: When processing finished
        error_message: Error message if job failed
    """

    __tablename__ = 'generation_jobs'

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
        comment="Human-readable job name"
    )

    description: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Optional longer description"
    )

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------

    status: Mapped[GenerationJobStatus] = mapped_column(
        db.Enum(GenerationJobStatus),
        default=GenerationJobStatus.CREATED,
        nullable=False,
        index=True,
        comment="Current job status"
    )

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    config_json: Mapped[Dict[str, Any]] = mapped_column(
        db.JSON,
        nullable=False,
        comment="Full job configuration including prompts, models, params"
    )

    # -------------------------------------------------------------------------
    # Source/Target References
    # -------------------------------------------------------------------------

    source_scenario_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('rating_scenarios.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Source scenario for input items (optional)"
    )

    target_scenario_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('rating_scenarios.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Target scenario created from outputs (optional)"
    )

    # -------------------------------------------------------------------------
    # Progress Tracking
    # -------------------------------------------------------------------------

    total_items: Mapped[int] = mapped_column(
        db.Integer,
        default=0,
        nullable=False,
        comment="Total number of outputs to generate"
    )

    completed_items: Mapped[int] = mapped_column(
        db.Integer,
        default=0,
        nullable=False,
        comment="Successfully completed outputs"
    )

    failed_items: Mapped[int] = mapped_column(
        db.Integer,
        default=0,
        nullable=False,
        comment="Failed outputs"
    )

    # -------------------------------------------------------------------------
    # Cost Tracking
    # -------------------------------------------------------------------------

    total_tokens: Mapped[int] = mapped_column(
        db.Integer,
        default=0,
        nullable=False,
        comment="Total tokens used (input + output)"
    )

    total_cost_usd: Mapped[float] = mapped_column(
        db.Float,
        default=0.0,
        nullable=False,
        comment="Estimated total cost in USD"
    )

    # -------------------------------------------------------------------------
    # Ownership
    # -------------------------------------------------------------------------

    created_by: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False,
        index=True,
        comment="Username who created the job"
    )

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When the job was created"
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime,
        nullable=True,
        comment="When processing started"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime,
        nullable=True,
        comment="When processing finished"
    )

    # -------------------------------------------------------------------------
    # Error Handling
    # -------------------------------------------------------------------------

    error_message: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Error message if job failed"
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------

    outputs: Mapped[List["GeneratedOutput"]] = relationship(
        "GeneratedOutput",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="GeneratedOutput.id"
    )

    source_scenario: Mapped[Optional["RatingScenarios"]] = relationship(
        "RatingScenarios",
        foreign_keys=[source_scenario_id],
        backref="generation_jobs_as_source"
    )

    target_scenario: Mapped[Optional["RatingScenarios"]] = relationship(
        "RatingScenarios",
        foreign_keys=[target_scenario_id],
        backref="generation_jobs_as_target"
    )

    # -------------------------------------------------------------------------
    # Table Configuration
    # -------------------------------------------------------------------------

    __table_args__ = (
        db.Index('ix_generation_jobs_created_by_status', 'created_by', 'status'),
        db.Index('ix_generation_jobs_created_at', 'created_at'),
    )

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def progress_percent(self) -> float:
        """Calculate progress as percentage (0-100)."""
        if self.total_items == 0:
            return 0.0
        return round((self.completed_items / self.total_items) * 100, 1)

    @property
    def is_active(self) -> bool:
        """Check if job is currently active (running or queued)."""
        return self.status in (GenerationJobStatus.RUNNING, GenerationJobStatus.QUEUED)

    @property
    def can_start(self) -> bool:
        """Check if job can be started."""
        return self.status in (GenerationJobStatus.CREATED, GenerationJobStatus.PAUSED)

    @property
    def can_pause(self) -> bool:
        """Check if job can be paused."""
        return self.status == GenerationJobStatus.RUNNING

    @property
    def can_cancel(self) -> bool:
        """Check if job can be cancelled."""
        return self.status in (
            GenerationJobStatus.CREATED,
            GenerationJobStatus.QUEUED,
            GenerationJobStatus.RUNNING,
            GenerationJobStatus.PAUSED
        )

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------

    def to_dict(self, include_outputs: bool = False) -> Dict[str, Any]:
        """
        Convert to dictionary for API responses.

        Args:
            include_outputs: Whether to include output summaries

        Returns:
            Dictionary representation of the job
        """
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'config': self.config_json,
            'source_scenario_id': self.source_scenario_id,
            'target_scenario_id': self.target_scenario_id,
            'progress': {
                'total': self.total_items,
                'completed': self.completed_items,
                'failed': self.failed_items,
                'percent': self.progress_percent,
            },
            'cost': {
                'total_tokens': self.total_tokens,
                'total_cost_usd': round(self.total_cost_usd, 4),
            },
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'can_start': self.can_start,
            'can_pause': self.can_pause,
            'can_cancel': self.can_cancel,
        }

        if include_outputs:
            result['outputs_summary'] = {
                'total': self.outputs.count(),
                'completed': self.outputs.filter_by(status=GeneratedOutputStatus.COMPLETED).count(),
                'failed': self.outputs.filter_by(status=GeneratedOutputStatus.FAILED).count(),
            }

        return result

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to lightweight summary for list views."""
        config = self.config_json or {}
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'progress_percent': self.progress_percent,
            'total_items': self.total_items,
            'completed_items': self.completed_items,
            'failed_items': self.failed_items,
            'total_cost_usd': self.total_cost_usd,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'config_json': {
                'prompts': config.get('prompts', []),
                'llm_models': config.get('llm_models', []),
            },
        }

    @classmethod
    def get_active_jobs_for_user(cls, username: str) -> List["GenerationJob"]:
        """Get all active jobs for a user."""
        return cls.query.filter(
            cls.created_by == username,
            cls.status.in_([GenerationJobStatus.RUNNING, GenerationJobStatus.QUEUED])
        ).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_jobs_for_user(
        cls,
        username: str,
        *,
        status: Optional[GenerationJobStatus] = None,
        limit: int = 50
    ) -> List["GenerationJob"]:
        """
        Get jobs for a user with optional filtering.

        Args:
            username: The user's username
            status: Optional status filter
            limit: Maximum number of jobs to return

        Returns:
            List of matching jobs
        """
        query = cls.query.filter_by(created_by=username)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.created_at.desc()).limit(limit).all()

    def __repr__(self) -> str:
        return f"<GenerationJob {self.id}: {self.name} ({self.status.value})>"


# =============================================================================
# GENERATED OUTPUT MODEL
# =============================================================================


class GeneratedOutput(db.Model):
    """
    A single generated output from a batch generation job.

    Stores full provenance information:
    - Which source item was used
    - Which prompt template was applied
    - Which LLM model generated this
    - The actual generated content
    - Token usage and timing metrics

    This model enables:
    1. Tracking exactly how each output was produced
    2. Comparing outputs from different prompts/models
    3. Creating evaluation scenarios from outputs
    4. Cost attribution and analysis

    Attributes:
        id: Primary key
        job_id: Foreign key to parent GenerationJob
        source_item_id: The input EvaluationItem used
        prompt_template_id: The PromptTemplate used
        llm_model_id: The LLMModel (DB ID) used
        llm_model_name: The model string identifier (e.g., "gpt-4")
        prompt_variant_name: Human-readable variant name
        generated_content: The actual generated text
        rendered_system_prompt: The final system prompt after variable substitution
        rendered_user_prompt: The final user prompt after variable substitution
        status: Current output status
        input_tokens: Tokens in the prompt
        output_tokens: Tokens in the response
        total_cost_usd: Cost for this specific generation
        processing_time_ms: How long generation took
        attempt_count: Number of generation attempts
        error_message: Error message if failed
        created_at: When the output was created
        completed_at: When generation finished
    """

    __tablename__ = 'generated_outputs'

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

    job_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('generation_jobs.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Parent generation job"
    )

    # -------------------------------------------------------------------------
    # Source Tracking
    # -------------------------------------------------------------------------

    source_item_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('evaluation_items.item_id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Source evaluation item"
    )

    prompt_template_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('prompt_templates.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Prompt template used"
    )

    llm_model_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('llm_models.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="LLM model DB ID"
    )

    # Store model name separately for resilience (in case model is deleted)
    llm_model_name: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False,
        comment="LLM model identifier string (e.g., 'gpt-4')"
    )

    # -------------------------------------------------------------------------
    # Variant Information
    # -------------------------------------------------------------------------

    prompt_variant_name: Mapped[Optional[str]] = mapped_column(
        db.String(100),
        nullable=True,
        comment="Human-readable prompt variant name"
    )

    prompt_variables_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        db.JSON,
        nullable=True,
        comment="Variable overrides applied to this generation"
    )

    # -------------------------------------------------------------------------
    # Generated Content
    # -------------------------------------------------------------------------

    generated_content: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="The generated text output"
    )

    # Store rendered prompts for debugging and reproducibility
    rendered_system_prompt: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Final system prompt after variable substitution"
    )

    rendered_user_prompt: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Final user prompt after variable substitution"
    )

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------

    status: Mapped[GeneratedOutputStatus] = mapped_column(
        db.Enum(GeneratedOutputStatus),
        default=GeneratedOutputStatus.PENDING,
        nullable=False,
        index=True,
        comment="Current output status"
    )

    # -------------------------------------------------------------------------
    # Token Tracking
    # -------------------------------------------------------------------------

    input_tokens: Mapped[int] = mapped_column(
        db.Integer,
        default=0,
        nullable=False,
        comment="Tokens in the prompt"
    )

    output_tokens: Mapped[int] = mapped_column(
        db.Integer,
        default=0,
        nullable=False,
        comment="Tokens in the response"
    )

    total_cost_usd: Mapped[float] = mapped_column(
        db.Float,
        default=0.0,
        nullable=False,
        comment="Cost for this specific generation"
    )

    # -------------------------------------------------------------------------
    # Timing
    # -------------------------------------------------------------------------

    processing_time_ms: Mapped[int] = mapped_column(
        db.Integer,
        default=0,
        nullable=False,
        comment="Generation time in milliseconds"
    )

    # -------------------------------------------------------------------------
    # Retry Handling
    # -------------------------------------------------------------------------

    attempt_count: Mapped[int] = mapped_column(
        db.Integer,
        default=0,
        nullable=False,
        comment="Number of generation attempts"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Error message if failed"
    )

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When output was created"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime,
        nullable=True,
        comment="When generation finished"
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------

    job: Mapped["GenerationJob"] = relationship(
        "GenerationJob",
        back_populates="outputs"
    )

    source_item: Mapped[Optional["EvaluationItem"]] = relationship(
        "EvaluationItem",
        backref="generated_outputs"
    )

    prompt_template: Mapped[Optional["PromptTemplate"]] = relationship(
        "PromptTemplate",
        backref="generated_outputs"
    )

    llm_model: Mapped[Optional["LLMModel"]] = relationship(
        "LLMModel",
        backref="generated_outputs"
    )

    # -------------------------------------------------------------------------
    # Table Configuration
    # -------------------------------------------------------------------------

    __table_args__ = (
        # Composite index for finding outputs by job and status
        db.Index('ix_generated_outputs_job_status', 'job_id', 'status'),
        # Composite index for finding outputs by source
        db.Index('ix_generated_outputs_source', 'source_item_id', 'prompt_template_id', 'llm_model_id'),
        # Index for querying pending items
        db.Index('ix_generated_outputs_pending', 'status', 'created_at'),
    )

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def total_tokens(self) -> int:
        """Total tokens (input + output)."""
        return self.input_tokens + self.output_tokens

    @property
    def is_complete(self) -> bool:
        """Check if generation is complete (success or failure)."""
        return self.status in (GeneratedOutputStatus.COMPLETED, GeneratedOutputStatus.FAILED)

    @property
    def content_preview(self) -> str:
        """Get a preview of the generated content (first 200 chars)."""
        if not self.generated_content:
            return ""
        content = self.generated_content.strip()
        if len(content) <= 200:
            return content
        return content[:197] + "..."

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------

    def to_dict(self, include_prompts: bool = False) -> Dict[str, Any]:
        """
        Convert to dictionary for API responses.

        Args:
            include_prompts: Whether to include rendered prompts

        Returns:
            Dictionary representation
        """
        llm_model_color = None
        if self.llm_model and getattr(self.llm_model, "color", None):
            llm_model_color = self.llm_model.color
        else:
            try:
                from db.models.llm_model import LLMModel
                llm_model_color = LLMModel.generate_color(self.llm_model_name)
            except Exception:
                llm_model_color = None

        result = {
            'id': self.id,
            'job_id': self.job_id,
            'source_item_id': self.source_item_id,
            'prompt_template_id': self.prompt_template_id,
            'llm_model_id': self.llm_model_id,
            'llm_model_name': self.llm_model_name,
            'llm_model_color': llm_model_color,
            'prompt_variant_name': self.prompt_variant_name,
            'prompt_variables': self.prompt_variables_json,
            'generated_content': self.generated_content,
            'content_preview': self.content_preview,
            'status': self.status.value if self.status else None,
            'tokens': {
                'input': self.input_tokens,
                'output': self.output_tokens,
                'total': self.total_tokens,
            },
            'cost_usd': round(self.total_cost_usd, 6),
            'processing_time_ms': self.processing_time_ms,
            'attempt_count': self.attempt_count,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

        if include_prompts:
            result['rendered_system_prompt'] = self.rendered_system_prompt
            result['rendered_user_prompt'] = self.rendered_user_prompt

        return result

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to lightweight summary for list views."""
        llm_model_color = None
        if self.llm_model and getattr(self.llm_model, "color", None):
            llm_model_color = self.llm_model.color
        else:
            try:
                from db.models.llm_model import LLMModel
                llm_model_color = LLMModel.generate_color(self.llm_model_name)
            except Exception:
                llm_model_color = None
        return {
            'id': self.id,
            'source_item_id': self.source_item_id,
            'llm_model_name': self.llm_model_name,
            'llm_model_color': llm_model_color,
            'prompt_variant_name': self.prompt_variant_name,
            'status': self.status.value if self.status else None,
            'content_preview': self.content_preview,
            'total_tokens': self.total_tokens,
        }

    def mark_processing(self) -> None:
        """Mark this output as currently being processed."""
        self.status = GeneratedOutputStatus.PROCESSING
        self.attempt_count += 1
        db.session.add(self)

    def mark_completed(
        self,
        content: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        processing_time_ms: int,
        rendered_system_prompt: Optional[str] = None,
        rendered_user_prompt: Optional[str] = None
    ) -> None:
        """
        Mark this output as successfully completed.

        Args:
            content: The generated content
            input_tokens: Tokens in the prompt
            output_tokens: Tokens in the response
            cost_usd: Cost for this generation
            processing_time_ms: Time taken
            rendered_system_prompt: Optional final system prompt
            rendered_user_prompt: Optional final user prompt
        """
        self.status = GeneratedOutputStatus.COMPLETED
        self.generated_content = content
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_cost_usd = cost_usd
        self.processing_time_ms = processing_time_ms
        self.completed_at = datetime.utcnow()
        self.error_message = None

        if rendered_system_prompt:
            self.rendered_system_prompt = rendered_system_prompt
        if rendered_user_prompt:
            self.rendered_user_prompt = rendered_user_prompt

        db.session.add(self)

    def mark_failed(self, error: str) -> None:
        """
        Mark this output as failed.

        Args:
            error: The error message
        """
        self.status = GeneratedOutputStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()
        db.session.add(self)

    def __repr__(self) -> str:
        return f"<GeneratedOutput {self.id}: job={self.job_id} model={self.llm_model_name} status={self.status.value}>"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_pending_outputs_for_job(job_id: int, limit: int = 100) -> List[GeneratedOutput]:
    """
    Get pending outputs for a job, ordered by creation time.

    Args:
        job_id: The generation job ID
        limit: Maximum number of outputs to return

    Returns:
        List of pending GeneratedOutput instances
    """
    return GeneratedOutput.query.filter_by(
        job_id=job_id,
        status=GeneratedOutputStatus.PENDING
    ).order_by(
        GeneratedOutput.created_at.asc()
    ).limit(limit).all()


def get_failed_outputs_for_job(job_id: int) -> List[GeneratedOutput]:
    """
    Get failed outputs for a job (for retry or review).

    Args:
        job_id: The generation job ID

    Returns:
        List of failed GeneratedOutput instances
    """
    return GeneratedOutput.query.filter_by(
        job_id=job_id,
        status=GeneratedOutputStatus.FAILED
    ).order_by(
        GeneratedOutput.created_at.asc()
    ).all()
