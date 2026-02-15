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
import re
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

# YJS decoding for UserPrompt content
logger = logging.getLogger(__name__)

# YJS decoding for UserPrompt content
try:
    import y_py as Y
    YJS_AVAILABLE = True
except ImportError:
    YJS_AVAILABLE = False
    logger.warning("y-py not installed, YJS content decoding will not work")


# =============================================================================
# CONSTANTS
# =============================================================================

# Default limits
DEFAULT_MAX_PARALLEL = 5
DEFAULT_MAX_RETRIES = 3
DEFAULT_BATCH_SIZE = 10

# Retry delays (exponential backoff)
RETRY_DELAYS = [1, 5, 15]  # seconds


# =============================================================================
# YJS DECODING HELPERS
# =============================================================================

def decode_yjs_content(content) -> Dict[str, Any]:
    """
    Decode YJS binary content to extract text.

    YJS content is stored as a JSON array of numbers representing
    the Yjs CRDT state update. This function extracts readable text
    from the binary data.

    Since the Python y-py library may have compatibility issues with
    the JavaScript YJS encoding, this function uses a hybrid approach:
    1. First try y-py decoding (if available and compatible)
    2. Fall back to direct text extraction from binary data

    Args:
        content: Either a list of numbers (YJS binary) or a dict (already decoded)

    Returns:
        Dict with 'blocks' structure: {"blocks": {"default": {"title": "default", "content": "...", "position": 0}}}
    """
    if not isinstance(content, list):
        # Already decoded or unknown format
        return content if isinstance(content, dict) else {}

    try:
        # Try y-py decoding first (if available)
        if YJS_AVAILABLE:
            try:
                result = _decode_yjs_with_ypy(content)
                if result and result.get('blocks'):
                    return result
            except Exception as e:
                logger.debug(f"y-py decoding failed, falling back to text extraction: {e}")

        # Fall back to direct text extraction from binary data
        return _extract_text_from_yjs_binary(content)

    except Exception as e:
        logger.error(f"Failed to decode YJS content: {e}")
        return {}


def _decode_yjs_with_ypy(content: list) -> Dict[str, Any]:
    """
    Try to decode YJS content using y-py library.

    Note: y-py loses embedded objects (variable placeholders) when converting
    Y.Text to string. We extract these from the raw binary and restore them.

    Returns empty dict if decoding fails.
    """
    if not YJS_AVAILABLE:
        return {}

    try:
        update_bytes = bytes(content)

        # First, extract embedded variable placeholders from raw binary
        # Y.js stores them as JSON: {"variable":"name"}
        embedded_vars = _extract_embedded_variables(update_bytes)
        logger.debug(f"Found {len(embedded_vars)} embedded variables in YJS binary")

        doc = Y.YDoc()
        with doc.begin_transaction() as txn:
            txn.apply_v1(update_bytes)

        blocks_map = doc.get_map('blocks')
        result_blocks = {}

        for block_id in blocks_map:
            block_value = blocks_map.get(block_id)
            if block_value is None:
                continue

            block_data = {}
            if hasattr(block_value, 'get'):
                block_data['title'] = block_value.get('title') or block_id
                block_data['position'] = block_value.get('position') or 0
                content_ytext = block_value.get('content')
                if content_ytext is not None:
                    text_content = str(content_ytext) if hasattr(content_ytext, '__str__') else ''
                    # Restore embedded variables as {{variable}} placeholders
                    text_content = _restore_variable_placeholders(text_content, embedded_vars)
                    block_data['content'] = text_content
                else:
                    block_data['content'] = ''
            else:
                block_data = {'title': block_id, 'content': str(block_value), 'position': 0}

            result_blocks[block_id] = block_data

        if result_blocks:
            logger.info(f"Decoded YJS content with y-py: {len(result_blocks)} blocks found")
            return {'blocks': result_blocks}

    except Exception as e:
        logger.debug(f"y-py decoding failed: {e}")

    return {}


def _extract_embedded_variables(data: bytes) -> List[str]:
    """
    Extract embedded variable names from YJS binary data.

    Y.js stores embedded objects as JSON: {"variable":"name"}
    These are lost when converting Y.Text to string.

    Returns list of variable names found.
    """
    import re
    variables = []

    # Convert bytes to string, ignoring non-UTF8 bytes
    try:
        text = data.decode('utf-8', errors='ignore')
        # Find all {"variable":"..."} patterns
        pattern = r'\{"variable"\s*:\s*"([^"]+)"\}'
        matches = re.findall(pattern, text)
        variables.extend(matches)
    except Exception:
        pass

    return variables


