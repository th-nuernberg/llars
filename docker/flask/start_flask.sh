#!/bin/sh

echo "Waiting for 2 seconds before starting the Flask app..."
sleep 2

export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"
export FLASK_APP="main"
# Add local pip bin to PATH for gunicorn
export PATH="$PATH:/home/flaskuser/.local/bin"

echo "App directory listing:"
ls -la /app || true
python - <<'PY'
import os
import sys

print("sys.path:", sys.path)
print("main exists:", os.path.exists("/app/main.py"))
PY

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

# Determine environment: development or production
# PROJECT_STATE is set in docker-compose.yml from .env
PROJECT_STATE="${PROJECT_STATE:-development}"

echo "Starting Flask app on port 8081 (mode: $PROJECT_STATE)..."

if [ "$PROJECT_STATE" = "production" ]; then
    # Production: Use Gunicorn with eventlet for real WebSocket support
    # - No auto-reload (code changes require restart)
    # - Eventlet worker for async/WebSocket handling
    # - Lower CPU usage, better performance
    # - wsgi.py handles eventlet monkey-patching before app import
    echo "Production mode: Starting with Gunicorn + eventlet..."
    export SOCKETIO_ASYNC_MODE="eventlet"
    exec gunicorn \
        --config /usr/local/bin/gunicorn.conf.py \
        "wsgi:app"
else
    # Development: Use Flask dev server with auto-reload
    # - Auto-reload on code changes
    # - Threading mode (polling fallback for WebSocket)
    # - Higher CPU usage due to file watching
    echo "Development mode: Starting with Flask dev server + auto-reload..."
    export SOCKETIO_ASYNC_MODE="threading"
    exec python -m flask --app main run --host=0.0.0.0 --port=8081 --reload
fi
