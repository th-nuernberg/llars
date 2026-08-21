"""
Schema + contract tests for the v1 chatbot API.

Test IDs: APIV1-CB-001..014.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas.api_v1.chatbot_api import (
    ChatbotAccessSpec,
    ChatbotCreateRequest,
    ChatbotPatchRequest,
    ChatbotTweakRequest,
    ChatMessageRequest,
    RagCollectionRef,
    WizardCrawlSpec,
    WizardQuickbuildRequest,
)


class TestCreateRequest:
    def test_APIV1_CB_001_minimal_happy_path(self):
        req = ChatbotCreateRequest(
            name="bot1", display_name="Bot 1", system_prompt="You help."
        )
        assert req.name == "bot1"
        assert req.access.is_public is False
        assert req.wizard is None

    def test_APIV1_CB_002_with_wizard_branch(self):
        req = ChatbotCreateRequest(
            name="bot2", display_name="Bot 2", system_prompt="x",
            wizard={"crawl_url": "https://example.com", "max_pages": 30},
        )
        assert req.wizard is not None
        assert req.wizard.max_pages == 30

    def test_APIV1_CB_003_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            ChatbotCreateRequest.model_validate({
                "name": "x", "display_name": "x", "system_prompt": "x",
                "TYPO": "should fail",
            })

    def test_APIV1_CB_004_color_pattern(self):
        with pytest.raises(ValidationError):
            ChatbotCreateRequest(
                name="x", display_name="x", system_prompt="x", color="not-a-hex",
            )

    def test_APIV1_CB_005_temperature_bounds(self):
        # Valid bounds
        ChatbotCreateRequest(
            name="x", display_name="x", system_prompt="x", temperature=0.0,
        )
        ChatbotCreateRequest(
            name="x", display_name="x", system_prompt="x", temperature=2.0,
        )
        with pytest.raises(ValidationError):
            ChatbotCreateRequest(
                name="x", display_name="x", system_prompt="x", temperature=2.1,
            )


class TestAccessSpecHardening:
    """C1-pattern: privileged role names must be rejected client-side."""

    def test_APIV1_CB_006_admin_role_rejected(self):
        with pytest.raises(ValidationError) as exc:
            ChatbotAccessSpec(allowed_roles=["admin"])
        assert "not allowed on chatbot access list" in str(exc.value)

    def test_APIV1_CB_007_only_documented_roles_accepted(self):
        spec = ChatbotAccessSpec(
            allowed_roles=["evaluator", "researcher", "chatbot_manager"]
        )
        assert sorted(spec.allowed_roles) == [
            "chatbot_manager", "evaluator", "researcher",
        ]

    def test_APIV1_CB_008_unknown_role_rejected(self):
        with pytest.raises(ValidationError):
            ChatbotAccessSpec(allowed_roles=["super-mod"])


class TestImportCaps:
    """H1-pattern: every list field has a documented max_length."""

    def test_APIV1_CB_009_collections_max_20(self):
        with pytest.raises(ValidationError):
            ChatbotCreateRequest(
                name="x", display_name="x", system_prompt="x",
                collections=[{"collection_id": i} for i in range(1, 22)],
            )

    def test_APIV1_CB_010_allowed_usernames_max_200(self):
        with pytest.raises(ValidationError):
            ChatbotAccessSpec(
                allowed_usernames=[f"user{i}" for i in range(201)]
            )

    def test_APIV1_CB_011_collections_at_cap_accepted(self):
        req = ChatbotCreateRequest(
            name="x", display_name="x", system_prompt="x",
            collections=[{"collection_id": i} for i in range(1, 21)],
        )
        assert len(req.collections) == 20


class TestTweakRequest:
    def test_APIV1_CB_012_empty_tweak_is_legal(self):
        # Empty tweak should still validate; the route handler treats it
        # as a no-op and returns the unchanged chatbot.
        req = ChatbotTweakRequest()
        assert req.system_prompt is None

    def test_APIV1_CB_013_extra_field_rejected_on_tweak(self):
        with pytest.raises(ValidationError):
            ChatbotTweakRequest.model_validate({"display_name": "X"})  # display_name not in tweak


class TestQuickbuild:
    def test_APIV1_CB_014_quickbuild_requires_crawl_and_model(self):
        # Both fields required
        with pytest.raises(ValidationError):
            WizardQuickbuildRequest.model_validate({})
        # Happy path
        req = WizardQuickbuildRequest.model_validate({
            "crawl": {"crawl_url": "https://example.com"},
            "model_name": "Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506",
        })
        assert req.access.is_public is False
        assert str(req.crawl.crawl_url).startswith("https://example.com")
