# LLARS IJCAI-ECAI 2026 Demo Paper - Notes & Key Concepts

**Ziel:** Paper neu schreiben mit Fokus auf drei Hauptinnovationen:
1. **LLM-as-Evaluator** (nicht nur LLM-as-Judge!)
2. **Scenario Wizard** mit automatischem Daten-Mapping
3. **Kollaboratives Prompt Engineering**

---

## 1. LLM-AS-EVALUATOR (Hauptinnovation!)

### Unterschied zu LLM-as-Judge
- **LLM-as-Judge** (z.B. MT-Bench, Chatbot Arena): Fokus auf paarweisen Vergleich (A vs B)
- **LLM-as-Evaluator** (LLARS): LLMs als vollwertige Evaluatoren bei ALLEN Aufgabentypen

### Was LLARS bietet
LLMs können bei **jedem Szenario-Typ** als Evaluatoren eingesetzt werden:

| Szenario-Typ | LLM-Evaluator Fähigkeiten |
|--------------|---------------------------|
| **Rating** | Multi-dimensionale Bewertung (Kohärenz, Flüssigkeit, Relevanz, Konsistenz) |
| **Ranking** | Items in Kategorien/Reihenfolge sortieren |
| **Labeling** | Kategorien zuweisen (binär, multi-class, multi-label) |
| **Comparison** | Paarweiser Vergleich mit Konfidenz |
| **Authenticity** | Echt vs. Fake Erkennung |
| **Mail Rating** | Domain-spezifische Beratungsqualität |

### Technische Features
- **Multi-Provider Integration**: OpenAI, Anthropic, Google, lokale Modelle via LiteLLM
- **BYOK (Bring Your Own Key)**: Benutzer können eigene API-Keys einbinden
- **Admin-kontrollierte Modelle**: Institutionen können erlaubte Modelle definieren
- **Real-time Progress**: Socket.IO für Live-Updates während Evaluation
- **Token Tracking**: Automatische Kosten- und Token-Verfolgung

### Code-Evidenz
```vue
<!-- ScenarioOwnerCard.vue -->
<div class="stat" v-if="scenario.llm_evaluator_count > 0">
  <LIcon size="16" color="grey">mdi-robot-outline</LIcon>
  <span>{{ scenario.llm_evaluator_count }} {{ $t('scenarioManager.card.llms') }}</span>
</div>
```

```javascript
// useLLMEvaluation.js
export const TASK_TYPES = {
  RANKING: 'ranking',
  RATING: 'rating',
  AUTHENTICITY: 'authenticity',
  MAIL_RATING: 'mail_rating',
  COMPARISON: 'comparison',
  LABELING: 'labeling'
}
```

### Formulierungsvorschläge
- "LLARS treats LLMs as first-class evaluators alongside human annotators"
- "Unlike LLM-as-Judge approaches limited to pairwise comparison, LLARS enables LLMs to participate in rating, ranking, labeling, and authenticity assessment tasks"
- "Researchers can assign both human evaluators and LLM evaluators to any scenario, enabling direct comparison of human and machine judgments"

---

## 2. SCENARIO WIZARD mit AI-gestütztem Daten-Mapping

### Kernfunktionalität
- **Datei-Upload**: JSON, CSV, XLSX per Drag & Drop
- **AI-Analyse**: Automatische Erkennung des passenden Evaluierungstyps
- **Schema-Mapping**: Automatisches Mapping auf LLARS-Datenstruktur
- **Vorschau**: Sofortige Vorschau der importierten Daten

### 5-Schritt Wizard
1. **Daten hochladen** - Drag & Drop oder Dateiauswahl
2. **Aufgabentyp wählen** - AI-Vorschlag + manuelle Auswahl
3. **Konfiguration** - Dimensionen, Skalen, Presets
4. **Team zusammenstellen** - Menschen UND LLMs einladen
5. **Zusammenfassung** - Review und Start

### AI-Analyse Heuristiken
| Datenmerkmal | Vorgeschlagener Typ |
|--------------|---------------------|
| Ground-Truth Labels | labeling |
| Paare zum Vergleichen | comparison |
| Items für Reihenfolge | ranking |
| Qualität bewerten | rating |

### Presets für verschiedene Domains
- **LLM-Judge Standard**: Kohärenz, Flüssigkeit, Relevanz, Konsistenz
- **SummEval**: Zusammenfassungsqualität
- **Antwort-Qualität**: Hilfsbereitschaft, Genauigkeit, Ton
- **Beratungsqualität**: Empathie, Klarheit, Professionalität

### Formulierungsvorschläge
- "The Scenario Wizard employs AI-assisted data analysis to automatically detect appropriate evaluation types and map uploaded data to LLARS's internal schema"
- "Researchers can bring their own datasets in common formats (JSON, CSV, XLSX) and have them automatically configured for evaluation"
- "A five-step guided workflow enables both novice and expert users to quickly set up complex evaluation scenarios"

---

## 3. KOLLABORATIVES PROMPT ENGINEERING

### Kernfunktionalität
- **Multi-User Editing**: Gleichzeitige Bearbeitung von Prompts
- **Yjs CRDT-basiert**: Konfliktfreie Synchronisation
- **Live Cursor**: Sehen wo andere gerade arbeiten
- **Sharing**: Prompts mit Team teilen
- **Git-like Versioning**: Diff-Visualisierung, History

### Features
- **Eigene Prompts**: Erstellen, bearbeiten, teilen
- **Geteilte Prompts**: Von anderen geteilte Prompts bearbeiten
- **Template-Variablen**: Platzhalter für dynamische Inhalte
- **Test-Interface**: Prompts direkt testen

