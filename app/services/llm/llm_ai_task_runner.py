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
    ComparisonMessage,
    ComparisonSession,
    EmailThread,
    EvaluationItem,
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

        # Comparison scenarios use ComparisonSessions, not ScenarioThreads
        if function_name == "comparison":
            session_ids = LLMAITaskRunner._resolve_comparison_session_ids(scenario, thread_ids)
            if not session_ids:
                logger.info("[LLM AI Runner] No comparison sessions for scenario %s", scenario_id)
                return
            for model_id in resolved_models:
                LLMAITaskRunner._run_comparison_sessions(model_id, session_ids, scenario.id)
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
            elif function_name in ("labeling", "text_classification"):
                task_type = "labeling" if function_name == "labeling" else "text_classification"
                LLMAITaskRunner._run_text_classification(
                    model_id,
                    scenario_thread_ids,
                    scenario.id,
                    scenario,
                    task_type=task_type,
                )
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
    def _resolve_comparison_session_ids(
        scenario: RatingScenarios,
        session_ids: Optional[List[int]] = None,
    ) -> List[int]:
        """Resolve ComparisonSession IDs for comparison scenarios."""
        sessions = ComparisonSession.query.filter_by(scenario_id=scenario.id).all()
        available = [s.id for s in sessions]
        if session_ids:
            session_set = {sid for sid in session_ids if isinstance(sid, int)}
            return [sid for sid in available if sid in session_set]
        return available

    @staticmethod
    def _run_comparison_sessions(
        model_id: str,
        session_ids: Iterable[int],
        scenario_id: int
    ) -> None:
        """
        Run LLM evaluation for ComparisonSessions.

        For each session, evaluate all bot_pair messages where the LLM
        compares the two responses and picks a winner.
        """
        client = LLMClientFactory.get_client_for_model(model_id)

        for session_id in session_ids:
            try:
                session = ComparisonSession.query.get(session_id)
                if not session:
                    continue

                # Get all bot_pair messages for this session
                bot_pair_messages = ComparisonMessage.query.filter_by(
                    session_id=session_id,
                    type='bot_pair'
                ).order_by(ComparisonMessage.idx.asc()).all()

                if not bot_pair_messages:
                    continue

                for msg in bot_pair_messages:
                    # Check if we already have a result for this message
                    # Use session_id as thread_id and msg.idx as a sub-identifier in payload
                    existing = LLMTaskResult.query.filter_by(
                        scenario_id=scenario_id,
                        thread_id=session_id,  # Using session_id as thread_id
                        model_id=model_id,
                        task_type="comparison",
                    ).first()

                    # Check if this specific message idx was already evaluated
                    if existing and existing.payload_json:
                        evaluated_indices = existing.payload_json.get('evaluated_indices', [])
                        if msg.idx in evaluated_indices:
                            continue

                    # Parse the bot_pair content (JSON with llm1 and llm2 responses)
                    try:
                        content = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                        llm1_response = content.get('llm1', '')
                        llm2_response = content.get('llm2', '')
                    except (json.JSONDecodeError, TypeError):
                        # If not JSON, skip
                        continue

                    if not llm1_response or not llm2_response:
                        continue

                    # Get context from previous user message
                    user_msg = ComparisonMessage.query.filter_by(
                        session_id=session_id,
                        type='user',
                        idx=msg.idx - 1
                    ).first()
                    user_question = user_msg.content if user_msg else "Keine Frage verfügbar"

                    system_prompt = (
                        "Du bist ein Experte für den Vergleich von KI-Antworten. "
                        "Vergleiche die beiden Antworten auf die gleiche Nutzeranfrage und "
                        "entscheide, welche besser ist. "
                        "Antworte ausschließlich im JSON-Format."
                    )
                    user_prompt = (
                        f"Nutzeranfrage: {user_question}\n\n"
                        f"Antwort A (LLM 1):\n{llm1_response}\n\n"
                        f"Antwort B (LLM 2):\n{llm2_response}\n\n"
                        "Welche Antwort ist besser? Gib JSON im Format:\n"
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
                            "session_id": session_id,
                            "message_idx": msg.idx,
                            "model_id": model_id,
                        },
                    )

                    comparison_data = LLMAITaskRunner._validate_comparison_payload(payload)
                    if comparison_data is None:
                        raise ValueError("Invalid comparison payload")

                    # Add message index to track which messages were evaluated
                    comparison_data['message_idx'] = msg.idx
                    comparison_data['session_id'] = session_id

                    if existing:
                        # Append to existing results
                        existing_results = existing.payload_json.get('results', []) if existing.payload_json else []
                        existing_results.append(comparison_data)
                        evaluated_indices = existing.payload_json.get('evaluated_indices', []) if existing.payload_json else []
                        evaluated_indices.append(msg.idx)
                        existing.payload_json = {
                            'results': existing_results,
                            'evaluated_indices': evaluated_indices,
                        }
                        existing.raw_response = raw_response
                        existing.error = None
                        db.session.add(existing)
                    else:
                        db.session.add(LLMTaskResult(
                            scenario_id=scenario_id,
                            thread_id=session_id,
                            model_id=model_id,
                            task_type="comparison",
                            payload_json={
                                'results': [comparison_data],
                                'evaluated_indices': [msg.idx],
                            },
                            raw_response=raw_response,
                            error=None,
                        ))
                    db.session.commit()

                    # Broadcast success
                    _broadcast_task_completed(
                        scenario_id=scenario_id,
                        model_id=model_id,
                        thread_id=session_id,
                        task_type="comparison",
                        result=comparison_data,
                    )

            except LLMResponseError as exc:
                db.session.rollback()
                LLMAITaskRunner._store_error(
                    scenario_id=scenario_id,
                    thread_id=session_id,
                    model_id=model_id,
                    task_type="comparison",
                    error=str(exc),
                    raw_response=exc.raw_response if hasattr(exc, 'raw_response') else None,
                )
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=session_id,
                    task_type="comparison",
                    error=str(exc),
                )
            except Exception as exc:
                db.session.rollback()
                logger.warning(
                    "[LLM AI Runner] Comparison session %s failed: %s",
                    session_id,
                    exc,
                )
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=session_id,
                    task_type="comparison",
                    error=str(exc),
                )

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
    def _get_bucket_config(scenario: RatingScenarios) -> Tuple[List[str], List[str]]:
        """
        Extract bucket configuration from scenario config_json.

        Returns:
            Tuple of (bucket_names, bucket_keys) where:
            - bucket_names: Display names for prompts (e.g., ["Gut", "Mittel", "Schlecht"])
            - bucket_keys: Lowercase keys for JSON response (e.g., ["gut", "mittel", "schlecht"])
        """
        default_buckets = ["Gut", "Mittel", "Schlecht", "Neutral"]
        config = scenario.config_json
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except (json.JSONDecodeError, TypeError):
                config = {}
        if not isinstance(config, dict):
            config = {}

        buckets_config = config.get("buckets", [])
        if not buckets_config or not isinstance(buckets_config, list):
            return default_buckets, [b.lower() for b in default_buckets]

        bucket_names = []
        for bucket in buckets_config:
            if isinstance(bucket, dict):
                name = bucket.get("name", {})
                if isinstance(name, dict):
                    # Use German name, fallback to English, fallback to id
                    bucket_name = name.get("de") or name.get("en") or str(bucket.get("id", ""))
                elif isinstance(name, str):
                    bucket_name = name
                else:
                    bucket_name = str(bucket.get("id", ""))
                if bucket_name:
                    bucket_names.append(bucket_name)
            elif isinstance(bucket, str):
                bucket_names.append(bucket)

        if not bucket_names:
            return default_buckets, [b.lower() for b in default_buckets]

        bucket_keys = [b.lower() for b in bucket_names]
        return bucket_names, bucket_keys

    @staticmethod
    def _run_ranking(model_id: str, thread_ids: Iterable[int], scenario_id: int) -> None:
        client = LLMClientFactory.get_client_for_model(model_id)

        # Load scenario to get bucket configuration
        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            logger.warning("[LLM AI Runner] Scenario not found for ranking: %s", scenario_id)
            return

        bucket_names, bucket_keys = LLMAITaskRunner._get_bucket_config(scenario)
        thread_ids_list = list(thread_ids)

        for thread_id in thread_ids_list:
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

                # NEW: If no Features, try EvaluationItem/Message approach
                if not features:
                    LLMAITaskRunner._run_ranking_for_item(
                        client, model_id, thread_id, scenario_id, bucket_keys
                    )
                    continue

                # Legacy: Feature-based ranking (multiple features per thread)
                # Load messages to get source/context text
                messages = Message.query.filter_by(thread_id=thread_id).order_by(Message.timestamp).all()
                source_text = None
                for msg in messages:
                    # Look for source article or similar context messages
                    sender_lower = (msg.sender or "").lower()
                    if "source" in sender_lower or "artikel" in sender_lower or "original" in sender_lower:
                        source_text = msg.content
                        break
                # Fallback: use first message if no explicit source found
                if not source_text and messages:
                    source_text = messages[0].content

                seed = int(
                    hashlib.sha256(
                        f"{scenario_id}:{thread_id}:{model_id}".encode("utf-8")
                    ).hexdigest()[:8],
                    16,
                )
                rng = random.Random(seed)
                shuffled = list(features)
                rng.shuffle(shuffled)

                # Determine feature type for context-aware prompts
                feature_type = features[0].feature_type.name if features else "Feature"
                is_summary_ranking = feature_type.lower() in ("summary", "zusammenfassung")

                # Build feature list with letter IDs for easier reference
                feature_lines = []
                letter_map = {}  # Maps letter to feature_id for response parsing
                for idx, feature in enumerate(shuffled):
                    letter = chr(65 + idx)  # A, B, C, ...
                    letter_map[letter] = feature.feature_id
                    # Truncate very long content for prompt efficiency
                    content = feature.content[:500] + "..." if len(feature.content) > 500 else feature.content
                    feature_lines.append(f"{letter} (ID {feature.feature_id}): {content}")

                # Build dynamic prompt based on configured buckets
                buckets_list = ", ".join(bucket_keys)
                json_example_lines = [f'  "{key}": [feature_id, ...]' for key in bucket_keys]
                json_example = "{\n" + ",\n".join(json_example_lines) + "\n}"

                # Context-aware system prompt
                if is_summary_ranking and source_text:
                    system_prompt = """Du bist ein Experte für die Bewertung von Textzusammenfassungen.

Bewertungskriterien:
- **Relevanz**: Erfasst die wichtigsten Informationen des Originaltexts
- **Konsistenz**: Faktentreu, keine erfundenen Informationen
- **Kohärenz**: Logischer Aufbau, zusammenhängende Sätze
- **Flüssigkeit**: Gut lesbar, grammatikalisch korrekt

Antworte AUSSCHLIESSLICH im JSON-Format mit den Feature-IDs (Zahlen)."""

                    user_prompt = f"""Bewerte die folgenden Zusammenfassungen basierend auf dem Originaltext.

ORIGINALTEXT:
{source_text[:2000]}{"..." if len(source_text) > 2000 else ""}

ZUSAMMENFASSUNGEN (zufällig sortiert):
{chr(10).join(feature_lines)}

Ordne JEDE Feature-ID genau EINEM Bucket zu:
- **{bucket_keys[0]}**: Erfasst Kerninhalt präzise, faktisch korrekt, gut lesbar
- **{bucket_keys[1] if len(bucket_keys) > 1 else 'mittel'}**: Akzeptabel, aber mit Schwächen (fehlende Details, kleine Fehler)
- **{bucket_keys[2] if len(bucket_keys) > 2 else 'schlecht'}**: Unvollständig, faktisch falsch, oder schlecht lesbar
{f'- **{bucket_keys[3]}**: Nicht eindeutig kategorisierbar' if len(bucket_keys) > 3 else ''}

Antworte im JSON-Format (verwende die numerischen Feature-IDs, nicht die Buchstaben):
{json_example}"""
                else:
                    # Generic ranking prompt for non-summary features
                    system_prompt = (
                        "Du bist ein strenger Evaluator für Qualitäts-Rankings. "
                        "Antworte ausschließlich im JSON-Format."
                    )
                    context_section = f"\nKONTEXT:\n{source_text[:1500]}...\n" if source_text else ""
                    user_prompt = (
                        f"Ordne alle Feature-IDs genau einmal einem Bucket zu. "
                        f"Erlaubte Buckets: {buckets_list}.\n"
                        f"{context_section}\n"
                        f"Features (zufällig sortiert):\n"
                        + "\n".join(feature_lines)
                        + f"\n\nGib JSON im Format:\n{json_example}"
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
                bucket_map = LLMAITaskRunner._validate_bucket_payload(payload, features, bucket_keys)
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
    def _run_ranking_for_item(
        client,
        model_id: str,
        thread_id: int,
        scenario_id: int,
        bucket_keys: List[str],
    ) -> None:
        """
        Rank a single EvaluationItem/Message into a bucket.

        This is used when no Features exist but we have an EvaluationItem with content.
        The item content (from Message) is evaluated and assigned to a quality bucket.
        """
        from db.models import EvaluationItem

        try:
            # Check if already processed
            existing = LLMTaskResult.query.filter_by(
                scenario_id=scenario_id,
                thread_id=thread_id,
                model_id=model_id,
                task_type="ranking",
            ).first()
            if existing and existing.payload_json:
                return

            # Load the EvaluationItem and its messages
            item = EvaluationItem.query.get(thread_id)
            if not item:
                logger.debug("[LLM AI Runner] No EvaluationItem for thread %s", thread_id)
                return

            # Get item content from messages
            messages = Message.query.filter_by(item_id=thread_id).order_by(Message.timestamp).all()
            if not messages:
                # Fallback: try thread_id based messages
                messages = Message.query.filter_by(thread_id=thread_id).order_by(Message.timestamp).all()

            if not messages:
                logger.debug("[LLM AI Runner] No messages for item %s", thread_id)
                return

            # Get the main content (typically the generated text to rank)
            item_content = messages[0].content if messages else ""
            item_subject = item.subject or "Item"

            # Detect if this is a summary (from sender or subject)
            is_summary = any(
                kw in (item_subject.lower() + " " + (messages[0].sender or "").lower())
                for kw in ["summary", "zusammenfassung", "mistral", "magistral", "gpt", "claude", "llm"]
            )

            # Build evaluation prompt
            if is_summary:
                system_prompt = """Du bist ein Experte für die Bewertung von Textzusammenfassungen.

Bewertungskriterien:
- **Relevanz**: Erfasst die wichtigsten Informationen
- **Konsistenz**: Faktentreu, keine erfundenen Informationen
- **Kohärenz**: Logischer Aufbau, zusammenhängende Sätze
- **Flüssigkeit**: Gut lesbar, grammatikalisch korrekt

Antworte AUSSCHLIESSLICH im JSON-Format."""

                bucket_descriptions = {
                    "gut": "Erfasst Kerninhalt präzise, faktisch korrekt, gut lesbar",
                    "good": "Captures core content precisely, factually correct, readable",
                    "moderat": "Akzeptabel, aber mit Schwächen (fehlende Details, kleine Fehler)",
                    "moderate": "Acceptable but with weaknesses (missing details, minor errors)",
                    "schlecht": "Unvollständig, faktisch falsch, oder schlecht lesbar",
                    "poor": "Incomplete, factually incorrect, or poorly readable",
                }

                bucket_desc_lines = []
                for key in bucket_keys:
                    desc = bucket_descriptions.get(key.lower(), f"Bucket {key}")
                    bucket_desc_lines.append(f"- **{key}**: {desc}")

                user_prompt = f"""Bewerte die folgende Zusammenfassung:

TITEL: {item_subject}

INHALT:
{item_content[:3000]}{"..." if len(item_content) > 3000 else ""}

Ordne diese Zusammenfassung genau EINEM der folgenden Buckets zu:
{chr(10).join(bucket_desc_lines)}

Antworte im JSON-Format:
{{"bucket": "<bucket_name>", "reasoning": "<kurze Begründung>"}}"""
            else:
                # Generic item ranking
                system_prompt = (
                    "Du bist ein strenger Evaluator für Qualitäts-Rankings. "
                    "Antworte ausschließlich im JSON-Format."
                )
                user_prompt = f"""Bewerte den folgenden Text und ordne ihn einem Bucket zu.

TITEL: {item_subject}

INHALT:
{item_content[:3000]}{"..." if len(item_content) > 3000 else ""}

Erlaubte Buckets: {", ".join(bucket_keys)}

Antworte im JSON-Format:
{{"bucket": "<bucket_name>", "reasoning": "<kurze Begründung>"}}"""

            raw_response = None
            payload, raw_response = LLMAITaskRunner._request_json(
                client,
                model_id,
                system_prompt,
                user_prompt,
                max_tokens=500,
                trace={
                    "task": "ranking",
                    "scenario_id": scenario_id,
                    "thread_id": thread_id,
                    "model_id": model_id,
                },
            )

            # Validate and normalize bucket assignment
            assigned_bucket = payload.get("bucket", "").strip().lower()
            bucket_keys_lower = [k.lower() for k in bucket_keys]

            if assigned_bucket not in bucket_keys_lower:
                # Try to find closest match
                for key in bucket_keys:
                    if key.lower() in assigned_bucket or assigned_bucket in key.lower():
                        assigned_bucket = key.lower()
                        break
                else:
                    # Default to middle bucket if no match
                    assigned_bucket = bucket_keys_lower[len(bucket_keys) // 2] if bucket_keys else "moderat"

            # Find the original case bucket key
            final_bucket = bucket_keys[bucket_keys_lower.index(assigned_bucket)]

            # Store result - format compatible with ranking display
            result_payload = {
                "bucket": final_bucket,
                "reasoning": payload.get("reasoning", ""),
                "item_id": thread_id,
                # Store in bucket_map format for compatibility
                final_bucket: [thread_id],
            }

            if existing:
                existing.payload_json = result_payload
                existing.raw_response = raw_response
                existing.error = None
                db.session.add(existing)
            else:
                db.session.add(LLMTaskResult(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type="ranking",
                    payload_json=result_payload,
                    raw_response=raw_response,
                    error=None,
                ))
            db.session.commit()

            logger.info(
                "[LLM AI Runner] Ranked item %s into bucket '%s' (model: %s)",
                thread_id, final_bucket, model_id
            )

            # Broadcast success
            _broadcast_task_completed(
                scenario_id=scenario_id,
                model_id=model_id,
                thread_id=thread_id,
                task_type="ranking",
                result=result_payload,
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
            _broadcast_task_failed(
                scenario_id=scenario_id,
                model_id=model_id,
                thread_id=thread_id,
                task_type="ranking",
                error=str(exc),
            )
        except Exception as exc:
            db.session.rollback()
            logger.warning("[LLM AI Runner] Item ranking failed for %s: %s", thread_id, exc)
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
        scenario = RatingScenarios.query.get(scenario_id)

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

                # Try EvaluationItem model first (new model)
                eval_item = EvaluationItem.query.filter_by(item_id=thread_id).first()
                if eval_item:
                    # Use dimensional rating for EvaluationItem-based scenarios
                    messages = Message.query.filter_by(item_id=thread_id).order_by(Message.timestamp.asc()).all()
                    if not messages:
                        logger.info("[LLM AI Runner] No messages for item %s, skipping", thread_id)
                        continue

                    message_lines = [
                        f"{msg.sender}: {msg.content}"
                        for msg in messages
                    ]

                    # Get dimensional rating config from scenario
                    config = scenario.config_json or {} if scenario else {}
                    dimensions = config.get('dimensions', [
                        {'id': 'coherence', 'name': {'de': 'Kohärenz', 'en': 'Coherence'}},
                        {'id': 'fluency', 'name': {'de': 'Flüssigkeit', 'en': 'Fluency'}},
                        {'id': 'relevance', 'name': {'de': 'Relevanz', 'en': 'Relevance'}},
                        {'id': 'consistency', 'name': {'de': 'Konsistenz', 'en': 'Consistency'}}
                    ])
                    scale_min = config.get('min', 1)
                    scale_max = config.get('max', 5)

                    dimension_names = [d.get('name', {}).get('en', d.get('id', 'unknown')) for d in dimensions]
                    dim_list_str = ", ".join(dimension_names)

                    system_prompt = (
                        f"You are evaluating text quality on multiple dimensions: {dim_list_str}. "
                        f"Rate each dimension on a scale from {scale_min} (very poor) to {scale_max} (excellent). "
                        "Respond only in JSON format."
                    )
                    user_prompt = (
                        "Rate the following text on each dimension.\n"
                        "Return JSON in this format:\n"
                        "{\n"
                        '  "dimensional_ratings": [\n'
                        + ",\n".join([f'    {{"dimension": "{d.get("id", "unknown")}", "rating": <{scale_min}-{scale_max}>}}' for d in dimensions])
                        + "\n  ],\n"
                        '  "overall_rating": <weighted average>,\n'
                        '  "justification": "<brief explanation>"\n'
                        "}\n\n"
                        f"Subject: {eval_item.subject or 'N/A'}\n\n"
                        "Content:\n"
                        + "\n".join(message_lines)
                    )

                    raw_response = None
                    payload, raw_response = LLMAITaskRunner._request_json(
                        client,
                        model_id,
                        system_prompt,
                        user_prompt,
                        max_tokens=1500,
                        trace={
                            "task": "rating",
                            "scenario_id": scenario_id,
                            "thread_id": thread_id,
                            "model_id": model_id,
                            "type": "dimensional",
                        },
                    )

                    # Validate dimensional ratings
                    dim_ratings = payload.get("dimensional_ratings", [])
                    if not dim_ratings:
                        raise ValueError("No dimensional_ratings in response")

                    payload_out = {
                        "type": "dimensional",
                        "dimensional_ratings": dim_ratings,
                        "overall_rating": payload.get("overall_rating"),
                        "justification": payload.get("justification", ""),
                    }

                else:
                    # Fall back to legacy EmailThread/Feature model
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
        """Rate entire email conversations using configured dimensions."""
        client = LLMClientFactory.get_client_for_model(model_id)

        # Load scenario config to get dimensions
        scenario = RatingScenarios.query.get(scenario_id)
        config = scenario.config_json if scenario else {}
        if isinstance(config, str):
            import json
            try:
                config = json.loads(config)
            except (json.JSONDecodeError, TypeError):
                config = {}

        # Get dimensions from config (check multiple locations)
        eval_config = config.get("eval_config", {}) or {}
        eval_config_inner = eval_config.get("config", {}) or {}
        dimensions = config.get("dimensions", []) or eval_config.get("dimensions", []) or eval_config_inner.get("dimensions", [])

        # Get global scale settings
        global_min = config.get("min", eval_config.get("min", eval_config_inner.get("min", 1)))
        global_max = config.get("max", eval_config.get("max", eval_config_inner.get("max", 5)))

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

                # Build dimension descriptions for prompt
                if dimensions:
                    dim_descriptions = []
                    for dim in dimensions:
                        dim_id = dim.get("id", "unknown")
                        dim_name = dim.get("name", {})
                        name = dim_name.get("de", dim_name.get("en", dim_id)) if isinstance(dim_name, dict) else str(dim_name)
                        dim_desc = dim.get("description", {})
                        desc = dim_desc.get("de", dim_desc.get("en", "")) if isinstance(dim_desc, dict) else str(dim_desc)
                        # Get dimension-specific scale or use global
                        dim_scale = dim.get("scale", {})
                        scale_min = dim_scale.get("min", global_min) if dim_scale else global_min
                        scale_max = dim_scale.get("max", global_max) if dim_scale else global_max
                        dim_descriptions.append(f'- "{dim_id}" ({name}, Skala {scale_min}-{scale_max}): {desc}')

                    dimensions_text = "\n".join(dim_descriptions)
                    dim_ids = [d.get("id") for d in dimensions]

                    system_prompt = (
                        "Du bist ein Experte für die Bewertung von E-Mail-Beratungsverläufen. "
                        "Bewerte die Konversation auf mehreren Dimensionen. "
                        "Antworte ausschließlich im JSON-Format."
                    )
                    user_prompt = (
                        "Bewerte die folgende E-Mail-Konversation auf diesen Dimensionen:\n"
                        f"{dimensions_text}\n\n"
                        "Gib JSON im Format:\n"
                        "{\n"
                        '  "type": "dimensional",\n'
                        '  "dimensional_ratings": [\n'
                        + ",\n".join([f'    {{"dimension": "{d}", "rating": <Wert>, "reasoning": "<Begründung>"}}' for d in dim_ids])
                        + "\n  ],\n"
                        '  "overall_rating": <Durchschnitt aller Dimensionen>,\n'
                        '  "overall_reasoning": "<Gesamtbegründung>"\n'
                        "}\n\n"
                        f"Betreff: {thread.subject or 'Kein Betreff'}\n\n"
                        "Konversation:\n"
                        + "\n".join(message_lines)
                    )
                else:
                    # Fallback to simple rating if no dimensions configured
                    system_prompt = (
                        "Du bist ein Experte für die Bewertung von E-Mail-Konversationen. "
                        f"Bewerte die Gesamtqualität der Beratungskonversation auf einer Skala von {global_min} bis {global_max}. "
                        "Antworte ausschließlich im JSON-Format."
                    )
                    user_prompt = (
                        "Bewerte die folgende E-Mail-Konversation.\n"
                        "Gib JSON im Format:\n"
                        "{\n"
                        f'  "rating": {global_min}-{global_max},\n'
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
                    max_tokens=1500,  # More tokens for dimensional response
                    trace={
                        "task": "mail_rating",
                        "scenario_id": scenario_id,
                        "thread_id": thread_id,
                        "model_id": model_id,
                    },
                )
                rating_data = LLMAITaskRunner._validate_mail_rating_payload(payload, dimensions=dimensions)
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
        scenario: RatingScenarios,
        task_type: str = "text_classification",
    ) -> None:
        """Classify texts into custom labels defined in scenario config."""
        client = LLMClientFactory.get_client_for_model(model_id)

        # Get custom labels from scenario config
        config = scenario.config_json
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except (json.JSONDecodeError, TypeError):
                config = {}
        if not isinstance(config, dict):
            config = {}

        custom_labels = []
        label_descriptions = {}

        if isinstance(config.get("classification_labels"), list):
            custom_labels = [label for label in config.get("classification_labels", []) if isinstance(label, str)]
            if isinstance(config.get("label_descriptions"), dict):
                label_descriptions = {
                    key: value
                    for key, value in config.get("label_descriptions", {}).items()
                    if isinstance(key, str) and isinstance(value, str)
                }
        elif isinstance(config.get("labels"), list):
            custom_labels = [label for label in config.get("labels", []) if isinstance(label, str)]
        else:
            categories = []
            if isinstance(config.get("categories"), list):
                categories = config.get("categories", [])
            else:
                eval_config = config.get("eval_config")
                if isinstance(eval_config, dict):
                    eval_config_inner = eval_config.get("config")
                    if isinstance(eval_config_inner, dict) and isinstance(eval_config_inner.get("categories"), list):
                        categories = eval_config_inner.get("categories", [])
                    elif isinstance(eval_config.get("categories"), list):
                        categories = eval_config.get("categories", [])

            for category in categories:
                label = None
                description = None

                if isinstance(category, str):
                    label = category
                elif isinstance(category, dict):
                    label = category.get("id")
                    name = category.get("name")
                    if not label:
                        if isinstance(name, dict):
                            label = name.get("de") or name.get("en")
                        elif isinstance(name, str):
                            label = name

                    desc = category.get("description")
                    if isinstance(desc, dict):
                        description = desc.get("de") or desc.get("en")
                    elif isinstance(desc, str):
                        description = desc

                if label:
                    custom_labels.append(str(label))
                    if description:
                        label_descriptions[str(label)] = str(description)

        if not custom_labels:
            custom_labels = ["positive", "negative", "neutral"]

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
                    task_type=task_type,
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
                        "task": task_type,
                        "scenario_id": scenario_id,
                        "thread_id": thread_id,
                        "model_id": model_id,
                    },
                )
                classification_data = LLMAITaskRunner._validate_classification_payload(payload, custom_labels)
                if classification_data is None:
                    raise ValueError(f"Invalid {task_type} payload")

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
                        task_type=task_type,
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
                    task_type=task_type,
                    result=classification_data,
                )

            except LLMResponseError as exc:
                db.session.rollback()
                LLMAITaskRunner._store_error(
                    scenario_id=scenario_id,
                    thread_id=thread_id,
                    model_id=model_id,
                    task_type=task_type,
                    error=str(exc),
                    raw_response=exc.raw_response,
                )
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type=task_type,
                    error=str(exc),
                )
            except Exception as exc:
                db.session.rollback()
                logger.warning("[LLM AI Runner] %s failed for thread %s: %s", task_type, thread_id, exc)
                # Broadcast failure
                _broadcast_task_failed(
                    scenario_id=scenario_id,
                    model_id=model_id,
                    thread_id=thread_id,
                    task_type=task_type,
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
    def _validate_bucket_payload(
        payload: Dict[str, Any],
        features: List[Feature],
        bucket_keys: Optional[List[str]] = None
    ) -> Optional[Dict[str, List[int]]]:
        """
        Validate bucket payload from LLM response.

        Args:
            payload: The parsed JSON response from LLM
            features: List of features that should be assigned to buckets
            bucket_keys: List of valid bucket names (lowercase). If None, uses defaults.

        Returns:
            Dictionary mapping bucket names to feature IDs, or None if invalid
        """
        if not isinstance(payload, dict):
            return None

        # Use provided bucket keys or fall back to defaults
        valid_keys = bucket_keys if bucket_keys else ["gut", "mittel", "schlecht", "neutral"]

        expected_ids = {f.feature_id for f in features}
        buckets = {}

        for key in valid_keys:
            ids = payload.get(key, [])
            if not isinstance(ids, list):
                return None
            clean_ids = []
            for item in ids:
                if isinstance(item, int):
                    clean_ids.append(item)
                elif isinstance(item, str) and item.strip().isdigit():
                    clean_ids.append(int(item.strip()))
                # Skip invalid items instead of failing completely
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
    def _validate_mail_rating_payload(
        payload: Dict[str, Any],
        dimensions: List[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Validate mail_rating response: supports both simple and dimensional formats."""
        if not isinstance(payload, dict):
            return None

        # Check for dimensional format
        if payload.get("type") == "dimensional" and "dimensional_ratings" in payload:
            dim_ratings = payload.get("dimensional_ratings", [])
            if not isinstance(dim_ratings, list):
                return None

            validated_ratings = []
            for dr in dim_ratings:
                if not isinstance(dr, dict):
                    continue
                dim_id = dr.get("dimension")
                rating = dr.get("rating")
                reasoning = dr.get("reasoning", "")

                # Handle string ratings
                if isinstance(rating, str):
                    try:
                        rating = float(rating.strip())
                        if rating == int(rating):
                            rating = int(rating)
                    except (ValueError, AttributeError):
                        continue

                if dim_id and rating is not None:
                    validated_ratings.append({
                        "dimension": dim_id,
                        "rating": rating,
                        "reasoning": str(reasoning) if reasoning else ""
                    })

            if not validated_ratings:
                return None

            # Get overall rating
            overall_rating = payload.get("overall_rating")
            if isinstance(overall_rating, str):
                try:
                    overall_rating = float(overall_rating.strip())
                    if overall_rating == int(overall_rating):
                        overall_rating = int(overall_rating)
                except (ValueError, AttributeError):
                    # Calculate average if not provided
                    overall_rating = sum(r["rating"] for r in validated_ratings) / len(validated_ratings)
                    overall_rating = round(overall_rating, 2)

            if overall_rating is None:
                # Calculate average
                overall_rating = sum(r["rating"] for r in validated_ratings) / len(validated_ratings)
                overall_rating = round(overall_rating, 2)

            return {
                "type": "dimensional",
                "dimensional_ratings": validated_ratings,
                "overall_rating": overall_rating,
                "overall_reasoning": str(payload.get("overall_reasoning", "")) or ""
            }

        # Fallback: Simple format {"rating": X, "reasoning": "..."}
        rating = payload.get("rating")
        reasoning = payload.get("reasoning", "")

        # Handle string ratings
        if isinstance(rating, str) and rating.strip().replace(".", "").isdigit():
            rating = float(rating.strip())
            if rating == int(rating):
                rating = int(rating)

        # Validate rating exists and is numeric
        if rating is None or not isinstance(rating, (int, float)):
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
        """Validate labeling/classification response with custom labels."""
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
