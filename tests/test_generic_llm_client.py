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
    def test_synthesis_calls_analysis_provider_with_augmented_prompt(self, mock_search):
        mock_search.return_value = [
            {"title": "T1", "url": "https://u1", "snippet": "S1"},
        ]
        analysis_provider = MagicMock()
        analysis_provider.call.return_value = "synthesized prose"

        result = GenericLLMClient._call_bing_v7_grounded_synthesis(
            bing_api_key="k", prompt="Q?", bing_endpoint="https://api.bing.microsoft.com/",
            analysis_provider=analysis_provider, timeout=10.0,
        )
        assert result == "synthesized prose"

        analysis_provider.call.assert_called_once()
        call_kwargs = analysis_provider.call.call_args.kwargs
        # The augmented prompt should contain both the original question and
        # the formatted Bing results.
        assert "Q?" in call_kwargs["prompt"]
        assert "T1" in call_kwargs["prompt"]
        assert "[1]" in call_kwargs["prompt"]

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
