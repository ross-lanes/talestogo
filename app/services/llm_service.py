import os
import json
import logging
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Custom exceptions for LLM service errors
class LLMServiceError(Exception):
    """Base exception for LLM service errors"""
    pass


class LLMConfigurationError(LLMServiceError):
    """Raised when LLM API keys are not configured"""
    pass


class LLMAPIError(LLMServiceError):
    """Raised when LLM API calls fail"""
    pass


class LLMAnalysisError(LLMServiceError):
    """Raised when response analysis fails"""
    pass

# --- Perplexity Integration Via OpenAI ---
from openai import OpenAI

# --- Anthropic (Claude) Integration ---
# CORRECTED IMPORT: The Anthropic client is in the top-level package
import anthropic

# --- Google (Gemini) Integration ---
from google import genai as google_genai

# Load API keys from .env file
load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Configure Clients ---
# Use a try/except block for safer initialization
try:
    perplexity_client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai") if PERPLEXITY_API_KEY else None
except Exception as e:
    print(f"⚠️ Warning: Could not initialize Perplexity client. Error: {e}")
    perplexity_client = None

try:
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
except Exception as e:
    print(f"⚠️ Warning: Could not initialize Anthropic client. Error: {e}")
    anthropic_client = None

try:
    gemini_client = google_genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except Exception as e:
    print(f"⚠️ Warning: Could not initialize Gemini client. Error: {e}")
    gemini_client = None

# --- Tenacity Retry Decorator ---
retry_decorator = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)

# === 1. SERVICE FOR QUERYING LLMS (DATA COLLECTION) ===

@retry_decorator
def _call_perplexity_api(query: str) -> str:
    """
    Helper function to call Perplexity API.
    Raises LLMConfigurationError if API key not configured.
    Raises LLMAPIError if API call fails.
    """
    if not perplexity_client:
        logger.error("Perplexity API key not configured or client failed to initialize")
        raise LLMConfigurationError("Perplexity API key not configured or client failed to initialize.")

    try:
        logger.info(f"Calling Perplexity API with model 'sonar' for query: '{query[:50]}...'")
        response = perplexity_client.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "system", "content": "You are a helpful assistant providing detailed, factual answers."},
                {"role": "user", "content": query},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Perplexity API call failed for query '{query[:50]}...': {str(e)}")
        raise LLMAPIError(f"Perplexity API call failed: {str(e)}") from e

@retry_decorator
def _call_anthropic_api(query: str) -> str:
    """
    Helper function to call Anthropic (Claude) API.
    Raises LLMConfigurationError if API key not configured.
    Raises LLMAPIError if API call fails.
    """
    if not anthropic_client:
        logger.error("Anthropic API key not configured or client failed to initialize")
        raise LLMConfigurationError("Anthropic API key not configured or client failed to initialize.")

    try:
        logger.info(f"Calling Anthropic API for query: '{query[:50]}...'")
        message = anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": query}
            ]
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Anthropic API call failed for query '{query[:50]}...': {str(e)}")
        raise LLMAPIError(f"Anthropic API call failed: {str(e)}") from e

