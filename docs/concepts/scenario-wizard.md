# Szenario Wizard

**Status:** Produktiv | **Stand:** Januar 2026

## Übersicht

Der Szenario Wizard ist ein mehrstufiger Assistent zur Erstellung von Evaluations-Szenarien in LLARS. Er unterstützt Forscher dabei, Daten hochzuladen, den passenden Evaluierungstyp zu wählen und Teams zusammenzustellen.

## Evaluierungstypen

LLARS unterstützt 4 generalisierte Evaluierungstypen:

| Typ | Beschreibung | Anwendungsfälle | Presets |
|-----|--------------|-----------------|---------|
| **rating** | Bewertung auf einer Skala | Qualitätsbewertung, Sentiment-Score, Empfehlungswahrscheinlichkeit | Likert-5, Likert-7, Sterne (1-5), Prozent |
| **ranking** | Items sortieren oder kategorisieren | Priorisierung, Qualitätseinteilung, Relevanz-Sortierung | 3 Kategorien, 5 Kategorien, Priorität, Relevanz |
| **labeling** | Kategorien zuweisen | Klassifikation, Themenerkennung, Authentizitätsprüfung | Binär (Echt/Fake), Multi-Class, Multi-Label |
| **comparison** | Items paarweise vergleichen | A/B-Vergleiche, Präferenz-Studien, Modell-Vergleiche | Paarweise, Mit Konfidenz, Multi-Kriterien |

> **Hinweis:** Der frühere Typ `mail_rating` wurde entfernt. Alle Bewertungsaufgaben nutzen nun den generalisierten `rating`-Typ mit konfigurierbaren Dimensionen.

## Wizard-Schritte

### Schritt 1: Daten hochladen

- **Unterstützte Formate:** JSON, CSV, XLSX
- **Drag & Drop** oder Dateiauswahl
- **AI-Analyse:** Automatische Erkennung des Evaluierungstyps
- **Vorschau:** Erste Datensätze werden angezeigt

```
┌─────────────────────────────────────────────┐
│  📁 Dateien hier ablegen oder auswählen     │
│                                             │
│  Unterstützte Formate: JSON, CSV, XLSX      │
└─────────────────────────────────────────────┘
```

### Schritt 2: Aufgabentyp definieren

- **AI-Vorschlag:** Basierend auf Datenanalyse
- **Manuelle Auswahl:** 4 Typen zur Auswahl
- **Beschreibung:** Erklärt jeden Typ

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Rating  │  │ Ranking  │  │ Labeling │  │Comparison│
│    ⭐    │  │    ↕️    │  │    🏷️    │  │    ⚖️    │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### Schritt 3: Konfiguration

Je nach gewähltem Typ:

**Rating:**
- Skala (min, max, Schrittweite)
- Preset auswählen (Likert-5, Sterne, etc.)
- Labels für Skalenwerte

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
  labeling: 5
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

## Siehe auch

- [Szenario Manager Testing](./scenario-manager-testing.md)
- [Datenbank-Schema](../docs/entwickler/datenbank-schema.md)
- [Permission System](../docs/guides/permission-system.md)
