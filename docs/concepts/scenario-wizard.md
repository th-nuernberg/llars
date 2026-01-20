# Szenario Wizard

**Status:** Produktiv | **Stand:** Januar 2026

## Übersicht

Der Szenario Wizard ist ein mehrstufiger Assistent zur Erstellung von Evaluations-Szenarien in LLARS. Er unterstützt Forscher dabei, Daten hochzuladen, den passenden Evaluierungstyp zu wählen und Teams zusammenzustellen.

## Evaluierungstypen

LLARS unterstützt 4 generalisierte Evaluierungstypen sowie 2 LLARS-spezifische Typen:

| Typ | Beschreibung | Anwendungsfälle | Presets |
|-----|--------------|-----------------|---------|
| **rating** | Multi-dimensionales Rating (LLM-as-Judge) | Text-Qualität, LLM-Evaluation, Zusammenfassungen | LLM-Judge Standard, SummEval, Antwort-Qualität, Nachrichtenartikel |
| **ranking** | Items sortieren oder kategorisieren | Priorisierung, Qualitätseinteilung, Relevanz-Sortierung | 3 Kategorien, 5 Kategorien, Priorität, Relevanz |
| **labeling** | Kategorien zuweisen | Klassifikation, Themenerkennung, Authentizitätsprüfung | Binär (Echt/Fake), Multi-Class, Multi-Label |
| **comparison** | Items paarweise vergleichen | A/B-Vergleiche, Präferenz-Studien, Modell-Vergleiche | Paarweise, Mit Konfidenz, Multi-Kriterien |

LLARS-spezifische Typen (Psychosoziale Online-Beratung):

| Typ | Beschreibung | Basistyp | Presets |
|-----|--------------|----------|---------|
| **mail_rating** | Mehrdimensionale Bewertung von Beratungs-E-Mails | rating | Beratungsqualität, Antwortqualität, Einfache Bewertung |
| **authenticity** | Erkennung von echten vs. gefälschten Nachrichten | labeling | Nachrichten-Echtheit, KI-Erkennung, Dringlichkeit |

> **Hinweis:** LLARS-spezifische Typen nutzen die generalisierten Basistypen (`mail_rating` → `rating`, `authenticity` → `labeling`).

## Wizard-Schritte

### Schritt 1: Daten hochladen

- **Unterstützte Formate:** JSON, CSV, XLSX
- **Drag & Drop** oder Dateiauswahl
- **AI-Analyse:** Automatische Erkennung des Evaluierungstyps
- **Vorschau:** Erste Datensätze werden angezeigt
- **Beispiele:** Ideales Datenformat im Tab **Datenformat** (neben Einladungen)

```
┌─────────────────────────────────────────────┐
│  📁 Dateien hier ablegen oder auswählen     │
│                                             │
│  Unterstützte Formate: JSON, CSV, XLSX      │
└─────────────────────────────────────────────┘
```

### Schritt 2: Aufgabentyp definieren

- **AI-Vorschlag:** Basierend auf Datenanalyse
- **Manuelle Auswahl:** 4 generalisierte + 2 LLARS-spezifische Typen
- **Beschreibung:** Erklärt jeden Typ

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Rating  │  │ Ranking  │  │ Labeling │  │Comparison│
│    ⭐    │  │    ↕️    │  │    🏷️    │  │    ⚖️    │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### Schritt 3: Konfiguration

Je nach gewähltem Typ:

**Rating (Multi-Dimensional):**
- **Typ:** Multi-Dimensional (LLM-as-Judge) oder klassisch (Likert, Sterne)
- **Dimensionen:** Kohärenz, Flüssigkeit, Relevanz, Konsistenz (anpassbar)
- **Skala:** min, max, Schrittweite (Standard: 1-5)
- **Gewichtung:** Jede Dimension hat ein Gewicht für die Gesamtbewertung
- **Presets:** LLM-Judge Standard, SummEval, Antwort-Qualität, Nachrichtenartikel

**Ranking:**
- Kategorie-Buckets definieren
- Reihenfolge vs. Kategorisierung
- Ties erlauben

**Labeling:**
- Kategorien definieren
- Multi-Label erlauben
- "Unsicher"-Option aktivieren

**Comparison:**
- Vergleichskriterien
- Tie erlauben
- Konfidenz-Skala aktivieren

