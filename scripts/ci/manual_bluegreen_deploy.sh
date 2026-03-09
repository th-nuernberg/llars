#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
MODE="${1:-help}"

cd "$DEPLOY_PATH"

run_staging_smoke() {
  local admin_api_key
  admin_api_key="$(grep '^SYSTEM_ADMIN_API_KEY=' .env | cut -d= -f2- || true)"
  BASE_URL="${BASE_URL:-http://localhost:55080}" SYSTEM_ADMIN_API_KEY="$admin_api_key" \
    bash scripts/ci/smoke_test.sh
}

run_staging_e2e() {
  local e2e_password
  e2e_password="$(grep '^LLARS_ADMIN_PASSWORD=' .env | cut -d= -f2- || echo "admin123")"
  local e2e_run_tag="${E2E_RUN_TAG:-Manual Test}"
  local e2e_admin_user="${E2E_ADMIN_USER:-test_admin}"
  local e2e_researcher_user="${E2E_RESEARCHER_USER:-test_researcher}"
  local e2e_evaluator_user="${E2E_EVALUATOR_USER:-test_evaluator}"
  local e2e_only="${E2E_ONLY:-}"
  docker compose --profile testing build smoke-test-service
  docker compose --profile testing run --rm --entrypoint "" \
    -e PLAYWRIGHT_BASE_URL="${PLAYWRIGHT_BASE_URL:-http://localhost:55080}" \
    -e E2E_TEST_PASSWORD="$e2e_password" \
    -e E2E_RUN_TAG="$e2e_run_tag" \
    -e E2E_ADMIN_USER="$e2e_admin_user" \
    -e E2E_RESEARCHER_USER="$e2e_researcher_user" \
    -e E2E_EVALUATOR_USER="$e2e_evaluator_user" \
    -e E2E_ONLY="$e2e_only" \
    -e NODE_TLS_REJECT_UNAUTHORIZED=0 \
    smoke-test-service \
    bash -c "cd /tests/e2e && npx playwright test --project=chromium --workers=1"
}

usage() {
  cat <<'EOF'
Manual LLARS Blue-Green Deploy

Usage:
  manual_bluegreen_deploy.sh prepare
  manual_bluegreen_deploy.sh test
  manual_bluegreen_deploy.sh switch
  manual_bluegreen_deploy.sh full
  manual_bluegreen_deploy.sh status

Commands:
  prepare  Build/start inactive color and expose it on staging (:55080)
  test     Run staging smoke tests (set RUN_E2E=1 for full Playwright suite)
  switch   Switch production nginx to the prepared candidate
  full     prepare + test (+ optional E2E) + switch
  status   Show current blue-green state

Optional env for RUN_E2E=1:
  E2E_RUN_TAG             Default: "Manual Test"
  E2E_ADMIN_USER          Default: test_admin
  E2E_RESEARCHER_USER     Default: test_researcher
  E2E_EVALUATOR_USER      Default: test_evaluator
  E2E_ONLY                Run single spec or grep pattern
EOF
}

case "$MODE" in
  prepare)
    bash scripts/ci/deploy_bluegreen.sh deploy
    ;;
  test)
    run_staging_smoke
    if [ "${RUN_E2E:-0}" = "1" ]; then
      run_staging_e2e
    fi
    ;;
  switch)
    bash scripts/ci/deploy_bluegreen.sh switch
    ;;
  full)
    bash scripts/ci/deploy_bluegreen.sh deploy
    run_staging_smoke
    if [ "${RUN_E2E:-0}" = "1" ]; then
      run_staging_e2e
    fi
    bash scripts/ci/deploy_bluegreen.sh switch
    ;;
  status)
    bash scripts/ci/deploy_bluegreen.sh status
    ;;
  *)
    usage
    exit 1
    ;;
esac
