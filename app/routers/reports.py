"""
Report CRUD and Export API Endpoints
Provides endpoints for creating, reading, updating, deleting reports and exporting them in various formats.
"""
from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import base64
import io
from pathlib import Path

from .. import crud, models, schemas
from ..auth import get_current_user
from ..database import get_db
from ..routers.analytics import get_active_brand_id


# Main reports router with /reports prefix
router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

# Separate router for the how-tales-works endpoint (no prefix)
how_tales_works_router = APIRouter(
    tags=["Export"]
)


@router.post("/", response_model=schemas.Report, status_code=201)
def create_report(
    report: schemas.ReportCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new report for the current user."""
    return crud.create_report(db=db, report=report, user_id=current_user.id)


@router.get("/", response_model=List[schemas.Report])
def read_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Retrieve a list of reports for the current user's active brand (including shared brands)."""
    # Import brand_access utility
    from app.utils.brand_access import get_data_owner_user_id

    # Get the data owner user_id (for shared brands, this is the brand owner's ID)
    data_owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    return crud.get_reports(db, user_id=data_owner_user_id, brand_id=brand_id, skip=skip, limit=limit)


def get_report_with_brand_access(db: Session, report_id: int, current_user_id: int, brand_id: Optional[int]) -> models.Report:
    """
    Helper function to get a report with brand access validation.
    Works for both owned and shared brands.
    """
    from app.utils.brand_access import get_data_owner_user_id

    # Get the data owner user_id (for shared brands, this is the brand owner's ID)
    data_owner_user_id = get_data_owner_user_id(db, brand_id, current_user_id)

    # Get the report using the data owner's user_id
    db_report = crud.get_report(db, report_id=report_id, user_id=data_owner_user_id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    return db_report


@router.get("/{report_id}", response_model=schemas.Report)
def read_report(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Retrieve a single report by its ID (supports shared brands)."""
    return get_report_with_brand_access(db, report_id, current_user.id, brand_id)


@router.put("/{report_id}", response_model=schemas.Report)
def update_report(
    report_id: int,
    report_update: schemas.ReportUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Update a report (supports shared brands)."""
    from app.utils.brand_access import get_data_owner_user_id

    # Get the data owner user_id (for shared brands, this is the brand owner's ID)
    data_owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    db_report = crud.update_report(
        db,
        report_id=report_id,
        report_update=report_update,
        user_id=data_owner_user_id
    )
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report


@router.delete("/{report_id}", response_model=schemas.Report)
def delete_report(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Delete a report (supports shared brands)."""
    from app.utils.brand_access import get_data_owner_user_id

    # Get the data owner user_id (for shared brands, this is the brand owner's ID)
    data_owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    deleted_report = crud.delete_report(db, report_id=report_id, user_id=data_owner_user_id)
    if deleted_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return deleted_report


@router.post("/upload-charts")
async def upload_chart_images(
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Upload chart images (as base64 strings) and save them to disk.
    Accepts any number of chart images as form data.

    Format: {brand_name}_{chart_type}_{timestamp}.png
    This matches the format users see when downloading images from the website.
    """
    if not brand_id:
        raise HTTPException(status_code=400, detail="No active brand found")

    # Get brand name
    brand = db.query(models.BrandInfo).filter(models.BrandInfo.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Format brand name for filename (spaces to underscores, remove special chars)
    brand_name_formatted = brand.brand_name.replace(' ', '_').replace('-', '_')
    brand_name_formatted = ''.join(c for c in brand_name_formatted if c.isalnum() or c == '_')

    # Create report_charts directory if it doesn't exist
    charts_dir = Path("frontend/public/report_charts")
    charts_dir.mkdir(parents=True, exist_ok=True)

    # Parse form data
    form_data = await request.form()

    chart_paths = {}
    timestamp = form_data.get('timestamp', '')

    # Process each chart image
    for field_name, value in form_data.items():
        if field_name == 'timestamp':
            continue

        try:
            base64_data = str(value)

            # Remove the data:image/png;base64, prefix if present
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]

            # Decode base64 to binary
            image_data = base64.b64decode(base64_data)

            # Create filename matching website download format
            # Format: {BrandName}_{chart_type}_{timestamp}.png
            filename = f"{brand_name_formatted}_{field_name}_{timestamp}.png"
            filepath = charts_dir / filename

            # Write file
            with open(filepath, 'wb') as f:
                f.write(image_data)

            # Store relative path
            chart_paths[field_name] = f"report_charts/{filename}"

        except Exception as e:
            print(f"Error saving {field_name} chart: {e}")
            continue

    return {
        "success": True,
        "chart_paths": chart_paths,
        "message": f"Uploaded {len(chart_paths)} chart(s) for report generation",
        "brand_name": brand.brand_name
    }


@router.get("/{report_id}/export/word")
def export_report_to_word(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Export a report to Word document format with embedded charts (supports shared brands)."""
    from app.services.report_export import export_to_word_with_charts

    # Get the report with brand access validation
    db_report = get_report_with_brand_access(db, report_id, current_user.id, brand_id)

    # Generate Word document with charts
    word_file = export_to_word_with_charts(
        db_report.report_content,
        db_report.title,
        db,
        user_id=current_user.id,
        brand_id=brand_id
    )

    # Create safe filename
    safe_filename = "".join(c for c in db_report.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_filename}.docx"

    return StreamingResponse(
        word_file,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{report_id}/export/pdf")
def export_report_to_pdf(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Export a report to PDF format (supports shared brands)."""
    from app.services.report_export import export_to_pdf

    # Get the report with brand access validation
    db_report = get_report_with_brand_access(db, report_id, current_user.id, brand_id)

    # Generate PDF
    pdf_file = export_to_pdf(db_report.report_content, db_report.title)

    # Create safe filename
    safe_filename = "".join(c for c in db_report.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_filename}.pdf"

    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{report_id}/export/html")
def export_report_to_html(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Export a report to interactive HTML with embedded Chart.js visualizations (supports shared brands)."""
    from app.services.report_html import generate_html_report_with_charts

    # Get the report with brand access validation
    db_report = get_report_with_brand_access(db, report_id, current_user.id, brand_id)

    # Generate HTML with charts
    html_content = generate_html_report_with_charts(
        db_report.report_content,
        db_report.title,
        db,
        user_id=current_user.id,
        brand_id=brand_id
    )

    # Create safe filename
    safe_filename = "".join(c for c in db_report.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_filename}.html"

    return StreamingResponse(
        io.BytesIO(html_content.encode('utf-8')),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{report_id}/export/pptx")
def export_report_to_pptx(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Export a report to PowerPoint slideshow with embedded PNG charts (supports shared brands)."""
    from app.services.report_slideshow import generate_slideshow

    # Get the report with brand access validation
    db_report = get_report_with_brand_access(db, report_id, current_user.id, brand_id)

    # Generate PowerPoint slideshow
    pptx_file = generate_slideshow(
        db_report.report_content,
        db_report.title,
        db,
        user_id=current_user.id,
        brand_id=brand_id
    )

    # Create safe filename
    safe_filename = "".join(c for c in db_report.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_filename}.pptx"

    return StreamingResponse(
        pptx_file,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@how_tales_works_router.get("/export/how-tales-works/word")
def export_how_tales_works_word(
    current_user: models.User = Depends(get_current_user)
):
    """Export How Tales Works methodology page as Word document."""
    from app.services.report_export import export_to_word

    # Methodology content
    methodology_content = """# How Tales Works

## Data Collection Methods

The analysis of your brand's AI reputation is conducted using the Tales platform, which employs a systematic multi-platform AI querying methodology. Data is collected by submitting strategically designed queries to major large language models. These queries are automatically generated using AI to cover relevant topic areas including leadership and reputation, technology and innovation, and industry positioning.

Critically, most queries are designed as "visibility tests" that deliberately exclude your brand name, allowing the study to measure organic mentions—instances where AI platforms independently reference your organization when answering relevant questions. A list of descriptive words ideally included in AI responses to describe your brand are also automatically generated by AI, as well as a list of your competitors. The queries, descriptors and competitors are all reviewed by a human and edited to ensure they fit your brand's needs. All responses are collected via API with timestamps and platform metadata, enabling temporal and cross-platform comparative analysis.

**Note:** While the Tales platform allows users to assign priority levels (High, Medium, Low) to queries and descriptors for organizational purposes, these priority designations do not impact the quantitative analysis or metric calculations in any way—all queries and descriptors are weighted equally in the analysis.

## Analytical Framework

The collected responses undergo a two-stage analysis process combining structured data extraction with AI-powered insight generation. In the first stage, Perplexity's Sonar model analyzes each response to extract structured data including mention type (direct, indirect, or absent), brand positioning (categorized as leader, top 3, featured, listed, or not mentioned), sentiment classification (very positive, positive, neutral, negative, or mixed), associated descriptors and adjectives, competitor mentions, and cited sources.

This extraction process is context-aware, incorporating your brand's industry context, strategic messaging, target descriptors, and known competitors to ensure relevant and accurate classification. In the second stage, Perplexity's Sonar Pro model synthesizes these structured findings with real-time industry news and comprehensive brand context to generate strategic insights and actionable recommendations, explicitly connecting each finding to specific performance gaps and opportunities.

## Key Performance Metrics

The study calculates multiple quantitative metrics to assess your brand's AI reputation:

- **Mention Rate:** Measures the percentage of responses where the brand is referenced when not explicitly included in the query, indicating organic visibility in AI responses.
- **Sentiment Distribution:** Tracks the breakdown of positive, neutral, and negative associations across all mentions.
- **Brand Positioning:** Analyzes where your brand appears in AI-generated lists and discussions, calculating an average positioning score and leadership visibility percentage.
- **Descriptor Match Rate:** Compares target descriptors that your brand aims to be associated with against descriptors actually used by AI platforms, identifying alignment gaps.
- **Share of Voice:** Quantifies your brand's mentions relative to total organization mentions across all responses, including competitors, with weighting based on positioning strength.

All metrics are segmented by platform to identify which AI systems perform better or worse for your brand.

## Mathematical Formulas for Metric Calculations

### Brand Mentions (Mention Rate)

The mention rate quantifies how frequently your brand is referenced by AI platforms when the brand name is not explicitly included in the query, measuring organic visibility.

**Formula:**

Mention Rate (%) = (Number of Mentions / Total Qualifying Responses) × 100

| Component | Definition |
|-----------|------------|
| Numerator | Count of responses where brand_mentioned field equals 'Yes' OR 'Indirect' |
| Denominator | Total count of all responses in the analysis period |
| Critical Exclusion | Both numerator and denominator exclude responses from queries where brand_in_query = True |
| Rationale | Excluding branded queries prevents inflated mention rates and isolates organic AI platform behavior |

**Example:** If there were 85 total responses from non-branded queries, and your brand was mentioned (directly or indirectly) in 34 of them, the mention rate would be (34/85) × 100 = 40.0%

### Positioning Score

The positioning metric evaluates where your brand appears in AI-generated responses, with higher scores indicating more prominent placement.

**Average Positioning Score Formula:**

Average Positioning Score = (Sum of Individual Position Scores) / Total Responses

**Position Scoring System:**

| Position Category | Point Value |
|-------------------|-------------|
| Leader | 5 points |
| Top 3 | 4 points |
| Featured | 3 points |
| Listed | 2 points |
| Not Mentioned | 1 point |

Each response receives a score (1-5) based on how your brand was positioned. The scores are summed across all qualifying responses and divided by total response count to produce an average (range: 1.0 to 5.0). Responses from queries where brand_in_query = True are excluded.

**Leadership Visibility (Sub-metric):**

Leadership Visibility (%) = ((Leader Count + Top 3 Count) / Total Responses) × 100

This metric specifically measures high-quality visibility by combining the top two positioning categories.

### Share of Voice

Share of Voice quantifies your brand's relative visibility compared to all organizations (including competitors) mentioned across AI responses.

**Formula:**

Share of Voice (%) = (Brand Mentions / Total All Organization Mentions) × 100

| Component | Definition |
|-----------|------------|
| Brand Mentions (Numerator) | Count of responses where your brand achieved positioning of 'Leader', 'Top 3', 'Featured', or 'Listed' |
| Total Mentions (Denominator) | Sum of all organization mentions including: (1) your brand mentions and (2) all competitor mentions |
| Competitor Counting | The competitors field contains comma-separated organization names; each occurrence increments that competitor's mention count |
| Exclusion | Only responses from queries where brand_in_query = False are included |

**Example:** If your brand appeared in 34 responses with qualifying positioning, and competitors appeared in a combined 56 responses, the total mentions would be 90. Your share of voice would be (34/90) × 100 = 37.8%

### Target Descriptor Adoption

Target descriptor adoption measures how successfully your brand has become associated with the specific descriptors and attributes it aims to own strategically.

**Formula:**

Descriptor Match Rate (%) = (Number of Target Descriptors Found / Total Target Descriptors) × 100

| Component | Definition |
|-----------|------------|
| Total Target Descriptors | Count of all descriptors configured as strategic targets for your brand in the platform |
| Target Descriptors Found | Count of unique target descriptors that appear in at least one AI response |
| Matching Logic | Case-insensitive matching; a target descriptor is counted as "found" if it appears in any response where your brand was mentioned |
| Inclusion | This calculation INCLUDES responses from queries where brand_in_query = True (quality of associations matters regardless of query type) |

**Example:** If your brand has 20 target descriptors and 13 of those descriptors appeared in at least one response, the descriptor match rate would be (13/20) × 100 = 65.0%

### Competitive Threat Analysis

Unlike the quantitative metrics above, competitive threat analysis is **not based on a mathematical formula**. Instead, it employs a qualitative AI-powered methodology to identify strategic competitive risks.

**Process:**

1. **Data Collection Phase:** Gathers Share of Voice data showing competitor mention frequencies, identifies specific query-response pairs where your brand was not mentioned but competitors were, and extracts "competitive loss" examples.

2. **AI Analysis Phase:** Submits concrete response examples and competitive data to Perplexity Sonar Pro model, which identifies patterns in which competitors consistently outperform your brand and analyzes the specific descriptors and positioning competitors have claimed.

3. **Output:** Generates qualitative descriptions of top 3-5 competitive threats, specific examples of queries/responses where competitors won visibility, strategic implications, and recommended counter-actions.

**Rationale:** Competitive threats involve nuanced strategic considerations that resist reduction to single numerical scores. The AI-powered qualitative analysis can weigh multidimensional factors more effectively than a predetermined formula, while remaining data-driven and grounded in actual response examples.

### Summary of Metric Calculation Approaches

| Metric | Type | Includes Branded Queries? | Rationale |
|--------|------|---------------------------|-----------|
| Mention Rate | Quantitative Formula | No (Excluded) | Measures organic visibility without bias |
| Positioning Score | Quantitative Formula | No (Excluded) | Assesses natural positioning |
| Share of Voice | Quantitative Formula | No (Excluded) | Compares competitive visibility organically |
| Descriptor Match | Quantitative Formula | Yes (Included) | Quality of associations matters regardless of query type |
| Sentiment Distribution | Quantitative Formula | Yes (Included) | Sentiment reflects perception across all contexts |
| Competitive Threats | Qualitative AI Analysis | Context-dependent | Strategic nuance requires pattern recognition |

## Competitive Intelligence Analysis

Competitor analysis forms a critical component of the methodology, examining how your brand performs relative to other organizations in AI-generated discourse. The system tracks pre-configured competitors with metadata including organization type, focus areas, and key descriptors, while also automatically extracting mentions of organizations not initially identified as competitors.

Co-occurrence analysis reveals which competitors frequently appear alongside your brand in AI responses, and comparative share of voice calculations quantify relative visibility. The analysis identifies specific queries where competitors received more favorable positioning than your brand, extracts the descriptors and positioning competitors own, and examines concrete response examples showing competitive advantages. These findings enable the generation of targeted recommendations for closing competitive gaps and claiming strategic positioning currently owned by rivals.

## Recommendations Generation

The strategic recommendations produced for your brand result from a sophisticated AI-driven synthesis process that connects quantitative performance data with qualitative strategic context. The system performs gap analysis comparing target descriptors against actual usage, diagnoses which AI platforms underperform and infers why based on response patterns, benchmarks competitive positioning to identify claimable strategic territory, analyzes source types that different platforms prioritize, and incorporates real-time industry developments to identify timely opportunities.

Each recommendation includes strategic rationale backed by specific metrics, four to five tactical action steps with measurable targets, explicit alignment with target descriptors your brand aims to reinforce, source strategies specifying what content to create and where to publish it, and platform targeting identifying which AI systems each tactic aims to influence. This approach ensures recommendations are data-driven, actionable, and directly tied to measurable improvements in AI reputation metrics.

## Limitations and Considerations

Several important limitations should be considered when interpreting these findings. AI platform responses can vary over time due to model updates, training data changes, and index refreshes, meaning that findings represent a snapshot rather than static characteristics. Finally, while the analysis identifies correlations between content strategies and AI reputation metrics, establishing direct causation requires controlled longitudinal studies that account for confounding variables such as broader industry trends, news coverage, and publication timing effects.
"""

    # Generate Word document
    word_file = export_to_word(methodology_content, "How Tales Works")

    return StreamingResponse(
        word_file,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=How_Tales_Works.docx"}
    )
