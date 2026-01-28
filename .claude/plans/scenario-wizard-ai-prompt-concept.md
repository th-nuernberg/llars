# Scenario Wizard AI Prompt - Statusbericht & Konzept

**Stand:** 2026-01-28
**Autor:** Claude Code
**Status:** IMPLEMENTIERT

## 1. Statusbericht: Aktueller Zustand

### 1.1 Beteiligte Dateien

| Datei | Funktion | Status |
|-------|----------|--------|
| `app/services/ai_assist/field_prompt_service.py` | AI Prompt Templates (DB-gestützt) | Hardcodierte Schemas |
| `app/services/data_import/ai_analyzer.py` | AI Analyse-Logik | Duplizierte Schema-Info |
| `app/schemas/evaluation_data_schemas.py` | **Zentrale Schema-Definition** (Ground Truth) | Nicht genutzt von AI |
| `llars-frontend/src/views/ScenarioManager/config/evaluationPresets.js` | UI Presets | Nicht an AI übergeben |
| `app/routes/ai_assist/scenario_analysis_routes.py` | API Endpoints | Kein Schema-Export |

### 1.2 Aktuelles AI Prompt ("scenario.analysis")

**Positiv:**
- Kennt alle 6 Evaluationstypen (rating, ranking, labeling, comparison, mail_rating, authenticity)
- Hat JSON-Ausgabeformat definiert
- Enthält LLM-as-Judge Standard-Metriken

**Defizite:**

1. **Keine zentrale Schema-Integration:**
   - Schema-Informationen sind hardcodiert im Prompt
   - Änderungen am zentralen Schema werden nicht automatisch übernommen
   - Inkonsistenzen zwischen AI-Prompt und tatsächlichem Schema möglich

2. **Fehlende Mapping-Beispiele:**
   - Keine konkreten Beispiele für CSV-Dateien
   - Keine Beispiele für JSONL-Format
   - Keine Beispiele für verschachtelte JSON-Strukturen
   - Keine Beispiele für OpenAI/LMSYS-Formate

3. **Keine Preset-Kenntnis:**
   - AI weiß nichts über verfügbare UI-Presets
   - Kann nicht empfehlen wann Standard- vs Custom-Config verwendet werden sollte

4. **Unvollständige Zielformat-Beschreibung:**
   - Vereinfachte Beispiele ohne alle Pflichtfelder
   - Keine Erklärung der Metadaten-Struktur

### 1.3 Datenfluss (aktuell)

```
Upload → DataParser → detected_structure → AIAnalyzer → AI Response
                                               ↑
                                        Hardcoded Prompts
                                        (Keine Schema-Integration)
```

---

## 2. Konzept: Verbesserungen

### 2.1 Zentrale Schema-Integration

**Ziel:** AI Prompt bezieht Schema-Informationen aus zentralem Service.

**Implementierung:**

```python
# app/services/evaluation/schema_export_service.py (NEU)

from schemas.evaluation_data_schemas import (
    EvaluationType, ContentType, SourceType, RankingMode, LabelingMode,
    EvaluationData, Item, Reference, Bucket, Dimension, Scale, Category
)

class SchemaExportService:
    """Exportiert Schema-Definitionen für AI-Prompts."""

    @staticmethod
    def get_schema_for_ai_prompt() -> str:
        """Generiert Schema-Beschreibung für AI-Prompt."""
        return f"""
## LLARS EVALUATIONSTYPEN (function_type_id)

{SchemaExportService._get_evaluation_types()}

## ZIELFORMAT: EvaluationData Schema

{SchemaExportService._get_target_format()}

## KONFIGURATIONSOPTIONEN

{SchemaExportService._get_config_options()}
"""

    @staticmethod
    def _get_evaluation_types() -> str:
        """Evaluation Types mit IDs und Beschreibungen."""
        types = {
            EvaluationType.RANKING: (1, "Items sortieren/kategorisieren (Gut/Mittel/Schlecht)"),
            EvaluationType.RATING: (2, "Multi-dimensionales Rating (LLM-as-Judge Metriken)"),
            EvaluationType.MAIL_RATING: (3, "E-Mail-Beratungsverläufe bewerten (LLARS-spezifisch)"),
            EvaluationType.COMPARISON: (4, "Items paarweise vergleichen (A vs B)"),
            EvaluationType.AUTHENTICITY: (5, "Echt/Fake erkennen (Mensch vs KI)"),
            EvaluationType.LABELING: (7, "Kategorien zuweisen (binär, multi-class)")
        }
        return "\n".join([
            f"- {t.value} (ID={id}): {desc}"
            for t, (id, desc) in types.items()
        ])
```

