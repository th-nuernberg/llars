"""
Unit Tests: API Scope Enforcement
==================================

Tests for ``require_api_scope`` (app/auth/decorators.py) — the gate that
sits between ``api_key_or_token_required`` and the v1 routes. Drives the
table-driven matrix described in the v1 plan:
    {3 scopes} × {3 auth methods} × {allow, deny}

Test IDs: SCOPE-001..SCOPE-024.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from flask import Flask, g, jsonify

from auth.decorators import require_api_scope


# ---------------------------------------------------------------------------
# Test app — minimal, zero blueprint sprawl, mounts one route per scope.
# ---------------------------------------------------------------------------


def _build_scope_app() -> Flask:
    """One Flask app exposing three scope-gated probe routes.

    The fake `before_request` hook seeds `g.authentik_user`, `g.api_key_scopes`
    etc. so the scope decorator sees a realistic context without us having to
    drag in the full auth chain.
    """
    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.route("/probe/read")
    @require_api_scope("scenario:read")
    def probe_read():
        return jsonify({"ok": True, "route": "read"})

    @app.route("/probe/write")
    @require_api_scope("scenario:write")
    def probe_write():
        return jsonify({"ok": True, "route": "write"})

    @app.route("/probe/admin")
    @require_api_scope("admin:*")
    def probe_admin():
        return jsonify({"ok": True, "route": "admin"})

    return app


class _FakeUser:
    """Just enough of `User` for `require_api_scope` to grab `username`."""

    def __init__(self, username: str = "alice"):
        self.username = username


@pytest.fixture
def scope_app():
    return _build_scope_app()


@pytest.fixture
def client(scope_app):
    return scope_app.test_client()


def _seed_g(app: Flask, *, scopes, username="alice"):
    """Install a before_request that fakes the auth-chain output."""
    app.before_request_funcs.setdefault(None, []).clear()

    @app.before_request
    def _seed():
        g.authentik_user = _FakeUser(username)
        g.api_key_scopes = scopes


# ---------------------------------------------------------------------------
# 1. Explicit-scope path (key with a scope list)
# ---------------------------------------------------------------------------


class TestExplicitScopeKey:
    """API key that carries a scope CSV — must allow exact + admin:* match,
    deny everything else (no fall-through to RBAC)."""

    def test_SCOPE_001_read_scope_allows_read_route(self, scope_app, client):
        _seed_g(scope_app, scopes=["scenario:read"])
        assert client.get("/probe/read").status_code == 200

    def test_SCOPE_002_read_scope_denies_write_route(self, scope_app, client):
        _seed_g(scope_app, scopes=["scenario:read"])
        resp = client.get("/probe/write")
        assert resp.status_code == 403
        assert "required_scopes" in resp.get_json()

    def test_SCOPE_003_write_scope_allows_write_route(self, scope_app, client):
        _seed_g(scope_app, scopes=["scenario:write"])
        assert client.get("/probe/write").status_code == 200

    def test_SCOPE_004_write_scope_denies_admin_route(self, scope_app, client):
        _seed_g(scope_app, scopes=["scenario:write"])
        assert client.get("/probe/admin").status_code == 403

    def test_SCOPE_005_admin_star_allows_everything(self, scope_app, client):
        _seed_g(scope_app, scopes=["admin:*"])
        assert client.get("/probe/read").status_code == 200
        assert client.get("/probe/write").status_code == 200
        assert client.get("/probe/admin").status_code == 200

    def test_SCOPE_006_unknown_scope_does_not_satisfy_required(
        self, scope_app, client
    ):
        _seed_g(scope_app, scopes=["random:nonsense"])
        assert client.get("/probe/read").status_code == 403


# ---------------------------------------------------------------------------
# 2. OAuth path (scopes is None — defer to RBAC permissions)
# ---------------------------------------------------------------------------


class TestOAuthFallback:
    """Bearer-token callers carry `g.api_key_scopes = None`. The decorator
    must look up RBAC permissions or admin role instead of pretending the
    list is empty (which would be a vacuous deny)."""

    def test_SCOPE_010_admin_role_bypasses_scope_check(self, scope_app, client):
        _seed_g(scope_app, scopes=None)
        with patch(
            "services.permission_service.PermissionService.user_has_role",
            return_value=True,
        ):
            assert client.get("/probe/admin").status_code == 200

    def test_SCOPE_011_rbac_permission_unlocks_read(self, scope_app, client):
        _seed_g(scope_app, scopes=None)
        with patch(
            "services.permission_service.PermissionService.user_has_role",
            return_value=False,
        ), patch(
            "services.permission_service.PermissionService.check_permission",
            side_effect=lambda u, p: p == "feature:rating:view",
        ):
            assert client.get("/probe/read").status_code == 200

    def test_SCOPE_012_no_role_no_perm_denies(self, scope_app, client):
        _seed_g(scope_app, scopes=None)
        with patch(
            "services.permission_service.PermissionService.user_has_role",
            return_value=False,
        ), patch(
            "services.permission_service.PermissionService.check_permission",
            return_value=False,
        ):
            assert client.get("/probe/write").status_code == 403


# ---------------------------------------------------------------------------
# 3. Legacy-key path (scopes is empty list — same fallback as OAuth)
# ---------------------------------------------------------------------------


class TestLegacyKeyFallback:
    """Pre-scope keys carry `[]`. The decorator must fall through to the
    same RBAC path as OAuth, otherwise we'd retroactively break existing
    keys when scope enforcement ships."""

    def test_SCOPE_020_empty_scopes_with_admin_role_passes(
        self, scope_app, client
    ):
        _seed_g(scope_app, scopes=[])
        with patch(
            "services.permission_service.PermissionService.user_has_role",
            return_value=True,
        ):
            assert client.get("/probe/write").status_code == 200

    def test_SCOPE_021_empty_scopes_no_role_no_perm_denies(
        self, scope_app, client
    ):
        _seed_g(scope_app, scopes=[])
        with patch(
            "services.permission_service.PermissionService.user_has_role",
            return_value=False,
        ), patch(
            "services.permission_service.PermissionService.check_permission",
            return_value=False,
        ):
            assert client.get("/probe/read").status_code == 403


# ---------------------------------------------------------------------------
# 4. Missing-auth-context guard
# ---------------------------------------------------------------------------


class TestMissingContext:
    """If the chain didn't run (no `g.authentik_user`), we must not 500 —
    we surface a clean 401 so the caller knows to authenticate."""

    def test_SCOPE_030_no_user_returns_401(self, scope_app, client):
        # Don't seed g — simulates someone forgetting the
        # @api_key_or_token_required decorator on a v1 route.
        @scope_app.before_request
        def _strip():
            g.api_key_scopes = None  # emulate no auth chain at all
            # no g.authentik_user set

        assert client.get("/probe/read").status_code == 401
