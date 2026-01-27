"""
Batch Generation Service.

Orchestrates batch LLM generation jobs that apply prompts to items
using one or more LLM models.

Architecture:
    BatchGenerationService (this file)
        ├── Creates and manages GenerationJob instances
        ├── Builds the generation matrix (items × prompts × models)
        ├── Delegates actual generation to GenerationWorker
        └── Tracks progress and handles job lifecycle

Usage:
    from services.generation import BatchGenerationService

    # Create a job
    job = BatchGenerationService.create_job(
        name="Summarization Test",
        config={
            "sources": {"type": "scenario", "scenario_id": 123},
            "prompts": [{"template_id": 1, "variant_name": "Standard"}],
            "llm_models": ["gpt-4"],
            "generation_params": {"temperature": 0.7}
        },
        created_by="admin"
    )

    # Start the job
    BatchGenerationService.start_job(job.id)

    # Check status
    status = BatchGenerationService.get_job_status(job.id)
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from db import db
from db.models import (
    EvaluationItem,
    GeneratedOutput,
    GeneratedOutputStatus,
    GenerationJob,
    GenerationJobStatus,
    LLMModel,
    PromptTemplate,
    RatingScenarios,
    ScenarioItems,
    UserPrompt,
    get_pending_outputs_for_job,
)
from decorators.error_handler import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION SCHEMA
# =============================================================================

"""
Job Configuration Schema (config_json):

