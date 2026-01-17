# Szenario Wizard: KI-Analyse UI Konzept

**Version:** 1.0
**Datum:** 16. Januar 2026
**Status:** In Entwicklung

---

## Übersicht

Dieses Konzept beschreibt das UI für die KI-gestützte Datenanalyse im Szenario Wizard. Die Analyse erfolgt via SSE-Streaming und befüllt visuelle Elemente live. Nach der Analyse kann der Benutzer:

1. **Vorschläge editieren** - Alle KI-Vorschläge sind anpassbar
2. **Mit der KI chatten** - Vorhaben erklären, Änderungen besprechen
3. **Konfiguration verfeinern** - Labels, Skalen, Buckets definieren

---

## Architektur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ScenarioWizard.vue                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    StreamingAnalysisPanel.vue                          │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │  │
│  │  │EvalTypeCard │ │ScenarioCard │ │ReasoningCard│ │DataQualityCard  │  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘  │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐│  │
│  │  │                      AIChatPanel.vue                              ││  │
│  │  │  ┌─────────────────────────────────────────────────────────────┐ ││  │
│  │  │  │ Chat Messages (scrollable)                                  │ ││  │
│  │  │  └─────────────────────────────────────────────────────────────┘ ││  │
│  │  │  ┌─────────────────────────────────────────────────────────────┐ ││  │
│  │  │  │ Input + Send Button                                         │ ││  │
│  │  │  └─────────────────────────────────────────────────────────────┘ ││  │
│  │  └───────────────────────────────────────────────────────────────────┘│  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## UI Layout

### Gesamtansicht nach Streaming

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🤖 KI-Analyse                                                    ✓ Fertig  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────┐  ┌────────────────────────────────────────┐  │
│  │ 📊 EVALUATIONSTYP        │  │ 📝 SZENARIO                            │  │
│  │                          │  │                                        │  │
│  │    ⭐                    │  │  Name:                                 │  │
│  │   Rating                 │  │  ┌────────────────────────────────┐   │  │
│  │                          │  │  │ Authentizitätsbewertung    ✏️  │   │  │
│  │  Konfidenz: 85%          │  │  └────────────────────────────────┘   │  │
│  │  ●●●●●●●●○○              │  │                                        │  │
│  │                          │  │  Beschreibung:                         │  │
│  │  [Typ ändern ▼]          │  │  ┌────────────────────────────────┐   │  │
│  │                          │  │  │ Evaluatoren bewerten ob    ✏️  │   │  │
│  │                          │  │  │ Nachrichten echt oder KI-      │   │  │
│  │                          │  │  │ generiert sind.                │   │  │
│  │                          │  │  └────────────────────────────────┘   │  │
│  └──────────────────────────┘  └────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ 💬 KI-Begründung                                              [▼]   │  │
│  │                                                                       │  │
│  │ "Die Daten enthalten synthetische Nachrichten mit einem 'label'-     │  │
│  │  Feld, das auf eine Bewertungsskala hindeutet..."                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────────────┐  │
│  │ 📁 DATEN        │  │ ✅ QUALITÄT     │  │ 💡 EMPFEHLUNGEN            │  │
│  │                 │  │                 │  │                            │  │
│  │  150 Items      │  │ ████████░░ 82%  │  │ • 'label' als Ground-Truth │  │
│  │  5 Felder       │  │                 │  │ • Fehlende Werte prüfen    │  │
│  │  2 Dateien      │  │ ⚠️ 2 Probleme   │  │                            │  │
│  └─────────────────┘  └─────────────────┘  └────────────────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  💬 MIT KI VERFEINERN                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  🤖 Ich habe die Daten analysiert und schlage einen Rating-Task vor. │  │
│  │     Möchtest du etwas anpassen oder hast du Fragen?                  │  │
│  │                                                                       │  │
│  │  ┌─ Schnellaktionen ──────────────────────────────────────────────┐  │  │
│  │  │ [Labels definieren] [Skala anpassen] [Typ ändern] [Erklären]  │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Beschreibe dein Vorhaben oder stelle eine Frage...            [📤]  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Komponenten im Detail

