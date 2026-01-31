# Evaluation Datenformate

**Version:** 1.0 | **Status:** Aktiv

Diese Dokumentation beschreibt die JSON-Schemas für alle 6 Evaluationstypen in LLARS. Nutze die **Minimalbeispiele** für einen schnellen Start und die **vollständigen Beispiele** als Referenz.

---

## Übersicht

| Typ | function_type_id | Verwendung |
|-----|------------------|------------|
| **Ranking** | 1 | Items in Qualitätsbuckets sortieren |
| **Rating** | 2 | Multi-dimensionale Bewertung (LLM Evaluator) |
| **Mail Rating** | 3 | E-Mail-Verläufe bewerten |
| **Comparison** | 4 | Paarweiser A/B-Vergleich |
| **Authenticity** | 5 | Echt/Fake-Klassifikation |
| **Labeling** | 7 | Kategorien zuweisen |

---

## Schnellstart: Minimalbeispiele

### Ranking (Minimal)

```json
{
  "schema_version": "1.0",
  "type": "ranking",
  "items": [
    { "id": "item_1", "label": "Text 1", "content": "Erster Text zum Ranken" },
    { "id": "item_2", "label": "Text 2", "content": "Zweiter Text zum Ranken" }
  ],
  "config": {
    "mode": "simple",
    "buckets": [
      { "id": "good", "label": { "de": "Gut", "en": "Good" }, "color": "#98d4bb", "order": 1 },
      { "id": "poor", "label": { "de": "Schlecht", "en": "Poor" }, "color": "#e8a087", "order": 2 }
    ],
    "allow_ties": true,
    "require_complete": true
  }
}
```

### Rating (Minimal)

```json
{
  "schema_version": "1.0",
  "type": "rating",
  "items": [
    { "id": "item_1", "label": "Zu bewertender Text", "content": "Der Text, der bewertet werden soll." }
  ],
  "config": {
    "scale": { "min": 1, "max": 5, "step": 1 },
    "dimensions": [
      { "id": "quality", "label": { "de": "Qualität", "en": "Quality" }, "weight": 1.0 }
    ],
    "show_overall": false
  }
}
```

### Comparison (Minimal)

```json
{
  "schema_version": "1.0",
  "type": "comparison",
  "items": [
    { "id": "item_a", "label": "Option A", "content": "Erste Option" },
    { "id": "item_b", "label": "Option B", "content": "Zweite Option" }
  ],
  "config": {
    "question": { "de": "Welche Option ist besser?", "en": "Which option is better?" },
    "allow_tie": true,
    "show_source": false
  }
}
```

### Labeling (Minimal)

```json
{
  "schema_version": "1.0",
  "type": "labeling",
  "items": [
    { "id": "item_1", "label": "Text", "content": "Zu klassifizierender Text" }
  ],
  "config": {
    "mode": "single",
    "labels": [
      { "id": "positive", "label": { "de": "Positiv", "en": "Positive" } },
      { "id": "negative", "label": { "de": "Negativ", "en": "Negative" } }
    ],
    "allow_other": false
  }
}
```

---

## Basis-Schema

Alle Evaluationstypen folgen dieser Grundstruktur:

```typescript
interface EvaluationData {
  schema_version: "1.0";
  type: "ranking" | "rating" | "mail_rating" | "comparison" | "authenticity" | "labeling";

  // Optional: Kontext/Referenz (rechts im Interface)
  reference?: Reference;

  // Items zum Bewerten (links im Interface)
  items: Item[];

  // Typ-spezifische Konfiguration
  config: TypeConfig;

  // Optional: Ground Truth für supervised evaluation
  ground_truth?: GroundTruth;
}

interface Reference {
  type: "text" | "conversation";
  label: string;                    // UI-Anzeigename
  content: string | Message[];      // Text oder Messages
  metadata?: Record<string, any>;
}

interface Item {
  id: string;                       // Technische ID (NICHT LLM-Namen!)
  label: string;                    // UI-Anzeigename
  source?: Source;
  content: string | ConversationContent;
}

interface Source {
  type: "human" | "llm" | "unknown";
  name?: string;                    // Bei LLM: Modellname
}

interface Message {
  role: string;                     // "Klient", "Berater", "User", "Assistant"
  content: string;
  timestamp?: string;               // ISO 8601
}
```

---

