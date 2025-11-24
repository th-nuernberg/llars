#!/bin/bash
# ============================================
# Keycloak Startup Script with Dynamic Realm Configuration
# ============================================
# This script:
# 1. Generates realm-import.json from template based on PROJECT_STATE
# 2. Starts Keycloak in appropriate mode (dev/prod)

set -e

echo "================================================"
echo "Keycloak Startup Script"
echo "================================================"
echo "Project State: ${PROJECT_STATE:-development}"
echo "================================================"

# ============================================
# Step 1: Configure Realm from Template
# ============================================
echo "[1/2] Generating realm configuration..."

if [ ! -f /opt/keycloak/import-config/realm-import-template.json ]; then
    echo "ERROR: realm-import-template.json not found!"
    exit 1
fi

# Run Python configuration script
python3 /opt/keycloak/import-config/configure-realm.py

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to generate realm configuration"
    exit 1
fi

echo "[1/2] Realm configuration generated successfully"

# ============================================
# Step 2: Start Keycloak
# ============================================
echo "[2/2] Starting Keycloak..."

if [ "${PROJECT_STATE}" = "production" ]; then
    echo "Starting Keycloak in PRODUCTION mode (optimized)"
    exec /opt/keycloak/bin/kc.sh start --optimized --import-realm
else
    echo "Starting Keycloak in DEVELOPMENT mode"
    exec /opt/keycloak/bin/kc.sh start-dev --import-realm
fi