### 1. EvalTypeCard.vue

**Zweck:** Zeigt den erkannten Evaluationstyp mit Konfidenz an.

```
┌──────────────────────────────┐
│ 📊 EVALUATIONSTYP            │
│                              │
│         ⭐                   │   ← Großes Icon (40px)
│       Rating                 │   ← Typ-Name (bold)
│                              │
│   Konfidenz: 85%             │
│   ●●●●●●●●○○                 │   ← 10 Dots, gefüllt nach %
│                              │
│   ┌────────────────────────┐ │
│   │ Typ ändern         ▼   │ │   ← Dropdown zum Ändern
│   └────────────────────────┘ │
└──────────────────────────────┘

Props:
  - evalType: string ('rating' | 'ranking' | 'labeling' | 'comparison')
  - confidence: number (0-1)
  - reasoning: string
  - loading: boolean
  - editable: boolean

Events:
  - @update:evalType - Wenn Benutzer Typ ändert

States:
  - loading: Skeleton mit Pulse-Animation
  - streaming: Icon erscheint, Konfidenz füllt sich
  - complete: Voll interaktiv, Dropdown aktiv
```

**Eval-Type Mapping:**

| Typ | Icon | Farbe | Label |
|-----|------|-------|-------|
| rating | `mdi-star` | `#D1BC8A` | Rating |
| ranking | `mdi-sort-ascending` | `#88c4c8` | Ranking |
| labeling | `mdi-tag-multiple` | `#b0ca97` | Labeling |
| comparison | `mdi-compare` | `#e8a087` | Vergleich |
| authenticity | `mdi-shield-check` | `#98d4bb` | Authentizität |

---

### 2. ScenarioSuggestionCard.vue

**Zweck:** Editierbare Felder für Szenario-Name und Beschreibung.

```
┌────────────────────────────────────────────┐
│ 📝 SZENARIO-VORSCHLAG                      │
│                                            │
│ Name:                                      │
│ ┌────────────────────────────────────────┐ │
│ │ Authentizitätsbewertung syntheti... ✏️ │ │  ← v-text-field
│ └────────────────────────────────────────┘ │
│                                            │
│ Beschreibung:                              │
│ ┌────────────────────────────────────────┐ │
│ │ Evaluatoren sollen bewerten, ob       │ │
│ │ die gezeigten Nachrichten von einem   │ │  ← v-textarea (auto-grow)
│ │ Menschen oder einer KI stammen.    ✏️ │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ [KI neu generieren lassen 🔄]              │  ← Optional: Neu generieren
└────────────────────────────────────────────┘

Props:
  - name: string
  - description: string
  - loading: boolean
  - streaming: boolean (Typewriter-Effekt aktiv)

Events:
  - @update:name
  - @update:description
  - @regenerate - Neu generieren angefordert

States:
  - loading: Skeleton-Lines
  - streaming: Text erscheint zeichenweise, Cursor blinkt
  - complete: Normale Textfelder, editierbar
```

---

### 3. ReasoningCard.vue

**Zweck:** Zeigt die KI-Begründung (collapsible).

```
┌────────────────────────────────────────────────────────────┐
│ 💬 Warum dieser Typ?                              [▼ / ▲] │
├────────────────────────────────────────────────────────────┤
│                                                            │  ← Collapsible
│ "Die Daten enthalten synthetische Nachrichten, die        │
│  auf Authentizität und Qualität bewertet werden sollen.   │
│  Das vorhandene 'label'-Feld deutet auf eine Bewertung    │
│  hin, möglicherweise auf einer Skala. Da keine Paare      │
│  oder Kategorien erkennbar sind, ist eine Skalenbewertung │
│  am sinnvollsten."                                        │
│                                                            │
└────────────────────────────────────────────────────────────┘

Props:
  - reasoning: string
  - loading: boolean
  - streaming: boolean
  - collapsed: boolean (default: false während Streaming, true danach)

Events:
  - @toggle - Collapse/Expand

States:
  - loading: Skeleton
  - streaming: Text streamt rein, expanded
  - complete: Collapsed by default, expandable
```

