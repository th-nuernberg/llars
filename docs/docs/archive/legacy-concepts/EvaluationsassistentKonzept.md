# Frontend-Konzept: Neuer Evaluationsassistent

**Version:** 1.0 | **Stand:** 14. Januar 2026
**Autor:** Claude Code | **Ziel:** IJCAI-ECAI 2026 Demo Track

---

## Executive Summary

Der neue Evaluationsassistent transformiert LLARS von einem einfachen Tool-Menü zu einer **vollwertigen Evaluations-Plattform** mit:
- **LLM-as-Evaluator**: LLMs nehmen als gleichwertige "Nutzer" an Evaluationen teil
- **Live-Monitoring**: Echtzeit-Fortschritt für Researcher (nicht nur Admins)
- **Transparenz-Dashboard**: Jede Antwort, jedes Rating einsehbar
- **Researcher-Empowerment**: Volle Szenario-Verwaltung ohne Admin-Panel

---

## 1. Neue Navigationsstruktur

### 1.1 Route-Hierarchie

```
/evaluation                          # EvaluationAssistant.vue (NEU - Haupt-Container)
├── /evaluation/dashboard            # MyScenariosDashboard.vue (NEU)
├── /evaluation/create               # ScenarioWizard.vue (NEU - Step-by-Step)
├── /evaluation/scenario/:id         # ScenarioDetail.vue (NEU - Detailansicht)
│   ├── /evaluation/scenario/:id/monitor    # ScenarioMonitor.vue (NEU)
│   ├── /evaluation/scenario/:id/responses  # ResponseExplorer.vue (NEU)
│   └── /evaluation/scenario/:id/export     # ResultsExport.vue (NEU)
├── /evaluation/participate          # ParticipateHub.vue (NEU - Evaluator-Ansicht)
└── /evaluation/tools                # EvaluationToolsHub.vue (bisheriger EvaluationHub)
    ├── /Ranker
    ├── /Rater
    ├── /HistoryGeneration
    ├── /comparison
    └── /authenticity
```

### 1.2 Router-Konfiguration (router.js Erweiterung)

```javascript
// Evaluation Assistant Routes (NEU)
{
  path: '/evaluation',
  name: 'EvaluationAssistant',
  component: EvaluationAssistant,
  meta: { requiresAuth: true },
  children: [
    { path: '', redirect: { name: 'EvaluationDashboard' } },
    { path: 'dashboard', name: 'EvaluationDashboard', component: MyScenariosDashboard },
    { path: 'create', name: 'ScenarioCreate', component: ScenarioWizard },
    { path: 'participate', name: 'EvaluationParticipate', component: ParticipateHub },
    { path: 'tools', name: 'EvaluationTools', component: EvaluationToolsHub },
    {
      path: 'scenario/:id',
      name: 'ScenarioDetail',
      component: ScenarioDetail,
      children: [
        { path: '', redirect: { name: 'ScenarioMonitor' } },
        { path: 'monitor', name: 'ScenarioMonitor', component: ScenarioMonitor },
        { path: 'responses', name: 'ResponseExplorer', component: ResponseExplorer },
        { path: 'export', name: 'ResultsExport', component: ResultsExport }
      ]
    }
  ]
}
```

---

## 2. Komponenten-Architektur

### 2.1 Hauptcontainer: EvaluationAssistant.vue

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER                                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🧪 Evaluationsassistent          [Researcher: Max Mustermann]│ │
│ │ Manage your evaluation scenarios                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ NAVIGATION TABS (LTabs)                                         │
│ ┌──────────┬──────────┬──────────┬──────────┬──────────┐       │
│ │📊 Dashboard│➕ Erstellen│📈 Monitor │✏️ Teilnehmen│🛠️ Tools  │       │
│ └──────────┴──────────┴──────────┴──────────┴──────────┘       │
├─────────────────────────────────────────────────────────────────┤
│ CONTENT AREA                                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                                                              │ │
│ │                    <router-view />                           │ │
│ │                                                              │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Rollenbasierte Tab-Sichtbarkeit:**

