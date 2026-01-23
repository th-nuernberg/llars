"""
Output Export Service.

Handles export of generated outputs to various formats and creation
of evaluation scenarios from generated content.

Supported exports:
- CSV: Tabular format with all output metadata
- JSON: Full structured export
- Evaluation Scenario: Creates a new scenario with generated outputs as items

Usage:
    from services.generation import OutputExportService

    # Export to CSV
    csv_data = OutputExportService.export_to_csv(job_id)

    # Export to JSON
    json_data = OutputExportService.export_to_json(job_id)

    # Create evaluation scenario
    scenario = OutputExportService.create_evaluation_scenario(
        job_id=job_id,
        scenario_name="Summarization Comparison",
        evaluation_type="ranking",
        created_by="admin"
    )
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from db import db
from db.models import (
    EvaluationItem,
    FeatureFunctionType,
    GeneratedOutput,
    GeneratedOutputStatus,
    GenerationJob,
    Message,
    RatingScenarios,
    ScenarioItems,
    ScenarioRoles,
    ScenarioUsers,
)
from decorators.error_handler import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


# =============================================================================
# EVALUATION TYPE MAPPING
# =============================================================================

# Map evaluation type names to function_type_ids
EVALUATION_TYPE_MAP = {
    "ranking": 1,
    "rating": 2,
    "mail_rating": 3,
    "comparison": 4,
    "authenticity": 5,
    "labeling": 7,
}


class OutputExportService:
    """
    Service for exporting generated outputs.

    Supports:
    - CSV export with metadata
    - JSON export with full details
    - Creation of evaluation scenarios from outputs
    """

    # -------------------------------------------------------------------------
    # CSV Export
    # -------------------------------------------------------------------------

    @classmethod
    def export_to_csv(
        cls,
        job_id: int,
        *,
        include_prompts: bool = False,
        status_filter: Optional[GeneratedOutputStatus] = None
    ) -> io.BytesIO:
        """
        Export job outputs to CSV format.

        Args:
            job_id: The generation job ID
            include_prompts: Whether to include rendered prompts
            status_filter: Optional filter for output status

        Returns:
            BytesIO buffer containing CSV data

        Raises:
            NotFoundError: If job not found
        """
        job = cls._get_job_or_raise(job_id)
        outputs = cls._get_outputs(job_id, status_filter)

        logger.info("[Export] Exporting job %d to CSV (%d outputs)", job_id, len(outputs))

        # Define columns
        columns = [
            "id",
            "source_item_id",
            "prompt_template_id",
            "prompt_variant_name",
            "llm_model_name",
            "status",
            "generated_content",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "cost_usd",
            "processing_time_ms",
            "error_message",
            "created_at",
            "completed_at",
        ]

        if include_prompts:
            columns.extend(["rendered_system_prompt", "rendered_user_prompt"])

        # Create CSV
        output_buffer = io.StringIO()
        writer = csv.DictWriter(output_buffer, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()

        for o in outputs:
            row = {
                "id": o.id,
                "source_item_id": o.source_item_id,
                "prompt_template_id": o.prompt_template_id,
                "prompt_variant_name": o.prompt_variant_name,
                "llm_model_name": o.llm_model_name,
                "status": o.status.value if o.status else None,
                "generated_content": o.generated_content,
                "input_tokens": o.input_tokens,
                "output_tokens": o.output_tokens,
                "total_tokens": o.total_tokens,
                "cost_usd": round(o.total_cost_usd, 6),
                "processing_time_ms": o.processing_time_ms,
                "error_message": o.error_message,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "completed_at": o.completed_at.isoformat() if o.completed_at else None,
            }

            if include_prompts:
                row["rendered_system_prompt"] = o.rendered_system_prompt
                row["rendered_user_prompt"] = o.rendered_user_prompt

            writer.writerow(row)

        # Convert to bytes
        csv_content = output_buffer.getvalue()
        byte_buffer = io.BytesIO(csv_content.encode('utf-8'))
        byte_buffer.seek(0)

        return byte_buffer

    # -------------------------------------------------------------------------
    # JSON Export
    # -------------------------------------------------------------------------

    @classmethod
    def export_to_json(
        cls,
        job_id: int,
        *,
        include_prompts: bool = True,
        status_filter: Optional[GeneratedOutputStatus] = None
    ) -> Dict[str, Any]:
        """
        Export job outputs to JSON format.

        Args:
            job_id: The generation job ID
            include_prompts: Whether to include rendered prompts
            status_filter: Optional filter for output status

        Returns:
            Dict with job info and outputs

        Raises:
            NotFoundError: If job not found
        """
        job = cls._get_job_or_raise(job_id)
        outputs = cls._get_outputs(job_id, status_filter)

        logger.info("[Export] Exporting job %d to JSON (%d outputs)", job_id, len(outputs))

        return {
            "job": {
                "id": job.id,
                "name": job.name,
                "description": job.description,
                "status": job.status.value if job.status else None,
                "config": job.config_json,
                "progress": {
                    "total": job.total_items,
                    "completed": job.completed_items,
                    "failed": job.failed_items,
                },
                "cost": {
                    "total_tokens": job.total_tokens,
                    "total_cost_usd": round(job.total_cost_usd, 4),
                },
                "created_by": job.created_by,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            },
            "outputs": [o.to_dict(include_prompts=include_prompts) for o in outputs],
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "total_outputs": len(outputs),
                "filter": status_filter.value if status_filter else "all",
            }
        }

    # -------------------------------------------------------------------------
    # Evaluation Scenario Creation
    # -------------------------------------------------------------------------

    @classmethod
    def create_evaluation_scenario(
        cls,
        job_id: int,
        scenario_name: str,
        evaluation_type: str,
        created_by: str,
        *,
        description: Optional[str] = None,
        config_json: Optional[Dict[str, Any]] = None,
    ) -> RatingScenarios:
        """
        Create an evaluation scenario from generated outputs.

        This creates:
        1. A new RatingScenario
        2. EvaluationItems for each completed output
        3. ScenarioItems linking outputs to the scenario
        4. The creator as OWNER in ScenarioUsers

        Args:
            job_id: The generation job ID
            scenario_name: Name for the new scenario
            evaluation_type: Type of evaluation (ranking, rating, comparison, etc.)
            created_by: Username who creates the scenario
            description: Optional scenario description
            config_json: Optional scenario configuration

        Returns:
            Created RatingScenarios instance

        Raises:
            NotFoundError: If job not found
            ValidationError: If evaluation_type is invalid or no outputs
        """
        job = cls._get_job_or_raise(job_id)

        # Check if scenario was already created from this job
        if job.target_scenario_id:
            raise ValidationError(
                f"Job {job_id} already has a scenario created (ID: {job.target_scenario_id}). "
                "Each job can only create one scenario."
            )

        # Validate evaluation type
        if evaluation_type not in EVALUATION_TYPE_MAP:
            raise ValidationError(
                f"Invalid evaluation_type: {evaluation_type}. "
                f"Valid types: {list(EVALUATION_TYPE_MAP.keys())}"
            )

        # Get completed outputs
        outputs = cls._get_outputs(job_id, GeneratedOutputStatus.COMPLETED)
        if not outputs:
            raise ValidationError(f"Job {job_id} has no completed outputs to create scenario from")

        logger.info(
            "[Export] Creating %s scenario '%s' from job %d (%d outputs)",
            evaluation_type, scenario_name, job_id, len(outputs)
        )

        # Get or create function type
        function_type_id = EVALUATION_TYPE_MAP[evaluation_type]
        function_type = FeatureFunctionType.query.filter_by(function_type_id=function_type_id).first()
        if not function_type:
            # Create if not exists
            function_type = FeatureFunctionType(
                function_type_id=function_type_id,
                name=evaluation_type
            )
            db.session.add(function_type)
            db.session.flush()

        # Build scenario config
        scenario_config = config_json or {}
        scenario_config["source_generation_job_id"] = job_id
        scenario_config["generation_job_name"] = job.name

        # Create the scenario
        scenario = RatingScenarios(
            scenario_name=scenario_name,
            function_type_id=function_type_id,
            begin=datetime.utcnow(),
            end=datetime.utcnow(),  # Will be updated when scenario ends
            created_by=created_by,
            config_json=scenario_config,
        )
        db.session.add(scenario)
        db.session.flush()  # Get scenario.id

        # Create EvaluationItems from outputs
        item_ids = cls._create_evaluation_items_from_outputs(outputs, function_type_id)

        # Link items to scenario
        for item_id in item_ids:
            scenario_item = ScenarioItems(
                scenario_id=scenario.id,
                item_id=item_id
            )
            db.session.add(scenario_item)

        # Add creator as owner
        from db.models import User
        user = User.query.filter_by(username=created_by).first()
        if user:
            scenario_user = ScenarioUsers(
                scenario_id=scenario.id,
                user_id=user.id,
                role=ScenarioRoles.OWNER
            )
            db.session.add(scenario_user)

        # Update the generation job with target scenario
        job.target_scenario_id = scenario.id

        db.session.commit()

        logger.info(
            "[Export] Created scenario %d with %d items from job %d",
            scenario.id, len(item_ids), job_id
        )

        return scenario

    @classmethod
    def _create_evaluation_items_from_outputs(
        cls,
        outputs: List[GeneratedOutput],
        function_type_id: int
    ) -> List[int]:
        """
        Create EvaluationItems from GeneratedOutputs.

        Each output becomes one EvaluationItem with the generated content
        stored as a Message.

        Returns:
            List of created item IDs
        """
        from sqlalchemy import func

        item_ids = []

        # Get the current max chat_id to ensure uniqueness
        # Use a special range for generated content (starting at 1,000,000)
        max_chat_id_result = db.session.query(func.max(EvaluationItem.chat_id)).scalar()
        base_chat_id = max(max_chat_id_result or 0, 1_000_000) + 1

        for idx, output in enumerate(outputs):
            # Create EvaluationItem with unique chat_id
            # Each output gets a unique chat_id = base + index
            unique_chat_id = base_chat_id + idx

            item = EvaluationItem(
                chat_id=unique_chat_id,
                institut_id=0,  # Not used for generated content
                subject=f"Generated: {output.prompt_variant_name or 'Default'} / {output.llm_model_name}",
                sender=output.llm_model_name,
                function_type_id=function_type_id,
            )
            db.session.add(item)
            db.session.flush()  # Get item.item_id

            # Create Message with generated content
            message = Message(
                item_id=item.item_id,
                sender=output.llm_model_name,
                content=output.generated_content or "",
                timestamp=output.completed_at or datetime.utcnow(),
                generated_by=f"Generation Job {output.job_id}",
            )
            db.session.add(message)

            item_ids.append(item.item_id)

        return item_ids

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    @classmethod
    def get_job_statistics(cls, job_id: int) -> Dict[str, Any]:
        """
        Get detailed statistics for a job's outputs.

        Returns:
            Dict with statistics grouped by prompt/model
        """
        job = cls._get_job_or_raise(job_id)
        outputs = GeneratedOutput.query.filter_by(job_id=job_id).all()

        # Group by prompt variant
        by_prompt: Dict[str, Dict[str, Any]] = {}
        for o in outputs:
            key = o.prompt_variant_name or "Default"
            if key not in by_prompt:
                by_prompt[key] = {
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "tokens": 0,
                    "cost_usd": 0.0,
                }
            by_prompt[key]["total"] += 1
            if o.status == GeneratedOutputStatus.COMPLETED:
                by_prompt[key]["completed"] += 1
                by_prompt[key]["tokens"] += o.total_tokens
                by_prompt[key]["cost_usd"] += o.total_cost_usd
            elif o.status == GeneratedOutputStatus.FAILED:
                by_prompt[key]["failed"] += 1

        # Group by model
        by_model: Dict[str, Dict[str, Any]] = {}
        for o in outputs:
            key = o.llm_model_name
            if key not in by_model:
                by_model[key] = {
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "tokens": 0,
                    "cost_usd": 0.0,
                    "avg_processing_time_ms": 0,
                }
            by_model[key]["total"] += 1
            if o.status == GeneratedOutputStatus.COMPLETED:
                by_model[key]["completed"] += 1
                by_model[key]["tokens"] += o.total_tokens
                by_model[key]["cost_usd"] += o.total_cost_usd

        # Calculate average processing time
        for model_key, stats in by_model.items():
            completed_outputs = [
                o for o in outputs
                if o.llm_model_name == model_key and o.status == GeneratedOutputStatus.COMPLETED
            ]
            if completed_outputs:
                avg_time = sum(o.processing_time_ms for o in completed_outputs) / len(completed_outputs)
                stats["avg_processing_time_ms"] = round(avg_time, 0)

        return {
            "job_id": job_id,
            "job_name": job.name,
            "overall": {
                "total": len(outputs),
                "completed": sum(1 for o in outputs if o.status == GeneratedOutputStatus.COMPLETED),
                "failed": sum(1 for o in outputs if o.status == GeneratedOutputStatus.FAILED),
                "pending": sum(1 for o in outputs if o.status == GeneratedOutputStatus.PENDING),
                "total_tokens": job.total_tokens,
                "total_cost_usd": round(job.total_cost_usd, 4),
            },
            "by_prompt_variant": by_prompt,
            "by_model": by_model,
        }

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

    @classmethod
    def _get_outputs(
        cls,
        job_id: int,
        status_filter: Optional[GeneratedOutputStatus] = None
    ) -> List[GeneratedOutput]:
        """Get outputs for a job with optional status filter."""
        query = GeneratedOutput.query.filter_by(job_id=job_id)
        if status_filter:
            query = query.filter_by(status=status_filter)
        return query.order_by(GeneratedOutput.id).all()
