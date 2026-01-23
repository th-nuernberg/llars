"""
Generation Worker.

Processes batch generation jobs by executing LLM calls for each
pending output in the generation matrix.

Architecture:
    GenerationWorker
        ├── Fetches pending GeneratedOutput records
        ├── Renders prompts with PromptTemplateService
        ├── Calls LLMs via LLMClientFactory
        ├── Updates output records with results
        ├── Emits Socket.IO progress events
        └── Handles errors and retries

Usage:
    from services.generation import GenerationWorker

    worker = GenerationWorker(job_id, socketio=socketio)
    worker.run()  # Blocks until job is complete

    # Or with async start:
    GenerationWorker.start_async(job_id, socketio=socketio)
"""

from __future__ import annotations

import logging
import time
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
    Message,
    PromptTemplate,
    UserPrompt,
    get_pending_outputs_for_job,
)
from llm.openai_utils import extract_message_text
from services.evaluation import PromptTemplateService
from services.llm.llm_client_factory import LLMClientFactory

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Default limits
DEFAULT_MAX_PARALLEL = 5
DEFAULT_MAX_RETRIES = 3
DEFAULT_BATCH_SIZE = 10

# Retry delays (exponential backoff)
RETRY_DELAYS = [1, 5, 15]  # seconds


class GenerationWorker:
    """
    Worker that processes a batch generation job.

    The worker:
    1. Fetches pending outputs in batches
    2. Processes each output (render prompt, call LLM, save result)
    3. Handles errors with retry logic
    4. Emits progress events via Socket.IO
    5. Respects pause/cancel signals from the job status

    Attributes:
        job_id: The generation job ID
        socketio: Optional SocketIO instance for progress events
        should_stop: Flag to signal worker to stop
    """

    def __init__(
        self,
        job_id: int,
        *,
        socketio: Any = None,
    ):
        """
        Initialize the worker.

        Args:
            job_id: The generation job ID to process
            socketio: Optional SocketIO instance for progress events
        """
        self.job_id = job_id
        self.socketio = socketio
        self.should_stop = False

        # Cache for templates and models
        self._template_cache: Dict[int, PromptTemplate] = {}
        self._model_cache: Dict[str, LLMModel] = {}

    # -------------------------------------------------------------------------
    # Main Entry Point
    # -------------------------------------------------------------------------

    def run(self) -> None:
        """
        Run the worker until job is complete, paused, or cancelled.

        This is the main entry point. It processes all pending outputs
        and updates the job status when done.
        """
        logger.info("[GenWorker] Starting job %d", self.job_id)

        # Update job status to RUNNING
        job = self._update_job_status(GenerationJobStatus.RUNNING)
        if not job:
            logger.error("[GenWorker] Job %d not found", self.job_id)
            return

        # Get configuration
        config = job.config_json or {}
        limits = config.get("limits", {})
        max_retries = limits.get("max_retries", DEFAULT_MAX_RETRIES)
        max_cost = limits.get("max_cost_usd")

        # Emit start event
        self._emit_event("generation:job:started", {
            "job_id": self.job_id,
            "total_items": job.total_items,
        })

        try:
            # Process outputs in batches
            while not self.should_stop:
                # Check job status (for pause/cancel)
                job = GenerationJob.query.get(self.job_id)
                if not job or job.status not in (GenerationJobStatus.RUNNING, GenerationJobStatus.QUEUED):
                    logger.info("[GenWorker] Job %d status changed to %s, stopping",
                               self.job_id, job.status.value if job else "deleted")
                    break

                # Check budget limit
                if max_cost and job.total_cost_usd >= max_cost:
                    logger.warning("[GenWorker] Job %d exceeded budget limit ($%.2f)",
                                  self.job_id, max_cost)
                    self._update_job_status(GenerationJobStatus.PAUSED)
                    self._emit_event("generation:job:budget_exceeded", {
                        "job_id": self.job_id,
                        "cost": job.total_cost_usd,
                        "limit": max_cost,
                    })
                    break

                # Fetch pending outputs
                pending = get_pending_outputs_for_job(self.job_id, limit=DEFAULT_BATCH_SIZE)
                if not pending:
                    # No more pending outputs, job is complete
                    logger.info("[GenWorker] Job %d has no more pending outputs", self.job_id)
                    break

                # Process batch
                for output in pending:
                    if self.should_stop:
                        break

                    self._process_output(output, max_retries=max_retries)

            # Determine final status
            job = GenerationJob.query.get(self.job_id)
            if job and job.status == GenerationJobStatus.RUNNING:
                # Check if all outputs are processed
                pending_count = GeneratedOutput.query.filter_by(
                    job_id=self.job_id,
                    status=GeneratedOutputStatus.PENDING
                ).count()

                if pending_count == 0:
                    self._update_job_status(GenerationJobStatus.COMPLETED)
                    self._emit_event("generation:job:completed", {
                        "job_id": self.job_id,
                        "completed": job.completed_items,
                        "failed": job.failed_items,
                        "total_cost_usd": job.total_cost_usd,
                    })
                else:
                    # Still pending items but worker stopped (should not happen)
                    logger.warning("[GenWorker] Job %d has %d pending items but worker stopped",
                                  self.job_id, pending_count)

        except Exception as e:
            logger.exception("[GenWorker] Job %d failed with error: %s", self.job_id, e)
            self._update_job_status(GenerationJobStatus.FAILED, error=str(e))
            self._emit_event("generation:job:failed", {
                "job_id": self.job_id,
                "error": str(e),
            })

        logger.info("[GenWorker] Job %d finished", self.job_id)

    def stop(self) -> None:
        """Signal the worker to stop after the current item."""
        self.should_stop = True
        logger.info("[GenWorker] Stop signal received for job %d", self.job_id)

    # -------------------------------------------------------------------------
    # Output Processing
    # -------------------------------------------------------------------------

    def _process_output(self, output: GeneratedOutput, max_retries: int) -> None:
        """
        Process a single output.

        Steps:
        1. Mark as processing
        2. Render prompts
        3. Call LLM
        4. Save result or error
        5. Update job progress
        """
        start_time = time.time()

        try:
            # Mark as processing
            output.mark_processing()
            db.session.commit()

            # Emit started event for real-time UI updates
            self._emit_event("generation:item:started", {
                "job_id": self.job_id,
                "output_id": output.id,
                "model_name": output.llm_model_name,
                "source_item_id": output.source_item_id,
                "prompt_variant": output.prompt_variant_name,
            })

            # Get template and render prompts
            template = self._get_template(output.prompt_template_id, output)
            system_prompt, user_prompt = self._render_prompts(output, template)

            # Store rendered prompts
            output.rendered_system_prompt = system_prompt
            output.rendered_user_prompt = user_prompt

            # Call LLM (with streaming if socketio is available)
            content, tokens = self._call_llm(
                model_id=output.llm_model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output_id=output.id,
            )

            # Calculate cost
            cost = self._calculate_cost(output.llm_model_name, tokens)
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Mark as completed
            output.mark_completed(
                content=content,
                input_tokens=tokens["input"],
                output_tokens=tokens["output"],
                cost_usd=cost,
                processing_time_ms=processing_time_ms,
                rendered_system_prompt=system_prompt,
                rendered_user_prompt=user_prompt,
            )
            db.session.commit()

            # Update job progress
            self._update_job_progress(
                completed_delta=1,
                tokens_delta=tokens["total"],
                cost_delta=cost
            )

            # Emit success event
            self._emit_event("generation:item:completed", {
                "job_id": self.job_id,
                "output_id": output.id,
                "content_preview": output.content_preview,
                "tokens": tokens,
                "cost_usd": cost,
            })

            logger.debug("[GenWorker] Output %d completed (job %d)", output.id, self.job_id)

        except Exception as e:
            logger.warning("[GenWorker] Output %d failed (attempt %d): %s",
                          output.id, output.attempt_count, e)

            # Check if we should retry
            if output.attempt_count < max_retries:
                # Reset to pending for retry
                output.status = GeneratedOutputStatus.RETRYING
                output.error_message = str(e)
                db.session.commit()

                # Wait before retry (exponential backoff)
                delay = RETRY_DELAYS[min(output.attempt_count - 1, len(RETRY_DELAYS) - 1)]
                logger.info("[GenWorker] Retrying output %d in %d seconds", output.id, delay)
                time.sleep(delay)

                # Retry
                self._process_output(output, max_retries)
            else:
                # Max retries exceeded, mark as failed
                output.mark_failed(str(e))
                db.session.commit()

                # Update job progress
                self._update_job_progress(failed_delta=1)

                # Emit failure event
                self._emit_event("generation:item:failed", {
                    "job_id": self.job_id,
                    "output_id": output.id,
                    "error": str(e),
                    "attempts": output.attempt_count,
                })

    def _render_prompts(
        self,
        output: GeneratedOutput,
        template
    ) -> Tuple[str, str]:
        """
        Render system and user prompts for an output.

        Supports both PromptTemplate and UserPrompt (from Prompt Engineering).
        Uses the source item content and any variable overrides.

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Get source content
        content = self._get_source_content(output)

        # Build variables
        variables = {
            "content": content,
            "input": content,  # Common variable name
            "text_content": content,
            "thread_content": content,
        }

        # Add any custom variables from output config (excluding internal keys)
        if output.prompt_variables_json:
            for key, value in output.prompt_variables_json.items():
                if not key.startswith('_'):  # Skip internal keys like _user_prompt_id
                    variables[key] = value

        # Handle UserPrompt (from Prompt Engineering)
        if isinstance(template, UserPrompt):
            return self._render_user_prompt(template, variables)

        # Handle PromptTemplate (legacy)
        user_prompt = PromptTemplateService.render_prompt(template, **variables)
        return template.system_prompt or "", user_prompt

    def _render_user_prompt(
        self,
        user_prompt: UserPrompt,
        variables: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Render prompts from UserPrompt (Prompt Engineering module).

        UserPrompt stores content as JSON with blocks structure:
        {
            "blocks": {
                "system": {"content": "...", "position": 0},
                "instructions": {"content": "...", "position": 1}
            }
        }
        """
        content = user_prompt.content
        if not isinstance(content, dict):
            return "", str(content) if content else ""

        blocks = content.get('blocks', {})
        if not blocks:
            return "", ""

        # Sort blocks by position
        sorted_blocks = sorted(
            blocks.items(),
            key=lambda x: x[1].get('position', 0) if isinstance(x[1], dict) else 0
        )

        # Extract system prompt (if exists) and build user prompt
        system_prompt = ""
        user_prompt_parts = []

        for block_id, block_data in sorted_blocks:
            if isinstance(block_data, dict):
                block_content = block_data.get('content', '')
                if block_content:
                    # Substitute variables ({{variable_name}})
                    rendered = self._substitute_variables(block_content, variables)

                    if block_id.lower() == 'system':
                        system_prompt = rendered
                    else:
                        user_prompt_parts.append(rendered)

        return system_prompt, '\n\n'.join(user_prompt_parts)

    def _substitute_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute {{variable}} placeholders in text."""
        import re
        pattern = r'\{\{(\w+)\}\}'

        def replace(match):
            var_name = match.group(1)
            value = variables.get(var_name, match.group(0))
            return self._format_variable_value(value)

        return re.sub(pattern, replace, text)

    def _format_variable_value(self, value: Any) -> str:
        """
        Format a variable value for prompt substitution.

        Handles special cases:
        - messages array: Format as readable email thread
        - lists: Join with newlines
        - dicts: Format as readable text
        - other: Convert to string
        """
        if value is None:
            return ""

        # Handle messages array (email thread format)
        if isinstance(value, list) and len(value) > 0:
            first_item = value[0]
            # Check if it looks like a messages array (has 'role' or 'content' keys)
            if isinstance(first_item, dict) and ('role' in first_item or 'content' in first_item):
                return self._format_messages_array(value)
            # Generic list: join with newlines
            return "\n".join(str(item) for item in value)

        # Handle dict
        if isinstance(value, dict):
            return str(value)

        return str(value)

    def _format_messages_array(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format a messages array as a readable email thread.

        Expected message format:
        {
            "role": "Ratsuchende" or "Beratende",
            "content": "message text",
            "timestamp": "optional timestamp"
        }
        """
        formatted_parts = []

        for msg in messages:
            role = msg.get('role', 'Unbekannt')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')

            # Map roles to readable labels
            if role.lower() in ('ratsuchende', 'klient', 'client', 'user'):
                role_label = 'Klient'
            elif role.lower() in ('beratende', 'berater', 'counselor', 'assistant'):
                role_label = 'Berater'
            else:
                role_label = role

            # Format message
            header = f"[{role_label}]"
            if timestamp:
                header += f" ({timestamp})"

            formatted_parts.append(f"{header}\n{content}")

        return "\n\n---\n\n".join(formatted_parts)

    def _get_source_content(self, output: GeneratedOutput) -> str:
        """
        Get the source content for an output.

        Sources (in priority order):
        1. Input variable stored in prompt_variables_json (manual data)
        2. Source EvaluationItem content
        3. Custom text from job config

        Returns:
            Source content string
        """
        # Check for input in variables (from manual data upload)
        if output.prompt_variables_json:
            input_text = output.prompt_variables_json.get('input')
            if input_text:
                return input_text

        if output.source_item_id:
            # Get content from EvaluationItem
            item = EvaluationItem.query.get(output.source_item_id)
            if item:
                # Get messages for this item
                messages = Message.query.filter_by(item_id=item.item_id).order_by(
                    Message.timestamp.asc()
                ).all()

                if messages:
                    return "\n".join(f"{msg.sender}: {msg.content}" for msg in messages)

                # Fallback to subject if no messages
                return item.subject or ""

        # Check for custom text in job config
        job = GenerationJob.query.get(output.job_id)
        if job and job.config_json:
            sources = job.config_json.get("sources", {})
            if sources.get("type") == "custom":
                texts = sources.get("custom_texts", [])
                # Find the index of this output among custom text outputs
                # (simplified: just use the first text for now)
                if texts:
                    return texts[0]

        return ""

    def _call_llm(
        self,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        output_id: Optional[int] = None,
    ) -> Tuple[str, Dict[str, int]]:
        """
        Call the LLM and return the response with streaming support.

        Args:
            model_id: The model identifier
            system_prompt: System prompt
            user_prompt: User prompt
            output_id: Optional output ID for streaming events

        Returns:
            Tuple of (content, tokens_dict)

        Raises:
            Exception: If LLM call fails
        """
        # Get client
        client = LLMClientFactory.get_client_for_model(model_id)

        # Get generation params from job config
        job = GenerationJob.query.get(self.job_id)
        config = job.config_json if job else {}
        gen_params = config.get("generation_params", {})

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Check if streaming is enabled (default: True for real-time updates)
        enable_streaming = self.socketio is not None and output_id is not None

        if enable_streaming:
            # Streaming call
            content = ""
            tokens = {"input": 0, "output": 0, "total": 0}

            try:
                stream = client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    temperature=gen_params.get("temperature", 0.7),
                    max_tokens=gen_params.get("max_tokens", 1000),
                    top_p=gen_params.get("top_p", 1.0),
                    stream=True,
                )

                # Collect streamed content and emit tokens
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            token = delta.content
                            content += token
                            # Emit token for real-time streaming
                            self._emit_event("generation:item:token", {
                                "job_id": self.job_id,
                                "output_id": output_id,
                                "token": token,
                            })

                # Estimate tokens for streaming (actual count not always available)
                # Use rough estimation: ~4 chars per token
                tokens["output"] = max(1, len(content) // 4)
                tokens["input"] = max(1, (len(system_prompt) + len(user_prompt)) // 4)
                tokens["total"] = tokens["input"] + tokens["output"]

            except Exception as e:
                logger.warning("[GenWorker] Streaming failed, falling back to non-streaming: %s", e)
                # Fall back to non-streaming on error
                enable_streaming = False

        if not enable_streaming:
            # Non-streaming call
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=gen_params.get("temperature", 0.7),
                max_tokens=gen_params.get("max_tokens", 1000),
                top_p=gen_params.get("top_p", 1.0),
            )

            # Extract content
            content = ""
            if response.choices:
                content = extract_message_text(response.choices[0].message)

            # Extract token counts
            tokens = {"input": 0, "output": 0, "total": 0}
            if hasattr(response, "usage") and response.usage:
                tokens["input"] = getattr(response.usage, "prompt_tokens", 0)
                tokens["output"] = getattr(response.usage, "completion_tokens", 0)
                tokens["total"] = tokens["input"] + tokens["output"]

        return content, tokens

    def _calculate_cost(self, model_id: str, tokens: Dict[str, int]) -> float:
        """
        Calculate the cost for a generation.

        Args:
            model_id: The model identifier
            tokens: Token counts dict

        Returns:
            Cost in USD
        """
        model = self._get_model(model_id)
        if not model:
            return 0.0

        input_cost = (tokens["input"] / 1_000_000) * model.input_cost_per_million
        output_cost = (tokens["output"] / 1_000_000) * model.output_cost_per_million

        return input_cost + output_cost

    # -------------------------------------------------------------------------
    # Cache Helpers
    # -------------------------------------------------------------------------

    def _get_template(self, template_id: Optional[int], output: GeneratedOutput = None):
        """
        Get a template from cache or database.

        Supports both PromptTemplate and UserPrompt (from Prompt Engineering).
        If template_id is None, checks for _user_prompt_id in output variables.

        Returns:
            Either PromptTemplate or UserPrompt object
        """
        # Check if this is a UserPrompt (stored in variables)
        user_prompt_id = None
        if output and output.prompt_variables_json:
            user_prompt_id = output.prompt_variables_json.get('_user_prompt_id')

        if user_prompt_id:
            cache_key = f"user_{user_prompt_id}"
            if cache_key not in self._template_cache:
                user_prompt = UserPrompt.query.get(user_prompt_id)
                if not user_prompt:
                    raise ValueError(f"UserPrompt {user_prompt_id} not found")
                self._template_cache[cache_key] = user_prompt
            return self._template_cache[cache_key]

        # Standard PromptTemplate lookup
        if template_id is None:
            raise ValueError("Template ID is None and no UserPrompt ID found")

        if template_id not in self._template_cache:
            template = PromptTemplate.query.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            self._template_cache[template_id] = template
        return self._template_cache[template_id]

    def _get_model(self, model_id: str) -> Optional[LLMModel]:
        """Get a model from cache or database."""
        if model_id not in self._model_cache:
            self._model_cache[model_id] = LLMModel.get_by_model_id(model_id)
        return self._model_cache[model_id]

    # -------------------------------------------------------------------------
    # Status Updates
    # -------------------------------------------------------------------------

    def _update_job_status(
        self,
        status: GenerationJobStatus,
        error: Optional[str] = None
    ) -> Optional[GenerationJob]:
        """Update the job status."""
        job = GenerationJob.query.get(self.job_id)
        if not job:
            return None

        job.status = status
        if error:
            job.error_message = error
        if status == GenerationJobStatus.COMPLETED:
            job.completed_at = datetime.utcnow()
        if status == GenerationJobStatus.FAILED:
            job.completed_at = datetime.utcnow()

        db.session.commit()
        return job

    def _update_job_progress(
        self,
        completed_delta: int = 0,
        failed_delta: int = 0,
        tokens_delta: int = 0,
        cost_delta: float = 0.0
    ) -> None:
        """Update job progress counters."""
        job = GenerationJob.query.get(self.job_id)
        if not job:
            return

        job.completed_items += completed_delta
        job.failed_items += failed_delta
        job.total_tokens += tokens_delta
        job.total_cost_usd += cost_delta

        db.session.commit()

        # Emit progress event
        self._emit_event("generation:job:progress", {
            "job_id": self.job_id,
            "completed": job.completed_items,
            "failed": job.failed_items,
            "total": job.total_items,
            "percent": job.progress_percent,
            "cost_usd": job.total_cost_usd,
        })

    # -------------------------------------------------------------------------
    # Socket.IO Events
    # -------------------------------------------------------------------------

    def _emit_event(self, event: str, data: Dict[str, Any]) -> None:
        """Emit a Socket.IO event if socketio is available."""
        if self.socketio:
            try:
                logger.info("[GenWorker] Emitting event %s: %s", event, data)
                self.socketio.emit(event, data)
            except Exception as e:
                logger.warning("[GenWorker] Failed to emit event %s: %s", event, e)
        else:
            logger.warning("[GenWorker] No socketio instance available for event %s", event)

    # -------------------------------------------------------------------------
    # Static Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def start_async(job_id: int, *, socketio: Any = None) -> None:
        """
        Start a worker asynchronously in a background thread.

        Args:
            job_id: The job ID to process
            socketio: Optional SocketIO instance
        """
        import threading

        def _run():
            try:
                from main import app
                with app.app_context():
                    worker = GenerationWorker(job_id, socketio=socketio)
                    worker.run()
            except Exception as e:
                logger.exception("[GenWorker] Async job %d failed: %s", job_id, e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        logger.info("[GenWorker] Started async worker for job %d", job_id)
