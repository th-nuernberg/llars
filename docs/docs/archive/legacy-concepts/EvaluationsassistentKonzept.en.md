# Frontend Concept: New Evaluation Assistant

**Version:** 1.0 | **Date:** January 14, 2026
**Author:** Claude Code | **Goal:** IJCAI‑ECAI 2026 Demo Track

---

## Executive Summary

The new Evaluation Assistant transforms LLARS from a simple tool menu into a **full‑fledged evaluation platform** with:
- **LLM‑as‑Evaluator**: LLMs participate as equal "users" in evaluations
- **Live Monitoring**: Real‑time progress for researchers (not only admins)
- **Transparency Dashboard**: Every answer and rating visible
- **Researcher Empowerment**: Full scenario management without the admin panel

---

## 1. New Navigation Structure

### 1.1 Route Hierarchy

```
/evaluation                          # EvaluationAssistant.vue (NEW - main container)
├── /evaluation/dashboard            # MyScenariosDashboard.vue (NEW)
├── /evaluation/create               # ScenarioWizard.vue (NEW - step-by-step)
├── /evaluation/scenario/:id         # ScenarioDetail.vue (NEW - detail view)
│   ├── /evaluation/scenario/:id/monitor    # ScenarioMonitor.vue (NEW)
│   ├── /evaluation/scenario/:id/responses  # ResponseExplorer.vue (NEW)
│   └── /evaluation/scenario/:id/export     # ResultsExport.vue (NEW)
├── /evaluation/participate          # ParticipateHub.vue (NEW - evaluator view)
└── /evaluation/tools                # EvaluationToolsHub.vue (existing EvaluationHub)
    ├── /Ranker
    ├── /Rater
    ├── /HistoryGeneration
    ├── /comparison
    └── /authenticity
```

### 1.2 Router Configuration (router.js Extension)

```javascript
// Evaluation Assistant Routes (NEW)
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

## 2. Component Architecture

### 2.1 Main Container: EvaluationAssistant.vue

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER                                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🧪 Evaluation Assistant        [Researcher: Max Mustermann] │ │
│ │ Manage your evaluation scenarios                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ NAVIGATION TABS (LTabs)                                         │
│ ┌──────────┬──────────┬──────────┬──────────┬──────────┐       │
│ │📊 Dashboard│➕ Create │📈 Monitor│✏️ Participate│🛠️ Tools │       │
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

**Role‑based tab visibility:**

| Tab | Admin | Researcher | Evaluator |
|-----|-------|------------|-----------|
| Dashboard | ✅ | ✅ | ❌ |
| Create | ✅ | ✅ | ❌ |
| Monitor | ✅ (all) | ✅ (own) | ❌ |
| Participate | ✅ | ✅ | ✅ |
| Tools | ✅ | ✅ | ✅ |

---
### 2.2 Dashboard: MyScenariosDashboard.vue

```
┌─────────────────────────────────────────────────────────────────┐
│ STATS CARDS ROW                                                 │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│ │   🟢 3       │   🟡 2       │   ⚫ 5       │   📊 10      │  │
│ │   Active     │   Pending    │   Finished  │   Total      │  │
│ └──────────────┴──────────────┴──────────────┴──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│ FILTER ROW                                                      │
│ ┌────────────┬────────────┬────────────┬─────────────────────┐ │
│ │🔍 Search...│ Status ▼   │ Type ▼     │ [+ New Scenario]    │ │
│ └────────────┴────────────┴────────────┴─────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ SCENARIOS LIST (Cards Grid)                                     │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ ┌──────────────────────────┐ ┌──────────────────────────┐ │  │
│ │ │ 🏆 Ranking Study #1      │ │ ⭐ Rating Experiment     │ │  │
│ │ │ ━━━━━━━━━━━━━━━━━━━━━━━━ │ │ ━━━━━━━━━━━━━━━━━━━━━━━━ │ │  │
│ │ │ 📅 01.01 - 31.01.2026    │ │ 📅 15.01 - 28.02.2026    │ │  │
│ │ │ 👥 5 humans + 2 LLMs     │ │ 👥 3 humans + 1 LLM      │ │  │
│ │ │ ━━━━━━━━━━━━━━━━━━━━━━━━ │ │ ━━━━━━━━━━━━━━━━━━━━━━━━ │ │  │
│ │ │ Progress: ████████░░ 80% │ │ Progress: ██░░░░░░░░ 20% │ │  │
│ │ │                          │ │                          │ │  │
│ │ │ [📈Monitor] [✏️Edit] [🗑️]│ │ [📈Monitor] [✏️Edit] [🗑️]│ │  │
│ │ └──────────────────────────┘ └──────────────────────────┘ │  │
│ └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Scenario card features:**
- Type icon + emoji
- Time range with countdown ("ends in 5 days")
- Evaluator overview (humans + LLMs separately)
- Live progress bar
- Quick actions

