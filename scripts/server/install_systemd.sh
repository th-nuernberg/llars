#!/usr/bin/env bash
# =============================================================================
# LLARS Systemd Service Installer
# =============================================================================
# Installs/updates llars.service + health check timer on the server.
# All paths are derived automatically from the script's own location.
#
# Can be run in two ways:
#   1. Locally on server:  sudo bash /var/llars/scripts/server/install_systemd.sh
#   2. Remotely via SSH:   From repo root, run scripts/server/deploy_systemd.sh
#
# What it does:
#   1. Derives LLARS_ROOT from script location (scripts/server/ → ../../)
#   2. Generates systemd unit files with correct absolute paths
#   3. Installs updated llars.service (with retry logic)
#   4. Installs llars-healthcheck.service + timer (auto-recovery every 3 min)
#   5. Reloads systemd, enables the timer
# =============================================================================

set -euo pipefail

# --- Resolve LLARS_ROOT from script location ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LLARS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SCRIPTS_DIR="${SCRIPT_DIR}"
SYSTEMD_DIR="/etc/systemd/system"

echo "=== LLARS Systemd Installer ==="
echo "  LLARS_ROOT:  ${LLARS_ROOT}"
echo "  SCRIPTS_DIR: ${SCRIPTS_DIR}"

# Verify we're in the right place
if [ ! -f "${LLARS_ROOT}/docker-compose.yml" ]; then
    echo "ERROR: docker-compose.yml not found at ${LLARS_ROOT}/docker-compose.yml"
    echo "       Script must be located at <LLARS_ROOT>/scripts/server/install_systemd.sh"
    exit 1
fi

# Verify scripts exist
for script in llars_start_retry.sh llars_healthcheck.sh; do
    if [ ! -f "${SCRIPTS_DIR}/${script}" ]; then
        echo "ERROR: ${script} not found at ${SCRIPTS_DIR}/${script}"
        exit 1
    fi
done

# 1. Make scripts executable
echo "[1/5] Setting script permissions..."
chmod +x "${SCRIPTS_DIR}/llars_start_retry.sh"
chmod +x "${SCRIPTS_DIR}/llars_healthcheck.sh"

# 2. Backup old service
echo "[2/5] Backing up old llars.service..."
if [ -f "$SYSTEMD_DIR/llars.service" ]; then
    cp "$SYSTEMD_DIR/llars.service" "$SYSTEMD_DIR/llars.service.bak.$(date +%Y%m%d)"
fi

# 3. Generate and install systemd units (paths injected from LLARS_ROOT)
echo "[3/5] Generating systemd units with LLARS_ROOT=${LLARS_ROOT}..."

# Detect compose files
COMPOSE_FILES="-f ${LLARS_ROOT}/docker-compose.yml"
[ -f "${LLARS_ROOT}/docker-compose.prod.yml" ] && COMPOSE_FILES="${COMPOSE_FILES} -f ${LLARS_ROOT}/docker-compose.prod.yml"

cat > "$SYSTEMD_DIR/llars.service" <<UNIT
[Unit]
Description=LLARS Docker Compose Stack
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${LLARS_ROOT}
Environment=LLARS_ROOT=${LLARS_ROOT}

# Wait for Docker daemon to be fully ready
ExecStartPre=/bin/bash -c 'until docker info >/dev/null 2>&1; do sleep 2; done'

# Start LLARS with retry logic (handles transient healthcheck failures)
ExecStart=/bin/bash ${SCRIPTS_DIR}/llars_start_retry.sh

# Clean shutdown
ExecStop=/usr/bin/docker compose ${COMPOSE_FILES} down

TimeoutStartSec=600
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
UNIT

cat > "$SYSTEMD_DIR/llars-healthcheck.service" <<UNIT
[Unit]
Description=LLARS Health Check and Auto-Recovery
After=llars.service
Requires=llars.service

[Service]
Type=oneshot
WorkingDirectory=${LLARS_ROOT}
Environment=LLARS_ROOT=${LLARS_ROOT}
ExecStart=/bin/bash ${SCRIPTS_DIR}/llars_healthcheck.sh

# Don't log success (runs every 3 min, would spam the journal)
StandardOutput=null
StandardError=journal
UNIT

cat > "$SYSTEMD_DIR/llars-healthcheck.timer" <<UNIT
[Unit]
Description=LLARS Health Check Timer (every 3 minutes)
After=llars.service

[Timer]
# Start 90s after boot (give llars.service time to finish)
OnBootSec=90
# Then check every 3 minutes
OnUnitActiveSec=180

[Install]
WantedBy=timers.target
UNIT

# 4. Reload and enable
echo "[4/5] Reloading systemd and enabling timer..."
systemctl daemon-reload
systemctl enable llars.service
systemctl enable llars-healthcheck.timer
systemctl start llars-healthcheck.timer

# 5. Verify
echo "[5/5] Verifying installation..."
echo ""
systemctl list-timers llars-healthcheck.timer --no-pager
echo ""
echo "=== Installation complete ==="
echo "  llars.service:             updated (retry + force-start logic)"
echo "  llars-healthcheck.timer:   enabled (every 3 min auto-recovery)"
echo ""
echo "  Generated paths:"
echo "    LLARS_ROOT:    ${LLARS_ROOT}"
echo "    Start script:  ${SCRIPTS_DIR}/llars_start_retry.sh"
echo "    Health script:  ${SCRIPTS_DIR}/llars_healthcheck.sh"
echo ""
echo "Verify with:"
echo "  systemctl status llars.service"
echo "  systemctl status llars-healthcheck.timer"
echo "  journalctl -u llars-healthcheck.service --since '5 min ago'"
