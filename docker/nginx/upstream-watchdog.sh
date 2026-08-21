#!/bin/sh
# ============================================
# Nginx Upstream Watchdog
# ============================================
# Detects when upstream containers get new Docker IPs after restarts
# and reloads nginx to re-resolve DNS. Prevents 502 errors caused by
# stale DNS cache in nginx upstream blocks.
#
# Background: nginx resolves upstream hostnames only at config load time.
# When a container restarts and gets a new IP, nginx keeps using the old
# cached IP → 502 "Host is unreachable". This watchdog reloads nginx
# to force DNS re-resolution.

CHECK_INTERVAL="${WATCHDOG_INTERVAL:-15}"
FAIL_THRESHOLD=2
BACKEND_URL="http://127.0.0.1/auth/health_check"

consecutive_failures=0
last_reload_time=0

log() {
    echo "[upstream-watchdog] $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Wait for nginx to fully start
sleep 10

log "Started (interval=${CHECK_INTERVAL}s, threshold=${FAIL_THRESHOLD})"

while true; do
    # Check if backend is reachable through nginx
    if wget -q -O /dev/null --timeout=5 "$BACKEND_URL" 2>/dev/null; then
        if [ "$consecutive_failures" -gt 0 ]; then
            log "Backend recovered after ${consecutive_failures} failures"
        fi
        consecutive_failures=0
    else
        consecutive_failures=$((consecutive_failures + 1))

        if [ "$consecutive_failures" -ge "$FAIL_THRESHOLD" ]; then
            current_time=$(date +%s)
            # Cooldown: don't reload more than once per 30 seconds
            time_since_reload=$((current_time - last_reload_time))
            if [ "$time_since_reload" -ge 30 ]; then
                log "Backend unreachable (${consecutive_failures}x), reloading nginx to re-resolve DNS"
                nginx -s reload 2>/dev/null && log "Nginx reloaded successfully" || log "Nginx reload failed"
                last_reload_time=$current_time
                consecutive_failures=0
            fi
        fi
    fi

    sleep "$CHECK_INTERVAL"
done
