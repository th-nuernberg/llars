# Lars Demo Video - Gesamtkonzept

## Übersicht

**Ziel:** 10-minütiges Demo-Video für IJCAI-ECAI 2026 Demo Track
**Kernbotschaft:** Lars bringt Domain-Experten und AI-Entwickler zusammen für die komplette Pipeline: Prompt Engineering → Batch Generation → Hybride Evaluation

---

## 1. Demo-Szenario: News Article Summarization

### Warum dieses Szenario?
- **Universell verständlich** - jeder kennt Nachrichtenartikel
- **Zeigt alle Features** - Prompt Engineering, Batch Gen, Multi-Model Comparison
- **Konkrete Metriken** - Kohärenz, Faktentreue, Kürze messbar
- **Ranking passt perfekt** - "Welche Zusammenfassung ist besser?"

### Rollen im Video
| Rolle | Name | Aufgabe |
|-------|------|---------|
| Domain Expert | Dr. Sarah (Journalistin) | Definiert Qualitätskriterien |
| AI Developer | Max (Entwickler) | Optimiert Prompt-Struktur |
| Evaluator | Lisa | Bewertet Outputs |
| LLM Evaluator | GPT-4 | Automatische Bewertung |

---

## 2. Daten-Setup (Aufeinander abgestimmt)

### 2.1 Testdaten: 5 Nachrichtenartikel

```json
[
  {
    "id": "news_001",
    "title": "Breakthrough in Quantum Computing",
    "content": "Scientists at MIT announced a major breakthrough in quantum computing yesterday. The team successfully demonstrated a 1000-qubit processor that maintains coherence for over 10 minutes, a significant improvement over previous records. Dr. Jane Chen, lead researcher, stated that this development could accelerate drug discovery and climate modeling. The processor uses a novel error-correction technique that reduces noise by 99%. Industry experts predict commercial applications within five years.",
    "category": "Technology"
  },
  {
    "id": "news_002",
    "title": "Global Climate Summit Reaches Historic Agreement",
    "content": "World leaders at the 2026 Global Climate Summit in Berlin have agreed to reduce carbon emissions by 60% by 2035. The agreement, signed by 195 countries, includes binding commitments and financial penalties for non-compliance. Developing nations will receive $500 billion in green technology funding. Environmental groups praised the deal as 'a turning point for humanity,' while some industry representatives expressed concerns about economic impacts.",
    "category": "Environment"
  },
  {
    "id": "news_003",
    "title": "AI System Passes Medical Licensing Exam",
    "content": "An artificial intelligence system developed by Stanford researchers has passed the US Medical Licensing Examination with a score in the 90th percentile. The system, named MedAssist, demonstrated diagnostic accuracy comparable to experienced physicians across multiple specialties. However, researchers emphasize that the AI is designed to assist, not replace, human doctors. The FDA is currently reviewing the system for potential clinical use.",
    "category": "Healthcare"
  },
  {
    "id": "news_004",
    "title": "Electric Vehicle Sales Surpass Traditional Cars",
    "content": "For the first time in history, electric vehicle sales have exceeded traditional combustion engine cars globally. Data from the International Energy Agency shows that EVs accounted for 52% of new car sales in Q1 2026. Tesla, BYD, and Volkswagen lead the market. Analysts attribute the shift to falling battery costs, expanded charging infrastructure, and stricter emission regulations. The milestone was reached two years ahead of most predictions.",
    "category": "Automotive"
  },
  {
    "id": "news_005",
    "title": "New Study Links Social Media to Teen Mental Health",
    "content": "A comprehensive study involving 50,000 teenagers across 12 countries has found strong correlations between social media usage and mental health issues. Researchers at Oxford University report that teens spending more than 4 hours daily on social platforms show 40% higher rates of anxiety and depression. The study controlled for socioeconomic factors and pre-existing conditions. Experts are calling for age verification requirements and usage limits.",
    "category": "Society"
  }
]
```

