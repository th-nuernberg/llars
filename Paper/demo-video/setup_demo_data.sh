#!/bin/bash
# =============================================================================
# LLARS Demo Video - Demo-Daten Setup
# =============================================================================
#
# Dieses Skript bereitet die Demo-Daten für das IJCAI Video vor.
#
# VORAUSSETZUNG: LLARS muss laufen (./start_llars.sh)
#
# NUTZUNG:
#   ./setup_demo_data.sh          # Erstellt Demo-Daten
#   ./setup_demo_data.sh --clean  # Löscht Demo-Daten
#   ./setup_demo_data.sh --check  # Prüft Demo-Daten
#
# =============================================================================

set -e

DB_CONTAINER="llars_db_service"
DB_USER="dev_user"
DB_PASS="dev_password_change_me"
DB_NAME="database_llars"

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Demo-Daten Bezeichner
DEMO_PREFIX="IJCAI Demo"
PROMPT_NAME="${DEMO_PREFIX} - News Summary"
JOB_NAME="${DEMO_PREFIX} - Batch Generation"
SCENARIO_NAME="${DEMO_PREFIX} - Evaluation"

run_sql() {
    docker exec $DB_CONTAINER mariadb -u $DB_USER -p$DB_PASS $DB_NAME -e "$1"
}

check_data() {
    echo -e "\n${YELLOW}🔍 Prüfe Demo-Daten...${NC}"

    # Prüfe Prompts
    PROMPT_COUNT=$(run_sql "SELECT COUNT(*) FROM user_prompts WHERE name LIKE '%${DEMO_PREFIX}%';" 2>/dev/null | tail -1)
    if [ "$PROMPT_COUNT" -gt 0 ]; then
        echo -e "   ${GREEN}✓${NC} Prompt vorhanden ($PROMPT_COUNT)"
    else
        echo -e "   ${RED}✗${NC} Kein Demo-Prompt gefunden"
    fi

    # Prüfe Jobs
    JOB_COUNT=$(run_sql "SELECT COUNT(*) FROM generation_jobs WHERE name LIKE '%${DEMO_PREFIX}%';" 2>/dev/null | tail -1)
    if [ "$JOB_COUNT" -gt 0 ]; then
        echo -e "   ${GREEN}✓${NC} Batch Job vorhanden ($JOB_COUNT)"
    else
        echo -e "   ${RED}✗${NC} Kein Demo-Job gefunden"
    fi

    # Prüfe Szenarien
    SCENARIO_COUNT=$(run_sql "SELECT COUNT(*) FROM scenarios WHERE name LIKE '%${DEMO_PREFIX}%';" 2>/dev/null | tail -1)
    if [ "$SCENARIO_COUNT" -gt 0 ]; then
        echo -e "   ${GREEN}✓${NC} Szenario vorhanden ($SCENARIO_COUNT)"
    else
        echo -e "   ${RED}✗${NC} Kein Demo-Szenario gefunden"
    fi
}

clean_data() {
    echo -e "\n${YELLOW}🧹 Lösche Demo-Daten...${NC}"

    run_sql "
    -- Lösche Szenario-Daten
    DELETE FROM scenario_users WHERE scenario_id IN (SELECT id FROM scenarios WHERE name LIKE '%${DEMO_PREFIX}%');
    DELETE FROM item_ratings WHERE scenario_id IN (SELECT id FROM scenarios WHERE name LIKE '%${DEMO_PREFIX}%');
    DELETE FROM scenario_threads WHERE scenario_id IN (SELECT id FROM scenarios WHERE name LIKE '%${DEMO_PREFIX}%');
    DELETE FROM scenarios WHERE name LIKE '%${DEMO_PREFIX}%';

    -- Lösche Batch-Job-Daten
    DELETE FROM generation_outputs WHERE job_id IN (SELECT id FROM generation_jobs WHERE name LIKE '%${DEMO_PREFIX}%');
    DELETE FROM generation_jobs WHERE name LIKE '%${DEMO_PREFIX}%';

    -- Lösche Prompts (aber nur Demo-Prompts)
    DELETE FROM prompt_blocks WHERE prompt_id IN (SELECT id FROM user_prompts WHERE name LIKE '%${DEMO_PREFIX}%');
    DELETE FROM user_prompts WHERE name LIKE '%${DEMO_PREFIX}%';
    "

    echo -e "   ${GREEN}✓${NC} Demo-Daten gelöscht"
}

show_help() {
    echo "
╔════════════════════════════════════════════════════════════════╗
║           LLARS Demo Video - Daten-Vorbereitung                ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  Für das Demo-Video benötigen wir:                             ║
║                                                                ║
║  1. Eine FERTIGE Batch Generation mit 2 Modellen               ║
║  2. Ein FERTIGES Evaluations-Szenario                          ║
║                                                                ║
║  MANUELLE SCHRITTE:                                            ║
║  ──────────────────                                            ║
║                                                                ║
║  1. Öffne LLARS: http://localhost:55080                        ║
║                                                                ║
║  2. Erstelle Batch Generation:                                 ║
║     - Batch Generation → New Job                               ║
║     - Upload: data/news_articles.json                          ║
║     - Prompt: Erstelle 'News Summary' Prompt                   ║
║     - Models: GPT-4 + Mistral (oder andere 2)                  ║
║     - Name: '${JOB_NAME}'                                      ║
║     - Starten und WARTEN bis fertig                            ║
║                                                                ║
║  3. Erstelle Szenario aus Batch:                               ║
║     - Im fertigen Job → 'Create Scenario'                      ║
║     - Type: Ranking oder Rating                                ║
║     - Name: '${SCENARIO_NAME}'                                 ║
║     - Evaluatoren: admin + LLM Judge                           ║
║                                                                ║
║  4. Führe einige Bewertungen durch                             ║
║                                                                ║
║  5. Prüfe mit: ./setup_demo_data.sh --check                    ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
"
}

# Main
case "$1" in
    --clean)
        clean_data
        ;;
    --check)
        check_data
        ;;
    --help|-h)
        show_help
        ;;
    *)
        show_help
        echo -e "\n${YELLOW}Aktueller Status:${NC}"
        check_data
        ;;
esac