{
    "mode": "matrix",  # "matrix" (all combinations) or "sequential"

    "sources": {
        "type": "scenario" | "items" | "custom",
        "scenario_id": 123,           # if type=scenario
        "item_ids": [1, 2, 3],        # if type=items
        "custom_texts": ["text1", "text2"]  # if type=custom (no source items)
    },

    "prompts": [
        {
            "template_id": 1,
            "variant_name": "Standard",  # Human-readable name
            "variables": {}              # Optional variable overrides
        },
        {
            "template_id": 2,
            "variant_name": "Kurz",
            "variables": {"max_length": "50 Wörter"}
        }
    ],

    "llm_models": ["gpt-4", "claude-3-sonnet"],

    "generation_params": {
        "temperature": 0.7,
        "top_p": 1.0,
        "max_tokens": null
    },

    "output": {
        "create_scenario": false,
        "scenario_name": null,
        "evaluation_type": null
    },

    "limits": {
        "max_parallel": 5,          # Max parallel LLM requests
        "max_cost_usd": 10.0,       # Budget limit (optional)
        "max_retries": 3            # Retries per item
    }
}
"""


class BatchGenerationService:
    """
    Service for managing batch LLM generation jobs.

    This service handles:
    - Job creation with configuration validation
    - Generation matrix building (items × prompts × models)
    - Job lifecycle management (start, pause, cancel)
    - Progress tracking and status reporting
    """

    # -------------------------------------------------------------------------
    # Job Creation
    # -------------------------------------------------------------------------

    @classmethod
    def create_job(
        cls,
        name: str,
        config: Dict[str, Any],
        created_by: str,
        *,
        description: Optional[str] = None,
    ) -> GenerationJob:
        """
        Create a new batch generation job.

        This method:
        1. Validates the configuration
        2. Creates the GenerationJob record
        3. Creates all GeneratedOutput records (pending)
        4. Returns the job (not started yet)

        Args:
            name: Human-readable job name
            config: Job configuration (see schema above)
            created_by: Username who creates the job
            description: Optional longer description

        Returns:
            Created GenerationJob instance

        Raises:
            ValidationError: If configuration is invalid
        """
        logger.info("[BatchGen] Creating job '%s' by %s", name, created_by)

        # Validate configuration
        cls._validate_config(config)

        # Resolve source scenario if specified
        source_scenario_id = None
        sources_config = config.get("sources", {})
        if sources_config.get("type") == "scenario":
            source_scenario_id = sources_config.get("scenario_id")

        # Create the job
        job = GenerationJob(
            name=name,
            description=description,
            status=GenerationJobStatus.CREATED,
            config_json=config,
            source_scenario_id=source_scenario_id,
            total_items=0,
            completed_items=0,
            failed_items=0,
            total_tokens=0,
            total_cost_usd=0.0,
            created_by=created_by,
        )
        db.session.add(job)
        db.session.flush()  # Get job.id

        # Build the generation matrix and create outputs
        matrix = cls._build_generation_matrix(job.id, config)
        job.total_items = len(matrix)

        # Create GeneratedOutput records for each matrix entry
        cls._create_output_records(job.id, matrix)

        db.session.commit()
        logger.info(
            "[BatchGen] Created job %d with %d outputs to generate",
            job.id, job.total_items
        )

        return job

    @classmethod
    def _validate_config(cls, config: Dict[str, Any]) -> None:
        """
        Validate job configuration.

        Raises:
            ValidationError: If configuration is invalid
        """
        # Check required fields
        if "sources" not in config:
            raise ValidationError("Config missing 'sources' field")

        if "prompts" not in config or not config["prompts"]:
            raise ValidationError("Config missing 'prompts' field or prompts list is empty")

        if "llm_models" not in config or not config["llm_models"]:
            raise ValidationError("Config missing 'llm_models' field or models list is empty")

        # Validate sources
        sources = config["sources"]
        source_type = sources.get("type")
        if source_type not in ("scenario", "items", "custom", "manual", "prompt_only"):
            raise ValidationError(f"Invalid source type: {source_type}")

        if source_type == "scenario" and not sources.get("scenario_id"):
            raise ValidationError("Source type 'scenario' requires 'scenario_id'")

        if source_type == "items" and not sources.get("item_ids"):
            raise ValidationError("Source type 'items' requires 'item_ids'")

        if source_type == "custom" and not sources.get("custom_texts"):
            raise ValidationError("Source type 'custom' requires 'custom_texts'")

        if source_type == "manual" and not sources.get("items"):
            raise ValidationError("Source type 'manual' requires 'items'")

        # Validate prompts
        for i, prompt_cfg in enumerate(config["prompts"]):
            if not prompt_cfg.get("template_id"):
                raise ValidationError(f"Prompt {i} missing 'template_id'")

            template_id = prompt_cfg["template_id"]

            # Check UserPrompt first (from Prompt Engineering module)
            user_prompt = UserPrompt.query.get(template_id)
            if user_prompt:
                continue  # Valid user prompt found

            # Fall back to PromptTemplate (legacy)
            template = PromptTemplate.query.get(template_id)
            if not template:
                raise ValidationError(f"Prompt template {template_id} not found")
            if not template.is_active:
                raise ValidationError(f"Prompt template {template_id} is not active")

        # Validate LLM models (support both numeric IDs and string model_ids)
        for model_ref in config["llm_models"]:
            model = None

            # Try numeric ID first
            if isinstance(model_ref, int):
                model = LLMModel.query.get(model_ref)
            else:
                # Try string model_id
                model = LLMModel.get_by_model_id(model_ref)

            if not model:
                # Model might be external (LiteLLM), so just log warning
                logger.warning("[BatchGen] Model '%s' not in database, will use provider routing", model_ref)
            elif not model.is_active:
                raise ValidationError(f"LLM model '{model_ref}' is not active")

    @classmethod
    def _build_generation_matrix(
        cls,
        job_id: int,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build the generation matrix from configuration.

        Creates all combinations of:
        - Source items (or custom texts)
        - Prompt templates
        - LLM models

        Returns:
            List of matrix entries, each containing:
            {
                "source_item_id": int or None,
                "custom_text": str or None,
                "prompt_config": {...},
                "llm_model_name": str
            }
        """
        matrix = []

        # Resolve source items
        sources = config["sources"]
        source_type = sources.get("type")

        source_items: List[Optional[int]] = []
        custom_texts: List[Optional[str]] = []
        manual_structured_data: List[Dict[str, Any]] = []  # For manual items

        if source_type == "scenario":
            scenario_id = sources["scenario_id"]
            scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario_id).all()
            source_items = [si.item_id for si in scenario_items]
            custom_texts = [None] * len(source_items)
            logger.debug("[BatchGen] Resolved %d items from scenario %d", len(source_items), scenario_id)

        elif source_type == "items":
            source_items = sources["item_ids"]
            custom_texts = [None] * len(source_items)
            logger.debug("[BatchGen] Using %d direct item IDs", len(source_items))

        elif source_type == "custom":
            # No source items, just custom texts
            custom_texts = sources["custom_texts"]
            source_items = [None] * len(custom_texts)
            logger.debug("[BatchGen] Using %d custom texts", len(custom_texts))

        elif source_type == "manual":
            # Manual data upload - items with various formats:
            # - Simple: {"input": "text"} or {"content": "text"}
            # - Structured: {"subject": "...", "messages": [{role, content}]}
            manual_items = sources.get("items", [])
            custom_texts = []
            manual_structured_data = []  # Store structured data for later
            for item in manual_items:
                text = ""
                item_data = {"subject": "", "messages": []}
                # Try simple input/content fields first
                if item.get("input"):
                    text = item["input"]
                elif item.get("content"):
                    text = item["content"]
                # Handle structured messages format (email-style data)
                elif item.get("messages"):
                    messages = item["messages"]
                    item_data["messages"] = messages
                    item_data["subject"] = item.get("subject", "")
                    parts = []
                    if item.get("subject"):
                        parts.append(f"Betreff: {item['subject']}")
                    for msg in messages:
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        if role and content:
                            parts.append(f"{role}: {content}")
                        elif content:
                            parts.append(content)
                    text = "\n\n".join(parts)
                custom_texts.append(text)
                manual_structured_data.append(item_data)
            source_items = [None] * len(custom_texts)
            logger.debug("[BatchGen] Using %d manual items", len(custom_texts))

        elif source_type == "prompt_only":
            # No input data - just run prompt directly
            custom_texts = [""]  # Empty input, prompt is self-contained
            source_items = [None]
            logger.debug("[BatchGen] Prompt-only mode (no input data)")

        # Get prompts and models
        prompts = config["prompts"]
        llm_models = config["llm_models"]

        # Build matrix (all combinations)
        # Ensure manual_structured_data has entries for all items (empty for non-manual)
        if not manual_structured_data:
            manual_structured_data = [{"subject": "", "messages": []}] * len(custom_texts)

        for i, (item_id, custom_text) in enumerate(zip(source_items, custom_texts)):
            structured = manual_structured_data[i] if i < len(manual_structured_data) else {}
            for prompt_cfg in prompts:
                for model_name in llm_models:
                    matrix.append({
                        "source_item_id": item_id,
                        "source_index": i,  # Index in sources.items for later retrieval
                        "custom_text": custom_text,
                        "structured_data": structured,  # Include structured data
                        "prompt_config": prompt_cfg,
                        "llm_model_name": model_name,
                    })

        logger.info(
            "[BatchGen] Built matrix: %d items × %d prompts × %d models = %d total",
            len(source_items), len(prompts), len(llm_models), len(matrix)
        )

        return matrix

    @classmethod
    def _create_output_records(
        cls,
        job_id: int,
        matrix: List[Dict[str, Any]]
    ) -> None:
        """
        Create GeneratedOutput records for all matrix entries.

        All outputs start in PENDING status.
        """
        for entry in matrix:
            prompt_cfg = entry["prompt_config"]
            model_ref = entry["llm_model_name"]

            # Resolve LLM model (support both numeric IDs and string model_ids)
            llm_model_id = None
            llm_model_name = None
            if isinstance(model_ref, int):
                model = LLMModel.query.get(model_ref)
                if model:
                    llm_model_id = model.id
                    llm_model_name = model.model_id
            else:
                model = LLMModel.get_by_model_id(model_ref)
                llm_model_name = model_ref
                if model:
                    llm_model_id = model.id

            # Check if this is a UserPrompt (from Prompt Engineering) or PromptTemplate
            template_id = prompt_cfg["template_id"]
            prompt_template_id = None
            user_prompt = UserPrompt.query.get(template_id)
            if not user_prompt:
                # It's a PromptTemplate
                prompt_template_id = template_id

            # Build variables including custom input text if present
            variables = prompt_cfg.get("variables") or {}
            if entry.get("custom_text"):
                variables["input"] = entry["custom_text"]
            # Include structured data from manual items (subject, messages)
            structured = entry.get("structured_data", {})
            if structured.get("subject"):
                variables["subject"] = structured["subject"]
            if structured.get("messages"):
                variables["messages"] = structured["messages"]
            if user_prompt:
                variables["_user_prompt_id"] = template_id
            # Store source index for later retrieval during export
            if entry.get("source_index") is not None:
                variables["_source_index"] = entry["source_index"]

            output = GeneratedOutput(
                job_id=job_id,
                source_item_id=entry["source_item_id"],
                prompt_template_id=prompt_template_id,
                llm_model_id=llm_model_id,
                llm_model_name=llm_model_name or str(model_ref),
                prompt_variant_name=prompt_cfg.get("variant_name"),
                prompt_variables_json=variables if variables else None,
                status=GeneratedOutputStatus.PENDING,
            )
            db.session.add(output)

        logger.debug("[BatchGen] Created %d output records for job %d", len(matrix), job_id)

    # -------------------------------------------------------------------------
    # Job Lifecycle Management
    # -------------------------------------------------------------------------

    @classmethod
    def start_job(cls, job_id: int, *, socketio: Any = None) -> GenerationJob:
        """
        Start a generation job.

        The job is processed asynchronously in a background thread.

        Args:
            job_id: ID of the job to start
            socketio: Optional SocketIO instance for progress events

        Returns:
            Updated GenerationJob

        Raises:
            NotFoundError: If job not found
            ValidationError: If job cannot be started
        """
        job = cls._get_job_or_raise(job_id)

        if not job.can_start:
            raise ValidationError(
                f"Job {job_id} cannot be started (status: {job.status.value})"
            )

        # Update status
        job.status = GenerationJobStatus.QUEUED
        job.started_at = datetime.utcnow()
        db.session.commit()

        logger.info("[BatchGen] Starting job %d", job_id)

        # Start worker in background thread
        from services.generation.generation_worker import GenerationWorker

        def _run_job():
            try:
                # Import app for context
                from main import app
                with app.app_context():
                    worker = GenerationWorker(job_id, socketio=socketio)
                    worker.run()
            except Exception as e:
                logger.exception("[BatchGen] Job %d failed: %s", job_id, e)
                # Mark job as failed
                try:
                    from main import app
                    with app.app_context():
                        cls._mark_job_failed(job_id, str(e))
                except Exception:
                    logger.exception("[BatchGen] Could not mark job %d as failed", job_id)

        thread = threading.Thread(target=_run_job, daemon=True)
        thread.start()

        return job

    @classmethod
    def pause_job(cls, job_id: int) -> GenerationJob:
        """
        Pause a running job.

        The worker will stop after completing the current item.

        Args:
            job_id: ID of the job to pause

        Returns:
            Updated GenerationJob

        Raises:
            NotFoundError: If job not found
            ValidationError: If job cannot be paused
        """
        job = cls._get_job_or_raise(job_id)

        if not job.can_pause:
            raise ValidationError(
                f"Job {job_id} cannot be paused (status: {job.status.value})"
            )

        job.status = GenerationJobStatus.PAUSED
        db.session.commit()

        logger.info("[BatchGen] Paused job %d", job_id)
        return job

    @classmethod
    def cancel_job(cls, job_id: int) -> GenerationJob:
        """
        Cancel a job.

        The worker will stop and the job will be marked as cancelled.

        Args:
            job_id: ID of the job to cancel

        Returns:
            Updated GenerationJob

        Raises:
            NotFoundError: If job not found
            ValidationError: If job cannot be cancelled
        """
        job = cls._get_job_or_raise(job_id)

        if not job.can_cancel:
            raise ValidationError(
                f"Job {job_id} cannot be cancelled (status: {job.status.value})"
            )

        job.status = GenerationJobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        db.session.commit()

        logger.info("[BatchGen] Cancelled job %d", job_id)
        return job

    @classmethod
    def delete_job(cls, job_id: int) -> None:
        """
        Delete a job and all its outputs.

        Only completed, failed, or cancelled jobs can be deleted.

        Args:
            job_id: ID of the job to delete

        Raises:
            NotFoundError: If job not found
            ValidationError: If job cannot be deleted (still running)
        """
        job = cls._get_job_or_raise(job_id)

        if job.is_active:
            raise ValidationError(
                f"Cannot delete active job {job_id}. Cancel it first."
            )

        db.session.delete(job)
        db.session.commit()

        logger.info("[BatchGen] Deleted job %d", job_id)

    @classmethod
    def _mark_job_failed(cls, job_id: int, error: str) -> None:
        """Mark a job as failed with an error message."""
        job = GenerationJob.query.get(job_id)
        if job:
            job.status = GenerationJobStatus.FAILED
            job.error_message = error
            job.completed_at = datetime.utcnow()
            db.session.commit()

    @classmethod
    def _mark_job_completed(cls, job_id: int) -> None:
        """Mark a job as completed."""
        job = GenerationJob.query.get(job_id)
        if job:
            job.status = GenerationJobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            db.session.commit()
            logger.info("[BatchGen] Job %d completed", job_id)

    # -------------------------------------------------------------------------
    # Status and Queries
    # -------------------------------------------------------------------------

    @classmethod
    def get_job(cls, job_id: int) -> GenerationJob:
        """
        Get a job by ID.

        Args:
            job_id: Job ID

        Returns:
            GenerationJob instance

        Raises:
            NotFoundError: If job not found
        """
        return cls._get_job_or_raise(job_id)

    @classmethod
    def get_job_status(cls, job_id: int) -> Dict[str, Any]:
        """
        Get detailed status for a job.

        Returns:
            Dict with job status, progress, and statistics
        """
        job = cls._get_job_or_raise(job_id)
        result = job.to_dict(include_outputs=True)

        # Include currently processing output for reconnection support
        processing_output = GeneratedOutput.query.filter_by(
            job_id=job_id,
            status=GeneratedOutputStatus.PROCESSING
        ).first()

        if processing_output:
            result["currently_processing"] = {
                "output_id": processing_output.id,
                "model_name": processing_output.llm_model_name,
                "source_item_id": processing_output.source_item_id,
                "prompt_variant": processing_output.prompt_variant_name,
                "item_name": f"{processing_output.prompt_variant_name} (Item #{processing_output.source_item_id or processing_output.id})"
                    if processing_output.prompt_variant_name
                    else f"Item #{processing_output.source_item_id or processing_output.id}",
                # Include partial content for reconnection support
                "partial_content": processing_output.generated_content or ""
            }
        else:
            result["currently_processing"] = None

        return result

    @classmethod
    def get_jobs_for_user(
        cls,
        username: str,
        *,
        status: Optional[GenerationJobStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get jobs for a user.

        Args:
            username: User's username
            status: Optional status filter
            limit: Maximum number of jobs

        Returns:
            List of job summary dicts
        """
        jobs = GenerationJob.get_jobs_for_user(username, status=status, limit=limit)
        return [job.to_summary_dict() for job in jobs]

    @classmethod
    def get_job_outputs(
        cls,
        job_id: int,
        *,
        status: Optional[GeneratedOutputStatus] = None,
        page: int = 1,
        per_page: int = 50,
        include_prompts: bool = False
    ) -> Dict[str, Any]:
        """
        Get outputs for a job with pagination.

        Args:
            job_id: Job ID
            status: Optional status filter
            page: Page number (1-indexed)
            per_page: Items per page
            include_prompts: Whether to include rendered prompts

        Returns:
            Dict with 'items', 'total', 'page', 'pages'
        """
        cls._get_job_or_raise(job_id)  # Verify job exists

        query = GeneratedOutput.query.filter_by(job_id=job_id)
        if status:
            query = query.filter_by(status=status)

        query = query.order_by(GeneratedOutput.id)

        # Paginate
        total = query.count()
        pages = (total + per_page - 1) // per_page
        offset = (page - 1) * per_page

        outputs = query.offset(offset).limit(per_page).all()

        return {
            'items': [o.to_dict(include_prompts=include_prompts) for o in outputs],
            'total': total,
            'page': page,
            'pages': pages,
            'per_page': per_page,
        }

    @classmethod
    def get_output(cls, output_id: int) -> Dict[str, Any]:
        """
        Get a single output by ID.

        Args:
            output_id: Output ID

        Returns:
            Output dict with full details

        Raises:
            NotFoundError: If output not found
        """
        output = GeneratedOutput.query.get(output_id)
        if not output:
            raise NotFoundError(f"Output {output_id} not found")
        return output.to_dict(include_prompts=True)

    # -------------------------------------------------------------------------
    # Cost Estimation
    # -------------------------------------------------------------------------

    @classmethod
    def estimate_cost(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate cost for a job configuration before creating it.

        Args:
            config: Job configuration

        Returns:
            Dict with cost estimates:
            {
                "total_outputs": int,
                "estimated_cost_usd": float,
                "cost_breakdown": {...}
            }
        """
        cls._validate_config(config)

        # Count items
        sources = config["sources"]
        source_type = sources.get("type")

        if source_type == "scenario":
            scenario_id = sources["scenario_id"]
            item_count = ScenarioItems.query.filter_by(scenario_id=scenario_id).count()
        elif source_type == "items":
            item_count = len(sources["item_ids"])
        elif source_type == "manual":
            item_count = len(sources.get("items", []))
        elif source_type == "prompt_only":
            item_count = 1  # Single generation per prompt×model
        else:  # custom
            item_count = len(sources.get("custom_texts", []))

        prompt_count = len(config["prompts"])
        model_count = len(config["llm_models"])
        total_outputs = item_count * prompt_count * model_count

        # Estimate tokens (rough estimate: 500 input + 500 output per generation)
        avg_input_tokens = 500
        avg_output_tokens = 500

        # Calculate cost per model
        cost_breakdown = {}
        total_cost = 0.0

        for model_ref in config["llm_models"]:
            # Support both numeric IDs and string model_ids
            if isinstance(model_ref, int):
                model = LLMModel.query.get(model_ref)
                model_id = model.model_id if model else str(model_ref)
            else:
                model = LLMModel.get_by_model_id(model_ref)
                model_id = model_ref

            if model:
                outputs_for_model = item_count * prompt_count
                input_cost = (avg_input_tokens * outputs_for_model / 1_000_000) * model.input_cost_per_million
                output_cost = (avg_output_tokens * outputs_for_model / 1_000_000) * model.output_cost_per_million
                model_cost = input_cost + output_cost
                cost_breakdown[model_id] = {
                    "outputs": outputs_for_model,
                    "estimated_cost_usd": round(model_cost, 4)
                }
                total_cost += model_cost
            else:
                # Unknown model, use default estimate
                cost_breakdown[model_id] = {
                    "outputs": item_count * prompt_count,
                    "estimated_cost_usd": None,
                    "note": "Model not in database, cost unknown"
                }

        return {
            "total_outputs": total_outputs,
            "matrix": {
                "items": item_count,
                "prompts": prompt_count,
                "models": model_count,
            },
            "estimated_cost_usd": round(total_cost, 4),
            "cost_breakdown": cost_breakdown,
            "note": "Estimates based on ~500 input + 500 output tokens per generation"
        }

    # -------------------------------------------------------------------------
    # Job Progress Updates
    # -------------------------------------------------------------------------

    @classmethod
    def update_job_progress(
        cls,
        job_id: int,
        completed_delta: int = 0,
        failed_delta: int = 0,
        tokens_delta: int = 0,
        cost_delta: float = 0.0
    ) -> None:
        """
        Update job progress counters.

        Called by GenerationWorker after each output is processed.

        Args:
            job_id: Job ID
            completed_delta: Number of newly completed outputs
            failed_delta: Number of newly failed outputs
            tokens_delta: Tokens used
            cost_delta: Cost incurred
        """
        job = GenerationJob.query.get(job_id)
        if not job:
            return

        job.completed_items += completed_delta
        job.failed_items += failed_delta
        job.total_tokens += tokens_delta
        job.total_cost_usd += cost_delta

        db.session.commit()

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    @classmethod
    def _get_job_or_raise(cls, job_id: int) -> GenerationJob:
        """Get a job by ID or raise NotFoundError."""
        job = GenerationJob.query.get(job_id)
        if not job:
            raise NotFoundError(f"Generation job {job_id} not found")
        return job
