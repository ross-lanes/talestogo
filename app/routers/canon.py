"""
Canon - FDA Drug Data Research API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import httpx
import json
import io
import logging
from docx import Document

from app.services.llm_service import _call_perplexity_api, LLMConfigurationError, LLMAPIError
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/canon", tags=["canon"])

# OpenFDA API base URL
OPENFDA_BASE_URL = "https://api.fda.gov"


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    answer: str
    sources: list[str]
    disclaimer: str


class DocumentIssue(BaseModel):
    category: str  # 'accuracy', 'outdated', 'missing', 'warning'
    severity: str  # 'high', 'medium', 'low'
    text_excerpt: str
    issue_description: str
    fda_reference: str


class DocumentCheckResponse(BaseModel):
    drug_name: str
    fda_label_date: Optional[str]
    fda_set_id: Optional[str]
    dailymed_url: Optional[str]
    document_text_preview: str
    issues: List[DocumentIssue]
    summary: str
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
    Fetches relevant data from OpenFDA and uses Perplexity to synthesize an answer.
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
        # Call Perplexity to generate the answer
        answer = _call_perplexity_api(prompt)

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


async def get_full_drug_label(drug_name: str) -> dict:
    """Get comprehensive drug label information including metadata."""
    params = {
        "search": f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"',
        "limit": 1
    }
    data = await fetch_openfda_data("/drug/label.json", params)

    if not data.get("results"):
        return None

    label = data["results"][0]
    openfda = label.get("openfda", {})

    # Format the effective date
    effective_time = label.get("effective_time")
    formatted_date = None
    if effective_time and len(effective_time) == 8:
        formatted_date = f"{effective_time[:4]}-{effective_time[4:6]}-{effective_time[6:8]}"

    return {
        "brand_name": openfda.get("brand_name", ["Unknown"])[0],
        "generic_name": openfda.get("generic_name", [None])[0],
        "manufacturer": openfda.get("manufacturer_name", [None])[0],
        "effective_time": effective_time,
        "formatted_date": formatted_date,
        "set_id": label.get("set_id"),
        "version": label.get("version"),
        "indications_and_usage": label.get("indications_and_usage", []),
        "warnings": label.get("warnings", []),
        "adverse_reactions": label.get("adverse_reactions", []),
        "boxed_warning": label.get("boxed_warning", []),
        "contraindications": label.get("contraindications", []),
        "drug_interactions": label.get("drug_interactions", []),
        "dosage_and_administration": label.get("dosage_and_administration", []),
        "warnings_and_cautions": label.get("warnings_and_cautions", []),
    }


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text content from a Word document."""
    doc = Document(io.BytesIO(file_content))
    paragraphs = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text.strip())
    return "\n\n".join(paragraphs)


@router.post("/check-document", response_model=DocumentCheckResponse)
async def check_document(
    file: UploadFile = File(...),
    drug_name: str = Form(...),
    current_user = Depends(get_current_user)
):
    """
    Check a Word document against FDA drug label data.
    Analyzes claims in the document for accuracy against official FDA information.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="File must be a Word document (.docx)"
        )

    # Validate drug name
    drug_name = drug_name.strip()
    if not drug_name:
        raise HTTPException(status_code=400, detail="Drug name is required")

    # Read and extract document text
    try:
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")

        if len(file_content) > 10 * 1024 * 1024:  # 10 MB limit
            raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

        document_text = extract_text_from_docx(file_content)

        if not document_text.strip():
            raise HTTPException(status_code=400, detail="Document appears to be empty or contains no readable text")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading document: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Could not read document. Please ensure it's a valid .docx file."
        )

    # Fetch FDA label data
    fda_label = await get_full_drug_label(drug_name)

    if not fda_label:
        raise HTTPException(
            status_code=404,
            detail=f"No FDA label found for '{drug_name}'. Please check the drug name spelling."
        )

    # Build DailyMed URL
    dailymed_url = None
    if fda_label.get("set_id"):
        dailymed_url = f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={fda_label['set_id']}"

    # Build comprehensive FDA context for the LLM
    fda_context_parts = [
        f"Drug: {fda_label['brand_name']}",
    ]
    if fda_label.get("generic_name"):
        fda_context_parts.append(f"Generic Name: {fda_label['generic_name']}")
    if fda_label.get("manufacturer"):
        fda_context_parts.append(f"Manufacturer: {fda_label['manufacturer']}")
    if fda_label.get("formatted_date"):
        fda_context_parts.append(f"Label Effective Date: {fda_label['formatted_date']}")

    # Add all label sections
    section_map = {
        "indications_and_usage": "INDICATIONS AND USAGE",
        "boxed_warning": "BOXED WARNING",
        "warnings": "WARNINGS",
        "warnings_and_cautions": "WARNINGS AND PRECAUTIONS",
        "adverse_reactions": "ADVERSE REACTIONS",
        "contraindications": "CONTRAINDICATIONS",
        "drug_interactions": "DRUG INTERACTIONS",
        "dosage_and_administration": "DOSAGE AND ADMINISTRATION",
    }

    for key, title in section_map.items():
        content = fda_label.get(key, [])
        if content:
            # Truncate very long sections
            text = content[0][:3000] if len(content[0]) > 3000 else content[0]
            fda_context_parts.append(f"\n=== {title} ===\n{text}")

    fda_context = "\n".join(fda_context_parts)

    # Truncate document text for prompt if too long
    doc_text_for_prompt = document_text[:8000] if len(document_text) > 8000 else document_text

    # Build the analysis prompt
    prompt = f"""You are Canon, an expert medical/regulatory document reviewer. Your task is to check a document's claims about a pharmaceutical drug against official FDA label data.