---

### 4. DataStatsCard.vue

**Zweck:** Sofortige Daten-Übersicht (kein Streaming nötig).

```
┌─────────────────────────┐
│ 📁 DATEN                │
│                         │
│   150                   │  ← Große Zahl
│   Items                 │
│                         │
│   5 Felder              │
│   2 Dateien             │
│                         │
│ ┌─────────────────────┐ │
│ │ ▼ Feldübersicht     │ │  ← Expandable
│ ├─────────────────────┤ │
│ │ • messages (array)  │ │
│ │ • label (string)    │ │
│ │ • id (number)       │ │
│ │ • timestamp (string)│ │
│ │ • metadata (object) │ │
│ └─────────────────────┘ │
└─────────────────────────┘

Props:
  - itemCount: number
  - fieldCount: number
  - fileCount: number
  - fields: Array<{name: string, type: string, completeness: number}>

States:
  - Wird sofort mit data_summary Event befüllt
  - Kein Loading/Streaming State nötig
```

---

### 5. DataQualityCard.vue

**Zweck:** Zeigt Datenqualität und Probleme an.

```
┌─────────────────────────────┐
│ ✅ DATENQUALITÄT            │
│                             │
│ ████████████░░░░  82%       │  ← Progress Bar
│                             │
│ ⚠️ Probleme:                │
│ ┌─────────────────────────┐ │
│ │ • 18% fehlende 'label'  │ │  ← Chip-Liste
│ │ • Inkonsistente IDs     │ │
│ └─────────────────────────┘ │
│                             │
│ 💡 Empfehlungen:            │
│ ┌─────────────────────────┐ │
│ │ • Labels vervollständigen│ │
│ │ • IDs normalisieren     │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘

Props:
  - completeness: number (0-1)
  - issues: string[]
  - recommendations: string[]
  - loading: boolean

States:
  - loading: Skeleton
  - complete: Vollständig aus data_quality Event
```

---

### 6. AIChatPanel.vue (NEU)

**Zweck:** Chat-Interface zur Verfeinerung der Konfiguration.

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 💬 MIT KI VERFEINERN                                                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ [Scrollable Message Area]                                          │   │
│  │                                                                     │   │
│  │  ┌─ 🤖 KI ─────────────────────────────────────────────────────┐  │   │
│  │  │ Ich habe die Daten analysiert und schlage einen Rating-Task │  │   │
│  │  │ vor. Die Nachrichten scheinen auf Authentizität geprüft     │  │   │
│  │  │ werden zu sollen.                                            │  │   │
│  │  │                                                              │  │   │
│  │  │ ┌─ Schnellaktionen ────────────────────────────────────────┐│  │   │
│  │  │ │ [🏷️ Labels] [📊 Skala] [🔄 Typ ändern] [❓ Erklären]    ││  │   │
│  │  │ └──────────────────────────────────────────────────────────┘│  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │  ┌─ 👤 Du ─────────────────────────────────────────────────────┐  │   │
│  │  │ Ich möchte dass die Evaluatoren 3 Labels zur Auswahl haben: │  │   │
│  │  │ "echte Mail", "KI-generiert" und "unsicher"                 │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │  ┌─ 🤖 KI ─────────────────────────────────────────────────────┐  │   │
│  │  │ Verstanden! Ich habe die Konfiguration angepasst:           │  │   │
│  │  │                                                              │  │   │
│  │  │ ┌─ Änderungen ─────────────────────────────────────────────┐│  │   │
│  │  │ │ ✓ Evaluationstyp: authenticity (war: rating)            ││  │   │
│  │  │ │ ✓ Labels hinzugefügt:                                    ││  │   │
│  │  │ │   [echte Mail] [KI-generiert] [unsicher]                ││  │   │
│  │  │ └──────────────────────────────────────────────────────────┘│  │   │
│  │  │                                                              │  │   │
│  │  │ Soll ich noch etwas anpassen?                               │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ Beschreibe dein Vorhaben oder stelle eine Frage...          [📤]  │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

