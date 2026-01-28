# LLARS Evaluation Data Schemas

**Version:** 1.0
**Datum:** 2026-01-27
**Status:** Active

---

## Übersicht

Dieses Dokument definiert die einheitlichen JSON-Schemas für alle Evaluationstypen in LLARS. Diese Schemas dienen als zentrale Ground Truth und werden von allen Komponenten referenziert.

### Design-Prinzipien

1. **Einheitlichkeit:** Alle Typen folgen derselben Grundstruktur
2. **Flexibilität:** Unterstützt Text und Konversationen gleichermaßen
3. **Klarheit:** `id` ist technisch, `label` ist für die UI
4. **Herkunft:** `source` dokumentiert Ursprung (Mensch vs. LLM)
5. **Erweiterbarkeit:** Typ-spezifische Config in separatem Feld

---

## Basis-Schema

```typescript
interface EvaluationData {
  schema_version: "1.0";
  type: "ranking" | "rating" | "mail_rating" | "comparison" | "authenticity" | "labeling";

  // Kontext/Referenz - wird rechts im Interface angezeigt
  reference: Reference | null;

  // Items zum Bewerten - werden links im Interface angezeigt
  items: Item[];

  // Typ-spezifische Konfiguration
  config: TypeConfig;

  // Optional: Ground Truth für supervised evaluation (selten vorhanden!)
  // Bei Ranking meist NICHT vorhanden - Bucket-Zuordnung ist subjektiv
  ground_truth?: GroundTruth;
}

interface Reference {
  type: "text" | "conversation";
  label: string;                    // UI-Anzeigename: "Original-Artikel", "Kundenanfrage"
  content: string | Message[];      // Text oder Array von Messages
  metadata?: Record<string, any>;   // Zusätzliche Infos (Autor, Datum, etc.)
}

interface Item {
  id: string;                       // Technische ID: "item_1", "item_2" (NIEMALS LLM-Namen!)
  label: string;                    // UI-Anzeigename: "Zusammenfassung 1", "Antwort A"
  source: Source;
  content: string | ConversationContent;
}

interface Source {
  type: "human" | "llm" | "unknown";
  name?: string;                    // Bei LLM: "mistralai/Mistral-Small-3.2"
  metadata?: Record<string, any>;   // Zusätzliche Infos (Modell-Version, etc.)
}

interface Message {
  role: string;                     // "Klient", "Berater", "System", "User", "Assistant"
  content: string;
  timestamp?: string;               // ISO 8601: "2024-01-15T10:30:00Z"
  metadata?: Record<string, any>;
}

interface ConversationContent {
  type: "conversation";
  messages: Message[];
}

interface GroundTruth {
  value: string | number | string[];  // Label, Rating, oder Labels
  source?: Source;
  confidence?: number;                // 0-1
}
```

---

## 1. Ranking (function_type_id = 1)

**Zweck:** Mehrere Items in Qualitätsbuckets einordnen (Drag & Drop)

**UI-Layout:**
- Links: Items (Features) zum Ranken in Buckets, optional in Tabs gruppiert
- Rechts: Referenz/Kontext (Original-Text oder Konversation)

### Schema

```typescript
interface RankingData extends EvaluationData {
  type: "ranking";
  config: RankingConfig;
}

// Einfaches Ranking (eine Gruppe, ein Bucket-Set)
interface SimpleRankingConfig {
  mode: "simple";
  buckets: Bucket[];
  allow_ties: boolean;        // Mehrere Items pro Bucket erlaubt?
  require_complete: boolean;  // Müssen alle Items zugeordnet werden?
}

// Multi-Group Ranking (mehrere Tabs, je mit eigenen Buckets)
interface MultiGroupRankingConfig {
  mode: "multi_group";
  groups: RankingGroup[];     // Gruppen-Definitionen (werden als Tabs gerendert)
  require_complete: boolean;  // Müssen alle Gruppen vollständig sein?
}

// Gruppen-Definition: Enthält Label (für Tab-Name) und Bucket-Konfiguration
interface RankingGroup {
  id: string;                 // Technische ID: "summaries", "comments"
  label: {                    // → Wird im Frontend als Tab-Name gerendert
    de: string;               // "Zusammenfassungen"
    en: string;               // "Summaries"
  };
  description?: {             // Optional: Tooltip/Hilfetext
    de: string;
    en: string;
  };
  buckets: Bucket[];          // Jede Gruppe hat eigene Buckets
  allow_ties: boolean;
}

interface Bucket {
  id: string;           // "good", "moderate", "poor"
  label: {              // → Wird im Frontend als Bucket-Überschrift gerendert
    de: string;         // "Gut"
    en: string;         // "Good"
  };
  color: string;        // "#98d4bb"
  order: number;        // Sortierreihenfolge (1 = beste Qualität)
}

// Items referenzieren ihre Gruppe über `group` Feld
interface RankingItem extends Item {
  group?: string;       // Referenz auf RankingGroup.id → bestimmt Tab-Zugehörigkeit
                        // Optional bei mode: "simple" (alle Items in einer Gruppe)
}

type RankingConfig = SimpleRankingConfig | MultiGroupRankingConfig;
```

