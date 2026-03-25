#!/bin/sh

set -eu

prepare_storage() {
  mkdir -p \
    /app/storage \
    /app/storage/rag_images \
    /app/storage/screenshots \
    /app/storage/models \
    /app/storage/vectorstore
}

if [ "$(id -u)" = "0" ] && [ "${LLARS_FLASK_PRIVDROP_DONE:-0}" != "1" ]; then
  echo "Preparing writable storage directories for flaskuser..."
  prepare_storage
  chown -R flaskuser:flaskuser /app/storage
  chmod -R u+rwX,g+rwX /app/storage || true

  export LLARS_FLASK_PRIVDROP_DONE=1
  exec gosu flaskuser /usr/local/bin/start_flask.sh "$@"
fi

echo "Waiting for 2 seconds before starting the Flask app..."
sleep 2

# Ensure storage directories exist and are writable even when the container
# was started without the root setup branch above.
prepare_storage 2>/dev/null || true

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
FLASK_ENV_MODE="${FLASK_ENV:-}"

echo "Starting Flask app on port 8081 (PROJECT_STATE: $PROJECT_STATE, FLASK_ENV: $FLASK_ENV_MODE)..."

if [ "$PROJECT_STATE" = "production" ] || [ "$FLASK_ENV_MODE" = "production" ]; then
    # Production: Use Gunicorn with gevent-websocket for real WebSocket support
    # - No auto-reload (code changes require restart)
    # - Gevent worker for async/WebSocket handling (better Docker DNS than eventlet)
    # - Lower CPU usage, better performance, real WebSockets
    # - wsgi_gevent.py handles gevent monkey-patching before app import
    echo "Production mode: Starting with Gunicorn + gevent-websocket..."
    export SOCKETIO_ASYNC_MODE="gevent"
    exec gunicorn \
        --config /usr/local/bin/gunicorn.conf.py \
        "wsgi_gevent:app"
else
    # Development: Use Flask dev server with auto-reload
    # - Auto-reload on code changes
    # - Threading mode (polling fallback for WebSocket)
    # - Higher CPU usage due to file watching
    echo "Development mode: Starting with Flask dev server + auto-reload..."
    export SOCKETIO_ASYNC_MODE="threading"
    exec python -m flask --app main run --host=0.0.0.0 --port=8081 --reload
fi
