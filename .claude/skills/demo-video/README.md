# LLARS Demo Video Framework

## Zweck

Automatisierte Erstellung eines Demo-Videos für die **IJCAI 2026 Demo Track** Einreichung.

**Deadline:** 16. Februar 2026

Das Video demonstriert LLARS (LLM Assisted Research System) - eine Plattform zur kollaborativen Bewertung von LLM-Outputs.

## Konzept

Das Video zeigt zwei Sprecher im Dialog-Stil:
- **Host (Alex):** Amerikanischer Tech-Presenter - erklärt Features
- **Narrator (David):** Britischer Beobachter - stellt clevere Fragen

**Highlight:** Live-Kollaboration wird mit zwei echten Browser-Fenstern demonstriert.

## Verzeichnisstruktur

```
Paper/demo-video/
├── SCRIPT.json          # GROUND TRUTH - Das Drehbuch (27 Schritte)
├── run.py               # Haupt-Runner (Browser-Automation + TTS)
├── README.md            # Detaillierte Dokumentation
├── src/
│   └── tts.py           # Qwen3-TTS Integration
├── audio/               # Generierte Audio-Dateien
│   └── .section_hashes.json  # Section-Hashes für intelligentes Caching
├── voices/              # Voice-Referenzen (optional für Cloning)
├── output/              # Finale Videos
└── data/                # Demo-Daten (News-Artikel)
```

## Quick Start

```bash
cd Paper/demo-video

# Schnelltest - prüft ob alle UI-Elemente gefunden werden
python run.py --test

# Audio generieren (NUR geänderte Sections)
python run.py --smart

# Vollständige Aufnahme
python run.py
```

## Section-basiertes Audio-Caching

**NEU:** Audio wird nur für geänderte Sections neu generiert:

```bash
python run.py --smart                          # Nur geänderte Sections
python run.py --smart --sections INTRO         # Nur INTRO Section erzwingen
python run.py --smart --sections "PROMPT ENGINEERING"  # Mit Leerzeichen
```

### Sections im Skript

| Section | Steps | Audio-Dateien | Inhalt |
|---------|-------|---------------|--------|
| INTRO | 2 | 2 | Einführung, Problemstellung |
| PROMPT ENGINEERING | 11 | 11 | Editor, Variables, **Live-Collab Demo** |
| BATCH GENERATION | 5 | 5 | Job-Übersicht, Matrix-Kombinationen |
| SCENARIO MANAGER | 6 | 6 | Evaluationstypen, Human/LLM Judges |
| CONCLUSION | 3 | 3 | Zusammenfassung, GitHub Link |

**Total:** 27 Schritte, 27 Audio-Dateien

## Collaboration Demo

Das Video zeigt **echte Real-Time Kollaboration** mit zwei Browser-Fenstern:

```json
{"do": "collab_open", "user": "researcher"},
{"do": "collab_goto", "url": "/PromptEngineering/3"},
{"do": "collab_focus"},
{"do": "collab_type", "target": "First Block Editor", "text": "\n\n# Added by researcher", "delay": 0.1},
{"do": "collab_close"}
```

**Actions:**
- `collab_open` - Zweiten Browser öffnen + Login
- `collab_goto` - URL im Collab-Browser navigieren
- `collab_focus` - Quill-Editor fokussieren
- `collab_type` - Text zeichenweise tippen (sichtbar für Zuschauer)
- `collab_click` - Element klicken
- `collab_close` - Browser schließen

## TTS-Modelle

| Modell | Beschreibung | Performance |
|--------|--------------|-------------|
| `custom-small` | Vordefinierte Stimmen (Ryan=David, Aiden=Alex) | **Empfohlen** |
| `custom` | Größeres Modell, bessere Qualität | Langsamer |
| `design` | Voice Design mit Text-Parametern | Inkonsistent |
| `small/large` | Voice Cloning mit Referenz-Audio | Sehr langsam |

```bash
python run.py --smart --model custom-small  # Standard
python run.py --smart --model custom        # Bessere Qualität
```

**Hinweis:** Die Warnung `does not support create_voice_clone_prompt` ist normal - das custom-small Modell nutzt vordefinierte Stimmen.

## Demo-Daten (Backend Seeder)

Das Backend enthält einen Seeder für vorbereitete Demo-Daten:

**Datei:** `app/db/seeders/demo_video_data.py`

**Enthält:**
- 2 News-Summarization Prompts
- 1 abgeschlossener Batch-Generation Job
- 40 Outputs (10 Artikel × 2 Prompts × 2 Modelle)
- Pre-generierte Zusammenfassungen

```bash
# Seeder läuft automatisch bei PROJECT_STATE=development
docker compose restart llars_flask_service
```

## Typische Workflows

```bash
# Nach Änderung der Narration
python run.py --smart && python run.py

# Nur eine Section neu generieren
python run.py --smart --sections "PROMPT ENGINEERING"

# Nach Änderung der Actions (kein Audio nötig)
python run.py --test && python run.py

# Alles komplett neu
python run.py --audio --force && python run.py

# Quick Test ab bestimmtem Step
python run.py --test --from collab_1
```

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Element nicht gefunden | ELEMENT_MAP in run.py erweitern |
| Collab-Cursor nicht sichtbar | LLARS muss mit YJS-Server laufen |
| Audio zu langsam | `--model custom-small` nutzen |
| Section nicht erkannt | `_section` Marker im Format `=== NAME (30s) ===` |

## Entwicklungsstand

- [x] Browser-Automation (Selenium)
- [x] Two-Speaker Dialog System (Host + Narrator)
- [x] Qwen3-TTS Integration mit vordefinierten Stimmen
- [x] Section-basiertes Audio-Caching (`--smart`)
- [x] Real-Time Collaboration Demo (zwei Browser)
- [x] Demo-Daten Seeder (Backend)
- [x] Element-Test Mode (`--test`)
- [x] CLI mit allen Optionen
- [ ] Bildschirmaufnahme (ffmpeg)
- [ ] Finale Video-Produktion

## CLI-Referenz

```
python run.py [OPTIONS]

INFO:
  --list, -l              Liste aller Schritte
  --preview, -p           Detaillierte Vorschau

AUDIO:
  --smart                 Intelligente Generierung (nur geänderte Sections)
  --sections SECTION...   Bestimmte Sections erzwingen
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

OPTIONEN:
  --model MODEL           TTS-Modell wählen
  --voice-clone           Voice Cloning aktivieren
```
