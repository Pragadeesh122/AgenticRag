import unittest
from unittest.mock import patch

from llm.client import _ChatCompletionsFacade


class _DummyProvider:
    def __init__(self, name: str, chunks: list[dict]):
        self.name = name
        self._chunks = chunks
        self.calls: list[dict] = []

    def chat_completion(self, **kwargs):
        self.calls.append(kwargs)
        return iter(self._chunks)


class _Resolved:
    def __init__(self, provider, model: str):
        self.provider = provider
        self.model = model


class _Registry:
    def __init__(self, provider, model: str):
        self._provider = provider
        self._model = model

    def resolve_chat(self, _model):
        return _Resolved(self._provider, self._model)


class LLMStreamInstrumentationTests(unittest.TestCase):
    @patch("llm.client.estimate_cost_usd", return_value=0.002)
    @patch("llm.client.observe_llm_output_speed")
    @patch("llm.client.observe_llm_outcome")
    @patch("llm.client.observe_llm_ttft")
    def test_openai_stream_emits_ttft_and_final_usage(
        self,
        ttft_mock,
        outcome_mock,
        speed_mock,
        _cost_mock,
    ):
        chunks = [
            {"choices": [{"delta": {"content": "Hello"}}]},
            {
                "choices": [{"delta": {}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 7},
            },
        ]
        provider = _DummyProvider("openai", chunks)
        facade = _ChatCompletionsFacade(_Registry(provider, "gpt-5.4-mini"))

        stream = facade.create(messages=[{"role": "user", "content": "hi"}], stream=True)
        list(stream)

        self.assertEqual(provider.calls[0]["stream_options"], {"include_usage": True})
        ttft_mock.assert_called_once()
        speed_mock.assert_called_once()
        outcome_mock.assert_called_once()
        self.assertEqual(outcome_mock.call_args.kwargs["status"], "success")
        self.assertTrue(outcome_mock.call_args.kwargs["stream"])
        self.assertEqual(
            outcome_mock.call_args.kwargs["usage"],
            {"prompt_tokens": 11, "completion_tokens": 7},
        )

    @patch("llm.client.estimate_cost_usd", return_value=None)
    @patch("llm.client.observe_llm_output_speed")
    @patch("llm.client.observe_llm_outcome")
    @patch("llm.client.observe_llm_ttft")
    def test_non_supported_provider_skips_stream_options_and_handles_usage_missing(
        self,
        ttft_mock,
        outcome_mock,
        speed_mock,
        _cost_mock,
    ):
        chunks = [
            {"choices": [{"delta": {"content": "Hello"}}]},
            {"choices": [{"delta": {}}]},
        ]
        provider = _DummyProvider("anthropic", chunks)
        facade = _ChatCompletionsFacade(_Registry(provider, "claude-haiku-4-5"))

        stream = facade.create(
            messages=[{"role": "user", "content": "hi"}],
            stream=True,
        )
        list(stream)

        self.assertNotIn("stream_options", provider.calls[0])
        ttft_mock.assert_called_once()
        speed_mock.assert_not_called()
        outcome_mock.assert_called_once()
        self.assertEqual(outcome_mock.call_args.kwargs["status"], "usage_missing")
        self.assertIsNone(outcome_mock.call_args.kwargs["usage"])

