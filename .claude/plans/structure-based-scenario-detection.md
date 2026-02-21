# Konzept: Strukturbasierte Szenario-Erkennung

## Ziel

Die Datenstruktur (Feldnamen, Spalten) soll **deterministisch** den Evaluationstyp bestimmen. Das LLM wird nur für die Detailkonfiguration (Dimensionen, Labels, Presets) verwendet, **nicht** für die Typbestimmung.

---

## Aktueller vs. Neuer Flow

### Aktuell (AI-gesteuert)
```
Upload → AI analysiert alles → AI rät Typ + Config → User bestätigt
         ↑ Problem: AI kann falsch raten (authenticity vs mail_rating)
```

### Neu (Struktur-gesteuert)
```
Upload → Schema-Detector (deterministisch) → Typ steht fest
                                          → AI generiert nur Config-Details
                                          → User bestätigt Config
```

---

## Schema-Detector Regeln

### Prioritätsreihenfolge (WICHTIG!)

Die Erkennung erfolgt in dieser Reihenfolge. Erste Übereinstimmung gewinnt.

| Prio | Erkennungsmuster | → Typ |
|------|------------------|-------|
| 1 | `is_human`, `is_fake`, `synthetic`, `is_ai` | **authenticity** |
| 2 | `response_a` + `response_b` ODER `conversation_a` + `conversation_b` ODER `winner` | **comparison** |
| 3 | `summary_a` + `summary_b` ODER 3+ Spalten mit `_a`, `_b`, `_c` Suffix | **ranking** |
| 4 | `messages[]` Array (Konversation ohne is_human) | **mail_rating** |
| 5 | `question` + `response` ODER `prompt` + `completion` | **rating** |
| 6 | `category`, `label`, `sentiment`, `topic` (ohne Q&A) | **labeling** |
| 7 | Einzelne Texte ohne klare Struktur | **rating** (Fallback) |

**Hinweis:** Rating (Prio 5) kommt vor Labeling (Prio 6), weil Q&A-Struktur spezifischer ist als category-Felder (die oft Metadaten sind).

---

## Detaillierte Erkennungsregeln

### 1. Authenticity (Prio 1)
**Felder:** `is_human`, `is_fake`, `synthetic`, `is_ai`, `is_generated`, `human_written`

```python
AUTHENTICITY_FIELDS = {'is_human', 'is_fake', 'synthetic', 'is_ai', 'is_generated', 'human_written', 'ai_generated'}

def is_authenticity(fields: set) -> bool:
    return bool(fields & AUTHENTICITY_FIELDS)
```

**Beispiel-Strukturen:**
```json
// JSON
{"id": "1", "text": "...", "is_human": true}
{"id": "1", "messages": [...], "is_fake": false}
```
```csv
// CSV
id,text,is_human
id,content,synthetic
```

---

### 2. Comparison (Prio 2)
**Felder:** `response_a`/`response_b`, `conversation_a`/`conversation_b`, `answer_a`/`answer_b`, `winner`, `preferred`

```python
COMPARISON_PAIRS = [
    ('response_a', 'response_b'),
    ('conversation_a', 'conversation_b'),
    ('answer_a', 'answer_b'),
    ('output_a', 'output_b'),
    ('model_a', 'model_b'),
]
COMPARISON_INDICATORS = {'winner', 'preferred', 'chosen', 'better'}

def is_comparison(fields: set) -> bool:
    # Paarweise Felder
    for a, b in COMPARISON_PAIRS:
        if a in fields and b in fields:
            return True
    # Winner-Feld
    if fields & COMPARISON_INDICATORS:
        return True
    return False
```

**Beispiel-Strukturen:**
```json
{"prompt": "...", "response_a": "...", "response_b": "...", "winner": "a"}
```
```csv
id,prompt,response_a,response_b
```

---

### 3. Ranking (Prio 3)
**Felder:** `summary_a`/`summary_b`/`summary_c`, oder 3+ Felder mit gleichem Präfix und `_a`, `_b`, `_c` Suffix

