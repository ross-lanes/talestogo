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
