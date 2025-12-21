#!/bin/bash
# ============================================
# LLARS Startup Script
# ============================================
# Starts LLARS based on PROJECT_STATE in .env
#
# USAGE:
#   ./start_llars.sh              # Uses .env
#   ./start_llars.sh dev          # Force development mode
#   ./start_llars.sh prod         # Force production mode
#
# SETUP:
#   cp .env.template.development .env   # For development
#   cp .env.template.production .env    # For production
# ============================================

set -e

# Script directory
SCRIPT_DIR=$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]:-${(%):-%x}}")")" && pwd)
BASE_DIR="$SCRIPT_DIR"

echo "============================================"
echo "LLARS Startup Script"
echo "============================================"
echo "Base directory: $BASE_DIR"

# ============================================
# Step 1: Load .env file
# ============================================

ENV_FILE="$BASE_DIR/.env"

# Allow one-shot overrides via environment variables, even when .env defines defaults.
REMOVE_LLARS_VOLUMES_OVERRIDE="${REMOVE_LLARS_VOLUMES:-}"
PRUNE_LLARS_SYSTEM_OVERRIDE="${PRUNE_LLARS_SYSTEM:-}"
REMOVE_VOLUMES_OVERRIDE="${REMOVE_VOLUMES:-}"

if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "ERROR: .env file not found!"
    echo ""
    echo "Please create .env from a template:"
    echo ""
    echo "  For DEVELOPMENT:"
    echo "    cp .env.template.development .env"
    echo ""
    echo "  For PRODUCTION:"
    echo "    cp .env.template.production .env"
    echo "    # Then edit .env with your production secrets!"
    echo ""
    exit 1
fi

echo "Loading environment from: $ENV_FILE"
set -a  # Export all variables
source "$ENV_FILE"
set +a

# Re-apply environment override after sourcing .env (prevents accidental permanent REMOVE_* in .env)
if [ -z "$REMOVE_LLARS_VOLUMES_OVERRIDE" ] && [ -n "$REMOVE_VOLUMES_OVERRIDE" ]; then
    REMOVE_LLARS_VOLUMES_OVERRIDE="$REMOVE_VOLUMES_OVERRIDE"
fi

if [ -n "$REMOVE_LLARS_VOLUMES_OVERRIDE" ]; then
    REMOVE_LLARS_VOLUMES="$REMOVE_LLARS_VOLUMES_OVERRIDE"
    export REMOVE_LLARS_VOLUMES
fi

if [ -n "$PRUNE_LLARS_SYSTEM_OVERRIDE" ]; then
    PRUNE_LLARS_SYSTEM="$PRUNE_LLARS_SYSTEM_OVERRIDE"
    export PRUNE_LLARS_SYSTEM
fi

if [ -z "${REMOVE_LLARS_VOLUMES:-}" ] && [ -n "${REMOVE_VOLUMES:-}" ]; then
    REMOVE_LLARS_VOLUMES="$REMOVE_VOLUMES"
    export REMOVE_LLARS_VOLUMES
fi

# ============================================
# Step 2: Override PROJECT_STATE if argument given
# ============================================

PROJECT_STATE_ARG="${1:-}"
DETACH_MODE="${LLARS_DETACH:-false}"

for arg in "$@"; do
    if [ "$arg" = "--detach" ] || [ "$arg" = "--detached" ]; then
        DETACH_MODE=true
    fi
done

if [ "$PROJECT_STATE_ARG" = "prod" ] || [ "$PROJECT_STATE_ARG" = "production" ]; then
    PROJECT_STATE="production"
    echo "Mode: PRODUCTION (override via command line)"
elif [ "$PROJECT_STATE_ARG" = "dev" ] || [ "$PROJECT_STATE_ARG" = "development" ]; then
    PROJECT_STATE="development"
    echo "Mode: DEVELOPMENT (override via command line)"
else
    echo "Mode: ${PROJECT_STATE:-development} (from .env)"
    PROJECT_STATE="${PROJECT_STATE:-development}"
fi

export PROJECT_STATE

# ============================================
# Step 2b: Apply sane defaults (thin .env)
# ============================================