**Beziehung Item → Group → Label:**
```
Item.group = "summaries"
     ↓
config.groups[].id = "summaries"
     ↓
config.groups[].label.de = "Zusammenfassungen"  → Tab-Name im Frontend
```

### Beispiel: Einfaches Ranking (News-Zusammenfassungen)

```json
{
  "schema_version": "1.0",
  "type": "ranking",
  "reference": {
    "type": "text",
    "label": "Original-Artikel",
    "content": "Die Teilnehmer des Weltklimagipfels haben sich auf neue ambitionierte Ziele zur Reduktion von Treibhausgasen geeinigt. Die Industrieländer verpflichten sich zu einer Senkung der Emissionen um 55% bis 2030...",
    "metadata": {
      "source": "Reuters",
      "date": "2024-01-15"
    }
  },
  "items": [
    {
      "id": "item_1",
      "label": "Zusammenfassung 1",
      "source": { "type": "llm", "name": "mistralai/Mistral-Small-3.2-24B-Instruct-2506" },
      "content": "Auf dem Weltklimagipfel einigten sich die Teilnehmer auf eine CO2-Reduktion von 55% bis 2030."
    },
    {
      "id": "item_2",
      "label": "Zusammenfassung 2",
      "source": { "type": "llm", "name": "mistralai/Magistral-Small-2509" },
      "content": "Die Klimakonferenz beschloss neue Ziele zur Emissionsreduktion mit Fokus auf Industrieländer."
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

### Beispiel: Multi-Group Ranking (Zusammenfassungen + Kommentare parallel)

```json
{
  "schema_version": "1.0",
  "type": "ranking",
  "reference": {
    "type": "text",
    "label": "Original-Artikel",
    "content": "Die Teilnehmer des Weltklimagipfels haben sich auf neue ambitionierte Ziele zur Reduktion von Treibhausgasen geeinigt. Die Industrieländer verpflichten sich zu einer Senkung der Emissionen um 55% bis 2030. Bundeskanzler Olaf Scholz bezeichnete die Einigung als historischen Durchbruch...",
    "metadata": {
      "source": "Reuters",
      "date": "2024-01-15"
    }
  },
  "items": [
    {
      "id": "item_1",
      "label": "Zusammenfassung 1",
      "group": "summaries",
      "source": { "type": "llm", "name": "mistralai/Mistral-Small-3.2" },
      "content": "Auf dem Weltklimagipfel einigten sich die Teilnehmer auf eine CO2-Reduktion von 55% bis 2030."
    },
    {
      "id": "item_2",
      "label": "Zusammenfassung 2",
      "group": "summaries",
      "source": { "type": "llm", "name": "mistralai/Magistral-Small" },
      "content": "Die Klimakonferenz beschloss neue Ziele zur Emissionsreduktion mit Fokus auf Industrieländer."
    },
    {
      "id": "item_3",
      "label": "Zusammenfassung 3",
      "group": "summaries",
      "source": { "type": "llm", "name": "openai/gpt-4" },
      "content": "Industrieländer einigen sich auf 55% Emissionsreduktion bis 2030, Deutschland plant Kohleausstieg."
    },
    {
      "id": "item_4",
      "label": "Kommentar 1",
      "group": "comments",
      "source": { "type": "llm", "name": "mistralai/Mistral-Small-3.2" },
      "content": "Die Einigung ist ein wichtiger Schritt, aber die konkrete Umsetzung bleibt abzuwarten. Die Ziele sind ambitioniert, jedoch fehlen verbindliche Sanktionsmechanismen."
    },
    {
      "id": "item_5",
      "label": "Kommentar 2",
      "group": "comments",
      "source": { "type": "llm", "name": "mistralai/Magistral-Small" },
      "content": "Ein historischer Moment für den Klimaschutz. Die Verpflichtung der Industrieländer zeigt, dass internationaler Druck wirkt."
    },
    {
      "id": "item_6",
      "label": "Kommentar 3",
      "group": "comments",
      "source": { "type": "llm", "name": "openai/gpt-4" },
      "content": "Die Ergebnisse sind gemischt zu bewerten: Einerseits ambitionierte Ziele, andererseits bleiben Schwellenländer weitgehend verschont."
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

### Beispiel: LLARS Beratungsantworten ranken (einfach)

```json
{
  "schema_version": "1.0",
  "type": "ranking",
  "reference": {
    "type": "conversation",
    "label": "Beratungsverlauf",
    "content": [
      {
        "role": "Klient",
        "content": "Ich habe Probleme mit meiner Nebenkostenabrechnung. Der Vermieter verlangt 500€ Nachzahlung.",
        "timestamp": "2024-01-10T09:00:00Z"
      },
      {
        "role": "Berater",
        "content": "Vielen Dank für Ihre Anfrage. Haben Sie die Abrechnung bereits geprüft?",
        "timestamp": "2024-01-10T09:15:00Z"
      }
    ]
  },
  "items": [
    {
      "id": "item_1",
      "label": "Antwortvorschlag 1",
      "source": { "type": "llm", "name": "openai/gpt-4" },
      "content": "Ich empfehle Ihnen, zunächst die Abrechnung Punkt für Punkt zu prüfen. Achten Sie besonders auf den Verteilerschlüssel und die Gesamtkosten..."
    },
    {
      "id": "item_2",
      "label": "Antwortvorschlag 2",
      "source": { "type": "llm", "name": "anthropic/claude-3" },
      "content": "Eine Nachzahlung von 500€ ist erheblich. Lassen Sie uns gemeinsam prüfen, ob diese gerechtfertigt ist..."
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

### Beispiel: LLARS Multi-Group (Antworten + Rückfragen parallel ranken)

```json
{
  "schema_version": "1.0",
  "type": "ranking",
  "reference": {
    "type": "conversation",
    "label": "Beratungsverlauf",
    "content": [
      {
        "role": "Klient",
        "content": "Mein Chef hat mir heute gesagt, dass ich gekündigt werde. Ich arbeite seit 5 Jahren dort.",
        "timestamp": "2024-01-15T10:00:00Z"
      }
    ]
  },
  "items": [
    {
      "id": "item_1",
      "label": "Antwort 1",
      "group": "responses",
      "source": { "type": "llm", "name": "openai/gpt-4" },
      "content": "Das tut mir sehr leid zu hören. Eine Kündigung nach 5 Jahren ist sicher ein Schock. Haben Sie die Kündigung bereits schriftlich erhalten?"
    },
    {
      "id": "item_2",
      "label": "Antwort 2",
      "group": "responses",
      "source": { "type": "llm", "name": "anthropic/claude-3" },
      "content": "Ich verstehe, dass das sehr belastend für Sie ist. Bevor wir über rechtliche Schritte sprechen - wie geht es Ihnen damit?"
    },
    {
      "id": "item_3",
      "label": "Rückfrage 1",
      "group": "questions",
      "source": { "type": "llm", "name": "openai/gpt-4" },
      "content": "Wurde ein Grund für die Kündigung genannt? Gab es vorher Abmahnungen?"
    },
    {
      "id": "item_4",
      "label": "Rückfrage 2",
      "group": "questions",
      "source": { "type": "llm", "name": "anthropic/claude-3" },
      "content": "Gibt es einen Betriebsrat in Ihrem Unternehmen? Und haben Sie einen Arbeitsvertrag mit Kündigungsfristen?"
    }
  ],
  "config": {
    "mode": "multi_group",
    "groups": [
      {
        "id": "responses",
        "label": { "de": "Antworten", "en": "Responses" },
        "buckets": [
          { "id": "empathetic", "label": { "de": "Empathisch", "en": "Empathetic" }, "color": "#98d4bb", "order": 1 },
          { "id": "neutral", "label": { "de": "Neutral", "en": "Neutral" }, "color": "#D1BC8A", "order": 2 },
          { "id": "cold", "label": { "de": "Distanziert", "en": "Cold" }, "color": "#e8a087", "order": 3 }
        ],
        "allow_ties": true
      },
      {
        "id": "questions",
        "label": { "de": "Rückfragen", "en": "Follow-up Questions" },
        "buckets": [
          { "id": "relevant", "label": { "de": "Relevant", "en": "Relevant" }, "color": "#88c4c8", "order": 1 },
          { "id": "helpful", "label": { "de": "Hilfreich", "en": "Helpful" }, "color": "#b0ca97", "order": 2 },
          { "id": "irrelevant", "label": { "de": "Irrelevant", "en": "Irrelevant" }, "color": "#e8a087", "order": 3 }
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

**Zweck:** Multi-dimensionales Rating auf Likert-Skala (LLM-as-Judge Metriken)

**UI-Layout:**
- Links: Dimensionen mit Likert-Skalen
- Rechts: Zu bewertender Text/Kontext

### Schema

```typescript
interface RatingData extends EvaluationData {
  type: "rating";
  config: {
    scale: {
      min: number;          // 1
      max: number;          // 5
      step: number;         // 1
      labels?: Record<number, { de: string; en: string }>;  // "1": "Sehr schlecht"
    };
    dimensions: Dimension[];
    show_overall: boolean;  // Gesamtbewertung anzeigen?
  };
}

interface Dimension {
  id: string;               // "coherence", "fluency"
  label: {
    de: string;             // "Kohärenz"
    en: string;             // "Coherence"
  };
  description?: {
    de: string;
    en: string;
  };
  weight: number;           // Gewichtung für Gesamtscore (0-1, Summe = 1)
}
```

### Beispiel: Zusammenfassung bewerten (SummEval-Style)

```json
{
  "schema_version": "1.0",
  "type": "rating",
  "reference": {
    "type": "text",
    "label": "Quelldokument",
    "content": "Ein führendes Technologieunternehmen hat heute einen bedeutenden Fortschritt im Bereich der künstlichen Intelligenz vorgestellt..."
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

### Beispiel: LLARS Beratungsantwort bewerten

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
        "content": "Ich fühle mich überfordert bei der Arbeit und weiß nicht, wie ich damit umgehen soll.",
        "timestamp": "2024-01-15T09:00:00Z"
      },
      {
        "role": "Berater",
        "content": "Das tut mir leid zu hören. Seit wann haben Sie diese Gefühle?",
        "timestamp": "2024-01-15T09:05:00Z"
      },
      {
        "role": "Klient",
        "content": "Seit etwa drei Monaten. Es wird immer schlimmer.",
        "timestamp": "2024-01-15T09:10:00Z"
      }
    ]
  },
  "items": [
    {
      "id": "item_1",
      "label": "Nächste Beraterantwort",
      "source": { "type": "llm", "name": "openai/gpt-4" },
      "content": "Es klingt, als ob Sie unter großem Druck stehen. Können Sie mir mehr darüber erzählen, was genau Sie überfordert? Ist es die Arbeitsmenge, die Kollegen oder etwas anderes?"
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

**Zweck:** Gesamte E-Mail-Konversation bewerten (LLARS-spezifisch)

**UI-Layout:**
- Links: Dimensionen mit Likert-Skalen
- Rechts: Der gesamte E-Mail-Verlauf

### Schema

```typescript
interface MailRatingData extends EvaluationData {
  type: "mail_rating";
  config: {
    scale: Scale;
    dimensions: Dimension[];
    focus_role?: string;     // Welche Rolle wird bewertet? "Berater"
  };
}
```

### Beispiel: Beratungsqualität bewerten

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
            "content": "Sehr geehrte Damen und Herren, ich habe eine Frage zu meinem Mietvertrag...",
            "timestamp": "2024-01-10T09:00:00Z"
          },
          {
            "role": "Berater",
            "content": "Vielen Dank für Ihre Anfrage. Gerne helfe ich Ihnen weiter...",
            "timestamp": "2024-01-10T14:30:00Z"
          },
          {
            "role": "Klient",
            "content": "Danke für die ausführliche Antwort. Das hilft mir sehr.",
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

**Zweck:** Paarweiser A/B-Vergleich (welches ist besser?)

**UI-Layout:**
- Links: Option A
- Rechts: Option B
- Unten: Auswahlbuttons (A besser / Gleich / B besser)

### Schema

```typescript
interface ComparisonData extends EvaluationData {
  type: "comparison";
  config: {
    question: {
      de: string;
      en: string;
    };
    criteria?: string[];      // Worauf achten?
    allow_tie: boolean;       // "Gleich gut" erlaubt?
    show_source: boolean;     // LLM-Namen anzeigen?
  };
}
```

### Beispiel: Zwei Übersetzungen vergleichen

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
      "de": "Welche Übersetzung ist besser?",
      "en": "Which translation is better?"
    },
    "criteria": ["Natürlichkeit", "Genauigkeit", "Stil"],
    "allow_tie": true,
    "show_source": false
  }
}
```

### Beispiel: LLARS Beratungsantworten vergleichen

```json
{
  "schema_version": "1.0",
  "type": "comparison",
  "reference": {
    "type": "conversation",
    "label": "Beratungskontext",
    "content": [
      {
        "role": "Klient",
        "content": "Mein Arbeitgeber will mich kündigen, obwohl ich nichts falsch gemacht habe."
      }
    ]
  },
  "items": [
    {
      "id": "item_a",
      "label": "Antwort A",
      "source": { "type": "llm", "name": "openai/gpt-4" },
      "content": "Das tut mir leid zu hören. Eine Kündigung ist eine ernste Angelegenheit. Haben Sie bereits eine schriftliche Kündigung erhalten?"
    },
    {
      "id": "item_b",
      "label": "Antwort B",
      "source": { "type": "llm", "name": "anthropic/claude-3" },
      "content": "Ich verstehe, dass das sehr belastend für Sie ist. Lassen Sie uns zunächst klären: Wurde die Kündigung bereits ausgesprochen oder angedroht?"
    }
  ],
  "config": {
    "question": {
      "de": "Welche Antwort ist empathischer und hilfreicher?",
      "en": "Which response is more empathetic and helpful?"
    },
    "allow_tie": true,
    "show_source": false
  }
}
```

---

## 5. Authenticity (function_type_id = 5)

**Zweck:** Binäre Echt/Fake-Klassifikation (KI-generiert erkennen)

**UI-Layout:**
- Mitte: Der zu bewertende Text
- Unten: Zwei Buttons (Echt / Fake)

### Schema

```typescript
interface AuthenticityData extends EvaluationData {
  type: "authenticity";
  config: {
    options: [
      { id: string; label: { de: string; en: string } },
      { id: string; label: { de: string; en: string } }
    ];
    show_confidence: boolean;   // Konfidenz-Slider anzeigen?
  };
}
```

### Beispiel: KI-generierten Text erkennen

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

### Beispiel: LLARS E-Mail-Authentizität

```json
{
  "schema_version": "1.0",
  "type": "authenticity",
  "reference": null,
  "items": [
    {
      "id": "item_1",
      "label": "E-Mail",
      "source": { "type": "unknown" },
      "content": {
        "type": "conversation",
        "messages": [
          {
            "role": "Absender",
            "content": "Sehr geehrter Herr Müller, bezugnehmend auf unser Telefonat vom vergangenen Freitag möchte ich Ihnen hiermit die besprochenen Unterlagen zusenden..."
          }
        ]
      }
    }
  ],
  "config": {
    "options": [
      { "id": "authentic", "label": { "de": "Echte E-Mail", "en": "Authentic email" } },
      { "id": "generated", "label": { "de": "KI-generiert", "en": "AI-generated" } }
    ],
    "show_confidence": true
  }
}
```

---

## 7. Labeling (function_type_id = 7)

**Zweck:** Kategorie(n) zuweisen (Single-Label oder Multi-Label)

**UI-Layout:**
- Links: Label-Optionen (Checkboxen oder Radio-Buttons)
- Rechts: Zu klassifizierender Text

### Schema

```typescript
interface LabelingData extends EvaluationData {
  type: "labeling";
  config: {
    mode: "single" | "multi";     // Eine oder mehrere Labels?
    labels: Label[];
    allow_other: boolean;         // "Sonstiges" Option?
    min_labels?: number;          // Nur bei multi
    max_labels?: number;          // Nur bei multi
  };
}

interface Label {
  id: string;
  label: {
    de: string;
    en: string;
  };
  description?: {
    de: string;
    en: string;
  };
  color?: string;
}
```

### Beispiel: Nachrichtenartikel kategorisieren

```json
{
  "schema_version": "1.0",
  "type": "labeling",
  "reference": null,
  "items": [
    {
      "id": "item_1",
      "label": "Nachrichtenartikel",
      "source": { "type": "human", "name": "Reuters" },
      "content": "Die EZB hat heute die Leitzinsen um 0,25 Prozentpunkte gesenkt. Dies ist die erste Zinssenkung seit 2019..."
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

### Beispiel: LLARS Beratungsthemen klassifizieren (Multi-Label)

```json
{
  "schema_version": "1.0",
  "type": "labeling",
  "reference": null,
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
            "content": "Ich habe Probleme mit meinem Vermieter. Er will die Miete erhöhen und droht mit Kündigung, obwohl ich immer pünktlich gezahlt habe. Außerdem ist die Heizung kaputt."
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

## Zusammenfassung: Schema-Matrix

| Typ | function_type_id | Reference | Items | Besonderheit |
|-----|------------------|-----------|-------|--------------|
| **Ranking** | 1 | Text/Conversation | N Items → Buckets | Drag & Drop, Multi-Group (Tabs) |
| **Rating** | 2 | Text/Conversation | 1-N Items | Multi-Dimensional |
| **Mail Rating** | 3 | null | 1 Conversation | LLARS-spezifisch |
| **Comparison** | 4 | Text/Conversation | Genau 2 Items | A vs B |
| **Authenticity** | 5 | Optional | 1 Item | Binär |
| **Labeling** | 7 | Optional | 1 Item | Single/Multi-Label |

### Ranking Modi

| Modus | Beschreibung | Use Case |
|-------|--------------|----------|
| `simple` | Eine Gruppe, ein Bucket-Set | Zusammenfassungen ranken |
| `multi_group` | Mehrere Tabs, je eigene Buckets | Zusammenfassungen + Kommentare parallel |

---

## Datei-Speicherort

Diese Schemas werden zentral definiert unter:

```
app/schemas/
├── __init__.py                        # Export der Schemas
├── evaluation_data_schemas.py         # GROUND TRUTH: Pydantic-Models für alle 6 Typen
└── evaluation_schemas.py              # LLM-Output Schemas (nicht Evaluation-Input!)

app/services/evaluation/
├── schema_transformer_service.py      # DB-Models → EvaluationData Schema

app/routes/scenarios/
├── scenario_schema_api.py             # API-Endpoints für Schema-Daten

llars-frontend/src/schemas/
├── index.js                           # Export aller Schemas
├── evaluationSchemas.js               # JS-Version der Schemas mit JSDoc

llars-frontend/src/composables/
├── useEvaluationSchema.js             # Vue Composable für Schema-Nutzung
```

---

## Implementierungs-Status

| Komponente | Status | Beschreibung |
|------------|--------|--------------|
| Backend Pydantic Models | ✅ Fertig | `evaluation_data_schemas.py` |
| SchemaTransformer Service | ✅ Fertig | DB → Schema Konvertierung |
| Schema API Endpoints | ✅ Fertig | `/api/scenarios/{id}/schema` etc. |
| Frontend JS Schemas | ✅ Fertig | `evaluationSchemas.js` |
| Vue Composable | ✅ Fertig | `useEvaluationSchema.js` |
| Code-Dokumentation | ✅ Fertig | Alle Dateien mit Ground Truth Hinweisen |
