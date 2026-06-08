"""
Generic LLM Client for Tales Project

Routes API calls to different LLM providers based on configuration.
Supports OpenAI, Anthropic, Google (Gemini), Azure OpenAI, and OpenAI-compatible APIs.
"""

import os
from typing import Optional
import httpx

# Import LLM SDKs
try:
    from openai import OpenAI, AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    pass


class LLMConfigurationError(LLMClientError):
    """Raised when LLM is not properly configured."""
    pass


class LLMAPIError(LLMClientError):
    """Raised when LLM API call fails."""
    pass


class GenericLLMClient:
    """
    Generic client for calling different LLM APIs.

    Supported api_type values:
    - "openai": OpenAI API (GPT models)
    - "anthropic": Anthropic API (Claude models)
    - "google": Google GenAI API (Gemini models)
    - "azure": Azure OpenAI (requires api_endpoint + api_version; model_name is the deployment name)
    - "openai_compatible": Any OpenAI-compatible API (Perplexity, local models, etc.)
    """

    # Default timeout for API calls (4 minutes for web search models)
    DEFAULT_TIMEOUT = 240.0

    @staticmethod
    def call(
        api_type: str,
        api_key: str,
        model_name: str,
        prompt: str,
        api_endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        timeout: float = DEFAULT_TIMEOUT
    ) -> str:
        """
        Call an LLM API and return the response text.

        Args:
            api_type: One of "openai", "anthropic", "google", "openai_compatible"
            api_key: The decrypted API key
            model_name: The model to use (e.g., "gpt-4o", "claude-3-haiku-20240307")
            prompt: The prompt to send
            api_endpoint: Custom endpoint URL (required for openai_compatible)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            timeout: Request timeout in seconds

        Returns:
            The response text from the LLM

        Raises:
            LLMConfigurationError: If the API type is not supported or misconfigured
            LLMAPIError: If the API call fails
        """
        if api_type == "openai":
            return GenericLLMClient._call_openai(
                api_key, model_name, prompt, max_tokens, temperature, timeout
            )
        elif api_type == "anthropic":
            return GenericLLMClient._call_anthropic(
                api_key, model_name, prompt, max_tokens, temperature, timeout
            )
        elif api_type == "google":
            return GenericLLMClient._call_google(
                api_key, model_name, prompt, max_tokens, temperature, timeout
            )
        elif api_type == "azure":
            if not api_endpoint:
                raise LLMConfigurationError(
                    "api_endpoint (Azure resource URL) is required for azure API type"
                )
            if not api_version:
                raise LLMConfigurationError(
                    "api_version is required for azure API type (e.g., '2024-10-21')"
                )
            return GenericLLMClient._call_azure(
                api_key, model_name, prompt, api_endpoint, api_version,
                max_tokens, temperature, timeout
            )
        elif api_type == "openai_compatible":
            if not api_endpoint:
                raise LLMConfigurationError(
                    "api_endpoint is required for openai_compatible API type"
                )
            return GenericLLMClient._call_openai_compatible(
                api_key, model_name, prompt, api_endpoint, max_tokens, temperature, timeout
            )
        else:
            raise LLMConfigurationError(f"Unknown API type: {api_type}")

    @staticmethod
    def call_with_web_search(
        api_type: str,
        api_key: str,
        model_name: str,
        prompt: str,
        api_endpoint: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT
    ) -> str:
        """
        Call an LLM API with web search grounding (for State of the LLMs feature).

        Only supported for:
        - "google": Uses Google Search grounding tool
        - "openai_compatible" with Perplexity: Uses sonar model's built-in search

        Azure OpenAI is intentionally NOT supported here. Azure-only deployments
        gracefully omit the "State of the LLMs" report section (the caller in
        scripts/admin/generate_report.py handles this by returning a "Skipped"
        status that the report orchestrator reads to skip the section entirely).
        To re-enable web search, configure a Gemini or Perplexity provider
        alongside Azure.

        Args:
            api_type: One of "google", "openai_compatible"
            api_key: The decrypted API key
            model_name: The model to use
            prompt: The prompt to send
            api_endpoint: Custom endpoint URL (for Perplexity)
            timeout: Request timeout in seconds

        Returns:
            The response text from the LLM

        Raises:
            LLMConfigurationError: If the API type does not support web search
            LLMAPIError: If the API call fails
        """
        if api_type == "google":
            return GenericLLMClient._call_google_with_grounding(
                api_key, model_name, prompt, timeout
            )
        elif api_type == "openai_compatible":
            # Perplexity sonar model has built-in web search
            if not api_endpoint:
                raise LLMConfigurationError(
                    "api_endpoint is required for openai_compatible API type"
                )
            return GenericLLMClient._call_openai_compatible(
                api_key, model_name, prompt, api_endpoint, max_tokens=4000, temperature=0.7, timeout=timeout
            )
        else:
            raise LLMConfigurationError(
                f"API type '{api_type}' does not support web search. "
                "Only 'google' and 'openai_compatible' (Perplexity) support web search."
            )

    @staticmethod
    def _call_openai(
        api_key: str,
        model_name: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
        timeout: float
    ) -> str:
        """Call OpenAI API (GPT models)."""
        if not OPENAI_AVAILABLE:
            raise LLMConfigurationError("OpenAI SDK not installed. Run: pip install openai")

        try:
            http_client = httpx.Client(timeout=timeout)
            client = OpenAI(api_key=api_key, http_client=http_client)

            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content

        except Exception as e:
            raise LLMAPIError(f"OpenAI API error: {str(e)}")

    @staticmethod
    def _call_anthropic(
        api_key: str,
        model_name: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
        timeout: float
    ) -> str:
        """Call Anthropic API (Claude models)."""
        if not ANTHROPIC_AVAILABLE:
            raise LLMConfigurationError("Anthropic SDK not installed. Run: pip install anthropic")

        try:
            client = anthropic.Anthropic(api_key=api_key, timeout=timeout)

            message = client.messages.create(
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text

        except Exception as e:
            raise LLMAPIError(f"Anthropic API error: {str(e)}")

    @staticmethod
    def _call_google(
        api_key: str,
        model_name: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
        timeout: float
    ) -> str:
        """Call Google GenAI API (Gemini models)."""
        if not GOOGLE_AVAILABLE:
            raise LLMConfigurationError(
                "Google GenAI SDK not installed. Run: pip install google-genai"
            )

        try:
            client = google_genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=google_genai_types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
            return response.text

        except Exception as e:
            raise LLMAPIError(f"Google GenAI API error: {str(e)}")

    @staticmethod
    def _call_google_with_grounding(
        api_key: str,
        model_name: str,
        prompt: str,
        timeout: float
    ) -> str:
        """Call Google GenAI API with Google Search grounding (for web search)."""
        if not GOOGLE_AVAILABLE:
            raise LLMConfigurationError(
                "Google GenAI SDK not installed. Run: pip install google-genai"
            )

        try:
            client = google_genai.Client(api_key=api_key)
            search_tool = google_genai_types.Tool(
                google_search=google_genai_types.GoogleSearch()
            )
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=google_genai_types.GenerateContentConfig(tools=[search_tool]),
            )
            return response.text

        except Exception as e:
            raise LLMAPIError(f"Google GenAI API (with grounding) error: {str(e)}")

    @staticmethod
    def _call_azure(
        api_key: str,
        deployment_name: str,
        prompt: str,
        azure_endpoint: str,
        api_version: str,
        max_tokens: int,
        temperature: float,
        timeout: float
    ) -> str:
        """Call Azure OpenAI.

        For Azure, model_name is interpreted as the deployment name (Azure routes
        requests by deployment, not by model id). azure_endpoint is the resource
        URL like https://<resource>.openai.azure.com/.
        """
        if not OPENAI_AVAILABLE:
            raise LLMConfigurationError("OpenAI SDK not installed. Run: pip install openai")

        try:
            http_client = httpx.Client(timeout=timeout)
            client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
                http_client=http_client,
            )

            response = client.chat.completions.create(
                model=deployment_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content

        except Exception as e:
            raise LLMAPIError(f"Azure OpenAI API error ({azure_endpoint}): {str(e)}")

    @staticmethod
    def _call_openai_compatible(
        api_key: str,
        model_name: str,
        prompt: str,
        api_endpoint: str,
        max_tokens: int,
        temperature: float,
        timeout: float
    ) -> str:
        """Call OpenAI-compatible API (Perplexity, local models, etc.)."""
        if not OPENAI_AVAILABLE:
            raise LLMConfigurationError("OpenAI SDK not installed. Run: pip install openai")

        try:
            http_client = httpx.Client(timeout=timeout)
            client = OpenAI(
                api_key=api_key,
                base_url=api_endpoint,
                http_client=http_client
            )

            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content

        except Exception as e:
            raise LLMAPIError(f"OpenAI-compatible API error ({api_endpoint}): {str(e)}")

    @staticmethod
    def test_connection(
        api_type: str,
        api_key: str,
        model_name: str,
        api_endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        test_prompt: str = "Hello, please respond with a brief greeting."
    ) -> tuple[bool, str, Optional[str]]:
        """
        Test connection to an LLM provider.

        Args:
            api_type: The API type
            api_key: The decrypted API key
            model_name: The model to use
            api_endpoint: Custom endpoint URL (for openai_compatible / azure)
            api_version: api_version (azure only)
            test_prompt: The prompt to send for testing

        Returns:
            Tuple of (success: bool, message: str, response_preview: Optional[str])
        """
        try:
            response = GenericLLMClient.call(
                api_type=api_type,
                api_key=api_key,
                model_name=model_name,
                prompt=test_prompt,
                api_endpoint=api_endpoint,
                api_version=api_version,
                max_tokens=100,
                temperature=0.7,
                timeout=30.0  # Shorter timeout for testing
            )
            return True, "Connection successful", response[:200] if response else None

        except LLMConfigurationError as e:
            return False, f"Configuration error: {str(e)}", None

        except LLMAPIError as e:
            return False, f"API error: {str(e)}", None

        except Exception as e:
            return False, f"Unexpected error: {str(e)}", None
