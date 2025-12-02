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

# ============================================
# Step 2: Override PROJECT_STATE if argument given
# ============================================

PROJECT_STATE_ARG="${1:-}"

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
# Step 4: Stop existing services
# ============================================

cd "$BASE_DIR"
# ============================================
# Step 5: Handle REMOVE_VOLUMES
# ============================================

if [ "$REMOVE_VOLUMES" = "True" ] || [ "$REMOVE_VOLUMES" = "true" ]; then
    echo ""
    echo "============================================"
    echo "WARNING: REMOVE_VOLUMES=True detected!"
    echo "============================================"
    echo "This will DELETE ALL LLARS DATA including:"
    echo "  - Database (users, ratings, scenarios)"
    echo "  - RAG Collections and Documents"
    echo "  - Authentik (all user accounts)"
    echo "  - Model cache and embeddings"
    echo ""

    # Safety check in production
    if [ "$PROJECT_STATE" = "production" ]; then
        echo "PRODUCTION MODE DETECTED!"
        echo "Are you ABSOLUTELY SURE you want to delete all data? (yes/no)"
        read -r confirm
        if [ "$confirm" != "yes" ]; then
            echo "Aborted. Set REMOVE_VOLUMES=False in .env"
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
    echo ""
    echo "View logs:"
    echo "  docker compose -p llars logs -f"
    echo "============================================"

else
    echo ""
    echo "============================================"
    echo "Starting LLARS in DEVELOPMENT MODE"
    echo "============================================"
    echo "Using: docker-compose.yml (with --watch for hot-reload)"
    echo ""

    docker compose \
        -f docker-compose.yml \
        -p llars \
        up --build --watch

    echo ""
    echo "LLARS started in DEVELOPMENT mode"
    echo ""
    echo "Access points:"
    echo "  - Frontend:    http://${PROJECT_HOST}:${NGINX_EXTERNAL_PORT}"
    echo "  - Backend API: http://${PROJECT_HOST}:${NGINX_EXTERNAL_PORT}/api"
    echo "  - Authentik:   http://${PROJECT_HOST}:${AUTHENTIK_EXTERNAL_PORT}"
    echo "  - Database:    ${PROJECT_HOST}:${DB_EXTERNAL_PORT}"
    echo "  - Docs:        http://${PROJECT_HOST}:${MKDOCS_EXTERNAL_PORT}"
    echo ""
    echo "============================================"
fi
