"""
Tests for GenerationWorker prompt rendering behavior.

Focus: Prompt Engineering block mapping for batch generation.
"""

from types import SimpleNamespace

from services.generation.generation_worker import GenerationWorker


def _make_user_prompt(blocks):
    return SimpleNamespace(
        prompt_id=123,
        rendered_content={"blocks": blocks},
        content=None,
    )


def test_render_user_prompt_system_block_detected_by_title():
    worker = GenerationWorker(job_id=1)
    user_prompt = _make_user_prompt(
        {
            "intro_block": {"title": "Intro", "position": 0, "content": "Einleitung"},
            "a1b2c3": {"title": " System ", "position": 1, "content": "Du bist streng."},
            "task_block": {"title": "Task", "position": 2, "content": "Bewerte {{input}}"},
        }
    )

    system_prompt, user_prompt_text = worker._render_user_prompt(
        user_prompt,
        {"input": "diesen Text"},
    )

    assert system_prompt == "Du bist streng."
    assert user_prompt_text == "Einleitung\n\nBewerte diesen Text"


def test_render_user_prompt_system_block_detected_by_legacy_block_id():
    worker = GenerationWorker(job_id=1)
    user_prompt = _make_user_prompt(
        {
            "system": {"title": "Anweisung", "position": 0, "content": "Systemrolle"},
            "user_part": {"title": "Frage", "position": 1, "content": "Antwort auf {{input}}"},
        }
    )

    system_prompt, user_prompt_text = worker._render_user_prompt(
        user_prompt,
        {"input": "X"},
    )

    assert system_prompt == "Systemrolle"
    assert user_prompt_text == "Antwort auf X"


def test_render_user_prompt_combines_multiple_system_blocks_and_keeps_user_blocks():
    worker = GenerationWorker(job_id=1)
    user_prompt = _make_user_prompt(
        {
            "system": {"title": "System", "position": 0, "content": "Regel A"},
            "context": {"title": "Context", "position": 1, "content": "Kontext"},
            "secondary": {"title": "SYSTEM", "position": 2, "content": "Regel B"},
            "task": {"title": "Task", "position": 3, "content": "Aufgabe"},
        }
    )

    system_prompt, user_prompt_text = worker._render_user_prompt(user_prompt, {})

    assert system_prompt == "Regel A\n\nRegel B"
    assert user_prompt_text == "Kontext\n\nAufgabe"


def test_render_user_prompt_uses_prompt_engineering_variable_defaults_when_runtime_empty():
    worker = GenerationWorker(job_id=1)
    user_prompt = _make_user_prompt(
        {
            "system": {"title": "System", "position": 0, "content": "Rolle: {{role_name}}"},
            "task": {"title": "Task", "position": 1, "content": "Antwort in {{language}}."},
        }
    )
    user_prompt.rendered_content["variables"] = {
        "role_name": {"content": "Fachberater"},
        "language": {"content": "Deutsch"},
    }

    # Simulate prompt-only runtime values: aliases exist but are empty.
    system_prompt, user_prompt_text = worker._render_user_prompt(
        user_prompt,
        {"input": "", "content": "", "language": ""},
    )

    assert system_prompt == "Rolle: Fachberater"
    assert user_prompt_text == "Antwort in Deutsch."