| Tab | Admin | Researcher | Evaluator |
|-----|-------|------------|-----------|
| Dashboard | ✅ | ✅ | ❌ |
| Erstellen | ✅ | ✅ | ❌ |
| Monitor | ✅ (alle) | ✅ (eigene) | ❌ |
| Teilnehmen | ✅ | ✅ | ✅ |
| Tools | ✅ | ✅ | ✅ |

---

### 2.2 Dashboard: MyScenariosDashboard.vue

```
┌─────────────────────────────────────────────────────────────────┐
│ STATS CARDS ROW                                                 │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│ │   🟢 3       │   🟡 2       │   ⚫ 5       │   📊 10      │  │
│ │   Aktiv      │   Ausstehend │   Beendet    │   Gesamt     │  │
│ └──────────────┴──────────────┴──────────────┴──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│ FILTER ROW                                                      │
│ ┌────────────┬────────────┬────────────┬─────────────────────┐ │
│ │🔍 Suche... │ Status ▼   │ Typ ▼      │ [+ Neues Szenario]  │ │
│ └────────────┴────────────┴────────────┴─────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ SCENARIOS LIST (Cards Grid)                                     │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ ┌──────────────────────────┐ ┌──────────────────────────┐ │  │
│ │ │ 🏆 Ranking Study #1      │ │ ⭐ Rating Experiment     │ │  │
│ │ │ ━━━━━━━━━━━━━━━━━━━━━━━━ │ │ ━━━━━━━━━━━━━━━━━━━━━━━━ │ │  │
│ │ │ 📅 01.01 - 31.01.2026    │ │ 📅 15.01 - 28.02.2026    │ │  │
│ │ │ 👥 5 Menschen + 2 LLMs   │ │ 👥 3 Menschen + 1 LLM    │ │  │
│ │ │ ━━━━━━━━━━━━━━━━━━━━━━━━ │ │ ━━━━━━━━━━━━━━━━━━━━━━━━ │ │  │
│ │ │ Progress: ████████░░ 80% │ │ Progress: ██░░░░░░░░ 20% │ │  │
│ │ │                          │ │                          │ │  │
│ │ │ [📈Monitor] [✏️Edit] [🗑️]│ │ [📈Monitor] [✏️Edit] [🗑️]│ │  │
│ │ └──────────────────────────┘ └──────────────────────────┘ │  │
│ └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Szenario-Card Features:**
- Typ-Icon + Emoji
- Zeitraum mit Countdown ("endet in 5 Tagen")
- Evaluatoren-Übersicht (Menschen + LLMs separat)
- Live-Fortschrittsbalken
- Quick-Actions

---

### 2.3 Wizard: ScenarioWizard.vue

**Step-by-Step Prozess (v-stepper):**

```
┌─────────────────────────────────────────────────────────────────┐
│ STEPPER HEADER                                                  │
│ ┌─────┬─────┬─────┬─────┬─────┬─────┐                          │
│ │ ① ──│ ② ──│ ③ ──│ ④ ──│ ⑤ ──│ ⑥  │                          │
│ │Typ  │Daten│Eval.│LLMs │Zeit │Check│                          │
│ └─────┴─────┴─────┴─────┴─────┴─────┘                          │
├─────────────────────────────────────────────────────────────────┤
│ STEP CONTENT                                                    │
│                                                                 │
│ STEP 1: Evaluationstyp                                         │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Wählen Sie den Typ der Evaluation:                          ││
│ │                                                              ││
│ │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          ││
│ │ │ 🏆 Ranking   │ │ ⭐ Rating    │ │ ✉️ Verlauf   │          ││
│ │ │              │ │              │ │              │          ││
│ │ │ Features     │ │ Features     │ │ Konversation │          ││
│ │ │ sortieren    │ │ bewerten     │ │ bewerten     │          ││
│ │ └──────────────┘ └──────────────┘ └──────────────┘          ││
│ │                                                              ││
│ │ ┌──────────────┐ ┌──────────────┐                           ││
│ │ │ ⚖️ Vergleich │ │ 🕵️ Fake/Echt│                           ││
│ │ │              │ │              │                           ││
│ │ │ LLM vs LLM   │ │ Authentizität│                           ││
│ │ └──────────────┘ └──────────────┘                           ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ STEP 2: Daten auswählen                                        │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 📁 Threads auswählen                     [Import JSON] [📂] ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ ☐ Thread #1 - Beratungsgespräch Kredit    [Vorschau]       ││
│ │ ☑ Thread #2 - Kontoeröffnung              [Vorschau]       ││
│ │ ☑ Thread #3 - Beschwerde Gebühren         [Vorschau]       ││
│ │ ...                                                         ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ [Alle auswählen] [Auswahl aufheben]  Ausgewählt: 2/15      ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ STEP 3: Menschliche Evaluatoren                                │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 👥 Evaluatoren einladen                                     ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ ┌─────────────────────┐ ┌─────────────────────┐             ││
│ │ │ 👤 Max Mustermann   │ │ 👤 Erika Beispiel   │             ││
│ │ │ ○ Viewer ● Evaluator│ │ ● Viewer ○ Evaluator│             ││
│ │ └─────────────────────┘ └─────────────────────┘             ││
│ │                                                              ││
│ │ [🔗 Einladungslink generieren]                              ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ STEP 4: LLM Evaluatoren ⭐ NEU                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 🤖 LLM-Evaluatoren als Teilnehmer hinzufügen                ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ Diese LLMs werden die Evaluation automatisch durchführen.   ││
│ │                                                              ││
│ │ ┌─────────────────────┐ ┌─────────────────────┐             ││
│ │ │ 🤖 GPT-4o           │ │ 🤖 Claude 3.5       │             ││
│ │ │ ☑ Als Evaluator     │ │ ☑ Als Evaluator     │             ││
│ │ │ Provider: OpenAI    │ │ Provider: Anthropic │             ││
│ │ └─────────────────────┘ └─────────────────────┘             ││
│ │                                                              ││
│ │ ⚠️ LLM-Evaluatoren starten automatisch nach Szenario-Start ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ STEP 5: Zeitraum & Verteilung                                  │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 📅 Zeitraum                                                  ││
│ │ ┌────────────────┐  ┌────────────────┐                      ││
│ │ │ Start: 01.02.  │  │ Ende: 28.02.   │                      ││
│ │ └────────────────┘  └────────────────┘                      ││
│ │ [Heute] [+1 Woche] [+1 Monat]                               ││
│ │                                                              ││
│ │ 🔀 Verteilung                                                ││
│ │ ○ Alle erhalten alle Threads                                ││
│ │ ● Round-Robin (gleichmäßig verteilen)                       ││
│ │                                                              ││
│ │ 📋 Reihenfolge                                               ││
│ │ ○ Original  ● Gemischt (gleich)  ○ Gemischt (individuell)   ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ STEP 6: Zusammenfassung & Bestätigung                          │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ✅ Szenario-Zusammenfassung                                  ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ Name:        Ranking Study Januar 2026                      ││
│ │ Typ:         🏆 Ranking                                      ││
│ │ Zeitraum:    01.02.2026 - 28.02.2026 (28 Tage)             ││
│ │ Threads:     15 ausgewählt                                  ││
│ │ Menschen:    3 Evaluatoren, 2 Viewer                        ││
│ │ LLMs:        2 (GPT-4o, Claude 3.5 Sonnet)                  ││
│ │ Verteilung:  Round-Robin                                    ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │                                                              ││
│ │ ⚠️ Nach dem Start werden LLM-Evaluatoren sofort aktiviert. ││
│ │                                                              ││
│ │              [← Zurück]  [Szenario erstellen →]             ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

