#!/bin/sh
set -e

# Select nginx config based on PROJECT_STATE
PROJECT_STATE="${PROJECT_STATE:-development}"

echo "[nginx-entrypoint] PROJECT_STATE=${PROJECT_STATE}"

if [ "$PROJECT_STATE" = "production" ]; then
    echo "[nginx-entrypoint] Using production config (HTTPS enabled)"
    cp /etc/nginx/nginx.prod.conf /etc/nginx/nginx.conf
else
    echo "[nginx-entrypoint] Using development config (HTTP only)"
    cp /etc/nginx/nginx.dev.conf /etc/nginx/nginx.conf
fi

# Test nginx config
nginx -t

# Execute the main command
exec "$@"
