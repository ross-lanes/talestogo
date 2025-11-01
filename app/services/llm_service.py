import os
import json
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Dict, Any

# --- Perplexity Integration Via OpenAI ---
from openai import OpenAI

# --- Anthropic (Claude) Integration ---
# CORRECTED IMPORT: The Anthropic client is in the top-level package
import anthropic

# --- Google (Gemini) Integration ---
import google.generativeai as genai

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

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Tenacity Retry Decorator ---
retry_decorator = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)

# === 1. SERVICE FOR QUERYING LLMS (DATA COLLECTION) ===

@retry_decorator
def _call_perplexity_api(query: str) -> str:
    """Helper function to call Perplexity API."""
    if not perplexity_client:
        return "Error: Perplexity API key not configured or client failed to initialize."
    
    print(f"Calling Perplexity API with model 'llama-3-sonar-large-32k-online' for query: '{query[:50]}...'")
    response = perplexity_client.chat.completions.create(
        model="llama-3-sonar-large-32k-online",
        messages=[
            {"role": "system", "content": "You are a helpful assistant providing detailed, factual answers."},
            {"role": "user", "content": query},
        ],
    )
    return response.choices[0].message.content

@retry_decorator
def _call_anthropic_api(query: str) -> str:
    """Helper function to call Anthropic (Claude) API."""
    if not anthropic_client:
        return "Error: Anthropic API key not configured or client failed to initialize."

    print(f"Calling Anthropic API for query: '{query[:50]}...'")
    message = anthropic_client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": query}
        ]
    )
    return message.content[0].text

@retry_decorator
def _call_gemini_api(query: str) -> str:
    """Helper function to call Google (Gemini) API."""
    if not GEMINI_API_KEY:
        return "Error: Gemini API key not configured."

    print(f"Calling Gemini API for query: '{query[:50]}...'")
    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(query)
    return response.text

def query_platform_api(query: str, platform: str) -> str:
    """
    Routes a query to the correct LLM API based on the platform name.
    """
    platform_map = {
        "Perplexity": _call_perplexity_api,
        "Claude": _call_anthropic_api,
        "Gemini": _call_gemini_api
    }
    
    api_function = platform_map.get(platform)
    
    if not api_function:
        return f"Error: Unknown platform '{platform}'. Supported platforms are {list(platform_map.keys())}."
        
    try:
        return api_function(query)
    except Exception as e:
        print(f"ERROR: API call to {platform} failed for query '{query[:50]}...'. Error: {e}")
        return f"API call to {platform} failed: {e}"


# === 2. SERVICE FOR ANALYZING RAW RESPONSES ===

@retry_decorator
def analyze_raw_response(
    query_text: str,
    response_text: str,
    competitors: List[str],
    descriptors: List[str]
) -> Dict[str, Any]:
    """
    Uses an LLM (Gemini by default) to analyze a raw response and extract structured data.
    """
    if not GEMINI_API_KEY:
        print("ERROR: Gemini API key is required for analysis but is not configured.")
        return {"error": "Gemini API key not configured for analysis."}

    competitor_list_str = ", ".join(f'"{c}"' for c in competitors)
    descriptor_list_str = ", ".join(f'"{d}"' for d in descriptors)

    system_prompt = (
        "You are an expert AI Optimization analyst. Your task is to analyze an AI-generated response "
        "objectively based on a provided query. Respond ONLY with a valid JSON object, with no other text "
        "or explanations. All fields in the JSON must be populated."
    )
    
    user_prompt = f"""
    Analyze the following AI response based on the original query and the provided context.

    **Original Query:**
    "{query_text}"

    **AI Response to Analyze:**
    ---
    {response_text}
    ---

    **Analysis Context:**
    - The primary entity of interest is "Princeton Plasma Physics Laboratory (PPPL)".
    - Look for these specific competitors: [{competitor_list_str}]
    - Look for these specific target descriptors being associated with PPPL: [{descriptor_list_str}]

    **Task:**
    Return a single, valid JSON object with the following structure and rules:
    {{
      "pppl_mentioned": "Yes",
      "pppl_position": "Leader",
      "sentiment": "Positive",
      "descriptors": ["pioneering", "spherical tokamak"],
      "competitors": ["MIT PSFC", "Commonwealth Fusion Systems"],
      "sources": ["PPPL.gov", "wikipedia.org"],
      "notes": "The response highlights PPPL's leadership role and correctly associates it with key technologies."
    }}

    **Rules for JSON fields:**
    1.  `"pppl_mentioned"`: String. Must be one of "Yes", "No", or "Indirect".
    2.  `"pppl_position"`: String. Must be one of "Leader", "Top 3", "Featured", "Listed", or "Not Mentioned".
    3.  `"sentiment"`: String. Must be one of "Very Positive", "Positive", "Neutral", "Negative", "Mixed".
    4.  `"descriptors"`: Array of strings. List ONLY target descriptors associated with PPPL.
    5.  `"competitors"`: Array of strings. List ONLY competitors from the provided list that are mentioned.
    6.  `"sources"`: Array of strings. List any sources cited. If none, return an empty array [].
    7.  `"notes"`: String. A brief, one-sentence summary of PPPL's representation.

    Now, analyze the provided AI Response and return the JSON object.
    """

    print(f"Analyzing response for query: '{query_text[:50]}...'")
    model = genai.GenerativeModel(
        'gemini-2.5-pro',
        system_instruction=system_prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    response = model.generate_content(user_prompt)
    
    try:
        analysis_json = json.loads(response.text)
        return analysis_json
    except (json.JSONDecodeError, KeyError) as e:
        print(f"ERROR: Could not parse JSON from analysis response. Error: {e}")
        print(f"Raw analysis response: {response.text}")
        return {"error": "Failed to parse analysis from LLM."}
