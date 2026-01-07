#!/usr/bin/env bash
set -euo pipefail

DURATION_SECONDS="${DURATION_SECONDS:-21600}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-600}"
BRANCH="${BRANCH:-main}"
LOG_FILE="${LOG_FILE:-pipeline-monitor.log}"
GITLAB_API_BASE="${GITLAB_API_BASE:-https://git.informatik.fh-nuernberg.de/api/v4}"
ENV_FILE="${ENV_FILE:-.env}"

if [ -f "$ENV_FILE" ]; then
  while IFS='=' read -r key value; do
    case "$key" in
      GITLAB_TOKEN|GITLAB_PROJECT_ID|GITLAB_API_BASE)
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        value="${value%$'\r'}"
        export "$key=$value"
        ;;
    esac
  done < <(grep -E '^(GITLAB_TOKEN|GITLAB_PROJECT_ID|GITLAB_API_BASE)=' "$ENV_FILE" || true)
fi

if [ -z "${GITLAB_TOKEN:-}" ] || [ -z "${GITLAB_PROJECT_ID:-}" ]; then
  echo "ERROR: GITLAB_TOKEN or GITLAB_PROJECT_ID not set." | tee -a "$LOG_FILE"
  exit 1
fi

start_ts=$(date +%s)
end_ts=$((start_ts + DURATION_SECONDS))

log() {
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*" | tee -a "$LOG_FILE"
}

while [ "$(date +%s)" -lt "$end_ts" ]; do
  pipelines_json=$(curl -sS --fail --max-time 20 --connect-timeout 5 \
    --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    "$GITLAB_API_BASE/projects/$GITLAB_PROJECT_ID/pipelines?ref=$BRANCH&per_page=1" || true)

  if [ -z "$pipelines_json" ]; then
    log "ERROR: Failed to fetch pipelines for branch=$BRANCH"
    sleep "$INTERVAL_SECONDS"
    continue
  fi

  pipeline_id=$(python3 -c 'import json,sys; p=json.load(sys.stdin); print(p[0]["id"] if p else "")' \
    <<< "$pipelines_json" 2>/dev/null || true)

  pipeline_status=$(python3 -c 'import json,sys; p=json.load(sys.stdin); print(p[0]["status"] if p else "")' \
    <<< "$pipelines_json" 2>/dev/null || true)

  if [ -z "$pipeline_id" ]; then
    log "No pipeline found for branch=$BRANCH"
  else
    log "Pipeline $pipeline_id status=$pipeline_status"
  fi

  if [ "$pipeline_status" = "failed" ]; then
    jobs_json=$(curl -sS --fail --max-time 20 --connect-timeout 5 \
      --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
      "$GITLAB_API_BASE/projects/$GITLAB_PROJECT_ID/pipelines/$pipeline_id/jobs?per_page=100" || true)

    failed_jobs=$(python3 -c 'import json,sys; jobs=json.load(sys.stdin); print(\"\\n\".join(f\"{j.get(\\\"id\\\")}\\|{j.get(\\\"name\\\")}\" for j in jobs if j.get(\"status\") == \"failed\"))' \
      <<< "$jobs_json" 2>/dev/null || true)

    while IFS='|' read -r job_id job_name; do
      [ -z "$job_id" ] && continue
      log "Job failed: $job_name ($job_id)"
      curl -sS --fail --max-time 20 --connect-timeout 5 \
        --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        "$GITLAB_API_BASE/projects/$GITLAB_PROJECT_ID/jobs/$job_id/trace" \
        | tail -50 | sed 's/^/  /' >> "$LOG_FILE"
    done <<< "$failed_jobs"
  fi

  sleep "$INTERVAL_SECONDS"
done

log "Monitoring complete."