## 1. Ranking (function_type_id = 1)

**Zweck:** Items per Drag & Drop in Qualitätsbuckets einordnen.

**UI-Layout:**

- Links: Items zum Ranken
- Rechts: Referenz/Kontext (optional)

### Vollständiges Beispiel: Einfaches Ranking

```json
{
  "schema_version": "1.0",
  "type": "ranking",
  "reference": {
    "type": "text",
    "label": "Original-Artikel",
    "content": "Die Teilnehmer des Weltklimagipfels haben sich auf neue ambitionierte Ziele zur Reduktion von Treibhausgasen geeinigt. Die Industrieländer verpflichten sich zu einer Senkung der Emissionen um 55% bis 2030.",
    "metadata": {
      "source": "Reuters",
      "date": "2024-01-15"
    }
  },
  "items": [
    {
      "id": "item_1",
      "label": "Zusammenfassung 1",
      "source": { "type": "llm", "name": "mistralai/Mistral-Small-3.2" },
      "content": "Auf dem Weltklimagipfel einigten sich die Teilnehmer auf eine CO2-Reduktion von 55% bis 2030."
    },
    {
      "id": "item_2",
      "label": "Zusammenfassung 2",
      "source": { "type": "llm", "name": "openai/gpt-4" },
      "content": "Die Klimakonferenz beschloss neue Ziele zur Emissionsreduktion mit Fokus auf Industrieländer."
    },
    {
      "id": "item_3",
      "label": "Zusammenfassung 3",
      "source": { "type": "human" },
      "content": "Industrieländer einigen sich auf 55% weniger Emissionen bis 2030."
    }
  ],
  "config": {
    "mode": "simple",
    "buckets": [
      { "id": "good", "label": { "de": "Gut", "en": "Good" }, "color": "#98d4bb", "order": 1 },
      { "id": "moderate", "label": { "de": "Moderat", "en": "Moderate" }, "color": "#D1BC8A", "order": 2 },
      { "id": "poor", "label": { "de": "Schlecht", "en": "Poor" }, "color": "#e8a087", "order": 3 }
    ],
    "allow_ties": true,
    "require_complete": true
  }
}
```

### Multi-Group Ranking (Tabs)

Für paralleles Ranken mehrerer Kategorien:

```json
{
  "schema_version": "1.0",
  "type": "ranking",
  "reference": {
    "type": "text",
    "label": "Original-Artikel",
    "content": "Der Weltklimagipfel hat historische Beschlüsse gefasst..."
  },
  "items": [
    {
      "id": "item_1",
      "label": "Zusammenfassung 1",
      "group": "summaries",
      "source": { "type": "llm", "name": "gpt-4" },
      "content": "Klimagipfel einigt sich auf 55% CO2-Reduktion."
    },
    {
      "id": "item_2",
      "label": "Zusammenfassung 2",
      "group": "summaries",
      "source": { "type": "llm", "name": "claude-3" },
      "content": "Neue Klimaziele für Industrieländer beschlossen."
    },
    {
      "id": "item_3",
      "label": "Kommentar 1",
      "group": "comments",
      "source": { "type": "llm", "name": "gpt-4" },
      "content": "Ein wichtiger Schritt, aber Umsetzung bleibt abzuwarten."
    },
    {
      "id": "item_4",
      "label": "Kommentar 2",
      "group": "comments",
      "source": { "type": "llm", "name": "claude-3" },
      "content": "Historischer Moment für den Klimaschutz."
    }
  ],
  "config": {
    "mode": "multi_group",
    "groups": [
      {
        "id": "summaries",
        "label": { "de": "Zusammenfassungen", "en": "Summaries" },
        "buckets": [
          { "id": "accurate", "label": { "de": "Präzise", "en": "Accurate" }, "color": "#98d4bb", "order": 1 },
          { "id": "acceptable", "label": { "de": "Akzeptabel", "en": "Acceptable" }, "color": "#D1BC8A", "order": 2 },
          { "id": "inaccurate", "label": { "de": "Ungenau", "en": "Inaccurate" }, "color": "#e8a087", "order": 3 }
        ],
        "allow_ties": true
      },
      {
        "id": "comments",
        "label": { "de": "Kommentare", "en": "Comments" },
        "buckets": [
          { "id": "insightful", "label": { "de": "Einsichtsreich", "en": "Insightful" }, "color": "#88c4c8", "order": 1 },
          { "id": "balanced", "label": { "de": "Ausgewogen", "en": "Balanced" }, "color": "#b0ca97", "order": 2 },
          { "id": "biased", "label": { "de": "Einseitig", "en": "Biased" }, "color": "#e8a087", "order": 3 }
        ],
        "allow_ties": true
      }
    ],
    "require_complete": true
  }
}
```

