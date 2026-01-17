"""
LLM AI Task Runner

Executes scenario tasks (ranking, rating, authenticity) for LLM evaluators.
Broadcasts progress updates via WebSocket for real-time UI feedback.
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
import threading
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

from db.database import db
from db.models import (
    EmailThread,
    Feature,
    FeatureFunctionType,
    LLMTaskResult,
    Message,
    RatingScenarios,
    ScenarioThreads,
)
from llm.openai_utils import extract_message_text
from services.llm.llm_client_factory import LLMClientFactory
from services.system_settings_service import get_setting

logger = logging.getLogger(__name__)


def _get_socketio():
    """
    Get the Flask-SocketIO instance for broadcasting progress.

    Tries multiple import paths to handle different execution contexts.

    Returns:
        SocketIO instance if found, None otherwise
    """
    try:
        # Try direct import from main
        try:
            from main import socketio
            return socketio
        except ImportError:
            pass

        # Try import from app.main
        try:
            from app.main import socketio
            return socketio
        except ImportError:
            pass

        # Try Flask extensions
        from flask import current_app
        if hasattr(current_app, 'extensions') and 'socketio' in current_app.extensions:
            return current_app.extensions['socketio']

        return None
    except Exception:
        return None


def _broadcast_task_completed(
    scenario_id: int,
    model_id: str,
    thread_id: int,
    task_type: str,
    result: dict,
    processing_time_ms: int = 0,
):
    """Broadcast that a task completed successfully."""
    socketio = _get_socketio()
    if not socketio:
        return

    try:
        from socketio_handlers.events_llm_evaluation import broadcast_evaluation_completed
        broadcast_evaluation_completed(
            socketio,
            scenario_id=scenario_id,
            model_id=model_id,
            thread_id=thread_id,
            task_type=task_type,
            result=result,
            processing_time_ms=processing_time_ms,
        )
    except Exception as e:
        logger.debug(f"[LLM AI Runner] Failed to broadcast completion: {e}")


def _broadcast_task_failed(
    scenario_id: int,
    model_id: str,
    thread_id: int,
    task_type: str,
    error: str,
):
    """Broadcast that a task failed."""
    socketio = _get_socketio()
    if not socketio:
        return

    try:
        from socketio_handlers.events_llm_evaluation import broadcast_evaluation_failed
        broadcast_evaluation_failed(
            socketio,
            scenario_id=scenario_id,
            model_id=model_id,
            thread_id=thread_id,
            task_type=task_type,
            error=error,
        )
    except Exception as e:
        logger.debug(f"[LLM AI Runner] Failed to broadcast failure: {e}")


def _broadcast_scenario_completed(scenario_id: int, summary: dict):
    """Broadcast that all evaluations for a scenario are complete."""
    socketio = _get_socketio()
    if not socketio:
        return

    try:
        from socketio_handlers.events_llm_evaluation import broadcast_scenario_completed
        broadcast_scenario_completed(socketio, scenario_id=scenario_id, summary=summary)
    except Exception as e:
        logger.debug(f"[LLM AI Runner] Failed to broadcast scenario completion: {e}")

def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_log_settings() -> Dict[str, Any]:
    tasks_raw = get_setting("llm_ai_log_tasks", "") or ""
    tasks = {
        t.strip().lower()
        for t in str(tasks_raw).split(",")
        if t.strip()
    }
    return {
        "log_prompts": bool(get_setting("llm_ai_log_prompts", False)),
        "log_responses": bool(get_setting("llm_ai_log_responses", True)),
        "log_response_max": max(0, _safe_int(get_setting("llm_ai_log_response_max", 800), 800)),
        "log_prompt_max": max(0, _safe_int(get_setting("llm_ai_log_prompt_max", 800), 800)),
        "log_tasks": tasks,
    }


def _format_trace(trace: Optional[Dict[str, Any]]) -> str:
    if not trace:
        return ""
    parts = []
    for key in ("task", "scenario_id", "thread_id", "model_id"):
        value = trace.get(key)
        if value is not None and value != "":
            parts.append(f"{key}={value}")
    return " ".join(parts)


def _truncate(text: str, limit: int) -> str:
    if text is None:
        return ""
    raw = str(text)
    if limit <= 0 or len(raw) <= limit:
        return raw
    return f"{raw[:limit]}...<truncated>"


def _should_log(
    trace: Optional[Dict[str, Any]],
    *,
    log_prompts: bool,
    log_responses: bool,
    log_tasks: Iterable[str],
) -> bool:
    if not (log_prompts or log_responses):
        return False
    if log_tasks:
        task = (trace or {}).get("task")
        return task in log_tasks
    return True


class LLMResponseError(Exception):
    def __init__(self, message: str, raw_response: Optional[str] = None):
        super().__init__(message)
        self.raw_response = raw_response


class LLMAITaskRunner:
    """Run scenario tasks for configured LLM evaluators."""

    MAX_RETRIES = 2

    @staticmethod
    def run_for_scenario_async(
        scenario_id: int,
        *,
        model_ids: Optional[List[str]] = None,
        thread_ids: Optional[List[int]] = None,
    ) -> None:
        def _runner():
            try:
                from main import app
                with app.app_context():
                    LLMAITaskRunner.run_for_scenario(
                        scenario_id,
                        model_ids=model_ids,
                        thread_ids=thread_ids,
                    )
            except Exception as exc:
                logger.warning(f"[LLM AI Runner] Async run failed: {exc}")

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()

    @staticmethod
    def run_for_scenario(
        scenario_id: int,
        *,
        model_ids: Optional[List[str]] = None,
        thread_ids: Optional[List[int]] = None,
    ) -> None:
        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            logger.warning("[LLM AI Runner] Scenario not found: %s", scenario_id)
            return

        function_type = FeatureFunctionType.query.filter_by(
            function_type_id=scenario.function_type_id
        ).first()
        function_name = function_type.name if function_type else None

        resolved_models = LLMAITaskRunner._resolve_model_ids(scenario, model_ids)
        if not resolved_models:
            return

        scenario_thread_ids = LLMAITaskRunner._resolve_thread_ids(scenario, thread_ids)
        if not scenario_thread_ids:
            return

        for model_id in resolved_models:
            if function_name == "ranking":
                LLMAITaskRunner._run_ranking(model_id, scenario_thread_ids, scenario.id)
            elif function_name == "rating":
                LLMAITaskRunner._run_rating(model_id, scenario_thread_ids, scenario.id)
            elif function_name == "authenticity":
                LLMAITaskRunner._run_authenticity(model_id, scenario_thread_ids, scenario.id)
            elif function_name == "mail_rating":
                LLMAITaskRunner._run_mail_rating(model_id, scenario_thread_ids, scenario.id)
            elif function_name == "text_classification":
                LLMAITaskRunner._run_text_classification(model_id, scenario_thread_ids, scenario.id, scenario)
            elif function_name == "comparison":
                LLMAITaskRunner._run_comparison(model_id, scenario_thread_ids, scenario.id)
            else:
                logger.info(
                    "[LLM AI Runner] Task type '%s' not supported for model %s",
                    function_name,
                    model_id,
                )

    @staticmethod
    def _resolve_model_ids(
        scenario: RatingScenarios,
        model_ids: Optional[List[str]] = None,
    ) -> List[str]:
        selected = model_ids
        if selected is None:
            config = scenario.config_json
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except (json.JSONDecodeError, TypeError):
                    config = {}
            if not isinstance(config, dict):
                config = {}
            selected = config.get("llm_evaluators") or config.get("selected_llms") or []
        if not isinstance(selected, list):
            return []
        cleaned = []
        for model_id in selected:
            if isinstance(model_id, str):
                mid = model_id.strip()
            elif isinstance(model_id, dict):
                mid = str(model_id.get("model_id") or "").strip()
            else:
                continue
            if mid and mid not in cleaned:
                cleaned.append(mid)
        return cleaned

    @staticmethod
    def _resolve_thread_ids(
        scenario: RatingScenarios,
        thread_ids: Optional[List[int]] = None,
    ) -> List[int]:
        threads = ScenarioThreads.query.filter_by(scenario_id=scenario.id).all()
        available = [t.thread_id for t in threads]
        if thread_ids:
            thread_set = {tid for tid in thread_ids if isinstance(tid, int)}
            return [tid for tid in available if tid in thread_set]
        return available

    @staticmethod
    def _store_error(
        *,
        scenario_id: int,
        thread_id: int,
        model_id: str,
        task_type: str,
        error: str,
        raw_response: Optional[str] = None,
    ) -> None:
        try:
            existing = LLMTaskResult.query.filter_by(
                scenario_id=scenario_id,
                thread_id=thread_id,
                model_id=model_id,
                task_type=task_type,
            ).first()
            if existing:
                existing.error = error
                if raw_response:
                    existing.raw_response = raw_response
                db.session.add(existing)
            else:
                db.session.add(LLMTaskResult(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type=task_type,
                    payload_json=None,
                    raw_response=raw_response,
                    error=error,
                ))
            db.session.commit()
        except Exception:
            db.session.rollback()

    @staticmethod
    def _run_ranking(model_id: str, thread_ids: Iterable[int], scenario_id: int) -> None:
        client = LLMClientFactory.get_client_for_model(model_id)

        for thread_id in thread_ids:
            try:
                existing = LLMTaskResult.query.filter_by(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="ranking",
                ).first()
                if existing and existing.payload_json:
                    continue

                features = Feature.query.filter_by(thread_id=thread_id).all()
                if not features:
                    continue

                seed = int(
                    hashlib.sha256(
                        f"{scenario_id}:{thread_id}:{model_id}".encode("utf-8")
                    ).hexdigest()[:8],
                    16,
                )
                rng = random.Random(seed)
                shuffled = list(features)
                rng.shuffle(shuffled)

                feature_lines = []
                for feature in shuffled:
                    feature_lines.append(
                        f"- ID {feature.feature_id} (Typ: {feature.feature_type.name}, Modell: {feature.llm.name}): {feature.content}"
                    )

                system_prompt = (
                    "Du bist ein strenger Evaluator für Feature-Rankings. "
                    "Antworte ausschließlich im JSON-Format."
                )
                user_prompt = (
                    "Ordne alle Feature-IDs genau einmal einem Bucket zu. "
                    "Erlaubte Buckets: gut, mittel, schlecht, neutral.\n"
                    "Gib JSON im Format:\n"
                    "{\n"
                    '  "gut": [feature_id, ...],\n'
                    '  "mittel": [feature_id, ...],\n'
                    '  "schlecht": [feature_id, ...],\n'
                    '  "neutral": [feature_id, ...]\n'
                    "}\n\n"
                    "Features (zufällig sortiert):\n"
                    + "\n".join(feature_lines)
                )

                raw_response = None
                payload, raw_response = LLMAITaskRunner._request_json(
                    client,
                    model_id,
                    system_prompt,
                    user_prompt,
                    max_tokens=1200,
                    trace={
                        "task": "ranking",
                        "scenario_id": scenario_id,
                        "thread_id": thread_id,
                        "model_id": model_id,
                    },
                )
                bucket_map = LLMAITaskRunner._validate_bucket_payload(payload, features)
                if not bucket_map:
                    raise ValueError("Invalid ranking payload")

                if existing:
                    existing.payload_json = bucket_map
                    existing.raw_response = raw_response
                    existing.error = None
                    db.session.add(existing)
                else:
                    db.session.add(LLMTaskResult(
                        scenario_id=scenario_id,
                        thread_id=thread_id,
                        model_id=model_id,
                        task_type="ranking",
                        payload_json=bucket_map,
                        raw_response=raw_response,
                        error=None,
                    ))
                db.session.commit()

                # Broadcast success
                _broadcast_task_completed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="ranking",
                    result=bucket_map,
                )

            except LLMResponseError as exc:
                db.session.rollback()
                LLMAITaskRunner._store_error(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="ranking",
                    error=str(exc),
                    raw_response=exc.raw_response,
                )
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="ranking",
                    error=str(exc),
                )
            except Exception as exc:
                db.session.rollback()
                logger.warning("[LLM AI Runner] Ranking failed for thread %s: %s", thread_id, exc)
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="ranking",
                    error=str(exc),
                )

    @staticmethod
    def _run_rating(model_id: str, thread_ids: Iterable[int], scenario_id: int) -> None:
        client = LLMClientFactory.get_client_for_model(model_id)

        for thread_id in thread_ids:
            try:
                existing = LLMTaskResult.query.filter_by(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="rating",
                ).first()
                if existing and existing.payload_json:
                    continue

                thread = EmailThread.query.filter_by(thread_id=thread_id).first()
                features = Feature.query.filter_by(thread_id=thread_id).all()
                if not thread or not features:
                    continue

                messages = Message.query.filter_by(thread_id=thread_id).order_by(Message.timestamp.asc()).all()
                message_lines = [
                    f"{msg.sender}: {msg.content}"
                    for msg in messages
                ]

                feature_lines = []
                for feature in features:
                    feature_lines.append(
                        f"- ID {feature.feature_id} (Typ: {feature.feature_type.name}, Modell: {feature.llm.name}): {feature.content}"
                    )

                system_prompt = (
                    "Bewerte die Qualität jedes Features auf einer Skala von 1 (schlecht) bis 5 (sehr gut). "
                    "Antworte ausschließlich im JSON-Format."
                )
                user_prompt = (
                    "Gib JSON im Format:\n"
                    "{\n"
                    '  "ratings": [{"feature_id": 123, "rating": 1}, ...]\n'
                    "}\n\n"
                    "Kontext (Konversation):\n"
                    + "\n".join(message_lines)
                    + "\n\nFeatures:\n"
                    + "\n".join(feature_lines)
                )

                raw_response = None
                payload, raw_response = LLMAITaskRunner._request_json(
                    client,
                    model_id,
                    system_prompt,
                    user_prompt,
                    max_tokens=1200,
                    trace={
                        "task": "rating",
                        "scenario_id": scenario_id,
                        "thread_id": thread_id,
                        "model_id": model_id,
                    },
                )
                ratings = LLMAITaskRunner._validate_ratings_payload(payload, features)
                if ratings is None:
                    raise ValueError("Invalid ratings payload")

                payload_out = {
                    "ratings": [
                        {"feature_id": fid, "rating": rating}
                        for fid, rating in ratings.items()
                    ]
                }
                if existing:
                    existing.payload_json = payload_out
                    existing.raw_response = raw_response
                    existing.error = None
                    db.session.add(existing)
                else:
                    db.session.add(LLMTaskResult(
                        scenario_id=scenario_id,
                        thread_id=thread_id,
                        model_id=model_id,
                        task_type="rating",
                        payload_json=payload_out,
                        raw_response=raw_response,
                        error=None,
                    ))
                db.session.commit()

                # Broadcast success
                _broadcast_task_completed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="rating",
                    result=payload_out,
                )

            except LLMResponseError as exc:
                db.session.rollback()
                LLMAITaskRunner._store_error(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="rating",
                    error=str(exc),
                    raw_response=exc.raw_response,
                )
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="rating",
                    error=str(exc),
                )
            except Exception as exc:
                db.session.rollback()
                logger.warning("[LLM AI Runner] Rating failed for thread %s: %s", thread_id, exc)
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="rating",
                    error=str(exc),
                )

    @staticmethod
    def _run_authenticity(model_id: str, thread_ids: Iterable[int], scenario_id: int) -> None:
        client = LLMClientFactory.get_client_for_model(model_id)

        for thread_id in thread_ids:
            try:
                existing = LLMTaskResult.query.filter_by(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="authenticity",
                ).first()
                if existing and existing.payload_json:
                    continue

                messages = Message.query.filter_by(thread_id=thread_id).order_by(Message.timestamp.asc()).all()
                if not messages:
                    continue

                message_lines = [f"{msg.sender}: {msg.content}" for msg in messages]
                system_prompt = (
                    "Entscheide, ob die Konversation echt (real) oder künstlich (fake) ist. "
                    "Antworte ausschließlich im JSON-Format."
                )
                user_prompt = (
                    "Gib JSON im Format:\n"
                    "{\n"
                    '  "vote": "real" | "fake",\n'
                    '  "confidence": 1-5\n'
                    "}\n\n"
                    "Konversation:\n"
                    + "\n".join(message_lines)
                )

                raw_response = None
                payload, raw_response = LLMAITaskRunner._request_json(
                    client,
                    model_id,
                    system_prompt,
                    user_prompt,
                    max_tokens=300,
                    trace={
                        "task": "authenticity",
                        "scenario_id": scenario_id,
                        "thread_id": thread_id,
                        "model_id": model_id,
                    },
                )
                vote_data = LLMAITaskRunner._validate_authenticity_payload(payload)
                if vote_data is None:
                    raise ValueError("Invalid authenticity payload")

                if existing:
                    existing.payload_json = vote_data
                    existing.raw_response = raw_response
                    existing.error = None
                    db.session.add(existing)
                else:
                    db.session.add(LLMTaskResult(
                        scenario_id=scenario_id,
                        thread_id=thread_id,
                        model_id=model_id,
                        task_type="authenticity",
                        payload_json=vote_data,
                        raw_response=raw_response,
                        error=None,
                    ))
                db.session.commit()

                # Broadcast success
                _broadcast_task_completed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="authenticity",
                    result=vote_data,
                )

            except LLMResponseError as exc:
                db.session.rollback()
                LLMAITaskRunner._store_error(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="authenticity",
                    error=str(exc),
                    raw_response=exc.raw_response,
                )
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="authenticity",
                    error=str(exc),
                )
            except Exception as exc:
                db.session.rollback()
                logger.warning("[LLM AI Runner] Authenticity failed for thread %s: %s", thread_id, exc)
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="authenticity",
                    error=str(exc),
                )

    @staticmethod
    def _run_mail_rating(model_id: str, thread_ids: Iterable[int], scenario_id: int) -> None:
        """Rate entire email conversations on a scale of 1-5."""
        client = LLMClientFactory.get_client_for_model(model_id)

        for thread_id in thread_ids:
            try:
                existing = LLMTaskResult.query.filter_by(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="mail_rating",
                ).first()
                if existing and existing.payload_json:
                    continue

                thread = EmailThread.query.filter_by(thread_id=thread_id).first()
                if not thread:
                    continue

                messages = Message.query.filter_by(thread_id=thread_id).order_by(Message.timestamp.asc()).all()
                if not messages:
                    continue

                message_lines = [f"{msg.sender}: {msg.content}" for msg in messages]

                system_prompt = (
                    "Du bist ein Experte für die Bewertung von E-Mail-Konversationen. "
                    "Bewerte die Gesamtqualität der Beratungskonversation auf einer Skala von 1 bis 5. "
                    "Berücksichtige dabei: Empathie, Fachlichkeit, Verständlichkeit, Hilfsbereitschaft und Lösungsorientierung. "
                    "Antworte ausschließlich im JSON-Format."
                )
                user_prompt = (
                    "Bewerte die folgende E-Mail-Konversation.\n"
                    "Gib JSON im Format:\n"
                    "{\n"
                    '  "rating": 1-5,\n'
                    '  "reasoning": "Kurze Begründung für die Bewertung"\n'
                    "}\n\n"
                    f"Betreff: {thread.subject or 'Kein Betreff'}\n\n"
                    "Konversation:\n"
                    + "\n".join(message_lines)
                )

                raw_response = None
                payload, raw_response = LLMAITaskRunner._request_json(
                    client,
                    model_id,
                    system_prompt,
                    user_prompt,
                    max_tokens=500,
                    trace={
                        "task": "mail_rating",
                        "scenario_id": scenario_id,
                        "thread_id": thread_id,
                        "model_id": model_id,
                    },
                )
                rating_data = LLMAITaskRunner._validate_mail_rating_payload(payload)
                if rating_data is None:
                    raise ValueError("Invalid mail_rating payload")

                if existing:
                    existing.payload_json = rating_data
                    existing.raw_response = raw_response
                    existing.error = None
                    db.session.add(existing)
                else:
                    db.session.add(LLMTaskResult(
                        scenario_id=scenario_id,
                        thread_id=thread_id,
                        model_id=model_id,
                        task_type="mail_rating",
                        payload_json=rating_data,
                        raw_response=raw_response,
                        error=None,
                    ))
                db.session.commit()

                # Broadcast success
                _broadcast_task_completed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="mail_rating",
                    result=rating_data,
                )

            except LLMResponseError as exc:
                db.session.rollback()
                LLMAITaskRunner._store_error(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="mail_rating",
                    error=str(exc),
                    raw_response=exc.raw_response,
                )
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="mail_rating",
                    error=str(exc),
                )
            except Exception as exc:
                db.session.rollback()
                logger.warning("[LLM AI Runner] Mail rating failed for thread %s: %s", thread_id, exc)
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="mail_rating",
                    error=str(exc),
                )

    @staticmethod
    def _run_text_classification(
        model_id: str,
        thread_ids: Iterable[int],
        scenario_id: int,
        scenario: RatingScenarios
    ) -> None:
        """Classify texts into custom labels defined in scenario config."""
        client = LLMClientFactory.get_client_for_model(model_id)

        # Get custom labels from scenario config
        config = scenario.config_json if isinstance(scenario.config_json, dict) else {}
        custom_labels = config.get("classification_labels", ["positive", "negative", "neutral"])
        label_descriptions = config.get("label_descriptions", {})

        labels_text = ", ".join(f'"{label}"' for label in custom_labels)
        descriptions_text = ""
        if label_descriptions:
            descriptions_text = "\n".join(
                f"- {label}: {desc}" for label, desc in label_descriptions.items()
            )
            descriptions_text = f"\n\nLabel-Beschreibungen:\n{descriptions_text}"

        for thread_id in thread_ids:
            try:
                existing = LLMTaskResult.query.filter_by(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="text_classification",
                ).first()
                if existing and existing.payload_json:
                    continue

                messages = Message.query.filter_by(thread_id=thread_id).order_by(Message.timestamp.asc()).all()
                if not messages:
                    continue

                # Combine all messages as text to classify
                text_content = "\n".join(f"{msg.sender}: {msg.content}" for msg in messages)

                system_prompt = (
                    "Du bist ein Experte für Textklassifikation. "
                    "Klassifiziere den folgenden Text in eine der vorgegebenen Kategorien. "
                    "Antworte ausschließlich im JSON-Format."
                )
                user_prompt = (
                    f"Klassifiziere den folgenden Text.\n"
                    f"Erlaubte Labels: {labels_text}{descriptions_text}\n\n"
                    "Gib JSON im Format:\n"
                    "{\n"
                    f'  "label": "<eines der Labels: {labels_text}>",\n'
                    '  "confidence": 1-5,\n'
                    '  "reasoning": "Kurze Begründung"\n'
                    "}\n\n"
                    f"Text:\n{text_content}"
                )

                raw_response = None
                payload, raw_response = LLMAITaskRunner._request_json(
                    client,
                    model_id,
                    system_prompt,
                    user_prompt,
                    max_tokens=500,
                    trace={
                        "task": "text_classification",
                        "scenario_id": scenario_id,
                        "thread_id": thread_id,
                        "model_id": model_id,
                    },
                )
                classification_data = LLMAITaskRunner._validate_classification_payload(payload, custom_labels)
                if classification_data is None:
                    raise ValueError("Invalid text_classification payload")

                if existing:
                    existing.payload_json = classification_data
                    existing.raw_response = raw_response
                    existing.error = None
                    db.session.add(existing)
                else:
                    db.session.add(LLMTaskResult(
                        scenario_id=scenario_id,
                        thread_id=thread_id,
                        model_id=model_id,
                        task_type="text_classification",
                        payload_json=classification_data,
                        raw_response=raw_response,
                        error=None,
                    ))
                db.session.commit()

                # Broadcast success
                _broadcast_task_completed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="text_classification",
                    result=classification_data,
                )

            except LLMResponseError as exc:
                db.session.rollback()
                LLMAITaskRunner._store_error(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="text_classification",
                    error=str(exc),
                    raw_response=exc.raw_response,
                )
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="text_classification",
                    error=str(exc),
                )
            except Exception as exc:
                db.session.rollback()
                logger.warning("[LLM AI Runner] Text classification failed for thread %s: %s", thread_id, exc)
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="text_classification",
                    error=str(exc),
                )

    @staticmethod
    def _run_comparison(model_id: str, thread_ids: Iterable[int], scenario_id: int) -> None:
        """Compare two responses/texts and choose the better one."""
        client = LLMClientFactory.get_client_for_model(model_id)

        for thread_id in thread_ids:
            try:
                existing = LLMTaskResult.query.filter_by(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="comparison",
                ).first()
                if existing and existing.payload_json:
                    continue

                thread = EmailThread.query.filter_by(thread_id=thread_id).first()
                if not thread:
                    continue

                messages = Message.query.filter_by(thread_id=thread_id).order_by(Message.timestamp.asc()).all()
                if len(messages) < 2:
                    continue

                # Assume first two messages are the two texts to compare
                # Or use specific message structure for A/B comparison
                text_a = messages[0].content if messages else ""
                text_b = messages[1].content if len(messages) > 1 else ""

                system_prompt = (
                    "Du bist ein Experte für den Vergleich von Texten/Antworten. "
                    "Vergleiche die beiden Texte und entscheide, welcher besser ist. "
                    "Antworte ausschließlich im JSON-Format."
                )
                user_prompt = (
                    "Vergleiche die folgenden zwei Texte/Antworten.\n\n"
                    f"Text A:\n{text_a}\n\n"
                    f"Text B:\n{text_b}\n\n"
                    "Gib JSON im Format:\n"
                    "{\n"
                    '  "winner": "A" | "B" | "tie",\n'
                    '  "confidence": 1-5,\n'
                    '  "reasoning": "Begründung für die Entscheidung"\n'
                    "}"
                )

                raw_response = None
                payload, raw_response = LLMAITaskRunner._request_json(
                    client,
                    model_id,
                    system_prompt,
                    user_prompt,
                    max_tokens=500,
                    trace={
                        "task": "comparison",
                        "scenario_id": scenario_id,
                        "thread_id": thread_id,
                        "model_id": model_id,
                    },
                )
                comparison_data = LLMAITaskRunner._validate_comparison_payload(payload)
                if comparison_data is None:
                    raise ValueError("Invalid comparison payload")

                if existing:
                    existing.payload_json = comparison_data
                    existing.raw_response = raw_response
                    existing.error = None
                    db.session.add(existing)
                else:
                    db.session.add(LLMTaskResult(
                        scenario_id=scenario_id,
                        thread_id=thread_id,
                        model_id=model_id,
                        task_type="comparison",
                        payload_json=comparison_data,
                        raw_response=raw_response,
                        error=None,
                    ))
                db.session.commit()

                # Broadcast success
                _broadcast_task_completed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="comparison",
                    result=comparison_data,
                )

            except LLMResponseError as exc:
                db.session.rollback()
                LLMAITaskRunner._store_error(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="comparison",
                    error=str(exc),
                    raw_response=exc.raw_response,
                )
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="comparison",
                    error=str(exc),
                )
            except Exception as exc:
                db.session.rollback()
                logger.warning("[LLM AI Runner] Comparison failed for thread %s: %s", thread_id, exc)
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type="comparison",
                    error=str(exc),
                )

    @staticmethod
    def _request_json(
        client,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int,
        trace: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], str]:
        base_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        last_error = None
        trace_label = _format_trace(trace)
        last_raw = ""
        log_settings = _get_log_settings()
        log_prompts = bool(log_settings.get("log_prompts"))
        log_responses = bool(log_settings.get("log_responses"))
        log_response_max = int(log_settings.get("log_response_max", 800))
        log_prompt_max = int(log_settings.get("log_prompt_max", 800))
        log_tasks = log_settings.get("log_tasks", set())

        for attempt in range(LLMAITaskRunner.MAX_RETRIES + 1):
            messages = list(base_messages)
            if last_error:
                messages.append({
                    "role": "user",
                    "content": f"Deine vorherige Antwort war ungültig ({last_error}). "
                               "Bitte nur valides JSON gemäß Schema liefern."
                })

            if log_prompts and _should_log(trace, log_prompts=log_prompts, log_responses=log_responses, log_tasks=log_tasks):
                logger.info(
                    "[LLM AI Runner] prompt attempt=%s %s system=%s",
                    attempt + 1,
                    trace_label,
                    _truncate(system_prompt, log_prompt_max),
                )
                logger.info(
                    "[LLM AI Runner] prompt attempt=%s %s user=%s",
                    attempt + 1,
                    trace_label,
                    _truncate(user_prompt, log_prompt_max),
                )

            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=0.2,
                max_tokens=max_tokens,
                extra_body={"response_format": {"type": "json_object"}},
            )
            content = extract_message_text(response.choices[0].message) if response.choices else ""
            last_raw = content or ""
            if log_responses and _should_log(trace, log_prompts=log_prompts, log_responses=log_responses, log_tasks=log_tasks):
                logger.info(
                    "[LLM AI Runner] response attempt=%s %s %s",
                    attempt + 1,
                    trace_label,
                    _truncate(content, log_response_max),
                )
            try:
                parsed = LLMAITaskRunner._parse_json(content)
                if log_responses and _should_log(trace, log_prompts=log_prompts, log_responses=log_responses, log_tasks=log_tasks):
                    logger.info(
                        "[LLM AI Runner] parsed %s %s",
                        trace_label,
                        _truncate(parsed, log_response_max),
                    )
                return parsed, content
            except Exception as exc:
                last_error = str(exc)
                if log_responses and _should_log(trace, log_prompts=log_prompts, log_responses=log_responses, log_tasks=log_tasks):
                    logger.warning(
                        "[LLM AI Runner] invalid json %s error=%s",
                        trace_label,
                        last_error,
                    )
                if attempt == LLMAITaskRunner.MAX_RETRIES:
                    raise LLMResponseError(last_error, raw_response=last_raw)
        raise LLMResponseError("LLM did not return valid JSON", raw_response=last_raw)

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        raw = (text or "").strip()
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)

    @staticmethod
    def _validate_bucket_payload(payload: Dict[str, Any], features: List[Feature]) -> Optional[Dict[str, List[int]]]:
        if not isinstance(payload, dict):
            return None
        expected_ids = {f.feature_id for f in features}
        buckets = {}
        for key in ("gut", "mittel", "schlecht", "neutral"):
            ids = payload.get(key, [])
            if not isinstance(ids, list):
                return None
            clean_ids = []
            for item in ids:
                if isinstance(item, int):
                    clean_ids.append(item)
                elif isinstance(item, str) and item.strip().isdigit():
                    clean_ids.append(int(item.strip()))
                else:
                    return None
            buckets[key] = clean_ids

        all_ids = [fid for ids in buckets.values() for fid in ids]
        if len(set(all_ids)) != len(all_ids):
            return None
        if set(all_ids) != expected_ids:
            return None
        return buckets

    @staticmethod
    def _validate_ratings_payload(payload: Dict[str, Any], features: List[Feature]) -> Optional[Dict[int, int]]:
        ratings = payload.get("ratings") if isinstance(payload, dict) else None
        if not isinstance(ratings, list):
            return None
        expected_ids = {f.feature_id for f in features}
        out: Dict[int, int] = {}
        for item in ratings:
            if not isinstance(item, dict):
                return None
            feature_id = item.get("feature_id")
            rating = item.get("rating")
            if isinstance(feature_id, str) and feature_id.strip().isdigit():
                feature_id = int(feature_id.strip())
            if not isinstance(feature_id, int):
                return None
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return None
            out[feature_id] = rating

        if set(out.keys()) != expected_ids:
            return None
        return out

    @staticmethod
    def _validate_authenticity_payload(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(payload, dict):
            return None
        vote = payload.get("vote")
        confidence = payload.get("confidence")
        if isinstance(vote, str):
            vote = vote.strip().lower()
        if vote not in {"real", "fake"}:
            return None
        if isinstance(confidence, str) and confidence.strip().isdigit():
            confidence = int(confidence.strip())
        if not isinstance(confidence, int) or confidence < 1 or confidence > 5:
            return None
        return {"vote": vote, "confidence": confidence}

    @staticmethod
    def _validate_mail_rating_payload(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate mail_rating response: rating (1-5) and optional reasoning."""
        if not isinstance(payload, dict):
            return None
        rating = payload.get("rating")
        reasoning = payload.get("reasoning", "")

        # Handle string ratings
        if isinstance(rating, str) and rating.strip().isdigit():
            rating = int(rating.strip())

        # Validate rating is 1-5
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return None

        # Reasoning is optional but should be a string if present
        if reasoning and not isinstance(reasoning, str):
            reasoning = str(reasoning)

        return {"rating": rating, "reasoning": reasoning or ""}

    @staticmethod
    def _validate_classification_payload(
        payload: Dict[str, Any],
        allowed_labels: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Validate text_classification response with custom labels."""
        if not isinstance(payload, dict):
            return None
        label = payload.get("label")
        confidence = payload.get("confidence", 3)
        reasoning = payload.get("reasoning", "")

        # Normalize label
        if isinstance(label, str):
            label = label.strip().lower()
            # Try to match against allowed labels (case-insensitive)
            for allowed in allowed_labels:
                if allowed.lower() == label:
                    label = allowed
                    break

        # Validate label is in allowed list
        if label not in allowed_labels and label.lower() not in [l.lower() for l in allowed_labels]:
            return None

        # Validate confidence
        if isinstance(confidence, str) and confidence.strip().isdigit():
            confidence = int(confidence.strip())
        if not isinstance(confidence, int) or confidence < 1 or confidence > 5:
            confidence = 3  # Default if invalid

        return {"label": label, "confidence": confidence, "reasoning": reasoning or ""}

    @staticmethod
    def _validate_comparison_payload(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate comparison response: winner (A/B/tie) and confidence."""
        if not isinstance(payload, dict):
            return None
        winner = payload.get("winner")
        confidence = payload.get("confidence", 3)
        reasoning = payload.get("reasoning", "")

        # Normalize winner
        if isinstance(winner, str):
            winner = winner.strip().upper()
        if winner not in {"A", "B", "TIE"}:
            # Try lowercase
            if winner and winner.lower() in {"a", "b", "tie"}:
                winner = winner.upper() if winner.lower() != "tie" else "tie"
            else:
                return None

        # Validate confidence
        if isinstance(confidence, str) and confidence.strip().isdigit():
            confidence = int(confidence.strip())
        if not isinstance(confidence, int) or confidence < 1 or confidence > 5:
            confidence = 3

        return {"winner": winner, "confidence": confidence, "reasoning": reasoning or ""}
