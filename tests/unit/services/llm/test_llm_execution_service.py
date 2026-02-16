from types import SimpleNamespace

from services.llm.llm_execution_service import LLMExecutionService


class _FakeCompletions:
    def __init__(self, side_effects):
        self._side_effects = list(side_effects)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(dict(kwargs))
        effect = self._side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect


class _FakeClient:
    def __init__(self, side_effects):
        self.chat = SimpleNamespace(completions=_FakeCompletions(side_effects))


def _ok_response():
    return SimpleNamespace(choices=[], usage=None)


def test_build_chat_completion_params_drops_sampling_for_gpt5():
    params = LLMExecutionService.build_chat_completion_params(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": "hi"}],
        stream=False,
        temperature=0.2,
        top_p=0.8,
        max_tokens=123,
    )

    assert "temperature" not in params
    assert "top_p" not in params
    assert params["max_tokens"] == 123


def test_execute_chat_completion_retries_without_temperature_on_unsupported_error():
    LLMExecutionService.clear_param_fix_hints()
    err = Exception(
        "Unsupported value: 'temperature' does not support 0.2 with this model. "
        "Only the default (1) value is supported."
    )
    client = _FakeClient([err, _ok_response()])

    LLMExecutionService.execute_chat_completion(
        client,
        model="custom-model",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.2,
        model_key="custom-model",
    )

    assert len(client.chat.completions.calls) == 2
    assert "temperature" in client.chat.completions.calls[0]
    assert "temperature" not in client.chat.completions.calls[1]


def test_execute_chat_completion_drops_max_tokens_when_provider_rejects_it():
    LLMExecutionService.clear_param_fix_hints()
    err = Exception("Unsupported parameter: 'max_tokens'. Use 'max_completion_tokens' instead.")
    client = _FakeClient([err, _ok_response()])

    LLMExecutionService.execute_chat_completion(
        client,
        model="some-openai-model",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=200,
        model_key="some-openai-model",
    )

    assert len(client.chat.completions.calls) == 2
    assert "max_tokens" in client.chat.completions.calls[0]
    assert "max_tokens" not in client.chat.completions.calls[1]

    # Hint should be remembered for the same model key.
    second_client = _FakeClient([_ok_response()])
    LLMExecutionService.execute_chat_completion(
        second_client,
        model="some-openai-model",
        messages=[{"role": "user", "content": "again"}],
        max_tokens=200,
        model_key="some-openai-model",
    )
    assert "max_tokens" not in second_client.chat.completions.calls[0]
