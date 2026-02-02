# LLARS Demo Video Framework

## Zweck

Automatisierte Erstellung eines Demo-Videos für die **IJCAI 2026 Demo Track** Einreichung.

**Deadline:** 16. Februar 2026

Das Video demonstriert LLARS (LLM Assisted Research System) - eine Plattform zur kollaborativen Bewertung von LLM-Outputs.

## Konzept

Das Video zeigt zwei Sprecher, die sich gegenseitig LLARS vorstellen:
- **Sprecher 1 (Host):** Führt durch die Demo, erklärt Features
- **Sprecher 2 (Sir Attenborough-Stil):** Kommentiert und stellt Fragen

## Verzeichnisstruktur

```
Paper/demo-video/
├── SCRIPT.json          # GROUND TRUTH - Das Drehbuch
├── run.py               # Haupt-Runner
├── src/
│   └── tts.py           # Qwen3-TTS Integration
├── audio/               # Generierte Audio-Dateien (gitignored)
├── output/              # Finale Videos (gitignored)
└── data/                # Demo-Daten (News-Artikel etc.)
```

## Befehle

```bash
cd Paper/demo-video

# Schnelltest - prüft ob alle UI-Elemente gefunden werden
python run.py --test

# Audio generieren (nur wenn Narration geändert wurde)
python run.py --audio

# Audio neu generieren (Cache ignorieren)
python run.py --audio --force

# Vorschau ohne Aufnahme
python run.py --no-record

# Vollständige Aufnahme
python run.py

# Mit Audio-Wiedergabe während Aufnahme
python run.py --no-silent
```

## SCRIPT.json Format

Das Skript ist die **einzige Wahrheitsquelle**. Jede Änderung hier wird sofort wirksam.

### Grundstruktur

```json
{
  "config": {
    "url": "http://localhost:55080",
    "resolution": [1920, 1080],
    "tts_model": "large",
    "output_file": "llars_demo.mp4",
    "language": "en",
    "login": {
      "username": "admin",
      "password": "admin123"
    }
  },
  "steps": [
    {
      "id": "intro_1",
      "speaker": "host",
      "narration": "Welcome to LLARS...",
      "actions": [...]
    }
  ]
}
```

### Timing-Steuerung

Aktionen laufen **sequentiell** in der angegebenen Reihenfolge.

#### `sync` - Warte auf Narration

```json
{"do": "sync", "after": "Prompt Engineering"}  // Wartet bis Wort gesprochen
{"do": "sync", "at": 3.5}                       // Wartet bis Sekunde 3.5
{"do": "sync", "at": "50%"}                     // Wartet bis 50% der Narration
```

#### `highlight_before` - Highlight vor Klick

```json
{"do": "click", "target": "Button", "highlight_before": 2}
// Highlightet Element 2 Sekunden, dann klickt
```

### Verfügbare Aktionen

| Aktion | Beschreibung | Beispiel |
|--------|--------------|----------|
| `click` | Element anklicken | `{"do": "click", "target": "Create Prompt"}` |
| `type` | Text eingeben | `{"do": "type", "target": "Input", "text": "Hello"}` |
| `sync` | Auf Narration warten | `{"do": "sync", "after": "click on"}` |
| `wait` | Pause | `{"do": "wait", "seconds": 2}` |
| `wait_for_modal` | Auf Dialog warten | `{"do": "wait_for_modal"}` |
| `goto` | Navigation | `{"do": "goto", "url": "/Home"}` |
| `highlight` | Element highlighten | `{"do": "highlight", "target": "X", "duration": 2}` |
| `show_title` | Titel-Overlay | `{"do": "show_title", "title": "LLARS", "subtitle": "..."}` |

### Element-Namen

Anstatt CSS-Selektoren verwendet das Skript lesbare Namen:

```json
{"do": "click", "target": "Prompt Engineering"}  // Feature-Card
{"do": "click", "target": "Create Prompt"}       // Button
{"do": "click", "target": "New Block"}           // Sidebar-Button
{"do": "type", "target": "First Block Editor", "text": "..."}  // Quill Editor
```

Die Zuordnung zu CSS-Selektoren ist in `run.py` → `ELEMENT_MAP` definiert.

## Sprecher-System

### Konfiguration (SCRIPT.json)

