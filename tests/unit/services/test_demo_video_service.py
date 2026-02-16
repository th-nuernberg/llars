"""Unit tests for demo video data service."""

from types import SimpleNamespace

from db.models.llm_model import LLMModel
from services.demo_video_service import (
    COLLAB_USER,
    DEMO_USER,
    LIVE_PROMPT_NAME,
    LIVE_PROMPT_KEY,
    NARRATIVE_FEATURE_TYPE_NAME,
    PRESEED_PROMPT_KEY,
    PRESEED_PROMPT_NAME,
    STRUCTURED_FEATURE_TYPE_NAME,
    _build_eval_prompt_content,
    _build_preseed_prompt_content,
    _color_distance_sq,
    _ensure_demo_model_color_contrast,
    _resolve_prompt_feature_type,
    _select_balanced_partial_features,
    _sort_outputs_for_case,
)


def _build_llm_model(model_id: str, color: str, provider: str = "test") -> LLMModel:
    return LLMModel(
        model_id=model_id,
        display_name=model_id,
        provider=provider,
        model_type=LLMModel.MODEL_TYPE_LLM,
        color=color,
        context_window=4096,
        max_output_tokens=1024,
        input_cost_per_million=0.0,
        output_cost_per_million=0.0,
        is_default=False,
        is_active=True,
    )


def test_DEMO_COLOR_001_ensure_demo_models_get_clear_color_distance(app, db, app_context):
    """Demo models should be recolored to remain clearly distinguishable."""
    mistral_id = "Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506"
    gpt5_nano_id = "Global/OpenAI/gpt-5-nano"

    mistral = _build_llm_model(mistral_id, "#8A993A", provider="mistral")
    gpt5_nano = _build_llm_model(gpt5_nano_id, "#89983B", provider="openai")
    # Additional model ensures palette isn't empty and reflects real-world seeding.
    other = _build_llm_model("Global/Mistral/Magistral-Small-2509", "#486E9C", provider="mistral")

    db.session.add_all([mistral, gpt5_nano, other])
    db.session.commit()

    changed = _ensure_demo_model_color_contrast()

    assert changed >= 1
    assert mistral.color != gpt5_nano.color
    assert _color_distance_sq(mistral.color, gpt5_nano.color) >= 12000


def test_DEMO_PROMPT_001_preseed_prompt_contains_block_authorship():
    """Pre-seed prompt should include explicit collaboration attribution metadata."""
    content = _build_preseed_prompt_content()
    attribution = content.get("collaboration_attribution", {})
    blocks = content.get("blocks", {})

    assert attribution.get("owner") == DEMO_USER
    assert COLLAB_USER in attribution.get("shared_with", [])
    assert blocks["System Prompt"]["author"] == DEMO_USER
    assert blocks["Task Explanation"]["author"] == COLLAB_USER
    assert blocks["Data Format Explanation"]["author"] == DEMO_USER


def test_DEMO_PROMPT_002_live_prompt_contains_block_authorship():
    """Live prompt should include explicit collaboration attribution metadata."""
    content = _build_eval_prompt_content()
    attribution = content.get("collaboration_attribution", {})
    blocks = content.get("blocks", {})
    data_block_content = blocks["Data Format Explanation"]["content"]

    assert attribution.get("owner") == DEMO_USER
    assert COLLAB_USER in attribution.get("shared_with", [])
    assert blocks["System Prompt"]["author"] == COLLAB_USER
    assert blocks["Task Explanation"]["author"] == DEMO_USER
    assert blocks["Data Format Explanation"]["author"] == COLLAB_USER
    assert "The data below is provided as a subject line followed by the email thread content from a counselling session." in data_block_content
    assert "Subject: {{subject}}" in data_block_content
    assert "Content: {{content}}" in data_block_content


def test_DEMO_SORT_001_outputs_are_sorted_by_prompt_then_model_then_id():
    """Output sorting should be deterministic for seeded ranking feature order."""
    outputs = [
        SimpleNamespace(id=9, prompt_variant_name=LIVE_PROMPT_NAME, llm_model_name="Global/OpenAI/gpt-5-nano"),
        SimpleNamespace(id=7, prompt_variant_name=PRESEED_PROMPT_NAME, llm_model_name="Global/OpenAI/gpt-5-nano"),
        SimpleNamespace(id=8, prompt_variant_name=LIVE_PROMPT_NAME, llm_model_name="Global/Mistral/Mistral-Small-3.2"),
        SimpleNamespace(id=6, prompt_variant_name=PRESEED_PROMPT_NAME, llm_model_name="Global/Mistral/Mistral-Small-3.2"),
    ]

    sorted_outputs = _sort_outputs_for_case(outputs)
    assert [out.id for out in sorted_outputs] == [6, 7, 8, 9]


def test_DEMO_PROVENANCE_001_prompt_feature_type_resolution_handles_aliases():
    """Prompt-to-feature-type mapping should stay stable across label variants."""
    structured_type = SimpleNamespace(type_id=1, name=STRUCTURED_FEATURE_TYPE_NAME)
    narrative_type = SimpleNamespace(type_id=2, name=NARRATIVE_FEATURE_TYPE_NAME)
    feature_type_by_prompt = {
        PRESEED_PROMPT_KEY: structured_type,
        LIVE_PROMPT_KEY: narrative_type,
    }

    assert _resolve_prompt_feature_type(
        PRESEED_PROMPT_NAME, feature_type_by_prompt, structured_type
    ) is structured_type
    assert _resolve_prompt_feature_type(
        LIVE_PROMPT_NAME, feature_type_by_prompt, structured_type
    ) is narrative_type
    assert _resolve_prompt_feature_type(
        "Situation Summary (Narrative)", feature_type_by_prompt, structured_type
    ) is narrative_type
    assert _resolve_prompt_feature_type(
        "Unknown Prompt", feature_type_by_prompt, structured_type
    ) is structured_type


def test_DEMO_PROVENANCE_002_partial_selection_balances_prompt_and_model():
    """Partial selection should choose one feature per prompt and per model when possible."""
    features = [
        SimpleNamespace(feature_id=10, type_id=1, llm_id=101),
        SimpleNamespace(feature_id=11, type_id=1, llm_id=202),
        SimpleNamespace(feature_id=12, type_id=2, llm_id=101),
        SimpleNamespace(feature_id=13, type_id=2, llm_id=202),
    ]

    selected = _select_balanced_partial_features(features)

    assert len(selected) == 2
    assert selected[0].type_id != selected[1].type_id
    assert selected[0].llm_id != selected[1].llm_id
