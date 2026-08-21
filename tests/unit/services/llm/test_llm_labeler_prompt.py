"""Tests that the LLM labeler (_run_text_classification) hands the model the
CORRECT task for wizard-created labeling scenarios.

Regression guard for scenario 660 "Survey Screening": the runner was sending the
model bare category ids ("cat_1782...") with no meaning AND dropping the task
description + inclusion criteria (they live under eval_config.config.*Markdown,
which the old top-level guidance builder never read). This asserts the assembled
prompt now carries the human label names (include/exclude), the unsure option,
the task description and the criteria — and that a category-id answer is stored.

Test IDs: LABELTASK_001..004
"""

from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest


# Minimal shape mirroring scenario 660's config_json (wizard/nested layout).
CONFIG_660 = {
    "enable_llm_evaluation": True,
    "eval_type": "labeling",
    "eval_config": {
        "config": {
            "allowUnsure": True,
            "categories": [
                {"id": "cat_inc", "name": {"de": "include", "en": "include"}},
                {"id": "cat_exc", "name": {"de": "exclude", "en": "exclude"}},
            ],
            "unsureOption": {"id": "unsure", "name": {"de": "uncertain", "en": "uncertain"}},
            "taskDescriptionMarkdown": {
                "de": "Entscheide fuer jede Arbeit, ob sie EINGESCHLOSSEN oder AUSGESCHLOSSEN wird.",
                "en": "",
            },
            "criteriaMarkdown": {
                "de": "1. LLM-basiert: nutzt ein Large Language Model.\n2. Simulierter Gespraechspartner.",
                "en": "",
            },
            "type": "multiclass",
        },
        "presetId": "custom",
    },
}


def _create_function_type(db, ftype_id=7, name="labeling"):
    from db.models.scenario import FeatureFunctionType
    if FeatureFunctionType.query.get(ftype_id):
        return
    db.session.add(FeatureFunctionType(function_type_id=ftype_id, name=name))
    db.session.flush()


def _create_scenario(db, config):
    from db.models.scenario import RatingScenarios
    _create_function_type(db)
    s = RatingScenarios(
        scenario_name="Survey Screening", function_type_id=7,
        config_json=config, created_by="creator",
    )
    db.session.add(s)
    db.session.flush()
    return s


def _create_item_with_text(db, scenario, text):
    from db.models.scenario import EvaluationItem, ScenarioItems, Message
    it = EvaluationItem(subject="Paper", chat_id=1)
    db.session.add(it)
    db.session.flush()
    db.session.add(ScenarioItems(scenario_id=scenario.id, item_id=it.item_id))
    db.session.add(Message(
        item_id=it.item_id, sender="paper",
        content=text, timestamp=datetime(2026, 1, 1),
    ))
    db.session.flush()
    return it


def _run_capture(db, scenario, item, answer_label="cat_inc"):
    """Run the labeler with the LLM call mocked; return the captured prompt +
    the stored LLMTaskResult payload."""
    from services.llm import llm_ai_task_runner as mod
    from services.llm.llm_ai_task_runner import LLMAITaskRunner

    captured = {}

    def fake_request_json(client, api_model_id, system_prompt, user_prompt, trace=None):
        captured["system"] = system_prompt
        captured["user"] = user_prompt
        return (
            {"label": answer_label, "confidence": 4, "reasoning": "matches criteria"},
            '{"label": "%s"}' % answer_label,
        )

    with patch.object(
        mod.LLMClientFactory, "resolve_client_and_model_id",
        return_value=(MagicMock(), "mistralai/Mistral-Medium-3.5-128B"),
    ), patch.object(LLMAITaskRunner, "_request_json", side_effect=fake_request_json), \
            patch.object(mod, "_broadcast_task_completed", lambda *a, **k: None), \
            patch.object(mod, "_broadcast_model_aborted", lambda *a, **k: None):
        LLMAITaskRunner._run_text_classification(
            "Global/Mistral/Mistral-Medium-3.5-128B",
            [item.item_id], scenario.id, scenario, task_type="labeling",
        )
    return captured