### Anwendungsfälle
- Teams entwickeln gemeinsam Evaluation-Rubrics
- Iteratives Verfeinern von LLM-Evaluator Prompts
- Teilen von bewährten Prompts zwischen Projekten

### Formulierungsvorschläge
- "LLARS provides a collaborative prompt engineering workspace where research teams can jointly develop and refine evaluation criteria"
- "Real-time multi-user editing with conflict-free synchronization enables distributed teams to iterate on prompts simultaneously"
- "Prompts can be shared across teams and projects, promoting reuse of validated evaluation criteria"

---

## 4. BESTE FORMULIERUNGEN AUS ALTEN PAPERN

### Abstract (alt - anpassen!)
> "We demonstrate LLARS, an open-source platform that integrates human evaluation, LLM-as-Judge automation, and retrieval-augmented generation (RAG) for systematic assessment of large language model outputs."

### Neu (Vorschlag):
> "We demonstrate LLARS, an open-source platform that uniquely treats LLMs as first-class evaluators alongside human annotators across multiple evaluation paradigms including rating, ranking, labeling, and comparison. LLARS combines (1) a scenario wizard with AI-assisted data mapping for rapid study setup, (2) collaborative prompt engineering for distributed teams, and (3) comprehensive inter-rater agreement analysis between human and machine evaluators."

### Positioning (wichtig!)
> "Existing tools address parts of this challenge: Label Studio and Argilla offer annotation interfaces but lack integrated LLM evaluation; Chatbot Arena provides pairwise comparison but operates as a public benchmark rather than a customizable research tool. None combine human evaluation, LLM-as-Evaluator, and collaborative prompt engineering in a single platform."

### Use Case Results (beibehalten)
> "2,400 ratings and 600 rankings collected over 4 weeks. Inter-annotator agreement ranged from α = 0.61 to 0.78. LLM-as-Judge showed moderate correlation (r = 0.54) with human rankings."

---

## 5. ARCHITEKTUR-ÜBERBLICK

### Stack
- **Backend**: Flask 3.0 + MariaDB + ChromaDB
- **Frontend**: Vue.js 3.4 + Vuetify 3.5
- **Real-time**: Socket.IO + Yjs CRDT
- **LLM Integration**: LiteLLM (100+ Provider)
- **Auth**: Authentik OAuth2/OIDC

### Evaluation Types (DB IDs)
| ID | Type | Description |
|----|------|-------------|
| 1 | ranking | Items sortieren/kategorisieren |
| 2 | rating | Multi-dimensionales Rating |
| 3 | mail_rating | E-Mail-Beratung (→ rating) |
| 4 | comparison | Paarweiser Vergleich |
| 5 | authenticity | Echt/Fake (→ labeling) |
| 7 | labeling | Kategorien zuweisen |

---

## 6. VERGLEICHSTABELLE FÜR PAPER

| Feature | LLARS | Label Studio | Argilla | Chatbot Arena |
|---------|-------|--------------|---------|---------------|
| Human Annotation | ✓ | ✓ | ✓ | ✓ |
| LLM-as-Evaluator (all types) | ✓ | ✗ | ✗ | ✗ |
| LLM-as-Judge (pairwise) | ✓ | ✗ | ✓ | ✓ |
| Scenario Wizard | ✓ | ✗ | ✗ | ✗ |
| Auto Data Mapping | ✓ | ✗ | ✗ | ✗ |
| Collaborative Prompts | ✓ | ✗ | ✗ | ✗ |
| Real-time Collab | ✓ | ✗ | Limited | ✗ |
| BYOK (Own API Keys) | ✓ | ✗ | ✗ | ✗ |
| Multi-Provider LLM | ✓ | ✗ | Limited | Limited |
| Agreement Metrics | 9 metrics | Manual | Limited | Leaderboard |
| Open Source | ✓ | ✓ | ✓ | ✗ |

---

## 7. DEMO SCENARIO (für Paper)

1. **Upload Dataset**: Researcher uploads CSV with text samples
2. **AI Analysis**: Wizard suggests "rating" with "response-quality" preset
3. **Configure**: Adjust dimensions (Helpfulness, Accuracy, Tone)
4. **Add Evaluators**: 3 human annotators + GPT-4 + Claude-3
5. **Start Evaluation**: All evaluators (human & LLM) rate items
6. **Compare**: View agreement metrics between humans and LLMs
7. **Iterate**: Refine LLM prompts in collaborative workspace

---

## 8. KEY MESSAGES

1. **LLM-as-Evaluator > LLM-as-Judge**: Broader scope, all evaluation types
2. **Human + Machine**: First-class support for both, direct comparison
3. **Scenario Wizard**: Rapid study setup with AI assistance
4. **Collaborative Prompts**: Teams develop evaluation criteria together
5. **Production-Ready**: Deployed in real research (counseling domain)

---

## 9. PAPER STRUCTURE (Vorschlag)

1. **Introduction** (~0.5 page)
   - Problem: Need for flexible human+LLM evaluation
   - Gap: Existing tools limited to specific paradigms
   - Contribution: LLM-as-Evaluator + Wizard + Collab Prompts

2. **System Overview** (~0.5 page)
   - Architecture diagram (simplified)
   - Key components

3. **Key Innovations** (~1.5 pages)
   - 3.1 LLM-as-Evaluator
   - 3.2 Scenario Wizard
   - 3.3 Collaborative Prompt Engineering

4. **Application** (~0.3 page)
   - Counseling use case, metrics

5. **Demo Scenario** (~0.2 page)
   - What attendees will experience

6. **References** (~2 pages)