### 2.2 Prompt für Zusammenfassung

```
SYSTEM:
You are an expert news editor creating concise summaries for busy readers.
Your summaries must be:
- Exactly 2 sentences long
- Factually accurate (no hallucinations)
- Include the key finding and its significance
- Written in neutral, journalistic tone

USER:
Summarize this news article:

Title: {{title}}
Category: {{category}}

Article:
{{content}}
```

### 2.3 LLM-Modelle für Vergleich
- **Mistral-Small** (schnell, günstig)
- **GPT-4** (Referenz-Qualität)
- **Claude-3-Haiku** (Alternative)

### 2.4 Evaluation: Ranking
- **Typ:** Bucket-Based Ranking (3 Buckets: Best, Acceptable, Poor)
- **Warum Ranking?** Relative Vergleiche sind für Menschen einfacher als absolute Scores
- **Metriken:** Krippendorff's α, Spearman Correlation

---

## 3. Video-Struktur (10 Minuten)

```
┌─────────────────────────────────────────────────────────────────┐
│  0:00 - 0:45  │  Intro & Problem Statement                      │
├─────────────────────────────────────────────────────────────────┤
│  0:45 - 3:00  │  Module 1: Collaborative Prompt Engineering     │
│               │  → Real-time Collaboration (2 Cursors)          │
│               │  → Version History                               │
│               │  → Direct Testing                                │
├─────────────────────────────────────────────────────────────────┤
│  3:00 - 4:30  │  Module 2: Batch Generation                     │
│               │  → Data Upload                                   │
│               │  → Multi-Model Selection                         │
│               │  → Cost Estimation & Progress                    │
├─────────────────────────────────────────────────────────────────┤
│  4:30 - 7:00  │  Module 3: Large-Scale Evaluation               │
│               │  → Scenario Wizard (AI-assisted setup)          │
│               │  → Human Evaluation Interface                    │
│               │  → LLM-as-Judge parallel                         │
│               │  → Live Agreement Dashboard                      │
├─────────────────────────────────────────────────────────────────┤
│  7:00 - 8:30  │  Standalone Use Cases                           │
│               │  → Import external data for evaluation          │
│               │  → Export for downstream use                     │
├─────────────────────────────────────────────────────────────────┤
│  8:30 - 9:30  │  Results & Impact                               │
│               │  → Agreement Metrics Visualization              │
│               │  → Human-LLM Correlation                         │
├─────────────────────────────────────────────────────────────────┤
│  9:30 - 10:00 │  Conclusion & Call to Action                    │
│               │  → Open Source, Requirements, Links             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Technische Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEMO VIDEO PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   SKRIPT    │───▶│ AUTOCLICKER │───▶│   SCREEN    │         │
│  │   (JSON)    │    │  (Python)   │    │  RECORDER   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│        │                  │                   │                 │
│        ▼                  ▼                   ▼                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │    TTS      │    │   TIMING    │    │   VIDEO     │         │
│  │  (OpenAI)   │    │   SYNC      │    │   OUTPUT    │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│        │                  │                   │                 │
│        └──────────────────┴───────────────────┘                 │
│                           │                                     │
│                           ▼                                     │
│                  ┌─────────────────┐                            │
│                  │  FINAL VIDEO    │                            │
│                  │  (Audio+Screen) │                            │
│                  └─────────────────┘                            │
│                                                                 │
│  INTERAKTIV: Live Preview + Pause/Edit bei jedem Schritt       │
└─────────────────────────────────────────────────────────────────┘
```

### Komponenten

1. **Skript-Engine** (`script.json`)
   - Timing für jeden Schritt
   - Gesprochener Text
   - UI-Aktionen (Klicks, Eingaben)
   - Pause-Punkte für manuelle Überprüfung

2. **Autoclicker** (`autoclicker.py`)
   - PyAutoGUI für Maus/Keyboard
   - Selenium für präzise Web-Interaktion
   - Wartet auf UI-Elemente (nicht nur Zeit)
   - Highlight-Effekte für Cursor

