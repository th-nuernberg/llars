"""
Pydantic Schema for LLM-as-Judge Evaluation Results.

This module defines the structured output format that the LLM must produce
when evaluating two email conversation threads (Mailverläufe).

Based on LLARS existing metrics:
- counsellor_coherence_rating (1-5)
- client_coherence_rating (1-5)
- quality_rating (1-5)
- overall_rating (binary -> translated to authenticity)

Extended with:
- empathy
- solution_orientation
"""

from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


class WinnerChoice(str, Enum):
    """Possible winner outcomes"""
    A = "A"
    B = "B"
    TIE = "TIE"


class MetricScore(BaseModel):
    """Score comparison for a single metric between two threads."""

    score_a: float = Field(
        ge=1.0, le=5.0,
        description="Score für Verlauf A (1=sehr schlecht, 5=sehr gut)"
    )
    score_b: float = Field(
        ge=1.0, le=5.0,
        description="Score für Verlauf B (1=sehr schlecht, 5=sehr gut)"
    )
    reasoning: str = Field(
        min_length=10,
        max_length=500,
        description="Kurze Begründung für die vergebenen Scores (10-500 Zeichen)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "score_a": 4.0,
                "score_b": 3.5,
                "reasoning": "Verlauf A zeigt mehr Einfühlungsvermögen durch aktives Zuhören."
            }
        }


class EvaluationCriteria(BaseModel):
    """
    Detailed evaluation criteria based on LLARS metrics.

    Each criterion compares Thread A vs Thread B with scores 1-5.
    """

    counsellor_coherence: MetricScore = Field(
        description=(
            "Kohärenz der beratenden Person: "
            "Wie logisch, zusammenhängend und professionell sind die Antworten des Beraters? "
            "Bewertet wird: Klarheit der Kommunikation, logischer Aufbau, Konsistenz."
        )
    )

    client_coherence: MetricScore = Field(
        description=(
            "Kohärenz der ratsuchenden Person: "
            "Wie realistisch, nachvollziehbar und natürlich verhält sich der Klient? "
            "Bewertet wird: Realismus des Verhaltens, emotionale Konsistenz, Reaktionen."
        )
    )

    quality: MetricScore = Field(
        description=(
            "Beratungsqualität insgesamt: "
            "Wie gut ist die therapeutische/beratende Qualität des Gesprächs? "
            "Bewertet wird: Professionalität, Hilfsamkeit, Zielorientierung."
        )
    )

    empathy: MetricScore = Field(
        description=(
            "Empathie und emotionale Unterstützung: "
            "Wie einfühlsam und verständnisvoll reagiert der Berater? "
            "Bewertet wird: Aktives Zuhören, Validierung von Gefühlen, Wärme."
        )
    )

    authenticity: MetricScore = Field(
        description=(
            "Authentizität und Natürlichkeit: "
            "Wie authentisch und natürlich wirkt der gesamte Gesprächsverlauf? "
            "Bewertet wird: Sprachliche Natürlichkeit, realistische Interaktion."
        )
    )

    solution_orientation: MetricScore = Field(
        description=(
            "Lösungsorientierung und Handlungsempfehlungen: "
            "Wie gut werden konkrete Lösungsansätze und Hilfestellungen angeboten? "
            "Bewertet wird: Praktische Tipps, Ressourcen, nächste Schritte."
        )
    )


class ChainOfThought(BaseModel):
    """
    Structured Chain-of-Thought reasoning BEFORE the final decision.

    This ensures the LLM thinks through the comparison systematically
    before arriving at a conclusion.
    """

    step_1_overview: str = Field(
        min_length=50,
        max_length=500,
        description=(
            "Schritt 1: Kurze Zusammenfassung beider Verläufe. "
            "Was sind die Hauptthemen? Welche Situation wird beraten?"
        )
    )

    step_2_strengths_a: str = Field(
        min_length=30,
        max_length=400,
        description=(
            "Schritt 2: Stärken von Verlauf A. "
            "Was macht Verlauf A besonders gut? Welche positiven Aspekte fallen auf?"
        )
    )

    step_3_strengths_b: str = Field(
        min_length=30,
        max_length=400,
        description=(
            "Schritt 3: Stärken von Verlauf B. "
            "Was macht Verlauf B besonders gut? Welche positiven Aspekte fallen auf?"
        )
    )

    step_4_weaknesses_a: str = Field(
        min_length=20,
        max_length=400,
        description=(
            "Schritt 4: Schwächen von Verlauf A. "
            "Wo hat Verlauf A Verbesserungspotential? Was könnte besser sein?"
        )
    )

    step_5_weaknesses_b: str = Field(
        min_length=20,
        max_length=400,
        description=(
            "Schritt 5: Schwächen von Verlauf B. "
            "Wo hat Verlauf B Verbesserungspotential? Was könnte besser sein?"
        )
    )

    step_6_comparison: str = Field(
        min_length=50,
        max_length=500,
        description=(
            "Schritt 6: Direkter Vergleich. "
            "Was sind die wichtigsten Unterschiede? Welcher Aspekt gibt den Ausschlag?"
        )
    )


