"""
Canon - FDA Drug Data Research API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import httpx
import json

from app.services.llm_service import _call_gemini_api, LLMConfigurationError, LLMAPIError
from app.auth import get_current_user

router = APIRouter(prefix="/canon", tags=["canon"])

# OpenFDA API base URL
OPENFDA_BASE_URL = "https://api.fda.gov"


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    answer: str
    sources: list[str]
    disclaimer: str


async def fetch_openfda_data(endpoint: str, params: dict) -> dict:
    """Fetch data from OpenFDA API."""
    async with httpx.AsyncClient() as client:
        url = f"{OPENFDA_BASE_URL}{endpoint}"
        response = await client.get(url, params=params, timeout=30.0)
        if response.status_code == 404:
            return {"results": [], "meta": {"results": {"total": 0}}}
        response.raise_for_status()
        return response.json()


async def get_drug_label_context(drug_name: str) -> str:
    """Get drug label information for context."""
    try:
        params = {
            "search": f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"',
            "limit": 1
        }
        data = await fetch_openfda_data("/drug/label.json", params)

        if not data.get("results"):
            return f"No FDA label found for {drug_name}."

        label = data["results"][0]
        openfda = label.get("openfda", {})

        sections = []
        sections.append(f"Drug: {openfda.get('brand_name', ['Unknown'])[0]}")
        if openfda.get("generic_name"):
            sections.append(f"Generic Name: {openfda['generic_name'][0]}")
        if openfda.get("manufacturer_name"):
            sections.append(f"Manufacturer: {openfda['manufacturer_name'][0]}")

        if label.get("indications_and_usage"):
            sections.append(f"Indications: {label['indications_and_usage'][0][:1000]}")
        if label.get("warnings"):
            sections.append(f"Warnings: {label['warnings'][0][:1000]}")
        if label.get("adverse_reactions"):
            sections.append(f"Adverse Reactions: {label['adverse_reactions'][0][:1000]}")
        if label.get("boxed_warning"):
            sections.append(f"Boxed Warning: {label['boxed_warning'][0][:500]}")
        if label.get("contraindications"):
            sections.append(f"Contraindications: {label['contraindications'][0][:500]}")
        if label.get("drug_interactions"):
            sections.append(f"Drug Interactions: {label['drug_interactions'][0][:500]}")

        return "\n\n".join(sections)
    except Exception as e:
        return f"Error fetching label for {drug_name}: {str(e)}"


async def get_adverse_events_context(drug_name: str) -> str:
    """Get adverse events information for context."""
    try:
        params = {
            "search": f'patient.drug.medicinalproduct:"{drug_name}"',
            "count": "patient.reaction.reactionmeddrapt.exact",
            "limit": 20
        }
        data = await fetch_openfda_data("/drug/event.json", params)

        if not data.get("results"):
            return f"No adverse events found for {drug_name}."

        events = []
        total = 0
        for r in data["results"]:
            events.append(f"- {r['term']}: {r['count']} reports")
            total += r["count"]

        return f"Top adverse events reported for {drug_name} (total reports in top 20: {total}):\n" + "\n".join(events)
    except Exception as e:
        return f"Error fetching adverse events for {drug_name}: {str(e)}"


def extract_drug_names(question: str) -> list[str]:
    """Extract potential drug names from a question using common patterns."""
    # This is a simple extraction - the LLM will handle the actual interpretation
    # Common drug name patterns in questions
    import re

    # Look for quoted strings first
    quoted = re.findall(r'"([^"]+)"', question)
    if quoted:
        return quoted

    # Look for common drug question patterns
    patterns = [
        r'(?:about|for|of|with|between|vs\.?|versus)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'([A-Z][a-z]+)\s+(?:vs\.?|versus|and|or)\s+([A-Z][a-z]+)',
    ]

    drugs = []
    for pattern in patterns:
        matches = re.findall(pattern, question)
        for match in matches:
            if isinstance(match, tuple):
                drugs.extend(match)
            else:
                drugs.append(match)

    # Filter out common non-drug words
    stop_words = {'What', 'Which', 'How', 'Does', 'Is', 'Are', 'The', 'FDA', 'Drug', 'Has', 'Have', 'Can', 'Could', 'Would', 'Should'}
    drugs = [d for d in drugs if d not in stop_words]

    return list(set(drugs))


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    current_user = Depends(get_current_user)
):
    """
    Answer a natural language question about FDA drug data using AI.
    Fetches relevant data from OpenFDA and uses Gemini to synthesize an answer.
    """
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if len(question) > 1000:
        raise HTTPException(status_code=400, detail="Question too long (max 1000 characters)")

    # Extract drug names from the question
    drug_names = extract_drug_names(question)

    # Gather context from OpenFDA
    context_parts = []
    sources = []

    for drug_name in drug_names[:3]:  # Limit to 3 drugs to avoid too much context
        label_context = await get_drug_label_context(drug_name)
        if "No FDA label found" not in label_context and "Error" not in label_context:
            context_parts.append(f"=== FDA Label for {drug_name} ===\n{label_context}")
            sources.append(f"FDA Drug Label: {drug_name}")

        events_context = await get_adverse_events_context(drug_name)
        if "No adverse events found" not in events_context and "Error" not in events_context:
            context_parts.append(f"=== Adverse Events for {drug_name} ===\n{events_context}")
            sources.append(f"FDA Adverse Event Reporting System (FAERS): {drug_name}")

    # If no drug names were extracted, try a general search
    if not context_parts:
        # Try to use the first capitalized word as a potential drug name
        words = question.split()
        for word in words:
            if word[0].isupper() and len(word) > 2:
                label_context = await get_drug_label_context(word)
                if "No FDA label found" not in label_context:
                    context_parts.append(f"=== FDA Label for {word} ===\n{label_context}")
                    sources.append(f"FDA Drug Label: {word}")
                    break

    # Build the prompt for the LLM
    context_str = "\n\n".join(context_parts) if context_parts else "No specific FDA data was found for the drugs mentioned in your question."

    prompt = f"""You are Canon, an AI assistant specialized in FDA drug data research. Your role is to answer questions about pharmaceutical drugs based on official FDA data.

USER QUESTION: {question}

FDA DATA CONTEXT:
{context_str}

INSTRUCTIONS:
1. Answer the user's question based ONLY on the FDA data provided above.
2. If the data doesn't contain enough information to fully answer the question, say so clearly.
3. Be specific and cite which drug or data source your answer comes from.
4. If comparing drugs, present the comparison clearly and objectively.
5. For adverse events, remind users that reports don't prove causation.
6. Keep your answer concise but complete.
7. If no relevant FDA data was found, explain what types of questions you can answer.

Provide a helpful, accurate answer:"""

    try:
        # Call Gemini to generate the answer
        answer = _call_gemini_api(prompt)

        # Add default source if none were found
        if not sources:
            sources = ["OpenFDA API (no specific drug data matched)"]

        return QuestionResponse(
            answer=answer,
            sources=sources,
            disclaimer="This information is sourced from the FDA's openFDA database. It is intended for informational purposes only and should not be used as a substitute for professional medical advice, diagnosis, or treatment. Adverse event reports do not prove that a drug caused the reported reaction. Always consult with a qualified healthcare provider."
        )

    except LLMConfigurationError as e:
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Please contact the administrator."
        )
    except LLMAPIError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI service temporarily unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your question: {str(e)}"
        )
