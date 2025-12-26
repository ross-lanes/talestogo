"""
Big Idea Generator - Marketing Idea Generation API Routes

This router provides endpoints for generating marketing "Big Ideas" using the
Gemini API with Google Search grounding. The API key is stored securely on
the server and not exposed to the frontend.
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
    prefix="/api/bigidea",
    tags=["bigidea-marketing"],
)


# --- Request/Response Models ---

class BigIdeaFormData(BaseModel):
    """Form data for big idea generation"""
    clientName: str
    accountName: Optional[str] = None
    clientDescription: str
    competitors: Optional[str] = None
    strategicImperatives: Optional[str] = None
    numberOfIdeas: int = 3
    ideaAreas: str
    ideaScale: str  # Safe, Ambitious, Very Ambitious, Incredibly Ambitious
    targetAudience: str
    countryRegion: Optional[str] = None
    campaignGoal: str
    budget: str  # Low, Medium, High, Premium


class Idea(BaseModel):
    """A single generated marketing idea"""
    id: Optional[str] = None
    title: str
    description: str
    area: str
    scale: str
    rationale: str


class MarketShareDataItem(BaseModel):
    """Market share data for a competitor"""
    name: str
    percentage: float


class CompetitorAnalysis(BaseModel):
    """Competitor analysis from AI generation"""
    competitors: List[str]
    competitorStrategies: str
    differentiationStrategies: str
    marketShareData: Optional[List[MarketShareDataItem]] = None


class GroundingUrl(BaseModel):
    """URL from Google Search grounding"""
    uri: str
    title: Optional[str] = None


class GeneratedResponse(BaseModel):
    """Full response from idea generation"""
    ideas: List[Idea]
    competitorAnalysis: CompetitorAnalysis
    groundingUrls: Optional[List[GroundingUrl]] = None


class ExpandIdeaRequest(BaseModel):
    """Request to expand an existing idea"""
    formData: BigIdeaFormData
    originalIdea: Idea


# --- Helper Functions ---

def _generate_id(index: int) -> str:
    """Generate a unique ID for an idea"""
    import time
    return f"idea-{int(time.time() * 1000)}-{index}"


def _build_generation_prompt(form_data: BigIdeaFormData) -> str:
    """Build the prompt for idea generation"""
    return f"""You are a world-class marketing ideation specialist. Your goal is to generate 'Big Ideas' for a marketing agency client, along with a concise competitor analysis.

Client: {form_data.clientName}
{f'Account Name: {form_data.accountName}' if form_data.accountName else ''}
Client / Account Description: {form_data.clientDescription}
{f'Client / Agency Strategic Imperatives: {form_data.strategicImperatives}' if form_data.strategicImperatives else ''}
{f'Known Competitors: {form_data.competitors}' if form_data.competitors else ''}
Number of Ideas to generate: {form_data.numberOfIdeas}
Areas for Ideas: {form_data.ideaAreas}
Scale of Ideas: {form_data.ideaScale}
Target Audience Demographics: {form_data.targetAudience}
{f'Target Country/Region: {form_data.countryRegion}' if form_data.countryRegion else ''}
Specific Campaign Goal: {form_data.campaignGoal}
Detailed Budget Indicator: {form_data.budget}

First, use Google Search to research the client's industry, key competitors in the specified areas (and any provided known competitors), and their current marketing strategies or recent successful campaigns. Identify potential gaps, emerging trends, or areas where the client can differentiate and innovate, considering the target audience, campaign goal, and budget. Also, look for examples of successful marketing campaigns (even outside their direct competitors) that align with the requested scale.

Based on this research and your own creative intelligence, perform a competitor analysis and then generate {form_data.numberOfIdeas} distinct marketing ideas. Each idea should be a 'big idea', meaning it's impactful, aligns with the specified scale, and is tailored to the provided parameters.

