#!/bin/bash
# ============================================
# LLARS Demo Video - Recording Script
# ============================================
#
# Nutzung:
#   ./run_demo.sh              # Komplette Aufnahme
#   ./run_demo.sh --preview    # Nur Skript-Vorschau
#   ./run_demo.sh --audio-only # Nur TTS generieren
#   ./run_demo.sh --resume     # Fortsetzen von Checkpoint
#
# Voraussetzungen:
#   - LLARS läuft unter http://localhost:55080
#   - ffmpeg installiert
#   - OPENAI_API_KEY gesetzt (für TTS)
#
# Hotkeys während Aufnahme:
#   SPACE - Pause/Resume
#   R     - Segment wiederholen
#   E     - Skript editieren
#   S     - Screenshot speichern
#   Q     - Beenden mit Checkpoint
#   N     - Segment überspringen

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         LLARS Demo Video Recording System                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Prüfe Voraussetzungen
check_requirements() {
    echo -e "${YELLOW}Prüfe Voraussetzungen...${NC}"

    # Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 nicht gefunden${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python3${NC}"

    # ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        echo -e "${RED}❌ ffmpeg nicht gefunden${NC}"
        echo "  Installiere mit: brew install ffmpeg (macOS)"
        exit 1
    fi
    echo -e "${GREEN}✓ ffmpeg${NC}"

    # Chrome
    if ! command -v google-chrome &> /dev/null && ! [ -d "/Applications/Google Chrome.app" ]; then
        echo -e "${YELLOW}⚠️ Chrome nicht gefunden - Selenium benötigt Chrome${NC}"
    else
        echo -e "${GREEN}✓ Chrome${NC}"
    fi

    # LLARS
    if ! curl -s http://localhost:55080 > /dev/null 2>&1; then
        echo -e "${RED}❌ LLARS nicht erreichbar unter http://localhost:55080${NC}"
        echo "  Starte LLARS mit: ./start_llars.sh"
        exit 1
    fi
    echo -e "${GREEN}✓ LLARS erreichbar${NC}"

    # OpenAI API Key
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${YELLOW}⚠️ OPENAI_API_KEY nicht gesetzt - nutze lokales TTS${NC}"
    else
        echo -e "${GREEN}✓ OpenAI API Key${NC}"
    fi

    echo ""
}

# Python-Abhängigkeiten installieren
install_dependencies() {
    echo -e "${YELLOW}Installiere Python-Abhängigkeiten...${NC}"
    pip3 install -r requirements.txt -q
    echo -e "${GREEN}✓ Abhängigkeiten installiert${NC}"
    echo ""
}

# TTS Pre-Generierung
generate_audio() {
    echo -e "${YELLOW}Generiere TTS Audio...${NC}"
    python3 -c "
import json
import sys
sys.path.insert(0, 'src')
from tts import TTSEngine

with open('scripts/full_script.json') as f:
    script = json.load(f)

tts = TTSEngine(voice='alloy')
tts.pre_generate_all(script, 'audio')
"
    echo -e "${GREEN}✓ Audio generiert${NC}"
    echo ""
}

# Skript-Vorschau
show_preview() {
    echo -e "${BLUE}Skript-Vorschau:${NC}"
    echo ""
    python3 src/orchestrator.py --script scripts/full_script.json --preview
}

# Hauptaufnahme
run_recording() {
    echo -e "${BLUE}"
    echo "════════════════════════════════════════════════════════════"
    echo "  AUFNAHME STARTET"
    echo "════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    echo ""
    echo "Hotkeys:"
    echo "  SPACE - Pause/Resume"
    echo "  R     - Segment wiederholen"
    echo "  E     - Skript editieren"
    echo "  S     - Screenshot speichern"
    echo "  Q     - Beenden mit Checkpoint"
    echo "  N     - Segment überspringen"
    echo ""
    echo -e "${YELLOW}Drücke ENTER zum Starten...${NC}"
    read

    # sudo für keyboard-Modul (benötigt auf macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${YELLOW}Keyboard-Zugriff benötigt Admin-Rechte auf macOS${NC}"
        sudo python3 src/orchestrator.py --script scripts/full_script.json --output output
    else
        python3 src/orchestrator.py --script scripts/full_script.json --output output
    fi
}

# Resume von Checkpoint
resume_recording() {
    CHECKPOINT=$(ls -t checkpoints/*.json 2>/dev/null | head -1)
    if [ -z "$CHECKPOINT" ]; then
        echo -e "${RED}❌ Kein Checkpoint gefunden${NC}"
        exit 1
    fi

    echo -e "${YELLOW}Fortsetzen von: $CHECKPOINT${NC}"
    python3 src/orchestrator.py --resume "$CHECKPOINT"
}

# Hauptprogramm
case "${1:-}" in
    --preview)
        check_requirements
        show_preview
        ;;
    --audio-only)
        check_requirements
        install_dependencies
        generate_audio
        ;;
    --resume)
        check_requirements
        resume_recording
        ;;
    --help|-h)
        echo "Nutzung: $0 [OPTION]"
        echo ""
        echo "Optionen:"
        echo "  --preview     Zeigt Skript-Vorschau ohne Aufnahme"
        echo "  --audio-only  Generiert nur TTS Audio"
        echo "  --resume      Setzt von letztem Checkpoint fort"
        echo "  --help        Zeigt diese Hilfe"
        echo ""
        echo "Ohne Option: Startet komplette Aufnahme"
        ;;
    *)
        check_requirements
        install_dependencies
        generate_audio
        run_recording
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"