### 2.2 Mapping-Beispiele nach Dateityp

**Neuer Abschnitt im AI-Prompt:**

```
## DATEI-FORMAT MAPPING-BEISPIELE

### CSV-Dateien
Eingabe:
```csv
id,question,answer_a,answer_b,model_a,model_b
1,"Was ist Python?","Python ist...","Python ist eine...","gpt-4","claude-3"
```

Mapping:
- Erkennung: Spalten `answer_a`/`answer_b` oder `text_a`/`text_b` → **comparison**
- Mapping: id→item_id, question→reference.content, answer_a→items[0].content, answer_b→items[1].content

### JSON-Dateien
Eingabe:
```json
{
  "metadata": {"source": "study_xyz"},
  "items": [
    {"id": "1", "messages": [{"role": "user", "content": "..."}]}
  ]
}
```

Mapping:
- Erkennung: `messages` Array mit `role`/`content` → **conversation**
- Mapping: items[].messages→conversation, items[].id→item_id

### JSONL-Dateien (eine JSON pro Zeile)
```jsonl
{"id":"1","prompt":"...","response":"...","model":"gpt-4"}
{"id":"2","prompt":"...","response":"...","model":"claude-3"}
```

Mapping:
- Erkennung: Einzelne Texte mit prompt/response → **rating** oder **ranking**
- Mapping: prompt→reference.content, response→items[0].content

### OpenAI/LMSYS Format
```json
{"conversation_a":[{"role":"user","content":"Hi"},{"role":"assistant","content":"Hello!"}],
 "conversation_b":[{"role":"user","content":"Hi"},{"role":"assistant","content":"Hi there!"}],
 "model_a":"gpt-4","model_b":"claude-3","winner":"model_a"}
```

Mapping:
- Erkennung: Zwei Konversationen mit winner → **comparison**
- Ground-Truth: winner Feld kann als Label verwendet werden
```

### 2.3 Preset-Integration

**Neuer Abschnitt im AI-Prompt:**

```
## VERFÜGBARE KONFIGURATIONSPRESETS

Nutze Standard-Presets wenn die Daten gut passen. Custom nur bei besonderen Anforderungen.

### Rating Presets
- `llm-judge-standard`: 4 Dimensionen (Kohärenz, Flüssigkeit, Relevanz, Konsistenz) - DEFAULT
- `summeval`: 7 Dimensionen mit gemischten Skalen
- `response-quality`: Für LLM-Antworten (Hilfsbereitschaft, Genauigkeit, Vollständigkeit, Klarheit)
- `news-article`: Für Nachrichtenartikel (Genauigkeit, Objektivität, Vollständigkeit, Lesbarkeit)

Wann Custom? Wenn domänenspezifische Dimensionen nötig sind (z.B. medizinische Texte, Rechtstexte)

### Ranking Presets
- `buckets-3`: Gut/Mittel/Schlecht - DEFAULT
- `buckets-5`: Sehr gut bis Sehr schlecht (feinere Abstufung)
- `priority`: Items nach Priorität sortieren
- `relevance`: Nach Relevanz sortieren (Ties erlaubt)

### Labeling Presets
- `binary-authentic`: Fake/Echt (mit Unsicher-Option) - für Authentizität
- `binary-sentiment`: Positiv/Negativ (mit Neutral)
- `sentiment-3`: Positiv/Neutral/Negativ
- `topic-multilabel`: Mehrere Themen pro Item

### Comparison Presets
- `pairwise`: A vs B - welches ist besser? - DEFAULT
- `pairwise-confidence`: Mit Konfidenz-Bewertung
- `multicriteria`: Vergleich nach mehreren Kriterien
```

