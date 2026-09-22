"""
Question-first co-pilot: the model answers decision questions first, the
label is derived from the answer key, and the explicit label is kept too.

Test IDs: [COPILOT_Q_001] through [COPILOT_Q_006]
"""

import pytest


QUESTIONS = {
    "enabled": True,
    "items": [
        {"id": "q1", "title": {"de": "Thema"}, "text": {"de": "Wessen Erleben?"},
         "options": [{"id": "S", "label": {"de": "Sprecher"}}, {"id": "G", "label": {"de": "Gegenüber"}}]},
        {"id": "q2", "title": {"de": "Präsupposition"}, "text": {"de": "Voraussetzen?"},
         "options": [{"id": "S", "label": {"de": "nein"}}, {"id": "G", "label": {"de": "ja"}}]},
        {"id": "q3", "title": {"de": "Bezugsrahmen"}, "text": {"de": "Wer ist Maßstab?"},
         "options": [{"id": "S", "label": {"de": "ich"}}, {"id": "G", "label": {"de": "geteilt"}}]},
    ],
    "mapping": {"SSS": "D", "GSS": "Q", "SGS": "A", "GGS": "I"},
}
ALLOWED = ["D", "Q", "A", "I", "R"]


def _cfg(questions=QUESTIONS, copilot=None):
    inner = {
        "mode": "single",
        "labels": [{"id": lid, "label": {"de": lid}} for lid in ALLOWED],
        "copilot": copilot or {"enabled": True, "prompt": "Label: {item}", "top_k": 2},
    }
    if questions is not None:
        inner["questions"] = questions
    return {"eval_config": {"type": "labeling", "config": inner}}


class TestCopilotQuestions:

    def test_COPILOT_Q_001_get_questions_config(self):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService

        q = LabelingCopilotService.get_questions_config(_cfg())
        assert [i["id"] for i in q["items"]] == ["q1", "q2", "q3"]
        assert q["mapping"]["GSS"] == "Q"
        assert LabelingCopilotService.get_questions_config(_cfg(questions=None)) is None
        assert LabelingCopilotService.get_questions_config(_cfg(questions={**QUESTIONS, "enabled": False})) is None

    def test_COPILOT_Q_002_questions_block_renders_questions_and_mapping(self):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService

        block = LabelingCopilotService.build_questions_block(
            LabelingCopilotService.get_questions_config(_cfg()))
        assert "1. q1 — Thema: Wessen Erleben?" in block
        assert "S = Sprecher / G = Gegenüber" in block
        assert "GSS → Q" in block

    def test_COPILOT_Q_003_validator_carries_answers_and_derived_label(self):
        from services.llm.llm_ai_task_runner import LLMAITaskRunner
        from services.evaluation.labeling_copilot_service import LabelingCopilotService

        q = LabelingCopilotService.get_questions_config(_cfg())
        payload = {"suggestions": [
            {"answers": {"q1": "g", "q2": "S", "q3": "S"}, "label_id": "Q", "confidence": "high"},
            {"answers": {"q1": "G", "q2": "G", "q3": "S"}, "label_id": "A"},  # explicit ≠ derived
        ]}
        out = LLMAITaskRunner._validate_copilot_payload(payload, ALLOWED, 2, q)
        assert out[0]["label_id"] == "Q"
        assert out[0]["answers"] == {"q1": "G", "q2": "S", "q3": "S"}
        assert out[0]["derived_label_id"] == "Q"
        assert out[0]["consistent"] is True
        # The explicit label wins; the divergence is recorded, not "fixed".
        assert out[1]["label_id"] == "A"
        assert out[1]["derived_label_id"] == "I"
        assert out[1]["consistent"] is False

    def test_COPILOT_Q_004_validator_tolerates_missing_or_bad_answers(self):
        from services.llm.llm_ai_task_runner import LLMAITaskRunner
        from services.evaluation.labeling_copilot_service import LabelingCopilotService

        q = LabelingCopilotService.get_questions_config(_cfg())
        payload = {"suggestions": [
            {"label_id": "D"},                                   # no answers at all
            {"answers": {"q1": "X", "q9": "S"}, "label_id": "R"},  # nothing usable
        ]}
        out = LLMAITaskRunner._validate_copilot_payload(payload, ALLOWED, 2, q)
        assert [s["label_id"] for s in out] == ["D", "R"]
        assert "answers" not in out[0] and "answers" not in out[1]
        # Incomplete answers: kept, but no key → no derived label.
        partial = {"suggestions": [{"answers": {"q1": "G"}, "label_id": "Q"}]}
        out = LLMAITaskRunner._validate_copilot_payload(partial, ALLOWED, 1, q)
        assert out[0]["answers"] == {"q1": "G"}
        assert out[0]["derived_label_id"] is None
        assert out[0]["consistent"] is None

    def test_COPILOT_Q_005_validator_unchanged_without_questions(self):
        from services.llm.llm_ai_task_runner import LLMAITaskRunner

        payload = {"suggestions": [{"answers": {"q1": "G"}, "label_id": "Q"}]}
        out = LLMAITaskRunner._validate_copilot_payload(payload, ALLOWED, 1)
        assert out == [{"label_id": "Q", "rationale": "", "evidence": "", "confidence": "medium"}]

    def test_COPILOT_Q_006_changing_questions_bumps_prompt_version(self):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService

        first = LabelingCopilotService.normalize_config_on_write(_cfg())
        v1 = first["eval_config"]["config"]["copilot"]["prompt_version"]
        same = LabelingCopilotService.normalize_config_on_write(_cfg(), previous_config=first)
        assert same["eval_config"]["config"]["copilot"]["prompt_version"] == v1

        changed = {**QUESTIONS, "mapping": {**QUESTIONS["mapping"], "GGG": "R"}}
        bumped = LabelingCopilotService.normalize_config_on_write(_cfg(questions=changed), previous_config=first)
        assert bumped["eval_config"]["config"]["copilot"]["prompt_version"] == v1 + 1