Props:
  - sessionId: string (Import Session für Kontext)
  - currentConfig: Object (aktuelle Konfiguration)
  - initialMessage: string (erste KI-Nachricht nach Analyse)

Events:
  - @config-update: {field: string, value: any} - Wenn KI Konfiguration ändert

States:
  - idle: Warten auf Benutzereingabe
  - streaming: KI antwortet (Typewriter-Effekt)
  - error: Fehler bei API-Aufruf
```

**Schnellaktionen (Quick Actions):**

| Aktion | Prompt an KI | Erwartete Reaktion |
|--------|--------------|-------------------|
| Labels definieren | "Hilf mir Labels für diesen Task zu definieren" | KI fragt nach Kategorien |
| Skala anpassen | "Ich möchte die Bewertungsskala anpassen" | KI zeigt Skalen-Optionen |
| Typ ändern | "Ich denke ein anderer Evaluationstyp wäre besser" | KI erklärt Alternativen |
| Erklären | "Erkläre mir warum du diesen Typ gewählt hast" | KI erläutert Reasoning |

**Chat-Message Typen:**

```typescript
interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date

  // Optional: Strukturierte Daten
  configChanges?: ConfigChange[]
  quickActions?: QuickAction[]
}

interface ConfigChange {
  field: string       // 'evalType', 'labels', 'scales', etc.
  oldValue: any
  newValue: any
  applied: boolean
}

interface QuickAction {
  label: string
  icon: string
  prompt: string
}
```

---

## Streaming & Parsing

### useStreamingParser.js

Composable für inkrementelles JSON-Parsing während des Streams.

```javascript
import { ref, reactive } from 'vue'

export function useStreamingParser() {
  const buffer = ref('')
  const parsed = reactive({
    evalType: null,
    evalTypeConfidence: null,
    evalTypeReasoning: '',
    scenarioName: '',
    scenarioDescription: '',
    dataQuality: null
  })

  const streamingState = reactive({
    evalType: 'pending',      // 'pending' | 'streaming' | 'complete'
    scenarioName: 'pending',
    scenarioDescription: 'pending',
    reasoning: 'pending',
    dataQuality: 'pending'
  })

  function processChunk(chunk) {
    buffer.value += chunk

    // Versuche Felder zu extrahieren
    extractField('eval_type', (v) => {
      parsed.evalType = v
      streamingState.evalType = 'complete'
    })

    extractField('eval_type_confidence', (v) => {
      parsed.evalTypeConfidence = v
    })

    // Streaming-Felder (Text wird inkrementell angezeigt)
    extractStreamingField('eval_type_reasoning', (partial) => {
      parsed.evalTypeReasoning = partial
      streamingState.reasoning = 'streaming'
    })

    extractStreamingField('scenario_name', (partial) => {
      parsed.scenarioName = partial
      streamingState.scenarioName = 'streaming'
    })

    extractStreamingField('scenario_description', (partial) => {
      parsed.scenarioDescription = partial
      streamingState.scenarioDescription = 'streaming'
    })
  }

  function finalize() {
    // Markiere alle als complete
    Object.keys(streamingState).forEach(k => {
      streamingState[k] = 'complete'
    })
  }

  return {
    parsed,
    streamingState,
    processChunk,
    finalize
  }
}
```

---

## Datenfluss

### Initiale Analyse

```
1. User lädt Dateien hoch
   ↓
2. User klickt "KI analysieren"
   ↓
3. POST /api/ai-assist/analyze-scenario-data/stream
   ↓