# If PROJECT_URL is provided, derive PROJECT_HOST and NGINX_EXTERNAL_PORT (for status output)
derive_host_and_port_from_url() {
    local url="${PROJECT_URL:-}"
    if [ -z "$url" ]; then
        return 0
    fi

    # Strip protocol
    local without_proto="${url#*://}"
    local hostport="${without_proto%%/*}"

    # Basic host:port split (IPv6 not supported here; use PROJECT_HOST/NGINX_EXTERNAL_PORT explicitly in that case)
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

# Defaults consistent with docker-compose.yml
PROJECT_HOST="${PROJECT_HOST:-localhost}"
NGINX_EXTERNAL_PORT="${NGINX_EXTERNAL_PORT:-55080}"
AUTHENTIK_EXTERNAL_PORT="${AUTHENTIK_EXTERNAL_PORT:-55095}"
DB_EXTERNAL_PORT="${DB_EXTERNAL_PORT:-55306}"
MKDOCS_EXTERNAL_PORT="${MKDOCS_EXTERNAL_PORT:-55800}"

export PROJECT_HOST NGINX_EXTERNAL_PORT AUTHENTIK_EXTERNAL_PORT DB_EXTERNAL_PORT MKDOCS_EXTERNAL_PORT

# ============================================
# Step 3: Check Docker Daemon
# ============================================

MAX_ATTEMPTS=10
SLEEP_DURATION=5

get_os_type() {
    OS_TYPE=$(uname)
    case "$OS_TYPE" in
        Darwin)
            echo "OS: MacOS"
            ;;
        Linux)
            echo "OS: Linux"
            ;;
        *_NT-*)
            echo "OS: Windows"
            ;;
        *)
            echo "Unsupported OS: $OS_TYPE"
            exit 1
            ;;
    esac
}

check_and_start_docker() {
    get_os_type
    if ! docker info >/dev/null 2>&1; then
        echo "Docker daemon not running. Attempting to start..."

        OS_TYPE=$(uname)
        case "$OS_TYPE" in
            Darwin)
                open /Applications/Docker.app
                ;;
            Linux)
                sudo systemctl start docker
                ;;
            *_NT-*)
                echo "Docker not running. Please start Docker manually!"
                exit 1
                ;;
            *)
                echo "Unsupported OS: $OS_TYPE"
                exit 1
                ;;
        esac

        for ((i=1; i<=MAX_ATTEMPTS; i++)); do
            sleep $SLEEP_DURATION
            if docker info >/dev/null 2>&1; then
                echo "Docker daemon started successfully."
                return 0
            fi
        done

        echo "Failed to start Docker daemon. Please check manually."
        exit 1
    else
        echo "Docker daemon is running."
    fi
}

check_and_start_docker

# ============================================
# Step 3b: Docker Socket Access (Admin Docker Monitor)
# ============================================
#
# The Admin Docker Monitor reads container stats + logs via /var/run/docker.sock.
# On Docker Desktop (macOS), the socket is usually owned by the host user and may
# not be group-writable. We try to make it group-writable (when allowed) and
# export DOCKER_SOCK_GID so docker-compose can add the matching group.
#

