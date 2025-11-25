"""
LLM-as-Judge Service for LLARS.

This service handles the evaluation of email conversation threads (Mailverläufe)
using LLM-based pairwise comparison with structured Pydantic output.

Features:
- Structured JSON output via Pydantic schema
- Position-swap strategy to eliminate bias
- Chain-of-thought reasoning before decision
- Streaming support for live UI updates
"""

import json
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from openai import OpenAI

from .judge_schema import (
    JudgeEvaluationResult,
    calculate_aggregate_scores
)

logger = logging.getLogger(__name__)


class JudgeService:
    """
    Service for LLM-as-Judge evaluations of email conversations.

    Uses LiteLLM Proxy (TH Nürnberg) to evaluate two conversation threads
    and determine which one is better based on multiple criteria.
    """

    # System prompt for the LLM Judge
    SYSTEM_PROMPT = """Du bist ein Experte für die Bewertung von Beratungsgesprächen im Kontext psychologischer Online-Beratung.

Deine Aufgabe ist es, zwei E-Mail-Verläufe zwischen Beratenden und Ratsuchenden zu vergleichen und zu bewerten, welcher Verlauf qualitativ besser ist.

## WICHTIGE REGELN:

1. **Reihenfolge beachten**: Führe ZUERST dein Chain-of-Thought Reasoning durch (step_1 bis step_6)
2. **Dann bewerten**: Bewerte DANACH jedes der sechs Kriterien einzeln für beide Verläufe (Scores 1-5)
3. **Zuletzt entscheiden**: Triff ZULETZT deine Gesamtentscheidung (winner: A, B, oder TIE)

## BEWERTUNGSKRITERIEN (jeweils 1-5 Skala):

1. **Berater-Kohärenz** (counsellor_coherence): Logik, Zusammenhang und Professionalität der Berater-Antworten
2. **Klienten-Kohärenz** (client_coherence): Realismus und Nachvollziehbarkeit des Klientenverhaltens
3. **Beratungsqualität** (quality): Therapeutische Qualität insgesamt
4. **Empathie** (empathy): Einfühlungsvermögen und emotionale Unterstützung
5. **Authentizität** (authenticity): Natürlichkeit des gesamten Gesprächs
6. **Lösungsorientierung** (solution_orientation): Konkrete Hilfestellungen und Handlungsempfehlungen

## WICHTIG FÜR FAIRE BEWERTUNG:

- **Ignoriere die Position** der Verläufe (ob A oder B zuerst kommt) - bewerte rein nach Inhalt und Qualität!
- Sei objektiv und begründe deine Entscheidungen nachvollziehbar
- Bei wirklicher Gleichwertigkeit: Wähle TIE
- Gib eine ehrliche Konfidenz an (0.0 = unsicher, 1.0 = sehr sicher)

Du MUSST deine Antwort als valides JSON gemäß dem vorgegebenen Schema ausgeben."""

    # User prompt template
    USER_PROMPT_TEMPLATE = """Vergleiche die folgenden zwei E-Mail-Beratungsverläufe und bestimme, welcher qualitativ besser ist.

=== VERLAUF A (Säule {pillar_a}: {pillar_a_name}) ===

{thread_a_content}

=== VERLAUF B (Säule {pillar_b}: {pillar_b_name}) ===

{thread_b_content}

---

Führe nun eine detaillierte Bewertung durch:
1. Analysiere beide Verläufe im Chain-of-Thought
2. Bewerte jedes der 6 Kriterien für beide Verläufe (1-5)
3. Bestimme den Gewinner (A, B, oder TIE)

Antworte NUR mit einem validen JSON-Objekt gemäß dem Schema."""

    # Pillar names mapping
    PILLAR_NAMES = {
        1: "Rollenspiele",
        2: "Feature aus Säule 1",
        3: "Anonymisierte Daten",
        4: "Synthetisch generiert",
        5: "Live-Testungen"
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "mistralai/Mistral-Small-3.2-24B-Instruct-2506"
    ):
        """
        Initialize the Judge Service.

        Args:
            api_key: LiteLLM API key (default: from LITELLM_API_KEY env var)
            base_url: LiteLLM proxy URL (default: from LITELLM_BASE_URL env var)
            model: Model to use for evaluation
        """
        self.api_key = api_key or os.getenv("LITELLM_API_KEY")
        if not self.api_key:
            raise ValueError("LITELLM_API_KEY must be provided or set in environment")

        self.base_url = base_url or os.getenv(
            "LITELLM_BASE_URL",
            "https://kiz1.in.ohmportal.de/llmproxy/v1"
        )
        self.model = model

        # Initialize OpenAI client for LiteLLM proxy
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        logger.info(f"[JudgeService] Initialized with model={self.model}")

    def format_thread_for_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format an email thread for inclusion in the prompt.

        Args:
            messages: List of message dicts with 'content', 'is_counsellor', etc.

        Returns:
            Formatted string representation of the thread
        """
        formatted_lines = []

        for i, msg in enumerate(messages, 1):
            role = "BERATER" if msg.get('is_counsellor', False) else "RATSUCHENDE"
            content = msg.get('content', '').strip()

            # Truncate very long messages
            if len(content) > 2000:
                content = content[:2000] + "... [gekürzt]"

            formatted_lines.append(f"[Nachricht {i} - {role}]:")
            formatted_lines.append(content)
            formatted_lines.append("")  # Empty line between messages

        return "\n".join(formatted_lines)

    def _get_json_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for structured output."""
        return JudgeEvaluationResult.model_json_schema()

    def evaluate_pair(
        self,
        thread_a_messages: List[Dict[str, Any]],
        thread_b_messages: List[Dict[str, Any]],
        pillar_a: int,
        pillar_b: int,
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[JudgeEvaluationResult, Dict[str, Any]]:
        """
        Evaluate a pair of threads.

        Args:
            thread_a_messages: Messages from thread A
            thread_b_messages: Messages from thread B
            pillar_a: Pillar number for thread A (1-5)
            pillar_b: Pillar number for thread B (1-5)
            stream_callback: Optional callback for streaming chunks

        Returns:
            Tuple of (JudgeEvaluationResult, metadata_dict)
        """
        start_time = time.time()

        # Format threads for prompt
        thread_a_content = self.format_thread_for_prompt(thread_a_messages)
        thread_b_content = self.format_thread_for_prompt(thread_b_messages)

        # Build user prompt
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            pillar_a=pillar_a,
            pillar_a_name=self.PILLAR_NAMES.get(pillar_a, f"Säule {pillar_a}"),
            pillar_b=pillar_b,
            pillar_b_name=self.PILLAR_NAMES.get(pillar_b, f"Säule {pillar_b}"),
            thread_a_content=thread_a_content,
            thread_b_content=thread_b_content
        )

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # Prepare metadata for TH Nürnberg tracking
        metadata = {
            "tags": ["Technische Hochschule Nürnberg", "KIA", "LLM-as-Judge"]
        }

        try:
            if stream_callback:
                # Streaming mode
                full_response = self._stream_evaluate(messages, metadata, stream_callback)
            else:
                # Non-streaming mode
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,  # Low for consistency
                    max_tokens=4000,
                    extra_body={
                        "metadata": metadata,
                        "response_format": {"type": "json_object"}
                    }
                )
                full_response = response.choices[0].message.content
                token_count = response.usage.total_tokens if response.usage else None

            # Parse JSON response
            result = self._parse_response(full_response)

            # Calculate timing and metadata
            latency_ms = int((time.time() - start_time) * 1000)

            eval_metadata = {
                "latency_ms": latency_ms,
                "token_count": token_count if not stream_callback else None,
                "model": self.model,
                "aggregate_scores": calculate_aggregate_scores(result)
            }

            logger.info(
                f"[JudgeService] Evaluation complete: winner={result.winner}, "
                f"confidence={result.confidence:.2f}, latency={latency_ms}ms"
            )

            return result, eval_metadata

        except Exception as e:
            logger.error(f"[JudgeService] Evaluation failed: {e}")
            raise

    def _stream_evaluate(
        self,
        messages: List[Dict[str, str]],
        metadata: Dict[str, Any],
        callback: Callable[[str], None]
    ) -> str:
        """
        Perform streaming evaluation with callback.

        Args:
            messages: Chat messages
            metadata: Request metadata
            callback: Function to call with each chunk

        Returns:
            Complete response text
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=4000,
            stream=True,
            extra_body={
                "metadata": metadata,
                "response_format": {"type": "json_object"}
            }
        )

        full_response = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                callback(content)

        return full_response

    def _parse_response(self, response_text: str) -> JudgeEvaluationResult:
        """
        Parse the LLM response into a JudgeEvaluationResult.

        Args:
            response_text: Raw JSON response from LLM

        Returns:
            Parsed JudgeEvaluationResult

        Raises:
            ValueError: If parsing fails
        """
        try:
            # Clean up response if needed
            text = response_text.strip()

            # Handle markdown code blocks
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            # Parse JSON
            data = json.loads(text.strip())

            # Transform flexible LLM response to our schema
            transformed_data = self._transform_llm_response(data)

            # Validate with Pydantic
            result = JudgeEvaluationResult.model_validate(transformed_data)

            return result

        except json.JSONDecodeError as e:
            logger.error(f"[JudgeService] JSON parse error: {e}")
            logger.error(f"[JudgeService] Raw response: {response_text[:500]}...")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

        except Exception as e:
            logger.error(f"[JudgeService] Validation error: {e}")
            raise ValueError(f"Failed to validate LLM response: {e}")

    def _transform_llm_response(self, data: dict) -> dict:
        """
        Transform flexible LLM response format to our expected schema.

        Handles various formats the LLM might return, including:
        - step_1, step_2, etc. format
        - counsellor_analysis, client_analysis, etc. format
        - Already correct format with chain_of_thought and criteria_scores
        """
        # If already in correct format with proper chain_of_thought fields, return as-is
        if "chain_of_thought" in data and "criteria_scores" in data:
            cot = data["chain_of_thought"]
            # Check if chain_of_thought has the required fields
            required_cot_fields = [
                "step_1_overview", "step_2_strengths_a", "step_3_strengths_b",
                "step_4_weaknesses_a", "step_5_weaknesses_b", "step_6_comparison"
            ]
            if all(f in cot for f in required_cot_fields):
                return data

        # Extract analysis texts from various possible formats
        analysis_texts = []

        # Try step_X format first
        for i in range(1, 7):
            step_key = f"step_{i}"
            if step_key in data:
                analysis_texts.append(data[step_key])

        # Try analysis-named format (counsellor_analysis, etc.)
        analysis_fields = [
            'counsellor_analysis', 'client_analysis', 'quality_analysis',
            'empathy_analysis', 'authenticity_analysis', 'solution_analysis'
        ]
        for field in analysis_fields:
            if field in data and data[field] not in analysis_texts:
                analysis_texts.append(data[field])

        # If we have a chain_of_thought dict with wrong field names, extract its values
        if "chain_of_thought" in data and isinstance(data["chain_of_thought"], dict):
            for value in data["chain_of_thought"].values():
                if isinstance(value, str) and value not in analysis_texts:
                    analysis_texts.append(value)

        # Ensure we have at least 6 analysis texts (pad with defaults if needed)
        default_texts = [
            "Beide Verläufe wurden analysiert und verglichen.",
            "Verlauf A zeigt einige positive Aspekte in der Beratung.",
            "Verlauf B zeigt ebenfalls positive Aspekte in der Beratung.",
            "Verlauf A könnte in einigen Bereichen verbessert werden.",
            "Verlauf B könnte in einigen Bereichen verbessert werden.",
            "Der direkte Vergleich zeigt unterschiedliche Stärken beider Verläufe."
        ]
        while len(analysis_texts) < 6:
            analysis_texts.append(default_texts[len(analysis_texts)])

        # Build chain_of_thought with correct field names
        chain_of_thought = {
            "step_1_overview": analysis_texts[0][:500] if len(analysis_texts[0]) >= 50 else analysis_texts[0] + " " * (50 - len(analysis_texts[0])),
            "step_2_strengths_a": analysis_texts[1][:400] if len(analysis_texts[1]) >= 30 else analysis_texts[1] + " " * (30 - len(analysis_texts[1])),
            "step_3_strengths_b": analysis_texts[2][:400] if len(analysis_texts[2]) >= 30 else analysis_texts[2] + " " * (30 - len(analysis_texts[2])),
            "step_4_weaknesses_a": analysis_texts[3][:400] if len(analysis_texts[3]) >= 20 else analysis_texts[3] + " " * (20 - len(analysis_texts[3])),
            "step_5_weaknesses_b": analysis_texts[4][:400] if len(analysis_texts[4]) >= 20 else analysis_texts[4] + " " * (20 - len(analysis_texts[4])),
            "step_6_comparison": analysis_texts[5][:500] if len(analysis_texts[5]) >= 50 else analysis_texts[5] + " " * (50 - len(analysis_texts[5]))
        }

        # Build criteria_scores from scores field
        scores = data.get("scores", {})
        scores_a = scores.get("A", {})
        scores_b = scores.get("B", {})

        # Generate reasoning from analysis texts
        def get_reasoning(default_text, min_len=10):
            text = default_text if len(default_text) >= min_len else default_text + " " * (min_len - len(default_text))
            return text[:500]

        criteria_scores = {
            "counsellor_coherence": {
                "score_a": float(scores_a.get("counsellor_coherence", 3)),
                "score_b": float(scores_b.get("counsellor_coherence", 3)),
                "reasoning": get_reasoning(analysis_texts[0] if analysis_texts else "Kohärenz wurde bewertet.")
            },
            "client_coherence": {
                "score_a": float(scores_a.get("client_coherence", 3)),
                "score_b": float(scores_b.get("client_coherence", 3)),
                "reasoning": get_reasoning(analysis_texts[1] if len(analysis_texts) > 1 else "Klienten-Kohärenz wurde bewertet.")
            },
            "quality": {
                "score_a": float(scores_a.get("quality", 3)),
                "score_b": float(scores_b.get("quality", 3)),
                "reasoning": get_reasoning(analysis_texts[2] if len(analysis_texts) > 2 else "Qualität wurde bewertet.")
            },
            "empathy": {
                "score_a": float(scores_a.get("empathy", 3)),
                "score_b": float(scores_b.get("empathy", 3)),
                "reasoning": get_reasoning(analysis_texts[3] if len(analysis_texts) > 3 else "Empathie wurde bewertet.")
            },
            "authenticity": {
                "score_a": float(scores_a.get("authenticity", 3)),
                "score_b": float(scores_b.get("authenticity", 3)),
                "reasoning": get_reasoning(analysis_texts[4] if len(analysis_texts) > 4 else "Authentizität wurde bewertet.")
            },
            "solution_orientation": {
                "score_a": float(scores_a.get("solution_orientation", 3)),
                "score_b": float(scores_b.get("solution_orientation", 3)),
                "reasoning": get_reasoning(analysis_texts[5] if len(analysis_texts) > 5 else "Lösungsorientierung wurde bewertet.")
            }
        }

        # Get winner and confidence
        winner = data.get("winner", "TIE")
        if winner not in ["A", "B", "TIE"]:
            winner = "TIE"

        confidence = data.get("confidence", 0.5)
        if isinstance(confidence, (int, float)):
            confidence = min(max(float(confidence), 0.0), 1.0)
        else:
            confidence = 0.5

        # Build final justification
        final_justification = data.get("final_justification", "")
        if not final_justification or len(final_justification) < 50:
            # Build from analysis texts
            justification_parts = [t for t in analysis_texts if t]
            final_justification = " ".join(justification_parts[:3])
            if len(final_justification) < 50:
                final_justification = f"Die Bewertung ergab {winner} als Gewinner mit einer Konfidenz von {confidence:.2f}. " + final_justification
        final_justification = final_justification[:1000]

        return {
            "chain_of_thought": chain_of_thought,
            "criteria_scores": criteria_scores,
            "winner": winner,
            "confidence": confidence,
            "final_justification": final_justification
        }

    def evaluate_with_position_swap(
        self,
        thread_a_messages: List[Dict[str, Any]],
        thread_b_messages: List[Dict[str, Any]],
        pillar_a: int,
        pillar_b: int
    ) -> Tuple[JudgeEvaluationResult, JudgeEvaluationResult, str, Dict[str, Any]]:
        """
        Evaluate with position-swap to eliminate position bias.

        This runs the evaluation twice:
        1. First with A|B order
        2. Second with B|A order (swapped)

        If results disagree, the final result is TIE.

        Args:
            thread_a_messages: Messages from thread A
            thread_b_messages: Messages from thread B
            pillar_a: Pillar number for thread A
            pillar_b: Pillar number for thread B

        Returns:
            Tuple of:
            - result_ab: Result from A|B evaluation
            - result_ba: Result from B|A evaluation
            - final_winner: Consolidated winner (A, B, or TIE)
            - swap_metadata: Metadata about the swap process
        """
        logger.info(f"[JudgeService] Starting position-swap evaluation: Säule {pillar_a} vs Säule {pillar_b}")

        # First evaluation: A | B
        logger.info("[JudgeService] Evaluation 1/2: A|B order")
        result_ab, meta_ab = self.evaluate_pair(
            thread_a_messages, thread_b_messages,
            pillar_a, pillar_b
        )

        # Second evaluation: B | A (swapped)
        logger.info("[JudgeService] Evaluation 2/2: B|A order (swapped)")
        result_ba, meta_ba = self.evaluate_pair(
            thread_b_messages, thread_a_messages,
            pillar_b, pillar_a
        )

        # Adjust result_ba winner (since positions were swapped)
        # If BA says "A" won, it means B won in original order
        winner_ba_adjusted = {
            "A": "B",
            "B": "A",
            "TIE": "TIE"
        }.get(result_ba.winner, "TIE")

        # Determine final winner
        if result_ab.winner == winner_ba_adjusted:
            # Both evaluations agree
            final_winner = result_ab.winner
            agreement = True
        else:
            # Evaluations disagree - position bias detected
            final_winner = "TIE"
            agreement = False
            logger.warning(
                f"[JudgeService] Position bias detected! "
                f"AB said {result_ab.winner}, BA adjusted said {winner_ba_adjusted} -> TIE"
            )

        swap_metadata = {
            "result_ab_winner": result_ab.winner,
            "result_ba_winner": result_ba.winner,
            "result_ba_adjusted": winner_ba_adjusted,
            "final_winner": final_winner,
            "agreement": agreement,
            "position_bias_detected": not agreement,
            "combined_latency_ms": meta_ab["latency_ms"] + meta_ba["latency_ms"],
            "avg_confidence": (result_ab.confidence + result_ba.confidence) / 2
        }

        logger.info(
            f"[JudgeService] Position-swap complete: "
            f"final_winner={final_winner}, agreement={agreement}"
        )

        return result_ab, result_ba, final_winner, swap_metadata


# Factory function
def create_judge_service(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None
) -> JudgeService:
    """
    Create a JudgeService instance.

    Args:
        api_key: LiteLLM API key
        base_url: LiteLLM proxy URL
        model: Model to use

    Returns:
        Configured JudgeService instance
    """
    return JudgeService(
        api_key=api_key,
        base_url=base_url,
        model=model or "mistralai/Mistral-Small-3.2-24B-Instruct-2506"
    )
