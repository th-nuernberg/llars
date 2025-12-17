#!/bin/bash
set -euo pipefail

echo "======================================="
echo "  Matomo Auto-Configuration Script"
echo "======================================="

MATOMO_DIR="/var/www/html"
CONFIG_FILE="${MATOMO_DIR}/config/config.ini.php"

: "${MATOMO_DATABASE_HOST:?MATOMO_DATABASE_HOST is required}"
: "${MATOMO_DATABASE_USERNAME:?MATOMO_DATABASE_USERNAME is required}"
: "${MATOMO_DATABASE_PASSWORD:?MATOMO_DATABASE_PASSWORD is required}"
: "${MATOMO_DATABASE_DBNAME:?MATOMO_DATABASE_DBNAME is required}"

MATOMO_DATABASE_TABLES_PREFIX="${MATOMO_DATABASE_TABLES_PREFIX:-matomo_}"
MATOMO_DATABASE_ADAPTER="${MATOMO_DATABASE_ADAPTER:-PDO\\MYSQL}"

PROJECT_URL="${PROJECT_URL:-}"
PROJECT_HOST="${PROJECT_HOST:-localhost}"
PROJECT_STATE="${PROJECT_STATE:-development}"
NGINX_EXTERNAL_PORT="${NGINX_EXTERNAL_PORT:-80}"

export MATOMO_SUPERUSER_LOGIN="${MATOMO_SUPERUSER_LOGIN:-admin}"
export MATOMO_SUPERUSER_PASSWORD="${MATOMO_SUPERUSER_PASSWORD:-}"
export MATOMO_SUPERUSER_EMAIL="${MATOMO_SUPERUSER_EMAIL:-admin@example.com}"
export MATOMO_SITE_NAME="${MATOMO_SITE_NAME:-LLARS}"
DEFAULT_SITE_URL="${PROJECT_URL}"
if [ -z "${DEFAULT_SITE_URL}" ]; then
  if [ "${PROJECT_STATE}" = "production" ]; then
    DEFAULT_SITE_URL="https://${PROJECT_HOST}"
  else
    DEFAULT_SITE_URL="http://${PROJECT_HOST}:${NGINX_EXTERNAL_PORT}"
  fi
fi
export MATOMO_SITE_URL="${MATOMO_SITE_URL:-${DEFAULT_SITE_URL}}"

# Matomo validates the HTTP Host header against [General] trusted_hosts[].
# When running LLARS in development behind Docker (host port != container port),
# the incoming Host header includes the external port (e.g. localhost:55080).
# If trusted_hosts does not include the port variant, Matomo will fall back to the
# first trusted host and generate wrong absolute URLs (breaking CSP and assets).
MATOMO_TRUSTED_HOST_FROM_URL="$(echo "${MATOMO_SITE_URL}" | sed -E 's#https?://([^/]+).*#\1#')"
export MATOMO_TRUSTED_HOST="${MATOMO_TRUSTED_HOST:-${MATOMO_TRUSTED_HOST_FROM_URL:-${PROJECT_HOST}}}"

if [ -z "${MATOMO_SITE_URL}" ]; then
  echo "ERROR: MATOMO_SITE_URL is empty (set MATOMO_SITE_URL or PROJECT_URL in .env)"
  exit 1
fi

if [ -z "${MATOMO_SUPERUSER_PASSWORD}" ]; then
  echo "ERROR: MATOMO_SUPERUSER_PASSWORD is empty (set it in .env)"
  exit 1
fi

if [ "${PROJECT_STATE}" = "production" ]; then
  if [ "${MATOMO_SUPERUSER_PASSWORD}" = "admin123" ]; then
    echo "ERROR: MATOMO_SUPERUSER_PASSWORD is still the insecure default (admin123). Set a strong password in production."
    exit 1
  fi
  if [ "${MATOMO_DATABASE_PASSWORD}" = "matomo_password_change_me" ]; then
    echo "ERROR: MATOMO_DATABASE_PASSWORD is still the insecure default. Set a strong password in production."
    exit 1
  fi
fi

mkdir -p "${MATOMO_DIR}/config"

if [ ! -f "${CONFIG_FILE}" ]; then
  echo "[1/4] Creating Matomo config: ${CONFIG_FILE}"

  SALT="$(php -r 'echo bin2hex(random_bytes(16));')"

  cat > "${CONFIG_FILE}" <<EOF
; <?php exit; ?> DO NOT REMOVE THIS LINE

[database]
host = "${MATOMO_DATABASE_HOST}"
username = "${MATOMO_DATABASE_USERNAME}"
password = "${MATOMO_DATABASE_PASSWORD}"
dbname = "${MATOMO_DATABASE_DBNAME}"
tables_prefix = "${MATOMO_DATABASE_TABLES_PREFIX}"
port = 3306
adapter = ${MATOMO_DATABASE_ADAPTER}
type = InnoDB
schema = Mysql
charset = utf8mb4
collation = utf8mb4_general_ci

[General]
salt = "${SALT}"
trusted_hosts[] = "${MATOMO_TRUSTED_HOST}"
proxy_uri_header = 1
installation_in_progress = 1
EOF

  chmod 640 "${CONFIG_FILE}" || true
fi

echo "[2/4] Running Matomo installer (idempotent)..."
php /install-matomo.php