**Verteilungs-Einstellungen:**
- `all`: Alle Evaluatoren bewerten alle Items
- `random`: Zufällige Verteilung
- `sequential`: Sequentielle Zuweisung

### Schritt 4: Team zusammenstellen

- **Menschliche Evaluatoren:** Benutzer einladen
- **LLM-Modelle:** Automatische Evaluation durch KI
- **Rollen:** EVALUATOR, RATER

### Schritt 5: Zusammenfassung

- Übersicht aller Einstellungen
- Szenario erstellen
- Optional: LLM-Evaluation sofort starten

## AI-Analyse

Der Wizard nutzt ein LLM zur Analyse hochgeladener Daten:

```python
# Prompt für Datenanalyse
SCENARIO_ANALYSIS_FIELD_KEY = "scenario.analysis"

# Analysiert:
# - Datenstruktur (Felder, Typen)
# - Anwendungsfall
# - Empfohlene Konfiguration
```

### Entscheidungshilfe im Prompt

Das LLM nutzt folgende Heuristiken:

| Datenmerkmal | Vorgeschlagener Typ |
|--------------|---------------------|
| Ground-Truth Labels | labeling |
| Paare zum Vergleichen | comparison |
| Items für Reihenfolge/Kategorien | ranking |
| Qualität/Eigenschaft bewerten | rating |

## Technische Details

### Frontend-Komponenten

```
ScenarioManager/
├── components/
│   ├── ScenarioWizard.vue          # Haupt-Wizard
│   ├── EvaluationConfigEditor.vue  # Typ-Konfiguration
│   └── config/
│       ├── RatingConfigEditor.vue
│       ├── RankingConfigEditor.vue
│       ├── LabelingConfigEditor.vue
│       ├── ComparisonConfigEditor.vue
│       └── EvaluationPreview.vue
├── config/
│   └── evaluationPresets.js        # Presets & Typen
└── composables/
    ├── useScenarioManager.js       # CRUD-Operationen
    └── useDataImport.js            # Daten-Import
```

