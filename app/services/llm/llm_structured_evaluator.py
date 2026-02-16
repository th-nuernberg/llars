"""
LLM Structured Evaluator.

Enhanced LLM evaluator with:
- Pydantic schema validation for structured output
- Prompt template support
- Token usage tracking
- Socket.IO event broadcasting
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, ValidationError

from db import db
from db.models import (
    EmailThread,
    Feature,
    LLMTaskResult,
    Message,
    PromptTemplate,
    RatingScenarios,
    ScenarioThreads,
)
from llm.openai_utils import extract_message_text
from schemas.evaluation_schemas import (
    AuthenticityEvaluationResult,
    BaseEvaluationResult,
    ClassificationEvaluationResult,
    ComparisonEvaluationResult,
    MailRatingEvaluationResult,
    RankingEvaluationResult,
    RatingEvaluationResult,
    get_schema_for_task_type,
)
from services.evaluation import PromptTemplateService, TokenTrackingService, BudgetExceededError
from services.llm.llm_client_factory import LLMClientFactory
from services.llm.llm_execution_service import LLMExecutionService

logger = logging.getLogger(__name__)


class LLMStructuredEvaluator:
    """
    Enhanced LLM evaluator with structured output support.

    Features:
    - Uses Pydantic schemas for response validation
    - Supports customizable prompt templates
    - Tracks token usage and costs
    - Emits Socket.IO events for live monitoring
    """

    MAX_RETRIES = 3

    def __init__(
        self,
        *,
        user_id: int,
        socketio: Optional[Any] = None,
        use_structured_output: bool = True,
    ):
        """
        Initialize the evaluator.

        Args:
            user_id: User ID for budget tracking
            socketio: Optional SocketIO instance for live updates
            use_structured_output: Whether to use Pydantic schema validation
        """
        self.user_id = user_id
        self.socketio = socketio
        self.use_structured_output = use_structured_output

    def run_evaluation(
        self,
        *,
        scenario_id: int,
        model_ids: Optional[List[str]] = None,
        thread_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Run evaluations for a scenario.

        Args:
            scenario_id: Scenario ID to evaluate
            model_ids: Optional list of model IDs to use
            thread_ids: Optional list of thread IDs to evaluate

        Returns:
            Dict with evaluation summary
        """
        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            logger.warning("[Structured Eval] Scenario not found: %s", scenario_id)
            return {"error": "Scenario not found"}

        # Get task type
        from db.models import FeatureFunctionType
        function_type = FeatureFunctionType.query.filter_by(
            function_type_id=scenario.function_type_id
        ).first()
        task_type = function_type.name if function_type else None

        if not task_type:
            return {"error": "Unknown task type"}

        # Resolve models and threads
        resolved_models = self._resolve_model_ids(scenario, model_ids)
        if not resolved_models:
            return {"error": "No models to evaluate"}

        resolved_threads = self._resolve_thread_ids(scenario, thread_ids)
        if not resolved_threads:
            return {"error": "No threads to evaluate"}

        # Get prompt template
        config = scenario.config_json if isinstance(scenario.config_json, dict) else {}
        template_id = config.get("prompt_template_id")
        template = PromptTemplateService.get_template_for_task(task_type, template_id)

        # Run evaluations
        results = {
            "scenario_id": scenario_id,
            "task_type": task_type,
            "models": {},
            "total_completed": 0,
            "total_errors": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
        }

        for model_id in resolved_models:
            model_results = self._run_model_evaluations(
                model_id=model_id,
                task_type=task_type,
                thread_ids=resolved_threads,
                scenario_id=scenario_id,
                scenario=scenario,
                template=template,
            )
            results["models"][model_id] = model_results
            results["total_completed"] += model_results["completed"]
            results["total_errors"] += model_results["errors"]
            results["total_tokens"] += model_results["tokens_used"]
            results["total_cost_usd"] += model_results["cost_usd"]

        # Broadcast completion
        if self.socketio:
            from socketio_handlers.events_llm_evaluation import broadcast_scenario_completed
            broadcast_scenario_completed(self.socketio, scenario_id, results)

        return results

    def _run_model_evaluations(
        self,
        *,
        model_id: str,
        task_type: str,
        thread_ids: List[int],
        scenario_id: int,
        scenario: RatingScenarios,
        template: Optional[PromptTemplate],
    ) -> Dict[str, Any]:
        """Run evaluations for a single model across all threads."""
        client, api_model_id = LLMClientFactory.resolve_client_and_model_id(model_id)
        schema_class = get_schema_for_task_type(task_type)

        results = {
            "model_id": model_id,
            "completed": 0,
            "errors": 0,
            "tokens_used": 0,
            "cost_usd": 0.0,
            "thread_results": {},
        }

        for thread_id in thread_ids:
            # Skip if already evaluated
            existing = LLMTaskResult.query.filter_by(
                scenario_id=scenario_id,
                thread_id=thread_id,
                model_id=model_id,
                task_type=task_type,
            ).first()
            if existing and existing.payload_json and not existing.error:
                results["completed"] += 1
                continue

            # Broadcast start
            if self.socketio:
                from socketio_handlers.events_llm_evaluation import broadcast_evaluation_started
                broadcast_evaluation_started(self.socketio, scenario_id, model_id, thread_id)

            try:
                # Check budget
                try:
                    TokenTrackingService.check_budget(self.user_id, estimated_tokens=2000)
                except BudgetExceededError as e:
                    logger.warning("[Structured Eval] Budget exceeded for user %s", self.user_id)
                    results["errors"] += 1
                    results["thread_results"][thread_id] = {"error": str(e)}
                    continue

                # Build prompts
                system_prompt, user_prompt = self._build_prompts(
                    task_type=task_type,
                    thread_id=thread_id,
                    scenario=scenario,
                    template=template,
                )

                # Execute evaluation
                start_time = time.time()
                result, raw_response, tokens = self._execute_with_retry(
                    client=client,
                    model_id=model_id,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema_class=schema_class,
                    task_type=task_type,
                    thread_id=thread_id,
                )
                processing_time_ms = int((time.time() - start_time) * 1000)

                # Store result
                self._store_result(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type=task_type,
                    result=result,
                    raw_response=raw_response,
                    tokens=tokens,
                    processing_time_ms=processing_time_ms,
                    template=template,
                )

                # Track usage
                cost_usd = TokenTrackingService.track_usage(
                    user_id=self.user_id,
                    model_id=model_id,
                    task_type=task_type,
                    input_tokens=tokens.get("input", 0),
                    output_tokens=tokens.get("output", 0),
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    processing_time_ms=processing_time_ms,
                    success=True,
                    prompt_template_id=template.id if template else None,
                ).estimated_cost_usd

                results["completed"] += 1
                results["tokens_used"] += tokens.get("total", 0)
                results["cost_usd"] += cost_usd
                results["thread_results"][thread_id] = {"success": True}

                # Broadcast completion
                if self.socketio:
                    from socketio_handlers.events_llm_evaluation import broadcast_evaluation_completed
                    broadcast_evaluation_completed(
                        self.socketio,
                        scenario_id=scenario_id,
                        model_id=model_id,
                        thread_id=thread_id,
                        task_type=task_type,
                        result=result.model_dump() if isinstance(result, BaseModel) else result,
                        tokens_used=tokens.get("total", 0),
                        cost_usd=cost_usd,
                        processing_time_ms=processing_time_ms,
                    )

            except Exception as e:
                logger.exception("[Structured Eval] Evaluation failed for thread %s", thread_id)
                results["errors"] += 1
                results["thread_results"][thread_id] = {"error": str(e)}

                # Track failed usage
                TokenTrackingService.track_usage(
                    user_id=self.user_id,
                    model_id=model_id,
                    task_type=task_type,
                    input_tokens=0,
                    output_tokens=0,
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    success=False,
                    error_message=str(e),
                )

                # Store error
                self._store_error(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type=task_type,
                    error=str(e),
                )

                # Broadcast failure
                if self.socketio:
                    from socketio_handlers.events_llm_evaluation import broadcast_evaluation_failed
                    broadcast_evaluation_failed(
                        self.socketio,
                        scenario_id=scenario_id,
                        model_id=model_id,
                        thread_id=thread_id,
                        task_type=task_type,
                        error=str(e),
                    )

        return results

    def _build_prompts(
        self,
        *,
        task_type: str,
        thread_id: int,
        scenario: RatingScenarios,
        template: Optional[PromptTemplate],
    ) -> tuple[str, str]:
        """Build system and user prompts for evaluation."""
        # Get thread data
        thread = EmailThread.query.filter_by(thread_id=thread_id).first()
        messages = Message.query.filter_by(thread_id=thread_id).order_by(Message.timestamp.asc()).all()
        features = Feature.query.filter_by(thread_id=thread_id).all()

        # Format thread content
        thread_content = "\n".join(f"{msg.sender}: {msg.content}" for msg in messages)

        # Format features
        seed = int(
            hashlib.sha256(
                f"{scenario.id}:{thread_id}".encode("utf-8")
            ).hexdigest()[:8],
            16,
        )
        rng = random.Random(seed)
        shuffled_features = list(features)
        rng.shuffle(shuffled_features)

        feature_lines = []
        for f in shuffled_features:
            feature_lines.append(
                f"- ID {f.feature_id} (Typ: {f.feature_type.name}, Modell: {f.llm.name}): {f.content}"
            )
        features_text = "\n".join(feature_lines)

        # Use template or fallback to defaults
        if template:
            system_prompt = template.system_prompt
            user_prompt = PromptTemplateService.render_prompt(
                template,
                features=features_text,
                thread_content=thread_content,
                subject=thread.subject if thread else "Kein Betreff",
                text_a=messages[0].content if messages else "",
                text_b=messages[1].content if len(messages) > 1 else "",
                labels=self._get_classification_labels(scenario),
                label_descriptions=self._get_label_descriptions(scenario),
                text_content=thread_content,
            )
        else:
            # Fallback to inline prompts from DEFAULT_PROMPTS
            from services.evaluation.prompt_template_service import DEFAULT_PROMPTS
            defaults = DEFAULT_PROMPTS.get(task_type, {})
            system_prompt = defaults.get("system_prompt", "")
            user_prompt = defaults.get("user_prompt_template", "").format(
                features=features_text,
                thread_content=thread_content,
                subject=thread.subject if thread else "Kein Betreff",
                text_a=messages[0].content if messages else "",
                text_b=messages[1].content if len(messages) > 1 else "",
                labels=self._get_classification_labels(scenario),
                label_descriptions=self._get_label_descriptions(scenario),
                text_content=thread_content,
            )

        return system_prompt, user_prompt

    def _get_classification_labels(self, scenario: RatingScenarios) -> str:
        """Get classification labels from scenario config."""
        config = scenario.config_json if isinstance(scenario.config_json, dict) else {}
        labels = config.get("classification_labels", ["positive", "negative", "neutral"])
        return ", ".join(f'"{l}"' for l in labels)

    def _get_label_descriptions(self, scenario: RatingScenarios) -> str:
        """Get label descriptions from scenario config."""
        config = scenario.config_json if isinstance(scenario.config_json, dict) else {}
        descriptions = config.get("label_descriptions", {})
        if descriptions:
            return "\n".join(f"- {k}: {v}" for k, v in descriptions.items())
        return ""

    def _execute_with_retry(
        self,
        *,
        client,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        schema_class: Type[BaseEvaluationResult],
        task_type: str,
        thread_id: int,
    ) -> tuple[BaseEvaluationResult, str, Dict[str, int]]:
        """Execute LLM call with retries and schema validation."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        last_error = None
        raw_response = ""
        total_tokens = {"input": 0, "output": 0, "total": 0}

        for attempt in range(self.MAX_RETRIES):
            if last_error:
                messages.append({
                    "role": "user",
                    "content": f"Deine vorherige Antwort war ungültig: {last_error}. "
                               "Bitte antworte NUR mit validem JSON gemäß dem Schema."
                })

            try:
                response = LLMExecutionService.execute_chat_completion(
                    client,
                    model=model_id,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=2000,
                    extra_body={"response_format": {"type": "json_object"}},
                    model_key=model_id,
                )

                # Extract content and token counts
                content = extract_message_text(response.choices[0].message) if response.choices else ""
                raw_response = content

                # Track tokens
                if hasattr(response, "usage") and response.usage:
                    total_tokens["input"] += getattr(response.usage, "prompt_tokens", 0)
                    total_tokens["output"] += getattr(response.usage, "completion_tokens", 0)
                    total_tokens["total"] = total_tokens["input"] + total_tokens["output"]

                # Parse JSON
                parsed = self._parse_json(content)

                # Validate with Pydantic schema if enabled
                if self.use_structured_output:
                    result = schema_class.model_validate(parsed)
                    return result, raw_response, total_tokens
                else:
                    return parsed, raw_response, total_tokens

            except ValidationError as e:
                last_error = f"Schema validation failed: {e.errors()[:3]}"
                logger.warning(
                    "[Structured Eval] Validation error for thread %s (attempt %d): %s",
                    thread_id, attempt + 1, last_error
                )
            except json.JSONDecodeError as e:
                last_error = f"Invalid JSON: {str(e)}"
                logger.warning(
                    "[Structured Eval] JSON parse error for thread %s (attempt %d): %s",
                    thread_id, attempt + 1, last_error
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "[Structured Eval] Error for thread %s (attempt %d): %s",
                    thread_id, attempt + 1, last_error
                )

        raise ValueError(f"Failed after {self.MAX_RETRIES} attempts: {last_error}")

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from response text."""
        raw = (text or "").strip()
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)

    def _store_result(
        self,
        *,
        scenario_id: int,
        thread_id: int,
        model_id: str,
        task_type: str,
        result: Any,
        raw_response: str,
        tokens: Dict[str, int],
        processing_time_ms: int,
        template: Optional[PromptTemplate],
    ) -> None:
        """Store evaluation result in database."""
        # Convert Pydantic model to dict
        if isinstance(result, BaseModel):
            payload = result.model_dump()
            # Extract reasoning separately
            reasoning = {
                "reasoning": result.reasoning,
                "confidence": result.confidence,
            }
            # Add task-specific reasoning
            if hasattr(result, "chain_of_thought"):
                reasoning["chain_of_thought"] = result.chain_of_thought.model_dump()
            if hasattr(result, "indicators"):
                reasoning["indicators"] = [i.model_dump() for i in result.indicators]
            if hasattr(result, "criteria"):
                reasoning["criteria"] = [c.model_dump() for c in result.criteria]
        else:
            payload = result
            reasoning = {"reasoning": result.get("reasoning", "")}

        existing = LLMTaskResult.query.filter_by(
            scenario_id=scenario_id,
            thread_id=thread_id,
            model_id=model_id,
            task_type=task_type,
        ).first()

        if existing:
            existing.payload_json = payload
            existing.raw_response = raw_response
            existing.reasoning_json = reasoning
            existing.input_tokens = tokens.get("input", 0)
            existing.output_tokens = tokens.get("output", 0)
            existing.processing_time_ms = processing_time_ms
            existing.prompt_template_id = template.id if template else None
            existing.prompt_version = template.version if template else None
            existing.error = None
            db.session.add(existing)
        else:
            db.session.add(LLMTaskResult(
                scenario_id=scenario_id,
                thread_id=thread_id,
                model_id=model_id,
                task_type=task_type,
                payload_json=payload,
                raw_response=raw_response,
                reasoning_json=reasoning,
                input_tokens=tokens.get("input", 0),
                output_tokens=tokens.get("output", 0),
                processing_time_ms=processing_time_ms,
                prompt_template_id=template.id if template else None,
                prompt_version=template.version if template else None,
                error=None,
            ))

        db.session.commit()

    def _store_error(
        self,
        *,
        scenario_id: int,
        thread_id: int,
        model_id: str,
        task_type: str,
        error: str,
    ) -> None:
        """Store evaluation error in database."""
        existing = LLMTaskResult.query.filter_by(
            scenario_id=scenario_id,
            thread_id=thread_id,
            model_id=model_id,
            task_type=task_type,
        ).first()

        if existing:
            existing.error = error
            db.session.add(existing)
        else:
            db.session.add(LLMTaskResult(
                scenario_id=scenario_id,
                thread_id=thread_id,
                model_id=model_id,
                task_type=task_type,
                payload_json=None,
                raw_response=None,
                error=error,
            ))

        db.session.commit()

    def _resolve_model_ids(
        self,
        scenario: RatingScenarios,
        model_ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Resolve model IDs from scenario config or provided list."""
        if model_ids:
            return [m.strip() for m in model_ids if isinstance(m, str) and m.strip()]

        config = scenario.config_json if isinstance(scenario.config_json, dict) else {}
        selected = config.get("llm_evaluators", [])
        return [m.strip() for m in selected if isinstance(m, str) and m.strip()]

    def _resolve_thread_ids(
        self,
        scenario: RatingScenarios,
        thread_ids: Optional[List[int]] = None,
    ) -> List[int]:
        """Resolve thread IDs from scenario or provided list."""
        available = [
            t.thread_id for t in ScenarioThreads.query.filter_by(scenario_id=scenario.id).all()
        ]
        if thread_ids:
            return [tid for tid in thread_ids if tid in available]
        return available


# Async wrapper for background execution
def run_structured_evaluation_async(
    scenario_id: int,
    user_id: int,
    *,
    model_ids: Optional[List[str]] = None,
    thread_ids: Optional[List[int]] = None,
    use_structured_output: bool = True,
) -> None:
    """
    Run structured evaluation in background thread.

    Args:
        scenario_id: Scenario ID to evaluate
        user_id: User ID for budget tracking
        model_ids: Optional model IDs
        thread_ids: Optional thread IDs
        use_structured_output: Whether to use Pydantic validation
    """
    import threading

    def _runner():
        try:
            from main import app
            with app.app_context():
                # Get socketio instance
                from main import socketio

                evaluator = LLMStructuredEvaluator(
                    user_id=user_id,
                    socketio=socketio,
                    use_structured_output=use_structured_output,
                )
                evaluator.run_evaluation(
                    scenario_id=scenario_id,
                    model_ids=model_ids,
                    thread_ids=thread_ids,
                )
        except Exception as e:
            logger.exception("[Structured Eval] Async evaluation failed: %s", e)

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
