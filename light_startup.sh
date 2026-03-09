#!/bin/bash
# ============================================
# LLARS Light Startup Script
# ============================================
# Fast startup path:
# - does NOT stop existing services
# - does NOT force image rebuilds
# - does NOT remove volumes/images/cache
#
# Usage:
#   ./light_startup.sh
#   ./light_startup.sh dev
#   ./light_startup.sh prod
#   ./light_startup.sh --watch
#   ./light_startup.sh --detach
#   ./light_startup.sh dev backend-flask-service frontend-vue-service nginx-service
# ============================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR"
ENV_FILE="$BASE_DIR/.env"

PROJECT_STATE_ARG=""
DETACH_MODE="${LLARS_DETACH:-true}"
WATCH_MODE=false
SERVICES=()

for arg in "$@"; do
    case "$arg" in
        dev|development)
            PROJECT_STATE_ARG="development"
            ;;
        prod|production)
            PROJECT_STATE_ARG="production"
            ;;
        --detach|--detached)
            DETACH_MODE=true
            WATCH_MODE=false
            ;;
        --watch)
            WATCH_MODE=true
            DETACH_MODE=false
            ;;
        -h|--help)
            cat <<'EOF'
LLARS Light Startup Script

Usage:
  ./light_startup.sh [dev|prod] [--detach|--watch] [service ...]

Behavior:
  - Starts LLARS without cleanup and without forced rebuild.
  - Uses docker-compose.yml (+ docker-compose.prod.yml in production).
  - Optional trailing service names start only a subset.

Examples:
  ./light_startup.sh
  ./light_startup.sh --watch
  ./light_startup.sh dev backend-flask-service frontend-vue-service nginx-service
  ./light_startup.sh prod
EOF
            exit 0
            ;;
        --*)
            echo "Unknown option: $arg"
            echo "Use --help for usage."
            exit 1
            ;;
        *)
            SERVICES+=("$arg")
            ;;
    esac
done

echo "============================================"
echo "LLARS Light Startup"
echo "============================================"
echo "Base directory: $BASE_DIR"

if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "ERROR: .env file not found!"
    echo "Create one first:"
    echo "  cp .env.template.development .env"
    echo ""
    exit 1
fi

echo "Loading environment from: $ENV_FILE"
set -a
source "$ENV_FILE"
set +a

if [ -n "$PROJECT_STATE_ARG" ]; then
    PROJECT_STATE="$PROJECT_STATE_ARG"
else
    PROJECT_STATE="${PROJECT_STATE:-development}"
fi
export PROJECT_STATE

derive_host_and_port_from_url() {
    local url="${PROJECT_URL:-}"
    if [ -z "$url" ]; then
        return 0
    fi

    local without_proto="${url#*://}"
    local hostport="${without_proto%%/*}"
    local derived_host="$hostport"
    local derived_port=""

    if [[ "$hostport" == *:* ]]; then
        derived_host="${hostport%%:*}"
        derived_port="${hostport##*:}"
    fi

    if [ -z "${PROJECT_HOST:-}" ] && [ -n "$derived_host" ]; then
        PROJECT_HOST="$derived_host"
        export PROJECT_HOST
    fi

    if [ -z "${NGINX_EXTERNAL_PORT:-}" ] && [[ "$derived_port" =~ ^[0-9]+$ ]]; then
        NGINX_EXTERNAL_PORT="$derived_port"
        export NGINX_EXTERNAL_PORT
    fi
}

derive_host_and_port_from_url

PROJECT_HOST="${PROJECT_HOST:-localhost}"
NGINX_EXTERNAL_PORT="${NGINX_EXTERNAL_PORT:-55080}"
AUTHENTIK_EXTERNAL_PORT="${AUTHENTIK_EXTERNAL_PORT:-55095}"
DB_EXTERNAL_PORT="${DB_EXTERNAL_PORT:-55306}"
MKDOCS_EXTERNAL_PORT="${MKDOCS_EXTERNAL_PORT:-55800}"

export PROJECT_HOST NGINX_EXTERNAL_PORT AUTHENTIK_EXTERNAL_PORT DB_EXTERNAL_PORT MKDOCS_EXTERNAL_PORT

if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon is not running. Start Docker and retry."
    exit 1
fi