For the competitor analysis, provide:
- 'competitors': A list of 3-5 key competitors.
- 'competitorStrategies': A brief summary of their dominant strategies or recent successful campaigns in the specified areas.
- 'differentiationStrategies': Unique selling propositions or campaign angles for the client that differentiate them from competitors and leverage identified gaps.
- 'marketShareData': (Optional, if research provides) An array of objects, each with 'name' (competitor name) and 'percentage' (their estimated market share as a number). Ensure percentages sum to 100% or are reflective of their share *relative to each other*. If exact percentages are not found, provide relative estimations or leave this field empty.

For each marketing idea, provide the following:
- A concise 'title'.
- A detailed 'description' explaining the concept, specific target audience segments, key messaging, and how it would be executed, considering the budget.
- The 'area' it primarily falls into (e.g., 'Digital', 'TV', 'Experiential', 'Integrated').
- The 'scale' of the idea, explicitly reflecting the requested scale (e.g., 'Safe', 'Ambitious', 'Very Ambitious, Incredibly Ambitious').
- A 'rationale' explaining why this idea is compelling, how it leverages competitive insights or addresses gaps, how it aligns with the requested scale, target audience, and campaign goal, and how it is feasible within the budget.

The output MUST be a single JSON object containing both the 'competitorAnalysis' (including marketShareData if provided) and an array of 'ideas'. Wrap the JSON output in a markdown code block, like this: ```json
{{ "competitorAnalysis": {{"competitors": [], "competitorStrategies": "", "differentiationStrategies": "", "marketShareData": [{{"name": "Comp A", "percentage": 40}}, {{"name": "Comp B", "percentage": 30}}]}}, "ideas": [{{"id": "...", "title": "...", "description": "...", "area": "...", "scale": "...", "rationale": "..."}}] }}
```. DO NOT include any other text outside this JSON block.
"""


def _build_expansion_prompt(form_data: BigIdeaFormData, original_idea: Idea) -> str:
    """Build the prompt for expanding an existing idea"""
    return f"""You are a world-class marketing ideation specialist. Your task is to expand upon an existing marketing idea for a client, exploring new avenues and providing significantly more depth and detail.

Client: {form_data.clientName}
{f'Account Name: {form_data.accountName}' if form_data.accountName else ''}
Client / Account Description: {form_data.clientDescription}
{f'Client / Agency Strategic Imperatives: {form_data.strategicImperatives}' if form_data.strategicImperatives else ''}
Original Idea Title: {original_idea.title}
Original Idea Description: {original_idea.description}
Original Idea Rationale: {original_idea.rationale}
Original Idea Area: {original_idea.area}
Original Idea Scale: {original_idea.scale}
Target Audience Demographics: {form_data.targetAudience}
{f'Target Country/Region: {form_data.countryRegion}' if form_data.countryRegion else ''}
Specific Campaign Goal: {form_data.campaignGoal}
Detailed Budget Indicator: {form_data.budget}

Expand this single idea. Provide a significantly more detailed 'description' that explores additional avenues, thought processes, specific execution tactics, and potential sub-campaigns. Elaborate on the 'rationale' to include new justifications, deeper competitive insights, and how it aligns even more strongly with the client's goals and target audience. The 'title', 'area', and 'scale' should remain consistent with the original idea, but the 'description' and 'rationale' should be extensively improved and detailed.

