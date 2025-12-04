"""
Heads - Marketing Persona Generation API Routes

This router provides endpoints for generating marketing personas using the
Gemini API. The API key is stored securely on the server (Railway) and not
exposed to the frontend.
"""
import json
import httpx
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import get_current_user
from app.models import User
from app.config import GEMINI_API_KEY


router = APIRouter(
    prefix="/api/heads",
    tags=["heads-marketing"],
)


# --- Request/Response Models ---

class HeadsFormData(BaseModel):
    """Form data for persona generation"""
    brand: str
    brandAccount: Optional[str] = None
    accountDetails: Optional[str] = None
    occupations: str
    targetCountries: Optional[str] = None
    ageRanges: Optional[str] = None
    website: Optional[str] = None
    archetypes: Optional[List[str]] = []
    numberOfPersonas: Optional[int] = 3
    customCharacteristic1: Optional[str] = None
    customCharacteristic2: Optional[str] = None
    customCharacteristic3: Optional[str] = None
    customCharacteristic4: Optional[str] = None


class Source(BaseModel):
    """Source citation from Gemini grounding"""
    title: str
    uri: str


class Persona(BaseModel):
    """Generated persona data"""
    id: Optional[str] = None
    generalizationTitle: str
    name: str
    age: str
    occupation: str
    location: Optional[str] = None
    workplace: Optional[str] = None
    technologyAbility: Optional[str] = None
    technologyComfortability: Optional[str] = None
    profile: str
    goals: List[str]
    frustrations: List[str]
    brandView: str
    marketingStrategy: str
    avatarBase64: Optional[str] = None


class GenerationResult(BaseModel):
    """Result of persona generation"""
    personas: List[Persona]
    sources: List[Source]


class PersonaImageRequest(BaseModel):
    """Request for persona image generation"""
    persona: Persona
    styleKeywords: Optional[str] = None


class PersonaImageResponse(BaseModel):
    """Response with generated image"""
    imageBase64: str


# --- Helper Functions ---

def _generate_id() -> str:
    """Generate a random ID for a persona"""
    import random
    import string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))


def _build_persona_prompt(form_data: HeadsFormData) -> str:
    """Build the prompt for persona generation"""
    archetype_instruction = ""
    if form_data.archetypes:
        archetype_instruction = f"Include personas matching these specific archetypes: {', '.join(form_data.archetypes)}."

    custom_traits = [
        form_data.customCharacteristic1,
        form_data.customCharacteristic2,
        form_data.customCharacteristic3,
        form_data.customCharacteristic4,
    ]
    custom_traits = [t for t in custom_traits if t]

    custom_traits_instruction = ""
    if custom_traits:
        custom_traits_instruction = f"MANDATORY CHARACTERISTICS: Ensure the generated personas incorporate the following specific traits/characteristics where appropriate: {', '.join(custom_traits)}."

    count = form_data.numberOfPersonas or 3
    brand_account_instruction = f'The specific brand account or focus area is: "{form_data.brandAccount}".' if form_data.brandAccount else ""
    account_details_instruction = f'Contextual Account Details & Goals: "{form_data.accountDetails}".' if form_data.accountDetails else ""

    target_countries_note = f" based on the requested countries: {form_data.targetCountries}" if form_data.targetCountries else ""

    return f"""
    You are an expert marketing strategist. Create detailed user personas for the brand: "{form_data.brand}".
    {f"The brand's website is: {form_data.website}." if form_data.website else ""}
    {brand_account_instruction}
    {account_details_instruction}

    Target Occupations: {form_data.occupations}
    Target Countries: {form_data.targetCountries or "Global / Relevant to brand"}
    Target Age Ranges: {form_data.ageRanges or "Varies based on occupation"}

    {archetype_instruction}
    {custom_traits_instruction}

    QUANTITY REQUIREMENT:
    You MUST generate a JSON list containing EXACTLY {count} distinct personas.
    Do not stop after one. Ensure the array has {count} items.

    CRITICAL INSTRUCTIONS FOR ACCURACY:
    1. Ensure occupation details, salary expectations, and industry trends are accurate.
    2. Assign a specific "location" (City, Country) to each persona{target_countries_note}.
    3. Assign a specific "workplace".
       - IF the occupation is a medical professional (e.g., Doctor, Nurse, Surgeon), use a REAL, EXISTING medical facility (Hospital, Clinic) in that specific "location".
       - For other occupations, generate a plausible company name or use a real one if relevant.
    4. Determine "technologyAbility" - Provide a descriptive rating (e.g., "Expert - Highly proficient with industry software").
    5. Determine "technologyComfortability" - Provide a sentiment (e.g., "Early Adopter - Always tries new features", "Skeptic - Prefers established tools").

    OUTPUT FORMAT:
    Return ONLY a valid JSON array. Do not include markdown formatting (like ```json).
    The output must be a raw JSON array of objects.

    Structure:
    [
      {{
        "generalizationTitle": "The Pioneer",
        "name": "Alex Chen",
        "age": "28",
        "occupation": "UX Designer",
        "location": "Seattle, WA",
        "workplace": "Amazon",
        "technologyAbility": "Expert - Proficient in code & design",
        "technologyComfortability": "Digital Native - Early Adopter",
        "profile": "...",
        "goals": ["..."],
        "frustrations": ["..."],
        "brandView": "...",
        "marketingStrategy": "..."
      }},
      ... ({count} total objects)
    ]
    """


