#!/usr/bin/env bash
# =============================================================================
# LLARS Systemd Remote Deployer
# =============================================================================
# Deploys the systemd service files to the production server via SSH.
# Reads server credentials from the project .env file.
#
# Usage (from repo root):
#   bash scripts/server/deploy_systemd.sh [prod|dev]
#
# What it does:
#   1. Reads SSH host + sudo password from .env
#   2. Copies scripts to server via scp
#   3. Runs install_systemd.sh on the server via SSH + sudo
# =============================================================================

set -euo pipefail

# --- Resolve paths from script location ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"

TARGET="${1:-prod}"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env not found at ${ENV_FILE}"
    exit 1
fi

# --- Read credentials from .env (handles special chars in passwords) ---
get_env() {
    grep "^${1}=" "$ENV_FILE" | head -1 | cut -d= -f2-
}

case "$TARGET" in
    prod|production)
        SSH_HOST="llars"
        SUDO_PASS="$(get_env LLARS_SERVER_PASSWORD)"
        echo "=== Deploying systemd services to PRODUCTION ==="
        ;;
    dev)
        SSH_HOST="llars-dev"
        SUDO_PASS="$(get_env LLARS_DEV_SERVER_PASSWORD)"
        echo "=== Deploying systemd services to DEV ==="
        ;;
    *)
        echo "Usage: $0 [prod|dev]"
        exit 1
        ;;
esac

if [ -z "$SUDO_PASS" ]; then
    echo "ERROR: Could not read server password from ${ENV_FILE}"
    exit 1
fi

# --- Determine LLARS_ROOT on the remote server ---
REMOTE_LLARS_ROOT=$(ssh "$SSH_HOST" 'grep -m1 "^WorkingDirectory=" /etc/systemd/system/llars.service 2>/dev/null | cut -d= -f2- || echo "/var/llars"')
REMOTE_SCRIPTS_DIR="${REMOTE_LLARS_ROOT}/scripts/server"

echo "  SSH_HOST:          ${SSH_HOST}"
echo "  REMOTE_LLARS_ROOT: ${REMOTE_LLARS_ROOT}"
echo "  REMOTE_SCRIPTS:    ${REMOTE_SCRIPTS_DIR}"
echo ""

# --- 1. Ensure remote directory exists ---
echo "[1/3] Creating remote directory..."
ssh "$SSH_HOST" "echo '${SUDO_PASS}' | sudo -S mkdir -p '${REMOTE_SCRIPTS_DIR}' && echo '${SUDO_PASS}' | sudo -S chown \$(whoami):\$(id -gn) '${REMOTE_SCRIPTS_DIR}'" 2>/dev/null

# --- 2. Copy scripts ---
echo "[2/3] Copying scripts to ${SSH_HOST}:${REMOTE_SCRIPTS_DIR}/..."
scp -q \
    "${SCRIPT_DIR}/llars_start_retry.sh" \
    "${SCRIPT_DIR}/llars_healthcheck.sh" \
    "${SCRIPT_DIR}/install_systemd.sh" \
    "${SSH_HOST}:${REMOTE_SCRIPTS_DIR}/"

# --- 3. Run installer with sudo ---
echo "[3/3] Running install_systemd.sh on ${SSH_HOST}..."
echo ""
ssh "$SSH_HOST" "echo '${SUDO_PASS}' | sudo -S bash '${REMOTE_SCRIPTS_DIR}/install_systemd.sh'" 2>/dev/null

echo ""
echo "=== Deployment complete ==="
