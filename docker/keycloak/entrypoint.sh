#!/bin/bash
set -e

echo "======================================"
echo "Keycloak Entrypoint - PROJECT_STATE: ${PROJECT_STATE:-development}"
echo "======================================"

# Pfade
REALM_TEMPLATE="/opt/keycloak/import-config/realm-import-template.json"
REALM_OUTPUT="/opt/keycloak/data/import/realm-import.json"

# Realm-Konfiguration basierend auf PROJECT_STATE anpassen
if [ "${PROJECT_STATE}" = "production" ]; then
    echo "Konfiguriere Keycloak für PRODUCTION..."

    # Production: SSL required, strikte Sicherheit
    SSL_REQUIRED="external"
    HOSTNAME_STRICT="true"
    HTTP_ENABLED="false"

    # Setze KC_HOSTNAME_STRICT und KC_HTTP_ENABLED für production
    export KC_HOSTNAME_STRICT=true
    export KC_HTTP_ENABLED=false

    echo "  - sslRequired: $SSL_REQUIRED"
    echo "  - KC_HOSTNAME_STRICT: $HOSTNAME_STRICT"
    echo "  - KC_HTTP_ENABLED: $HTTP_ENABLED"

else
    echo "Konfiguriere Keycloak für DEVELOPMENT..."

    # Development: HTTP erlaubt, lockere Sicherheit
    SSL_REQUIRED="none"
    HOSTNAME_STRICT="false"
    HTTP_ENABLED="true"

    # Setze KC_HOSTNAME_STRICT und KC_HTTP_ENABLED für development
    export KC_HOSTNAME_STRICT=false
    export KC_HTTP_ENABLED=true

    echo "  - sslRequired: $SSL_REQUIRED"
    echo "  - KC_HOSTNAME_STRICT: $HOSTNAME_STRICT"
    echo "  - KC_HTTP_ENABLED: $HTTP_ENABLED"
fi

# Stelle sicher, dass das import Verzeichnis existiert
mkdir -p /opt/keycloak/data/import

# Kopiere Template und ersetze Platzhalter
if [ -f "$REALM_TEMPLATE" ]; then
    echo "Generiere realm-import.json aus Template..."
    sed "s/\"sslRequired\": \"__SSL_REQUIRED__\"/\"sslRequired\": \"$SSL_REQUIRED\"/" "$REALM_TEMPLATE" > "$REALM_OUTPUT"
    echo "✓ Realm-Konfiguration erstellt"
else
    echo "⚠ Kein Template gefunden, verwende existierende realm-import.json"
fi

echo "======================================"
echo "Starte Keycloak..."
echo "======================================"

# Führe ursprüngliches Keycloak-Kommando aus
exec /opt/keycloak/bin/kc.sh "$@"
