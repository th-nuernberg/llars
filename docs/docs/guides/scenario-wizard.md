# Szenario Wizard

**Version:** 2.0 | **Stand:** Januar 2026

Der Szenario Wizard ist ein mehrstufiger Assistent zur Erstellung von Evaluations-Szenarien in LLARS. Er unterstützt Forscher dabei, Daten hochzuladen, den passenden Evaluierungstyp automatisch zu erkennen und Teams zusammenzustellen.

---

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│  Schritt 1    Schritt 2    Schritt 3    Schritt 4    Schritt 5     │
│  [Daten]  →   [Typ]    →   [Config]  →   [Team]   →  [Fertig]      │
└─────────────────────────────────────────────────────────────────────┘
```

| Schritt | Beschreibung |
|---------|--------------|
| 1. Daten hochladen | Dateien importieren, automatische Analyse |
| 2. Aufgabentyp | Evaluationstyp bestätigen oder ändern |
| 3. Konfiguration | Dimensionen, Skalen, Buckets anpassen |
| 4. Team | Evaluatoren und LLM-Modelle einladen |
| 5. Zusammenfassung | Überprüfen und erstellen |

---

## Schritt 1: Daten hochladen

### Unterstützte Formate

| Format | Beschreibung | Beispiel |
|--------|--------------|----------|
| **CSV/TSV** | Komma- oder Tab-getrennte Werte | `data.csv` / `data.tsv` |
| **JSON** | Array von Objekten | `[{...}, {...}]` |
| **JSONL/NDJSON** | Ein Objekt pro Zeile | `data.jsonl` |
| **XLSX** | Excel-Datei | `data.xlsx` |

### Datenformate

LLARS unterstützt zwei Datenformate für Ranking-Szenarien:

#### Wide Format (Standard)

Jede Zeile enthält alle Varianten in separaten Spalten:

```csv
source_text,summary_a,summary_b,summary_c
"Der Original-Artikel...","GPT-4 Summary","Claude Summary","Llama Summary"
```

#### Long Format (Neu!)

Gleiche ID erscheint mehrfach mit verschiedenen Varianten:

```csv
chat_id,llm_name,output,source
8,gpt-4,"GPT-4 Ausgabe...","Original-Text..."
8,claude-3,"Claude Ausgabe...","Original-Text..."
8,llama-3,"Llama Ausgabe...","Original-Text..."
```

!!! info "Automatische Erkennung"
    LLARS erkennt Long-Format automatisch und transformiert die Daten in das LLARS-Format.

### Upload-Bereich

```
┌─────────────────────────────────────────────┐
│  📁 Dateien hier ablegen oder auswählen     │
│                                             │
│  Unterstützte Formate: JSON, JSONL, CSV/TSV, │
│  XLSX                                       │
└─────────────────────────────────────────────┘
```

Nach dem Upload startet automatisch die **Datenanalyse**.

---

## Automatische Typ-Erkennung

### Zweistufiges System

LLARS nutzt ein intelligentes zweistufiges System zur Typ-Erkennung:

```
┌──────────────────┐      definit      ┌─────────────────┐
│  SchemaDetector  │  ───────────────► │  Typ erkannt!   │
│  (deterministisch)│                   └─────────────────┘
└────────┬─────────┘
         │ unsicher
         ▼
