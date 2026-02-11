# Lars Demo Video - IJCAI 2026 Demo Track

Automatisiertes Demo-Video-System für die Lars-Plattform.

Dieses Verzeichnis dient der Produktion eines **Demo-Videos für den IJCAI‑ECAI 2026 Demonstrations Track**. IJCAI ist eine internationale, gemeinnützige Organisation und richtet eine der führenden AI-Konferenzen aus; IJCAI‑ECAI 2026 findet in Bremen vom 15.–21. August 2026 statt. Nützliche Einstiegslinks:
- [IJCAI-ECAI 2026 (Offizielle Konferenzseite)](https://2026.ijcai.org/)
- [IJCAI-ECAI 2026 Demonstrations Track (Call for Papers)](https://2026.ijcai.org/ijcai-ecai-2026-call-for-papers-demos/)
- [IJCAI Organisation (Hauptseite)](https://www.ijcai.org/home)

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
├── run.py                    # Hauptskript (Browser-Automation + TTS + Recording)
├── SCRIPT.json               # Einzige Wahrheitsquelle für alle Schritte
├── data/                     # Demo-Inputs (z.B. news_articles.json)
├── src/
│   └── tts.py                # Qwen3-TTS Integration (qwen-tts)
├── audio/                    # Generierte Audio-Dateien
│   ├── .section_hashes.json  # Hashes für Section-Caching
│   └── .audio_hashes.json    # Hashes pro Step (Text + TTS-Setup)
├── voices/                   # Voice-Referenzen (optional, für Voice Cloning)
└── output/                   # Fertige Videos
```

---

## Features

### Two-Speaker Dialog System

| Sprecher | Name | Rolle | Stimme |
|----------|------|-------|--------|
| `moderator` | Alex | Amerikanischer Tech-Presenter | Aiden (Qwen3 CustomVoice) |
| `guest` | David | Britischer Beobachter | Ryan (Qwen3 CustomVoice) |

**Dialog-Stil:** Moderator erklärt Features, Guest stellt Fragen.

### Real-Time Collaboration Demo

Das Video zeigt Live-Kollaboration mit **zwei Browser-Fenstern**:
1. **Haupt-Browser:** `ijcai_reviewer_1` bearbeitet Prompt
2. **Collab-Browser:** `ijcai_reviewer_2` tippt gleichzeitig

```json
{"do": "collab_open", "user": "ijcai_reviewer_2", "password": "ijcai_reviewer_123"},
{"do": "collab_goto", "url": "/promptengineering"},
{"do": "collab_type", "target": "First Block Editor", "text": "\n# Added by reviewer"}
```

### Section-basiertes Audio-Caching

Audio wird nur für geänderte Sections neu generiert:

```bash
python run.py --smart                   # Nur geänderte Sections
python run.py --smart --sections INTRO  # Nur bestimmte Section erzwingen
```

**Sections im Skript (Stand: `SCRIPT.json`, 68 Schritte / 68 Audio-Dateien):**

| Section | Audio-Dateien | Beschreibung |
|---------|---------------|--------------|
| INTRO | 4 | Einführung und Problemstellung |
| PROMPT ENGINEERING | 16 | Prompt-Editor + Live-Collab Demo |
| BRING YOUR OWN MODELS | 3 | Provider-Setup |
| BATCH GENERATION | 12 | Batch-Processing zeigen |
| SCENARIO FROM BATCH | 6 | Szenario-Wizard aus Batch |
| SCENARIO MANAGER | 9 | Workspace + Tabs |
| HUMAN EVALUATION | 5 | Ranking UI |
| DOCUMENTATION | 7 | MkDocs Documentation |
| CONCLUSION | 3 | Zusammenfassung + Link |

Hinweis: Sections für `--sections` sind die Großbuchstaben-Namen (z.B. `PROMPT ENGINEERING`).

---

## TTS-Modelle

| Modell | Beschreibung | Empfohlen |
|--------|--------------|-----------|
| `custom-small` | Vordefinierte Stimmen (Ryan, Aiden) - schnell | **Ja** |
| `custom` | Größeres CustomVoice-Modell | Für Qualität |
| `design` | Voice Design (Text-basierte Parameter) | Nein |
| `small/large` | Base-Modelle für Voice Cloning (mit `--voice-clone`) | Nur finale Produktion |

```bash
python run.py --smart --model custom-small  # Standard (schnell)
python run.py --smart --model custom        # Bessere Qualität
python run.py --smart --model small --voice-clone  # Voice Cloning (langsam)
```

**Hinweis:** Die Warnung `does not support create_voice_clone_prompt` ist normal - die CustomVoice-Modelle nutzen vordefinierte Stimmen statt Voice Cloning.

---

## Skript-Struktur (SCRIPT.json)

```json
{
  "config": {
    "url": "https://llars.e-beratungsinstitut.de",
    "login": {"username": "ijcai_reviewer_1", "password": "ijcai_reviewer_123"},
    "tts_model": "custom-small",
    "speakers": {
      "moderator": {"name": "Alex", "macos_voice": "Fred"},
      "guest": {"name": "David", "macos_voice": "Daniel"}
    }
  },
  "steps": [
    {
      "_section": "=== INTRO (25s) ===",
      "id": "intro_1",
      "speaker": "guest",
      "narration": "Alex, I've been hearing about this Lars system...",
      "actions": [
        {"do": "show_title", "title": "Lars", "subtitle": "LLM Assisted Research System"}
      ]
    }
  ]
}
```

---

## Verfügbare Actions

| Action | Beschreibung | Beispiel |
|--------|--------------|----------|
| `goto` | URL navigieren | `{"do": "goto", "url": "/Home"}` |
| `login` | Login erzwingen | `{"do": "login"}` |
| `click` | Element klicken | `{"do": "click", "target": "Prompt Engineering"}` |
| `click_if_present` | Klick nur wenn vorhanden | `{"do": "click_if_present", "target": "Close"}` |
| `click_random` | Zufälliges Element klicken | `{"do": "click_random", "target": "Collab Color Preset"}` |
| `click_index` | Element via Index klicken | `{"do": "click_index", "target": "LLM List", "index": 0}` |
| `type` | Text tippen | `{"do": "type", "target": "Input", "text": "..."}` |
| `clear` | Input leeren | `{"do": "clear", "target": "Name Input"}` |
| `highlight` | Element hervorheben | `{"do": "highlight", "target": "...", "duration": 2}` |
| `drag` | Drag & Drop | `{"do": "drag", "from": "Ranking Item", "to": "Best Bucket"}` |
| `upload` | Datei hochladen | `{"do": "upload", "target": "File Input", "file": "data/news_articles.json"}` |
| `set_text_from_file` | Textarea mit Datei füllen | `{"do": "set_text_from_file", "target": "Manual Data Textarea", "file": "data/news_articles.json"}` |
| `wait` | Pause | `{"do": "wait", "seconds": 1.5}` |
| `wait_for` | Warten auf Element | `{"do": "wait_for", "target": "Test Prompt Dialog", "timeout": 10}` |
| `wait_for_modal` | Warten auf Dialog | `{"do": "wait_for_modal"}` |
| `sync` | Warten bis Narration erreicht | `{"do": "sync", "after": "Variables"}` |
| `show_title` | Titel-Overlay anzeigen | `{"do": "show_title", "title": "...", "subtitle": "..."}` |
| `scroll` | Scrollen | `{"do": "scroll", "target": "Manual Data Textarea", "amount": 260}` |
| `scroll_to` | Element scrollen | `{"do": "scroll_to", "target": "Matrix Preview"}` |
| `close_file_dialog` | File-Dialog schließen | `{"do": "close_file_dialog"}` |

### Collaboration Actions

| Action | Beschreibung | Beispiel |
|--------|--------------|----------|
| `collab_open` | Zweiten Browser öffnen | `{"do": "collab_open", "user": "ijcai_reviewer_2", "password": "ijcai_reviewer_123"}` |
| `collab_goto` | Collab-Browser navigieren | `{"do": "collab_goto", "url": "/promptengineering"}` |
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
  --from STEP_ID          Ab bestimmtem Step starten (ID oder Nummer)
  --no-record             Ohne Video-Aufnahme

SONSTIGES:
  --script PATH           Alternatives Skript verwenden
  --model, -m MODEL        TTS-Modell (custom-small, custom, design, small, large)
  --voice-clone           Voice Cloning aktivieren (sehr langsam)
```

---

## Production Setup

Das Demo-Video läuft gegen die Production-Instanz `https://llars.e-beratungsinstitut.de`.

### User-Accounts

Die Demo verwendet dedizierte IJCAI-Reviewer-Accounts:

| User | Rolle | Funktion im Video |
|------|-------|--------------------|
| `ijcai_reviewer_1` | ijcai_reviewer | Hauptakteur (Login, Prompt erstellen, Batch starten) |
| `ijcai_reviewer_2` | ijcai_reviewer | Collab-Partner (zweiter Browser) |

Die User werden mit dem **llars-seeder** Repo provisioniert:

```bash
# Im llars-seeder Repo:
cd /path/to/llars-seeder
./provision_users.sh          # Erstellt alle User via Admin-API
```

Credentials: siehe `llars-seeder/users.yaml`

### Demo-Daten Management

Das Script `app/scripts/demo_video_manage.py` verwaltet die Demo-Daten auf dem Server. Es läuft im Flask-Container mit App-Context.

**Daten-Aufteilung:**

| Daten | Typ | Besitzer |
|-------|-----|----------|
| "News Summary Prompt" | Pre-Seed (vor Aufnahme) | ijcai_reviewer_1 |
| "News Summary Demo Job" (40 Outputs) | Pre-Seed (vor Aufnahme) | ijcai_reviewer_1 |
| "News Summary Eval" | Live (während Aufnahme) | ijcai_reviewer_1 |
| "Live Collab Batch Job" | Live (während Aufnahme) | ijcai_reviewer_1 |
| Ranking Scenario | Live (während Aufnahme) | ijcai_reviewer_1 |

**Befehle:**

```bash
# Status anzeigen
docker exec llars_flask_service python3 /app/scripts/demo_video_manage.py status

# Pre-Seed-Daten erstellen (idempotent)
docker exec llars_flask_service python3 /app/scripts/demo_video_manage.py seed

# Live-Daten löschen (für erneute Aufnahme)
docker exec llars_flask_service python3 /app/scripts/demo_video_manage.py cleanup

# Komplett-Reset (cleanup + seed)
docker exec llars_flask_service python3 /app/scripts/demo_video_manage.py reset
```

**Auf Production (SSH):**

```bash
ssh user@llars-server
docker exec llars_flask_service python3 /app/scripts/demo_video_manage.py reset
```

### Aufnahme-Workflow

```bash
# 1. Auf Production: Demo-Daten vorbereiten
docker exec llars_flask_service python3 /app/scripts/demo_video_manage.py reset

# 2. Lokal: Audio generieren (falls Narration geändert)
cd Paper/demo-video
python run.py --smart

# 3. Lokal: Element-Test (prüft ob alle Selektoren funktionieren)
python run.py --test

# 4. Lokal: Video aufnehmen
python run.py

# --- Für erneute Aufnahme: ---
# 5. Auf Production: Live-Daten löschen
docker exec llars_flask_service python3 /app/scripts/demo_video_manage.py cleanup
# 6. Lokal: Erneut aufnehmen
python run.py
```

**Hinweis:** `run.py` läuft lokal (steuert Chrome via Selenium), `demo_video_manage.py` läuft auf dem Server (Flask ORM).

### Lokale Entwicklung (optional)

Für lokales Testen (`http://localhost:55080`):
- SCRIPT.json `config.url` auf `http://localhost:55080` setzen
- `PROJECT_STATE=development` aktiviert den automatischen Demo-Seeder
- `demo_video_manage.py` funktioniert auch im lokalen Container

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
    "Prompt Engineering": ".feature-card:contains('Prompt'), .feature-title:contains('Prompt')",
    "Batch Generation": ".feature-card:contains('Generation'), .feature-title:contains('Generation')",
    "News Summary Prompt": ".prompt-card:contains('News Summary')",
    "First Block Editor": ".editor-block:first-child .ql-editor",
    ...
}
```

### Selektor finden:
1. Lars öffnen in Chrome
2. Rechtsklick → Untersuchen auf das Element
3. Selektor kopieren oder `data-testid` suchen
4. In ELEMENT_MAP eintragen

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| TTS-Modell lädt nicht | `pip install -r requirements.txt` und ggf. `pip install torch` (platform-spezifisch) |
| Browser findet Element nicht | Element-Map in run.py erweitern |
| Collab-Cursor nicht sichtbar | Lars muss mit YJS-Server laufen |
| Audio zu langsam | `--model custom-small` nutzen |
| "does not support create_voice_clone_prompt" | Normal - Modell nutzt vordefinierte Stimmen |
| Section/Audio-Hash nicht gespeichert | Prüfe `audio/.section_hashes.json` und `audio/.audio_hashes.json` |
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
pip install -r requirements.txt
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
- [x] Bildschirmaufnahme (ffmpeg)
- [ ] Finale Video-Produktion
