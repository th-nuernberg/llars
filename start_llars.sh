#!/bin/sh
# Lade Umgebungsvariablen

source .env

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
docker compose -p llars up --build  --remove-orphans