---

## 2. Rating (function_type_id = 2)

**Zweck:** Multi-dimensionale Bewertung auf Likert-Skala (LLM Evaluator Metriken).

**UI-Layout:**

- Links: Dimensionen mit Likert-Skalen
- Rechts: Zu bewertender Text/Kontext

### Vollständiges Beispiel: SummEval-Style

```json
{
  "schema_version": "1.0",
  "type": "rating",
  "reference": {
    "type": "text",
    "label": "Quelldokument",
    "content": "Ein führendes Technologieunternehmen hat heute einen bedeutenden Fortschritt im Bereich der künstlichen Intelligenz vorgestellt. Der neue Algorithmus kann komplexe wissenschaftliche Probleme in Sekunden lösen, für die menschliche Forscher Wochen benötigen würden.",
    "metadata": { "source": "TechNews", "date": "2024-01-20" }
  },
  "items": [
    {
      "id": "item_1",
      "label": "Generierte Zusammenfassung",
      "source": { "type": "llm", "name": "mistralai/Mistral-Small-3.2" },
      "content": "Ein Tech-Konzern stellte eine KI vor, die wissenschaftliche Probleme lösen kann."
    }
  ],
  "config": {
    "scale": {
      "min": 1,
      "max": 5,
      "step": 1,
      "labels": {
        "1": { "de": "Sehr schlecht", "en": "Very poor" },
        "2": { "de": "Schlecht", "en": "Poor" },
        "3": { "de": "Akzeptabel", "en": "Acceptable" },
        "4": { "de": "Gut", "en": "Good" },
        "5": { "de": "Sehr gut", "en": "Very good" }
      }
    },
    "dimensions": [
      {
        "id": "coherence",
        "label": { "de": "Kohärenz", "en": "Coherence" },
        "description": { "de": "Logischer Aufbau und Zusammenhang", "en": "Logical structure and connection" },
        "weight": 0.25
      },
      {
        "id": "fluency",
        "label": { "de": "Flüssigkeit", "en": "Fluency" },
        "description": { "de": "Grammatik und Lesbarkeit", "en": "Grammar and readability" },
        "weight": 0.25
      },
      {
        "id": "relevance",
        "label": { "de": "Relevanz", "en": "Relevance" },
        "description": { "de": "Wichtige Informationen erfasst", "en": "Important information captured" },
        "weight": 0.25
      },
      {
        "id": "consistency",
        "label": { "de": "Konsistenz", "en": "Consistency" },
        "description": { "de": "Faktentreue zum Original", "en": "Factual accuracy to source" },
        "weight": 0.25
      }
    ],
    "show_overall": true
  }
}
```

### Beratungsantwort bewerten

```json
{
  "schema_version": "1.0",
  "type": "rating",
  "reference": {
    "type": "conversation",
    "label": "Beratungskontext",
    "content": [
      {
        "role": "Klient",
        "content": "Ich fühle mich überfordert bei der Arbeit.",
        "timestamp": "2024-01-15T09:00:00Z"
      },
      {
        "role": "Berater",
        "content": "Das tut mir leid. Seit wann haben Sie diese Gefühle?",
        "timestamp": "2024-01-15T09:05:00Z"
      }
    ]
  },
  "items": [
    {
      "id": "item_1",
      "label": "Nächste Beraterantwort",
      "source": { "type": "llm", "name": "openai/gpt-4" },
      "content": "Es klingt, als ob Sie unter großem Druck stehen. Können Sie mir mehr darüber erzählen?"
    }
  ],
  "config": {
    "scale": { "min": 1, "max": 5, "step": 1 },
    "dimensions": [
      { "id": "empathy", "label": { "de": "Empathie", "en": "Empathy" }, "weight": 0.3 },
      { "id": "helpfulness", "label": { "de": "Hilfsbereitschaft", "en": "Helpfulness" }, "weight": 0.3 },
      { "id": "professionalism", "label": { "de": "Professionalität", "en": "Professionalism" }, "weight": 0.2 },
      { "id": "clarity", "label": { "de": "Klarheit", "en": "Clarity" }, "weight": 0.2 }
    ],
    "show_overall": true
  }
}
```

