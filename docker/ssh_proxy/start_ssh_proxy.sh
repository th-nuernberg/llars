#!/bin/sh

# Setze die Umgebungsvariablen für die SSH-Verbindung
PROXY_REMOTE_USER=${PROXY_REMOTE_USER:-steigerwaldph}
PROXY_REMOTE_HOST=${PROXY_REMOTE_HOST:-141.75.89.10}
PROXY_REMOTE_PORT=${PROXY_REMOTE_PORT:-8093}
PROXY_LOCAL_PORT=${PROXY_LOCAL_PORT:-8093}
SSH_KEY_PATH="/root/.ssh/id_rsa"

# Setze Umgebungsvariablen für autossh
export AUTOSSH_LOGFILE="/var/log/autossh.log"
export AUTOSSH_DEBUG=1
export AUTOSSH_GATETIME=0

# Funktion zum Starten von autossh
start_autossh() {
    autossh -M 0 -N -o "StrictHostKeyChecking=no" -o "UserKnownHostsFile=/dev/null" \
        -L 0.0.0.0:${PROXY_LOCAL_PORT}:localhost:${PROXY_REMOTE_PORT} \
        -i "$SSH_KEY_PATH" ${PROXY_REMOTE_USER}@${PROXY_REMOTE_HOST} -v 2>&1 | tee -a $AUTOSSH_LOGFILE &

    AUTOSSH_PID=$!
}

# Funktion zum Überprüfen der Verbindung
check_connection() {
    RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8093/info)
    HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
    RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_STATUS" = "200" ]; then
        echo "$(date): Successfully connected to localhost:8093/info" | tee -a $AUTOSSH_LOGFILE
        echo "Response from server:" | tee -a $AUTOSSH_LOGFILE
        echo "$RESPONSE_BODY" | tee -a $AUTOSSH_LOGFILE
    else
        echo "$(date): Failed to connect to localhost:8093/info" | tee -a $AUTOSSH_LOGFILE
        echo "HTTP Status: $HTTP_STATUS" | tee -a $AUTOSSH_LOGFILE
        echo "Response from server:" | tee -a $AUTOSSH_LOGFILE
        echo "$RESPONSE_BODY" | tee -a $AUTOSSH_LOGFILE
    fi
}

echo "Starting SSH Tunnel to ${PROXY_REMOTE_USER}@${PROXY_REMOTE_HOST}, forwarding local port ${PROXY_LOCAL_PORT} to remote port ${PROXY_REMOTE_PORT}..."

# Starte autossh
start_autossh

# Warte kurz, damit der Tunnel Zeit hat, sich aufzubauen
sleep 5

# Erste Überprüfung
check_connection

# Hauptschleife
while true; do
    if ! kill -0 $AUTOSSH_PID 2>/dev/null; then
        echo "$(date): autossh process died. Restarting..." | tee -a $AUTOSSH_LOGFILE
        start_autossh
        sleep 5
    fi

    # Überprüfe die Verbindung
    check_connection

    # Warte eine Minute bis zur nächsten Überprüfung
    sleep 60
done