```python
def is_ranking(fields: set) -> bool:
    # Explizite Summary-Felder
    summary_fields = {f for f in fields if f.startswith('summary_')}
    if len(summary_fields) >= 2:
        return True

    # Generisches Pattern: prefix_a, prefix_b, prefix_c
    suffixes = {'_a', '_b', '_c', '_1', '_2', '_3'}
    prefixes = {}
    for field in fields:
        for suffix in suffixes:
            if field.endswith(suffix):
                prefix = field[:-len(suffix)]
                prefixes[prefix] = prefixes.get(prefix, 0) + 1

    # 3+ Varianten eines Feldes = Ranking
    return any(count >= 3 for count in prefixes.values())
```

**Beispiel-Strukturen:**
```csv
id,source_text,summary_a,summary_b,summary_c
id,question,answer_1,answer_2,answer_3
```

---

### 4. Labeling (Prio 4)
**Felder:** `category`, `label`, `sentiment`, `topic`, `class`, `tag`, `classification`

```python
LABELING_FIELDS = {'category', 'label', 'sentiment', 'topic', 'class', 'tag', 'classification', 'category_id'}

def is_labeling(fields: set) -> bool:
    # Muss ein Labeling-Feld haben UND Text-Content
    has_label_field = bool(fields & LABELING_FIELDS)
    has_content = bool(fields & {'text', 'content', 'message', 'document'})
    return has_label_field and has_content
```

**Beispiel-Strukturen:**
```json
{"id": "1", "text": "...", "category": "positive"}
{"id": "1", "content": "...", "sentiment": "negative"}
```

---

### 5. Mail Rating (Prio 5)
**Felder:** `messages` Array mit Konversationsstruktur

```python
def is_mail_rating(data: dict) -> bool:
    # Muss messages Array haben
    if 'messages' not in data:
        return False
    messages = data.get('messages', [])
    if not isinstance(messages, list) or len(messages) < 2:
        return False
    # Prüfe Konversationsstruktur (role/content oder sender/text)
    first_msg = messages[0] if messages else {}
    return 'role' in first_msg or 'sender' in first_msg or 'from' in first_msg
```

**Beispiel-Strukturen:**
```json
{
  "id": "1",
  "subject": "Anfrage",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

---

### 6. Rating (Prio 6 / Fallback)
**Felder:** `question`/`response`, `prompt`/`completion`, `input`/`output`

```python
RATING_PAIRS = [
    ('question', 'response'),
    ('question', 'answer'),
    ('prompt', 'completion'),
    ('prompt', 'response'),
    ('input', 'output'),
]

def is_rating(fields: set) -> bool:
    for q, a in RATING_PAIRS:
        if q in fields and a in fields:
            return True
    # Fallback: Einzelne Texte
    return bool(fields & {'text', 'content', 'response', 'answer'})
```

---

## CSV-Spezifische Regeln

Bei CSV wird die **erste Zeile (Header)** analysiert:

```python
def detect_csv_type(headers: list[str]) -> str:
    fields = set(h.lower().strip() for h in headers)

    if is_authenticity(fields): return 'authenticity'
    if is_comparison(fields): return 'comparison'
    if is_ranking(fields): return 'ranking'
    if is_labeling(fields): return 'labeling'
    # CSV hat kein messages Array → kein mail_rating
    if is_rating(fields): return 'rating'

    return None  # Unbekannt → AI entscheidet
```

---

## JSON/JSONL-Spezifische Regeln

Bei JSON wird das **erste Objekt** (oder bei Array das erste Element) analysiert:

```python
def detect_json_type(data: dict | list) -> str:
    sample = data[0] if isinstance(data, list) else data
    fields = set(sample.keys())

    if is_authenticity(fields): return 'authenticity'
    if is_comparison(fields): return 'comparison'
    if is_ranking(fields): return 'ranking'
    if is_labeling(fields): return 'labeling'
    if is_mail_rating(sample): return 'mail_rating'
    if is_rating(fields): return 'rating'

    return None  # Unbekannt → AI entscheidet
```

---

## Implementierung: SchemaDetector Service

### Neue Datei: `app/services/data_import/schema_detector.py`

```python
"""
Deterministic schema detection for evaluation data.
Determines evaluation type based on field names/structure, NOT AI.
"""

