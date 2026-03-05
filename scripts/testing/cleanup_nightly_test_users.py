#!/usr/bin/env python3
"""Cleanup temporary nightly E2E users after the full Playwright run.

Expected env vars (same set as CI job):
- PLAYWRIGHT_API_BASE_URL / PLAYWRIGHT_BASE_URL
- E2E_BOOTSTRAP_TEST_USERS=true
- E2E_KEEP_TEST_USERS=false
- E2E_BOOTSTRAP_ADMIN_USER (default: admin)
- E2E_BOOTSTRAP_ADMIN_PASSWORD (default: E2E_TEST_PASSWORD)
- E2E_ADMIN_USER / E2E_RESEARCHER_USER / E2E_EVALUATOR_USER / E2E_CHATBOT_MANAGER_USER
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def request_json(
    method: str,
    url: str,
    token: str | None = None,
    payload: dict | None = None,
) -> tuple[int, dict | None, str]:
    body = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                data = None
            return resp.status, data, raw
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            data = None
        return err.code, data, raw
    except Exception as err:  # noqa: BLE001
        return 0, None, str(err)


def main() -> int:
    if not env_flag("E2E_BOOTSTRAP_TEST_USERS"):
        print("[cleanup] Bootstrap mode disabled; nothing to cleanup.")
        return 0

    if env_flag("E2E_KEEP_TEST_USERS"):
        print("[cleanup] E2E_KEEP_TEST_USERS=true; skipping cleanup.")
        return 0

    base_url = os.getenv("PLAYWRIGHT_API_BASE_URL") or os.getenv("PLAYWRIGHT_BASE_URL") or "http://localhost:55080"
    base_url = base_url.rstrip("/")

    bootstrap_user = os.getenv("E2E_BOOTSTRAP_ADMIN_USER", "admin")
    bootstrap_password = os.getenv("E2E_BOOTSTRAP_ADMIN_PASSWORD") or os.getenv("E2E_TEST_PASSWORD", "admin123")

    login_status, login_data, login_raw = request_json(
        "POST",
        f"{base_url}/auth/login",
        payload={"username": bootstrap_user, "password": bootstrap_password},
    )
    if login_status != 200 or not isinstance(login_data, dict) or not login_data.get("access_token"):
        print(f"[cleanup] Bootstrap login failed ({login_status}): {login_raw}")
        return 1

    token = str(login_data["access_token"])

    target_users = [
        os.getenv("E2E_CHATBOT_MANAGER_USER", "test_chatbot_manager"),
        os.getenv("E2E_RESEARCHER_USER", "test_researcher"),
        os.getenv("E2E_EVALUATOR_USER", "test_evaluator"),
        os.getenv("E2E_ADMIN_USER", "test_admin"),
    ]

    # Preserve order while removing duplicates/empties.
    deduped_targets: list[str] = []
    seen: set[str] = set()
    for username in target_users:
        name = (username or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        deduped_targets.append(name)

    failed = False
    for username in deduped_targets:
        if username == bootstrap_user:
            print(f"[cleanup] Skip deleting bootstrap admin user '{username}'.")
            continue

        safe_username = urllib.parse.quote(username, safe="")
        status, _, raw = request_json(
            "DELETE",
            f"{base_url}/api/admin/users/{safe_username}",
            token=token,
        )
        if status in (200, 204, 404):
            print(f"[cleanup] deleted-or-absent user '{username}' (status={status})")
        else:
            failed = True
            print(f"[cleanup] failed to delete '{username}' (status={status}): {raw}")

    if failed:
        print("[cleanup] completed with errors.")
        return 1

    print("[cleanup] completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
