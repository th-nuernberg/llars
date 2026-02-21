"""Unit tests for LLM model color generation."""

from db.models.llm_model import LLMModel, _hex_to_rgb, _rgb_distance_sq, _seed_color


def _min_distance_sq(color: str, existing_colors: list[str]) -> int:
    color_rgb = _hex_to_rgb(color)
    assert color_rgb is not None
    existing_rgbs = [rgb for rgb in (_hex_to_rgb(c) for c in existing_colors) if rgb]
    assert existing_rgbs
    return min(_rgb_distance_sq(color_rgb, existing_rgb) for existing_rgb in existing_rgbs)


def _build_llm_model(model_id: str, color: str) -> LLMModel:
    return LLMModel(
        model_id=model_id,
        display_name=model_id,
        provider='test',
        model_type=LLMModel.MODEL_TYPE_LLM,
        color=color,
        context_window=4096,
        max_output_tokens=1024,
        input_cost_per_million=0.0,
        output_cost_per_million=0.0,
        is_default=False,
        is_active=True,
    )


def test_LLM_COLOR_001_generate_color_stable_without_existing():
    """Color generation remains deterministic for the same model id."""
    model_id = 'test/provider/model-a'
    color_a = LLMModel.generate_color(model_id, existing_colors=[])
    color_b = LLMModel.generate_color(model_id, existing_colors=[])
    assert color_a == color_b


def test_LLM_COLOR_002_generate_color_maximizes_distance_to_existing():
    """Distance-aware generation should improve separation from existing colors."""
    model_id = 'test/provider/model-needs-spacing'
    seeded = _seed_color(model_id)
    existing = [seeded]

    generated = LLMModel.generate_color(model_id, existing_colors=existing)

    assert generated != seeded
    assert _min_distance_sq(generated, existing) > _min_distance_sq(seeded, existing)


def test_LLM_COLOR_003_get_assigned_colors_respects_exclude_model_id(app, db, app_context):
    """Existing DB colors are normalized and model exclusion is respected."""
    model_a = _build_llm_model('test/provider/model-1', '#AABBCC')
    model_b = _build_llm_model('test/provider/model-2', '#bbccdd')
    db.session.add(model_a)
    db.session.add(model_b)
    db.session.commit()

    all_colors = LLMModel.get_assigned_colors()
    assert '#AABBCC' in all_colors
    assert '#BBCCDD' in all_colors

    filtered = LLMModel.get_assigned_colors(exclude_model_id='test/provider/model-1')
    assert '#AABBCC' not in filtered
    assert '#BBCCDD' in filtered