ensure_proxy_uri_header() {
  if [ ! -f "${CONFIG_FILE}" ]; then
    return 0
  fi

  if grep -qE '^[[:space:]]*proxy_uri_header[[:space:]]*=' "${CONFIG_FILE}"; then
    sed -i -E 's/^[[:space:]]*proxy_uri_header[[:space:]]*=.*/proxy_uri_header = 1/' "${CONFIG_FILE}" || true
    return 0
  fi

  TMP_FILE="$(mktemp)"
  awk '
    BEGIN { inserted = 0 }
    /^[[:space:]]*\[General\][[:space:]]*$/ {
      print
      print "proxy_uri_header = 1"
      inserted = 1
      next
    }
    { print }
    END {
      if (inserted == 0) {
        print ""
        print "[General]"
        print "proxy_uri_header = 1"
      }
    }
  ' "${CONFIG_FILE}" > "${TMP_FILE}"
  mv "${TMP_FILE}" "${CONFIG_FILE}"
}

ensure_proxy_uri_header

cleanup_duplicate_general_sections() {
  if [ ! -f "${CONFIG_FILE}" ]; then
    return 0
  fi

  TMP_FILE="$(mktemp)"
  awk '
    BEGIN { general_seen = 0; skipping = 0 }
    /^[[:space:]]*\[General\][[:space:]]*$/ {
      general_seen++
      if (general_seen > 1) {
        skipping = 1
        next
      }
      skipping = 0
      print
      next
    }
    /^[[:space:]]*\[[^]]+\][[:space:]]*$/ {
      skipping = 0
      print
      next
    }
    {
      if (skipping) next
      print
    }
  ' "${CONFIG_FILE}" > "${TMP_FILE}"
  mv "${TMP_FILE}" "${CONFIG_FILE}"
}

cleanup_duplicate_general_sections

cleanup_invalid_trusted_hosts() {
  if [ ! -f "${CONFIG_FILE}" ]; then
    return 0
  fi

  TMP_FILE="$(mktemp)"
  awk '
    BEGIN { bad = sprintf("%c", 1) }
    {
      if ($0 ~ /^[[:space:]]*trusted_hosts\[\][[:space:]]*=/ && index($0, bad) > 0) {
        next
      }
      print
    }
  ' "${CONFIG_FILE}" > "${TMP_FILE}"
  mv "${TMP_FILE}" "${CONFIG_FILE}"
}

cleanup_invalid_trusted_hosts

ensure_trusted_host() {
  local host="${1:-}"
  if [ -z "${host}" ]; then
    return 0
  fi
  if [ ! -f "${CONFIG_FILE}" ]; then
    return 0
  fi

  if grep -qF "trusted_hosts[] = \"${host}\"" "${CONFIG_FILE}"; then
    return 0
  fi

  TMP_FILE="$(mktemp)"
  awk -v host="${host}" '
    BEGIN { inserted = 0 }
    /^[[:space:]]*\[General\][[:space:]]*$/ {
      print
      print "trusted_hosts[] = \"" host "\""
      inserted = 1
      next
    }
    { print }
    END {
      if (inserted == 0) {
        print ""
        print "[General]"
        print "trusted_hosts[] = \"" host "\""
      }
    }
  ' "${CONFIG_FILE}" > "${TMP_FILE}"
  mv "${TMP_FILE}" "${CONFIG_FILE}"
}

# Always ensure both host variants are trusted (host and host:port)
ensure_trusted_host "${MATOMO_TRUSTED_HOST}"
if [ -n "${MATOMO_TRUSTED_HOST_FROM_URL:-}" ] && [ "${MATOMO_TRUSTED_HOST_FROM_URL}" != "${MATOMO_TRUSTED_HOST}" ]; then
  ensure_trusted_host "${MATOMO_TRUSTED_HOST_FROM_URL}"
fi

is_truthy() {
  case "$(echo "${1:-}" | tr '[:upper:]' '[:lower:]' | xargs)" in
    1|true|yes|y|on) return 0 ;;
    *) return 1 ;;
  esac
}

if is_truthy "${MATOMO_OIDC_ENABLED:-false}"; then
  echo "[3/4] Installing and configuring OIDC SSO (RebelOIDC)..."

  if [ "${PROJECT_STATE}" = "production" ]; then
    if [ "${AUTHENTIK_MATOMO_CLIENT_SECRET:-}" = "llars-matomo-secret-change-in-production" ]; then
      echo "ERROR: AUTHENTIK_MATOMO_CLIENT_SECRET is still the insecure default. Set a strong secret in production."
      exit 1
    fi
  fi

  MATOMO_DOMAIN="${MATOMO_SITE_URL}"
  MATOMO_DOMAIN="$(echo "${MATOMO_DOMAIN}" | sed -E 's#(https?://[^/]+).*#\\1#')"

  php "${MATOMO_DIR}/console" plugin:install-or-update RebelOIDC --no-interaction --ignore-warn --matomo-domain="${MATOMO_DOMAIN}"
  php "${MATOMO_DIR}/console" plugin:activate RebelOIDC --no-interaction --ignore-warn --matomo-domain="${MATOMO_DOMAIN}"

  php /configure-rebeloidc.php
fi

echo "[4/4] Ensuring permissions..."
chown -R www-data:www-data "${MATOMO_DIR}/config" || true
chown -R www-data:www-data "${MATOMO_DIR}/tmp" || true

echo "======================================="
echo "  Matomo configuration complete!"
echo "======================================="
