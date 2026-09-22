"""
Unit tests for LabelingCopilotService.update_labeling_settings — the merge
behind ``PUT /api/v1/scenarios/<id>/labeling-config`` (question-first
labeling + second choice, switchable headlessly via API key).

Test IDs: LABEL_SET_001..013
"""

from __future__ import annotations

import pytest

from services.evaluation.labeling_copilot_service import LabelingCopilotService


def _questions(mapping=None):
    return {
        "enabled": True,
        "sliders": True,
        "items": [
            {
                "id": "q1",
                "title": {"de": "Thema", "en": "Topic"},
                "text": {"de": "Wessen Erleben?", "en": "Whose experience?"},
                "options": [
                    {"id": "S", "label": {"de": "Sprecher:in", "en": "Speaker"}},
                    {"id": "G", "label": {"de": "Gegenüber", "en": "Other"}},
                ],
            }
        ],
        "mapping": mapping if mapping is not None else {"S": "D", "G": "R"},
    }


def _wizard_config():
    # wizard layout: {eval_config: {type, config: {...}}} — the layout of the
    # VRM study scenario 758
    return {
        "eval_config": {
            "type": "conversation_labeling",
            "config": {
                "mode": "single",
                "labels": [{"id": "D", "name": {"de": "D"}}, {"id": "R", "name": {"de": "R"}}],
            },
        }
    }


def _v1_config():
    # api_v1 layout mirrors the inner config at config.config
    inner = {"mode": "single", "labels": [{"id": "D"}, {"id": "R"}]}
    return {"eval_config": {"type": "labeling", "config": dict(inner)}, "config": dict(inner)}


class TestUpdateLabelingSettings:
    def test_LABEL_SET_001_sets_questions_and_second_choice_in_inner_config(self):
        out = LabelingCopilotService.update_labeling_settings(
            _wizard_config(), {"questions": _questions(), "second_choice": True}
        )
        inner = out["eval_config"]["config"]
        assert inner["second_choice"] is True
        assert inner["questions"]["items"][0]["id"] == "q1"
        assert inner["questions"]["mapping"] == {"S": "D", "G": "R"}
        # defaults filled by the schema
        assert inner["questions"]["direct_selection"] is True

    def test_LABEL_SET_002_does_not_mutate_input(self):
        cfg = _wizard_config()
        LabelingCopilotService.update_labeling_settings(cfg, {"second_choice": True})
        assert "second_choice" not in cfg["eval_config"]["config"]

    def test_LABEL_SET_003_mirrors_into_config_config_for_v1_layout(self):
        out = LabelingCopilotService.update_labeling_settings(
            _v1_config(), {"questions": _questions(), "second_choice": True}
        )
        assert out["eval_config"]["config"]["second_choice"] is True
        assert out["config"]["second_choice"] is True
        assert out["config"]["questions"]["mapping"] == {"S": "D", "G": "R"}

    def test_LABEL_SET_004_none_removes_questions(self):
        cfg = LabelingCopilotService.update_labeling_settings(
            _wizard_config(), {"questions": _questions()}
        )
        out = LabelingCopilotService.update_labeling_settings(cfg, {"questions": None})
        assert "questions" not in out["eval_config"]["config"]

    def test_LABEL_SET_005_rejects_mapping_to_unknown_label(self):
        with pytest.raises(ValueError, match="unknown labels.*X"):
            LabelingCopilotService.update_labeling_settings(
                _wizard_config(), {"questions": _questions({"S": "D", "G": "X"})}
            )

    def test_LABEL_SET_006_rejects_unknown_fields_empty_body_and_bad_types(self):
        with pytest.raises(ValueError, match="Unknown fields"):
            LabelingCopilotService.update_labeling_settings(_wizard_config(), {"mode": "multi"})
        with pytest.raises(ValueError, match="questions, second_choice and/or labels"):
            LabelingCopilotService.update_labeling_settings(_wizard_config(), {})
        with pytest.raises(ValueError, match="boolean"):
            LabelingCopilotService.update_labeling_settings(_wizard_config(), {"second_choice": "yes"})
        # schema violation: a question needs exactly two options
        bad = _questions()
        bad["items"][0]["options"] = bad["items"][0]["options"][:1]
        with pytest.raises(ValueError, match="questions:"):
            LabelingCopilotService.update_labeling_settings(_wizard_config(), {"questions": bad})

    def test_LABEL_SET_007_rejects_config_without_labeling_block(self):
        with pytest.raises(ValueError, match="no labeling config"):
            LabelingCopilotService.update_labeling_settings({}, {"second_choice": True})


