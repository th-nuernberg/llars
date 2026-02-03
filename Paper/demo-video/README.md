# LLARS Demo Video - IJCAI 2026 Demo Track

Automatisiertes Demo-Video-System für die LLARS-Plattform.

## Quick Start

```bash
cd Paper/demo-video

# 1. Skript prüfen
python run.py --list          # Alle Schritte anzeigen
python run.py --preview       # Detaillierte Vorschau

# 2. Audio generieren (nur geänderte Sections)
python run.py --smart

# 3. Element-Test (ohne Aufnahme)
python run.py --test

# 4. Video aufnehmen
python run.py
```

---

## Architektur

```
Paper/demo-video/
├── run.py              # Hauptskript (Browser-Automation + TTS)
├── SCRIPT.json         # Einzige Wahrheitsquelle für alle Schritte
├── src/
│   └── tts.py          # Qwen3-TTS Integration
├── audio/              # Generierte Audio-Dateien
│   └── .section_hashes.json  # Hashes für Section-Caching
├── voices/             # Voice-Referenzen (optional)
└── output/             # Fertige Videos
```

---

## Features

### Two-Speaker Dialog System

| Sprecher | Name | Rolle | Stimme |
|----------|------|-------|--------|
| `host` | Alex | Amerikanischer Tech-Presenter | Aiden (Qwen3) |
| `narrator` | David | Britischer Beobachter | Ryan (Qwen3) |

**Dialog-Stil:** Host erklärt Features, Narrator stellt Fragen.

### Real-Time Collaboration Demo

Das Video zeigt Live-Kollaboration mit **zwei Browser-Fenstern**:
1. **Haupt-Browser:** Admin-User bearbeitet Prompt
2. **Collab-Browser:** Researcher-User tippt gleichzeitig

```json
{"do": "collab_open", "user": "researcher"},
{"do": "collab_goto", "url": "/PromptEngineering/3"},
{"do": "collab_type", "target": "First Block Editor", "text": "\n# Added by researcher"}
```

### Section-basiertes Audio-Caching

Audio wird nur für geänderte Sections neu generiert:

```bash
python run.py --smart                   # Nur geänderte Sections
python run.py --smart --sections INTRO  # Nur bestimmte Section erzwingen
```

**Sections im Skript (27 Schritte total):**

| Section | Audio-Dateien | Beschreibung |
|---------|---------------|--------------|
| INTRO | 2 | Einführung und Problemstellung |
| PROMPT ENGINEERING | 11 | Prompt-Editor + Live-Collab Demo |
| BATCH GENERATION | 5 | Batch-Processing zeigen |
| SCENARIO MANAGER | 6 | Evaluations-System |
| CONCLUSION | 3 | Zusammenfassung + GitHub Link |

---

## TTS-Modelle

| Modell | Beschreibung | Empfohlen |
|--------|--------------|-----------|
| `custom-small` | Vordefinierte Stimmen (Ryan, Aiden) - schnell | **Ja** |
| `custom` | Größeres Modell mit vordefinierten Stimmen | Für Qualität |
| `design` | Voice Design (Text-basierte Parameter) | Nein |
| `small/large` | Voice Cloning (benötigt Referenz-Audio) | Nur finale Produktion |

```bash
python run.py --smart --model custom-small  # Standard (schnell)
python run.py --smart --model custom        # Bessere Qualität
```

**Hinweis:** Die Warnung `does not support create_voice_clone_prompt` ist normal - das custom-small Modell nutzt vordefinierte Stimmen statt Voice Cloning.

---

## Skript-Struktur (SCRIPT.json)

```json
{
  "config": {
    "url": "http://localhost:55080",
    "tts_model": "custom-small",
    "speakers": {
      "host": {"name": "Alex", "macos_voice": "Fred"},
      "narrator": {"name": "David", "macos_voice": "Daniel"}
    }
  },
  "steps": [
    {
      "_section": "=== INTRO (25s) ===",
      "id": "intro_1",
      "speaker": "narrator",
      "narration": "Alex, I've been hearing about this LLARS system...",
      "actions": [
        {"do": "show_title", "title": "LLARS", "subtitle": "LLM Assisted Rating System"}
      ]
    }
  ]
}
```

---

## Verfügbare Actions

| Action | Beschreibung | Beispiel |
|--------|--------------|----------|
| `click` | Element klicken | `{"do": "click", "target": "Prompt Engineering"}` |
| `goto` | URL navigieren | `{"do": "goto", "url": "/Home"}` |
| `wait` | Pause | `{"do": "wait", "seconds": 1.5}` |
| `highlight` | Element hervorheben | `{"do": "highlight", "target": "...", "duration": 2}` |
| `sync` | Warten bis Narration erreicht | `{"do": "sync", "after": "Variables"}` |
| `show_title` | Titel-Overlay anzeigen | `{"do": "show_title", "title": "...", "subtitle": "..."}` |
| `type` | Text tippen | `{"do": "type", "target": "Input", "text": "..."}` |