3. **Screen Recorder** (`recorder.py`)
   - OBS Studio CLI oder ffmpeg
   - 1920x1080, 30fps
   - Separater Audio-Track

4. **TTS Engine** (`tts.py`)
   - OpenAI TTS API (alloy/onyx voice)
   - Pre-generierte Audio-Dateien
   - Synchronisiert mit Aktionen

5. **Orchestrator** (`orchestrator.py`)
   - Startet alle Komponenten
   - Live-Preview Fenster
   - Pause/Resume/Edit Interface
   - Checkpoint-System

---

## 5. Interaktiver Workflow

```
┌────────────────────────────────────────────────────────────────┐
│                     RECORDING SESSION                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  [START]──▶ Scene 1 ──▶ [CHECKPOINT] ──▶ Scene 2 ──▶ ...     │
│                              │                                 │
│                              ▼                                 │
│                    ┌─────────────────┐                         │
│                    │ Preview Window  │                         │
│                    │                 │                         │
│                    │  [✓ OK]         │                         │
│                    │  [✗ Redo]       │                         │
│                    │  [✎ Edit]       │                         │
│                    └─────────────────┘                         │
│                              │                                 │
│                    ┌─────────┼─────────┐                       │
│                    ▼         ▼         ▼                       │
│               Continue    Redo     Edit Script                 │
│                              │         │                       │
│                              └────▶ Claude ◀──┘               │
│                                   Assistance                   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Steuerung während Aufnahme

| Taste | Aktion |
|-------|--------|
| `Space` | Pause/Resume |
| `R` | Aktuelle Szene wiederholen |
| `E` | Skript im Editor öffnen |
| `S` | Snapshot speichern |
| `Q` | Beenden (mit Checkpoint) |
| `N` | Nächste Szene überspringen |

---

## 6. Datei-Struktur

```
Paper/demo-video/
├── KONZEPT.md                 # Dieses Dokument
├── data/
│   ├── news_articles.json     # Testdaten
│   └── reference_summaries.json
├── scripts/
│   ├── full_script.json       # Komplettes Skript
│   ├── scene_01_intro.json
│   ├── scene_02_prompt_eng.json
│   ├── scene_03_batch_gen.json
│   ├── scene_04_evaluation.json
│   └── scene_05_outro.json
├── audio/
│   └── (generierte TTS-Dateien)
├── src/
│   ├── orchestrator.py        # Hauptsteuerung
│   ├── autoclicker.py         # UI-Automatisierung
│   ├── recorder.py            # Screen Recording
│   ├── tts.py                 # Text-to-Speech
│   └── utils.py               # Hilfsfunktionen
├── output/
│   └── (aufgenommene Videos)
└── requirements.txt
```

---

## 7. Nächste Schritte

1. **[ ] Testdaten erstellen** - news_articles.json mit 5 Artikeln
2. **[ ] Skript schreiben** - Detailliert für jede Szene
3. **[ ] Autoclicker implementieren** - Mit Selenium + PyAutoGUI
4. **[ ] TTS generieren** - OpenAI API für alle Texte
5. **[ ] Orchestrator bauen** - Mit interaktiver Steuerung
6. **[ ] Testlauf** - Erste Aufnahme, Fehler identifizieren
7. **[ ] Iteration** - Skript/Timing anpassen
8. **[ ] Finale Aufnahme** - Sauberer Durchlauf

---

## 8. Technische Anforderungen

### Software
- Python 3.10+
- OBS Studio (für Recording)
- Chrome Browser (für Selenium)
- ffmpeg (für Audio/Video Merge)

### Python Packages
```
pyautogui
selenium
webdriver-manager
openai
pydub
keyboard
mss
opencv-python
```

### Lars Setup
- Lokale Instanz unter localhost:55080
- Admin-User eingeloggt
- Testdaten vorgeladen
- 2 Browser-Fenster (für Collaboration Demo)