### 2.4 Live-Monitor: ScenarioMonitor.vue

```
┌─────────────────────────────────────────────────────────────────┐
│ SCENARIO HEADER                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 🏆 Ranking Study Januar 2026                    🟢 AKTIV    ││
│ │ 📅 01.02.2026 - 28.02.2026 (noch 14 Tage)                   ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ REAL-TIME METRICS (Socket.IO Live-Updates)                      │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│ │ 📊 Gesamt    │ ✅ Erledigt  │ 📈 Fortschritt│ ⏱️ Avg.Zeit │  │
│ │    75        │    52        │    69%       │    2.3 min  │  │
│ │ Aufgaben     │ Bewertungen  │              │ pro Thread  │  │
│ └──────────────┴──────────────┴──────────────┴──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│ EVALUATOR PROGRESS                                              │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 👥 Menschliche Evaluatoren                                   ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ 👤 Max Mustermann     ████████████████░░░░ 80%  (12/15) ✓   ││
│ │ 👤 Erika Beispiel     ████████░░░░░░░░░░░░ 40%  (6/15)      ││
│ │ 👤 Hans Schmidt       ████████████████████ 100% (15/15) ✓✓  ││
│ │                                                              ││
│ │ 🤖 LLM Evaluatoren                                           ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ 🤖 GPT-4o             ████████████████████ 100% (15/15) ✓✓  ││
│ │    ⚡ Durchschnitt: 0.8s pro Thread                         ││
│ │ 🤖 Claude 3.5 Sonnet  ████████████████░░░░ 80%  (12/15) ⏳  ││
│ │    ⚡ Durchschnitt: 1.2s pro Thread | Aktuell: Thread #13   ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ ACTIVITY FEED (Live)                                 🔴 LIVE   │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 14:32:15  🤖 Claude 3.5 Sonnet bewertete Thread #12         ││
│ │ 14:31:58  👤 Max Mustermann bewertete Thread #8             ││
│ │ 14:31:45  🤖 Claude 3.5 Sonnet bewertete Thread #11         ││
│ │ 14:30:22  👤 Erika Beispiel startete Evaluation             ││
│ │ 14:28:10  🤖 GPT-4o abgeschlossen (100%)                    ││
│ │ ...                                                          ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ ACTIONS                                                         │
│ [📤 Export Zwischenstand] [📧 Reminder senden] [🔍 Responses]  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2.5 Transparenz-Explorer: ResponseExplorer.vue ⭐ KEY FEATURE

```
┌─────────────────────────────────────────────────────────────────┐
│ RESPONSE EXPLORER - Vollständige Transparenz                    │
├─────────────────────────────────────────────────────────────────┤
│ FILTER BAR                                                      │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Evaluator: [Alle ▼] Thread: [Alle ▼] Nur LLMs: [☐]        │ │
│ │ Sortierung: [Nach Zeit ▼]              🔍 Suche...         │ │
│ └────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ THREAD COMPARISON VIEW                                          │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Thread #5: "Beratungsgespräch Kreditantrag"                 ││
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │                                                              ││
│ │ 📧 Konversation (Vorschau)                    [Vollansicht] ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ Kunde: Guten Tag, ich möchte einen Kredit beantragen...  │││
│ │ │ Berater: Natürlich, gerne helfe ich Ihnen...             │││
│ │ │ [...]                                                     │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ ━━━ BEWERTUNGEN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │                                                              ││
│ │ 👤 Max Mustermann                           14:32:15        ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ Ranking: 1. Empathie  2. Klarheit  3. Vollständigkeit    │││
│ │ │                                                           │││
│ │ │ Optional Comment: "Sehr gute Beratung, empathisch..."    │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ 🤖 GPT-4o                                    14:28:03       ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ Ranking: 1. Klarheit  2. Empathie  3. Vollständigkeit    │││
│ │ │                                                           │││
│ │ │ LLM Reasoning (expandable):                              │││
│ │ │ ┌────────────────────────────────────────────────────┐   │││
│ │ │ │ "Die Beratung zeichnet sich durch besondere        │   │││
│ │ │ │ Klarheit aus, da der Berater jeden Schritt des     │   │││
│ │ │ │ Kreditprozesses verständlich erklärt. Die          │   │││
│ │ │ │ Empathie kommt ebenfalls zum Ausdruck, ist aber    │   │││
│ │ │ │ weniger dominant als die strukturierte Erklärung." │   │││
│ │ │ └────────────────────────────────────────────────────┘   │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ 🤖 Claude 3.5 Sonnet                         14:31:45       ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ Ranking: 1. Empathie  2. Vollständigkeit  3. Klarheit    │││
│ │ │                                                           │││
│ │ │ LLM Reasoning:                                            │││
│ │ │ ┌────────────────────────────────────────────────────┐   │││
│ │ │ │ "Der Berater zeigt von Beginn an Verständnis für   │   │││
│ │ │ │ die Situation des Kunden und baut eine vertrauens- │   │││
│ │ │ │ volle Atmosphäre auf. Dies priorisiere ich höher   │   │││
│ │ │ │ als die reine Informationsvermittlung."            │   │││
│ │ │ └────────────────────────────────────────────────────┘   │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ ━━━ VERGLEICHS-ANALYSE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ 📊 Agreement Analysis                                     │││
│ │ │ • Mensch vs GPT-4o: 67% Übereinstimmung                  │││
│ │ │ • Mensch vs Claude: 83% Übereinstimmung                  │││
│ │ │ • GPT-4o vs Claude: 50% Übereinstimmung                  │││
│ │ │                                                           │││
│ │ │ 🔍 Auffälligkeiten:                                       │││
│ │ │ • "Klarheit" unterschiedlich bewertet (Position 1-3)     │││
│ │ │ • Menschen und Claude priorisieren "Empathie"            │││
│ │ └──────────────────────────────────────────────────────────┘││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ NAVIGATION                                                      │
│ [← Thread #4]                                     [Thread #6 →] │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2.6 Ergebnis-Export: ResultsExport.vue

```
┌─────────────────────────────────────────────────────────────────┐
│ EXPORT CENTER                                                   │
├─────────────────────────────────────────────────────────────────┤
│ AGGREGIERTE STATISTIKEN                                         │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ┌─────────────────────┐ ┌─────────────────────┐             ││
│ │ │ 📊 Inter-Rater      │ │ 📈 Übereinstimmung  │             ││
│ │ │    Agreement        │ │    Human vs LLM     │             ││
│ │ │                     │ │                     │             ││
│ │ │ Krippendorff's α:   │ │ GPT-4o:    72%     │             ││
│ │ │    0.78             │ │ Claude:    81%     │             ││
│ │ │                     │ │                     │             ││
│ │ │ Cohen's κ:          │ │ Durchschnitt: 76%  │             ││
│ │ │    0.71             │ │                     │             ││
│ │ └─────────────────────┘ └─────────────────────┘             ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ EXPORT OPTIONEN                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Format:                                                      ││
│ │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        ││
│ │ │ 📄 CSV   │ │ 📋 JSON  │ │ 📝 LaTeX │ │ 📊 Excel │        ││
│ │ └──────────┘ └──────────┘ └──────────┘ └──────────┘        ││
│ │                                                              ││
│ │ Inhalt:                                                      ││
│ │ ☑ Alle Bewertungen                                          ││
│ │ ☑ LLM-Reasoning (vollständig)                               ││
│ │ ☑ Timestamps                                                ││
│ │ ☑ Agreement-Metriken                                        ││
│ │ ☐ Thread-Inhalte (Rohtext)                                  ││
│ │                                                              ││
│ │ Anonymisierung:                                              ││
│ │ ○ Keine  ● Pseudonymisiert  ○ Vollständig anonymisiert      ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ LATEX PAPER INTEGRATION (für IJCAI)                            │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 📝 LaTeX-Tabellen generieren                                 ││
│ │                                                              ││
│ │ [Ergebnistabelle] [IRR-Tabelle] [Human vs LLM Tabelle]      ││
│ │                                                              ││
│ │ Vorschau:                                                    ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ \begin{table}[h]                                          │││
│ │ │ \centering                                                │││
│ │ │ \caption{Inter-Rater Agreement Results}                   │││
│ │ │ \begin{tabular}{lcc}                                      │││
│ │ │ \toprule                                                  │││
│ │ │ Metric & Human & LLM \\                                   │││
│ │ │ \midrule                                                  │││
│ │ │ Krippendorff's $\alpha$ & 0.78 & 0.85 \\                  │││
│ │ │ ...                                                       │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ [📋 Kopieren] [💾 Download .tex]                            ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ [📥 Export starten]                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2.7 Teilnehmer-Hub: ParticipateHub.vue

```
┌─────────────────────────────────────────────────────────────────┐
│ MEINE EVALUATIONSAUFGABEN                                       │
├─────────────────────────────────────────────────────────────────┤
│ ÜBERSICHT                                                       │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ Du hast 3 aktive Szenarien mit insgesamt 23 offenen Aufgaben││
│ └──────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ AKTIVE SZENARIEN                                                │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ 🏆 Ranking Study Januar 2026                  🔴 8 offen ││││
│ │ │ ─────────────────────────────────────────────────────────│││
│ │ │ Dein Fortschritt: ████████░░░░░░░░ 47% (7/15)           │││
│ │ │ Endet in: 14 Tagen                                       │││
│ │ │                                                          │││
│ │ │ [▶️ Weiter machen]                                       │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ ⭐ Rating Experiment                         🟡 10 offen │││
│ │ │ ─────────────────────────────────────────────────────────│││
│ │ │ Dein Fortschritt: ████░░░░░░░░░░░░ 20% (2/10)           │││
│ │ │ Endet in: 28 Tagen                                       │││
│ │ │                                                          │││
│ │ │ [▶️ Starten]                                             │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ 🕵️ Fake/Echt Studie                         🟢 5 offen  │││
│ │ │ ─────────────────────────────────────────────────────────│││
│ │ │ Dein Fortschritt: ████████████████ 75% (15/20)          │││
│ │ │ Endet in: 3 Tagen ⚠️                                     │││
│ │ │                                                          │││
│ │ │ [▶️ Abschließen]                                         │││
│ │ └──────────────────────────────────────────────────────────┘││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ ABGESCHLOSSENE SZENARIEN                          [Ausklappen]  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Datenfluss & State Management

### 3.1 Composables

```
composables/
├── useEvaluationAssistant.js       # Haupt-State für den Assistenten
├── useScenarioWizard.js            # Wizard-Logik & Validierung
├── useScenarioMonitor.js           # Live-Monitoring via Socket.IO
├── useResponseExplorer.js          # Response-Navigation & Filter
├── useEvaluationProgress.js        # Fortschritts-Berechnung
└── useLlmEvaluators.js             # LLM-Evaluator-Verwaltung
```

### 3.2 useScenarioMonitor.js (Socket.IO Integration)

```javascript
// composables/useScenarioMonitor.js
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { getSocket } from '@/services/socketService'

export function useScenarioMonitor(scenarioId) {
  const socket = ref(null)
  const stats = ref(null)
  const activityFeed = ref([])
  const isConnected = ref(false)

  // Computed
  const humanEvaluators = computed(() =>
    stats.value?.rater_stats?.filter(r => !r.is_llm) || []
  )

  const llmEvaluators = computed(() =>
    stats.value?.rater_stats?.filter(r => r.is_llm) || []
  )

  const overallProgress = computed(() => {
    if (!stats.value) return 0
    const total = stats.value.total_assignments || 0
    const done = stats.value.completed_assignments || 0
    return total > 0 ? Math.round((done / total) * 100) : 0
  })

  // Socket Handlers
  function handleStatsUpdate(payload) {
    if (payload.scenario_id !== scenarioId.value) return
    stats.value = payload.stats
  }

  function handleActivityEvent(payload) {
    if (payload.scenario_id !== scenarioId.value) return
    activityFeed.value.unshift({
      timestamp: new Date(),
      evaluator: payload.evaluator,
      is_llm: payload.is_llm,
      thread_id: payload.thread_id,
      action: payload.action
    })
    // Limit feed size
    if (activityFeed.value.length > 50) {
      activityFeed.value = activityFeed.value.slice(0, 50)
    }
  }

  function subscribe() {
    if (!socket.value || !scenarioId.value) return
    socket.value.emit('scenario:subscribe', { scenario_id: scenarioId.value })
  }

  function unsubscribe() {
    if (!socket.value || !scenarioId.value) return
    socket.value.emit('scenario:unsubscribe', { scenario_id: scenarioId.value })
  }

  // Lifecycle
  onMounted(() => {
    socket.value = getSocket()
    if (socket.value) {
      socket.value.on('scenario:stats', handleStatsUpdate)
      socket.value.on('scenario:activity', handleActivityEvent)
      socket.value.on('connect', () => {
        isConnected.value = true
        subscribe()
      })
      if (socket.value.connected) {
        isConnected.value = true
        subscribe()
      }
    }
  })

  onUnmounted(() => {
    unsubscribe()
    if (socket.value) {
      socket.value.off('scenario:stats', handleStatsUpdate)
      socket.value.off('scenario:activity', handleActivityEvent)
    }
  })

  watch(scenarioId, (newId, oldId) => {
    if (oldId) unsubscribe()
    if (newId) subscribe()
  })

  return {
    stats,
    activityFeed,
    isConnected,
    humanEvaluators,
    llmEvaluators,
    overallProgress
  }
}
```

---

## 4. Backend-Erweiterungen

### 4.1 Neue API-Endpoints

```python
# app/routes/evaluation_assistant_routes.py

# Für Researcher: Eigene Szenarien
GET  /api/evaluation/my-scenarios
POST /api/evaluation/scenarios                    # Szenario erstellen (nicht /admin!)
GET  /api/evaluation/scenarios/<id>               # Szenario-Details
PUT  /api/evaluation/scenarios/<id>               # Szenario bearbeiten
DELETE /api/evaluation/scenarios/<id>             # Szenario löschen

# Live Monitoring
GET  /api/evaluation/scenarios/<id>/monitor       # Monitoring-Daten
GET  /api/evaluation/scenarios/<id>/activity      # Activity Feed (paginated)

# Response Explorer
GET  /api/evaluation/scenarios/<id>/responses     # Alle Responses
GET  /api/evaluation/scenarios/<id>/responses/<thread_id>  # Thread-Responses

# Export
GET  /api/evaluation/scenarios/<id>/export        # Export generieren
GET  /api/evaluation/scenarios/<id>/metrics       # IRR-Metriken

# LLM Evaluator Control
POST /api/evaluation/scenarios/<id>/llm/start     # LLM-Evaluation starten
POST /api/evaluation/scenarios/<id>/llm/pause     # LLM-Evaluation pausieren
GET  /api/evaluation/scenarios/<id>/llm/status    # LLM-Status
```

### 4.2 Socket.IO Events (Erweiterung)

```python
# app/socketio_handlers/events_evaluation.py

# Client → Server
'scenario:subscribe'        # { scenario_id: int }
'scenario:unsubscribe'      # { scenario_id: int }

# Server → Client
'scenario:stats'            # { scenario_id, stats: {...} }
'scenario:activity'         # { scenario_id, evaluator, is_llm, thread_id, action }
'scenario:llm_progress'     # { scenario_id, model_id, current_thread, progress }
'scenario:completed'        # { scenario_id }
```

---

## 5. LLM-Evaluator Transparenz

### 5.1 Datenmodell-Erweiterung

```python
# DB: Erweiterung für LLM-Reasoning
class EvaluationResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, ForeignKey('rating_scenarios.scenario_id'))
    thread_id = db.Column(db.Integer, ForeignKey('email_threads.thread_id'))
    evaluator_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=True)
    llm_model_id = db.Column(db.String(100), nullable=True)  # Für LLM-Evaluatoren

    response_type = db.Column(db.String(50))  # 'ranking', 'rating', 'authenticity'
    response_data = db.Column(db.JSON)        # Die eigentliche Bewertung

    # NEU: LLM-Transparenz
    llm_reasoning = db.Column(db.Text, nullable=True)      # Vollständiges Reasoning
    llm_prompt_used = db.Column(db.Text, nullable=True)    # Der verwendete Prompt
    llm_response_time_ms = db.Column(db.Integer, nullable=True)
    llm_tokens_used = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 5.2 LLM-Evaluator Prompt-Template

```python
# app/services/llm_evaluator_service.py

RANKING_EVALUATION_PROMPT = """
Du bist ein Evaluator für eine wissenschaftliche Studie zur Beratungsqualität.

## Aufgabe
Bewerte den folgenden E-Mail-Verlauf und erstelle ein Ranking der folgenden Features
nach ihrer Ausprägung in der Beratung:

{features_list}

## E-Mail-Verlauf
{thread_content}

## Antwortformat
Antworte im folgenden JSON-Format:
{{
  "ranking": [
    {{"position": 1, "feature": "Feature-Name"}},
    {{"position": 2, "feature": "Feature-Name"}},
    ...
  ],
  "reasoning": "Detaillierte Begründung deiner Entscheidung..."
}}

Begründe deine Entscheidung ausführlich im "reasoning"-Feld.
"""
```

---

## 6. Datei-Struktur (Neue Komponenten)

```
llars-frontend/src/
├── views/
│   └── Evaluation/
│       ├── EvaluationAssistant.vue          # Haupt-Container mit Tabs
│       ├── MyScenariosDashboard.vue         # Dashboard für eigene Szenarien
│       ├── ScenarioWizard.vue               # Step-by-Step Wizard
│       ├── ScenarioDetail.vue               # Detail-Container mit Sub-Routes
│       ├── ScenarioMonitor.vue              # Live-Monitoring
│       ├── ResponseExplorer.vue             # Transparenz-Explorer
│       ├── ResultsExport.vue                # Export-Center
│       └── ParticipateHub.vue               # Teilnehmer-Ansicht
│
├── components/
│   └── Evaluation/
│       ├── EvaluationToolsHub.vue           # Bisheriger EvaluationHub (umbenannt)
│       ├── ScenarioCard.vue                 # Szenario-Karte für Dashboard
│       ├── EvaluatorProgress.vue            # Fortschritts-Anzeige pro Evaluator
│       ├── LlmEvaluatorCard.vue             # LLM-Evaluator-Karte
│       ├── ActivityFeed.vue                 # Live-Activity-Feed
│       ├── ResponseCard.vue                 # Response-Anzeige (Mensch/LLM)
│       ├── AgreementChart.vue               # Agreement-Visualisierung
│       └── ExportOptions.vue                # Export-Optionen
│
└── composables/
    ├── useEvaluationAssistant.js
    ├── useScenarioWizard.js
    ├── useScenarioMonitor.js
    ├── useResponseExplorer.js
    ├── useEvaluationProgress.js
    └── useLlmEvaluators.js
```

---

## 7. Implementierungs-Reihenfolge

### Phase 1: Grundstruktur (Woche 1-2)
1. `EvaluationAssistant.vue` - Haupt-Container mit Tab-Navigation
2. `MyScenariosDashboard.vue` - Dashboard-Ansicht
3. Router-Erweiterung
4. Backend: `/api/evaluation/my-scenarios`

### Phase 2: Wizard & Erstellung (Woche 2-3)
1. `ScenarioWizard.vue` - Step-by-Step Wizard
2. `useLlmEvaluators.js` - LLM-Auswahl-Composable
3. Backend: POST `/api/evaluation/scenarios`

### Phase 3: Live-Monitoring (Woche 3-4)
1. `ScenarioMonitor.vue` - Monitoring-View
2. `useScenarioMonitor.js` - Socket.IO Integration
3. `ActivityFeed.vue` - Live-Feed
4. Backend: Socket.IO Events

### Phase 4: Transparenz-Explorer (Woche 4-5)
1. `ResponseExplorer.vue` - Response-Ansicht
2. `ResponseCard.vue` - Response-Darstellung
3. `AgreementChart.vue` - Visualisierung
4. Backend: Response-Endpoints + LLM-Reasoning

### Phase 5: Export & Polish (Woche 5-6)
1. `ResultsExport.vue` - Export-Center
2. LaTeX-Export für IJCAI
3. `ParticipateHub.vue` - Teilnehmer-Ansicht
4. UI-Polish, Tests, Dokumentation

---

## 8. IJCAI Demo-Highlights

### Was dieses Konzept für die Demo besonders macht:

1. **Human-AI Collaboration sichtbar**
   - Menschen und LLMs arbeiten parallel
   - Live-Vergleich der Bewertungen
   - Transparenz durch LLM-Reasoning

2. **Wissenschaftliche Rigorosität**
   - IRR-Metriken (Krippendorff's α, Cohen's κ)
   - Export für wissenschaftliche Papers
   - LaTeX-Integration

3. **Real-time Feedback**
   - Socket.IO Live-Updates
   - Activity Feed zeigt Arbeit in Echtzeit
   - Fortschrittsbalken aktualisieren live

4. **Researcher Empowerment**
   - Keine Admin-Abhängigkeit
   - Vollständige Kontrolle über Szenarien
   - Export-Möglichkeiten

---

**Stand:** 14. Januar 2026
**Nächster Schritt:** Review & Freigabe durch Product Owner
