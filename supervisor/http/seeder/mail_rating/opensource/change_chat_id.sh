#!/usr/bin/env bash

# Zielverzeichnis mit den JSON-Dateien
TARGET_DIR="/Users/philippsteigerwald/PycharmProjects/llars/supervisor/http/seeder/mail_rating/opensource"

# Offset für die neuen chat_ids (da alte chat_ids von 1 bis 128 belegt sind)
CHAT_ID_OFFSET=128

# Durch alle neuen Dateien von 129 bis 228 iterieren
for i in {129..228}; do
  FILE="$TARGET_DIR/conversation_${i}.json"

  if [[ -f "$FILE" ]]; then
    # Erhöhe die chat_id in der Datei um den Offset
    jq --argjson offset "$CHAT_ID_OFFSET" '.chat_id += $offset' "$FILE" > "${FILE}.tmp" && mv "${FILE}.tmp" "$FILE"
    echo "Updated chat_id in $FILE"
  else
    echo "Warning: $FILE does not exist, skipping."
  fi
done