configure_docker_socket_access() {
    DOCKER_SOCK="/var/run/docker.sock"

    if [ ! -S "$DOCKER_SOCK" ]; then
        echo "Docker socket not found at $DOCKER_SOCK (Docker Monitor disabled)."
        return 0
    fi

    # Docker Desktop remaps docker.sock ownership into containers as root:root (gid 0),
    # even if the host path is a user-owned proxy socket. In that case we must add
    # group 0 to the backend container to enable the Docker Monitor.
    local docker_os=""
    docker_os=$(docker info --format '{{.OperatingSystem}}' 2>/dev/null || echo "")
    if [[ "$docker_os" == *"Docker Desktop"* ]]; then
        if [ -n "${DOCKER_SOCK_GID:-}" ] && [ "$DOCKER_SOCK_GID" != "0" ]; then
            echo "Warning: DOCKER_SOCK_GID override ($DOCKER_SOCK_GID) ignored on Docker Desktop; using 0."
        fi
        export DOCKER_SOCK_GID="0"
        echo "Docker Desktop detected → using DOCKER_SOCK_GID=$DOCKER_SOCK_GID for Docker Monitor access."
        return 0
    fi

    # Respect explicit overrides (e.g. in .env or exported env vars)
    if [ -n "${DOCKER_SOCK_GID:-}" ]; then
        echo "Docker socket group id override detected: DOCKER_SOCK_GID=$DOCKER_SOCK_GID"
        return 0
    fi

    OS_TYPE=$(uname)
    local sock_uid=""
    local sock_gid=""
    local sock_mode=""

    if [ "$OS_TYPE" = "Darwin" ]; then
        sock_uid=$(stat -L -f '%u' "$DOCKER_SOCK" 2>/dev/null || echo "")
        sock_gid=$(stat -L -f '%g' "$DOCKER_SOCK" 2>/dev/null || echo "")
        sock_mode=$(stat -L -f '%OLp' "$DOCKER_SOCK" 2>/dev/null || echo "")
    else
        sock_uid=$(stat -c '%u' "$DOCKER_SOCK" 2>/dev/null || echo "")
        sock_gid=$(stat -c '%g' "$DOCKER_SOCK" 2>/dev/null || echo "")
        sock_mode=$(stat -c '%a' "$DOCKER_SOCK" 2>/dev/null || echo "")
    fi

    if [ -n "$sock_gid" ]; then
        export DOCKER_SOCK_GID="$sock_gid"
        echo "Docker socket group id: $DOCKER_SOCK_GID"
    else
        echo "Warning: Could not determine docker.sock group id."
    fi

    # Try to ensure group-writable permissions (only if we own the socket or are root)
    if [ -n "$sock_mode" ]; then
        # Bash arithmetic with base-8 conversion
        local mode_dec=$((8#$sock_mode))
        local group_write=$((mode_dec & 020))
        if [ "$group_write" -eq 0 ]; then
            local current_uid
            current_uid=$(id -u)
            if [ -n "$sock_uid" ] && { [ "$current_uid" -eq 0 ] || [ "$current_uid" -eq "$sock_uid" ]; }; then
                echo "docker.sock is not group-writable (mode $sock_mode) → applying chmod g+w..."
                chmod g+w "$DOCKER_SOCK" 2>/dev/null || true
            else
                echo "Warning: docker.sock not group-writable (mode $sock_mode)."
                echo "         Docker Monitor may not work unless group write is enabled."
            fi
        fi
    fi
}

configure_docker_socket_access

# ============================================
# Step 4: Stop existing services
# ============================================

cd "$BASE_DIR"
# ============================================
# Step 5: Handle PRUNE_LLARS_SYSTEM / REMOVE_LLARS_VOLUMES
# ============================================

if [ "$PRUNE_LLARS_SYSTEM" = "True" ] || [ "$PRUNE_LLARS_SYSTEM" = "true" ]; then
    echo ""
    echo "============================================"
    echo "WARNING: PRUNE_LLARS_SYSTEM=True detected!"
    echo "============================================"
    echo "This will DELETE ALL LLARS CONTAINERS, IMAGES, VOLUMES and BUILD CACHE:"
    echo "  - Containers (all llars_* containers)"
    echo "  - Local images built by LLARS"
    echo "  - Volumes used by LLARS"
    echo "  - LLARS build cache"
    echo ""

    # Safety check in development when PRUNE_LLARS_SYSTEM comes from .env
    if [ "$PROJECT_STATE" != "production" ] && [ -z "$PRUNE_LLARS_SYSTEM_OVERRIDE" ]; then
        echo "PRUNE_LLARS_SYSTEM is set in .env. This is dangerous and will wipe everything on every start."
        echo "Type 'yes' to continue (or set PRUNE_LLARS_SYSTEM=False in .env):"
        read -r confirm
        if [ "$confirm" != "yes" ]; then
            echo "Aborted. Set PRUNE_LLARS_SYSTEM=False in .env"
            exit 1
        fi
    fi

    # Safety check in production
    if [ "$PROJECT_STATE" = "production" ]; then
        echo "PRODUCTION MODE DETECTED!"
        echo "Are you ABSOLUTELY SURE you want to delete all LLARS system resources? (yes/no)"
        read -r confirm
        if [ "$confirm" != "yes" ]; then
            echo "Aborted. Set PRUNE_LLARS_SYSTEM=False in .env"
            exit 1
        fi
    fi

    echo "Stopping and removing LLARS services with volumes and local images..."
    docker compose -p llars down --volumes --remove-orphans --rmi local 2>/dev/null || true

    echo "Removing any remaining LLARS containers..."
    LLARS_CONTAINERS=$( { docker ps -aq --filter label=com.docker.compose.project=llars 2>/dev/null; docker ps -aq --filter name=llars_ 2>/dev/null; } | sort -u )
    if [ -n "$LLARS_CONTAINERS" ]; then
        for cid in $LLARS_CONTAINERS; do
            echo "  Deleting container: $cid"
            docker rm -f "$cid" 2>/dev/null || echo "  Warning: Could not delete $cid"
        done
    else
        echo "No additional LLARS containers found."
    fi

    echo "Removing ALL LLARS volumes..."
    LLARS_VOLUMES=$(docker volume ls -q --filter name=llars 2>/dev/null || true)

    if [ -n "$LLARS_VOLUMES" ]; then
        for volume in $LLARS_VOLUMES; do
            echo "  Deleting volume: $volume"
            docker volume rm "$volume" 2>/dev/null || echo "  Warning: Could not delete $volume"
        done
        echo ""
        echo "All LLARS volumes removed."
    else
        echo "No additional LLARS volumes found."
    fi

    echo "Removing ALL LLARS images..."
    LLARS_IMAGES=$( { \
        docker image ls -q --filter label=com.docker.compose.project=llars 2>/dev/null; \
        docker image ls -q --filter reference='llars-*' 2>/dev/null; \
        docker image ls -q --filter reference='llars_*' 2>/dev/null; \
    } | sort -u )
    if [ -n "$LLARS_IMAGES" ]; then
        for image in $LLARS_IMAGES; do
            echo "  Deleting image: $image"
            docker image rm -f "$image" 2>/dev/null || echo "  Warning: Could not delete $image"
        done
        echo ""
        echo "All LLARS images removed."
    else
        echo "No additional LLARS images found."
    fi

    echo "Pruning LLARS build cache..."
    docker builder prune -f --filter "label=com.docker.compose.project=llars" 2>/dev/null || true

    # Safety: reset PRUNE_LLARS_SYSTEM in .env so the next run doesn't prune again.
    if [ -z "$PRUNE_LLARS_SYSTEM_OVERRIDE" ] && [ -w "$ENV_FILE" ]; then
        if grep -qE '^PRUNE_LLARS_SYSTEM=' "$ENV_FILE"; then
            perl -pi -e 's/^PRUNE_LLARS_SYSTEM=.*/PRUNE_LLARS_SYSTEM=False/' "$ENV_FILE" 2>/dev/null || true
        else
            echo "PRUNE_LLARS_SYSTEM=False" >> "$ENV_FILE" 2>/dev/null || true
        fi
        echo "Safety: RESET PRUNE_LLARS_SYSTEM=False in .env"
    fi

    echo "============================================"
    echo ""
elif [ "$REMOVE_LLARS_VOLUMES" = "True" ] || [ "$REMOVE_LLARS_VOLUMES" = "true" ]; then
    echo ""
    echo "============================================"
    echo "WARNING: REMOVE_LLARS_VOLUMES=True detected!"
    echo "============================================"
    echo "This will DELETE ALL LLARS DATA including:"
    echo "  - Database (users, ratings, scenarios)"
    echo "  - RAG Collections and Documents"
    echo "  - Authentik (all user accounts)"
    echo "  - Model cache and embeddings"
    echo ""

    # Safety check in development when REMOVE_LLARS_VOLUMES comes from .env (prevents accidental repeated wipes)
    if [ "$PROJECT_STATE" != "production" ] && [ -z "$REMOVE_LLARS_VOLUMES_OVERRIDE" ]; then
        echo "REMOVE_LLARS_VOLUMES is set in .env. This is dangerous and will wipe data on every start."
        echo "Type 'yes' to continue (or set REMOVE_LLARS_VOLUMES=False in .env):"
        read -r confirm
        if [ "$confirm" != "yes" ]; then
            echo "Aborted. Set REMOVE_LLARS_VOLUMES=False in .env"
            exit 1
        fi
    fi

    # Safety check in production
    if [ "$PROJECT_STATE" = "production" ]; then
        echo "PRODUCTION MODE DETECTED!"
        echo "Are you ABSOLUTELY SURE you want to delete all data? (yes/no)"
        read -r confirm
        if [ "$confirm" != "yes" ]; then
            echo "Aborted. Set REMOVE_LLARS_VOLUMES=False in .env"
            exit 1
        fi
    fi

    # Stop and remove containers WITH volumes
    echo "Stopping and removing LLARS services with volumes..."
    docker compose -p llars down --volumes --remove-orphans 2>/dev/null || true

    # Also remove any remaining volumes with llars prefix
    echo "Removing ALL LLARS volumes..."
    LLARS_VOLUMES=$(docker volume ls -q --filter name=llars 2>/dev/null || true)

    if [ -n "$LLARS_VOLUMES" ]; then
        for volume in $LLARS_VOLUMES; do
            echo "  Deleting: $volume"
            docker volume rm "$volume" 2>/dev/null || echo "  Warning: Could not delete $volume"
        done
        echo ""
        echo "All LLARS volumes removed."
    else
        echo "No additional LLARS volumes found."
    fi

    # Safety: reset REMOVE_LLARS_VOLUMES in .env so the next run doesn't wipe data again.
    # Recommended usage is one-shot: `REMOVE_LLARS_VOLUMES=True ./start_llars.sh`
    if [ -z "$REMOVE_LLARS_VOLUMES_OVERRIDE" ] && [ -w "$ENV_FILE" ]; then
        if grep -qE '^REMOVE_LLARS_VOLUMES=' "$ENV_FILE"; then
            perl -pi -e 's/^REMOVE_LLARS_VOLUMES=.*/REMOVE_LLARS_VOLUMES=False/' "$ENV_FILE" 2>/dev/null || true
        else
            echo "REMOVE_LLARS_VOLUMES=False" >> "$ENV_FILE" 2>/dev/null || true
        fi
        echo "Safety: RESET REMOVE_LLARS_VOLUMES=False in .env"
    fi

    echo "============================================"
    echo ""
else
    # Normal stop without removing volumes
    echo ""
    echo "Stopping existing LLARS services..."
    docker compose -p llars down --remove-orphans 2>/dev/null || true
fi

# ============================================
# Step 6: Start Docker Compose
# ============================================

cd "$BASE_DIR"

if [ "$PROJECT_STATE" = "production" ]; then
    echo ""
    echo "============================================"
    echo "Starting LLARS in PRODUCTION MODE"
    echo "============================================"
    echo "Using: docker-compose.yml + docker-compose.prod.yml"
    echo ""

    docker compose \
        -f docker-compose.yml \
        -f docker-compose.prod.yml \
        -p llars \
        up --build --detach

    echo ""
    echo "LLARS started in PRODUCTION mode"
    echo ""
    echo "Access points:"
    echo "  - Frontend:    https://${PROJECT_HOST}"
    echo "  - Backend API: https://${PROJECT_HOST}/api"
    echo "  - Authentik:   https://${PROJECT_HOST}/authentik"
    echo "  - Matomo:      https://${PROJECT_HOST}/analytics/ (UI)"
    echo ""
    echo "View logs:"
    echo "  docker compose -p llars logs -f"
    echo "============================================"

else
    echo ""
    echo "============================================"
    echo "Starting LLARS in DEVELOPMENT MODE"
    echo "============================================"
    if [ "$DETACH_MODE" = "true" ] || [ "$DETACH_MODE" = "True" ]; then
        echo "Using: docker-compose.yml (detached)"
    else
        echo "Using: docker-compose.yml (with --watch for hot-reload)"
    fi
    echo ""

    if [ "$DETACH_MODE" = "true" ] || [ "$DETACH_MODE" = "True" ]; then
        docker compose \
            -f docker-compose.yml \
            -p llars \
            up --build --detach
    else
        docker compose \
            -f docker-compose.yml \
            -p llars \
            up --build --watch
    fi

    echo ""
    echo "LLARS started in DEVELOPMENT mode"
    echo ""
    echo "Access points:"
    echo "  - Frontend:    http://${PROJECT_HOST}:${NGINX_EXTERNAL_PORT}"
    echo "  - Backend API: http://${PROJECT_HOST}:${NGINX_EXTERNAL_PORT}/api"
    echo "  - Authentik:   http://${PROJECT_HOST}:${AUTHENTIK_EXTERNAL_PORT}"
    echo "  - Matomo:      http://${PROJECT_HOST}:${NGINX_EXTERNAL_PORT}/analytics/ (UI)"
    echo "  - Database:    ${PROJECT_HOST}:${DB_EXTERNAL_PORT}"
    echo "  - Docs:        http://${PROJECT_HOST}:${MKDOCS_EXTERNAL_PORT}"
    echo ""
    echo "============================================"
fi
