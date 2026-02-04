# Lars Demo Video - Narration Script

**Gesamtdauer:** 10 Minuten | **Sprache:** Englisch | **Stimme:** OpenAI alloy

---

## Scene 1: Introduction (0:00 - 0:45)

### 01_01 | Title Slide (0:00 - 0:15)

**[VISUAL: Titelfolie mit Lars Logo, Autoren, Affiliation]**

> "Evaluating Large Language Model outputs requires two groups with complementary expertise: Domain experts who understand what constitutes quality, and AI developers who know how to structure effective prompts."

---

### 01_02 | Problem Statement (0:15 - 0:30)

**[VISUAL: Diagramm zeigt isolierte Gruppen - Annotationstools vs. LLM-Frameworks]**

> "Current tools force these groups to work in isolation. Annotation platforms lack LLM integration, while LLM evaluation frameworks require technical expertise."

---

### 01_03 | Lars Overview (0:30 - 0:45)

**[VISUAL: Browser öffnet sich, Lars Dashboard erscheint]**

> "Lars bridges this gap with three integrated modules: Collaborative Prompt Engineering, Batch Generation, and Large-Scale Evaluation. Let me show you how they work together."

---

## Scene 2: Collaborative Prompt Engineering (0:45 - 3:00)

### 02_01 | Navigate to Module (0:45 - 0:55)

**[VISUAL: Klick auf "Prompt Engineering" in Sidebar]**

> "Let's start with Collaborative Prompt Engineering. Here, domain experts and AI developers work together in real-time to develop evaluation prompts."

---

### 02_02 | Create New Prompt (0:55 - 1:10)

**[VISUAL: Klick auf "Create Prompt", Dialog öffnet sich, Name eingeben]**

> "I'll create a new prompt for news article summarization. Watch how changes are tracked at the character level - every edit shows who made it and when."

---

### 02_03 | System Block (1:10 - 1:35)

**[VISUAL: System-Block editieren, Text erscheint Zeichen für Zeichen]**

> "The system block defines the LLM's role. As a journalist, I specify that summaries must be exactly two sentences, factually accurate, and written in neutral tone. Notice how each block is editable with full version control."

---

### 02_04 | User Block with Variables (1:35 - 1:55)

**[VISUAL: User-Block editieren, Variables werden hervorgehoben]**

> "The user block contains variables in double curly braces. These placeholders - title, category, content - will be filled with actual data during batch generation."

---

### 02_05 | Real-Time Collaboration (1:55 - 2:20)

**[VISUAL: Split-Screen mit zwei Browser-Fenstern, beide zeigen denselben Prompt]**

> "Now watch real-time collaboration in action. In this second browser window, another team member - let's say our AI developer Max - joins the same prompt. Both cursors are visible, and edits synchronize instantly through conflict-free replicated data types."

---

### 02_06 | Direct Testing (2:20 - 2:40)

**[VISUAL: Test-Panel öffnen, Beispieldaten eingeben, LLM-Output erscheint]**

> "Each user can test the prompt independently without blocking others. I'll upload a sample article and immediately see how the LLM interprets our criteria. This tight feedback loop enables rapid iteration."

---

### 02_07 | Version History (2:40 - 3:00)

**[VISUAL: Version History öffnen, durch Commits scrollen]**

> "The version history tracks every change. We can compare versions, see who contributed what, and roll back if needed. This is valuable for compliance documentation under regulations like the EU AI Act."

---

## Scene 3: Batch Generation (3:00 - 4:30)

### 03_01 | Navigate to Module (3:00 - 3:10)

**[VISUAL: Klick auf "Batch Generation" in Sidebar]**

> "With our prompt refined, let's move to Batch Generation. This module bridges prompt engineering and evaluation by automating output creation at scale."

---

### 03_02 | Create Generation Job (3:10 - 3:25)

**[VISUAL: "Create Job" klicken, Job-Name eingeben]**

