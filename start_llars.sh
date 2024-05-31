#!/bin/sh
# Lade Umgebungsvariablen
source .env

# Überprüfen, ob der Docker-Daemon läuft
if ! docker info >/dev/null 2>&1; then
    echo "Docker-Daemon läuft nicht. Versuche zu starten..."
    # Versuchen, Docker mit systemctl zu starten
    open /Applications/Docker.app
    sleep 5
    # Überprüfen, ob der Start erfolgreich war
    if ! docker info >/dev/null 2>&1; then
        echo "Fehler beim Starten des Docker-Daemons. Bitte manuell überprüfen."
        exit 1
    fi
    echo "Docker-Daemon erfolgreich gestartet."
else
    echo "Docker-Daemon läuft bereits."
fi

# Stoppen der Dienste
echo "Stopping services..."
if [ "$REMOVE_VOLUMES" = "True" ]; then
  echo "Removing volumes..."
  docker compose -p llars down --volumes
  echo "Successfully removed volumes."
  echo "Services stopped."
else
  docker compose -p llars down
  echo "Services stopped."
fi

# Ausführen von Docker Compose mit --build
echo "Ausführen von Docker Compose mit --build..."
docker compose -p llars up --build  --remove-orphans --watch #--detach
echo "Waiting for services to start..."

#sleep 10
#echo "Compose Watch"
#docker compose watch
#docker compose -p llars up # Attaching to LLars-Network output