configure_docker_socket_gid() {
    local docker_sock="/var/run/docker.sock"

    if [ ! -S "$docker_sock" ]; then
        return 0
    fi

    if [ -n "${DOCKER_SOCK_GID:-}" ]; then
        return 0
    fi

    local docker_os=""
    docker_os="$(docker info --format '{{.OperatingSystem}}' 2>/dev/null || true)"
    if [[ "$docker_os" == *"Docker Desktop"* ]]; then
        export DOCKER_SOCK_GID="0"
        return 0
    fi

    local sock_gid=""
    if [ "$(uname)" = "Darwin" ]; then
        sock_gid="$(stat -L -f '%g' "$docker_sock" 2>/dev/null || true)"
    else
        sock_gid="$(stat -c '%g' "$docker_sock" 2>/dev/null || true)"
    fi

    if [ -n "$sock_gid" ]; then
        export DOCKER_SOCK_GID="$sock_gid"
    fi
}

configure_docker_socket_gid

COMPOSE_FILES=(-f docker-compose.yml)
if [ "$PROJECT_STATE" = "production" ]; then
    COMPOSE_FILES+=(-f docker-compose.prod.yml)
fi

echo ""
echo "Mode: $PROJECT_STATE"
echo "Fast path: no down, no --build, no pruning."
if [ "${#SERVICES[@]}" -gt 0 ]; then
    echo "Services: ${SERVICES[*]}"
else
    echo "Services: all"
fi
echo ""

if [ "$PROJECT_STATE" = "production" ]; then
    if [ "${#SERVICES[@]}" -gt 0 ]; then
        docker compose "${COMPOSE_FILES[@]}" -p llars up --detach "${SERVICES[@]}"
    else
        docker compose "${COMPOSE_FILES[@]}" -p llars up --detach
    fi
else
    if [ "$WATCH_MODE" = "true" ]; then
        if docker compose up --help 2>/dev/null | grep -q -- "--watch"; then
            if [ "${#SERVICES[@]}" -gt 0 ]; then
                docker compose "${COMPOSE_FILES[@]}" -p llars up --watch "${SERVICES[@]}"
            else
                docker compose "${COMPOSE_FILES[@]}" -p llars up --watch
            fi
        else
            echo "Warning: --watch is not supported by this Docker Compose version. Starting attached mode instead."
            if [ "${#SERVICES[@]}" -gt 0 ]; then
                docker compose "${COMPOSE_FILES[@]}" -p llars up "${SERVICES[@]}"
            else
                docker compose "${COMPOSE_FILES[@]}" -p llars up
            fi
        fi
    elif [ "$DETACH_MODE" = "true" ] || [ "$DETACH_MODE" = "True" ]; then
        if [ "${#SERVICES[@]}" -gt 0 ]; then
            docker compose "${COMPOSE_FILES[@]}" -p llars up --detach "${SERVICES[@]}"
        else
            docker compose "${COMPOSE_FILES[@]}" -p llars up --detach
        fi
    else
        if [ "${#SERVICES[@]}" -gt 0 ]; then
            docker compose "${COMPOSE_FILES[@]}" -p llars up "${SERVICES[@]}"
        else
            docker compose "${COMPOSE_FILES[@]}" -p llars up
        fi
    fi
fi

if [ "$PROJECT_STATE" = "production" ] || [ "$DETACH_MODE" = "true" ] || [ "$DETACH_MODE" = "True" ]; then
    if [ "$PROJECT_STATE" = "production" ]; then
        PUBLIC_BASE_URL="${PROJECT_URL:-https://${PROJECT_HOST}}"
    else
        PUBLIC_BASE_URL="${PROJECT_URL:-http://${PROJECT_HOST}:${NGINX_EXTERNAL_PORT}}"
    fi

    echo ""
    echo "LLARS started (light mode)."
    echo "Frontend:    ${PUBLIC_BASE_URL}"
    echo "Backend API: ${PUBLIC_BASE_URL}/api"
    echo "Authentik:   ${PUBLIC_BASE_URL}/authentik"
    echo "Database:    ${PROJECT_HOST}:${DB_EXTERNAL_PORT}"
    echo "Docs:        ${PUBLIC_BASE_URL}/mkdocs"
    echo ""
    echo "Tip: Use ./start_llars.sh when you need a full rebuild/restart workflow."
fi