---

### 2.3 Wizard: ScenarioWizard.vue

**Step‑by‑step process (v-stepper):**

```
┌─────────────────────────────────────────────────────────────────┐
│ STEPPER HEADER                                                  │
│ ┌─────┬─────┬─────┬─────┬─────┬─────┐                          │
│ │ ① ──│ ② ──│ ③ ──│ ④ ──│ ⑤ ──│ ⑥  │                          │
│ │Type │Data │Eval.│LLMs │Time │Check│                          │
│ └─────┴─────┴─────┴─────┴─────┴─────┘                          │
├─────────────────────────────────────────────────────────────────┤
│ STEP CONTENT                                                    │
│                                                                 │
│ STEP 1: Evaluation type                                        │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Select evaluation type:                                     ││
│ │                                                             ││
│ │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          ││
│ │ │ 🏆 Ranking   │ │ ⭐ Rating    │ │ ✉️ History   │          ││
│ │ │              │ │              │ │              │          ││
│ │ │ Sort outputs │ │ Rate outputs │ │ Rate convo   │          ││
│ │ └──────────────┘ └──────────────┘ └──────────────┘          ││
│ │                                                             ││
│ │ ┌──────────────┐ ┌──────────────┐                           ││
│ │ │ ⚖️ Comparison│ │ 🕵️ Fake/Real│                           ││
│ │ │              │ │              │                           ││
│ │ │ LLM vs LLM   │ │ Authenticity │                           ││
│ │ └──────────────┘ └──────────────┘                           ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ STEP 2: Select data                                            │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 📁 Select threads                     [Import JSON] [📂]     ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ ☐ Thread #1 - Loan counseling           [Preview]           ││
│ │ ☑ Thread #2 - Account opening           [Preview]           ││
│ │ ☑ Thread #3 - Fee complaint             [Preview]           ││
│ │ ...                                                         ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ [Select all] [Clear selection]  Selected: 2/15              ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ STEP 3: Human evaluators                                       │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 👥 Invite evaluators                                        ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ ┌─────────────────────┐ ┌─────────────────────┐             ││
│ │ │ 👤 Max Mustermann   │ │ 👤 Erika Beispiel   │             ││
│ │ │ ○ Viewer ● Evaluator│ │ ● Viewer ○ Evaluator│             ││
│ │ └─────────────────────┘ └─────────────────────┘             ││
│ │                                                              ││
│ │ [🔗 Generate invite link]                                   ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ STEP 4: LLM evaluators ⭐ NEW                                  │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 🤖 Add LLM evaluators as participants                       ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ These LLMs will run the evaluation automatically.           ││
│ │                                                              ││
│ │ ┌─────────────────────┐ ┌─────────────────────┐             ││
│ │ │ 🤖 GPT-4o           │ │ 🤖 Claude 3.5       │             ││
│ │ │ ☑ As evaluator      │ │ ☑ As evaluator      │             ││
│ │ │ Provider: OpenAI    │ │ Provider: Anthropic │             ││
│ │ └─────────────────────┘ └─────────────────────┘             ││
│ │                                                              ││
│ │ ⚠️ LLM evaluators start automatically after scenario start  ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ STEP 5: Schedule & distribution                               │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 📅 Schedule                                                  ││
│ │ ┌────────────────┐  ┌────────────────┐                      ││
│ │ │ Start: 02/01   │  │ End: 02/28     │                      ││
│ │ └────────────────┘  └────────────────┘                      ││
│ │ [Today] [+1 week] [+1 month]                                ││
│ │                                                              ││
│ │ 🔀 Distribution                                              ││
│ │ ○ Everyone gets all threads                                 ││
│ │ ● Round‑robin (even distribution)                           ││
│ │                                                              ││
│ │ 📋 Order                                                     ││
│ │ ○ Original  ● Mixed (equal)  ○ Mixed (individual)           ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ STEP 6: Summary & confirmation                                │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ✅ Scenario summary                                          ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ Name:        Ranking Study January 2026                     ││
│ │ Type:        🏆 Ranking                                      ││
│ │ Schedule:    02/01/2026 - 02/28/2026 (28 days)              ││
│ │ Threads:     15 selected                                    ││
│ │ Humans:      3 evaluators, 2 viewers                        ││
│ │ LLMs:        2 (GPT-4o, Claude 3.5 Sonnet)                  ││
│ │ Distribution: Round‑robin                                   ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │                                                              ││
│ │ ⚠️ After start, LLM evaluators are activated immediately.  ││
│ │                                                              ││
│ │              [← Back]  [Create scenario →]                  ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

### 2.4 Live Monitor: ScenarioMonitor.vue

```
┌─────────────────────────────────────────────────────────────────┐
│ SCENARIO HEADER                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 🏆 Ranking Study January 2026                   🟢 ACTIVE   ││
│ │ 📅 02/01/2026 - 02/28/2026 (14 days left)                   ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ REAL‑TIME METRICS (Socket.IO live updates)                      │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│ │ 📊 Total     │ ✅ Done      │ 📈 Progress  │ ⏱️ Avg. time │  │
│ │    75        │    52        │    69%       │    2.3 min  │  │
│ │ tasks        │ ratings      │              │ per thread  │  │
│ └──────────────┴──────────────┴──────────────┴──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│ EVALUATOR PROGRESS                                              │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 👥 Human evaluators                                         ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ 👤 Max Mustermann     ████████████████░░░░ 80%  (12/15) ✓   ││
│ │ 👤 Erika Beispiel     ████████░░░░░░░░░░░░ 40%  (6/15)      ││
│ │ 👤 Hans Schmidt       ████████████████████ 100% (15/15) ✓✓  ││
│ │                                                              ││
│ │ 🤖 LLM evaluators                                            ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ 🤖 GPT-4o             ████████████████████ 100% (15/15) ✓✓  ││
│ │    ⚡ Avg: 0.8s per thread                                  ││
│ │ 🤖 Claude 3.5 Sonnet  ████████████████░░░░ 80%  (12/15) ⏳  ││
│ │    ⚡ Avg: 1.2s per thread | Current: Thread #13            ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ ACTIVITY FEED (Live)                                 🔴 LIVE   │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 14:32:15  🤖 Claude 3.5 Sonnet rated thread #12             ││
│ │ 14:31:58  👤 Max Mustermann rated thread #8                 ││
│ │ 14:31:45  🤖 Claude 3.5 Sonnet rated thread #11             ││
│ │ 14:30:22  👤 Erika Beispiel started evaluation              ││
│ │ 14:28:10  🤖 GPT-4o completed (100%)                        ││
│ │ ...                                                          ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ ACTIONS                                                         │
│ [📤 Export interim] [📧 Send reminder] [🔍 Responses]           │
└─────────────────────────────────────────────────────────────────┘
```

---
### 2.5 Transparency Explorer: ResponseExplorer.vue ⭐ KEY FEATURE

```
┌─────────────────────────────────────────────────────────────────┐
│ RESPONSE EXPLORER - Full transparency                            │
├─────────────────────────────────────────────────────────────────┤
│ FILTER BAR                                                      │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Evaluator: [All ▼] Thread: [All ▼] LLMs only: [☐]         │ │
│ │ Sort: [By time ▼]                    🔍 Search...          │ │
│ └────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ THREAD COMPARISON VIEW                                          │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Thread #5: "Loan application counseling"                    ││
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │                                                              ││
│ │ 📧 Conversation (preview)                     [Full view]    ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ Customer: Hello, I would like to apply for a loan...      │││
│ │ │ Advisor: Of course, I will gladly help you...             │││
│ │ │ [...]                                                     │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ ━━━ RATINGS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │                                                              ││
│ │ 👤 Max Mustermann                           14:32:15        ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ Ranking: 1. Empathy  2. Clarity  3. Completeness          │││
│ │ │                                                           │││
│ │ │ Optional comment: "Very good counseling, empathetic..."  │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ 🤖 GPT-4o                                    14:28:03       ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ Ranking: 1. Clarity  2. Empathy  3. Completeness          │││
│ │ │                                                           │││
│ │ │ LLM reasoning (expandable):                               │││
│ │ │ ┌────────────────────────────────────────────────────┐   │││
│ │ │ │ "The counseling is characterized by outstanding    │   │││
│ │ │ │ clarity, as the advisor explains each step of the  │   │││
│ │ │ │ loan process clearly. Empathy is also present,     │   │││
│ │ │ │ but less dominant than the structured explanation."│   │││
│ │ │ └────────────────────────────────────────────────────┘   │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ 🤖 Claude 3.5 Sonnet                         14:31:45       ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ Ranking: 1. Empathy  2. Completeness  3. Clarity          │││
│ │ │                                                           │││
│ │ │ LLM reasoning:                                            │││
│ │ │ ┌────────────────────────────────────────────────────┐   │││
│ │ │ │ "The advisor shows understanding from the start   │   │││
│ │ │ │ and builds a trusting atmosphere. I prioritize    │   │││
│ │ │ │ this higher than pure information delivery."      │   │││
│ │ │ └────────────────────────────────────────────────────┘   │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ ━━━ COMPARISON ANALYSIS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ 📊 Agreement analysis                                     │││
│ │ │ • Human vs GPT-4o: 67% agreement                         │││
│ │ │ • Human vs Claude: 83% agreement                         │││
│ │ │ • GPT-4o vs Claude: 50% agreement                        │││
│ │ │                                                           │││
│ │ │ 🔍 Notable differences:                                   │││
│ │ │ • "Clarity" ranked differently (position 1-3)            │││
│ │ │ • Humans and Claude prioritize "Empathy"                 │││
│ │ └──────────────────────────────────────────────────────────┘││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ NAVIGATION                                                      │
│ [← Thread #4]                                     [Thread #6 →] │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2.6 Results Export: ResultsExport.vue

```
┌─────────────────────────────────────────────────────────────────┐
│ EXPORT CENTER                                                   │
├─────────────────────────────────────────────────────────────────┤
│ AGGREGATED STATISTICS                                           │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ┌─────────────────────┐ ┌─────────────────────┐             ││
│ │ │ 📊 Inter‑Rater      │ │ 📈 Agreement        │             ││
│ │ │    Agreement        │ │    Human vs LLM     │             ││
│ │ │                     │ │                     │             ││
│ │ │ Krippendorff's α:   │ │ GPT-4o:    72%      │             ││
│ │ │    0.78             │ │ Claude:    81%      │             ││
│ │ │                     │ │                     │             ││
│ │ │ Cohen's κ:          │ │ Average:   76%      │             ││
│ │ │    0.71             │ │                     │             ││
│ │ └─────────────────────┘ └─────────────────────┘             ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ EXPORT OPTIONS                                                  │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Format:                                                      ││
│ │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        ││
│ │ │ 📄 CSV   │ │ 📋 JSON  │ │ 📝 LaTeX │ │ 📊 Excel │        ││
│ │ └──────────┘ └──────────┘ └──────────┘ └──────────┘        ││
│ │                                                              ││
│ │ Content:                                                     ││
│ │ ☑ All ratings                                               ││
│ │ ☑ LLM reasoning (full)                                      ││
│ │ ☑ Timestamps                                                ││
│ │ ☑ Agreement metrics                                         ││
│ │ ☐ Thread content (raw text)                                 ││
│ │                                                              ││
│ │ Anonymization:                                               ││
│ │ ○ None  ● Pseudonymized  ○ Fully anonymized                 ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ LATEX PAPER INTEGRATION (for IJCAI)                            │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 📝 Generate LaTeX tables                                     ││
│ │                                                              ││
│ │ [Result table] [IRR table] [Human vs LLM table]             ││
│ │                                                              ││
│ │ Preview:                                                     ││
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
│ │ [📋 Copy] [💾 Download .tex]                                ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ [📥 Start export]                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2.7 Participant Hub: ParticipateHub.vue

```
┌─────────────────────────────────────────────────────────────────┐
│ MY EVALUATION TASKS                                             │
├─────────────────────────────────────────────────────────────────┤
│ OVERVIEW                                                       │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ You have 3 active scenarios with 23 open tasks total        ││
│ └──────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ ACTIVE SCENARIOS                                                │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ 🏆 Ranking Study January 2026                🔴 8 open   ││││
│ │ │ ─────────────────────────────────────────────────────────│││
│ │ │ Your progress: ████████░░░░░░░░ 47% (7/15)               │││
│ │ │ Ends in: 14 days                                         │││
│ │ │                                                          │││
│ │ │ [▶️ Continue]                                            │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ ⭐ Rating Experiment                       🟡 10 open    │││
│ │ │ ─────────────────────────────────────────────────────────│││
│ │ │ Your progress: ████░░░░░░░░░░░░ 20% (2/10)               │││
│ │ │ Ends in: 28 days                                         │││
│ │ │                                                          │││
│ │ │ [▶️ Start]                                               │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ 🕵️ Fake/Real Study                       🟢 5 open       │││
│ │ │ ─────────────────────────────────────────────────────────│││
│ │ │ Your progress: ████████████████ 75% (15/20)             │││
│ │ │ Ends in: 3 days ⚠️                                       │││
│ │ │                                                          │││
│ │ │ [▶️ Finish]                                              │││
│ │ └──────────────────────────────────────────────────────────┘││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ COMPLETED SCENARIOS                              [Expand]       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow & State Management

### 3.1 Composables

```
composables/
├── useEvaluationAssistant.js       # Main state for the assistant
├── useScenarioWizard.js            # Wizard logic & validation
├── useScenarioMonitor.js           # Live monitoring via Socket.IO
├── useResponseExplorer.js          # Response navigation & filters
├── useEvaluationProgress.js        # Progress calculation
└── useLlmEvaluators.js             # LLM evaluator management
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

  // Socket handlers
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

## 4. Backend Extensions

### 4.1 New API Endpoints

```python
# app/routes/evaluation_assistant_routes.py

# For researchers: own scenarios
GET  /api/evaluation/my-scenarios
POST /api/evaluation/scenarios                    # Create scenario (not /admin!)
GET  /api/evaluation/scenarios/<id>               # Scenario details
PUT  /api/evaluation/scenarios/<id>               # Edit scenario
DELETE /api/evaluation/scenarios/<id>             # Delete scenario

# Live monitoring
GET  /api/evaluation/scenarios/<id>/monitor       # Monitoring data
GET  /api/evaluation/scenarios/<id>/activity      # Activity feed (paginated)

# Response explorer
GET  /api/evaluation/scenarios/<id>/responses     # All responses
GET  /api/evaluation/scenarios/<id>/responses/<thread_id>  # Thread responses

# Export
GET  /api/evaluation/scenarios/<id>/export        # Generate export
GET  /api/evaluation/scenarios/<id>/metrics       # IRR metrics

# LLM evaluator control
POST /api/evaluation/scenarios/<id>/llm/start     # Start LLM evaluation
POST /api/evaluation/scenarios/<id>/llm/pause     # Pause LLM evaluation
GET  /api/evaluation/scenarios/<id>/llm/status    # LLM status
```

### 4.2 Socket.IO Events (Extension)

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

## 5. LLM Evaluator Transparency

### 5.1 Data Model Extension

```python
# DB: extension for LLM reasoning
class EvaluationResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, ForeignKey('rating_scenarios.scenario_id'))
    thread_id = db.Column(db.Integer, ForeignKey('email_threads.thread_id'))
    evaluator_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=True)
    llm_model_id = db.Column(db.String(100), nullable=True)  # For LLM evaluators

    response_type = db.Column(db.String(50))  # 'ranking', 'rating', 'authenticity'
    response_data = db.Column(db.JSON)        # The actual rating

    # NEW: LLM transparency
    llm_reasoning = db.Column(db.Text, nullable=True)      # Full reasoning
    llm_prompt_used = db.Column(db.Text, nullable=True)    # Prompt used
    llm_response_time_ms = db.Column(db.Integer, nullable=True)
    llm_tokens_used = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 5.2 LLM Evaluator Prompt Template