> "I'll create a new generation job. The system generates all combinations of evaluation items, prompt templates, and LLM models - a matrix approach for systematic comparison."

---

### 03_03 | Upload Data (3:25 - 3:45)

**[VISUAL: Datei hochladen, Felder werden automatisch erkannt]**

> "First, I upload our five news articles as the data source. The system detects the fields automatically - title, content, category - matching our prompt variables."

---

### 03_04 | Model Selection (3:45 - 4:00)

**[VISUAL: Prompt auswählen, drei LLM-Modelle anklicken]**

> "Next, I select our News Summary Prompt and choose three LLM models: Mistral-Small for speed, GPT-4 as our quality reference, and Claude-Haiku as an alternative."

---

### 03_05 | Cost Estimation (4:00 - 4:15)

**[VISUAL: Kostenübersicht wird hervorgehoben, Budget-Limit eingeben]**

> "Before execution, Lars estimates the total cost based on token counts and model pricing. I can set budget limits - jobs automatically pause if costs exceed thresholds."

---

### 03_06 | Run Generation (4:15 - 4:30)

**[VISUAL: Job starten, Progress-Bar läuft, Outputs erscheinen]**

> "Starting the job - watch the real-time progress via WebSocket. Five articles times three models equals fifteen outputs. Each result maintains full provenance: source item, prompt, and model."

---

## Scene 4: Large-Scale Evaluation (4:30 - 7:00)

### 04_01 | Convert to Scenario (4:30 - 4:45)

**[VISUAL: "To Scenario" Button klicken, Wizard öffnet sich]**

> "Now for Large-Scale Evaluation. I'll convert our generated outputs directly into an evaluation scenario. The AI-assisted Scenario Wizard analyzes the data and suggests the appropriate evaluation type."

---

### 04_02 | Wizard Recommendation (4:45 - 5:05)

**[VISUAL: Wizard zeigt "Ranking" Empfehlung]**

> "The wizard detected that we have multiple summaries per article from different models. It recommends Ranking - asking evaluators which summary is best. This makes sense: relative comparison is easier for humans than absolute scores."

---

### 04_03 | Bucket Configuration (5:05 - 5:20)

**[VISUAL: Bucket-Konfiguration, 3 Buckets auswählen]**

> "I configure bucket-based ranking with three tiers: Best, Acceptable, and Poor. Evaluators first sort summaries into buckets, then rank within each bucket - reducing cognitive load for large-scale evaluations."

---

### 04_04 | Evaluation Interface (5:20 - 5:40)

**[VISUAL: Evaluation-View öffnet sich, Drag&Drop von Items in Buckets]**

> "Here's the evaluation interface. Each article appears with its three candidate summaries. Evaluators drag and drop to rank them. The interface is designed for domain experts - no technical knowledge required."

---

### 04_05 | LLM-as-Judge (5:40 - 6:05)

**[VISUAL: Settings öffnen, LLM Evaluator aktivieren, GPT-4 auswählen]**

> "Human evaluation is the gold standard, but domain experts' time is limited. That's why Lars supports LLM evaluators running in parallel. I'll add GPT-4 as an LLM judge using the same ranking criteria. Watch how both human and machine evaluations proceed simultaneously."

---

### 04_06 | Live Agreement Dashboard (6:05 - 6:30)

**[VISUAL: Dashboard zeigt Agreement-Matrix, Metriken werden hervorgehoben]**

> "The real power is in the live agreement dashboard. Lars computes agreement across all evaluator combinations in real-time: human-human for inter-annotator reliability, LLM-LLM for model consistency, and critically, human-LLM alignment. Here we see Krippendorff's alpha, Cohen's kappa, and correlation coefficients updating as evaluations come in."

---

### 04_07 | Disagreement Analysis (6:30 - 7:00)

**[VISUAL: Disagreement-Tab öffnen, Chart zeigt Muster]**