4. SSE Events:
   │
   ├─ data_summary → DataStatsCard (sofort vollständig)
   │
   ├─ thinking → Alle Cards zeigen Skeleton
   │
   ├─ chunk → useStreamingParser extrahiert Felder live
   │          → EvalTypeCard: Icon + Name erscheinen
   │          → ScenarioSuggestionCard: Text streamt
   │          → ReasoningCard: Begründung streamt
   │
   ├─ suggestions → Parsing abgeschlossen
   │                → Alle Felder editierbar
   │
   ├─ data_quality → DataQualityCard befüllt
   │
   └─ done → AIChatPanel erscheint mit initialer Nachricht
```

### Chat-Verfeinerung

```
1. User schreibt Nachricht oder klickt Quick Action
   ↓
2. POST /api/import/ai/chat-stream
   Body: {
     session_id: "...",
     messages: [...chatHistory],
     current_config: {evalType, labels, scales, ...}
   }
   ↓
3. SSE Events:
   │
   ├─ thinking → "KI denkt nach..."
   │
   ├─ config_update → Konfiguration wird live aktualisiert
   │   {field: "labels", value: ["echt", "fake", "unsicher"]}
   │   → EvalTypeCard oder andere Cards aktualisieren sich
   │
   ├─ chunk → Chat-Antwort streamt
   │
   └─ done → Antwort komplett
```

---

## Konfigurations-Objekt

Das Config-Objekt wird durch Analyse und Chat aufgebaut:

```javascript
const config = {
  // Basis (aus Analyse)
  evalType: 'authenticity',
  scenarioName: 'Authentizitätsbewertung synthetischer Nachrichten',
  scenarioDescription: 'Evaluatoren bewerten ob Nachrichten echt sind.',

  // Erweitert (aus Chat)
  labels: [
    { name: 'echte Mail', color: '#98d4bb' },
    { name: 'KI-generiert', color: '#e8a087' },
    { name: 'unsicher', color: '#D1BC8A' }
  ],

  // Für Rating-Tasks
  scales: [
    { name: 'Qualität', min: 1, max: 5, labels: ['schlecht', 'mittel', 'gut'] }
  ],

  // Für Ranking-Tasks
  buckets: [
    { name: 'Gut', order: 1, color: '#98d4bb' },
    { name: 'Mittel', order: 2, color: '#D1BC8A' },
    { name: 'Schlecht', order: 3, color: '#e8a087' }
  ],

  // Field Mapping
  fieldMapping: {
    'messages': 'conversation',
    'label': 'ground_truth'
  }
}
```

---

## Design System Integration

### Farben

| Element | Variable | Hex |
|---------|----------|-----|
| Card Header | `--llars-primary` | `#b0ca97` |
| Confidence High | `--llars-success` | `#98d4bb` |
| Confidence Medium | `--llars-secondary` | `#D1BC8A` |
| Confidence Low | `--llars-danger` | `#e8a087` |
| Accent | `--llars-accent` | `#88c4c8` |
| Skeleton | `--llars-skeleton` | `#3a3a3a` |
| Streaming Cursor | `--llars-primary` | `#b0ca97` |

### Animationen

```css
/* Skeleton Pulse */
@keyframes skeleton-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}

.skeleton {
  animation: skeleton-pulse 1.5s ease-in-out infinite;
  background: var(--llars-skeleton);
  border-radius: 4px;
}

/* Streaming Cursor */
@keyframes cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.streaming-cursor {
  animation: cursor-blink 1s infinite;
  color: var(--llars-primary);
}

/* Card Appear */
@keyframes card-appear {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.analysis-card {
  animation: card-appear 0.3s ease-out;
}

/* Confidence Fill */
.confidence-bar {
  transition: width 0.5s ease-out;
}

.confidence-dot {
  transition: background-color 0.2s ease;
}
```

---

## Beispiel-Interaktionen

### Szenario 1: Einfache Analyse

```
[User lädt E-Mail-Datensatz hoch]

[KI analysiert...]
  → EvalType: rating (85%)
  → Name: "E-Mail Qualitätsbewertung"
  → Beschreibung: "Bewertung der Kommunikationsqualität"

[Chat erscheint]
🤖: "Ich schlage eine Qualitätsbewertung auf einer 5-Punkte-Skala vor.
     Möchtest du die Bewertungskriterien anpassen?"

     [Skala anpassen] [Labels definieren] [Passt so ✓]
```

