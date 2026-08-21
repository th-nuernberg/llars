"""
Security Hardening Tests: /api/v1 surface
==========================================

Regression tests for four security findings on the public v1 API:

  C1 — ReferralLinkSpec.role_name is restricted to scenario-side roles only
       (no admin escalation via referral signup).
  C2 — Slug squatting is blocked: only the slug's creator (or admin) may
       update an existing referral link via the v1 service.
  H1 — Bulk-import payloads are capped (items, features, assessors).
  M1 — Non-owner GET/PATCH/DELETE returns 404 (not 409), so scenario-ID
       validity isn't leaked through a status-code differential.

Test IDs: APIV1-SEC-001..APIV1-SEC-010.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g
from pydantic import ValidationError

from decorators.error_handler import NotFoundError
from schemas.api_v1.scenario_api import (
    LlarsNativeEnvelope,
    NativeFeature,
    NativeItem,
    ReferralLinkSpec,
    ScenarioCreateRequest,
)
from schemas.evaluation_data_schemas import Source, SourceType
from services.api_v1_scenario_service import ApiV1Error, _sync_referral_link


# ---------------------------------------------------------------------------
# C1 — ReferralLinkSpec rejects "admin" (and other off-list roles)
# ---------------------------------------------------------------------------


class TestC1RoleNameWhitelist:
    """The pre-fix code accepted any string as role_name. Posting `admin`
    here was a one-step privilege escalation: ReferralRegistration would
    promote anyone joining via the link straight to global admin."""

    def test_APIV1_SEC_001_admin_role_rejected(self):
        with pytest.raises(ValidationError) as exc:
            ReferralLinkSpec(slug="emnlp-pilot", role_name="admin")
        # Pydantic surfaces the failed pattern with the field name.
        assert "role_name" in str(exc.value)

    def test_APIV1_SEC_002_random_role_rejected(self):
        with pytest.raises(ValidationError):
            ReferralLinkSpec(slug="emnlp-pilot", role_name="researcher")

    def test_APIV1_SEC_003_evaluator_assessor_viewer_accepted(self):
        for role in ("evaluator", "assessor", "viewer"):
            spec = ReferralLinkSpec(slug=f"slug-{role}", role_name=role)
            assert spec.role_name == role

    def test_APIV1_SEC_004_admin_via_full_request_rejected(self):
        """End-to-end through ScenarioCreateRequest — make sure the regex
        is reachable through the canonical create envelope, not just the
        sub-model in isolation."""
        with pytest.raises(ValidationError):
            ScenarioCreateRequest.model_validate(
                {
                    "name": "Pwn",
                    "eval_config": {
                        "type": "comparison",
                        "config": {"question": {"de": "?", "en": "?"}},
                    },
                    "referral_link": {
                        "slug": "pwn-link",
                        "role_name": "admin",  # the attack
                    },
                }
            )


# ---------------------------------------------------------------------------
# C2 — Slug squatting: only the slug creator (or admin) may re-sync
# ---------------------------------------------------------------------------


class TestC2SlugSquattingGuard:
    """`_sync_referral_link` previously called `ReferralService.update_link`
    on any matching slug, regardless of who owned it. This test stubs the
    DB lookups so we can drive the ownership branch deterministically."""

    def _run(
        self,
        existing_creator: str,
        requesting_username: str,
        is_admin: bool = False,
    ):
        """Invoke the service helper with a pre-existing slug owned by
        `existing_creator`, while `requesting_username` tries to re-target
        it. Returns whatever the helper returns or re-raises."""
        existing_link = SimpleNamespace(
            id=42,
            slug="contested-slug",
            created_by=existing_creator,
        )
        scenario = SimpleNamespace(id=999)
        spec = ReferralLinkSpec(
            slug="contested-slug",
            label="Squatted",
            role_name="evaluator",
            auto_enroll=True,
        )

        update_link = MagicMock()

        with patch(
            "services.referral_service.ReferralService.get_link_by_slug",
            return_value=existing_link,
        ), patch(
            "services.referral_service.ReferralService.update_link",
            update_link,
        ), patch(
            "services.permission_service.PermissionService.user_has_role",
            return_value=is_admin,
        ):
            result = _sync_referral_link(scenario, spec, requesting_username)
        return result, update_link

    def test_APIV1_SEC_005_foreign_slug_blocked(self):
        with pytest.raises(ApiV1Error) as exc:
            self._run(
                existing_creator="alice",
                requesting_username="bob",
                is_admin=False,
            )
        assert "owned by another user" in str(exc.value)

    def test_APIV1_SEC_006_same_owner_allowed(self):
        """The original creator can still re-sync their own slug
        (idempotent updates are a documented part of the contract)."""
        result, update_link = self._run(
            existing_creator="alice",
            requesting_username="alice",
            is_admin=False,
        )
        assert result is not None
        update_link.assert_called_once()

    def test_APIV1_SEC_007_admin_override_allowed(self):
        """A global admin should still be able to re-target any slug —
        otherwise we lock ourselves out of cleanup workflows."""
        result, update_link = self._run(
            existing_creator="alice",
            requesting_username="opadmin",
            is_admin=True,
        )
        assert result is not None
        update_link.assert_called_once()


# ---------------------------------------------------------------------------
# H1 — Bulk-import caps (items / features / assessors)
# ---------------------------------------------------------------------------


class TestH1ImportCaps:
    def _item(self, idx: int) -> NativeItem:
        return NativeItem(
            id=f"item_{idx}",
            label=f"Item {idx}",
            source=Source(type=SourceType.HUMAN),
            content="x",
        )

    def test_APIV1_SEC_008_501_items_rejected(self):
        items = [self._item(i) for i in range(501)]
        with pytest.raises(ValidationError) as exc:
            LlarsNativeEnvelope(items=items)
        assert "items" in str(exc.value)

    def test_APIV1_SEC_009_features_capped(self):
        too_many = [
            NativeFeature(content=f"f{i}", generated_by="human") for i in range(51)
        ]
        with pytest.raises(ValidationError) as exc:
            NativeItem(
                id="x",
                label="x",
                source=Source(type=SourceType.HUMAN),
                content="x",
                features=too_many,
            )
        assert "features" in str(exc.value)

    def test_APIV1_SEC_010_assessors_capped(self):
        # 201 invites should fail — 200 is the documented cap.
        assessors = [{"username": f"u{i}"} for i in range(201)]
        with pytest.raises(ValidationError) as exc:
            ScenarioCreateRequest.model_validate(
                {
                    "name": "Big",
                    "eval_config": {
                        "type": "comparison",
                        "config": {"question": {"de": "?", "en": "?"}},
                    },
                    "assessors": assessors,
                }
            )
        assert "assessors" in str(exc.value)

    def test_APIV1_SEC_011_500_items_accepted(self):
        # Boundary: exactly the cap is allowed (off-by-one guard).
        env = LlarsNativeEnvelope(items=[self._item(i) for i in range(500)])
        assert len(env.items) == 500


# ---------------------------------------------------------------------------
# M1 — Owner-mismatch returns NotFoundError, not ConflictError
# ---------------------------------------------------------------------------


def _build_route_app() -> Flask:
    """Minimal Flask app so we can call the `_require_owner` helpers in
    a real request context. The helpers read `g.authentik_user`, so we
    can't call them in pure-Python without a context."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