┌──────────────────┐
│   AI-Analyse     │  ───────────────► Typ + Konfiguration
│   (LLM-basiert)  │
└──────────────────┘
```

### 1. SchemaDetector (Deterministisch)

Der SchemaDetector analysiert die Feldnamen und erkennt Muster:

| Evaluationstyp | Erkannte Felder | Priorität |
|----------------|-----------------|-----------|
| **Authenticity** | `is_human`, `is_fake`, `synthetic`, `is_ai` | 1 (höchste) |
| **Comparison** | `response_a` + `response_b`, `winner` | 2 |
| **Ranking** | `summary_a`, `summary_b`, `summary_c` | 3 |
| **Mail Rating** | `messages[]` Array (ohne `is_human`) | 4 |
| **Rating** | `question` + `response`, `prompt` + `completion` | 5 |
| **Labeling** | `category`, `label`, `sentiment` + Content | 6 |

!!! tip "Schema-basierte Erkennung"
    Wenn der SchemaDetector den Typ **definit** erkennt, wird das UI mit einem grünen Badge "Automatisch erkannt" markiert.

### 2. AI-Analyse (Fallback)

Wenn der SchemaDetector unsicher ist, analysiert ein LLM die Daten:

- Erkennt komplexere Muster
- Schlägt passende Presets vor
- Generiert Szenario-Namen und Beschreibung

---

## Long-Format Transformation (Neu!)

### Was ist Long-Format?

Long-Format Daten haben dieselbe Gruppen-ID mehrfach mit verschiedenen Varianten:

```
┌─────────────────────────────────────────────────────────────────┐
│ chat_id │ llm_name        │ output              │ source        │
├─────────┼─────────────────┼─────────────────────┼───────────────┤
│ 8       │ gpt-4           │ "GPT-4 Antwort..."  │ "Original..." │
│ 8       │ claude-3        │ "Claude Antwort..." │ "Original..." │
│ 8       │ llama-3         │ "Llama Antwort..."  │ "Original..." │
│ 9       │ gpt-4           │ "GPT-4 Antwort..."  │ "Original..." │
│ 9       │ claude-3        │ "Claude Antwort..." │ "Original..." │
└─────────────────────────────────────────────────────────────────┘
```

### Automatisches Field Mapping

LLARS generiert automatisch ein Mapping für Long-Format Daten:

| Mapping-Feld | Beschreibung | Beispiel |
|--------------|--------------|----------|
| `grouping_field` | Gruppiert zusammengehörige Zeilen | `chat_id` |
| `variant_field` | Identifiziert die Variante | `llm_name` |
| `output_field` | Enthält den generierten Content | `output` |
| `reference_field` | Enthält die Referenz/Quelle | `source` |

### Transformation

Die Daten werden automatisch transformiert:

```
Vorher: 30 Zeilen (Long-Format)
        ↓ Transformation
Nachher: 3 Ranking-Items (je 10 Varianten)
```

**Ergebnis-Struktur:**

```json
{
  "id": "group_8",
  "reference": {
    "type": "text",
    "content": "Original-Text..."
  },
  "items": [
    { "id": "item_1", "label": "gpt-4", "content": "GPT-4 Antwort..." },
    { "id": "item_2", "label": "claude-3", "content": "Claude Antwort..." },
    { "id": "item_3", "label": "llama-3", "content": "Llama Antwort..." }
  ]
}
```

---

## Schritt 2: Aufgabentyp

### Die 6 Evaluationstypen

=== "Rating"

    **Multi-dimensionale Bewertung (LLM Evaluator)**

    - Likert-Skalen pro Dimension
    - Gewichtete Gesamtbewertung
    - Standard: Kohärenz, Flüssigkeit, Relevanz, Konsistenz

    **Anwendungsfälle:** Text-Qualität, Zusammenfassungen, LLM-Outputs

=== "Ranking"

    **Items in Qualitätsbuckets sortieren**

    - Drag & Drop Interface
    - Konfigurierbare Buckets (z.B. Gut/Mittel/Schlecht)
    - Ties erlaubt

    **Anwendungsfälle:** Summary-Qualität, Priorisierung, LLM-Vergleiche

=== "Labeling"

    **Kategorien zuweisen**

    - Single-Label oder Multi-Label
    - Konfigurierbare Kategorien
    - Optional: "Unsicher"-Option

    **Anwendungsfälle:** Themen-Klassifikation, Sentiment-Analyse

=== "Comparison"

    **Paarweiser A/B-Vergleich**

    - Zwei Optionen nebeneinander
    - Winner auswählen
    - Optional: Tie möglich

    **Anwendungsfälle:** Modell-Vergleiche, Präferenz-Studien

=== "Authenticity"

    **Echt/Fake-Klassifikation**

    - Binäre Entscheidung
    - Optional: Konfidenz-Skala
    - LLARS-spezifisch (Psychosoziale Beratung)

    **Anwendungsfälle:** KI-generierte Texte erkennen

=== "Mail Rating"

    **E-Mail-Verläufe bewerten**

    - Konversation wird angezeigt
    - Multi-dimensionale Bewertung
    - LLARS-spezifisch (Beratungs-E-Mails)

    **Anwendungsfälle:** Beratungsqualität, Antwortqualität

### Typ-Auswahl

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Rating  │  │ Ranking  │  │ Labeling │  │Comparison│
│    ⭐    │  │    ↕️    │  │    🏷️    │  │    ⚖️    │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
     │
     └── ✓ Automatisch erkannt (Schema Detection)
```