---

## 3. Mail Rating (function_type_id = 3)

**Zweck:** Gesamte E-Mail-Konversation bewerten (LLARS-spezifisch).

### Vollständiges Beispiel

```json
{
  "schema_version": "1.0",
  "type": "mail_rating",
  "reference": null,
  "items": [
    {
      "id": "item_1",
      "label": "E-Mail-Verlauf #4521",
      "source": { "type": "human" },
      "content": {
        "type": "conversation",
        "messages": [
          {
            "role": "Klient",
            "content": "Sehr geehrte Damen und Herren, ich habe eine Frage zu meinem Mietvertrag. Der Vermieter verlangt eine Nachzahlung von 500€.",
            "timestamp": "2024-01-10T09:00:00Z"
          },
          {
            "role": "Berater",
            "content": "Vielen Dank für Ihre Anfrage. Haben Sie die Nebenkostenabrechnung bereits geprüft? Oft finden sich dort Fehler.",
            "timestamp": "2024-01-10T14:30:00Z"
          },
          {
            "role": "Klient",
            "content": "Danke für die Antwort. Ich werde die Abrechnung nochmal genau prüfen.",
            "timestamp": "2024-01-10T15:00:00Z"
          }
        ]
      }
    }
  ],
  "config": {
    "scale": { "min": 1, "max": 5, "step": 1 },
    "dimensions": [
      { "id": "response_quality", "label": { "de": "Antwortqualität", "en": "Response Quality" }, "weight": 0.3 },
      { "id": "solution_orientation", "label": { "de": "Lösungsorientierung", "en": "Solution Orientation" }, "weight": 0.3 },
      { "id": "communication", "label": { "de": "Kommunikation", "en": "Communication" }, "weight": 0.2 },
      { "id": "timeliness", "label": { "de": "Zeitnähe", "en": "Timeliness" }, "weight": 0.2 }
    ],
    "focus_role": "Berater"
  }
}
```

---

## 4. Comparison (function_type_id = 4)

**Zweck:** Paarweiser A/B-Vergleich (welches ist besser?).

**UI-Layout:**

- Links: Option A
- Rechts: Option B
- Unten: Auswahlbuttons

### Vollständiges Beispiel

```json
{
  "schema_version": "1.0",
  "type": "comparison",
  "reference": {
    "type": "text",
    "label": "Originaltext (Englisch)",
    "content": "The quick brown fox jumps over the lazy dog."
  },
  "items": [
    {
      "id": "item_a",
      "label": "Übersetzung A",
      "source": { "type": "llm", "name": "deepl/translator" },
      "content": "Der schnelle braune Fuchs springt über den faulen Hund."
    },
    {
      "id": "item_b",
      "label": "Übersetzung B",
      "source": { "type": "llm", "name": "openai/gpt-4" },
      "content": "Der flinke braune Fuchs springt über den trägen Hund."
    }
  ],
  "config": {
    "question": {
      "de": "Welche Übersetzung ist natürlicher und genauer?",
      "en": "Which translation is more natural and accurate?"
    },
    "criteria": ["Natürlichkeit", "Genauigkeit", "Stil"],
    "allow_tie": true,
    "show_source": false
  }
}
```

---

## 5. Authenticity (function_type_id = 5)

**Zweck:** Binäre Echt/Fake-Klassifikation (KI-generiert erkennen).

### Vollständiges Beispiel

```json
{
  "schema_version": "1.0",
  "type": "authenticity",
  "reference": {
    "type": "text",
    "label": "Bewertungskriterien",
    "content": "Bewerten Sie, ob dieser Text von einem Menschen oder einer KI geschrieben wurde."
  },
  "items": [
    {
      "id": "item_1",
      "label": "Zu bewertender Text",
      "source": { "type": "unknown" },
      "content": "Die Forschungsergebnisse zeigen eindeutig, dass regelmäßige Bewegung nicht nur die körperliche Gesundheit verbessert, sondern auch signifikante positive Auswirkungen auf die mentale Gesundheit hat."
    }
  ],
  "config": {
    "options": [
      { "id": "human", "label": { "de": "Von Mensch geschrieben", "en": "Written by human" } },
      { "id": "ai", "label": { "de": "KI-generiert", "en": "AI-generated" } }
    ],
    "show_confidence": true
  },
  "ground_truth": {
    "value": "ai",
    "source": { "type": "llm", "name": "openai/gpt-4" }
  }
}
```

