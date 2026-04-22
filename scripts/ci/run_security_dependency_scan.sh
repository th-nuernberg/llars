#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-report}"
REPORT_DIR="${2:-security-reports}"

if [[ "$MODE" != "report" && "$MODE" != "gate" ]]; then
  echo "Usage: $0 [report|gate] [report_dir]" >&2
  exit 2
fi

mkdir -p "$REPORT_DIR"

IGNORE_ARGS="$(grep -v '^#' app/.pip-audit-ignore | grep -v '^$' | sed 's/^/--ignore-vuln /' | tr '\n' ' ')"

set +e
eval "pip-audit -r app/requirements.txt --format json $IGNORE_ARGS" > "$REPORT_DIR/pip-audit.json"
PIP_AUDIT_EXIT=$?
(
  cd llars-frontend
  npm audit --audit-level=high --json > "../$REPORT_DIR/npm-audit.json"
)
NPM_AUDIT_EXIT=$?
set -e

[ -s "$REPORT_DIR/pip-audit.json" ] || echo "[]" > "$REPORT_DIR/pip-audit.json"
[ -s "$REPORT_DIR/npm-audit.json" ] || echo "{}" > "$REPORT_DIR/npm-audit.json"

python3 - "$REPORT_DIR" "$PIP_AUDIT_EXIT" "$NPM_AUDIT_EXIT" <<'PY'
import json
import sys
from pathlib import Path

report_dir = Path(sys.argv[1])
pip_exit = sys.argv[2]
npm_exit = sys.argv[3]

def load_json(path, fallback):
    raw = path.read_text()
    try:
        return json.loads(raw)
    except Exception:
        return fallback

pip_payload = load_json(report_dir / "pip-audit.json", [])
npm_payload = load_json(report_dir / "npm-audit.json", {})

pip_findings = len(pip_payload) if isinstance(pip_payload, list) else 0
npm_vulns = npm_payload.get("metadata", {}).get("vulnerabilities", {}) if isinstance(npm_payload, dict) else {}
npm_total = sum(value for value in npm_vulns.values() if isinstance(value, int))

print(
    f"security scan summary | mode_hint={'gate' if (pip_exit != '0' or npm_exit != '0') else 'clean'} "
    f"pip_audit_exit={pip_exit} pip_findings={pip_findings} "
    f"npm_audit_exit={npm_exit} npm_findings={npm_total}"
)

if isinstance(pip_payload, list):
    for dependency in pip_payload[:20]:
        name = dependency.get("name", "<unknown>")
        version = dependency.get("version", "<unknown>")
        vulns = dependency.get("vulns", [])
        for vuln in vulns[:10]:
            fixes = ",".join(vuln.get("fix_versions", [])) or "-"
            print(f"pip finding | package={name} version={version} id={vuln.get('id', '-')} fixes={fixes}")

if isinstance(npm_payload, dict):
    findings = npm_payload.get("vulnerabilities", {})
    if isinstance(findings, dict):
        for package_name, meta in list(findings.items())[:20]:
            if not isinstance(meta, dict):
                continue
            severity = meta.get("severity", "-")
            fix_available = meta.get("fixAvailable", False)
            print(
                f"npm finding | package={package_name} severity={severity} "
                f"fix_available={fix_available}"
            )
PY

if [ "$PIP_AUDIT_EXIT" -ne 0 ] || [ "$NPM_AUDIT_EXIT" -ne 0 ]; then
  if [ "$MODE" = "gate" ]; then
    echo "Blocking release due to unresolved dependency findings."
    exit 1
  fi
  echo "Security findings detected. Report-only mode keeps the pipeline green."
else
  echo "No unresolved dependency findings detected."
fi