> "The dashboard immediately reveals insights. In this case, GPT-4 tends to prefer longer summaries while human evaluators value conciseness. This disagreement pattern - visible in real-time - tells us exactly where to focus our next iteration. We can return to prompt engineering with these insights and refine our criteria until alignment improves."

---

## Scene 5: Standalone Use Cases (7:00 - 8:30)

### 05_01 | Export from Batch Generation (7:00 - 7:15)

**[VISUAL: Batch Generation, Export als CSV]**

> "Each module also works independently. Let me show you standalone use cases. First, Batch Generation without evaluation - useful for creating synthetic training data or test datasets."

---

### 05_02 | Import External Data (7:15 - 7:35)

**[VISUAL: Scenarios, Import External Data Dialog]**

> "Second, evaluation without batch generation. I can import existing outputs from any source - production systems, competitor analyses, research datasets. Here I'll upload a CSV with pre-generated summaries from an external system."

---

### 05_03 | Prompt Engineering Standalone (7:35 - 7:55)

**[VISUAL: Prompt Engineering, Export als JSON]**

> "And third, prompt engineering as a standalone training environment. Organizations use this workspace to document prompt development decisions with full attribution - relevant for compliance and knowledge transfer."

---

### 05_04 | Modular Adoption (7:55 - 8:30)

**[VISUAL: Diagramm zeigt modulare Adoption]**

> "The modular design means teams can adopt Lars incrementally. Start with evaluation for an existing project, add batch generation when you need scale, and bring in collaborative prompt engineering when domain experts join the team."

---

## Scene 6: Results & Impact (8:30 - 9:30)

### 06_01 | Counseling Case Study (8:30 - 9:00)

**[VISUAL: Dashboard mit Ergebnissen, Correlation Chart]**

> "In our deployment evaluating counseling responses, this workflow improved human-LLM agreement by 12 percent over four weeks. Five psychology students and two LLM evaluators collected 2,400 ratings. The live agreement metrics helped us identify systematic biases and iterate on our prompts until criteria were properly captured."

---

### 06_02 | Key Insight (9:00 - 9:30)

**[VISUAL: Diagramm zeigt Domain Expert + AI Developer = Better Prompts]**

> "The key insight: domain experts know what matters but struggle to express it in prompts. AI developers can write effective prompts but lack domain knowledge. Lars brings both groups into a shared environment where they iterate together until criteria are properly captured and validated at scale."

---

## Scene 7: Conclusion (9:30 - 10:00)

### 07_01 | Call to Action (9:30 - 10:00)

**[VISUAL: Abschluss-Folie mit Links und Requirements]**

> "Lars is open-source under MIT license. It requires Docker, 16 gigabytes of RAM, and supports over 100 LLM providers through LiteLLM. Visit our repository to get started, and find us at the demo booth to try it yourself. Thank you for watching."

---

## Timing Summary

| Scene | Start | End | Duration |
|-------|-------|-----|----------|
| 1. Introduction | 0:00 | 0:45 | 45s |
| 2. Prompt Engineering | 0:45 | 3:00 | 135s |
| 3. Batch Generation | 3:00 | 4:30 | 90s |
| 4. Evaluation | 4:30 | 7:00 | 150s |
| 5. Standalone | 7:00 | 8:30 | 90s |
| 6. Results | 8:30 | 9:30 | 60s |
| 7. Conclusion | 9:30 | 10:00 | 30s |
| **Total** | | | **600s (10 min)** |

---

## Notes for Recording

1. **Pacing:** Sprich ruhig und deutlich. Pause nach wichtigen Punkten.
2. **Synchronisation:** Aktionen sollten leicht NACH dem entsprechenden Text beginnen.
3. **Highlights:** Cursor-Highlights zeigen, wohin der Zuschauer schauen soll.
4. **Wiederholungen:** Bei Fehlern das Segment wiederholen (R-Taste).
5. **Checkpoints:** Nach jeder Szene wird automatisch ein Checkpoint gespeichert.
