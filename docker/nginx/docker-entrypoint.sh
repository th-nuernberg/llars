#!/bin/sh
set -e

# Select nginx config based on PROJECT_STATE
PROJECT_STATE="${PROJECT_STATE:-development}"

echo "[nginx-entrypoint] PROJECT_STATE=${PROJECT_STATE}"

if [ "$PROJECT_STATE" = "production" ]; then
    # Check if SSL certificates exist
    if [ -f "/etc/nginx/certs/cert.pem" ] && [ -f "/etc/nginx/certs/key.pem" ]; then
        echo "[nginx-entrypoint] Using production config with SSL (HTTPS enabled)"
        cp -f /etc/nginx/nginx.prod.conf /etc/nginx/nginx.conf
    else
        echo "[nginx-entrypoint] No SSL certs found, using production config for reverse proxy (HTTP only)"
        # Use prod config but without HTTPS server block
        # The HTTP server handles X-Forwarded-Proto from upstream reverse proxy
        cp -f /etc/nginx/nginx.prod-no-ssl.conf /etc/nginx/nginx.conf
    fi
else
    echo "[nginx-entrypoint] Using development config (HTTP only)"
    cp -f /etc/nginx/nginx.dev.conf /etc/nginx/nginx.conf
fi

# Test nginx config
nginx -t

# Execute the main command
exec "$@"
