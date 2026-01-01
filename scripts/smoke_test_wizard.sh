#!/bin/bash
# =============================================================================
# LLARS Chatbot Wizard Smoke Test
# =============================================================================
# Testet den kompletten Chatbot-Wizard-Workflow:
# 1. Wizard-Session erstellen mit Test-URL
# 2. Crawling starten und warten
# 3. Embedding abwarten
# 4. Chatbot konfigurieren
# 5. Chatbot finalisieren
# 6. Chatbot und Collection löschen
#
# Verwendung: ./scripts/smoke_test_wizard.sh
# Exit Codes: 0 = Erfolg, 1 = Fehler
# =============================================================================

set -e

BASE_URL="${BASE_URL:-http://localhost}"
# API Key Header ist X-API-Key (nicht X-API-Key!)
API_KEY="${SYSTEM_ADMIN_API_KEY:-llars-admin-key-change-in-production-12345}"
TEST_URL="${TEST_URL:-https://example.com}"  # Einfache Test-URL
MAX_WAIT_SECONDS=300  # Max 5 Minuten warten
POLL_INTERVAL=5

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

cleanup() {
    if [ -n "$CHATBOT_ID" ]; then
        log_info "Cleanup: Lösche Chatbot $CHATBOT_ID..."
        curl -sf -X DELETE "$BASE_URL/api/chatbot/$CHATBOT_ID" \
            -H "X-API-Key: $API_KEY" || true
    fi
}

trap cleanup EXIT

# =============================================================================
# 1. Health Check
# =============================================================================
log_info "=== LLARS Wizard Smoke Test ==="
log_info "Prüfe API Health..."

if ! curl -sf "$BASE_URL/auth/health_check" > /dev/null; then
    log_error "API nicht erreichbar!"
    exit 1
fi
log_info "✓ API Health OK"

# =============================================================================
# 2. Wizard Session erstellen
# =============================================================================
log_info "Erstelle Wizard-Session mit URL: $TEST_URL"

RESPONSE=$(curl -sf -X POST "$BASE_URL/api/chatbot/wizard" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "{
        \"url\": \"$TEST_URL\",
        \"crawl_config\": {
            \"max_pages\": 3,
            \"max_depth\": 1,
            \"use_playwright\": false
        }
    }" 2>&1) || {
    log_error "Wizard-Session konnte nicht erstellt werden!"
    log_error "Response: $RESPONSE"
    exit 1
}

CHATBOT_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('chatbot',{}).get('id',''))" 2>/dev/null)
SESSION_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)

if [ -z "$CHATBOT_ID" ] || [ -z "$SESSION_ID" ]; then
    log_error "Keine Chatbot-ID oder Session-ID erhalten!"
    log_error "Response: $RESPONSE"
    exit 1
fi

log_info "✓ Wizard-Session erstellt: Chatbot=$CHATBOT_ID, Session=$SESSION_ID"

# =============================================================================
# 3. Crawling starten
# =============================================================================
log_info "Starte Crawling..."

CRAWL_RESPONSE=$(curl -sf -X POST "$BASE_URL/api/chatbot/$CHATBOT_ID/wizard/crawl" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "{}" 2>&1) || {
    log_error "Crawling konnte nicht gestartet werden!"
    log_error "Response: $CRAWL_RESPONSE"
    exit 1
}

log_info "✓ Crawling gestartet"

# =============================================================================
# 4. Warten auf Crawling + Embedding
# =============================================================================
log_info "Warte auf Crawling und Embedding (max ${MAX_WAIT_SECONDS}s)..."

WAITED=0
LAST_STATUS=""

while [ $WAITED -lt $MAX_WAIT_SECONDS ]; do
    STATUS_RESPONSE=$(curl -sf "$BASE_URL/api/chatbot/$CHATBOT_ID/wizard/status" \
        -H "X-API-Key: $API_KEY" 2>/dev/null) || {
        log_warn "Status-Abfrage fehlgeschlagen, versuche erneut..."
        sleep $POLL_INTERVAL
        WAITED=$((WAITED + POLL_INTERVAL))
        continue
    }

    # Parse nested API response structure:
    # - status: session.build_status
    # - crawl_progress: progress.urls_completed / progress.urls_total * 100
    # - embedding_progress: progress.embedding_progress
    STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "
import sys,json
d=json.load(sys.stdin)
session = d.get('session', {})
print(session.get('build_status', d.get('status', 'unknown')))
" 2>/dev/null)
    CRAWL_PROGRESS=$(echo "$STATUS_RESPONSE" | python3 -c "
import sys,json
d=json.load(sys.stdin)
progress = d.get('progress', {})
total = progress.get('urls_total', 0)
completed = progress.get('urls_completed', 0)
if total > 0:
    print(int(completed / total * 100))
else:
    print(0)
" 2>/dev/null)
    EMBED_PROGRESS=$(echo "$STATUS_RESPONSE" | python3 -c "
import sys,json
d=json.load(sys.stdin)
progress = d.get('progress', {})
print(int(progress.get('embedding_progress', 0)))
" 2>/dev/null)

    if [ "$STATUS" != "$LAST_STATUS" ]; then
        log_info "Status: $STATUS (Crawl: ${CRAWL_PROGRESS}%, Embed: ${EMBED_PROGRESS}%)"
        LAST_STATUS="$STATUS"
    fi

    case "$STATUS" in
        "ready"|"configuring")
            log_info "✓ Crawling und Embedding abgeschlossen!"
            break
            ;;
        "error")
            log_error "Wizard-Build fehlgeschlagen!"
            log_error "Response: $STATUS_RESPONSE"
            exit 1
            ;;
        "crawling"|"embedding"|"draft")
            # Weiter warten
            ;;
        *)
            log_warn "Unbekannter Status: $STATUS"
            ;;
    esac

    sleep $POLL_INTERVAL
    WAITED=$((WAITED + POLL_INTERVAL))
done

if [ $WAITED -ge $MAX_WAIT_SECONDS ]; then
    log_error "Timeout: Wizard-Build nicht in ${MAX_WAIT_SECONDS}s abgeschlossen!"
    exit 1
fi

# =============================================================================
# 5. Chatbot konfigurieren (Wizard-Daten aktualisieren)
# =============================================================================
log_info "Konfiguriere Chatbot..."

CONFIG_RESPONSE=$(curl -sf -X PATCH "$BASE_URL/api/chatbot/wizard/sessions/$SESSION_ID/data" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "{
        \"chatbot_config\": {
            \"name\": \"smoke-test-bot-$(date +%s)\",
            \"display_name\": \"Smoke Test Bot\",
            \"system_prompt\": \"Du bist ein Test-Assistent.\",
            \"welcome_message\": \"Hallo! Ich bin ein Test-Bot.\",
            \"fallback_message\": \"Das kann ich leider nicht beantworten.\",
            \"icon\": \"mdi-robot\",
            \"primary_color\": \"#b0ca97\"
        }
    }" 2>&1) || {
    log_error "Chatbot-Konfiguration fehlgeschlagen!"
    log_error "Response: $CONFIG_RESPONSE"
    exit 1
}

log_info "✓ Chatbot konfiguriert"

# =============================================================================
# 6. Chatbot finalisieren
# =============================================================================
log_info "Finalisiere Chatbot..."

FINALIZE_RESPONSE=$(curl -sf -X POST "$BASE_URL/api/chatbot/$CHATBOT_ID/wizard/finalize" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "{}" 2>&1) || {
    log_error "Chatbot-Finalisierung fehlgeschlagen!"
    log_error "Response: $FINALIZE_RESPONSE"
    exit 1
}

log_info "✓ Chatbot finalisiert"

# =============================================================================
# 7. Verifizieren: Chatbot existiert
# =============================================================================
log_info "Verifiziere Chatbot..."

VERIFY_RESPONSE=$(curl -sf "$BASE_URL/api/chatbot/$CHATBOT_ID" \
    -H "X-API-Key: $API_KEY" 2>&1) || {
    log_error "Chatbot nicht gefunden!"
    exit 1
}

CHATBOT_NAME=$(echo "$VERIFY_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('chatbot',{}).get('name',''))" 2>/dev/null)
log_info "✓ Chatbot verifiziert: $CHATBOT_NAME"

# =============================================================================
# 8. Cleanup: Chatbot löschen
# =============================================================================
log_info "Lösche Test-Chatbot..."

DELETE_RESPONSE=$(curl -sf -X DELETE "$BASE_URL/api/chatbot/$CHATBOT_ID" \
    -H "X-API-Key: $API_KEY" 2>&1) || {
    log_warn "Chatbot-Löschung fehlgeschlagen (wird im Cleanup erneut versucht)"
}

# Cleanup-Trap deaktivieren (bereits gelöscht)
CHATBOT_ID=""

log_info "✓ Chatbot gelöscht"

# =============================================================================
# Erfolg!
# =============================================================================
echo ""
log_info "=========================================="
log_info "=== WIZARD SMOKE TEST ERFOLGREICH! ==="
log_info "=========================================="
echo ""

exit 0