---

## 7. Labeling (function_type_id = 7)

**Zweck:** Kategorie(n) zuweisen (Single-Label oder Multi-Label).

### Single-Label Beispiel

```json
{
  "schema_version": "1.0",
  "type": "labeling",
  "items": [
    {
      "id": "item_1",
      "label": "Nachrichtenartikel",
      "source": { "type": "human", "name": "Reuters" },
      "content": "Die EZB hat heute die Leitzinsen um 0,25 Prozentpunkte gesenkt. Dies ist die erste Zinssenkung seit 2019."
    }
  ],
  "config": {
    "mode": "single",
    "labels": [
      { "id": "politics", "label": { "de": "Politik", "en": "Politics" }, "color": "#4A90D9" },
      { "id": "economy", "label": { "de": "Wirtschaft", "en": "Economy" }, "color": "#50C878" },
      { "id": "sports", "label": { "de": "Sport", "en": "Sports" }, "color": "#FF6B6B" },
      { "id": "culture", "label": { "de": "Kultur", "en": "Culture" }, "color": "#9B59B6" },
      { "id": "science", "label": { "de": "Wissenschaft", "en": "Science" }, "color": "#F39C12" }
    ],
    "allow_other": false
  },
  "ground_truth": {
    "value": "economy"
  }
}
```

### Multi-Label Beispiel

```json
{
  "schema_version": "1.0",
  "type": "labeling",
  "items": [
    {
      "id": "item_1",
      "label": "Beratungsanfrage",
      "source": { "type": "human" },
      "content": {
        "type": "conversation",
        "messages": [
          {
            "role": "Klient",
            "content": "Ich habe Probleme mit meinem Vermieter. Er will die Miete erhöhen und droht mit Kündigung. Außerdem ist die Heizung kaputt."
          }
        ]
      }
    }
  ],
  "config": {
    "mode": "multi",
    "labels": [
      { "id": "legal", "label": { "de": "Rechtliche Frage", "en": "Legal question" } },
      { "id": "financial", "label": { "de": "Finanzielle Beratung", "en": "Financial advice" } },
      { "id": "conflict", "label": { "de": "Konfliktlösung", "en": "Conflict resolution" } },
      { "id": "housing", "label": { "de": "Wohnungsfragen", "en": "Housing issues" } },
      { "id": "maintenance", "label": { "de": "Instandhaltung", "en": "Maintenance" } }
    ],
    "allow_other": true,
    "min_labels": 1,
    "max_labels": 3
  },
  "ground_truth": {
    "value": ["legal", "housing", "maintenance"]
  }
}
```

---

## Schema-Referenz

### Ranking Config

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `mode` | `"simple" | "multi_group"` | Einfach oder mit Tabs |
| `buckets` | `Bucket[]` | Bucket-Definitionen |
| `allow_ties` | `boolean` | Mehrere Items pro Bucket? |
| `require_complete` | `boolean` | Alle Items zuordnen? |
| `groups` | `RankingGroup[]` | Nur bei `multi_group` |

### Rating Config

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `scale.min` | `number` | Minimum (meist 1) |
| `scale.max` | `number` | Maximum (meist 5) |
| `scale.step` | `number` | Schrittweite (meist 1) |
| `scale.labels` | `Record<number, I18nLabel>` | Skalenbeschriftungen |
| `dimensions` | `Dimension[]` | Bewertungsdimensionen |
| `show_overall` | `boolean` | Gesamtscore anzeigen? |

### Dimension

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | `string` | Technische ID |
| `label` | `I18nLabel` | Anzeigename |
| `description` | `I18nLabel` | Tooltip/Hilfetext |
| `weight` | `number` | Gewichtung (0-1, Summe = 1) |

---

## Dateien

Die Schemas sind definiert in:

```
Backend (Ground Truth):
app/schemas/evaluation_data_schemas.py

Frontend:
llars-frontend/src/schemas/evaluationSchemas.js

API:
GET /api/scenarios/{id}/schema
```
