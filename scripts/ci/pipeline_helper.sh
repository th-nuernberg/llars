#!/usr/bin/env bash
set -euo pipefail

GITLAB_API_BASE="${GITLAB_API_BASE:-https://git.informatik.fh-nuernberg.de/api/v4}"
ENV_FILE="${ENV_FILE:-.env}"
BRANCH="${BRANCH:-main}"

# Load credentials from .env
if [ -f "$ENV_FILE" ]; then
  while IFS='=' read -r key value; do
    case "$key" in
      GITLAB_TOKEN|GITLAB_PROJECT_ID)
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        value="${value%$'\r'}"
        export "$key=$value"
        ;;
    esac
  done < <(grep -E '^(GITLAB_TOKEN|GITLAB_PROJECT_ID)=' "$ENV_FILE" || true)
fi

if [ -z "${GITLAB_TOKEN:-}" ] || [ -z "${GITLAB_PROJECT_ID:-}" ]; then
  echo "ERROR: GITLAB_TOKEN or GITLAB_PROJECT_ID not set (check .env)"
  exit 1
fi

API="$GITLAB_API_BASE/projects/$GITLAB_PROJECT_ID"

api_get() {
  curl -sS --fail --max-time 20 --connect-timeout 5 \
    --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$1"
}

api_post() {
  curl -sS --fail --max-time 20 --connect-timeout 5 \
    --request POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$1"
}

# --- Commands ---