The output MUST be a single JSON object conforming to the 'Idea' interface, wrapped in a markdown code block, like this: ```json
{{ "id": "...", "title": "...", "description": "...", "area": "...", "scale": "...", "rationale": "..." }}
```. DO NOT include any other text outside this JSON block."""


# --- API Endpoints ---

@router.post("/generate-ideas", response_model=GeneratedResponse)
async def generate_ideas(
    form_data: BigIdeaFormData,
    current_user: User = Depends(get_current_user),
):
    """
    Generate marketing Big Ideas using Gemini AI with Google Search grounding.

    The Gemini API key is securely stored on the server and not exposed to clients.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key is not configured on the server. Please contact the administrator.",
        )

    prompt = _build_generation_prompt(form_data)

    # Use gemini-2.5-flash with Google Search grounding
    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            response = await client.post(
                f"{gemini_url}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "tools": [{"google_search": {}}],
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

    # Extract text response
    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")

    if not text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No response from Gemini AI",
        )

    # Parse the JSON response
    try:
        # Extract JSON from markdown code block
        json_match = text.strip()
        if "```json" in json_match:
            start = json_match.find("```json") + 7
            end = json_match.rfind("```")
            json_match = json_match[start:end].strip()
        elif "```" in json_match:
            start = json_match.find("```") + 3
            end = json_match.rfind("```")
            json_match = json_match[start:end].strip()

        parsed_data = json.loads(json_match)

        if not isinstance(parsed_data, dict) or "ideas" not in parsed_data or "competitorAnalysis" not in parsed_data:
            raise ValueError("Response missing required fields")

        # Add unique IDs to ideas
        ideas = []
        for idx, idea_data in enumerate(parsed_data["ideas"]):
            idea = Idea(
                id=_generate_id(idx),
                title=idea_data.get("title", ""),
                description=idea_data.get("description", ""),
                area=idea_data.get("area", ""),
                scale=idea_data.get("scale", ""),
                rationale=idea_data.get("rationale", ""),
            )
            ideas.append(idea)

        # Parse competitor analysis
        ca_data = parsed_data["competitorAnalysis"]
        market_share = None
        if ca_data.get("marketShareData"):
            market_share = [
                MarketShareDataItem(name=item["name"], percentage=item["percentage"])
                for item in ca_data["marketShareData"]
            ]

        competitor_analysis = CompetitorAnalysis(
            competitors=ca_data.get("competitors", []),
            competitorStrategies=ca_data.get("competitorStrategies", ""),
            differentiationStrategies=ca_data.get("differentiationStrategies", ""),
            marketShareData=market_share,
        )

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to parse idea data from Gemini: {str(e)}",
        )

    # Extract grounding URLs if available
    grounding_urls = []
    grounding_metadata = data.get("candidates", [{}])[0].get("groundingMetadata", {})
    grounding_chunks = grounding_metadata.get("groundingChunks", [])
    for chunk in grounding_chunks:
        web_data = chunk.get("web", {})
        if web_data.get("uri"):
            grounding_urls.append(GroundingUrl(
                uri=web_data["uri"],
                title=web_data.get("title"),
            ))

    return GeneratedResponse(
        ideas=ideas,
        competitorAnalysis=competitor_analysis,
        groundingUrls=grounding_urls if grounding_urls else None,
    )


@router.post("/expand-idea", response_model=GeneratedResponse)
async def expand_idea(
    request: ExpandIdeaRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Expand an existing idea with more detail using Gemini AI.

    The Gemini API key is securely stored on the server and not exposed to clients.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key is not configured on the server. Please contact the administrator.",
        )

    prompt = _build_expansion_prompt(request.formData, request.originalIdea)

    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

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
        json_match = text.strip()
        if "```json" in json_match:
            start = json_match.find("```json") + 7
            end = json_match.rfind("```")
            json_match = json_match[start:end].strip()
        elif "```" in json_match:
            start = json_match.find("```") + 3
            end = json_match.rfind("```")
            json_match = json_match[start:end].strip()

        parsed_data = json.loads(json_match)

        # Preserve original ID, area, and scale
        expanded_idea = Idea(
            id=request.originalIdea.id,
            title=parsed_data.get("title", request.originalIdea.title),
            description=parsed_data.get("description", ""),
            area=request.originalIdea.area,
            scale=request.originalIdea.scale,
            rationale=parsed_data.get("rationale", ""),
        )

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to parse expanded idea from Gemini: {str(e)}",
        )

    # Return with placeholder competitor analysis (expansion doesn't regenerate this)
    return GeneratedResponse(
        ideas=[expanded_idea],
        competitorAnalysis=CompetitorAnalysis(
            competitors=[],
            competitorStrategies="",
            differentiationStrategies="",
        ),
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