DRUG: {drug_name}
FDA LABEL EFFECTIVE DATE: {fda_label.get('formatted_date', 'Unknown')}

=== FDA LABEL DATA ===
{fda_context}

=== DOCUMENT TO CHECK ===
{doc_text_for_prompt}

=== INSTRUCTIONS ===
Analyze the document for:
1. **Accuracy Issues**: Claims that contradict or misrepresent FDA label information
2. **Outdated Information**: Information that may have changed based on the FDA label date
3. **Missing Information**: Critical safety information (boxed warnings, contraindications) that should be included
4. **Off-Label Claims**: Statements about uses not approved in the indications section

For each issue found, provide:
- Category: 'accuracy', 'outdated', 'missing', or 'warning'
- Severity: 'high' (safety-critical), 'medium' (significant), or 'low' (minor)
- The exact text excerpt from the document (keep brief, max 100 characters)
- Description of the issue
- What the FDA label actually says

Respond with valid JSON in this exact format:
{{
    "issues": [
        {{
            "category": "accuracy",
            "severity": "high",
            "text_excerpt": "quote from document",
            "issue_description": "description of what's wrong",
            "fda_reference": "what the FDA label says"
        }}
    ],
    "summary": "Overall assessment of the document's accuracy (2-3 sentences)"
}}

If no issues are found, return an empty issues array with a positive summary.
Important: Respond ONLY with valid JSON, no other text."""

    try:
        # Call AI to analyze
        response_text = _call_perplexity_api(prompt)

        # Clean the response - remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Parse the JSON response
        analysis = json.loads(response_text)

        issues = []
        for issue_data in analysis.get("issues", []):
            issues.append(DocumentIssue(
                category=issue_data.get("category", "accuracy"),
                severity=issue_data.get("severity", "medium"),
                text_excerpt=issue_data.get("text_excerpt", "")[:200],
                issue_description=issue_data.get("issue_description", ""),
                fda_reference=issue_data.get("fda_reference", "")
            ))

        summary = analysis.get("summary", "Analysis complete.")

        return DocumentCheckResponse(
            drug_name=fda_label["brand_name"],
            fda_label_date=fda_label.get("formatted_date"),
            fda_set_id=fda_label.get("set_id"),
            dailymed_url=dailymed_url,
            document_text_preview=document_text[:500] + ("..." if len(document_text) > 500 else ""),
            issues=issues,
            summary=summary,
            disclaimer="This analysis is based on FDA label data from openFDA. It is intended as a reference tool only and should not replace professional medical/legal/regulatory review. Always verify findings against the official FDA label."
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {str(e)}")
        logger.error(f"Raw response: {response_text[:500]}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze document. Please try again."
        )
    except LLMConfigurationError:
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
        logger.error(f"Error checking document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while checking the document: {str(e)}"
        )
