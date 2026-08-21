#!/usr/bin/env bash
set -euo pipefail

EVENT_TYPE="${1:-ci_cd.pipeline}"
MESSAGE="${2:-CI/CD event}"
SEVERITY="${3:-ci_cd}"
BASE_URL="${CI_EVENT_BASE_URL:-http://localhost:55080}"
TAG="${E2E_RUN_TAG:-Nightly Test}"

DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
ENV_FILE="${DEPLOY_PATH}/.env"
if [ -f "$ENV_FILE" ] && [ -z "${SYSTEM_ADMIN_API_KEY:-}" ]; then
  SYSTEM_ADMIN_API_KEY=$(grep '^SYSTEM_ADMIN_API_KEY=' "$ENV_FILE" | cut -d= -f2- || true)
fi

if [ -z "${SYSTEM_ADMIN_API_KEY:-}" ]; then
  echo "log_ci_event: SYSTEM_ADMIN_API_KEY missing, skipping"
  exit 0
fi

DETAILS=$(cat <<JSON
{
  "pipeline_id": "${CI_PIPELINE_ID:-}",
  "job_id": "${CI_JOB_ID:-}",
  "job_name": "${CI_JOB_NAME:-}",
  "commit": "${CI_COMMIT_SHA:-}",
  "branch": "${CI_COMMIT_REF_NAME:-}",
  "tag": "${TAG}",
  "source": "${CI_PIPELINE_SOURCE:-}"
}
JSON
)

PAYLOAD=$(cat <<JSON
{
  "event_type": "${EVENT_TYPE}",
  "message": "${MESSAGE}",
  "severity": "${SEVERITY}",
  "username": "gitlab-ci",
  "entity_type": "pipeline",
  "entity_id": "${CI_PIPELINE_ID:-}",
  "details": ${DETAILS}
}
JSON
)

curl -sS -L --max-time 10 \
  -H "X-API-Key: ${SYSTEM_ADMIN_API_KEY}" \
  -H "X-Forwarded-Proto: https" \
  -H "Content-Type: application/json" \
  -X POST "${BASE_URL}/api/admin/system/events/ci-cd" \
  -d "${PAYLOAD}" >/dev/null || true

echo "log_ci_event: ${EVENT_TYPE} -> ${BASE_URL}"
