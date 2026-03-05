#!/usr/bin/env python3
"""Validate nightly Home-tile and workflow coverage.

Checks:
1. home_tiles.contract.json routes match Home.vue routes.
2. Every tile/workflow contract name has a matching Playwright test title.
3. Tile and workflow names are unique.
4. Governance gate: if Home tile config changed in this commit, docs+tests must also change.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOME_FILE = REPO_ROOT / "llars-frontend/src/components/Home.vue"
TILE_CONTRACT_FILE = REPO_ROOT / "llars-frontend/src/config/home_tiles.contract.json"
WORKFLOW_CONTRACT_FILE = REPO_ROOT / "llars-frontend/e2e/nightly/nightly_workflows.contract.json"
NIGHTLY_TEST_DIR = REPO_ROOT / "llars-frontend/e2e/nightly"

REQUIRED_DOC_FILES = {
    "CLAUDE.md",
    "docs/testing/nightly/NIGHTLY_TILE_MATRIX.md",
}

REQUIRED_TEST_CHANGE_PREFIXES = {
    "llars-frontend/e2e/nightly/",
}

HOME_ROUTE_PATTERN = re.compile(r"route:\s*'([^']+)'")
TEST_TITLE_PATTERN = re.compile(r"\btest\(\s*['\"]([^'\"]+)['\"]")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def collect_home_routes() -> list[str]:
    content = HOME_FILE.read_text(encoding="utf-8")
    return HOME_ROUTE_PATTERN.findall(content)


def collect_nightly_test_titles() -> set[str]:
    titles: set[str] = set()
    for file in NIGHTLY_TEST_DIR.glob("*.spec.js"):
        content = file.read_text(encoding="utf-8")
        for title in TEST_TITLE_PATTERN.findall(content):
            titles.add(title.strip())
    return titles


def changed_files_in_head() -> set[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return set()

    files = {line.strip() for line in out.splitlines() if line.strip()}
    return files


def route_to_tile_test_id(route: str) -> str:
    normalized = re.sub(r"[/?=&]+", "-", route.strip().lstrip("/"))
    normalized = re.sub(r"-+", "-", normalized).strip("-").lower()
    return f"home-tile-{normalized}"


def validate() -> list[str]:
    errors: list[str] = []

    tile_contract = load_json(TILE_CONTRACT_FILE)
    workflow_contract = load_json(WORKFLOW_CONTRACT_FILE)

    tile_entries = tile_contract.get("tiles", [])
    workflow_entries = workflow_contract.get("workflows", [])

    tile_names = [entry.get("name", "").strip() for entry in tile_entries]
    tile_routes = [entry.get("route", "").strip() for entry in tile_entries]
    workflow_names = [entry.get("name", "").strip() for entry in workflow_entries]

    if len(tile_names) != len(set(tile_names)):
        errors.append("Duplicate tile names in home_tiles.contract.json")

    if len(tile_routes) != len(set(tile_routes)):
        errors.append("Duplicate tile routes in home_tiles.contract.json")

    if len(workflow_names) != len(set(workflow_names)):
        errors.append("Duplicate workflow names in nightly_workflows.contract.json")

    home_routes = collect_home_routes()
    home_route_set = set(home_routes)
    contract_route_set = set(tile_routes)

    missing_in_contract = sorted(home_route_set - contract_route_set)
    missing_in_home = sorted(contract_route_set - home_route_set)

    if missing_in_contract:
        errors.append(
            "Routes found in Home.vue but missing in home_tiles.contract.json: "
            + ", ".join(missing_in_contract)
        )

    if missing_in_home:
        errors.append(
            "Routes found in home_tiles.contract.json but missing in Home.vue: "
            + ", ".join(missing_in_home)
        )

    nightly_titles = collect_nightly_test_titles()

    missing_tile_tests = sorted(name for name in tile_names if name and name not in nightly_titles)
    if missing_tile_tests:
        errors.append(
            "Missing nightly tile tests (title must match tile name exactly): "
            + ", ".join(missing_tile_tests)
        )

    missing_workflow_tests = sorted(name for name in workflow_names if name and name not in nightly_titles)
    if missing_workflow_tests:
        errors.append(
            "Missing nightly workflow tests (title must match workflow name exactly): "
            + ", ".join(missing_workflow_tests)
        )

    for route in tile_routes:
        test_id = route_to_tile_test_id(route)
        if not test_id.startswith("home-tile-"):
            errors.append(f"Invalid generated test id for route: {route}")

    changed_files = changed_files_in_head()
    tile_files_touched = {
        "llars-frontend/src/components/Home.vue",
        "llars-frontend/src/config/home_tiles.contract.json",
    }

    if changed_files and (changed_files & tile_files_touched):
        has_doc_update = any(path in changed_files for path in REQUIRED_DOC_FILES)
        has_test_update = any(
            any(path.startswith(prefix) for prefix in REQUIRED_TEST_CHANGE_PREFIXES)
            for path in changed_files
        )

        if not has_doc_update:
            errors.append(
                "Tile policy violation: Home tile changes detected but required docs were not updated "
                f"({', '.join(sorted(REQUIRED_DOC_FILES))})."
            )

        if not has_test_update:
            errors.append(
                "Tile policy violation: Home tile changes detected but nightly tests were not updated "
                "(expected changes under llars-frontend/e2e/nightly/)."
            )

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Nightly coverage validation failed:\n")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Nightly coverage validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
