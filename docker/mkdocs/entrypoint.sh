#!/bin/sh
# MkDocs entrypoint with low-overhead dev server and static prod serving
set -e

STATE="${PROJECT_STATE:-development}"
BIND_ADDR="${MKDOCS_BIND_ADDR:-0.0.0.0:8000}"

# Split host/port so we can reuse the address for both mkdocs and python http.server
if echo "$BIND_ADDR" | grep -q ":"; then
  HOST="${BIND_ADDR%:*}"
  PORT="${BIND_ADDR##*:}"
else
  HOST="0.0.0.0"
  PORT="${BIND_ADDR}"
fi
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

start_dev() {
  echo "Starting MkDocs (development) at ${BIND_ADDR}"
  exec mkdocs serve \
    --dev-addr="${BIND_ADDR}" \
    --livereload \
    --watch mkdocs.yml \
    --watch docs
}

start_prod() {
  echo "Starting MkDocs (production) static server at ${HOST}:${PORT}"
  mkdocs build --clean --site-dir /docs/site
  exec python -m http.server "${PORT}" --bind "${HOST}" --directory /docs/site
}

case "$STATE" in
  production)
    start_prod
    ;;
  *)
    start_dev
    ;;
esac