cmd_status() {
  local pipeline_id="${1:-}"

  if [ -z "$pipeline_id" ]; then
    # Try running first, then latest
    pipeline_id=$(api_get "$API/pipelines?ref=$BRANCH&status=running&per_page=1" \
      | python3 -c "import sys,json; p=json.load(sys.stdin); print(p[0]['id'] if p else '')" 2>/dev/null)
    if [ -z "$pipeline_id" ]; then
      pipeline_id=$(api_get "$API/pipelines?ref=$BRANCH&per_page=1" \
        | python3 -c "import sys,json; p=json.load(sys.stdin); print(p[0]['id'] if p else '')")
    fi
  fi

  if [ -z "$pipeline_id" ]; then
    echo "No pipeline found for branch=$BRANCH"
    return 1
  fi

  # Get pipeline info
  local pipeline_info
  pipeline_info=$(api_get "$API/pipelines/$pipeline_id")
  local status ref created
  status=$(echo "$pipeline_info" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  ref=$(echo "$pipeline_info" | python3 -c "import sys,json; print(json.load(sys.stdin)['ref'])")
  created=$(echo "$pipeline_info" | python3 -c "import sys,json; print(json.load(sys.stdin)['created_at'][:16])")

  echo "Pipeline #$pipeline_id | $status | $ref | $created"
  echo "---"

  # Get jobs
  api_get "$API/pipelines/$pipeline_id/jobs?per_page=50" | python3 -c "
import sys, json
jobs = json.load(sys.stdin)
jobs.sort(key=lambda j: j['id'])
icons = {'success':'\u2713','failed':'\u2717','running':'\u27f3','pending':'\u25cb','created':'\u00b7','canceled':'\u2715','manual':'\u25b7','skipped':'\u2192'}
for j in jobs:
    icon = icons.get(j['status'], '?')
    dur = ''
    if j.get('duration'):
        dur = f\" ({j['duration']:.0f}s)\"
    print(f\"  {icon} {j['name']:30s} | {j['status']:10s} | ID: {j['id']}{dur}\")
"
}

cmd_jobs() {
  # Show only failed jobs with last 30 lines of log
  local pipeline_id="${1:-}"

  if [ -z "$pipeline_id" ]; then
    pipeline_id=$(api_get "$API/pipelines?ref=$BRANCH&per_page=1" \
      | python3 -c "import sys,json; p=json.load(sys.stdin); print(p[0]['id'] if p else '')")
  fi

  local failed_jobs
  failed_jobs=$(api_get "$API/pipelines/$pipeline_id/jobs?per_page=50" | python3 -c "
import sys, json
jobs = json.load(sys.stdin)
failed = [j for j in jobs if j['status'] == 'failed']
for j in failed:
    print(f\"{j['id']}|{j['name']}\")
")

  if [ -z "$failed_jobs" ]; then
    echo "No failed jobs in pipeline #$pipeline_id"
    return 0
  fi

  while IFS='|' read -r job_id job_name; do
    [ -z "$job_id" ] && continue
    echo "=== FAILED: $job_name (ID: $job_id) ==="
    api_get "$API/jobs/$job_id/trace" | tail -30
    echo ""
  done <<< "$failed_jobs"
}

cmd_log() {
  local job_id="${1:-}"
  local lines="${2:-50}"

  if [ -z "$job_id" ]; then
    echo "Usage: $0 log <job_id> [lines]"
    return 1
  fi

  api_get "$API/jobs/$job_id/trace" | tail -"$lines"
}

cmd_retry() {
  local job_id="${1:-}"

  if [ -z "$job_id" ]; then
    echo "Usage: $0 retry <job_id>"
    return 1
  fi

  echo "Retrying job $job_id..."
  api_post "$API/jobs/$job_id/retry" | python3 -c "
import sys, json
j = json.load(sys.stdin)
print(f\"Job '{j['name']}' restarted -> status: {j['status']} (ID: {j['id']})\")
"
}

cmd_cancel_all() {
  echo "Canceling running/pending pipelines on $BRANCH..."
  local pipelines
  pipelines=$(api_get "$API/pipelines?ref=$BRANCH&status=running&per_page=10")
  local pending
  pending=$(api_get "$API/pipelines?ref=$BRANCH&status=pending&per_page=10")

  # Merge and cancel
  python3 -c "
import sys, json
running = json.loads('''$pipelines''')
pending = json.loads('''$pending''')
all_ids = [p['id'] for p in running + pending]
for pid in all_ids:
    print(pid)
" | while read -r pid; do
    echo "  Canceling pipeline #$pid..."
    api_post "$API/pipelines/$pid/cancel" > /dev/null 2>&1 || true
  done
  echo "Done."
}

cmd_deploy() {
  echo "Triggering pipeline with FORCE_DEPLOY=true on $BRANCH..."
  curl -sS --fail --max-time 20 --connect-timeout 5 \
    --request POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    --form "ref=$BRANCH" \
    --form "variables[FORCE_DEPLOY]=true" \
    "$API/pipeline" | python3 -c "
import sys, json
p = json.load(sys.stdin)
print(f\"Pipeline #{p['id']} created (status: {p['status']})\")
"
}

cmd_trigger() {
  echo "Triggering pipeline on $BRANCH..."
  api_post "$API/pipeline?ref=$BRANCH" | python3 -c "
import sys, json
p = json.load(sys.stdin)
print(f\"Pipeline #{p['id']} created (status: {p['status']})\")
"
}

cmd_watch() {
  local pipeline_id="${1:-}"
  local interval="${2:-30}"

  if [ -z "$pipeline_id" ]; then
    pipeline_id=$(api_get "$API/pipelines?ref=$BRANCH&per_page=1" \
      | python3 -c "import sys,json; p=json.load(sys.stdin); print(p[0]['id'] if p else '')")
  fi

  echo "Watching pipeline #$pipeline_id (every ${interval}s, Ctrl+C to stop)..."
  while true; do
    clear
    echo "[$(date +%H:%M:%S)] Pipeline #$pipeline_id"
    echo "---"
    api_get "$API/pipelines/$pipeline_id/jobs?per_page=50" | python3 -c "
import sys, json
jobs = json.load(sys.stdin)
jobs.sort(key=lambda j: j['id'])
icons = {'success':'\u2713','failed':'\u2717','running':'\u27f3','pending':'\u25cb','created':'\u00b7','canceled':'\u2715','manual':'\u25b7','skipped':'\u2192'}
for j in jobs:
    icon = icons.get(j['status'], '?')
    dur = ''
    if j.get('duration'):
        dur = f\" ({j['duration']:.0f}s)\"
    print(f\"  {icon} {j['name']:30s} | {j['status']:10s}{dur}\")
"
    # Check if pipeline is done
    local pstatus
    pstatus=$(api_get "$API/pipelines/$pipeline_id" \
      | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
    if [[ "$pstatus" =~ ^(success|failed|canceled)$ ]]; then
      echo ""
      echo "Pipeline finished: $pstatus"
      break
    fi
    sleep "$interval"
  done
}

# --- Main ---

usage() {
  cat <<EOF
LLARS Pipeline Helper

Usage: $0 <command> [args]

Commands:
  status [pipeline_id]      Show pipeline status & all jobs (default: latest)
  jobs [pipeline_id]        Show failed jobs with log output
  log <job_id> [lines]      Show last N lines of job log (default: 50)
  retry <job_id>            Retry a failed job
  watch [pipeline_id] [s]   Watch pipeline until done (default: 30s interval)
  deploy                    Trigger FORCE_DEPLOY pipeline
  trigger                   Trigger a normal pipeline
  cancel-all                Cancel all running/pending pipelines on branch

Environment:
  BRANCH=main               Branch to operate on (default: main)
  ENV_FILE=.env              Path to .env file with credentials

Examples:
  $0 status                 # Latest pipeline status
  $0 status 30381           # Specific pipeline
  $0 jobs                   # Failed jobs + logs
  $0 retry 71568            # Retry a specific job
  $0 watch                  # Watch latest pipeline live
  $0 deploy                 # Trigger FORCE_DEPLOY
  $0 cancel-all             # Cancel everything running
EOF
}

case "${1:-}" in
  status)   cmd_status "${2:-}" ;;
  jobs)     cmd_jobs "${2:-}" ;;
  log)      cmd_log "${2:-}" "${3:-50}" ;;
  retry)    cmd_retry "${2:-}" ;;
  watch)    cmd_watch "${2:-}" "${3:-30}" ;;
  deploy)   cmd_deploy ;;
  trigger)  cmd_trigger ;;
  cancel-all) cmd_cancel_all ;;
  -h|--help|help) usage ;;
  *)
    usage
    exit 1
    ;;
esac