```python
# app/services/llm_evaluator_service.py

RANKING_EVALUATION_PROMPT = """
You are an evaluator for a scientific study on counseling quality.

## Task
Evaluate the following email thread and create a ranking of the following features
by how strongly they are expressed in the counseling:

{features_list}

## Email Thread
{thread_content}

## Response Format
Answer in the following JSON format:
{{
  "ranking": [
    {{"position": 1, "feature": "Feature name"}},
    {{"position": 2, "feature": "Feature name"}},
    ...
  ],
  "reasoning": "Detailed justification of your decision..."
}}

Explain your decision in detail in the "reasoning" field.
"""
```

---
## 6. File Structure (New Components)

```
llars-frontend/src/
├── views/
│   └── Evaluation/
│       ├── EvaluationAssistant.vue          # Main container with tabs
│       ├── MyScenariosDashboard.vue         # Dashboard for own scenarios
│       ├── ScenarioWizard.vue               # Step-by-step wizard
│       ├── ScenarioDetail.vue               # Detail container with sub routes
│       ├── ScenarioMonitor.vue              # Live monitoring
│       ├── ResponseExplorer.vue             # Transparency explorer
│       ├── ResultsExport.vue                # Export center
│       └── ParticipateHub.vue               # Participant view
│
├── components/
│   └── Evaluation/
│       ├── EvaluationToolsHub.vue           # Existing EvaluationHub (renamed)
│       ├── ScenarioCard.vue                 # Scenario card for dashboard
│       ├── EvaluatorProgress.vue            # Progress per evaluator
│       ├── LlmEvaluatorCard.vue             # LLM evaluator card
│       ├── ActivityFeed.vue                 # Live activity feed
│       ├── ResponseCard.vue                 # Response display (human/LLM)
│       ├── AgreementChart.vue               # Agreement visualization
│       └── ExportOptions.vue                # Export options
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

## 7. Implementation Order

### Phase 1: Base Structure (Week 1-2)
1. `EvaluationAssistant.vue` - Main container with tab navigation
2. `MyScenariosDashboard.vue` - Dashboard view
3. Router extension
4. Backend: `/api/evaluation/my-scenarios`

### Phase 2: Wizard & Creation (Week 2-3)
1. `ScenarioWizard.vue` - Step‑by‑step wizard
2. `useLlmEvaluators.js` - LLM selection composable
3. Backend: POST `/api/evaluation/scenarios`

### Phase 3: Live Monitoring (Week 3-4)
1. `ScenarioMonitor.vue` - Monitoring view
2. `useScenarioMonitor.js` - Socket.IO integration
3. `ActivityFeed.vue` - Live feed
4. Backend: Socket.IO events

### Phase 4: Transparency Explorer (Week 4-5)
1. `ResponseExplorer.vue` - Response view
2. `ResponseCard.vue` - Response rendering
3. `AgreementChart.vue` - Visualization
4. Backend: response endpoints + LLM reasoning

### Phase 5: Export & Polish (Week 5-6)
1. `ResultsExport.vue` - Export center
2. LaTeX export for IJCAI
3. `ParticipateHub.vue` - Participant view
4. UI polish, tests, documentation

---

## 8. IJCAI Demo Highlights

### What makes this concept special for the demo:

1. **Human‑AI collaboration made visible**
   - Humans and LLMs work in parallel
   - Live comparison of ratings
   - Transparency via LLM reasoning

2. **Scientific rigor**
   - IRR metrics (Krippendorff's α, Cohen's κ)
   - Export for scientific papers
   - LaTeX integration

3. **Real‑time feedback**
   - Socket.IO live updates
   - Activity feed shows work in real time
   - Progress bars update live

4. **Researcher empowerment**
   - No admin dependency
   - Full control over scenarios
   - Export options

---

**Date:** January 14, 2026
**Next step:** Review & approval by product owner