class TestCopilotMirror:
    def test_LABEL_SET_013_keeps_the_copilot_mirror_in_sync(self):
        """The v1 layout holds the inner config twice. A copilot block that is
        bumped in one copy and stale in the other is a trap: the VRM study ran
        with authoritative prompt_version 3 and mirror 1."""
        cfg = _v1_config()
        cfg["eval_config"]["config"]["copilot"] = {"prompt": "erste Fassung", "enabled": True}
        cfg["config"]["copilot"] = {"prompt": "erste Fassung", "enabled": True}
        first = LabelingCopilotService.normalize_config_on_write(cfg, None)
        assert first["config"]["copilot"] == first["eval_config"]["config"]["copilot"]

        changed = LabelingCopilotService.update_labeling_settings(first, {"questions": _questions()})
        out = LabelingCopilotService.normalize_config_on_write(changed, first)
        auth, mirror = out["eval_config"]["config"]["copilot"], out["config"]["copilot"]
        assert auth["prompt_version"] == 2, "changed questions must bump the version"
        assert mirror == auth, "the mirror must not lag behind the authoritative block"


class TestLabelPatches:
    """``labels`` merges by id — the path that carries the codebook text
    (``rule``/``anchors``) to the label buttons of a running study."""

    def _labelled_config(self):
        cfg = _wizard_config()
        cfg["eval_config"]["config"]["labels"] = [
            {"id": "K", "label": {"de": "K — Acknowledgement", "en": "K — Acknowledgment"},
             "description": {"de": "alt", "en": "old"}, "color": "#E8C4A0"},
            {"id": "D", "label": {"de": "D — Disclosure", "en": "D — Disclosure"}},
        ]
        return cfg

    def _labels_of(self, config):
        return LabelingCopilotService.locate_inner_config(config)["labels"]

    def test_LABEL_SET_008_merges_one_label_and_leaves_the_others_alone(self):
        out = LabelingCopilotService.update_labeling_settings(
            self._labelled_config(),
            {"labels": [{"id": "K",
                         "description": {"de": "neu", "en": "new"},
                         "rule": {"de": "Ersetzungstest", "en": "Swap test"},
                         "anchors": {"de": ["„Guten Tag Susanne“"], "en": ["“Hello.”"]}}]},
        )
        labels = {lbl["id"]: lbl for lbl in self._labels_of(out)}
        assert labels["K"]["description"]["de"] == "neu"
        assert labels["K"]["rule"]["en"] == "Swap test"
        assert labels["K"]["anchors"]["de"] == ["„Guten Tag Susanne“"]
        # untouched fields survive the patch, and so does the other label
        assert labels["K"]["color"] == "#E8C4A0"
        assert labels["K"]["label"]["de"] == "K — Acknowledgement"
        assert labels["D"] == {"id": "D", "label": {"de": "D — Disclosure", "en": "D — Disclosure"}}

    def test_LABEL_SET_009_keeps_the_label_order(self):
        out = LabelingCopilotService.update_labeling_settings(
            self._labelled_config(),
            {"labels": [{"id": "D", "description": {"de": "x", "en": "x"}}]},
        )
        assert [lbl["id"] for lbl in self._labels_of(out)] == ["K", "D"]

    def test_LABEL_SET_010_refuses_an_unknown_label_id(self):
        # A study must not gain a category through a typo — votes reference ids.
        with pytest.raises(ValueError, match="unknown label id 'Z'"):
            LabelingCopilotService.update_labeling_settings(
                self._labelled_config(), {"labels": [{"id": "Z", "label": {"de": "Z", "en": "Z"}}]})

    def test_LABEL_SET_011_refuses_empty_list_and_patches_without_id(self):
        with pytest.raises(ValueError, match="non-empty list"):
            LabelingCopilotService.update_labeling_settings(
                self._labelled_config(), {"labels": []})
        with pytest.raises(ValueError, match="needs an id"):
            LabelingCopilotService.update_labeling_settings(
                self._labelled_config(), {"labels": [{"description": {"de": "x", "en": "x"}}]})

    def test_LABEL_SET_012_validates_the_merged_label_against_the_schema(self):
        # description is a LocalizedString — a bare string must not slip through,
        # or an English rater silently reads German.
        with pytest.raises(ValueError, match="labels\\[K\\]"):
            LabelingCopilotService.update_labeling_settings(
                self._labelled_config(), {"labels": [{"id": "K", "description": "nur deutsch"}]})
