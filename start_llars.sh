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
docker compose -p llars up --build  --remove-orphans --detach
echo "Waiting for services to start..."

# Überprüfung, ob alle Container laufen
while true; do
    RUNNING_CONTAINERS=$(docker compose -p llars ps | grep 'Up' | wc -l)
    TOTAL_CONTAINERS=$(docker compose -p llars config --services | wc -l)

    if [ "$RUNNING_CONTAINERS" -eq "$TOTAL_CONTAINERS" ]; then
        echo "Alle Container sind gestartet."
        break
    else
        echo "Warte auf den Start der Container... ($RUNNING_CONTAINERS von $TOTAL_CONTAINERS sind bereit)"
        sleep 5
    fi
done
sleep 10
echo "Compose Watch"
docker compose watch
docker compose -p llars up # Attaching to LLars-Network output