class TestM1EnumerationOracle:
    """Pre-fix the v1 routes raised `ConflictError("Only the scenario
    owner can ...")` (HTTP 409) when a non-owner hit a real but foreign
    scenario — vs `NotFoundError` (HTTP 404) for nonexistent IDs. The
    differential leaked scenario-ID validity. All four `_require_owner`
    helpers must now raise `NotFoundError` with an identical body."""

    @pytest.fixture
    def fake_user(self):
        return SimpleNamespace(username="bob")

    @pytest.fixture
    def foreign_scenario(self):
        return SimpleNamespace(id=12345, created_by="alice")

    def _assert_not_found(self, helper, scenario, fake_user):
        app = _build_route_app()
        with app.test_request_context("/"):
            g.authentik_user = fake_user
            with patch(
                "services.permission_service.PermissionService.user_has_role",
                return_value=False,
            ):
                with pytest.raises(NotFoundError) as exc:
                    helper(scenario)
        # Body must read like the missing-scenario branch — not "Only
        # the scenario owner ..." which is what gave the oracle away.
        assert "not found" in str(exc.value).lower()
        assert "owner" not in str(exc.value).lower()

    def test_APIV1_SEC_012_items_helper_returns_404(
        self, fake_user, foreign_scenario
    ):
        from routes.api_v1.scenario_items_routes import _require_owner
        self._assert_not_found(_require_owner, foreign_scenario, fake_user)

    def test_APIV1_SEC_013_assessors_helper_returns_404(
        self, fake_user, foreign_scenario
    ):
        from routes.api_v1.scenario_assessors_routes import _require_owner
        self._assert_not_found(_require_owner, foreign_scenario, fake_user)

    def test_APIV1_SEC_014_referral_helper_returns_404(
        self, fake_user, foreign_scenario
    ):
        from routes.api_v1.scenario_referral_routes import _require_owner
        self._assert_not_found(_require_owner, foreign_scenario, fake_user)

    def test_APIV1_SEC_015_admin_still_passes(
        self, fake_user, foreign_scenario
    ):
        """Admins must still bypass — otherwise admin tooling breaks."""
        from routes.api_v1.scenario_items_routes import _require_owner

        app = _build_route_app()
        with app.test_request_context("/"):
            g.authentik_user = fake_user
            with patch(
                "services.permission_service.PermissionService.user_has_role",
                return_value=True,
            ):
                # Should not raise.
                _require_owner(foreign_scenario)