from typing import Optional, Dict, Any, Set, List
from dataclasses import dataclass
from enum import Enum


class EvaluationType(Enum):
    AUTHENTICITY = 'authenticity'
    COMPARISON = 'comparison'
    RANKING = 'ranking'
    LABELING = 'labeling'
    MAIL_RATING = 'mail_rating'
    RATING = 'rating'


@dataclass
class DetectionResult:
    """Result of schema detection."""
    eval_type: Optional[EvaluationType]
    confidence: str  # 'definite', 'likely', 'uncertain'
    matched_fields: List[str]
    reason: str


class SchemaDetector:
    """Detects evaluation type from data structure."""

    # Priority 1: Authenticity
    AUTHENTICITY_FIELDS = {
        'is_human', 'is_fake', 'synthetic', 'is_ai',
        'is_generated', 'human_written', 'ai_generated'
    }

    # Priority 2: Comparison
    COMPARISON_PAIRS = [
        ('response_a', 'response_b'),
        ('conversation_a', 'conversation_b'),
        ('answer_a', 'answer_b'),
        ('output_a', 'output_b'),
    ]
    COMPARISON_INDICATORS = {'winner', 'preferred', 'chosen', 'better'}

    # Priority 4: Labeling
    LABELING_FIELDS = {
        'category', 'label', 'sentiment', 'topic',
        'class', 'tag', 'classification', 'category_id'
    }

    # Priority 6: Rating
    RATING_PAIRS = [
        ('question', 'response'),
        ('question', 'answer'),
        ('prompt', 'completion'),
        ('prompt', 'response'),
        ('input', 'output'),
    ]

    def detect(self, data: Any, filename: str = None) -> DetectionResult:
        """Main detection entry point."""
        if isinstance(data, list) and data:
            sample = data[0]
        elif isinstance(data, dict):
            sample = data
        else:
            return DetectionResult(None, 'uncertain', [], 'Invalid data format')

        fields = set(str(k).lower() for k in sample.keys())

        # Priority order
        checks = [
            (self._check_authenticity, EvaluationType.AUTHENTICITY),
            (self._check_comparison, EvaluationType.COMPARISON),
            (self._check_ranking, EvaluationType.RANKING),
            (self._check_labeling, EvaluationType.LABELING),
            (self._check_mail_rating, EvaluationType.MAIL_RATING),
            (self._check_rating, EvaluationType.RATING),
        ]

        for check_fn, eval_type in checks:
            result = check_fn(fields, sample)
            if result:
                return DetectionResult(
                    eval_type=eval_type,
                    confidence='definite',
                    matched_fields=result,
                    reason=f"Detected {eval_type.value} based on fields: {result}"
                )

        return DetectionResult(None, 'uncertain', [], 'No clear pattern matched')

    def _check_authenticity(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        matched = fields & self.AUTHENTICITY_FIELDS
        return list(matched) if matched else None

    def _check_comparison(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        for a, b in self.COMPARISON_PAIRS:
            if a in fields and b in fields:
                return [a, b]
        indicators = fields & self.COMPARISON_INDICATORS
        if indicators:
            return list(indicators)
        return None

    def _check_ranking(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        # Check for summary_a, summary_b, summary_c pattern
        summary_fields = [f for f in fields if f.startswith('summary_')]
        if len(summary_fields) >= 2:
            return summary_fields

        # Check for generic _a, _b, _c pattern
        suffixes = ['_a', '_b', '_c', '_1', '_2', '_3']
        prefixes = {}
        for field in fields:
            for suffix in suffixes:
                if field.endswith(suffix):
                    prefix = field[:-len(suffix)]
                    if prefix not in prefixes:
                        prefixes[prefix] = []
                    prefixes[prefix].append(field)

        for prefix, matched in prefixes.items():
            if len(matched) >= 3:
                return matched

        return None

    def _check_labeling(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        label_fields = fields & self.LABELING_FIELDS
        content_fields = fields & {'text', 'content', 'message', 'document', 'input'}
        if label_fields and content_fields:
            return list(label_fields | content_fields)
        return None

    def _check_mail_rating(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        if 'messages' not in sample:
            return None
        messages = sample.get('messages', [])
        if not isinstance(messages, list) or len(messages) < 2:
            return None
        first_msg = messages[0] if messages else {}
        if isinstance(first_msg, dict):
            if any(k in first_msg for k in ['role', 'sender', 'from', 'author']):
                return ['messages']
        return None

    def _check_rating(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        for q, a in self.RATING_PAIRS:
            if q in fields and a in fields:
                return [q, a]
        # Fallback: any content field
        content = fields & {'text', 'content', 'response', 'answer', 'output'}
        if content:
            return list(content)
        return None
```

---

## Integration in AI Analyzer

### Änderung in `ai_analyzer.py`

```python
from services.data_import.schema_detector import SchemaDetector, DetectionResult

class AIDataAnalyzer:
    def __init__(self):
        self.schema_detector = SchemaDetector()

    async def analyze_structure(self, ...):
        # SCHRITT 1: Deterministische Erkennung
        detection = self.schema_detector.detect(parsed_data, filename)

        if detection.confidence == 'definite':
            # Typ steht fest → AI nur für Config
            return {
                "eval_type": detection.eval_type.value,
                "eval_type_source": "schema_detection",  # NEU
                "detected_fields": detection.matched_fields,
                "detection_reason": detection.reason,
                # AI generiert nur diese Felder:
                "suggested_preset": await self._ai_suggest_preset(detection.eval_type, parsed_data),
                "suggested_dimensions": await self._ai_suggest_dimensions(detection.eval_type, parsed_data),
            }
        else:
            # Unklare Struktur → AI darf Typ vorschlagen (wie bisher)
            return await self._ai_full_analysis(parsed_data, filename)
```

---

## Frontend-Anpassung

### Wizard zeigt Erkennungsquelle an

```vue
<template>
  <div v-if="analysisResult.eval_type_source === 'schema_detection'">
    <v-alert type="success" variant="tonal">
      <strong>Automatisch erkannt:</strong> {{ analysisResult.eval_type }}
      <br>
      <small>Basierend auf Feldern: {{ analysisResult.detected_fields.join(', ') }}</small>
    </v-alert>
  </div>
  <div v-else>
    <v-alert type="info" variant="tonal">
      <strong>KI-Vorschlag:</strong> {{ analysisResult.eval_type }}
      <br>
      <small>Die Datenstruktur war nicht eindeutig. Bitte überprüfen.</small>
    </v-alert>
  </div>
</template>
```

---

## Beispiel-Mappings

| Dateiname | Erkannte Felder | → Typ | Confidence |
|-----------|-----------------|-------|------------|
| `authenticity-conversations.json` | `is_human` | authenticity | definite |
| `mail-rating-conversations.json` | `messages[]` | mail_rating | definite |
| `ranking-summaries.csv` | `summary_a, summary_b, summary_c` | ranking | definite |
| `rating-responses/*.json` | `question, response` | rating | definite |
| `comparison-data.json` | `response_a, response_b, winner` | comparison | definite |
| `sentiment-data.csv` | `text, sentiment` | labeling | definite |
| `random-data.json` | `foo, bar, baz` | ??? | uncertain → AI |

---

## Vorteile

1. **Deterministisch**: Gleiche Daten → Immer gleiches Ergebnis
2. **Schneller**: Keine AI-Calls für Typ-Erkennung nötig
3. **Zuverlässiger**: Keine Fehlinterpretation durch AI
4. **Transparent**: User sieht genau warum ein Typ gewählt wurde
5. **Fallback**: Bei unklarer Struktur hilft AI weiterhin

---

## Implementierungs-Reihenfolge

1. **`schema_detector.py`** erstellen mit allen Regeln
2. **`ai_analyzer.py`** anpassen: Schema-Detector zuerst aufrufen
3. **Frontend** anpassen: Erkennungsquelle anzeigen
4. **Tests** schreiben für alle Erkennungsmuster

---

## Offene Fragen

1. Soll der User den automatisch erkannten Typ überschreiben können?
2. Sollen wir "magic fields" dokumentieren, damit User wissen welche Feldnamen zu welchem Typ führen?
3. Wie gehen wir mit Grenzfällen um (z.B. `messages[]` + `is_human` → authenticity gewinnt)?
