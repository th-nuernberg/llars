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
frontend_package_json = Path("llars-frontend/package.json")

def load_json(path, fallback):
    raw = path.read_text()
    try:
        return json.loads(raw)
    except Exception:
        return fallback

pip_payload = load_json(report_dir / "pip-audit.json", [])
npm_payload = load_json(report_dir / "npm-audit.json", {})
frontend_package = load_json(frontend_package_json, {})

pip_findings = len(pip_payload) if isinstance(pip_payload, list) else 0
npm_vulns = npm_payload.get("metadata", {}).get("vulnerabilities", {}) if isinstance(npm_payload, dict) else {}
npm_total = sum(value for value in npm_vulns.values() if isinstance(value, int))
runtime_dependencies = set((frontend_package.get("dependencies") or {}).keys()) if isinstance(frontend_package, dict) else set()
dev_dependencies = set((frontend_package.get("devDependencies") or {}).keys()) if isinstance(frontend_package, dict) else set()
npm_gate_blockers = []

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
            is_runtime_direct_dependency = package_name in runtime_dependencies
            is_dev_direct_dependency = package_name in dev_dependencies
            is_gate_blocker = (
                severity in {"high", "critical"}
                and bool(fix_available)
                and is_runtime_direct_dependency
                and not is_dev_direct_dependency
            )
            if is_gate_blocker:
                npm_gate_blockers.append(package_name)
            print(
                f"npm finding | package={package_name} severity={severity} "
                f"fix_available={fix_available} "
                f"runtime_direct={is_runtime_direct_dependency} "
                f"dev_direct={is_dev_direct_dependency} "
                f"gate_blocker={is_gate_blocker}"
            )

print(
    f"security gate policy | pip_blockers={pip_findings} "
    f"npm_gate_blockers={len(npm_gate_blockers)}"
)

block_release = pip_findings > 0 or len(npm_gate_blockers) > 0
print(f"security gate decision | block_release={block_release}")

Path(report_dir / "gate-result.json").write_text(json.dumps({
    "pip_findings": pip_findings,
    "npm_findings": npm_total,
    "npm_gate_blockers": npm_gate_blockers,
    "block_release": block_release,
}))
PY

GATE_DECISION="$(python3 - "$REPORT_DIR" <<'PY'
import json
import sys
from pathlib import Path

report_dir = Path(sys.argv[1])
payload = json.loads((report_dir / "gate-result.json").read_text())
print("true" if payload.get("block_release") else "false")
PY
)"

if [ "$PIP_AUDIT_EXIT" -ne 0 ] || [ "$NPM_AUDIT_EXIT" -ne 0 ]; then
  if [ "$MODE" = "gate" ] && [ "$GATE_DECISION" = "true" ]; then
    echo "Blocking release due to unresolved dependency findings that violate the release policy."
    exit 1
  fi
  if [ "$MODE" = "gate" ]; then
    echo "Security findings detected, but none violate the release gate policy."
  else
    echo "Security findings detected. Report-only mode keeps the pipeline green."
  fi
else
  echo "No unresolved dependency findings detected."
fi
