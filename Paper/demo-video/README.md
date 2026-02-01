# LLARS Demo Video System

**Ein-Klick-Automatisierung** für das IJCAI Demo Video.

## Quick Start

```bash
cd Paper/demo-video

# 1. Vorschau des Skripts
python run.py --preview

# 2. Nur Audio generieren (optional, wird sonst on-the-fly gemacht)
python run.py --audio

# 3. VOLLSTÄNDIGE AUFNAHME STARTEN
python run.py
```

**Das war's.** Chrome öffnet sich, LLARS wird durchgeklickt, Audio wird gesprochen, Bildschirm wird aufgenommen.

---

## Das Skript = Ground Truth

**`SCRIPT.json`** ist die einzige Datei, die du bearbeiten musst.

### Struktur

```json
{
  "steps": [
    {
      "id": "eindeutige_id",
      "narration": "Was gesprochen wird...",
      "actions": [
        {"do": "click", "target": "Button Name"},
        {"do": "type", "target": "Input Feld", "text": "Eingabe"},
        {"do": "wait", "seconds": 2}
      ]
    }
  ]
}
```

### Verfügbare Aktionen

| Aktion | Parameter | Beschreibung |
|--------|-----------|--------------|
| `click` | `target` | Klickt auf Element |
| `type` | `target`, `text`, `speed` | Tippt Text (speed: slow/medium/fast) |
| `highlight` | `target`, `duration` | Hebt Element hervor |
| `drag` | `from`, `to` | Drag & Drop |
| `upload` | `file` | Lädt Datei hoch |
| `wait` | `seconds` | Wartet N Sekunden |
| `wait_for` | `target`, `timeout` | Wartet auf Element |
| `wait_for_modal` | - | Wartet auf Dialog |
| `goto` | `url` | Navigiert zu URL |
| `show_title` | `title`, `subtitle` | Zeigt Titelfolie |

---

## Element-Mapping anpassen

In `run.py` gibt es `ELEMENT_MAP` - eine Zuordnung von **lesbaren Namen** zu **CSS-Selektoren**:

```python
ELEMENT_MAP = {
    "Prompt Engineering": "[data-testid='nav-prompt-engineering']",
    "Create Prompt": "button:contains('Create')",
    ...
}
```

### So findest du die richtigen Selektoren:

1. **LLARS öffnen** in Chrome
2. **Rechtsklick → Untersuchen** auf das Element
3. **Selektor kopieren** oder `data-testid` suchen
4. **In ELEMENT_MAP eintragen**

### Beispiel:

Wenn der "Create Prompt" Button so aussieht:
```html
<button class="v-btn primary" data-testid="create-prompt-btn">Create Prompt</button>
```

Dann in ELEMENT_MAP:
```python
"Create Prompt": "[data-testid='create-prompt-btn']",
```

---

## TTS (Text-to-Speech)

### Standard: Qwen3-TTS (lokal)

- **Model:** `Qwen3-TTS-12Hz-0.6B` (klein, schnell)
- **Benötigt:** ~4GB VRAM oder läuft auf CPU
- **Installation:** `pip install qwen-tts`

### Fallback: macOS `say`

Wenn Qwen nicht lädt, wird automatisch macOS `say` verwendet.

### Audio-Cache

Alle generierten Audio-Dateien werden in `audio/` gecached. Bei gleichem Text wird nicht neu generiert.

---

## Aufnahme-Optionen

```bash
# Normale Aufnahme
python run.py

# Ohne Aufnahme (nur Browser-Automatisierung)
python run.py --no-record

# Ab Schritt 5 starten
python run.py --step 5

# Anderes Skript verwenden
python run.py --script mein_skript.json
```

---

## Dateien

```
Paper/demo-video/
├── SCRIPT.json          ← BEARBEITE DIESE DATEI
├── run.py               ← Startet alles
├── README.md            ← Diese Anleitung
│
├── data/
│   └── news_articles.json   # Testdaten
│
├── audio/               # Generierte Audio-Dateien
├── output/              # Aufgenommene Videos
│
└── src/
    └── tts.py           # Qwen3-TTS Engine
```

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Element nicht gefunden | Selektor in ELEMENT_MAP anpassen |
| Audio-Fehler | `pip install qwen-tts` oder Fallback nutzen |
| Chrome startet nicht | `pip install selenium webdriver-manager` |
| ffmpeg fehlt | `brew install ffmpeg` (macOS) |
| LLARS nicht erreichbar | `./start_llars.sh` ausführen |

---

## Workflow

1. **LLARS starten:** `./start_llars.sh`
2. **Skript anpassen:** `SCRIPT.json` bearbeiten
3. **Vorschau:** `python run.py --preview`
4. **Audio pre-generieren:** `python run.py --audio`
5. **Aufnehmen:** `python run.py`
6. **Video in:** `output/llars_demo.mp4`

---

## Quellen

- [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) - Lokales TTS-Modell
- [Selenium](https://selenium-python.readthedocs.io/) - Browser-Automatisierung
