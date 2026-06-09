"""
Tests for GenericLLMClient — focused on the Azure code path and on the
validation guards that protect against missing Azure config.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.generic_llm_client import (
    GenericLLMClient,
    LLMAPIError,
    LLMConfigurationError,
)


class TestAzureValidation:
    def test_azure_missing_endpoint_raises(self):
        with pytest.raises(LLMConfigurationError, match="api_endpoint"):
            GenericLLMClient.call(
                api_type="azure",
                api_key="k",
                model_name="my-deployment",
                prompt="hi",
                api_version="2024-10-21",
            )

    def test_azure_missing_api_version_raises(self):
        with pytest.raises(LLMConfigurationError, match="api_version"):
            GenericLLMClient.call(
                api_type="azure",
                api_key="k",
                model_name="my-deployment",
                prompt="hi",
                api_endpoint="https://my.openai.azure.com/",
            )

    def test_unknown_api_type_raises(self):
        with pytest.raises(LLMConfigurationError, match="Unknown API type"):
            GenericLLMClient.call(
                api_type="bogus",
                api_key="k",
                model_name="m",
                prompt="hi",
            )


class TestAzureCall:
    @patch("app.services.generic_llm_client.AzureOpenAI")
    def test_azure_call_constructs_client_with_correct_args(self, mock_azure_cls):
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "azure response text"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
        mock_azure_cls.return_value = mock_client

        result = GenericLLMClient.call(
            api_type="azure",
            api_key="secret",
            model_name="gpt-4o-prod",
            prompt="hello",
            api_endpoint="https://my-resource.openai.azure.com/",
            api_version="2024-10-21",
            max_tokens=200,
            temperature=0.4,
        )

        assert result == "azure response text"

        # AzureOpenAI client must be constructed with the resource URL,
        # api_version, and api_key.
        mock_azure_cls.assert_called_once()
        kwargs = mock_azure_cls.call_args.kwargs
        assert kwargs["azure_endpoint"] == "https://my-resource.openai.azure.com/"
        assert kwargs["api_version"] == "2024-10-21"
        assert kwargs["api_key"] == "secret"

        # The chat.completions call should use the deployment name as the model.
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-prod"
        assert call_kwargs["max_tokens"] == 200
        assert call_kwargs["temperature"] == 0.4

    @patch("app.services.generic_llm_client.AzureOpenAI")
    def test_azure_call_wraps_sdk_errors(self, mock_azure_cls):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("boom")
        mock_azure_cls.return_value = mock_client

        with pytest.raises(LLMAPIError, match="Azure OpenAI API error"):
            GenericLLMClient.call(
                api_type="azure",
                api_key="k",
                model_name="m",
                prompt="hi",
                api_endpoint="https://x.openai.azure.com/",
                api_version="2024-10-21",
            )

    @patch("app.services.generic_llm_client.AzureOpenAI")
    def test_azure_call_raises_on_empty_choices(self, mock_azure_cls):
        """If Azure returns no choices (content filter / misconfig), raise cleanly
        instead of letting IndexError leak out."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(choices=[])
        mock_azure_cls.return_value = mock_client

        with pytest.raises(LLMAPIError, match="no choices"):
            GenericLLMClient.call(
                api_type="azure",
                api_key="k",
                model_name="m",
                prompt="hi",
                api_endpoint="https://x.openai.azure.com/",
                api_version="2024-10-21",
            )

    @patch("app.services.generic_llm_client.AzureOpenAI")
    def test_azure_call_handles_none_content(self, mock_azure_cls):
        """If Azure returns choices but content is None (refusal / tool_calls),
        return an empty string rather than letting None propagate."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
        mock_azure_cls.return_value = mock_client

        result = GenericLLMClient.call(
            api_type="azure",
            api_key="k",
            model_name="m",
            prompt="hi",
            api_endpoint="https://x.openai.azure.com/",
            api_version="2024-10-21",
        )
        assert result == ""


class TestWebSearchUnsupportedForAzure:
    def test_call_with_web_search_rejects_azure(self):
        with pytest.raises(LLMConfigurationError, match="does not support web search"):
            GenericLLMClient.call_with_web_search(
                api_type="azure",
                api_key="k",
                model_name="m",
                prompt="hi",
                api_endpoint="https://x.openai.azure.com/",
            )


# ==================== Bing Search v7 ====================

def _mock_bing_response(snippets):
    """Build a mock httpx.Response.json() return shape matching Bing v7."""
    return {
        "webPages": {
            "value": [
                {"name": title, "url": url, "snippet": text}
                for (title, url, text) in snippets
            ]
        }
    }


class TestBingV7Search:
    @patch("app.services.generic_llm_client.httpx.Client")
    def test_bing_v7_search_parses_results(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _mock_bing_response([
            ("Result A", "https://a.example", "snippet A"),
            ("Result B", "https://b.example", "snippet B"),
        ])
        mock_resp.raise_for_status.return_value = None
        mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

        results = GenericLLMClient._call_bing_v7_search(
            api_key="key", query="LLM news", api_endpoint="https://api.bing.microsoft.com/",
            timeout=10.0,
        )
        assert len(results) == 2
        assert results[0] == {"title": "Result A", "url": "https://a.example", "snippet": "snippet A"}

        # Confirm the correct URL was assembled and the API-key header was set.
        get_kwargs = mock_client_cls.return_value.__enter__.return_value.get.call_args.kwargs
        get_args = mock_client_cls.return_value.__enter__.return_value.get.call_args.args
        assert get_args[0] == "https://api.bing.microsoft.com/v7.0/search"
        assert get_kwargs["headers"]["Ocp-Apim-Subscription-Key"] == "key"
        assert get_kwargs["params"]["q"] == "LLM news"

    def test_format_bing_results_handles_empty(self):
        out = GenericLLMClient._format_bing_results_as_context([])
        assert "no search results" in out.lower()

    def test_format_bing_results_numbers_and_includes_urls(self):
        out = GenericLLMClient._format_bing_results_as_context([
            {"title": "T1", "url": "https://u1", "snippet": "S1"},
            {"title": "T2", "url": "https://u2", "snippet": "S2"},
        ])
        assert "[1]" in out and "[2]" in out
        assert "https://u1" in out and "https://u2" in out


class TestBingV7GroundedSynthesis:
    @patch("app.services.generic_llm_client.GenericLLMClient._call_bing_v7_search")
    def test_synthesis_distills_query_then_calls_analysis_provider(self, mock_search):
        """The full v7 path now does: distill → search → synthesize. The analysis
        provider gets called twice: once for distillation (short prompt), once
        for synthesis (the augmented prompt with Bing results)."""
        mock_search.return_value = [
            {"title": "T1", "url": "https://u1", "snippet": "S1"},
        ]
        analysis_provider = MagicMock()
        # Distillation returns a focused query; synthesis returns the final prose.
        analysis_provider.call.side_effect = ["LLM platform changes 2026", "synthesized prose"]

        result = GenericLLMClient._call_bing_v7_grounded_synthesis(
            bing_api_key="k",
            prompt="Long instruction about LLM platform changes ..." * 20,
            bing_endpoint="https://api.bing.microsoft.com/",
            analysis_provider=analysis_provider,
            timeout=10.0,
        )
        assert result == "synthesized prose"

        # Two calls: distill + synthesize.
        assert analysis_provider.call.call_count == 2

        # The distilled query (first call's return) is what got passed to Bing.
        mock_search.assert_called_once()
        assert mock_search.call_args.args[1] == "LLM platform changes 2026"

        # The synthesis prompt (second call) embeds the Bing results.
        synthesis_kwargs = analysis_provider.call.call_args_list[1].kwargs
        assert "T1" in synthesis_kwargs["prompt"]
        assert "[1]" in synthesis_kwargs["prompt"]

    @patch("app.services.generic_llm_client.GenericLLMClient._call_bing_v7_search")
    def test_synthesis_falls_back_to_truncated_prompt_if_distillation_fails(self, mock_search):
        """If the analysis provider errors during distillation, fall back to a
        truncated word-list of the original prompt rather than hard-failing."""
        mock_search.return_value = []
        analysis_provider = MagicMock()
        analysis_provider.call.side_effect = [
            RuntimeError("LLM transient error"),  # distillation fails
            "fallback synthesis",                  # synthesis still works
        ]

        result = GenericLLMClient._call_bing_v7_grounded_synthesis(
            bing_api_key="k",
            prompt="alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu",
            bing_endpoint="https://api.bing.microsoft.com/",
            analysis_provider=analysis_provider,
            timeout=10.0,
        )
        assert result == "fallback synthesis"

        # Fallback query = first 10 words of the prompt.
        mock_search.assert_called_once()
        assert mock_search.call_args.args[1] == "alpha beta gamma delta epsilon zeta eta theta iota kappa"


class TestBingV7EndpointNormalization:
    """Operators may paste the endpoint with or without /v7.0/search appended.
    The code must canonicalize without ever doubling up the path."""

    @pytest.mark.parametrize("endpoint", [
        "https://api.bing.microsoft.com",
        "https://api.bing.microsoft.com/",
        "https://api.bing.microsoft.com/v7.0",
        "https://api.bing.microsoft.com/v7.0/",
        "https://api.bing.microsoft.com/v7.0/search",
        "https://api.bing.microsoft.com/v7.0/search/",
    ])
    @patch("app.services.generic_llm_client.httpx.Client")
    def test_endpoint_normalizes_to_canonical_url(self, mock_client_cls, endpoint):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _mock_bing_response([])
        mock_resp.raise_for_status.return_value = None
        mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

        GenericLLMClient._call_bing_v7_search(
            api_key="k", query="q", api_endpoint=endpoint, timeout=10.0,
        )
        url = mock_client_cls.return_value.__enter__.return_value.get.call_args.args[0]
        assert url == "https://api.bing.microsoft.com/v7.0/search", (
            f"Endpoint {endpoint!r} normalized to {url!r}, expected canonical form"
        )


class TestBingV7Required:
    def test_bing_v7_requires_analysis_provider(self):
        with pytest.raises(LLMConfigurationError, match="analysis"):
            GenericLLMClient.call_with_web_search(
                api_type="bing_v7",
                api_key="k",
                model_name="bing",
                prompt="Q?",
                api_endpoint="https://api.bing.microsoft.com/",
                analysis_provider=None,
            )

    def test_bing_v7_requires_endpoint(self):
        with pytest.raises(LLMConfigurationError, match="api_endpoint"):
            GenericLLMClient.call_with_web_search(
                api_type="bing_v7",
                api_key="k",
                model_name="bing",
                prompt="Q?",
                analysis_provider=MagicMock(),
            )


# ==================== Azure AI Foundry — Bing Grounded ====================

class TestBingGroundedSDKGuard:
    def test_bing_grounded_raises_clear_error_when_sdk_missing(self, monkeypatch):
        """If the bing-grounded extra isn't installed, the user gets a clear
        message instead of an ImportError."""
        import app.services.generic_llm_client as glc
        monkeypatch.setattr(glc, "AZURE_AI_FOUNDRY_AVAILABLE", False)
        with pytest.raises(LLMConfigurationError, match="bing-grounded"):
            GenericLLMClient.call_with_web_search(
                api_type="bing_grounded",
                api_key="k",
                model_name="agent-id",
                prompt="Q?",
                api_endpoint="https://my-foundry.example/",
                api_version="2025-05-15-preview",
            )

    def test_bing_grounded_requires_endpoint(self, monkeypatch):
        # Even with the SDK present, no endpoint must fail with a clear error.
        import app.services.generic_llm_client as glc
        monkeypatch.setattr(glc, "AZURE_AI_FOUNDRY_AVAILABLE", True)
        with pytest.raises(LLMConfigurationError, match="api_endpoint"):
            GenericLLMClient.call_with_web_search(
                api_type="bing_grounded",
                api_key="k",
                model_name="agent-id",
                prompt="Q?",
            )


class TestBingGroundedAuth:
    """Bing Grounded supports two auth paths:
    - AzureKeyCredential when AZURE_FOUNDRY_API_KEY is set (key-based)
    - DefaultAzureCredential when no key (managed identity / az-login / SP env vars)
    """

    def _setup_sdk_mocks(self, monkeypatch):
        """Patch AIProjectClient, credentials, and the SDK-available flag.
        Returns (mock_project_client_cls, mock_key_cred_cls, mock_default_cred_cls).
        """
        import app.services.generic_llm_client as glc
        monkeypatch.setattr(glc, "AZURE_AI_FOUNDRY_AVAILABLE", True)

        mock_project_cls = MagicMock()
        mock_key_cred_cls = MagicMock()
        mock_default_cred_cls = MagicMock()

        monkeypatch.setattr(glc, "AIProjectClient", mock_project_cls, raising=False)
        monkeypatch.setattr(glc, "AzureKeyCredential", mock_key_cred_cls, raising=False)
        monkeypatch.setattr(glc, "DefaultAzureCredential", mock_default_cred_cls, raising=False)

        # Make the inner agent flow return a successful run with one assistant message.
        client = MagicMock()
        mock_project_cls.return_value = client
        # The `with client:` context manager hands back the client itself.
        client.__enter__.return_value = client
        client.__exit__.return_value = False

        thread = MagicMock(id="thread-1")
        client.agents.threads.create.return_value = thread

        run = MagicMock()
        run.status = "completed"
        client.agents.runs.create_and_process.return_value = run

        msg = MagicMock()
        msg.role = "assistant"
        msg.content = "agent response"
        client.agents.messages.list.return_value = [msg]

        return mock_project_cls, mock_key_cred_cls, mock_default_cred_cls

    def test_uses_azure_key_credential_when_api_key_set(self, monkeypatch):
        project_cls, key_cred_cls, default_cred_cls = self._setup_sdk_mocks(monkeypatch)

        GenericLLMClient.call_with_web_search(
            api_type="bing_grounded",
            api_key="secret-key",
            model_name="agent-id",
            prompt="Q?",
            api_endpoint="https://my-foundry.example/",
            api_version="2025-05-15-preview",
        )

        # AzureKeyCredential should be constructed with our key, and
        # DefaultAzureCredential should NOT be touched.
        key_cred_cls.assert_called_once_with("secret-key")
        default_cred_cls.assert_not_called()

    def test_falls_back_to_default_credential_when_no_key(self, monkeypatch):
        project_cls, key_cred_cls, default_cred_cls = self._setup_sdk_mocks(monkeypatch)

        GenericLLMClient.call_with_web_search(
            api_type="bing_grounded",
            api_key="",  # empty key → managed-identity path
            model_name="agent-id",
            prompt="Q?",
            api_endpoint="https://my-foundry.example/",
            api_version="2025-05-15-preview",
        )

        default_cred_cls.assert_called_once_with()
        key_cred_cls.assert_not_called()


class TestBingGroundedRunStatus:
    """Bing Grounded must verify the agent run actually completed — not just
    that it didn't fail. cancelled / expired / requires_action runs would
    return empty or stale messages."""

    @pytest.mark.parametrize("status", ["cancelled", "expired", "requires_action", None])
    def test_non_completed_status_raises(self, monkeypatch, status):
        import app.services.generic_llm_client as glc
        monkeypatch.setattr(glc, "AZURE_AI_FOUNDRY_AVAILABLE", True)

        mock_project_cls = MagicMock()
        monkeypatch.setattr(glc, "AIProjectClient", mock_project_cls, raising=False)
        monkeypatch.setattr(glc, "AzureKeyCredential", MagicMock(), raising=False)
        monkeypatch.setattr(glc, "DefaultAzureCredential", MagicMock(), raising=False)

        client = MagicMock()
        mock_project_cls.return_value = client
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.agents.threads.create.return_value = MagicMock(id="t1")

        run = MagicMock()
        run.status = status
        run.last_error = "transient failure"
        client.agents.runs.create_and_process.return_value = run

        with pytest.raises(LLMAPIError, match=str(status)):
            GenericLLMClient.call_with_web_search(
                api_type="bing_grounded",
                api_key="k",
                model_name="agent-id",
                prompt="Q?",
                api_endpoint="https://my-foundry.example/",
                api_version="2025-05-15-preview",
            )


class TestBingGroundedMessageExtraction:
    """No str(t) fallback — if a content block has no .text.value, skip it
    rather than returning the Python object repr as 'content'."""

    def test_skips_messagetext_block_without_value(self, monkeypatch):
        import app.services.generic_llm_client as glc
        monkeypatch.setattr(glc, "AZURE_AI_FOUNDRY_AVAILABLE", True)

        mock_project_cls = MagicMock()
        monkeypatch.setattr(glc, "AIProjectClient", mock_project_cls, raising=False)
        monkeypatch.setattr(glc, "AzureKeyCredential", MagicMock(), raising=False)
        monkeypatch.setattr(glc, "DefaultAzureCredential", MagicMock(), raising=False)

        client = MagicMock()
        mock_project_cls.return_value = client
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.agents.threads.create.return_value = MagicMock(id="t1")
        client.agents.runs.create_and_process.return_value = MagicMock(status="completed")

        # Build a message with two blocks: first has no .text.value, second does.
        first_block = MagicMock()
        first_block.text = MagicMock(spec=["whatever"])  # no .value attribute
        first_block.text.value = None  # explicit: no value

        second_block = MagicMock()
        second_block.text = MagicMock()
        second_block.text.value = "actual text content"

        msg = MagicMock()
        msg.role = "assistant"
        msg.content = [first_block, second_block]
        client.agents.messages.list.return_value = [msg]

        result = GenericLLMClient.call_with_web_search(
            api_type="bing_grounded",
            api_key="k",
            model_name="agent-id",
            prompt="Q?",
            api_endpoint="https://my-foundry.example/",
            api_version="2025-05-15-preview",
        )
        # Should return the second block's value, NOT a Python repr of the first.
        assert result == "actual text content"
        assert "<" not in result and "object at" not in result