class TestLabelerPrompt:

    def test_LABELTASK_001_prompt_has_label_names_not_just_ids(self, app, db):
        scenario = _create_scenario(db, CONFIG_660)
        item = _create_item_with_text(db, scenario, "Title: An LLM simulated patient. Abstract: ...")
        cap = _run_capture(db, scenario, item)
        prompt = cap["user"]
        # Ids are the answer space (align with human category_id) ...
        assert "cat_inc" in prompt and "cat_exc" in prompt
        # ... but their MEANING must be present so the model isn't guessing.
        assert "include" in prompt
        assert "exclude" in prompt
        assert "uncertain" in prompt  # allowUnsure mirrored

    def test_LABELTASK_002_prompt_has_task_and_criteria(self, app, db):
        scenario = _create_scenario(db, CONFIG_660)
        item = _create_item_with_text(db, scenario, "some paper text")
        prompt = _run_capture(db, scenario, item)["user"]
        assert "EINGESCHLOSSEN" in prompt          # task description reached the model
        assert "LLM-basiert" in prompt             # inclusion criteria reached the model
        assert "Simulierter Gespraechspartner" in prompt

    def test_LABELTASK_003_item_text_included(self, app, db):
        scenario = _create_scenario(db, CONFIG_660)
        item = _create_item_with_text(db, scenario, "UNIQUE_PAPER_MARKER_42")
        prompt = _run_capture(db, scenario, item)["user"]
        assert "UNIQUE_PAPER_MARKER_42" in prompt

    def test_LABELTASK_004_category_id_answer_is_stored(self, app, db):
        from db.models import LLMTaskResult
        scenario = _create_scenario(db, CONFIG_660)
        item = _create_item_with_text(db, scenario, "paper")
        _run_capture(db, scenario, item, answer_label="cat_exc")
        row = LLMTaskResult.query.filter_by(
            scenario_id=scenario.id, thread_id=item.item_id, task_type="labeling"
        ).first()
        assert row is not None
        assert row.payload_json["label"] == "cat_exc"

    def test_LABELTASK_006_labels_as_dicts_with_label_key(self, app, db):
        """Scenario 629 shape: top-level config.labels is a list of dicts using
        the 'label' key (not 'name') for the localized text. The old code took
        only strings from that list -> fell back to positive/negative/neutral."""
        from services.llm.llm_ai_task_runner import LLMAITaskRunner
        cfg = {
            "type": "labeling",
            "labels": [
                {"id": "stress", "label": {"de": "Stress / Überforderung", "en": "Stress"}},
                {"id": "grief", "label": {"de": "Trauer", "en": "Grief"}},
            ],
        }
        labels, descs = LLMAITaskRunner._extract_labels_from_config(cfg)
        assert labels == ["stress", "grief"]           # ids (align with human category_id)
        assert descs["stress"] == "Stress / Überforderung"
        assert descs["grief"] == "Trauer"

    def test_LABELTASK_007_plain_string_labels(self, app, db):
        from services.llm.llm_ai_task_runner import LLMAITaskRunner
        labels, descs = LLMAITaskRunner._extract_labels_from_config({"labels": ["a", "b", "c"]})
        assert labels == ["a", "b", "c"]
        assert descs == {}

    def test_LABELTASK_008_no_labels_falls_back_to_default(self, app, db):
        from services.llm.llm_ai_task_runner import LLMAITaskRunner
        labels, _ = LLMAITaskRunner._extract_labels_from_config({"type": "labeling"})
        assert labels == ["positive", "negative", "neutral"]

    def test_LABELTASK_009_629_shape_prompt_uses_topic_labels(self, app, db):
        """End-to-end: a 629-like config must send the topic labels + names, not
        the positive/negative/neutral default."""
        cfg = {
            "type": "labeling",
            "labels": [
                {"id": "stress", "label": {"de": "Stress / Überforderung"}},
                {"id": "grief", "label": {"de": "Trauer"}},
            ],
            "eval_config": {"config": {
                "labels": [
                    {"id": "stress", "label": {"de": "Stress / Überforderung"}},
                    {"id": "grief", "label": {"de": "Trauer"}},
                ],
                "task_description_markdown": {"de": "Ordne dem Text ein Beratungsthema zu."},
            }, "type": "labeling"},
        }
        scenario = _create_scenario(db, cfg)
        item = _create_item_with_text(db, scenario, "Ich bin total überfordert mit allem.")
        prompt = _run_capture(db, scenario, item, answer_label="stress")["user"]
        assert '"stress"' in prompt and '"grief"' in prompt
        assert "Stress / Überforderung" in prompt
        assert "Beratungsthema" in prompt              # task description reached the model
        assert "positive" not in prompt                # NOT the default fallback

    def test_LABELTASK_005_old_guidance_builder_missed_nested_config(self, app, db):
        """Documents the original bug: the generic (top-level) guidance builder
        returns nothing for the nested wizard config — which is why the fallback
        to the briefing resolver was needed."""
        from services.llm.llm_ai_task_runner import LLMAITaskRunner
        assert LLMAITaskRunner._build_scenario_guidance_block_from_config(CONFIG_660) == ""
        task, criteria = LLMAITaskRunner._get_scenario_briefing_prompt_settings_from_config(CONFIG_660)
        assert "EINGESCHLOSSEN" in task
        assert "LLM-basiert" in criteria