### Backend-Endpunkte

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/scenarios` | POST | Szenario erstellen |
| `/api/ai-assist/analyze-scenario-data` | POST | AI-Analyse |
| `/api/import/upload` | POST | Datei hochladen |
| `/api/import/transform` | POST | Daten transformieren |

### Datenbank-Mapping

```javascript
// Frontend → Backend Typ-IDs
const ID_TYPE_MAP = {
  ranking: 1,
  rating: 2,
  comparison: 4,
  labeling: 7,
  mail_rating: 3,
  authenticity: 5
}
```

## Presets

### Rating Presets

| ID | Name | Skala | Beschreibung |
|----|------|-------|--------------|
| `likert-5` | Likert-5 | 1-5 | Standard 5-Punkte Likert |
| `likert-7` | Likert-7 | 1-7 | Feinere Abstufung |
| `stars-5` | 5-Sterne | 1-5 | Klassische Sternebewertung |
| `percentage` | Prozent | 0-100 | Slider 0-100% |

### Labeling Presets

| ID | Name | Kategorien | Beschreibung |
|----|------|------------|--------------|
| `binary-authentic` | Echt/Fake | 2 | Authentizitätsprüfung |
| `binary-sentiment` | Positiv/Negativ | 2 | Sentiment-Analyse |
| `sentiment-3` | 3-Klassen Sentiment | 3 | Mit Neutral |
| `topic-multilabel` | Themen-Tags | n | Multi-Label |

### Ranking Presets

| ID | Name | Buckets | Beschreibung |
|----|------|---------|--------------|
| `buckets-3` | 3 Kategorien | Gut/Mittel/Schlecht | Standard |
| `buckets-5` | 5 Kategorien | Sehr gut bis Sehr schlecht | Feiner |
| `priority` | Priorität | Sortiert | Reihenfolge |

### Comparison Presets

| ID | Name | Beschreibung |
|----|------|--------------|
| `pairwise` | Paarweiser Vergleich | A vs B |
| `pairwise-confidence` | Mit Konfidenz | + Sicherheitsbewertung |
| `multicriteria` | Multi-Kriterien | Mehrere Dimensionen |

### Mail-Rating Presets

| ID | Name | Beschreibung |
|----|------|--------------|
| `beratungsqualitaet` | Beratungsqualität | Mehrdimensionale Bewertung von Beratungs-E-Mails |
| `antwortqualitaet` | Antwortqualität | Bewertung der Qualität einzelner Beraterantworten |
| `einfach` | Einfache Bewertung | Schnelle Gesamtbewertung ohne Dimensionen |
| `custom` | Benutzerdefiniert | Eigene Bewertungsdimensionen definieren |

### Authenticity Presets

| ID | Name | Beschreibung |
|----|------|--------------|
| `nachricht-echtheit` | Nachrichten-Echtheit | Echte vs. gefälschte Beratungsnachrichten |
| `ki-generiert` | KI-Erkennung | KI-generiert vs. menschlich |
| `dringlichkeit` | Dringlichkeits-Einschätzung | Akut bis niedrig |
| `custom` | Benutzerdefiniert | Eigene Kategorien definieren |

## Lokalisierung

Der Wizard unterstützt DE und EN:

```json
// de.json
{
  "scenarioManager": {
    "wizard": {
      "step1": { "title": "Daten hochladen" },
      "step2": { "title": "Aufgabentyp wählen" },
      "step3": { "title": "Konfiguration" },
      "step4": { "title": "Team zusammenstellen" },
      "step5": { "title": "Zusammenfassung" }
    },
    "types": {
      "rating": "Rating",
      "ranking": "Ranking",
      "labeling": "Labeling",
      "comparison": "Vergleich"
    }
  }
}
```

## Berechtigungen

| Permission | Beschreibung |
|------------|--------------|
| `data:manage_scenarios` | Szenarien erstellen/bearbeiten |
| `feature:rating:view` | Ratings ansehen |
| `feature:rating:edit` | Ratings bearbeiten |

## Beispiel-Workflow

1. **Forscher öffnet Szenario Manager**
2. **Klickt "Neues Szenario"** → Wizard öffnet sich
3. **Lädt Sentiment-Datensatz hoch** (CSV mit Texten)
4. **AI analysiert** → Schlägt "labeling" mit "binary-sentiment" vor
5. **Forscher akzeptiert** oder wählt anderes Preset
6. **Konfiguriert Verteilung** (alle bewerten alle)
7. **Lädt Team ein** (3 Evaluatoren + GPT-4)
8. **Erstellt Szenario** → Evaluation startet

## Datenformate für Import

### Rating-Daten

```json
[
  {
    "id": "1",
    "text": "Der zu bewertende Text...",
    "category": "Optional: Kategorie"
  }
]
```

### Ranking-Daten (z.B. Summary-Qualität)

**WICHTIG:** Bei Ranking-Szenarien wie Summary-Qualität werden:
- Der **Quelltext** als Kontext angezeigt (rechtes Panel)
- Die **zu rankenden Items** (z.B. Summaries) als Features gespeichert (linkes Panel)

```json
[
  {
    "subject": "Summary Ranking: Artikeltitel",
    "source_text": "Der vollständige Originaltext, der als Kontext dient...",
    "items": [
      { "id": "A", "content": "Erste Zusammenfassung..." },
      { "id": "B", "content": "Zweite Zusammenfassung..." },
      { "id": "C", "content": "Dritte Zusammenfassung..." }
    ],
    "task": "Ranken Sie die Zusammenfassungen nach Qualität"
  }
]
```

**Technische Umsetzung:**
- `source_text` → wird als **Message** gespeichert (Anzeige rechts)
- `items` → werden als **Features** gespeichert (Ranking links)
- Items werden NICHT als Messages gespeichert!

### Labeling-Daten

```json
[
  {
    "id": "1",
    "text": "Der zu klassifizierende Text...",
    "ground_truth": "kategorie_a"  // Optional für Accuracy-Berechnung
  }
]
```

### Comparison-Daten

```json
[
  {
    "id": "1",
    "context": "Optionaler Kontext...",
    "option_a": "Erste Option zum Vergleichen",
    "option_b": "Zweite Option zum Vergleichen",
    "task": "Welche Option ist besser?"
  }
]
```

### Authenticity-Daten

```json
[
  {
    "id": "1",
    "text": "Der Text zur Echtheitsprüfung...",
    "is_fake": true  // Ground Truth für Accuracy/F1-Berechnung
  }
]
```

## Siehe auch

- [Ranking-Szenarien im Detail](./ranking-scenarios.md)
- [Szenario Manager Testing](./scenario-manager-testing.md)
- [Datenbank-Schema](../docs/entwickler/datenbank-schema.md)
- [Permission System](../docs/guides/permission-system.md)