### 2.4 Entscheidungsbaum für Evaluationstyp

```
## EVALUATIONSTYP-ENTSCHEIDUNG

┌─ Haben die Daten zwei Antwort-Versionen pro Item?
│  ├─ JA (answer_a/answer_b, text_a/text_b, conversation_a/b)
│  │  └─ → **comparison**
│  │
│  └─ NEIN
│     ├─ Gibt es Label-Felder (is_fake, sentiment, category)?
│     │  ├─ JA, binär (fake/real, human/ai)
│     │  │  └─ → **authenticity** (wenn Echt/Fake) oder **labeling**
│     │  │
│     │  └─ JA, mehrklassig
│     │     └─ → **labeling**
│     │
│     └─ Sollen Items sortiert/kategorisiert werden?
│        ├─ JA, in Qualitätskategorien
│        │  └─ → **ranking**
│        │
│        └─ NEIN, einzeln bewerten
│           ├─ E-Mail/Chat-Konversationen (Beratung)?
│           │  └─ → **mail_rating**
│           │
│           └─ Einzelne Texte/Antworten
│              └─ → **rating**
```

### 2.5 Vollständiges Zielformat

```
## LLARS EVALUATIONDATA SCHEMA (Vollständig)

{
  "evaluation_type": "rating|ranking|labeling|comparison|mail_rating|authenticity",
  "config": {
    // Rating/Mail_Rating Config
    "scale": {"min": 1, "max": 5, "step": 1, "type": "likert"},
    "dimensions": [
      {"id": "coherence", "name": {"de": "Kohärenz"}, "weight": 0.25}
    ],

    // Ranking Config
    "buckets": [
      {"id": 1, "name": {"de": "Gut"}, "color": "#98d4bb"}
    ],
    "mode": "bucket|ordered|tournament",

    // Labeling/Authenticity Config
    "categories": [
      {"id": "authentic", "name": {"de": "Echt"}, "color": "#98d4bb"}
    ],
    "mode": "single|multi",

    // Comparison Config
    "criteria": [{"id": "overall", "name": {"de": "Gesamt"}}]
  },

  // Pro Item
  "reference": {
    "type": "text|conversation|document",
    "content": "..." // oder Array für conversation
  },
  "items": [
    {
      "id": "item-1",
      "content": "...",
      "source": {"type": "llm|human|system", "name": "gpt-4"},
      "group": "Summary" // optional, für Feature-Types
    }
  ],
  "metadata": {
    "original_id": "...",
    "filename": "...",
    "custom_fields": {}
  }
}
```

---

## 3. Implementierungsplan

### Phase 1: Schema Export Service (Backend)
1. Neuen Service `schema_export_service.py` erstellen
2. Methoden für AI-Prompt-taugliche Schema-Exporte
3. Integration in `field_prompt_service.py`

### Phase 2: AI Prompt Aktualisierung
1. Mapping-Beispiele für alle Dateitypen hinzufügen
2. Entscheidungsbaum für Evaluationstyp
3. Preset-Empfehlungen integrieren

### Phase 3: Dynamic Schema Injection
1. API Endpoint `/api/ai-assist/schema` für aktuelle Schema-Daten
2. Frontend lädt Schema beim Wizard-Start
3. Schema wird dynamisch in AI-Prompt injiziert

### Phase 4: Preset-Empfehlungen
1. AI analysiert Daten und empfiehlt passendes Preset
2. "Standard" vs "Custom" Empfehlung basierend auf Datenstruktur
3. Erklärung warum bestimmtes Preset gewählt wurde

---

## 4. Änderungsliste (Konkret)

### 4.1 Neue Dateien

| Datei | Beschreibung |
|-------|--------------|
| `app/services/evaluation/schema_export_service.py` | Schema-Export für AI-Prompts |
| `app/routes/ai_assist/schema_routes.py` | API für Schema-Daten |

### 4.2 Zu ändernde Dateien