def _build_image_prompt(persona: Persona, style_keywords: Optional[str] = None) -> str:
    """Build the prompt for persona image generation"""
    style_base = (
        f"Visual Style: {style_keywords}."
        if style_keywords and style_keywords.strip()
        else "Visual Style: Photorealistic, professional lighting."
    )

    return f"""
    Generate a professional portrait avatar for a user persona.

    Persona Details:
    - Name: {persona.name}
    - Age: {persona.age}
    - Occupation: {persona.occupation}
    - Description: {persona.profile}

    STRICT COMPOSITION REQUIREMENTS:
    1. The subject MUST look directly straight into the camera (direct eye contact).
    2. The framing MUST be a strict head-and-shoulders shot (head, neck, and tops of shoulders only).
    3. Center the subject.
    4. Neutral, clean background.

    {style_base}
    """


# --- API Endpoints ---

@router.post("/generate-personas", response_model=GenerationResult)
async def generate_personas(
    form_data: HeadsFormData,
    current_user: User = Depends(get_current_user),
):
    """
    Generate marketing personas using Gemini AI.

    The Gemini API key is securely stored on the server and not exposed to clients.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key is not configured on the server. Please contact the administrator.",
        )

    prompt = _build_persona_prompt(form_data)

    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{gemini_url}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.9,
                        "topK": 40,
                        "topP": 0.95,
                        "maxOutputTokens": 8192,
                    },
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_detail = "Gemini API request failed"
            try:
                error_data = e.response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_detail = error_data["error"]["message"]
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_detail,
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to Gemini API: {str(e)}",
            )

    data = response.json()
    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")

    if not text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No response from Gemini AI",
        )

    # Parse the JSON response
    try:
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        parsed_data = json.loads(cleaned_text)

        # Handle case where model wraps array in an object key
        if not isinstance(parsed_data, list) and isinstance(parsed_data, dict):
            for key in parsed_data:
                if isinstance(parsed_data[key], list):
                    parsed_data = parsed_data[key]
                    break

        if not isinstance(parsed_data, list):
            raise ValueError("Response is not an array")

        # Add IDs to personas
        personas = [
            Persona(id=_generate_id(), **p) for p in parsed_data
        ]
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to parse persona data from Gemini: {str(e)}",
        )

    # No grounding sources in this basic API call
    sources: List[Source] = []

    return GenerationResult(personas=personas, sources=sources)


@router.post("/generate-image", response_model=PersonaImageResponse)
async def generate_persona_image(
    request: PersonaImageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate an avatar image for a persona using Gemini AI.

    The Gemini API key is securely stored on the server and not exposed to clients.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key is not configured on the server. Please contact the administrator.",
        )

    prompt = _build_image_prompt(request.persona, request.styleKeywords)

    image_api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent"

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{image_api_url}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseModalities": ["image", "text"],
                        "responseMimeType": "text/plain",
                    },
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_detail = "Image generation failed"
            try:
                error_data = e.response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_detail = error_data["error"]["message"]
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_detail,
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to Gemini API: {str(e)}",
            )

    data = response.json()

    # Look for inline image data in the response
    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        inline_data = part.get("inlineData")
        if inline_data and inline_data.get("data"):
            mime_type = inline_data.get("mimeType", "image/png")
            image_base64 = f"data:{mime_type};base64,{inline_data['data']}"
            return PersonaImageResponse(imageBase64=image_base64)

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="No image data received from Gemini",
    )


@router.get("/api-status")
async def check_api_status(
    current_user: User = Depends(get_current_user),
):
    """
    Check if the Gemini API is configured and available.
    """
    return {
        "gemini_configured": bool(GEMINI_API_KEY),
        "message": "Gemini API is configured and ready" if GEMINI_API_KEY else "Gemini API key is not configured",
    }
