"""
AI Analyzer Service for LLM-assisted data analysis and transformation.

Uses LLM to analyze unknown data formats and generate transformation scripts.
Supports streaming responses for real-time configuration extraction.

IMPORTANT: Structure-based detection (SchemaDetector) is used FIRST.
AI is only used for:
1. Configuration details (dimensions, labels, presets) when type is known
2. Full analysis when structure is ambiguous (uncertain confidence)
"""

from typing import Any, Generator
import json
import logging
import re

from llm.litellm_client import LiteLLMClient
from db.models.llm_model import LLMModel
from services.evaluation.schema_export_service import SchemaExportService
from services.data_import.schema_detector import SchemaDetector, DetectionResult, EvaluationType

logger = logging.getLogger(__name__)

# Default colors for config items
DEFAULT_LABEL_COLORS = ["#98d4bb", "#e8a087", "#D1BC8A", "#88c4c8", "#b0ca97"]
DEFAULT_BUCKET_COLORS = ["#98d4bb", "#D1BC8A", "#e8a087"]

# Preset mappings for each evaluation type
DEFAULT_PRESETS = {
    'authenticity': 'binary-authentic',
    'comparison': 'pairwise',
    'ranking': 'buckets-3',
    'labeling': 'multi-label',
    'mail_rating': 'response-quality',
    'rating': 'llm-judge-standard',
}


def _safe_unique_set(values: list) -> set:
    """Create a set from values, filtering out unhashable types (lists, dicts)."""
    return set(v for v in values if v is not None and isinstance(v, (str, int, float, bool)))