def _restore_variable_placeholders(text: str, variables: List[str]) -> str:
    """
    Restore variable placeholders in text after YJS decoding.

    When Y.Text is converted to string via str(), embedded objects
    (variable chips like {{subject}}) are dropped, leaving gaps.
    For example: "Subject: {{subject}}\\n" becomes "Subject: \\n"

    This function detects gaps and restores {{variable}} placeholders
    using a two-phase approach:
    1. Label-based matching: "Subject: \\n" -> "Subject: {{subject}}\\n"
    2. Contextual gap detection: consecutive newlines where variables were
    """
    if not variables:
        return text

    result = text
    remaining_vars = list(variables)

    # ---- Phase 1: Label-based matching ----
    # Map labels (case-insensitive) to variable names they likely precede
    LABEL_TO_VARIABLE = {
        # subject
        'subject': 'subject', 'betreff': 'subject', 'topic': 'subject',
        'theme': 'subject', 'thema': 'subject',
        # messages / content (email/conversation style)
        'email thread': 'messages', 'email-thread': 'messages',
        'thread': 'messages', 'conversation': 'messages',
        'messages': 'messages', 'dialog': 'messages', 'dialogue': 'messages',
        'chat': 'messages', 'email': 'messages', 'nachrichten': 'messages',
        'konversation': 'messages', 'verlauf': 'messages',
        'case': 'messages', 'beratungsverlauf': 'messages',
        'counselling thread': 'messages', 'counseling thread': 'messages',
        # content
        'content': 'content', 'text': 'content', 'input': 'content',
        'inhalt': 'content', 'article': 'content', 'full article': 'content',
        'artikel': 'content', 'nachricht': 'content', 'body': 'content',
        'data': 'content',
        # title
        'title': 'title', 'titel': 'title', 'headline': 'title',
        'heading': 'title', 'überschrift': 'title',
    }

    # Find all "Label:" patterns followed by optional horizontal whitespace then newline
    # Use [ \t]* instead of \s* to avoid matching newlines in the label group
    label_pattern = re.compile(r'((?:^|\n)([\w][\w \t-]*?):[ \t]*)\n', re.IGNORECASE)

    for match in label_pattern.finditer(result):
        label_text = match.group(2).strip().lower()
        full_match = match.group(0)

        # Look up which variable this label maps to
        var_name = LABEL_TO_VARIABLE.get(label_text)

        # Direct match: label name == variable name (with space->underscore)
        if not var_name and label_text.replace(' ', '_') in remaining_vars:
            var_name = label_text.replace(' ', '_')
        if not var_name and label_text.replace(' ', '') in remaining_vars:
            var_name = label_text.replace(' ', '')

        if var_name and var_name in remaining_vars:
            placeholder = f"{{{{{var_name}}}}}"
            if placeholder not in result:
                replacement = f"{match.group(1)}{placeholder}\n"
                result = result.replace(full_match, replacement, 1)
                remaining_vars.remove(var_name)

    # ---- Phase 1b: messages/content alias matching ----
    # messages and content are often interchangeable in templates
    for var_name in list(remaining_vars):
        placeholder = f"{{{{{var_name}}}}}"
        if placeholder in result:
            remaining_vars.remove(var_name)
            continue

        if var_name in ('messages', 'content'):
            alt_labels = {
                'messages': ['email thread', 'thread', 'conversation', 'messages',
                             'email', 'chat', 'dialog', 'verlauf', 'case'],
                'content': ['content', 'text', 'input', 'inhalt', 'article',
                            'full article', 'body', 'data'],
            }
            for alt_label in alt_labels.get(var_name, []):
                gap_pat = re.compile(
                    rf'({re.escape(alt_label)}:[ \t]*)\n',
                    re.IGNORECASE
                )
                new_result = gap_pat.sub(rf'\g<1>{placeholder}\n', result, count=1)
                if new_result != result:
                    result = new_result
                    remaining_vars.remove(var_name)
                    break

    # ---- Phase 2: Contextual gap detection ----
    for var_name in list(remaining_vars):
        placeholder = f"{{{{{var_name}}}}}"
        if placeholder in result:
            remaining_vars.remove(var_name)
            continue

        if var_name in ('messages', 'content'):
            # After {{subject}} and before ---
            new_result = re.sub(
                r'(\{\{subject\}\}\s*\n)(\n*)(---)',
                rf'\1{placeholder}\n\n\3',
                result
            )
            if new_result != result:
                result = new_result
                remaining_vars.remove(var_name)
                continue

            # Before --- separator
            if '---' in result:
                new_result = re.sub(
                    r'(\n\n)(\n*)(---)',
                    rf'\1{placeholder}\n\n\3',
                    result, count=1
                )
                if new_result != result:
                    result = new_result
                    remaining_vars.remove(var_name)
                    continue

            # Triple+ newline = likely a gap where variable was dropped
            new_result = re.sub(
                r'(\n)\n\n(\n*)',
                rf'\1\n{placeholder}\n\2',
                result, count=1
            )
            if new_result != result:
                result = new_result
                remaining_vars.remove(var_name)
                continue

    # Log unplaced variables for debugging
    for var_name in remaining_vars:
        placeholder = f"{{{{{var_name}}}}}"
        if placeholder not in result:
            logger.warning(
                "[YJS] Could not restore {{%s}} in decoded text: %s...",
                var_name, result[:100]
            )

    return result


