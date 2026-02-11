# Evaluation Data Formats

**Version:** 1.0 | **Status:** Active

This documentation describes the JSON schemas for all 6 evaluation types in LLARS. Use the **minimal examples** for a quick start and the **full examples** as reference.

---

## Overview

| Type | function_type_id | Use case |
|------|------------------|----------|
| **Ranking** | 1 | Sort items into quality buckets |
| **Rating** | 2 | Multi-dimensional rating (LLM evaluator) |
| **Mail Rating** | 3 | Rate email conversations |
| **Comparison** | 4 | Pairwise A/B comparison |
| **Authenticity** | 5 | Real/Fake classification |
| **Labeling** | 7 | Assign categories |

---

## Quick start: minimal examples

### Ranking (minimal)

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

### Rating (minimal)

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

### Comparison (minimal)

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

### Labeling (minimal)

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

## Base schema

All evaluation types follow this base structure:

```typescript
interface EvaluationData {
  schema_version: "1.0";
  type: "ranking" | "rating" | "mail_rating" | "comparison" | "authenticity" | "labeling";

  // Optional: context/reference (right side in UI)
  reference?: Reference;

  // Items to evaluate (left side in UI)
  items: Item[];

  // Type-specific configuration
  config: TypeConfig;

  // Optional: ground truth for supervised evaluation
  ground_truth?: GroundTruth;
}

interface Reference {
  type: "text" | "conversation";
  label: string;                    // UI display name
  content: string | Message[];      // Text or messages
  metadata?: Record<string, any>;
}

interface Item {
  id: string;                       // Technical ID (NOT LLM names!)
  label: string;                    // UI display name
  source?: Source;
  content: string | ConversationContent;
}

interface Source {
  type: "human" | "llm" | "unknown";
  name?: string;                    // For LLM: model name
}

interface Message {
  role: string;                     // "Klient", "Berater", "User", "Assistant"
  content: string;
  timestamp?: string;               // ISO 8601
}
```

---

## 1. Ranking (function_type_id = 1)

**Purpose:** Drag & drop items into quality buckets.

**UI layout:**

- Left: items to rank
- Right: reference/context (optional)

### Full example: simple ranking

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

### Multi-group ranking (tabs)

For parallel ranking of multiple categories:

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

**Purpose:** Multi-dimensional rating on a Likert scale (LLM evaluator metrics).

**UI layout:**

- Left: dimensions with Likert scales
- Right: text/context to rate

### Full example: SummEval style

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

### Rating a counseling response

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

**Purpose:** Rate an entire email conversation (LLARS-specific).

### Full example

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

**Purpose:** Pairwise A/B comparison (which is better?).

**UI layout:**

- Left: option A
- Right: option B
- Bottom: choice buttons

### Full example

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

**Purpose:** Binary real/fake classification (detect AI-generated content).

### Full example

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
      "label": "Nachricht",
      "content": "Guten Tag, ich möchte wissen, wie ich mein Konto kündigen kann."
    }
  ],
  "config": {
    "options": [
      { "id": "human", "label": { "de": "Mensch", "en": "Human" } },
      { "id": "ai", "label": { "de": "KI", "en": "AI" } }
    ],
    "show_confidence": true
  }
}
```

---

## 7. Labeling (function_type_id = 7)

**Purpose:** Assign categories (single or multi-label).

### Single-label example

```json
{
  "schema_version": "1.0",
  "type": "labeling",
  "items": [
    {
      "id": "item_1",
      "label": "Ticket",
      "content": "Mein Internet ist seit gestern ausgefallen."
    }
  ],
  "config": {
    "mode": "single",
    "labels": [
      { "id": "technical", "label": { "de": "Technisches Problem", "en": "Technical issue" } },
      { "id": "billing", "label": { "de": "Abrechnung", "en": "Billing" } },
      { "id": "general", "label": { "de": "Allgemein", "en": "General" } }
    ],
    "allow_other": false
  },
  "ground_truth": {
    "value": "technical"
  }
}
```

### Multi-label example

```json
{
  "schema_version": "1.0",
  "type": "labeling",
  "items": [
    {
      "id": "item_1",
      "label": "Anfrage",
      "content": "Ich habe eine Frage zu meinem Mietvertrag und zu Reparaturen in meiner Wohnung."
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

## Schema reference

### Ranking config

| Field | Type | Description |
|------|-----|--------------|
| `mode` | `"simple" | "multi_group"` | Simple or with tabs |
| `buckets` | `Bucket[]` | Bucket definitions |
| `allow_ties` | `boolean` | Allow multiple items per bucket? |
| `require_complete` | `boolean` | Require all items to be assigned? |
| `groups` | `RankingGroup[]` | Only for `multi_group` |

### Rating config

| Field | Type | Description |
|------|-----|--------------|
| `scale.min` | `number` | Minimum (usually 1) |
| `scale.max` | `number` | Maximum (usually 5) |
| `scale.step` | `number` | Step size (usually 1) |
| `scale.labels` | `Record<number, I18nLabel>` | Scale labels |
| `dimensions` | `Dimension[]` | Rating dimensions |
| `show_overall` | `boolean` | Show overall score? |

### Dimension

| Field | Type | Description |
|------|-----|--------------|
| `id` | `string` | Technical ID |
| `label` | `I18nLabel` | Display name |
| `description` | `I18nLabel` | Tooltip/help text |
| `weight` | `number` | Weight (0-1, sum = 1) |

---

## Files

Schemas are defined in:

```
Backend (ground truth):
app/schemas/evaluation_data_schemas.py

Frontend:
llars-frontend/src/schemas/evaluationSchemas.js

API:
GET /api/scenarios/{id}/schema
```