### Collaboration Actions

| Action | Beschreibung | Beispiel |
|--------|--------------|----------|
| `collab_open` | Zweiten Browser öffnen | `{"do": "collab_open", "user": "researcher"}` |
| `collab_goto` | Collab-Browser navigieren | `{"do": "collab_goto", "url": "/PromptEngineering/3"}` |
| `collab_type` | Text im Collab-Browser tippen | `{"do": "collab_type", "target": "First Block Editor", "text": "..."}` |
| `collab_focus` | Editor im Collab-Browser fokussieren | `{"do": "collab_focus"}` |
| `collab_click` | Element im Collab-Browser klicken | `{"do": "collab_click", "target": "..."}` |
| `collab_close` | Collab-Browser schließen | `{"do": "collab_close"}` |

---

## CLI-Referenz

```
python run.py [OPTIONS]

INFO & PREVIEW:
  --list, -l              Liste aller Schritte
  --preview, -p           Detaillierte Vorschau

AUDIO:
  --smart                 Nur geänderte Sections generieren (EMPFOHLEN)
  --sections SECTION...   Bestimmte Sections erzwingen (mit --smart)
  --audio, -a             Alle Audio-Dateien generieren
  --force, -f             Cache ignorieren
  --only STEP_ID...       Nur bestimmte Steps
  --play [STEP_ID]        Audio abspielen

TEST:
  --test, -t              Element-Test ohne Aufnahme

AUFNAHME:
  --silent, -s            Ohne Audio-Wiedergabe
  --from STEP_ID          Ab bestimmtem Step starten
  --no-record             Ohne Video-Aufnahme

SONSTIGES:
  --model MODEL           TTS-Modell (custom-small, custom, design, small, large)
  --voice-clone           Voice Cloning aktivieren (sehr langsam)
```

---

## Demo-Daten (Seeder)

Das Backend enthält einen Seeder für vorbereitete Demo-Daten:

- **2 News-Summarization Prompts** (News Summary Prompt, Detailed Summary Prompt)
- **1 abgeschlossener Batch-Generation Job** mit 40 Outputs
- **10 News-Artikel** mit generierten Zusammenfassungen (2 Modelle x 2 Prompts)

```bash
# Seeder läuft automatisch bei PROJECT_STATE=development
docker compose restart llars_flask_service
```

**Seeder-Datei:** `app/db/seeders/demo_video_data.py`

---

## Typische Workflows

```bash
# Narration geändert (empfohlen)
python run.py --smart && python run.py

# Nur eine Section neu generieren
python run.py --smart --sections "PROMPT ENGINEERING"

# Actions geändert (kein Audio nötig)
python run.py --test && python run.py

# Alles neu generieren
python run.py --audio --force && python run.py

# Quick Test ab bestimmtem Step
python run.py --test --from collab_1

# Audio abspielen zur Kontrolle
python run.py --play intro_1
python run.py --play all
```

---

## Element-Mapping

In `run.py` gibt es `ELEMENT_MAP` - eine Zuordnung von lesbaren Namen zu CSS-Selektoren:

```python
ELEMENT_MAP = {
    "Prompt Engineering": ".feature-card:contains('Prompt')",
    "Batch Generation": ".feature-card:contains('Generation')",
    "News Summary Prompt": ".prompt-card:contains('News Summary')",
    "First Block Editor": ".block-editor:first-of-type .ql-editor",
    ...
}
```

### Selektor finden:
1. LLARS öffnen in Chrome
2. Rechtsklick → Untersuchen auf das Element
3. Selektor kopieren oder `data-testid` suchen
4. In ELEMENT_MAP eintragen

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| TTS-Modell lädt nicht | `pip install qwen3-tts torch` |
| Browser findet Element nicht | Element-Map in run.py erweitern |
| Collab-Cursor nicht sichtbar | LLARS muss mit YJS-Server laufen |
| Audio zu langsam | `--model custom-small` nutzen |
| "does not support create_voice_clone_prompt" | Normal - Modell nutzt vordefinierte Stimmen |
| Section-Hash nicht gespeichert | Prüfe `audio/.section_hashes.json` |
| ffmpeg fehlt | `brew install ffmpeg` (macOS) |

---

## Video-Specs

- **Auflösung:** 1920x1080 (Full HD)
- **Ziel-Länge:** 4-5 Minuten
- **Sprache:** Englisch
- **Format:** MP4

---

## Abhängigkeiten

```bash
pip install selenium webdriver-manager qwen3-tts torch soundfile
```

---

## Entwicklungsstand

- [x] Browser-Automation (Selenium)
- [x] Two-Speaker Dialog System
- [x] Qwen3-TTS Integration
- [x] Section-basiertes Audio-Caching
- [x] Real-Time Collaboration Demo (zwei Browser)
- [x] Demo-Daten Seeder
- [x] Element-Test Mode
- [ ] Bildschirmaufnahme (ffmpeg)
- [ ] Finale Video-Produktion