@retry_decorator
def _call_gemini_api(query: str) -> str:
    """
    Helper function to call Google (Gemini) API.
    Raises LLMConfigurationError if API key not configured.
    Raises LLMAPIError if API call fails.
    """
    if not GEMINI_API_KEY:
        logger.error("Gemini API key not configured")
        raise LLMConfigurationError("Gemini API key not configured.")

    try:
        logger.info(f"Calling Gemini API for query: '{query[:50]}...'")
        response = gemini_client.models.generate_content(
            model='gemini-2.5-pro',
            contents=query,
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini API call failed for query '{query[:50]}...': {str(e)}")
        raise LLMAPIError(f"Gemini API call failed: {str(e)}") from e

def query_platform_api(query: str, platform: str) -> str:
    """
    Routes a query to the correct LLM API based on the platform name.
    Raises ValueError if platform is unknown.
    Raises LLMConfigurationError if API key not configured.
    Raises LLMAPIError if API call fails.
    """
    platform_map = {
        "Perplexity": _call_perplexity_api,
        "Claude": _call_anthropic_api,
        "Gemini": _call_gemini_api
    }

    api_function = platform_map.get(platform)

    if not api_function:
        logger.error(f"Unknown platform '{platform}'. Supported: {list(platform_map.keys())}")
        raise ValueError(f"Unknown platform '{platform}'. Supported platforms are {list(platform_map.keys())}.")

    # Let exceptions propagate - they're already properly typed from helper functions
    return api_function(query)


# === 2. SERVICE FOR ANALYZING RAW RESPONSES ===

@retry_decorator
def analyze_raw_response(
    query_text: str,
    response_text: str,
    competitors: List[str],
    descriptors: List[str],
    brand_name: str = "the brand"
) -> Dict[str, Any]:
    """
    Uses Gemini to analyze a raw response and extract structured data.
    Raises LLMConfigurationError if Gemini API key not configured.
    Raises LLMAnalysisError if analysis fails or JSON parsing fails.
    """
    if not GEMINI_API_KEY:
        logger.error("Gemini API key is required for analysis but is not configured")
        raise LLMConfigurationError("Gemini API key is required for analysis but is not configured.")

    competitor_list_str = ", ".join(f'"{c}"' for c in competitors)
    descriptor_list_str = ", ".join(f'"{d}"' for d in descriptors)

    prompt = f"""You are an expert AI Optimization analyst. Your task is to analyze an AI-generated response objectively based on a provided query. Respond ONLY with a valid JSON object, with no other text or explanations. All fields in the JSON must be populated.

    Analyze the following AI response based on the original query and the provided context.

    **Original Query:**
    "{query_text}"

    **AI Response to Analyze:**
    ---
    {response_text}
    ---

    **Analysis Context:**
    - The primary entity of interest is "{brand_name}".
    - Look for these specific competitors: [{competitor_list_str}]
    - Look for these specific target descriptors being associated with {brand_name}: [{descriptor_list_str}]

    **Task:**
    Return a single, valid JSON object with the following structure and rules:
    {{
      "brand_mentioned": "Yes",
      "brand_position": "Leader",
      "sentiment": "Positive",
      "descriptors": ["innovative", "industry leader"],
      "competitors": ["Competitor A", "Competitor B"],
      "sources": ["example.com", "wikipedia.org"],
      "notes": "The response highlights {brand_name}'s leadership role and correctly associates it with key technologies."
    }}

    **Rules for JSON fields:**
    1.  `"brand_mentioned"`: String. Must be one of "Yes", "No", or "Indirect".
    2.  `"brand_position"`: String. Must be one of "Leader", "Top 3", "Featured", "Listed", or "Not Mentioned".
    3.  `"sentiment"`: String. Must be one of "Very Positive", "Positive", "Neutral", "Negative", "Mixed".
    4.  `"descriptors"`: Array of strings. List ONLY target descriptors associated with {brand_name}.
    5.  `"competitors"`: Array of strings. List ONLY competitors from the provided list that are mentioned.
    6.  `"sources"`: Array of strings. List any sources cited. If none, return an empty array [].
    7.  `"notes"`: String. A brief, one-sentence summary of {brand_name}'s representation.

    Now, analyze the provided AI Response and return the JSON object.
    """

    logger.info(f"Analyzing response with Gemini for query: '{query_text[:50]}...'")

    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
        )

        response_content = response.text

        # Clean the response - remove markdown code blocks if present
        if response_content.startswith("```json"):
            response_content = response_content[7:]
        if response_content.startswith("```"):
            response_content = response_content[3:]
        if response_content.endswith("```"):
            response_content = response_content[:-3]
        response_content = response_content.strip()

        # Parse the JSON response
        analysis_json = json.loads(response_content)
        logger.info(f"Successfully analyzed response for query: '{query_text[:50]}...'")
        return analysis_json

    except json.JSONDecodeError as e:
        raw_response = response_content if 'response_content' in locals() else 'No response'
        logger.error(f"Could not parse JSON from Gemini analysis response. Error: {e}")
        logger.error(f"Raw analysis response: {raw_response}")
        raise LLMAnalysisError(f"Failed to parse JSON from Gemini analysis: {str(e)}") from e

    except Exception as e:
        logger.error(f"Gemini analysis failed for query '{query_text[:50]}...': {str(e)}")
        raise LLMAnalysisError(f"Gemini analysis failed: {str(e)}") from e