---

## Schritt 3: Konfiguration

### Presets

Jeder Evaluationstyp hat vorkonfigurierte Presets:

#### Rating Presets

| Preset | Dimensionen/Typ | Skala | Beschreibung |
|--------|-----------------|-------|--------------|
| `llm-judge-standard` | Kohärenz, Flüssigkeit, Relevanz, Konsistenz | 1-5 | Standard für LLM Evaluator |
| `summeval` | 7 Dimensionen (Mixed Scales) | variabel | Demo mit unterschiedlichen Skalengrößen |
| `response-quality` | Hilfsbereitschaft, Genauigkeit, Vollständigkeit, Klarheit | 1-5 | Chat-Antworten |
| `news-article` | Genauigkeit, Objektivität, Vollständigkeit, Lesbarkeit | 1-5 | Nachrichtenartikel |
| `text-quality-3dim` | Inhalt, Sprache, Struktur | 1-5 | Kompakte 3-Dimensionen |
| `likert-5` | Einzeldimension | 1-5 | Standard Likert-Skala |
| `likert-7` | Einzeldimension | 1-7 | Feinere Abstufung |
| `stars-5` | Sterne | 1-5 | Klassische Sternebewertung |
| `stars-10` | Numerisch | 1-10 | 10-Punkte Skala |
| `percentage` | Slider | 0-100 | Prozent-Bewertung |

#### Ranking Presets

| Preset | Buckets/Typ | Beschreibung |
|--------|-------------|--------------|
| `buckets-3` | Gut, Mittel, Schlecht | Standard 3-Kategorien |
| `buckets-5` | Sehr gut bis Sehr schlecht | Feinere Abstufung |
| `priority` | Geordnet | Nach Priorität sortieren |
| `relevance` | Geordnet | Nach Relevanz sortieren |

#### Labeling Presets

| Preset | Kategorien | Beschreibung |
|--------|------------|--------------|
| `binary-authentic` | Echt, Fake | Authentizitätsprüfung |
| `binary-sentiment` | Positiv, Negativ | Binäre Sentiment-Analyse |
| `sentiment-3` | Positiv, Neutral, Negativ | 3-Klassen Sentiment |
| `topic-multilabel` | Konfigurierbar | Mehrere Themen pro Item |

#### Comparison Presets

| Preset | Typ | Beschreibung |
|--------|-----|--------------|
| `pairwise` | A vs B | Einfacher paarweiser Vergleich |
| `pairwise-confidence` | A vs B + Konfidenz | Mit Sicherheitsbewertung |
| `multicriteria` | Mehrere Kriterien | Relevanz, Qualität, Klarheit |
| `tournament` | Eliminierung | Turnier-Format

### Konfiguration anpassen

Je nach Typ können angepasst werden:

- **Dimensionen** (Rating): Namen, Beschreibungen, Gewichtung
- **Skala** (Rating): Minimum, Maximum, Schrittweite, Labels
- **Buckets** (Ranking): Namen, Farben, Reihenfolge
- **Kategorien** (Labeling): Namen, Farben, Multi-Select

