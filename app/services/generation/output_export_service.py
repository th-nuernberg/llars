"""
Output Export Service.

Handles export of generated outputs to various formats and creation
of evaluation scenarios from generated content.

SCHEMA GROUND TRUTH:
-------------------
Beim Export von Outputs und Erstellung von Evaluation-Szenarien
müssen die einheitlichen EvaluationData Schemas beachtet werden:

- Backend: app/schemas/evaluation_data_schemas.py (Pydantic Models)
- Frontend: llars-frontend/src/schemas/evaluationSchemas.js
- Transformer: app/services/evaluation/schema_transformer_service.py

WICHTIG für Szenario-Erstellung:
- Item.id: Technische ID (z.B. "item_1") - NIEMALS LLM-Namen!
- Item.label: UI-Anzeigename (generische Labels wie "Zusammenfassung 1")
- Item.source: {"type": "llm", "name": "model_name"} für LLM-Herkunft
- Message.generated_by: LLM-Modellname (für Tracking)

Dokumentation: .claude/plans/evaluation-data-schemas.md

Supported exports:
- CSV: Tabular format with all output metadata
- JSON: Full structured export (kann mit SchemaTransformer zu EvaluationData werden)
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
from datetime import datetime, timedelta
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
from schemas.evaluation_data_schemas import EvaluationType

logger = logging.getLogger(__name__)


# =============================================================================
# EVALUATION TYPE MAPPING (via unified schema)
# =============================================================================

def _get_evaluation_type_map() -> dict:
    """
    Get evaluation type to function_type_id mapping from unified schema.

    Uses EvaluationType enum from evaluation_data_schemas.py as ground truth.
    """
    return {et.value: et.to_function_type_id() for et in EvaluationType}


# Cached mapping for backward compatibility
EVALUATION_TYPE_MAP = _get_evaluation_type_map()


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
        use_legacy_format: bool = False,
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
            use_legacy_format: If True, uses old format (DEPRECATED)

        Returns:
            Created RatingScenarios instance

        Raises:
            NotFoundError: If job not found
            ValidationError: If evaluation_type is invalid or no outputs
        """
        # By default, use the fixed format with correct message handling
        if not use_legacy_format:
            return cls.create_evaluation_scenario_fixed(
                job_id=job_id,
                scenario_name=scenario_name,
                evaluation_type=evaluation_type,
                created_by=created_by,
                description=description,
                config_json=config_json,
            )

        # Legacy format (deprecated) - only used if explicitly requested
        logger.warning(
            "[Export] Using LEGACY format for scenario creation (deprecated). "
            "Use create_evaluation_scenario_fixed() or remove use_legacy_format=True."
        )

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
            "[Export] Creating %s scenario '%s' from job %d (%d outputs) [LEGACY]",
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
        # Set end date to 1 year from now by default (can be adjusted later)
        now = datetime.utcnow()
        scenario = RatingScenarios(
            scenario_name=scenario_name,
            function_type_id=function_type_id,
            begin=now,
            end=now + timedelta(days=365),  # Active for 1 year
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

        # Add creator as viewer (ownership is determined by created_by field)
        from db.models import User
        user = User.query.filter_by(username=created_by).first()
        if user:
            scenario_user = ScenarioUsers(
                scenario_id=scenario.id,
                user_id=user.id,
                role=ScenarioRoles.VIEWER
            )
            db.session.add(scenario_user)

        # Update the generation job with target scenario
        job.target_scenario_id = scenario.id

        db.session.commit()

        logger.info(
            "[Export] Created scenario %d with %d items from job %d [LEGACY]",
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
    # FIXED Evaluation Scenario Creation (with correct message formats)
    # -------------------------------------------------------------------------

    @classmethod
    def create_evaluation_scenario_fixed(
        cls,
        job_id: int,
        scenario_name: str,
        evaluation_type: str,
        created_by: str,
        *,
        description: Optional[str] = None,
        config_json: Optional[Dict[str, Any]] = None,
        response_role: Optional[str] = None,
    ) -> RatingScenarios:
        """
        Create an evaluation scenario with CORRECT message formats.

        This is a GENERALIZED approach that works for all evaluation types:
        1. Retrieves original messages from job config (sources.items)
        2. Creates messages with sender roles from source data
        3. Determines response role dynamically (or uses explicit response_role)
        4. Links generated content with LLM model attribution

        Args:
            job_id: The generation job ID
            scenario_name: Name for the new scenario
            evaluation_type: Type of evaluation (ranking, rating, mail_rating, etc.)
            created_by: Username who creates the scenario
            description: Optional scenario description
            config_json: Optional scenario configuration
            response_role: Optional explicit role for generated responses.
                          If not provided, role is determined from conversation pattern.

        Returns:
            Created RatingScenarios instance
        """
        job = cls._get_job_or_raise(job_id)

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

        # Get source items from job config
        job_config = job.config_json or {}
        source_items_list = job_config.get("sources", {}).get("items", [])
        source_items_by_id = {item.get("id"): item for item in source_items_list}

        # Get or create function type
        function_type_id = EVALUATION_TYPE_MAP[evaluation_type]
        function_type = FeatureFunctionType.query.filter_by(function_type_id=function_type_id).first()
        if not function_type:
            function_type = FeatureFunctionType(
                function_type_id=function_type_id,
                name=evaluation_type
            )
            db.session.add(function_type)
            db.session.flush()

        # Build scenario config with eval_type
        scenario_config = config_json or {}
        scenario_config["source_generation_job_id"] = job_id
        scenario_config["generation_job_name"] = job.name
        scenario_config["eval_type"] = evaluation_type

        # Add default eval config if not provided
        if "eval_config" not in scenario_config:
            scenario_config["eval_config"] = cls._get_default_eval_config(evaluation_type)

        # Create the scenario
        now = datetime.utcnow()
        scenario = RatingScenarios(
            scenario_name=scenario_name,
            function_type_id=function_type_id,
            begin=now,
            end=now + timedelta(days=365),
            created_by=created_by,
            config_json=scenario_config,
        )
        db.session.add(scenario)
        db.session.flush()

        # Create EvaluationItems with correct message format
        item_ids = cls._create_items_with_correct_format(
            outputs=outputs,
            function_type_id=function_type_id,
            evaluation_type=evaluation_type,
            source_items=source_items_by_id,
            job_name=job.name,
            response_role=response_role,
        )

        # Link items to scenario
        for item_id in item_ids:
            scenario_item = ScenarioItems(
                scenario_id=scenario.id,
                item_id=item_id
            )
            db.session.add(scenario_item)

        # Add creator as viewer (ownership is determined by created_by field)
        from db.models import User
        user = User.query.filter_by(username=created_by).first()
        if user:
            scenario_user = ScenarioUsers(
                scenario_id=scenario.id,
                user_id=user.id,
                role=ScenarioRoles.VIEWER
            )
            db.session.add(scenario_user)

        # Update the generation job with target scenario
        job.target_scenario_id = scenario.id

        db.session.commit()

        logger.info(
            "[Export] Created FIXED scenario %d with %d items from job %d",
            scenario.id, len(item_ids), job_id
        )

        return scenario

    @classmethod
    def _create_items_with_correct_format(
        cls,
        outputs: List[GeneratedOutput],
        function_type_id: int,
        evaluation_type: str,
        source_items: Dict[int, Dict[str, Any]],
        job_name: str,
        response_role: Optional[str] = None,
    ) -> List[int]:
        """
        Create EvaluationItems with correct message format.

        This is a GENERALIZED approach that works for all evaluation types:
        1. Original messages keep their role from source data
        2. Generated response gets a role determined by:
           - Explicit response_role parameter
           - Last different role in conversation (for dialogues)
           - "Response" as fallback

        Args:
            outputs: List of generated outputs
            function_type_id: Evaluation function type
            evaluation_type: Type name (for logging)
            source_items: Source items from job config
            job_name: Name of the generation job
            response_role: Optional explicit role for generated responses
        """
        from sqlalchemy import func
        import random

        item_ids = []

        # Get unique base for chat_id
        max_chat_id_result = db.session.query(func.max(EvaluationItem.chat_id)).scalar()
        base_chat_id = max(max_chat_id_result or 0, 1_000_000) + 1

        for idx, output in enumerate(outputs):
            # Get source data from variables or source_items
            variables = output.prompt_variables_json or {}
            messages_data = variables.get("messages", [])
            subject = variables.get("subject", "")

            # Try to find source item by index or ID
            source_idx = variables.get("source_index") or variables.get("_source_index")
            if source_idx is not None and source_idx < len(source_items):
                source_item = list(source_items.values())[source_idx]
                if not messages_data:
                    messages_data = source_item.get("messages", [])
                if not subject:
                    subject = source_item.get("subject", "")

            # Generate unique chat_id
            unique_chat_id = base_chat_id + idx + random.randint(0, 100000)

            # Create EvaluationItem
            item = EvaluationItem(
                chat_id=unique_chat_id,
                institut_id=None,
                subject=subject or f"Generated by {output.llm_model_name}",
                sender=job_name,
                function_type_id=function_type_id,
            )
            db.session.add(item)
            db.session.flush()

            # Create messages using unified approach
            cls._create_messages_unified(
                item=item,
                output=output,
                messages_data=messages_data,
                variables=variables,
                response_role=response_role,
            )

            item_ids.append(item.item_id)

        return item_ids

    @classmethod
    def _create_messages_unified(
        cls,
        item: EvaluationItem,
        output: GeneratedOutput,
        messages_data: List[Dict[str, Any]],
        variables: Dict[str, Any],
        response_role: Optional[str] = None,
    ) -> None:
        """
        Create messages with a unified, generalized approach.

        Works for all evaluation types:
        - Conversation-based (mail_rating, comparison): Multiple messages with roles
        - Content-based (rating, ranking, labeling): Source text + generated content

        Role determination for generated response:
        1. Use explicit response_role if provided
        2. For conversations: Use opposite of last message's role
        3. Fallback: "Response"

        Message structure from source data:
        {
            "role": "RoleName",      # Used as sender
            "content": "...",        # Message content
            "timestamp": "...",      # Optional timestamp
            "generated_by": "..."    # Optional, defaults to "Human"
        }
        """
        collected_roles = set()

        # 1. Create messages from source data (if available)
        if messages_data:
            for msg_data in messages_data:
                # Extract role - use as-is from data
                role = msg_data.get("role") or msg_data.get("sender") or "Source"
                content = msg_data.get("content", "")
                generated_by = msg_data.get("generated_by", "Human")

                collected_roles.add(role)

                # Parse timestamp
                timestamp = cls._parse_timestamp(msg_data.get("timestamp"))

                message = Message(
                    item_id=item.item_id,
                    sender=role,
                    content=content,
                    timestamp=timestamp,
                    generated_by=generated_by,
                )
                db.session.add(message)
        else:
            # No messages array - try to create from plain text variables
            source_data = (
                variables.get("input") or
                variables.get("content") or
                variables.get("text") or
                variables.get("source")
            )

            # Handle different source data formats
            if source_data:
                if isinstance(source_data, dict):
                    # Dict format: {"subject": "...", "content": "..."} or {"messages": [...]}
                    if "messages" in source_data:
                        # Nested messages - process them
                        for msg_data in source_data.get("messages", []):
                            role = msg_data.get("role") or msg_data.get("sender") or "Source"
                            content = msg_data.get("content", "")
                            collected_roles.add(role)
                            message = Message(
                                item_id=item.item_id,
                                sender=role,
                                content=str(content),
                                timestamp=cls._parse_timestamp(msg_data.get("timestamp")),
                                generated_by=msg_data.get("generated_by", "Human"),
                            )
                            db.session.add(message)
                    else:
                        # Simple dict with subject/content - combine into text
                        subject = source_data.get("subject", "")
                        content = source_data.get("content", "")
                        combined_text = f"{subject}\n\n{content}".strip() if subject else str(content)
                        source_msg = Message(
                            item_id=item.item_id,
                            sender="Source",
                            content=combined_text,
                            timestamp=datetime.utcnow(),
                            generated_by="Human",
                        )
                        db.session.add(source_msg)
                        collected_roles.add("Source")
                elif isinstance(source_data, list):
                    # List of messages - process each
                    for msg_data in source_data:
                        if isinstance(msg_data, dict):
                            role = msg_data.get("role") or msg_data.get("sender") or "Source"
                            content = msg_data.get("content", "")
                        else:
                            role = "Source"
                            content = str(msg_data)
                        collected_roles.add(role)
                        message = Message(
                            item_id=item.item_id,
                            sender=role,
                            content=str(content),
                            timestamp=datetime.utcnow(),
                            generated_by="Human",
                        )
                        db.session.add(message)
                else:
                    # Plain string
                    source_msg = Message(
                        item_id=item.item_id,
                        sender="Source",
                        content=str(source_data),
                        timestamp=datetime.utcnow(),
                        generated_by="Human",
                    )
                    db.session.add(source_msg)
                    collected_roles.add("Source")

        # 2. Determine role for generated response
        if response_role:
            # Explicit role provided
            gen_role = response_role
        elif messages_data:
            # For conversations: determine response role from pattern
            gen_role = cls._determine_response_role(messages_data, collected_roles)
        else:
            # Fallback for simple content
            gen_role = "Generated"

        # 3. Create message for generated content
        if output.generated_content:
            response_message = Message(
                item_id=item.item_id,
                sender=gen_role,
                content=output.generated_content,
                timestamp=output.completed_at or datetime.utcnow(),
                generated_by=output.llm_model_name,
            )
            db.session.add(response_message)

    @classmethod
    def _determine_response_role(
        cls,
        messages_data: List[Dict[str, Any]],
        collected_roles: set,
    ) -> str:
        """
        Determine the appropriate role for a generated response.

        Logic:
        1. If only one role exists, use "Response"
        2. If two roles exist (dialogue), use the opposite of the last message
        3. If more roles, use "Response" as fallback

        Common patterns:
        - Client/Counselor dialogue: Response should be Counselor
        - User/Assistant: Response should be Assistant
        - Question/Answer: Response should be Answer
        """
        if not messages_data:
            return "Response"

        # Get the last message's role
        last_role = messages_data[-1].get("role") or messages_data[-1].get("sender")

        if len(collected_roles) == 2:
            # Two-party dialogue - return the other role
            other_roles = collected_roles - {last_role}
            if other_roles:
                return other_roles.pop()

        # For single role or complex multi-party, use generic
        return "Response"

    @classmethod
    def _parse_timestamp(cls, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp from various formats."""
        if not timestamp_str:
            return datetime.utcnow()

        formats = [
            "%d.%m.%Y %H:%M",
            "%d.%m.%Y %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        return datetime.utcnow()

    @classmethod
    def _get_default_eval_config(cls, evaluation_type: str) -> Dict[str, Any]:
        """
        Get default eval config for an evaluation type.

        Returns appropriate default configuration based on the evaluation type.
        These are sensible defaults that can be overridden via config_json.
        """
        # Common base for multi-dimensional rating types
        base_rating_config = {
            "type": "multi-dimensional",
            "baseType": "rating",
            "min": 1,
            "max": 5,
            "step": 1,
            "showOverallScore": False,
            "allowFeedback": True,
        }

        # Standard LLM-as-Judge dimensions (works for most rating scenarios)
        # MUST match frontend preset in evaluationPresets.js ('llm-judge-standard')
        standard_dimensions = [
            {
                "id": "coherence",
                "name": {"de": "Kohärenz", "en": "Coherence"},
                "weight": 0.25
            },
            {
                "id": "fluency",
                "name": {"de": "Flüssigkeit", "en": "Fluency"},
                "weight": 0.25
            },
            {
                "id": "relevance",
                "name": {"de": "Relevanz", "en": "Relevance"},
                "weight": 0.25
            },
            {
                "id": "consistency",
                "name": {"de": "Konsistenz", "en": "Consistency"},
                "weight": 0.25
            }
        ]

        standard_labels = {
            "1": {"de": "Sehr schlecht", "en": "Very poor"},
            "2": {"de": "Schlecht", "en": "Poor"},
            "3": {"de": "Durchschnittlich", "en": "Average"},
            "4": {"de": "Gut", "en": "Good"},
            "5": {"de": "Sehr gut", "en": "Very good"}
        }

        configs = {
            "mail_rating": {
                "presetId": "mail-verlauf-bewertung",
                "config": {
                    **base_rating_config,
                    "dimensions": [
                        {
                            "id": "client_coherence",
                            "name": {"de": "Kohärenz ratsuchende Person", "en": "Client Coherence"},
                            "weight": 0.25
                        },
                        {
                            "id": "counsellor_coherence",
                            "name": {"de": "Kohärenz beratende Person", "en": "Counsellor Coherence"},
                            "weight": 0.25
                        },
                        {
                            "id": "quality",
                            "name": {"de": "Beratungsqualität", "en": "Counseling Quality"},
                            "weight": 0.25
                        },
                        {
                            "id": "overall",
                            "name": {"de": "Gesamtbewertung", "en": "Overall Rating"},
                            "weight": 0.25
                        }
                    ],
                    "labels": standard_labels,
                }
            },
            "rating": {
                "presetId": "llm-judge-standard",
                "config": {
                    **base_rating_config,
                    "dimensions": standard_dimensions,
                    "labels": standard_labels,
                }
            },
            "ranking": {
                "presetId": "ranking-default",
                "config": {
                    "type": "ranking",
                    "allowTies": False,
                    "showPosition": True,
                }
            },
            "comparison": {
                "presetId": "comparison-default",
                "config": {
                    "type": "comparison",
                    "options": ["A is better", "B is better", "Tie"],
                    "allowFeedback": True,
                }
            },
            "labeling": {
                "presetId": "labeling-default",
                "config": {
                    "type": "labeling",
                    "multiSelect": False,
                    "categories": [],  # To be filled by user
                }
            },
            "authenticity": {
                "presetId": "authenticity-default",
                "config": {
                    "type": "binary",
                    "options": [
                        {"value": "real", "label": {"de": "Echt", "en": "Real"}},
                        {"value": "fake", "label": {"de": "Fake", "en": "Fake"}},
                    ],
                    "allowFeedback": True,
                }
            },
        }

        return configs.get(evaluation_type, configs["rating"])

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