```json
{
  "config": {
    "speakers": {
      "host": {
        "name": "Alex",
        "voice": "en_default",
        "description": "Freundlicher Tech-Host"
      },
      "narrator": {
        "name": "David",
        "voice": "en_attenborough",
        "description": "Sir Attenborough-Stil"
      }
    }
  },
  "steps": [
    {
      "id": "intro_1",
      "speaker": "host",
      "narration": "Welcome to LLARS..."
    },
    {
      "id": "intro_2",
      "speaker": "narrator",
      "narration": "What we're witnessing here..."
    }
  ]
}
```

### Stimmen in Qwen3-TTS

Qwen3-TTS unterstützt Voice Cloning und Voice Design:

1. **Voice Design** - Beschreibung der gewünschten Stimme
2. **Voice Cloning** - Referenz-Audio für Stimmklon

Siehe `src/tts.py` für die Implementierung.

## Workflow

### 1. Skript bearbeiten

Bearbeite `SCRIPT.json` um Narration und Aktionen anzupassen.

### 2. Testen

```bash
python run.py --test
```

Prüft ob alle UI-Elemente gefunden werden.

### 3. Audio generieren

```bash
python run.py --audio
```

Generiert Audio-Dateien für alle Schritte. Gecachte Dateien werden übersprungen.

### 4. Vorschau

```bash
python run.py --no-record
```

Führt das Skript aus ohne aufzunehmen.

### 5. Finale Aufnahme

```bash
python run.py
```

## Troubleshooting

### Element nicht gefunden

1. Prüfe ob LLARS läuft: `http://localhost:55080`
2. Prüfe Element-Namen in `ELEMENT_MAP`
3. UI könnte sich geändert haben - Selektor anpassen

### Audio-Qualität

- Nutze `tts_model: "large"` für beste Qualität
- Erste Generierung lädt ~3GB Modell herunter

### Timing-Probleme

- Nutze mehr `sync`-Befehle für präzise Kontrolle
- `highlight_before` gibt Reviewern Zeit zu sehen was passiert

## Technische Details

- **Browser:** Selenium + Chrome
- **TTS:** Qwen3-TTS (CosyVoice2)
- **Recording:** ffmpeg
- **Audio-Sync:** Post-Processing mit Timestamps

## Stimmen-Konsistenz (Voice Cloning)

Für 100% konsistente Stimmen verwendet LLARS **Voice Cloning** mit Referenz-Audio:

### Setup

```bash
cd Paper/demo-video

# 1. Referenz-Audio erstellen (einmalig)
python src/tts.py --create-refs

# 2. Audio generieren (Voice Cloning)
python run.py --audio --force
```

### Wie es funktioniert

1. Jeder Sprecher hat eine **Referenz-Audio** (3-15 Sek.) in `voices/`
2. Qwen3-TTS extrahiert das **Speaker-Embedding** einmalig
3. Alle Generierungen nutzen dasselbe Embedding → **identische Stimme**

### Referenz-Dateien

```
voices/
├── alex_reference.wav    # Host (amerikanisch)
├── david_reference.wav   # Narrator (britisch, Attenborough)
└── chen_reference.wav    # Expert (optional)
```

**Tipp:** Ersetze die Dateien durch echte Sprachaufnahmen für noch bessere Qualität!

## Dialog-Stil

Das Video nutzt einen natürlichen Dialog-Stil:
- **David (Narrator)** stellt clevere Fragen und beobachtet
- **Alex (Host)** zeigt Features und erklärt

Beispiel-Dialog:
```
David: "Ah, I see. But how do you handle the actual article content?"
Alex:  "That's where variables come in! These placeholders get automatically filled..."
```

Der Dialog sollte sich wie ein echtes Gespräch anfühlen, nicht wie zwei Monologe.

## Demo-Daten Vorbereitung

Für das vollständige Demo (mit fertiger Batch Generation) benötigst du:

```bash
# Anleitung anzeigen
./setup_demo_data.sh

# Prüfen ob Daten existieren
./setup_demo_data.sh --check

# Demo-Daten löschen
./setup_demo_data.sh --clean
```

**Manuelle Schritte:**
1. Batch Generation mit 2 Modellen erstellen und durchlaufen lassen
2. Szenario aus fertiger Batch erstellen
3. Einige Bewertungen durchführen

## TODO

- [x] Zwei-Sprecher-Dialog implementieren
- [x] Sir Attenborough Stimme konfigurieren
- [x] Konsistente Stimmen Option
- [ ] Demo-Daten vorbereiten
- [ ] Skript finalisieren
- [ ] Finale Aufnahme erstellen
