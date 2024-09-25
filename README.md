# LLARS - Labeling und Leistungsbewertung von Antworten in Sprachmodellen

LLARS (Labeling und Leistungsbewertung von Antworten in Sprachmodellen) ist ein System zur Bewertung und zum Ranking von Outputs generierter Antworten durch verschiedene Sprachmodelle. Es hilft dabei, die Leistungsfähigkeit der Modelle durch menschliche und automatische Bewertung zu analysieren.

Im Englischen wird LLARS als **BARS** bezeichnet, was für **Benchmarking and Review System** steht.

## Voraussetzungen

Um LLARS auszuführen, müssen folgende Voraussetzungen erfüllt sein:

- **Docker** muss installiert sein. Du kannst Docker [hier herunterladen](https://docs.docker.com/get-docker/).

## Installation

1. **Docker installieren**: Falls Docker noch nicht installiert ist, folge den Anweisungen in der [offiziellen Docker-Dokumentation](https://docs.docker.com/get-docker/), um es auf deinem System zu installieren.

2. **Projekt klonen**: Klone das LLARS-Projekt auf deinen Rechner:

   ```bash
   git clone https://github.com/dein-repo/llars.git
   cd llars
   ```

## Projekt starten

Sobald Docker installiert ist, kannst du das Projekt mit folgendem Skript starten:

```bash
./start_llars.sh
```

Das Skript startet die notwendigen Docker-Container und konfiguriert das System entsprechend.

## Verwendung

Nachdem das Projekt gestartet wurde, kannst du über deinen Webbrowser auf das LLARS-Dashboard zugreifen. Der Standardzugangspunkt ist:

```
http://localhost:PORT
```

(Den richtigen `PORT` kannst du der `docker-compose.yml` Datei entnehmen.)

## Projektstruktur

* `start_llars.sh`: Skript zum Starten des Projekts mit Docker.
* `docker-compose.yml`: Konfigurationsdatei für Docker-Container.
* `backend/`: Backend-Komponenten des Projekts.
* `frontend/`: Frontend-Komponenten des Projekts.

## Troubleshooting

Falls beim Start des Projekts Fehler auftreten, überprüfe die folgenden Punkte:

* **Docker ist installiert und läuft korrekt.** Überprüfe dies mit:

  ```bash
  docker --version
  ```

* **Keine Port-Konflikte**: Stelle sicher, dass der Port, auf dem der LLARS-Dienst läuft, nicht von anderen Prozessen belegt ist.

## Lizenz

Dieses Projekt steht unter der [Lizenzname]-Lizenz. Details findest du in der Datei `LICENSE`.
