"""Unit tests for demo video data service."""

from db.models.llm_model import LLMModel
from services.demo_video_service import _color_distance_sq, _ensure_demo_model_color_contrast


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