---

## Schritt 4: Team zusammenstellen

### Menschliche Evaluatoren

Benutzer können über die Nutzersuche eingeladen werden (Name/Username + E-Mail):

| Rolle | Beschreibung |
|-------|--------------|
| **EVALUATOR** | Bewertet Items und kann interagieren |
| **VIEWER** | Nur lesend, keine Bewertungen |

### LLM-Modelle

Verfügbare LLMs werden dynamisch aus der Systemkonfiguration geladen:

- **System-Modelle** (admin-konfiguriert)
- **Eigene/geteilte Provider** (vom Nutzer oder Team bereitgestellt)

!!! info "LLM-Evaluation"
    Wenn LLM-Evaluation aktiviert ist, bewerten ausgewählte LLMs nach der Szenario-Erstellung automatisch alle Items basierend auf den konfigurierten Dimensionen.

---

## Schritt 5: Zusammenfassung

Überblick über alle Einstellungen:

```
┌─────────────────────────────────────────────────────────────┐
│  Zusammenfassung                                            │
├─────────────────────────────────────────────────────────────┤
│  Name:        Zusammenfassungs-Qualität Studie              │
│  Typ:         Ranking (3 Buckets)                           │
│  Items:       150                                           │
│  Team:        5 Evaluatoren + 2 LLMs                        │
│  Verteilung:  Alle bewerten alle                            │
├─────────────────────────────────────────────────────────────┤
│                           [Szenario erstellen]              │
└─────────────────────────────────────────────────────────────┘
```

Nach dem Erstellen:

- Szenario wird angelegt
- Einladungen werden verschickt
- Optional: LLM-Evaluation startet sofort

---

## Beispiel-Datenformate

### Rating-Daten

```json
[
  {
    "question": "Was ist die Hauptstadt von Frankreich?",
    "response": "Die Hauptstadt von Frankreich ist Paris."
  }
]
```

### Ranking-Daten (Wide Format)

```json
[
  {
    "source_text": "Der Original-Artikel über Klimawandel...",
    "summary_a": "GPT-4 Zusammenfassung...",
    "summary_b": "Claude Zusammenfassung...",
    "summary_c": "Llama Zusammenfassung..."
  }
]
```

### Ranking-Daten (Long Format)

```csv
doc_id,model,summary,source_text
DOC001,gpt-4,"GPT-4 Zusammenfassung...","Original-Artikel..."
DOC001,claude-3,"Claude Zusammenfassung...","Original-Artikel..."
DOC001,llama-3,"Llama Zusammenfassung...","Original-Artikel..."
```

### Labeling-Daten

```json
[
  {
    "text": "Das Produkt ist fantastisch!",
    "ground_truth": "positive"
  }
]
```

### Comparison-Daten

```json
[
  {
    "prompt": "Erkläre Quantencomputing",
    "response_a": "GPT-4 Antwort...",
    "response_b": "Claude Antwort...",
    "winner": "a"
  }
]
```

### Authenticity-Daten

```json
[
  {
    "text": "Der Text zur Echtheitsprüfung...",
    "is_human": true
  }
]
```

---

## API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/scenarios` | POST | Szenario erstellen |
| `/api/ai-assist/analyze-scenario-data/stream` | POST | Streaming AI-Analyse |
| `/api/ai-assist/transform-long-format` | POST | Long-Format transformieren |

---

## Berechtigungen

| Permission | Beschreibung |
|------------|--------------|
| `data:manage_scenarios` | Szenarien erstellen/bearbeiten |
| `data:import` | Daten importieren |

---

## Siehe auch

- [Szenario Manager](scenario-manager.md) - Szenarien verwalten
- [Evaluation](evaluation.md) - Bewertungen durchführen
- [Evaluation Datenformate](../entwickler/evaluation-datenformate.md) - Technische Referenz
