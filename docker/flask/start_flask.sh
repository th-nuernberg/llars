#!/bin/sh

echo "Waiting for 2 seconds before starting the Flask app..."
sleep 2

export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"
export FLASK_APP="main"

python - <<'PY'
import importlib
import traceback
import sys

try:
    importlib.import_module("main")
except Exception:
    traceback.print_exc()
    sys.exit(1)
PY

DB_HOST="${MYSQL_HOST:-db-maria-service}"
DB_PORT="${MYSQL_PORT:-3306}"
DB_NAME="${MYSQL_DATABASE:-database_llars}"
DB_USER="${MYSQL_USER:-dev_user}"
DB_PASS="${MYSQL_PASSWORD:-dev_password_change_me}"
MIGRATION_FILE="/app/migrations/20250214_chat_conversations_and_traces.sql"

if command -v mysql >/dev/null 2>&1 && [ -f "$MIGRATION_FILE" ]; then
  echo "Applying chat schema migration (idempotent)..."
  mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "-p$DB_PASS" "$DB_NAME" < "$MIGRATION_FILE" || echo "⚠️ Migration may have already been applied or failed; continuing startup."
else
  echo "Skipping migration (mysql client or file missing)"
fi

# Starte die Flask-App
# Note: Using threading async_mode for SocketIO, which works with flask run
# WebSocket will use long-polling fallback but is fully functional
echo "Starting Flask app on port 8081..."
python -m flask --app main run --host=0.0.0.0 --port=8081 --reload
