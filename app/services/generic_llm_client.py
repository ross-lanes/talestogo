"""
Generic LLM Client for Tales Project

Routes API calls to different LLM providers based on configuration.
Supports OpenAI, Anthropic, Google (Gemini), Azure OpenAI, OpenAI-compatible
APIs, and Bing web search (v7 REST + Azure AI Foundry Grounding with Bing).
"""

import os
from typing import Optional, List, Dict, Any
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

# Azure AI Foundry SDK — used only by the `bing_grounded` api_type. Declared
# as an optional extra in pyproject.toml ([project.optional-dependencies]
# bing-grounded). Installed via `pip install .[bing-grounded]`. If absent,
# `bing_grounded` calls return a clear "install the bing-grounded extra"
# error rather than a bare ImportError. `bing_v7` does not need this SDK.
try:
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    from azure.core.credentials import AzureKeyCredential
    AZURE_AI_FOUNDRY_AVAILABLE = True
except ImportError:
    AZURE_AI_FOUNDRY_AVAILABLE = False


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
        api_version: Optional[str] = None,
        analysis_provider: Optional[Any] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> str:
        """
        Call an LLM API with web search grounding (for State of the LLMs feature).

        Supported api_types:
        - "google": Gemini + Google Search grounding (single round-trip)
        - "openai_compatible" with Perplexity sonar: built-in web search
        - "bing_v7": Bing Search v7 REST retrieval, synthesized by analysis_provider
          (requires analysis_provider to be passed in)
        - "bing_grounded": Azure AI Foundry agent with Grounding-with-Bing tool
          (requires the optional `bing-grounded` extra to be installed)

        Azure OpenAI itself (api_type="azure") is intentionally NOT supported here —
        it has no native web search. Azure-only deployments configure a Bing
        provider alongside Azure to populate the State of the LLMs section.

        Args:
            api_type: One of "google", "openai_compatible", "bing_v7", "bing_grounded"
            api_key: The decrypted API key
            model_name: Provider-specific identifier (model / deployment / agent ID)
            prompt: The prompt to send
            api_endpoint: Custom endpoint URL (Perplexity / Bing v7 / AI Foundry)
            api_version: Azure AI Foundry api_version (bing_grounded only)
            analysis_provider: ProviderConfig used to synthesize Bing v7 search
                results. Required when api_type=="bing_v7". Ignored otherwise.
            timeout: Request timeout in seconds

        Returns:
            The response text from the LLM (or synthesized prose for bing_v7).

        Raises:
            LLMConfigurationError: If the api_type doesn't support web search or
                if required configuration is missing.
            LLMAPIError: If the upstream API call fails.
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
        elif api_type == "bing_v7":
            if not api_endpoint:
                raise LLMConfigurationError(
                    "api_endpoint is required for bing_v7 (e.g., 'https://api.bing.microsoft.com/')"
                )
            if analysis_provider is None:
                raise LLMConfigurationError(
                    "bing_v7 retrieves search results but does not synthesize them — "
                    "designate one of your providers with use_for_analysis=True so it "
                    "can write the State of the LLMs section from the search results."
                )
            return GenericLLMClient._call_bing_v7_grounded_synthesis(
                api_key, prompt, api_endpoint, analysis_provider, timeout
            )
        elif api_type == "bing_grounded":
            if not api_endpoint:
                raise LLMConfigurationError(
                    "api_endpoint (Azure AI Foundry project endpoint) is required for bing_grounded"
                )
            return GenericLLMClient._call_bing_grounded(
                api_key, model_name, prompt, api_endpoint, api_version, timeout
            )
        else:
            raise LLMConfigurationError(
                f"API type '{api_type}' does not support web search. "
                "Web search is provided by: 'google' (Gemini grounding), 'openai_compatible' "
                "(Perplexity sonar), 'bing_v7' (Bing Search v7 + analysis LLM), "
                "or 'bing_grounded' (Azure AI Foundry Grounding with Bing)."
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

    # ==================== Bing Search v7 (REST retrieval) ====================

    @staticmethod
    def _call_bing_v7_search(
        api_key: str,
        query: str,
        api_endpoint: str,
        timeout: float,
        count: int = 10,
    ) -> List[Dict[str, str]]:
        """Call Bing Search v7 REST API and return a list of {title, url, snippet}.

        Pure retrieval — does not call any LLM. Used by
        `_call_bing_v7_grounded_synthesis` to fetch fresh web results that the
        analysis provider then synthesizes into prose.

        api_endpoint is the Bing host (e.g., 'https://api.bing.microsoft.com/').
        The '/v7.0/search' path is appended automatically.
        """
        # Normalize endpoint. Operators may paste any of:
        #   https://api.bing.microsoft.com
        #   https://api.bing.microsoft.com/
        #   https://api.bing.microsoft.com/v7.0
        #   https://api.bing.microsoft.com/v7.0/search
        # We canonicalize to .../v7.0/search regardless of which they pasted.
        base = api_endpoint.rstrip("/")
        if base.endswith("/v7.0/search"):
            url = base
        elif base.endswith("/v7.0"):
            url = f"{base}/search"
        else:
            url = f"{base}/v7.0/search"

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(
                    url,
                    headers={"Ocp-Apim-Subscription-Key": api_key},
                    params={"q": query, "mkt": "en-US", "count": count, "responseFilter": "Webpages"},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            raise LLMAPIError(f"Bing Search v7 API error ({url}): {str(e)}")
        except Exception as e:
            raise LLMAPIError(f"Bing Search v7 unexpected error ({url}): {str(e)}")

        web_pages = (data.get("webPages") or {}).get("value") or []
        results: List[Dict[str, str]] = []
        for page in web_pages:
            results.append({
                "title": page.get("name", "") or "",
                "url": page.get("url", "") or "",
                "snippet": page.get("snippet", "") or "",
            })
        return results

    @staticmethod
    def _format_bing_results_as_context(results: List[Dict[str, str]]) -> str:
        """Format Bing search results as a numbered list the LLM can cite as [1], [2], etc."""
        if not results:
            return "(no search results returned)"
        lines = []
        for i, r in enumerate(results, start=1):
            lines.append(f"[{i}] {r['title']}")
            lines.append(f"    URL: {r['url']}")
            lines.append(f"    {r['snippet']}")
            lines.append("")
        return "\n".join(lines).rstrip()

    @staticmethod
    def _distill_search_query(prompt: str, analysis_provider, max_words: int = 10) -> str:
        """Reduce a long report-writing prompt to a concise search-engine query.

        Report prompts in scripts/admin/generate_report.py are paragraph-length
        instructions ("Research the latest trends...") — passing them verbatim
        to Bing as q= would return noise because search engines rank by keyword
        density. We ask the analysis LLM to extract the actual searchable intent
        (3-10 keywords) first, then use that as the query.

        Falls back to a truncated word-list of the prompt if the LLM call fails.
        """
        query_prompt = (
            "You are generating a query for a web search engine.\n"
            "Read the instruction below and write a single concise search query "
            f"(maximum {max_words} words) that would surface the most relevant, "
            "current information needed to answer it.\n\n"
            f"INSTRUCTION:\n{prompt}\n\n"
            "Respond with ONLY the search query — no quotes, no explanation, "
            "no markdown, no leading or trailing whitespace."
        )
        try:
            raw = analysis_provider.call(
                prompt=query_prompt, max_tokens=80, temperature=0.0
            )
            cleaned = (raw or "").strip().strip("\"'`")
            # Take the first line only — some models add a follow-up explanation
            # despite being asked not to.
            cleaned = cleaned.splitlines()[0].strip() if cleaned else ""
            if cleaned:
                return cleaned
        except Exception:
            pass
        # Fallback: first N words of the original prompt.
        return " ".join(prompt.split()[:max_words])

    @staticmethod
    def _call_bing_v7_grounded_synthesis(
        bing_api_key: str,
        prompt: str,
        bing_endpoint: str,
        analysis_provider,  # ProviderConfig — imported lazily to avoid circular import
        timeout: float,
    ) -> str:
        """Retrieve via Bing v7 then synthesize the results with analysis_provider.

        Three-step pattern:
          1. Distill the long report prompt into a concise Bing-friendly query
             (otherwise Bing's relevance ranker returns noise — long paragraph
             prompts score by every keyword, not by topical intent).
          2. Search Bing v7 with the distilled query.
          3. Synthesize prose from the results using the analysis_provider.

        The analysis_provider is the SAME provider the deployment uses for
        response analysis (use_for_analysis=True), so this composes Bing with
        whatever LLM the deployment already trusts.
        """
        # Step 1: distill the prompt into a search query.
        search_query = GenericLLMClient._distill_search_query(prompt, analysis_provider)

        # Step 2: search.
        results = GenericLLMClient._call_bing_v7_search(
            bing_api_key, search_query, bing_endpoint, timeout
        )

        # Step 3: synthesize using the analysis provider.
        context = GenericLLMClient._format_bing_results_as_context(results)
        augmented_prompt = (
            "You are answering a question using fresh web search results.\n\n"
            f"SEARCH QUERY USED: {search_query}\n\n"
            f"SEARCH RESULTS (from Bing):\n{context}\n\n"
            f"QUESTION:\n{prompt}\n\n"
            "Cite search results inline as [1], [2], etc. where relevant. "
            "If the results don't contain enough information to answer, say so "
            "rather than inventing details."
        )
        return analysis_provider.call(
            prompt=augmented_prompt, max_tokens=4000, temperature=0.5
        )

    # ==================== Azure AI Foundry — Grounding with Bing ====================

    @staticmethod
    def _call_bing_grounded(
        api_key: str,
        agent_id_or_deployment: str,
        prompt: str,
        api_endpoint: str,
        api_version: Optional[str],
        timeout: float,
    ) -> str:
        """Call an Azure AI Foundry agent that has the Grounding-with-Bing tool attached.

        Single round-trip — the agent retrieves via Bing and synthesizes the answer
        internally; we just send the prompt and read the response.

        Requires the optional `bing-grounded` extra to be installed:
            pip install talestogo[bing-grounded]

        NOTE: This implementation targets Azure AI Foundry's Agents API. The SDK
        surface is evolving; operators may need to adjust based on their tenant's
        actual API version. The plan documents this as "beta — needs live
        validation against a real provisioned resource."
        """
        if not AZURE_AI_FOUNDRY_AVAILABLE:
            raise LLMConfigurationError(
                "Azure AI Foundry SDK not installed. Run: "
                "pip install talestogo[bing-grounded] (or "
                "pip install azure-ai-projects azure-ai-agents azure-identity)"
            )

        if not agent_id_or_deployment:
            raise LLMConfigurationError(
                "bing_grounded requires model_name to be set to the Azure AI Foundry "
                "agent ID (the agent must have the Grounding-with-Bing-Search tool attached)"
            )

        try:
            # The endpoint here is the AI Foundry project endpoint, not an OpenAI
            # deployment URL. Two auth paths are supported:
            # - If AZURE_FOUNDRY_API_KEY is set (api_key non-empty), use
            #   AzureKeyCredential — explicit key-based auth.
            # - Otherwise fall back to DefaultAzureCredential, which auto-discovers
            #   managed identity (when running on Azure), az-login, or the standard
            #   AZURE_CLIENT_ID + AZURE_TENANT_ID + AZURE_CLIENT_SECRET service-
            #   principal env vars.
            if api_key:
                credential = AzureKeyCredential(api_key)  # type: ignore[name-defined]
            else:
                credential = DefaultAzureCredential()  # type: ignore[name-defined]

            credential_kwargs: Dict[str, Any] = {}
            if api_version:
                credential_kwargs["api_version"] = api_version
            client = AIProjectClient(  # type: ignore[name-defined]
                endpoint=api_endpoint,
                credential=credential,
                **credential_kwargs,
            )

            # Run the configured agent with the user prompt. The Grounding-with-Bing
            # tool is attached at agent-definition time (in Azure AI Foundry Studio),
            # not per-call, so we only need to invoke the agent and read the response.
            with client:
                thread = client.agents.threads.create()
                client.agents.messages.create(
                    thread_id=thread.id, role="user", content=prompt
                )
                run = client.agents.runs.create_and_process(
                    thread_id=thread.id, agent_id=agent_id_or_deployment
                )

                # Check positively for completion. Any other status (failed,
                # cancelled, expired, requires_action, …) means we shouldn't try
                # to read messages — they'll be empty or stale.
                run_status = getattr(run, "status", None)
                if run_status != "completed":
                    last_error = getattr(run, "last_error", None) or "(no error detail)"
                    raise LLMAPIError(
                        f"Azure AI Foundry agent run did not complete "
                        f"(status={run_status!r}): {last_error}"
                    )

                # Read back the assistant's reply from the thread.
                messages = list(client.agents.messages.list(thread_id=thread.id))
                for msg in messages:
                    if getattr(msg, "role", "") == "assistant":
                        text_content = getattr(msg, "content", None)
                        if isinstance(text_content, str):
                            return text_content
                        # Newer SDKs wrap content as a list of typed blocks.
                        # Accumulate all non-empty text values rather than
                        # returning the first one — longer responses (or runs
                        # that interleave text with tool-call blocks) get split
                        # across multiple blocks, and returning early truncates.
                        if isinstance(text_content, list) and text_content:
                            parts: List[str] = []
                            for block in text_content:
                                t = getattr(block, "text", None)
                                if t is None:
                                    continue
                                # Only collect if we can extract real text —
                                # don't fall back to str(t), which would
                                # return a Python object repr, not the
                                # message content.
                                val = getattr(t, "value", None)
                                if val:
                                    parts.append(val)
                            if parts:
                                return "\n\n".join(parts)
                return ""
        except LLMConfigurationError:
            raise
        except LLMAPIError:
            raise
        except Exception as e:
            raise LLMAPIError(
                f"Azure AI Foundry (Grounding with Bing) error ({api_endpoint}): {str(e)}"
            )

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
            with httpx.Client(timeout=timeout) as http_client:
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

            # Guard against empty choices (content filtering, API issues) and
            # None content (model refusal, tool_calls without text).
            if not response.choices:
                raise LLMAPIError(
                    f"Azure OpenAI returned no choices ({azure_endpoint}). "
                    "This usually means the prompt was filtered or the deployment is misconfigured."
                )
            return response.choices[0].message.content or ""

        except LLMAPIError:
            raise
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
            if api_type == "bing_v7":
                if not api_endpoint:
                    raise LLMConfigurationError(
                        "api_endpoint is required for bing_v7 (e.g., 'https://api.bing.microsoft.com/')"
                    )
                results = GenericLLMClient._call_bing_v7_search(
                    api_key=api_key,
                    query="test",
                    api_endpoint=api_endpoint,
                    timeout=30.0,
                    count=1,
                )
                preview = results[0]["snippet"][:200] if results else "(no results returned)"
                return True, "Bing Search v7 connection successful", preview

            elif api_type == "bing_grounded":
                response = GenericLLMClient._call_bing_grounded(
                    api_key=api_key,
                    agent_id_or_deployment=model_name,
                    prompt=test_prompt,
                    api_endpoint=api_endpoint or "",
                    api_version=api_version,
                    timeout=30.0,
                )
                return True, "Azure AI Foundry (Bing Grounded) connection successful", response[:200] if response else None

            else:
                response = GenericLLMClient.call(
                    api_type=api_type,
                    api_key=api_key,
                    model_name=model_name,
                    prompt=test_prompt,
                    api_endpoint=api_endpoint,
                    api_version=api_version,
                    max_tokens=100,
                    temperature=0.7,
                    timeout=30.0,
                )
                return True, "Connection successful", response[:200] if response else None

        except LLMConfigurationError as e:
            return False, f"Configuration error: {str(e)}", None

        except LLMAPIError as e:
            return False, f"API error: {str(e)}", None

        except Exception as e:
            return False, f"Unexpected error: {str(e)}", None