| Datei | Änderungen |
|-------|------------|
| `field_prompt_service.py` | DEFAULT_FIELD_PROMPTS["scenario.analysis"] komplett überarbeiten |
| `ai_analyzer.py` | Schema aus zentrale Service importieren statt hardcoden |
| `scenario_analysis_routes.py` | Schema-Daten in Kontext einfügen |

### 4.3 AI Prompt Struktur (Neu)

```
[System Prompt]
├── 1. Rolle & Aufgabe
├── 2. Evaluationstypen (aus SchemaExportService)
├── 3. Entscheidungsbaum für Typ-Auswahl
├── 4. Mapping-Beispiele nach Dateiformat
│   ├── CSV
│   ├── JSON
│   ├── JSONL
│   └── OpenAI/LMSYS
├── 5. Verfügbare Presets (aus evaluationPresets.js)
│   ├── Wann Standard-Preset?
│   └── Wann Custom-Config?
├── 6. Zielformat EvaluationData (aus Schema)
└── 7. Ausgabeformat JSON

[User Prompt]
├── Dateiname(n)
├── Erkannte Felder
├── Sample-Daten
└── User-Hinweis (optional)
```

---

## 5. Priorisierung & Implementierungsstatus

| Priorität | Task | Aufwand | Impact | Status |
|-----------|------|---------|--------|--------|
| 1 | Mapping-Beispiele im Prompt | Niedrig | Hoch | ✅ DONE |
| 2 | Entscheidungsbaum für Typ | Niedrig | Hoch | ✅ DONE |
| 3 | Preset-Empfehlungen | Mittel | Mittel | ✅ DONE |
| 4 | Schema Export Service | Mittel | Mittel | ✅ DONE |
| 5 | Dynamische Schema-Injection | Hoch | Niedrig | ⏳ Future |

**Implementiert am:** 2026-01-28

---

## 6. Beispiel: Verbesserter AI-Prompt (Ausschnitt)

```
Du bist ein Experte für Evaluations-Studiendesign. Analysiere die bereitgestellten Daten
und generiere Vorschläge für ein LLARS-Evaluationsszenario.

## EVALUATIONSTYPEN

| Typ | ID | Beschreibung | Erkennung |
|-----|---| -----------|-----------|
| ranking | 1 | Items sortieren/kategorisieren | Rang/Position, oder gruppierte Items |
| rating | 2 | Multi-dimensionales Rating | Einzelne Texte mit Qualitätsbewertung |
| mail_rating | 3 | E-Mail-Beratung bewerten | subject + mehrteilige Konversationen |
| comparison | 4 | A vs B Vergleich | answer_a/answer_b, text_a/text_b |
| authenticity | 5 | Echt/Fake erkennen | is_fake, synthetic, human/ai Labels |
| labeling | 7 | Kategorien zuweisen | category, label, sentiment Felder |

## DATEIFORMAT-ERKENNUNG

### CSV mit Vergleichsdaten
```csv
id,question,answer_a,answer_b
1,"Was ist X?","A sagt...","B sagt..."
```
→ **comparison** (zwei Antworten pro Frage)

### JSON mit Konversationen
```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```
→ **mail_rating** (wenn Beratungskontext) oder **rating** (wenn einzelne Q&A)

### JSONL mit Labels
```jsonl
{"text": "...", "is_human": true}
{"text": "...", "is_human": false}
```
→ **authenticity** (binäre Klassifikation Mensch/KI)

## PRESET-EMPFEHLUNGEN

Nutze Standard-Presets wenn möglich:
- **rating**: `llm-judge-standard` für allgemeine Textqualität
- **ranking**: `buckets-3` für Gut/Mittel/Schlecht Sortierung
- **comparison**: `pairwise` für einfache A vs B Vergleiche
- **labeling**: `binary-authentic` für Fake/Echt Erkennung

Nutze Custom-Config wenn:
- Domänenspezifische Dimensionen benötigt (Medizin, Recht, etc.)
- Ungewöhnliche Skalengrößen (z.B. 0-100 statt 1-5)
- Spezielle Kategorien die nicht in Presets vorhanden sind

[... Rest des Prompts ...]
```