def _extract_text_from_yjs_binary(content: list) -> Dict[str, Any]:
    """
    Extract readable text directly from YJS binary data.

    This is a fallback method that extracts ASCII text sequences
    from the raw binary data. It works because YJS stores text
    content as readable strings within the CRDT structure.

    Returns a single block with all extracted text concatenated.
    """
    try:
        data_bytes = bytes(content)

        # Find readable ASCII sequences (minimum length 8 characters)
        # to filter out short noise sequences
        ascii_sequences = []
        current_seq = []

        for b in data_bytes:
            # Accept printable ASCII and common control chars (newlines, tabs)
            if 32 <= b <= 126 or b in (10, 13, 9):
                char = chr(b) if 32 <= b <= 126 else ('\n' if b in (10, 13) else '\t')
                current_seq.append(char)
            else:
                if len(current_seq) >= 8:  # Minimum sequence length
                    ascii_sequences.append(''.join(current_seq))
                current_seq = []

        # Don't forget the last sequence
        if len(current_seq) >= 8:
            ascii_sequences.append(''.join(current_seq))

        # Filter out known YJS structure strings
        yjs_keywords = {'blocks', 'system', 'title', 'position', 'content', 'default'}
        filtered_sequences = []

        for seq in ascii_sequences:
            # Skip sequences that are just YJS structure keywords
            seq_stripped = seq.strip()
            if seq_stripped.lower() in yjs_keywords:
                continue
            # Skip very short sequences that look like noise
            if len(seq_stripped) < 10:
                continue
            filtered_sequences.append(seq)

        if filtered_sequences:
            # Combine all text sequences
            full_text = '\n'.join(filtered_sequences)
            logger.info(f"Extracted text from YJS binary: {len(full_text)} chars from {len(filtered_sequences)} sequences")
            return {
                'blocks': {
                    'default': {
                        'title': 'default',
                        'content': full_text,
                        'position': 0
                    }
                }
            }

    except Exception as e:
        logger.error(f"Failed to extract text from YJS binary: {e}")

    return {}


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

        # Cache for templates and models (LLM clients are cached centrally in LLMClientFactory)
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
        logger.info("[GenWorker] Starting job %d (socketio=%s)", self.job_id,
                   "present" if self.socketio else "None")

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

            model_color = None
            if output.llm_model and getattr(output.llm_model, "color", None):
                model_color = output.llm_model.color
            else:
                try:
                    from db.models.llm_model import LLMModel
                    model_color = LLMModel.generate_color(output.llm_model_name)
                except Exception:
                    model_color = None

            # Emit started event for real-time UI updates
            self._emit_event("generation:item:started", {
                "job_id": self.job_id,
                "output_id": output.id,
                "model_name": output.llm_model_name,
                "model_color": model_color,
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
                "model_color": model_color,
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
                    "model_color": model_color,
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
        # Get source data (content, subject, messages, etc.)
        source_data = self._get_source_data(output)
        content = source_data.get("content", "")
        subject = source_data.get("subject", "")
        messages = source_data.get("messages", [])

        # Build variables with multiple aliases for common template patterns
        # If no structured messages, use content as messages (for templates using {{messages}})
        messages_value = messages if messages else content
        logger.debug(
            "[GenWorker] Building variables: content_len=%d, messages_len=%d, messages_value_len=%d",
            len(content) if content else 0,
            len(messages) if messages else 0,
            len(messages_value) if isinstance(messages_value, (str, list)) else 0
        )
        variables = {
            # Content aliases
            "content": content,
            "input": content,
            "text_content": content,
            "thread_content": content,
            "email_thread": content,  # Common template variable
            "email_content": content,
            "thread": content,
            # Subject
            "subject": subject,
            "betreff": subject,  # German alias
            # Messages - either structured array or formatted content as fallback
            "messages": messages_value,
        }

        # Add any custom variables from output config (excluding internal keys)
        if output.prompt_variables_json:
            for key, value in output.prompt_variables_json.items():
                if not key.startswith('_'):  # Skip internal keys like _user_prompt_id
                    variables[key] = value

        # Handle UserPrompt (from Prompt Engineering)
        if isinstance(template, UserPrompt):
            logger.debug("[GenWorker] Rendering UserPrompt with variables: %s",
                        {k: (len(v) if isinstance(v, (str, list)) else type(v).__name__)
                         for k, v in variables.items()})
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

        UserPrompt stores content in one of two formats:
        1. JSON with blocks structure (original/seeder format):
           {"blocks": {"system": {"content": "...", "position": 0}}}

        2. YJS binary format (after collaborative editing):
           [2, 16, 151, 147, ...] - array of numbers representing YJS state

        This method handles both formats automatically.
        """
        # Prefer rendered_content (reliable text with {{variables}} from YJS server)
        if user_prompt.rendered_content and isinstance(user_prompt.rendered_content, dict):
            content = user_prompt.rendered_content
            logger.info(f"[GenWorker] Using rendered_content for UserPrompt {user_prompt.prompt_id}")
        else:
            content = user_prompt.content

        # Handle YJS binary format (list of numbers) - fallback for prompts without rendered_content
        if isinstance(content, list):
            logger.info(f"Decoding YJS binary content for UserPrompt {user_prompt.prompt_id}")
            content = decode_yjs_content(content)
            if not content:
                logger.warning(f"Failed to decode YJS content for UserPrompt {user_prompt.prompt_id}")
                return "", ""
            logger.info(f"[GenWorker] Decoded YJS content: {list(content.keys()) if isinstance(content, dict) else type(content)}")

        if not isinstance(content, dict):
            return "", str(content) if content else ""

        blocks = content.get('blocks', {})
        if not blocks:
            logger.warning("[GenWorker] No blocks found in decoded content")
            return "", ""

        # Log block details
        for block_id, block_data in blocks.items():
            if isinstance(block_data, dict):
                block_content = block_data.get('content', '')
                logger.info(f"[GenWorker] Block '{block_id}': content_len={len(block_content) if block_content else 0}, has_messages={{'{{messages}}' in block_content if block_content else False}}")

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
            formatted = self._format_variable_value(value)
            logger.info("[GenWorker] Substituting {{%s}}: value_type=%s, result_len=%d",
                        var_name, type(value).__name__, len(formatted) if formatted else 0)
            return formatted

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

    def _get_source_data(self, output: GeneratedOutput) -> Dict[str, Any]:
        """
        Get the source data for an output including content, subject, and messages.

        Sources (in priority order):
        1. Input variable stored in prompt_variables_json (manual data)
        2. Source EvaluationItem content
        3. Custom text from job config

        Returns:
            Dict with 'content', 'subject', and 'messages' keys
        """
        result = {"content": "", "subject": "", "messages": []}

        # Debug: Log what we receive
        logger.debug(
            "[GenWorker] _get_source_data for output %s: prompt_variables_json=%s, source_item_id=%s",
            output.id, type(output.prompt_variables_json), output.source_item_id
        )

        # Check for input in variables (from manual data upload)
        if output.prompt_variables_json:
            logger.debug("[GenWorker] prompt_variables_json keys: %s", list(output.prompt_variables_json.keys()))
            input_text = output.prompt_variables_json.get('input')
            if input_text:
                logger.info("[GenWorker] Found input in prompt_variables_json, length=%d", len(input_text))
                result["content"] = input_text

            # Also extract subject and messages if present (from manual items)
            if output.prompt_variables_json.get('subject'):
                result["subject"] = output.prompt_variables_json['subject']
                logger.debug("[GenWorker] Found subject in prompt_variables_json: %s", result["subject"])
            if output.prompt_variables_json.get('messages'):
                result["messages"] = output.prompt_variables_json['messages']
                logger.debug("[GenWorker] Found %d messages in prompt_variables_json", len(result["messages"]))

            # If we have input content, return now
            if input_text:
                return result

        if output.source_item_id:
            # Get content from EvaluationItem
            item = EvaluationItem.query.get(output.source_item_id)
            if item:
                result["subject"] = item.subject or ""

                # Get messages for this item
                messages = Message.query.filter_by(item_id=item.item_id).order_by(
                    Message.timestamp.asc()
                ).all()

                if messages:
                    # Store structured messages for advanced templates
                    result["messages"] = [
                        {"role": msg.sender, "content": msg.content}
                        for msg in messages
                    ]
                    # Format content as readable thread
                    result["content"] = "\n".join(
                        f"{msg.sender}: {msg.content}" for msg in messages
                    )
                else:
                    # Fallback to subject if no messages
                    result["content"] = item.subject or ""

                return result

        # Check for custom text in job config
        job = GenerationJob.query.get(output.job_id)
        if job and job.config_json:
            sources = job.config_json.get("sources", {})
            if sources.get("type") == "custom":
                texts = sources.get("custom_texts", [])
                # Find the index of this output among custom text outputs
                # (simplified: just use the first text for now)
                if texts:
                    result["content"] = texts[0]

        return result

    def _get_source_content(self, output: GeneratedOutput) -> str:
        """
        Get the source content for an output.

        Convenience wrapper around _get_source_data that returns just the content.

        Returns:
            Source content string
        """
        return self._get_source_data(output).get("content", "")

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
        # Get client (cached centrally in LLMClientFactory)
        client, api_model_id = LLMClientFactory.resolve_client_and_model_id(model_id)

        # Get generation params from job config (cached)
        if not hasattr(self, '_gen_params_cache'):
            job = GenerationJob.query.get(self.job_id)
            config = job.config_json if job else {}
            self._gen_params_cache = config.get("generation_params", {})
        gen_params = self._gen_params_cache

        # Detect OpenAI models (require max_completion_tokens instead of max_tokens)
        is_openai = ('openai' in (model_id or '').lower()
                     or api_model_id.lower().startswith('gpt-')
                     or api_model_id.lower().startswith('o'))

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Check if streaming is enabled (default: True for real-time updates)
        enable_streaming = self.socketio is not None and output_id is not None
        logger.info("[GenWorker] Streaming check: socketio=%s, output_id=%s, enabled=%s",
                   "present" if self.socketio else "None", output_id, enable_streaming)

        if enable_streaming:
            # Streaming call
            content = ""
            tokens = {"input": 0, "output": 0, "total": 0}
            last_save_time = time.time()
            SAVE_INTERVAL = 2.0  # Save partial content every 2 seconds for reconnection support

            try:
                # Build API call params - only include max_tokens if explicitly set
                stream_params = {
                    "model": api_model_id,
                    "messages": messages,
                    "temperature": gen_params.get("temperature", 0.7),
                    "top_p": gen_params.get("top_p", 1.0),
                    "stream": True,
                }
                # Only add max_tokens if explicitly specified (allows unlimited for reasoning models)
                if gen_params.get("max_tokens"):
                    key = "max_completion_tokens" if is_openai else "max_tokens"
                    stream_params[key] = gen_params["max_tokens"]

                stream = self._api_call_with_param_fix(client, stream_params)

                # Collect streamed content and emit tokens
                used_reasoning_field = False  # Track if we're using reasoning_content
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        # Check content first, then reasoning_content for reasoning models (Magistral)
                        token = None
                        if hasattr(delta, "content") and delta.content:
                            token = delta.content
                        elif hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            token = delta.reasoning_content
                            if not used_reasoning_field:
                                logger.info("[GenWorker] Using reasoning_content field (reasoning model detected)")
                                used_reasoning_field = True
                        elif hasattr(delta, "reasoning") and delta.reasoning:
                            token = delta.reasoning
                            if not used_reasoning_field:
                                logger.info("[GenWorker] Using reasoning field (reasoning model detected)")
                                used_reasoning_field = True

                        if token:
                            content += token
                            # Emit token for real-time streaming
                            self._emit_event("generation:item:token", {
                                "job_id": self.job_id,
                                "output_id": output_id,
                                "token": token,
                            })

                            # Periodically save partial content for reconnection support
                            current_time = time.time()
                            if current_time - last_save_time >= SAVE_INTERVAL:
                                self._save_partial_content(output_id, content)
                                last_save_time = current_time

                # Estimate tokens for streaming (actual count not always available)
                # Use rough estimation: ~4 chars per token
                tokens["output"] = max(1, len(content) // 4)
                tokens["input"] = max(1, (len(system_prompt) + len(user_prompt)) // 4)
                tokens["total"] = tokens["input"] + tokens["output"]

                # Some models (e.g. GPT-5-nano) return 200 OK for streaming but
                # send no content tokens. Fall back to non-streaming in that case.
                if not content.strip():
                    logger.warning("[GenWorker] Streaming returned empty content, falling back to non-streaming")
                    enable_streaming = False

            except Exception as e:
                logger.warning("[GenWorker] Streaming failed, falling back to non-streaming: %s", e)
                # Fall back to non-streaming on error
                enable_streaming = False

        if not enable_streaming:
            # Non-streaming call - build params without max_tokens if not specified
            call_params = {
                "model": api_model_id,
                "messages": messages,
                "temperature": gen_params.get("temperature", 0.7),
                "top_p": gen_params.get("top_p", 1.0),
            }
            # Only add max_tokens if explicitly specified (allows unlimited for reasoning models)
            if gen_params.get("max_tokens"):
                key = "max_completion_tokens" if is_openai else "max_tokens"
                call_params[key] = gen_params["max_tokens"]

            response = self._api_call_with_param_fix(client, call_params)

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

    @staticmethod
    def _api_call_with_param_fix(client, params: dict):
        """
        Call the chat completions API, automatically fixing unsupported params.

        Some models (e.g. OpenAI gpt-5-nano) reject custom temperature or
        require max_completion_tokens instead of max_tokens. This method
        catches 400 errors and retries with fixed parameters (up to 3 times).
        """
        max_fixes = 3
        for _ in range(max_fixes):
            try:
                return client.chat.completions.create(**params)
            except Exception as e:
                err_msg = str(e).lower()
                fixed = False
                if "temperature" in err_msg and "temperature" in params:
                    logger.info("[GenWorker] Model doesn't support custom temperature, removing")
                    params.pop("temperature")
                    fixed = True
                elif "max_tokens" in err_msg and "max_completion_tokens" in err_msg:
                    logger.info("[GenWorker] Model requires max_completion_tokens instead of max_tokens")
                    val = params.pop("max_tokens", None)
                    if val:
                        params["max_completion_tokens"] = val
                    fixed = True
                elif "top_p" in err_msg and "top_p" in params:
                    logger.info("[GenWorker] Model doesn't support custom top_p, removing")
                    params.pop("top_p")
                    fixed = True
                if not fixed:
                    raise
        return client.chat.completions.create(**params)

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
    # Partial Content Storage (for reconnection support)
    # -------------------------------------------------------------------------

    def _save_partial_content(self, output_id: int, content: str) -> None:
        """
        Save partial streaming content to the database for reconnection support.

        This allows clients who reconnect mid-stream to see what has been
        generated so far.
        """
        try:
            output = GeneratedOutput.query.get(output_id)
            if output and output.status == GeneratedOutputStatus.PROCESSING:
                output.generated_content = content
                db.session.commit()
                logger.debug("[GenWorker] Saved partial content for output %d (%d chars)",
                           output_id, len(content))
        except Exception as e:
            logger.warning("[GenWorker] Failed to save partial content for output %d: %s",
                         output_id, e)
            # Don't fail the streaming, just log the warning
            db.session.rollback()

    # -------------------------------------------------------------------------
    # Socket.IO Events
    # -------------------------------------------------------------------------

    def _emit_event(self, event: str, data: Dict[str, Any]) -> None:
        """Emit a Socket.IO event if socketio is available."""
        if self.socketio:
            try:
                # Emit to all connected clients on default namespace
                # namespace='/' ensures broadcast to default namespace
                self.socketio.emit(event, data, namespace='/')
                # Log token events at debug level to avoid spam, others at info
                if 'token' in event:
                    logger.debug("[GenWorker] Emitted %s", event)
                else:
                    logger.info("[GenWorker] Emitted event %s: %s", event, data)
            except Exception as e:
                logger.warning("[GenWorker] Failed to emit event %s: %s", event, e)
        else:
            logger.warning("[GenWorker] No socketio instance - event %s not sent", event)

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
