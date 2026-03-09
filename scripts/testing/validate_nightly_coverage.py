#!/usr/bin/env python3
"""Validate nightly Home-tile and workflow coverage.

Checks:
1. home_tiles.contract.json routes match Home.vue routes.
2. Every tile/workflow contract name has a matching Playwright test title.
3. Required Nightly activity IDs are present in specs.
4. Tile/workflow/activity names and IDs are unique.
5. Governance gate: if Home tile config changed in this commit, docs+tests must also change.
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
ACTIVITY_CONTRACT_FILE = REPO_ROOT / "llars-frontend/e2e/nightly/nightly_activities.contract.json"
NIGHTLY_TEST_DIR = REPO_ROOT / "llars-frontend/e2e/nightly"

REQUIRED_DOC_FILES = {
    "CLAUDE.md",
    "docs/testing/nightly/NIGHTLY_TILE_MATRIX.md",
    "docs/docs/guides/nightly-test-activities.md",
}

REQUIRED_TEST_CHANGE_PREFIXES = {
    "llars-frontend/e2e/nightly/",
}

HOME_ROUTE_PATTERN = re.compile(r"route:\s*'([^']+)'")
TEST_TITLE_PATTERN = re.compile(r"\btest\(\s*['\"]([^'\"]+)['\"]")
ACTIVITY_ID_PATTERN = re.compile(r"\[ACT:([A-Z0-9-]+)\]")
ACTIVITY_CALL_PATTERN = re.compile(r"\bactivity\(\s*['\"]([A-Z0-9-]+)['\"]")


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


def collect_nightly_activity_ids() -> set[str]:
    activity_ids: set[str] = set()
    for file in NIGHTLY_TEST_DIR.glob("*.spec.js"):
        content = file.read_text(encoding="utf-8")
        for activity_id in ACTIVITY_ID_PATTERN.findall(content):
            activity_ids.add(activity_id.strip())
        for activity_id in ACTIVITY_CALL_PATTERN.findall(content):
            activity_ids.add(activity_id.strip())
    return activity_ids


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
    activity_contract = load_json(ACTIVITY_CONTRACT_FILE)

    tile_entries = tile_contract.get("tiles", [])
    workflow_entries = workflow_contract.get("workflows", [])
    activity_entries = activity_contract.get("activities", [])

    tile_names = [entry.get("name", "").strip() for entry in tile_entries]
    tile_routes = [entry.get("route", "").strip() for entry in tile_entries]
    workflow_names = [entry.get("name", "").strip() for entry in workflow_entries]
    activity_ids = [entry.get("id", "").strip() for entry in activity_entries]
    required_activity_ids = [
        entry.get("id", "").strip()
        for entry in activity_entries
        if bool(entry.get("required"))
    ]
    activity_tests = [entry.get("test", "").strip() for entry in activity_entries]

    if len(tile_names) != len(set(tile_names)):
        errors.append("Duplicate tile names in home_tiles.contract.json")

    if len(tile_routes) != len(set(tile_routes)):
        errors.append("Duplicate tile routes in home_tiles.contract.json")

    if len(workflow_names) != len(set(workflow_names)):
        errors.append("Duplicate workflow names in nightly_workflows.contract.json")

    if len(activity_ids) != len(set(activity_ids)):
        errors.append("Duplicate activity IDs in nightly_activities.contract.json")

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

    unknown_activity_tests = sorted(
        test_name for test_name in set(activity_tests)
        if test_name and test_name not in nightly_titles
    )
    if unknown_activity_tests:
        errors.append(
            "Activity contract references unknown test titles: "
            + ", ".join(unknown_activity_tests)
        )

    nightly_activity_ids = collect_nightly_activity_ids()
    missing_required_activity_ids = sorted(
        activity_id
        for activity_id in required_activity_ids
        if activity_id and activity_id not in nightly_activity_ids
    )
    if missing_required_activity_ids:
        errors.append(
            "Missing required nightly activities (add [ACT:<ID>] test steps): "
            + ", ".join(missing_required_activity_ids)
        )

    unknown_activity_ids = sorted(
        activity_id
        for activity_id in nightly_activity_ids
        if activity_id not in set(activity_ids)
    )
    if unknown_activity_ids:
        errors.append(
            "Nightly specs use unknown activity IDs (not in nightly_activities.contract.json): "
            + ", ".join(unknown_activity_ids)
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