### Szenario 2: Typ-Änderung via Chat

```
👤: "Eigentlich sollen die Evaluatoren nur entscheiden ob die Mail
     von einem Menschen oder einer KI stammt."

🤖: "Verstanden! Das ist ein Authentizitäts-Task. Ich ändere:

     ┌─ Änderungen ─────────────────────────────┐
     │ ✓ Typ: authenticity (war: rating)        │
     │ ✓ Labels: [Mensch] [KI-generiert]        │
     └──────────────────────────────────────────┘

     Soll ich noch ein 'Unsicher'-Label hinzufügen?"

     [Ja, 'Unsicher' hinzufügen] [Nein, zwei reichen]
```

### Szenario 3: Detaillierte Konfiguration

```
👤: "Ich brauche eine Bewertung auf mehreren Dimensionen:
     Höflichkeit (1-5), Klarheit (1-5), und Professionalität (1-5)"

🤖: "Perfekt, ich richte eine Multi-Skalen-Bewertung ein:

     ┌─ Konfiguration ─────────────────────────┐
     │ Typ: rating                              │
     │                                          │
     │ Skalen:                                  │
     │ 📊 Höflichkeit      [1 ──●── 5]         │
     │ 📊 Klarheit         [1 ──●── 5]         │
     │ 📊 Professionalität [1 ──●── 5]         │
     └──────────────────────────────────────────┘

     Sollen die Skalen Textlabels haben (z.B. 'sehr unhöflich' bis
     'sehr höflich')?"
```

---

## Dateistruktur

```
llars-frontend/src/
├── components/
│   └── ScenarioWizard/
│       └── AIAnalysis/
│           ├── index.js                    # Exports
│           ├── StreamingAnalysisPanel.vue  # Container
│           ├── EvalTypeCard.vue            # Evaluationstyp
│           ├── ScenarioSuggestionCard.vue  # Name/Beschreibung
│           ├── ReasoningCard.vue           # KI-Begründung
│           ├── DataStatsCard.vue           # Daten-Übersicht
│           ├── DataQualityCard.vue         # Qualität
│           ├── AIChatPanel.vue             # Chat-Interface
│           └── ChatMessage.vue             # Einzelne Nachricht
│
├── composables/
│   ├── useStreamingParser.js   # JSON Streaming Parser
│   └── useAIChat.js            # Chat State & API
│
└── views/
    └── ScenarioManager/
        └── components/
            └── ScenarioWizard.vue  # Integration
```

---

## API Endpoints

### Bestehend

- `POST /api/ai-assist/analyze-scenario-data/stream` - Initiale Analyse

### Zu erweitern

- `POST /api/import/ai/chat-stream` - Chat für Konfigurationsverfeinerung

**Request:**
```json
{
  "session_id": "abc123",
  "messages": [
    {"role": "user", "content": "Ich möchte 3 Labels haben"}
  ],
  "current_config": {
    "evalType": "authenticity",
    "labels": ["echt", "fake"]
  }
}
```

**SSE Events:**
```
event: thinking
data: {"status": "processing"}

event: config_update
data: {"field": "labels", "value": ["echt", "fake", "unsicher"]}

event: chunk
data: {"content": "Ich habe "}

event: chunk
data: {"content": "ein drittes Label "}

event: chunk
data: {"content": "'unsicher' hinzugefügt."}

event: done
data: {"success": true}
```

---

## Nächste Schritte

1. [x] Konzept erstellen
2. [ ] StreamingAnalysisPanel.vue implementieren
3. [ ] Einzelne Cards implementieren
4. [ ] useStreamingParser.js erstellen
5. [ ] AIChatPanel.vue implementieren
6. [ ] In ScenarioWizard.vue integrieren
7. [ ] Backend Chat-Endpoint erweitern
8. [ ] E2E Tests

---

**Autor:** Claude Code
**Review:** Pending
