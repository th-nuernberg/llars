"""
AI Analyzer Service for LLM-assisted data analysis and transformation.

Uses LLM to analyze unknown data formats and generate transformation scripts.
"""

from typing import Any
import json
import logging

from llm.litellm_client import LiteLLMClient
from db.models.llm_model import LLMModel

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """
    AI-powered data analysis and transformation.

    Uses LLM to:
    - Analyze unknown data structures
    - Suggest field mappings
    - Generate Python transformation scripts
    """

    def __init__(self):
        """Initialize the AI analyzer."""
        self._client = LiteLLMClient()

    def _get_default_model(self) -> str:
        """Get the default LLM model ID."""
        model = LLMModel.get_default_model()
        if model:
            return model.model_id
        return "gpt-4o-mini"  # Fallback

    def analyze_structure(
        self,
        data: Any,
        filename: str | None = None,
        max_sample_items: int = 3
    ) -> dict[str, Any]:
        """
        Analyze data structure using LLM.

        Args:
            data: The data to analyze (parsed JSON/list/dict)
            filename: Original filename for context
            max_sample_items: Max items to include in sample

        Returns:
            Analysis result with detected format and mapping suggestions
        """
        # Prepare sample data
        if isinstance(data, list):
            sample = data[:max_sample_items]
        elif isinstance(data, dict) and "items" in data:
            sample = {
                "metadata": data.get("metadata", {}),
                "items": data["items"][:max_sample_items],
            }
        else:
            sample = data

        sample_json = json.dumps(sample, indent=2, ensure_ascii=False, default=str)

        # Truncate if too long
        if len(sample_json) > 4000:
            sample_json = sample_json[:4000] + "\n... (truncated)"

        prompt = f"""Analyze this data structure and determine the best way to import it into an LLM evaluation system.

Filename: {filename or 'unknown'}

Data sample:
```json
{sample_json}
```

Analyze and return a JSON object with:
1. "detected_format": The format type (one of: "openai", "lmsys", "csv", "custom")
2. "confidence": Your confidence score (0.0-1.0)
3. "field_mapping": Map detected fields to standard fields:
   - "id_field": Field containing unique identifier
   - "messages_field": Field containing conversation messages
   - "role_field": Field for message role (user/assistant)
   - "content_field": Field for message content
   - "subject_field": Field for conversation subject (optional)
4. "suggested_task_type": Best evaluation type ("rating", "ranking", "comparison", "mail_rating", "authenticity")
5. "reasoning": Brief explanation of your analysis
6. "warnings": List of any issues or concerns

Return ONLY valid JSON, no markdown formatting."""

        try:
            content = self._client.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            if not content:
                return {
                    "ai_analyzed": False,
                    "error": "No response from LLM",
                }

            # Try to extract JSON from response
            try:
                # Handle potential markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                result = json.loads(content.strip())
                result["ai_analyzed"] = True
                return result

            except json.JSONDecodeError:
                logger.warning(f"Could not parse AI response as JSON: {content[:200]}")
                return {
                    "ai_analyzed": False,
                    "error": "Could not parse AI response",
                    "raw_response": content[:500],
                }

        except Exception as e:
            logger.exception(f"AI analysis failed: {e}")
            return {
                "ai_analyzed": False,
                "error": str(e),
            }

    def generate_transform_script(
        self,
        data: Any,
        target_format: str = "llars",
        field_hints: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Generate a Python transformation script using LLM.

        Args:
            data: Sample data to transform
            target_format: Target format (default: llars)
            field_hints: Optional hints about field mappings

        Returns:
            Dictionary with generated script and metadata
        """
        # Prepare sample
        if isinstance(data, list):
            sample = data[:2]
        elif isinstance(data, dict) and "items" in data:
            sample = data["items"][:2]
        else:
            sample = data

        sample_json = json.dumps(sample, indent=2, ensure_ascii=False, default=str)

        if len(sample_json) > 3000:
            sample_json = sample_json[:3000] + "\n... (truncated)"

        hints_text = ""
        if field_hints:
            hints_text = f"\nField hints from user:\n{json.dumps(field_hints, indent=2)}\n"

        target_schema = """
{
  "id": "unique-string-id",
  "conversation": [
    {"role": "user", "content": "message text"},
    {"role": "assistant", "content": "response text"}
  ],
  "subject": "optional subject/title",
  "metadata": {}
}
"""

        prompt = f"""Generate a Python function to transform this data format into the LLARS import format.

Input data sample:
```json
{sample_json}
```
{hints_text}
Target format (each item should look like):
```json
{target_schema}
```

Requirements:
1. Function signature: def transform(data: list) -> list
2. Handle missing fields gracefully (use .get() with defaults)
3. Generate unique IDs if not present (use hashlib.md5)
4. Map roles correctly: "user"/"human"/"client" -> "user", "assistant"/"bot"/"ai" -> "assistant"
5. Include helpful comments
6. No external dependencies except hashlib

Return ONLY the Python code, no markdown formatting or explanations."""

        try:
            content = self._client.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            if not content:
                return {
                    "success": False,
                    "error": "No response from LLM",
                    "ai_generated": False,
                }

            # Clean up response
            if "```python" in content:
                content = content.split("```python")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            script = content.strip()

            # Validate it's actual Python
            try:
                compile(script, "<string>", "exec")
                syntax_valid = True
            except SyntaxError as e:
                syntax_valid = False
                script = f"# Syntax error detected: {e}\n\n{script}"

            return {
                "success": syntax_valid,
                "script": script,
                "language": "python",
                "ai_generated": True,
            }

        except Exception as e:
            logger.exception(f"Script generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "ai_generated": False,
            }

    def analyze_intent(
        self,
        data: Any,
        user_intent: str,
        filename: str | None = None,
        file_count: int = 1,
        detected_structure: dict | None = None
    ) -> dict[str, Any]:
        """
        Analyze user intent together with data structure.

        This is the main method for the "conversational" import wizard.
        It takes natural language input from the user and determines:
        - What task type they want (rating, ranking, comparison, etc.)
        - How to map their data fields to LLARS fields
        - What evaluation criteria to use

        Args:
            data: Sample data from uploaded files
            user_intent: Natural language description of what user wants
            filename: Original filename for context
            file_count: Number of files uploaded
            detected_structure: Previously detected structure info

        Returns:
            Analysis result with task type, field mapping, and criteria
        """
        # Prepare sample data
        if isinstance(data, list):
            sample = data[:3]
        elif isinstance(data, dict) and "items" in data:
            sample = data["items"][:3]
        else:
            sample = data

        sample_json = json.dumps(sample, indent=2, ensure_ascii=False, default=str)
        if len(sample_json) > 3500:
            sample_json = sample_json[:3500] + "\n... (truncated)"

        structure_info = ""
        if detected_structure:
            structure_info = f"""
Bereits erkannte Struktur:
- Format: {detected_structure.get('format', 'unbekannt')}
- Felder: {detected_structure.get('fields', [])}
- Einträge: {detected_structure.get('item_count', '?')}
"""

        prompt = f"""Du bist ein Assistent für ein Evaluations-System (LLARS). Analysiere die Benutzeranfrage und die Datenstruktur.

BENUTZERANFRAGE:
"{user_intent}"

KONTEXT:
- {file_count} Datei(en) hochgeladen
- Dateiname: {filename or 'unbekannt'}
{structure_info}

DATENBEISPIEL:
```json
{sample_json}
```

VERFÜGBARE TASK-TYPEN in LLARS:
1. "rating" - Einzelne Einträge auf Skala bewerten (z.B. 1-5 Sterne)
2. "ranking" - Mehrere Einträge nach Kriterium sortieren
3. "comparison" - Zwei Antworten/Texte direkt vergleichen (A vs B)
4. "mail_rating" - E-Mail/Chat-Konversationen bewerten
5. "authenticity" - Echt/Fake erkennen (ist es von Mensch oder KI?)
6. "classification" - Labels/Kategorien zuweisen

Analysiere und gib ein JSON-Objekt zurück mit:

{{
  "task_type": "<einer der obigen Task-Typen>",
  "task_description": "<kurze deutsche Beschreibung was gemacht werden soll>",
  "confidence": <0.0-1.0>,
  "field_mapping": {{
    "<quell-feld>": "<ziel-feld>",
    "messages": "conversation",
    "role": "sender_role"
  }},
  "role_mapping": {{
    "user": "Klient",
    "assistant": "Berater"
  }},
  "evaluation_criteria": ["Kriterium1", "Kriterium2"],
  "reasoning": "<Begründung für die Entscheidungen>"
}}

WICHTIG:
- evaluation_criteria nur bei rating/mail_rating relevant
- role_mapping für Konversationen (wer ist user, wer assistant)
- field_mapping: Pfade wie "messages[].content" sind erlaubt

Gib NUR valides JSON zurück, keine Markdown-Formatierung."""

        try:
            content = self._client.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            if not content:
                return {
                    "success": False,
                    "error": "No response from LLM",
                    "task_type": "mail_rating",  # Fallback
                    "field_mapping": {},
                    "evaluation_criteria": []
                }

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            result["success"] = True
            result["ai_analyzed"] = True

            # Ensure required fields exist
            result.setdefault("task_type", "mail_rating")
            result.setdefault("task_description", "Daten bewerten")
            result.setdefault("field_mapping", {})
            result.setdefault("role_mapping", {"user": "Klient", "assistant": "Berater"})
            result.setdefault("evaluation_criteria", [])
            result.setdefault("confidence", 0.7)

            return result

        except json.JSONDecodeError:
            logger.warning(f"Could not parse AI response as JSON: {content[:200] if content else 'empty'}")
            return {
                "success": False,
                "error": "Could not parse AI response",
                "task_type": "mail_rating",
                "field_mapping": {},
                "evaluation_criteria": []
            }
        except Exception as e:
            logger.exception(f"Intent analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_type": "mail_rating",
                "field_mapping": {},
                "evaluation_criteria": []
            }

    def suggest_improvements(
        self,
        data: Any,
        current_mapping: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Suggest improvements to current field mapping.

        Args:
            data: Sample data
            current_mapping: Current field mapping

        Returns:
            Suggestions for improvement
        """
        sample = data[:2] if isinstance(data, list) else data

        prompt = f"""Review this data and current field mapping. Suggest improvements.

Data sample:
```json
{json.dumps(sample, indent=2, default=str)[:2000]}
```

Current mapping:
```json
{json.dumps(current_mapping, indent=2)}
```

Return JSON with:
1. "issues": List of problems with current mapping
2. "suggestions": List of improvement suggestions
3. "alternative_mapping": Improved mapping if needed
4. "data_quality_notes": Notes about data quality

Return ONLY valid JSON."""

        try:
            content = self._client.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            if not content:
                return {"error": "No response from LLM"}

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

        except Exception as e:
            logger.exception(f"Improvement suggestions failed: {e}")
            return {"error": str(e)}
