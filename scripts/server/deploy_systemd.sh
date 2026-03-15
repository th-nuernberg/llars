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
#
# Password handling:
#   Uses a temporary file descriptor to pipe the sudo password, avoiding
#   shell quoting issues with special characters in passwords.
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

# --- Read credentials from .env ---
# Uses Python to safely parse values with special characters (quotes, pipes, etc.)
get_env() {
    python3 -c "
import re, sys
with open('${ENV_FILE}') as f:
    for line in f:
        m = re.match(r'^${1}=(.*)', line.rstrip('\n'))
        if m:
            print(m.group(1))
            sys.exit(0)
sys.exit(1)
" 2>/dev/null
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

# --- Helper: run command with sudo on remote, piping password via stdin ---
# Uses a heredoc to avoid shell quoting issues with special characters
remote_sudo() {
    ssh "$SSH_HOST" "cat | sudo -S bash -c '$1'" <<< "$SUDO_PASS" 2>/dev/null
}

# --- Determine LLARS_ROOT on the remote server ---
# Check existing service file, fall back to finding docker-compose.yml, then /var/llars
REMOTE_LLARS_ROOT=$(ssh "$SSH_HOST" bash -c '
    # Try existing systemd service
    if [ -f /etc/systemd/system/llars.service ]; then
        val=$(grep -m1 "^WorkingDirectory=" /etc/systemd/system/llars.service | cut -d= -f2-)
        if [ -n "$val" ] && [ -d "$val" ]; then
            echo "$val"
            exit 0
        fi
    fi
    # Try common locations
    for dir in /var/llars /opt/llars /home/*/llars; do
        if [ -f "$dir/docker-compose.yml" ]; then
            echo "$dir"
            exit 0
        fi
    done
    # Final fallback
    echo "/var/llars"
')
REMOTE_SCRIPTS_DIR="${REMOTE_LLARS_ROOT}/scripts/server"

echo "  SSH_HOST:          ${SSH_HOST}"
echo "  REMOTE_LLARS_ROOT: ${REMOTE_LLARS_ROOT}"
echo "  REMOTE_SCRIPTS:    ${REMOTE_SCRIPTS_DIR}"
echo ""

# --- 1. Ensure remote directory exists ---
echo "[1/3] Creating remote directory..."
remote_sudo "mkdir -p '${REMOTE_SCRIPTS_DIR}'"
# Set ownership to the SSH user so scp works without sudo
REMOTE_USER=$(ssh "$SSH_HOST" whoami)
remote_sudo "chown -R ${REMOTE_USER}:${REMOTE_USER} '${REMOTE_SCRIPTS_DIR}'"

# --- 2. Copy scripts ---
echo "[2/3] Copying scripts to ${SSH_HOST}:${REMOTE_SCRIPTS_DIR}/..."
scp -q \
    "${SCRIPT_DIR}/llars_start_retry.sh" \
    "${SCRIPT_DIR}/llars_healthcheck.sh" \
    "${SCRIPT_DIR}/llars_cleanup.sh" \
    "${SCRIPT_DIR}/install_systemd.sh" \
    "${SSH_HOST}:${REMOTE_SCRIPTS_DIR}/"

# --- 3. Run installer with sudo ---
echo "[3/3] Running install_systemd.sh on ${SSH_HOST}..."
echo ""
remote_sudo "bash '${REMOTE_SCRIPTS_DIR}/install_systemd.sh'"

echo ""
echo "=== Deployment complete ==="