class AIAnalyzer:
    """
    AI-powered data analysis and transformation.

    Uses SchemaDetector FIRST for deterministic type detection.
    Uses LLM to:
    - Generate configuration details (dimensions, labels, presets)
    - Full analysis only when structure is ambiguous
    """

    def __init__(self):
        """Initialize the AI analyzer."""
        self._client = LiteLLMClient()
        self._schema_detector = SchemaDetector()

    def _get_default_model(self) -> str:
        """Get the default LLM model ID."""
        model = LLMModel.get_default_model()
        if model:
            return model.model_id
        return "gpt-4o-mini"  # Fallback

    def detect_type_from_structure(
        self,
        data: Any,
        filename: str | None = None
    ) -> dict[str, Any]:
        """
        Detect evaluation type using deterministic schema detection.

        This is the PRIMARY method for type detection.
        Returns immediately if type is definite, no AI needed.

        Args:
            data: The data to analyze (parsed JSON/list/dict)
            filename: Original filename for context

        Returns:
            Detection result with eval_type, confidence, and matched fields
        """
        result = self._schema_detector.detect(data, filename)

        return {
            "detected": result.eval_type is not None,
            "eval_type": result.eval_type.value if result.eval_type else None,
            "confidence": result.confidence,
            "matched_fields": result.matched_fields,
            "reason": result.reason,
            "all_fields": result.all_fields,
            "source": "schema_detection"  # Indicates this was structure-based
        }

    def analyze_structure(
        self,
        data: Any,
        filename: str | None = None,
        max_sample_items: int = 3
    ) -> dict[str, Any]:
        """
        Analyze data structure - uses SchemaDetector FIRST, AI as fallback.

        Args:
            data: The data to analyze (parsed JSON/list/dict)
            filename: Original filename for context
            max_sample_items: Max items to include in sample

        Returns:
            Analysis result with detected format and mapping suggestions
        """
        # STEP 1: Try deterministic schema detection FIRST
        schema_result = self._schema_detector.detect(data, filename)

        if schema_result.confidence == 'definite':
            # Type is certain - return immediately without AI
            logger.info(f"SchemaDetector definitively detected: {schema_result.eval_type.value}")
            return {
                "ai_analyzed": False,
                "schema_detected": True,
                "detection_source": "schema_detection",
                "detected_format": "custom",
                "confidence": 1.0,
                "suggested_task_type": schema_result.eval_type.value,
                "matched_fields": schema_result.matched_fields,
                "reasoning": schema_result.reason,
                "field_mapping": self._infer_field_mapping(data, schema_result),
                "warnings": []
            }

        # STEP 2: Structure unclear - fall back to AI
        logger.info(f"SchemaDetector uncertain, falling back to AI analysis")

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

        # Get evaluation types and input examples from central schema
        eval_types_info = SchemaExportService.get_evaluation_types_description()
        input_examples = SchemaExportService.get_input_data_examples()

        prompt = f"""Analyze this data structure and determine the best way to import it into an LLM evaluation system.

**NOTE:** The automatic schema detector could not determine the type definitively.
Available fields: {schema_result.all_fields}

**FILENAME: {filename or 'unknown'}** ← IMPORTANT! The filename often indicates the evaluation type!
- "authenticity" in name → authenticity
- "ranking" in name → ranking
- "rating" in name → rating
- "comparison" in name → comparison

Data sample:
```json
{sample_json}
```

{eval_types_info}

{input_examples}

Analyze and return a JSON object with:
1. "detected_format": The format type (one of: "openai", "lmsys", "csv", "custom")
2. "confidence": Your confidence score (0.0-1.0)
3. "field_mapping": Map detected fields to standard fields:
   - "id_field": Field containing unique identifier
   - "messages_field": Field containing conversation messages
   - "role_field": Field for message role (user/assistant)
   - "content_field": Field for message content
   - "subject_field": Field for conversation subject (optional)
4. "suggested_task_type": Best evaluation type (use INPUT DATA EXAMPLES above to match patterns!)
5. "reasoning": Brief explanation - which input example matched best?
6. "warnings": List of any issues or concerns

**MOST IMPORTANT:** Analyze the STRUCTURE of the data!
Look at EVERY FIELD (id, is_human, is_fake, messages, source_text, summary_a, etc.)
and compare with the LLARS INPUT DATA EXAMPLES above to find the matching type!

Return ONLY valid JSON, no markdown formatting."""

        # Log prompt for debugging
        logger.info(f"AI Analyzer Structure Prompt Length: {len(prompt)} chars")
        logger.debug(f"AI Analyzer Structure Prompt (first 2000 chars):\n{prompt[:2000]}...")

        try:
            content = self._client.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            if not content:
                return {
                    "ai_analyzed": False,
                    "detection_source": "failed",
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
                result["schema_detected"] = False
                result["detection_source"] = "ai_analysis"
                return result

            except json.JSONDecodeError:
                logger.warning(f"Could not parse AI response as JSON: {content[:200]}")
                return {
                    "ai_analyzed": False,
                    "detection_source": "failed",
                    "error": "Could not parse AI response",
                    "raw_response": content[:500],
                }

        except Exception as e:
            logger.exception(f"AI analysis failed: {e}")
            return {
                "ai_analyzed": False,
                "detection_source": "failed",
                "error": str(e),
            }

    def _infer_field_mapping(self, data: Any, detection: DetectionResult) -> dict:
        """Infer field mapping based on detected type and data structure."""
        sample = data[0] if isinstance(data, list) and data else data
        if isinstance(sample, dict):
            fields = set(sample.keys())
        else:
            fields = set()

        mapping = {}

        # ID field
        for id_field in ['id', 'item_id', 'uuid', 'index']:
            if id_field in fields:
                mapping['id_field'] = id_field
                break

        # Messages/content field based on type
        if detection.eval_type == EvaluationType.MAIL_RATING:
            if 'messages' in fields:
                mapping['messages_field'] = 'messages'
            if 'subject' in fields:
                mapping['subject_field'] = 'subject'
        elif detection.eval_type == EvaluationType.RATING:
            for q_field in ['question', 'prompt', 'input', 'query']:
                if q_field in fields:
                    mapping['question_field'] = q_field
                    break
            for r_field in ['response', 'answer', 'output', 'completion']:
                if r_field in fields:
                    mapping['response_field'] = r_field
                    break
        elif detection.eval_type == EvaluationType.AUTHENTICITY:
            for auth_field in ['is_human', 'is_fake', 'synthetic', 'is_ai']:
                if auth_field in fields:
                    mapping['authenticity_field'] = auth_field
                    break
            for content_field in ['text', 'content', 'messages']:
                if content_field in fields:
                    mapping['content_field'] = content_field
                    break

        return mapping

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

        # Get file format examples from central schema
        format_examples = SchemaExportService.get_file_format_examples()

        target_schema = """
{
  "id": "unique-string-id",
  "conversation": [
    {"role": "user", "content": "message text"},
    {"role": "assistant", "content": "response text"}
  ],
  "subject": "optional subject/title",
  "metadata": {},
  "features": [
    {"type": "Summary", "content": "...", "generated_by": "Model_A"}
  ]
}
"""

        prompt = f"""Generate a Python function to transform this data format into the LLARS import format.

{format_examples}

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

        IMPORTANT: Uses SchemaDetector FIRST to determine type.
        AI is then used ONLY for configuration details (dimensions, labels, presets).

        Args:
            data: Sample data from uploaded files
            user_intent: Natural language description of what user wants
            filename: Original filename for context
            file_count: Number of files uploaded
            detected_structure: Previously detected structure info

        Returns:
            Analysis result with task type, field mapping, and criteria
        """
        # STEP 1: Deterministic schema detection FIRST
        schema_result = self._schema_detector.detect(data, filename)

        # Prepare sample data for AI config generation
        if isinstance(data, list):
            sample = data[:3]
        elif isinstance(data, dict) and "items" in data:
            sample = data["items"][:3]
        else:
            sample = data

        sample_json = json.dumps(sample, indent=2, ensure_ascii=False, default=str)
        if len(sample_json) > 3500:
            sample_json = sample_json[:3500] + "\n... (truncated)"

        # If type is definite, use AI only for config details
        if schema_result.confidence == 'definite':
            logger.info(f"SchemaDetector definite: {schema_result.eval_type.value} - AI for config only")
            return self._generate_config_for_detected_type(
                data=data,
                sample_json=sample_json,
                schema_result=schema_result,
                user_intent=user_intent,
                filename=filename
            )

        # STEP 2: Structure unclear - full AI analysis (legacy behavior)
        logger.info(f"SchemaDetector uncertain - falling back to full AI analysis")

        structure_info = ""
        if detected_structure:
            structure_info = f"""
Bereits erkannte Struktur:
- Format: {detected_structure.get('format', 'unbekannt')}
- Felder: {detected_structure.get('fields', [])}
- Einträge: {detected_structure.get('item_count', '?')}
"""

        # Get complete schema documentation from central service
        schema_documentation = SchemaExportService.get_schema_for_ai_prompt()

        prompt = f"""Du bist ein Experte für das LLARS Evaluations-System. Analysiere die hochgeladenen Daten und bestimme den RICHTIGEN Evaluationstyp.

=== BENUTZERANFRAGE ===
"{user_intent}"

=== KONTEXT ===
- {file_count} Datei(en) hochgeladen
- **DATEINAME: {filename or 'unbekannt'}** ← WICHTIG! Der Dateiname gibt oft einen Hinweis auf den Evaluationstyp!
  - "authenticity" im Namen → authenticity
  - "ranking" im Namen → ranking
  - "rating" im Namen → rating
  - "comparison" im Namen → comparison
{structure_info}

=== HOCHGELADENE DATEN (SAMPLE) ===
```json
{sample_json}
```

{schema_documentation}

=== DEINE AUFGABE ===

**DAS WICHTIGSTE: Analysiere die STRUKTUR der hochgeladenen Daten!**
Schau dir JEDES EINZELNE FELD an (id, is_human, messages, source_text, summary_a, etc.)
und vergleiche es mit den LLARS-Beispielen oben.

1. **VERGLEICHE** die hochgeladenen Daten mit den EINGABEDATEN-BEISPIELEN oben
2. **ERKENNE** das Muster: Welche FELDER existieren? Welchem LLARS-Beispiel entspricht das?
3. **WÄHLE** den passenden Evaluationstyp basierend auf den GEFUNDENEN FELDERN

Analysiere und gib ein JSON-Objekt zurück mit:

{{
  "task_type": "<einer der Evaluationstypen: ranking, rating, comparison, mail_rating, authenticity, labeling>",
  "task_description": "<kurze deutsche Beschreibung was gemacht werden soll>",
  "confidence": <0.0-1.0>,
  "recommended_preset": "<passendes Preset aus den Empfehlungen oben>",
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
  "reasoning": "<Begründung: Welches Eingabedaten-Beispiel hat am besten gepasst und warum?>"
}}

=== WICHTIGSTE REGEL ===

**VERGLEICHE DIE DATENSTRUKTUR MIT DEN LLARS-BEISPIELEN OBEN!**
Schau dir JEDES FELD in den hochgeladenen Daten an und finde das passende LLARS-Beispiel.
Die Feldnamen sind der Schlüssel zur Erkennung des richtigen Evaluationstyps!

=== ENTSCHEIDUNGSHILFE (PRÜFE IN DIESER REIHENFOLGE!) ===

1. AUTHENTICITY wenn: is_human ODER is_fake Feld existiert (HÖCHSTE PRIORITÄT!)
   → Auch wenn messages[] existiert! is_human/is_fake = IMMER authenticity!

2. COMPARISON wenn: answer_a + answer_b oder text_a + text_b (zwei Versionen)

3. LABELING wenn: sentiment/category/topic Labels (mehrklassig, NICHT is_human)

4. RANKING wenn: source_text + summary_a/b/c oder reference + mehrere Varianten
   **ODER Long-Format:** Gleiche ID erscheint mehrfach mit verschiedenen Outputs
   → 1 Referenz + N Outputs = IMMER Ranking!

5. MAIL_RATING wenn: messages[] Array OHNE is_human/is_fake Feld

6. RATING wenn: Einzelne Texte/Antworten ohne Vergleiche
   → 1 Referenz + 1 Output = Rating (Qualität bewerten)

**KRITISCH:**
- Wenn is_human oder is_fake existiert → IMMER authenticity wählen!
- Wenn gleiche ID mehrfach vorkommt mit verschiedenen Outputs → IMMER ranking wählen!

Gib NUR valides JSON zurück, keine Markdown-Formatierung."""

        # Log prompt for debugging
        logger.info(f"AI Analyzer Intent Prompt Length: {len(prompt)} chars")
        logger.debug(f"AI Analyzer Intent Prompt:\n{prompt[:2000]}...")

        try:
            content = self._client.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            if not content:
                return {
                    "success": False,
                    "detection_source": "ai_failed",
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
            result["schema_detected"] = False
            result["detection_source"] = "ai_analysis"

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
                "detection_source": "ai_failed",
                "error": "Could not parse AI response",
                "task_type": "mail_rating",
                "field_mapping": {},
                "evaluation_criteria": []
            }
        except Exception as e:
            logger.exception(f"Intent analysis failed: {e}")
            return {
                "success": False,
                "detection_source": "ai_failed",
                "error": str(e),
                "task_type": "mail_rating",
                "field_mapping": {},
                "evaluation_criteria": []
            }

    def _generate_config_for_detected_type(
        self,
        data: Any,
        sample_json: str,
        schema_result: DetectionResult,
        user_intent: str,
        filename: str | None = None
    ) -> dict[str, Any]:
        """
        Generate configuration details for a definitively detected type.

        AI is used ONLY for config (dimensions, labels, presets) - NOT for type.

        Args:
            data: Sample data
            sample_json: JSON string of sample
            schema_result: Detection result from SchemaDetector
            user_intent: User's description
            filename: Original filename

        Returns:
            Complete analysis result with fixed type and AI-generated config
        """
        eval_type = schema_result.eval_type.value
        default_preset = DEFAULT_PRESETS.get(eval_type, 'llm-judge-standard')

        # Get preset recommendations from schema service
        preset_recommendations = SchemaExportService.get_preset_recommendations()

        # Build a focused prompt for config generation only
        prompt = f"""Du bist ein LLARS Konfigurationsexperte.

Der Evaluationstyp wurde BEREITS AUTOMATISCH ERKANNT als: **{eval_type}**
(Basierend auf Feldern: {schema_result.matched_fields})

ÄNDERE DEN EVALUATIONSTYP NICHT! Er steht fest.

Benutzeranfrage: "{user_intent}"
Dateiname: {filename or 'unbekannt'}

Datenbeispiel:
```json
{sample_json}
```

{preset_recommendations}

Generiere KONFIGURATIONSDETAILS für diesen {eval_type}-Typ:

{{
  "task_description": "<kurze deutsche Beschreibung>",
  "recommended_preset": "<passendes Preset für {eval_type}>",
  "field_mapping": {{}},
  "role_mapping": {{"user": "Klient", "assistant": "Berater"}},
  "evaluation_criteria": ["Kriterium1", "Kriterium2"],
  "reasoning": "<Warum dieses Preset?>"
}}

Gib NUR valides JSON zurück."""

        try:
            content = self._client.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            if content:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                config = json.loads(content.strip())
            else:
                config = {}

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"AI config generation failed: {e}, using defaults")
            config = {}

        # Build final result - type is FIXED from schema detection
        return {
            "success": True,
            "task_type": eval_type,  # Fixed from schema detection
            "task_description": config.get("task_description", f"{eval_type.capitalize()} Evaluation"),
            "confidence": 1.0,  # 100% confident because schema detected
            "recommended_preset": config.get("recommended_preset", default_preset),
            "field_mapping": config.get("field_mapping", self._infer_field_mapping(data, schema_result)),
            "role_mapping": config.get("role_mapping", {"user": "Klient", "assistant": "Berater"}),
            "evaluation_criteria": config.get("evaluation_criteria", []),
            "reasoning": f"Typ automatisch erkannt anhand von: {schema_result.matched_fields}. {config.get('reasoning', '')}",
            # Metadata
            "ai_analyzed": True,
            "schema_detected": True,
            "detection_source": "schema_detection",
            "matched_fields": schema_result.matched_fields,
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

    def generate_field_mapping(
        self,
        data: Any,
        detected_type: str,
        detected_format: str = "unknown",
        filename: str | None = None
    ) -> dict[str, Any]:
        """
        Generate field mapping for detected data format.

        This is the SECOND LLM call after type detection.
        Used especially for Long-Format Ranking where we need to identify:
        - grouping_field: Which field groups rows together (e.g., chat_id)
        - variant_field: Which field identifies variants (e.g., llm_name)
        - output_field: Which field contains the content to evaluate
        - reference_field: Which field contains the source/reference

        Args:
            data: Sample data from uploaded files
            detected_type: The detected evaluation type (e.g., "ranking")
            detected_format: The format ("wide", "long", "unknown")
            filename: Original filename for context

        Returns:
            Mapping configuration for data transformation
        """
        # Prepare sample data
        if isinstance(data, list):
            sample = data[:10]  # More samples for better pattern detection
        elif isinstance(data, dict) and "items" in data:
            sample = data["items"][:10]
        else:
            sample = data

        # Get field names
        if isinstance(sample, list) and sample:
            fields = list(sample[0].keys()) if isinstance(sample[0], dict) else []
        elif isinstance(sample, dict):
            fields = list(sample.keys())
        else:
            fields = []

        sample_json = json.dumps(sample, indent=2, ensure_ascii=False, default=str)
        if len(sample_json) > 3000:
            sample_json = sample_json[:3000] + "\n... (truncated)"

        # Analyze data to detect if it's long format (same ID appears multiple times)
        is_long_format = self._detect_long_format(data)

        # Calculate Long-Format statistics for the prompt
        long_format_stats = ""
        unique_groups = 0
        variants_per_group = 0

        if is_long_format:
            # Find grouping field and calculate stats
            for field in fields:
                if field.lower().endswith('_id') or field.lower().endswith('id') or field in ['id', 'src_id', 'source_id']:
                    if field in sample:
                        values = [row.get(field) for row in data if isinstance(row, dict)]
                        unique_values = _safe_unique_set(values)
                        if len(unique_values) < len(values):
                            unique_groups = len(unique_values)
                            variants_per_group = len(values) // unique_groups if unique_groups > 0 else 0
                            long_format_stats = f"Gruppierungsfeld '{field}': {unique_groups} Gruppen, ~{variants_per_group} Varianten pro Gruppe"
                            break

        prompt = f"""Du analysierst Daten für ein {detected_type.upper()}-Szenario.
{"Das Format ist LONG FORMAT (gleiche ID erscheint mehrfach mit verschiedenen Varianten)." if is_long_format else ""}
{f"STATISTIK: {long_format_stats}" if long_format_stats else ""}

DATEINAME: {filename or 'unbekannt'}

VERFÜGBARE FELDER: {fields}

SAMPLE-DATEN (erste 10 Zeilen):
```json
{sample_json}
```

{"LONG FORMAT ERKENNUNG:" if is_long_format else ""}
{self._analyze_long_format_stats(data) if is_long_format else ""}

ERSTELLE EIN FELD-MAPPING als JSON:

{{
  "format": "long" oder "wide",
  "grouping_field": "<Feld das Items gruppiert, z.B. chat_id, item_id, source_id - NUR bei long format>",
  "variant_field": "<Feld das die Variante identifiziert, z.B. llm_name, model, model_name - NUR bei long format>",
  "output_field": "<Feld mit dem generierten Output/Content, z.B. feature_value, output, response, summary_a>",
  "reference_field": "<Feld mit der Referenz/Quelle, z.B. mails, source, input, source_text> oder null",
  "content_type": "text" oder "json" oder "conversation",
  "metadata_fields": ["<zusätzliche Felder die als Metadaten behalten werden sollen>"],
  "id_template": "<Template für unique ID, z.B. {{chat_id}}_{{llm_name}} bei long format>",
  "unique_groups": {unique_groups if unique_groups > 0 else "<Anzahl der eindeutigen Gruppen bei long format>"},
  "variants_per_group": {variants_per_group if variants_per_group > 0 else "<Anzahl Varianten pro Gruppe bei long format>"},
  "reasoning": "<Kurze Begründung für das Mapping>"
}}

REGELN FÜR LONG FORMAT:
- grouping_field: Welches Feld gruppiert zusammengehörige Zeilen? (gleiche Werte = gleiche Gruppe)
- variant_field: Welches Feld identifiziert die verschiedenen Versionen? (oft LLM/Model-Namen)
- Prüfe ob eine ID mehrfach vorkommt mit verschiedenen variant-Werten

REGELN FÜR WIDE FORMAT:
- grouping_field und variant_field sind null
- output_field kann mehrere sein (summary_a, summary_b, summary_c)

Gib NUR das JSON zurück, keine Erklärungen."""

        logger.info(f"Generating field mapping for {detected_type} ({detected_format})")

        try:
            content = self._client.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            if not content:
                return {
                    "success": False,
                    "error": "No response from LLM",
                    "format": "unknown"
                }

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            result["success"] = True

            # Validate required fields for long format
            if result.get("format") == "long":
                required = ["grouping_field", "variant_field", "output_field"]
                missing = [f for f in required if not result.get(f)]
                if missing:
                    result["warnings"] = [f"Missing required fields for long format: {missing}"]

            logger.info(f"Field mapping generated: format={result.get('format')}, "
                       f"grouping={result.get('grouping_field')}, variant={result.get('variant_field')}")

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse mapping response as JSON: {e}")
            return {
                "success": False,
                "error": "Could not parse LLM response",
                "format": "unknown"
            }
        except Exception as e:
            logger.exception(f"Field mapping generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "format": "unknown"
            }

    def _detect_long_format(self, data: Any) -> bool:
        """
        Detect if data is in long format (same ID appears multiple times).

        Returns True if a potential grouping field has duplicate values.

        Handles cryptic/abbreviated column names like:
        - src_id, s_id, sid → source/item ID
        - mdl, mod, m → model/variant
        """
        if not isinstance(data, list) or len(data) < 2:
            return False

        sample = data[0] if data else {}
        if not isinstance(sample, dict):
            return False

        fields = list(sample.keys())

        # Potential grouping fields - includes cryptic abbreviations
        grouping_candidates = [
            'chat_id', 'id', 'item_id', 'source_id', 'reference_id',
            'conversation_id', 'thread_id', 'doc_id', 'document_id',
            # Cryptic/abbreviated versions
            'src_id', 's_id', 'sid', 'cid', 'tid', 'ref_id', 'rid',
            'grp_id', 'group_id', 'gid', 'sample_id', 'idx', 'index'
        ]

        # Also check for any field ending with '_id' or containing 'id'
        for field in fields:
            lower_field = field.lower()
            if lower_field.endswith('_id') or lower_field.endswith('id'):
                if field not in grouping_candidates:
                    grouping_candidates.append(field)

        for field in grouping_candidates:
            if field in sample:
                # Check if this field has duplicates
                values = [row.get(field) for row in data[:100] if isinstance(row, dict)]
                unique_count = len(set(v for v in values if v is not None))
                total_count = len([v for v in values if v is not None])

                # If significantly fewer unique values than total rows, it's long format
                if unique_count > 0 and total_count > unique_count * 1.5:
                    logger.info(f"Long-Format detected: {field} has {unique_count} unique / {total_count} total")
                    return True

        # Check for model/llm_name fields which indicate variants
        # Includes cryptic abbreviations
        variant_indicators = [
            'llm_name', 'model', 'model_name', 'model_id', 'generator', 'variant',
            # Cryptic/abbreviated versions
            'mdl', 'mod', 'm', 'llm', 'gen', 'var', 'version', 'ver', 'v',
            'source', 'src', 'type', 'kind', 'system', 'sys'
        ]

        # Also check if any field has a small number of unique values (likely a variant field)
        for field in fields:
            if field not in grouping_candidates:
                values = [row.get(field) for row in data[:100] if isinstance(row, dict)]
                unique_values = _safe_unique_set(values)

                # If field has 2-10 unique values and appears in most rows, it's likely a variant field
                if 2 <= len(unique_values) <= 10 and len(values) > len(unique_values) * 2:
                    # Check if values look like model names (alphanumeric, no long sentences)
                    if all(isinstance(v, str) and len(v) < 50 for v in unique_values):
                        logger.info(f"Potential variant field detected: {field} with values {list(unique_values)[:5]}")
                        return True

        has_variant_field = any(v in sample for v in variant_indicators)
        if has_variant_field:
            logger.info(f"Variant indicator field found in: {[v for v in variant_indicators if v in sample]}")

        return has_variant_field

    def _analyze_long_format_stats(self, data: Any) -> str:
        """
        Analyze long format data and return statistics string.

        Handles cryptic/abbreviated column names.
        """
        if not isinstance(data, list) or not data:
            return ""

        sample = data[0]
        if not isinstance(sample, dict):
            return ""

        fields = list(sample.keys())
        stats_lines = []

        # Find grouping field - includes cryptic names
        grouping_candidates = [
            'chat_id', 'id', 'item_id', 'source_id', 'reference_id',
            'src_id', 's_id', 'sid', 'cid', 'tid', 'ref_id', 'rid',
            'grp_id', 'group_id', 'gid', 'sample_id', 'idx', 'index'
        ]

        # Also include any field ending with _id
        for field in fields:
            if field.lower().endswith('_id') or field.lower().endswith('id'):
                if field not in grouping_candidates:
                    grouping_candidates.append(field)

        for field in grouping_candidates:
            if field in sample:
                values = [row.get(field) for row in data if isinstance(row, dict)]
                unique_values = _safe_unique_set(values)
                if len(unique_values) < len(values):
                    stats_lines.append(f"- {field}: {len(unique_values)} eindeutige Werte, {len(values)} Zeilen")
                    stats_lines.append(f"  → Vermutlich Gruppierungs-Feld (gleiche {field} = zusammengehörige Items)")

        # Find variant field - includes cryptic names
        variant_candidates = [
            'llm_name', 'model', 'model_name', 'model_id', 'generator', 'variant',
            'mdl', 'mod', 'm', 'llm', 'gen', 'var', 'version', 'ver',
            'source', 'src', 'type', 'kind', 'system', 'sys'
        ]

        for field in variant_candidates:
            if field in sample:
                values = [row.get(field) for row in data if isinstance(row, dict)]
                unique_values = _safe_unique_set(values)
                stats_lines.append(f"- {field}: {len(unique_values)} verschiedene Werte: {list(unique_values)[:5]}...")
                stats_lines.append(f"  → Vermutlich Varianten-Feld (identifiziert verschiedene LLMs/Modelle)")

        # Also check all fields for potential variant patterns
        for field in fields:
            if field not in grouping_candidates and field not in variant_candidates:
                values = [row.get(field) for row in data[:100] if isinstance(row, dict)]
                unique_values = _safe_unique_set(values)
                if not unique_values:
                    continue

                # If field has 2-10 unique values, might be a variant
                if 2 <= len(unique_values) <= 10 and len(values) > len(unique_values) * 2:
                    if all(isinstance(v, str) and len(v) < 50 for v in unique_values):
                        stats_lines.append(f"- {field}: {len(unique_values)} verschiedene kurze Werte: {list(unique_values)[:5]}")
                        stats_lines.append(f"  → Möglicherweise Varianten-Feld")

        return "\n".join(stats_lines) if stats_lines else ""

    def chat_refine_streaming(
        self,
        data: Any,
        messages: list[dict],
        current_config: dict | None = None,
        filename: str | None = None
    ) -> Generator[dict, None, None]:
        """
        Streaming chat for configuration refinement.

        Enables conversational refinement of scenario configuration.
        Extracts structured config updates (labels, buckets, scales) during streaming.

        Args:
            data: Sample data from uploaded files
            messages: Chat history [{role, content}]
            current_config: Current configuration to refine
            filename: Original filename for context

        Yields:
            {"type": "thinking", "message": "..."}
            {"type": "config", "field": "task_type", "value": "rating"}
            {"type": "config", "field": "labels", "value": [...]}
            {"type": "config", "field": "buckets", "value": [...]}
            {"type": "config", "field": "scales", "value": [...]}
            {"type": "chunk", "content": "..."}
            {"type": "done", "config": {...}, "response": "..."}
        """
        # Prepare sample data
        if isinstance(data, list):
            sample = data[:3]
        elif isinstance(data, dict) and "items" in data:
            sample = data["items"][:3]
        else:
            sample = data

        sample_json = json.dumps(sample, indent=2, ensure_ascii=False, default=str)
        if len(sample_json) > 2500:
            sample_json = sample_json[:2500] + "\n... (truncated)"

        current_config = current_config or {}
        config_json = json.dumps(current_config, indent=2, ensure_ascii=False)

        # Build system prompt for config extraction
        # Get schema documentation from central service
        eval_types = SchemaExportService.get_evaluation_types_description()
        preset_recommendations = SchemaExportService.get_preset_recommendations()
        input_examples = SchemaExportService.get_input_data_examples()

        system_prompt = f"""Du bist ein Experte für das LLARS Evaluations-System.
Du hilfst Benutzern, ihre Daten für Evaluationen zu konfigurieren.

DEINE AUFGABE:
1. Verstehe was der Benutzer möchte
2. Erkenne den richtigen Evaluationstyp basierend auf den Datenmustern
3. Extrahiere Konfigurationswerte aus dem Gespräch
4. Gib strukturierte Updates und freundliche Antworten

{eval_types}

{input_examples}

{preset_recommendations}

KONFIGURATIONSSTRUKTUR:

Labels (für authenticity/labeling):
[{{"name": "echt", "color": "#98d4bb", "description": "Von Menschen"}}, ...]

Buckets (für ranking):
[{{"name": "gut", "order": 1, "color": "#98d4bb"}}, {{"name": "mittel", "order": 2, "color": "#D1BC8A"}}, {{"name": "schlecht", "order": 3, "color": "#e8a087"}}]

Dimensions (für rating/mail_rating):
[{{"id": "coherence", "name": "Kohärenz", "weight": 0.25}}, {{"id": "fluency", "name": "Flüssigkeit", "weight": 0.25}}]

Scales (für rating/mail_rating):
{{"min": 1, "max": 5, "labels": {{"1": "Sehr schlecht", "5": "Sehr gut"}}}}

ANTWORTFORMAT:
Antworte mit einem JSON-Block am ANFANG deiner Nachricht, gefolgt von deiner Erklärung:

```config
{{
  "task_type": "...",
  "recommended_preset": "preset-id",
  "labels": [...],
  "buckets": [...],
  "dimensions": [...],
  "scales": {{}},
  "field_mapping": {{}},
  "role_mapping": {{}}
}}
```

Dann deine freundliche Erklärung auf Deutsch.

WICHTIG:
- Gib nur Felder im config-Block an, die du ändern möchtest
- Lass Felder weg, die unverändert bleiben
- Wenn nichts geändert werden soll, lass den config-Block weg
- task_type muss einer der Werte aus der Evaluationstypen-Tabelle sein (nutze "labeling", nicht "classification")
- Empfehle immer ein passendes Preset mit recommended_preset
- Antworte immer auf Deutsch und freundlich"""

        # Build user context
        context_msg = f"""KONTEXT:
**DATEINAME: {filename or 'unbekannt'}** ← WICHTIG! Nutze den Dateinamen als Hinweis!
(authenticity/ranking/rating/comparison im Namen = entsprechender Typ)

Datenbeispiel:
```json
{sample_json}
```

Aktuelle Konfiguration:
```json
{config_json}
```"""

        # Build full message list
        full_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_msg}
        ]

        # Add chat history
        for msg in messages:
            full_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        # Log prompt for debugging
        logger.info(f"AI Chat Refine System Prompt Length: {len(system_prompt)} chars")
        logger.debug(f"AI Chat Refine System Prompt:\n{system_prompt[:3000]}...")

        try:
            # Emit thinking event
            yield {"type": "thinking", "message": "KI verarbeitet..."}

            # Stream the response
            full_response = ""
            config_extracted = False
            extracted_config = {}

            for chunk in self._client.stream_complete(
                messages=full_messages,
                temperature=0.3,
                max_tokens=1500
            ):
                full_response += chunk
                yield {"type": "chunk", "content": chunk}

                # Try to extract config from accumulated response
                if not config_extracted and "```config" in full_response:
                    config_match = re.search(r'```config\s*\n(.*?)\n```', full_response, re.DOTALL)
                    if config_match:
                        try:
                            config_json_str = config_match.group(1)
                            extracted_config = json.loads(config_json_str)
                            config_extracted = True

                            # Emit config updates for each field
                            for field in ["task_type", "task_description", "labels",
                                          "buckets", "scales", "field_mapping", "role_mapping"]:
                                if field in extracted_config:
                                    value = extracted_config[field]
                                    # Add default colors to labels/buckets if missing
                                    if field == "labels" and isinstance(value, list):
                                        value = self._add_label_colors(value)
                                    elif field == "buckets" and isinstance(value, list):
                                        value = self._add_bucket_colors(value)
                                    yield {"type": "config", "field": field, "value": value}

                        except json.JSONDecodeError:
                            pass  # Config not complete yet

            # Extract text response (everything after config block)
            text_response = full_response
            if "```config" in text_response:
                text_response = re.sub(r'```config\s*\n.*?\n```\s*', '', text_response, flags=re.DOTALL)
            text_response = text_response.strip()

            # Merge extracted config with current config
            final_config = {**current_config, **extracted_config}

            yield {
                "type": "done",
                "config": final_config,
                "response": text_response
            }

        except Exception as e:
            logger.exception(f"Chat refinement failed: {e}")
            yield {"type": "error", "error": str(e)}

    def _add_label_colors(self, labels: list) -> list:
        """Add default colors to labels if missing."""
        result = []
        for i, label in enumerate(labels):
            if isinstance(label, str):
                label = {"name": label}
            if isinstance(label, dict) and "color" not in label:
                label["color"] = DEFAULT_LABEL_COLORS[i % len(DEFAULT_LABEL_COLORS)]
            result.append(label)
        return result

    def _add_bucket_colors(self, buckets: list) -> list:
        """Add default colors and order to buckets if missing."""
        result = []
        for i, bucket in enumerate(buckets):
            if isinstance(bucket, str):
                bucket = {"name": bucket}
            if isinstance(bucket, dict):
                if "color" not in bucket:
                    bucket["color"] = DEFAULT_BUCKET_COLORS[i % len(DEFAULT_BUCKET_COLORS)]
                if "order" not in bucket:
                    bucket["order"] = i + 1
            result.append(bucket)
        return result

    def transform_long_format_to_ranking(
        self,
        data: list[dict],
        field_mapping: dict[str, Any]
    ) -> list[dict]:
        """
        Transform long-format data to LLARS ranking format (Wide-Format).

        Long-format: Each row is one variant (same grouping_field appears multiple times)
        Example input:
            src_id,mdl,out,inp
            S001,gpt4,output1,input1
            S001,claude,output2,input1
            S001,llama,output3,input1

        Wide-format output (for UniversalTransformer):
            {
                'id': 'S001',
                'source_text': 'input1',
                'summary_a': 'output1',  # gpt4
                'summary_b': 'output2',  # claude
                'summary_c': 'output3',  # llama
                'metadata': {'model_a': 'gpt4', 'model_b': 'claude', 'model_c': 'llama'}
            }

        Args:
            data: List of rows in long format
            field_mapping: Mapping from generate_field_mapping()

        Returns:
            List of Wide-Format items for UniversalTransformer
        """
        if not field_mapping.get('success'):
            logger.warning("Cannot transform: field mapping was not successful")
            return data

        grouping_field = field_mapping.get('grouping_field')
        variant_field = field_mapping.get('variant_field')
        output_field = field_mapping.get('output_field')
        reference_field = field_mapping.get('reference_field')
        metadata_fields = field_mapping.get('metadata_fields', [])

        if not all([grouping_field, variant_field, output_field]):
            logger.warning(f"Missing required fields for transformation: "
                          f"grouping={grouping_field}, variant={variant_field}, output={output_field}")
            return data

        # Group rows by grouping_field
        groups: dict[str, list[dict]] = {}
        for row in data:
            group_key = str(row.get(grouping_field, 'unknown'))
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(row)

        logger.info(f"Transforming long-format: {len(groups)} groups, {len(data)} total rows")

        # Suffix letters for Wide-Format (a, b, c, d, e, ...)
        suffix_letters = 'abcdefghijklmnopqrstuvwxyz'

        # Transform each group to Wide-Format
        result = []
        for group_id, rows in groups.items():
            # Get reference from first row (should be same across group)
            first_row = rows[0]
            reference_content = first_row.get(reference_field, '') if reference_field else ''

            # Parse reference if it's JSON string (e.g., messages array)
            if isinstance(reference_content, str) and reference_content.startswith('['):
                try:
                    reference_content = json.loads(reference_content)
                except json.JSONDecodeError:
                    pass

            # Build Wide-Format item
            wide_item = {
                'id': group_id,
                'source_text': reference_content,
            }

            # Add each variant as summary_a, summary_b, summary_c, etc.
            metadata = {}
            for i, row in enumerate(rows):
                if i >= len(suffix_letters):
                    logger.warning(f"Too many variants ({len(rows)}) for group {group_id}, truncating")
                    break

                suffix = suffix_letters[i]
                variant_name = row.get(variant_field, f'variant_{i}')
                output_content = row.get(output_field, '')

                # Parse output if it's JSON string
                if isinstance(output_content, str) and output_content.startswith('{'):
                    try:
                        output_content = json.loads(output_content)
                    except json.JSONDecodeError:
                        pass

                # Add as summary_a, summary_b, etc.
                wide_item[f'summary_{suffix}'] = output_content

                # Track model names in metadata
                metadata[f'model_{suffix}'] = str(variant_name)

                # Add other metadata fields
                for meta_field in metadata_fields:
                    if meta_field in row and meta_field not in [grouping_field, variant_field, output_field, reference_field]:
                        metadata[f'{meta_field}_{suffix}'] = row.get(meta_field)

            if metadata:
                wide_item['metadata'] = metadata

            result.append(wide_item)

        logger.info(f"Transformation complete: {len(result)} wide-format items with "
                   f"{len([k for k in result[0].keys() if k.startswith('summary_')]) if result else 0} variants each")
        return result