class JudgeEvaluationResult(BaseModel):
    """
    Complete evaluation result from the LLM Judge.

    This is the main output schema that the LLM must produce.
    It includes:
    1. Chain-of-Thought reasoning (done FIRST)
    2. Detailed criteria scores
    3. Final winner decision
    4. Confidence and justification
    """

    chain_of_thought: ChainOfThought = Field(
        description=(
            "Schrittweises Reasoning VOR der Entscheidung. "
            "Führe diese Analyse ZUERST durch!"
        )
    )

    criteria_scores: EvaluationCriteria = Field(
        description=(
            "Detaillierte Bewertung nach allen sechs Kriterien. "
            "Jedes Kriterium wird für beide Verläufe bewertet."
        )
    )

    winner: Literal["A", "B", "TIE"] = Field(
        description=(
            "Welcher Verlauf ist insgesamt besser? "
            "'A' wenn Verlauf A besser ist, "
            "'B' wenn Verlauf B besser ist, "
            "'TIE' wenn beide gleichwertig sind."
        )
    )

    confidence: float = Field(
        ge=0.0, le=1.0,
        description=(
            "Wie sicher bist du bei dieser Entscheidung? "
            "0.0 = sehr unsicher, 1.0 = sehr sicher. "
            "Bei TIE sollte die Konfidenz höher sein wenn beide wirklich gleichwertig sind."
        )
    )

    final_justification: str = Field(
        min_length=50,
        max_length=1000,
        description=(
            "Abschließende Begründung für die Gesamtentscheidung. "
            "Warum wurde dieser Gewinner gewählt? Was war ausschlaggebend?"
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "chain_of_thought": {
                    "step_1_overview": "Beide Verläufe behandeln einen Jugendlichen mit Schulproblemen...",
                    "step_2_strengths_a": "Verlauf A zeigt aktives Zuhören und stellt gute Fragen...",
                    "step_3_strengths_b": "Verlauf B bietet konkrete Lösungsvorschläge...",
                    "step_4_weaknesses_a": "In Verlauf A fehlen konkrete Handlungsempfehlungen...",
                    "step_5_weaknesses_b": "Verlauf B geht zu schnell zu Lösungen über...",
                    "step_6_comparison": "Der Hauptunterschied liegt in der Balance zwischen Zuhören und Beraten..."
                },
                "criteria_scores": {
                    "counsellor_coherence": {"score_a": 4.5, "score_b": 4.0, "reasoning": "..."},
                    "client_coherence": {"score_a": 4.0, "score_b": 4.0, "reasoning": "..."},
                    "quality": {"score_a": 4.0, "score_b": 3.5, "reasoning": "..."},
                    "empathy": {"score_a": 4.5, "score_b": 3.5, "reasoning": "..."},
                    "authenticity": {"score_a": 4.0, "score_b": 4.0, "reasoning": "..."},
                    "solution_orientation": {"score_a": 3.5, "score_b": 4.5, "reasoning": "..."}
                },
                "winner": "A",
                "confidence": 0.75,
                "final_justification": "Verlauf A überzeugt durch bessere empathische Kommunikation..."
            }
        }


# Helper function to calculate aggregate scores
def calculate_aggregate_scores(result: JudgeEvaluationResult) -> dict:
    """
    Calculate aggregate scores from evaluation result.

    Returns:
        dict with total_a, total_b, avg_a, avg_b, winner_by_score
    """
    criteria = result.criteria_scores

    scores_a = [
        criteria.counsellor_coherence.score_a,
        criteria.client_coherence.score_a,
        criteria.quality.score_a,
        criteria.empathy.score_a,
        criteria.authenticity.score_a,
        criteria.solution_orientation.score_a
    ]

    scores_b = [
        criteria.counsellor_coherence.score_b,
        criteria.client_coherence.score_b,
        criteria.quality.score_b,
        criteria.empathy.score_b,
        criteria.authenticity.score_b,
        criteria.solution_orientation.score_b
    ]

    total_a = sum(scores_a)
    total_b = sum(scores_b)
    avg_a = total_a / len(scores_a)
    avg_b = total_b / len(scores_b)

    # Determine winner by score
    if abs(total_a - total_b) < 0.5:  # Within 0.5 points = tie
        winner_by_score = "TIE"
    elif total_a > total_b:
        winner_by_score = "A"
    else:
        winner_by_score = "B"

    return {
        "total_a": total_a,
        "total_b": total_b,
        "avg_a": avg_a,
        "avg_b": avg_b,
        "winner_by_score": winner_by_score,
        "score_difference": abs(total_a - total_b),
        "scores_match_winner": winner_by_score == result.winner
    }
