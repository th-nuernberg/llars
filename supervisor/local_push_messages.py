#!/usr/bin/env python3

import os
import json
import requests

# Bitte hier anpassen:
FOLDER_PATH = "/Users/philippsteigerwald/PycharmProjects/darc/new_approach/generated_conversations"  # Pfad zum Ordner mit JSON-Dateien
# URL = "https://llars.e-beratungsinstitut.de/api/email_threads"  # Ziel-URL für die POST-Anfragen
URL = "http://localhost/api/email_threads"  # Ziel-URL für die POST-Anfragen

def main():
    if not os.path.isdir(FOLDER_PATH):
        print(f"Der Pfad '{FOLDER_PATH}' ist kein gültiger Ordner.")
        return

    print(f"Starte das Senden von JSON-Dateien aus '{FOLDER_PATH}' an '{URL}'.\n")

    # Rekursiv durch den angegebenen Ordner gehen
    for root, _, files in os.walk(FOLDER_PATH):
        for filename in files:
            if filename.lower().endswith(".json"):
                file_path = os.path.join(root, filename)
                print(f"Verarbeite Datei: {file_path}")

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # POST-Anfrage an die angegebene URL
                    response = requests.post(URL, json=data, headers={"Content-Type": "application/json"})

                    print(f"  → Status Code: {response.status_code}")
                    print(f"  → Response: {response.text}\n")

                except Exception as e:
                    print(f"Fehler beim Verarbeiten von {file_path}: {e}\n")

    print("Alle passenden JSON-Dateien wurden verarbeitet.")


if __name__ == "__main__":
    main()
