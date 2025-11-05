"""
HTML Report Export Service with Charts
Generates beautiful HTML reports with embedded charts using Chart.js
"""

import io
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from .. import analytics

def generate_html_report_with_charts(
    markdown_content: str,
    title: str,
    db: Session,
    user_id: int,
    brand_id: Optional[int] = None
) -> str:
    """
    Generate an HTML report with embedded charts from analytics data.

    Args:
        markdown_content: The markdown report content
        title: Report title
        db: Database session
        user_id: User ID for fetching analytics data
        brand_id: Brand ID for filtering analytics data

    Returns:
        HTML string with embedded charts
    """
    from app import models

    # Fetch analytics data
    sentiment_data = analytics.get_sentiment_breakdown(db, user_id=user_id, brand_id=brand_id) or {}
    positioning_data = analytics.get_positioning_breakdown(db, user_id=user_id, brand_id=brand_id)
    sov_data = analytics.get_share_of_voice(db, user_id=user_id, brand_id=brand_id)
    dashboard_data = analytics.get_dashboard_metrics(db, user_id=user_id, brand_id=brand_id)

    # Handle share_of_voice being either dict or list
    if isinstance(sov_data, list):
        # If it's a list, we can't use it for placeholders
        brand_sov = 0
    elif isinstance(sov_data, dict):
        brand_sov = sov_data.get('brand_sov', 0)
    else:
        brand_sov = 0

    # Get brand name
    brand_name = "Your Brand"  # Default
    if brand_id:
        brand = db.query(models.BrandInfo).filter(models.BrandInfo.id == brand_id).first()
        if brand:
            brand_name = brand.brand_name

    # Calculate positive sentiment rate (very_positive + positive)
    positive_sentiment_rate = sentiment_data.get('very_positive_pct', 0) + sentiment_data.get('positive_pct', 0)

    # Replace placeholders in markdown content
    markdown_content = markdown_content.replace('{brand_name}', brand_name)
    markdown_content = markdown_content.replace('{positive_sentiment_rate}', str(positive_sentiment_rate))
    markdown_content = markdown_content.replace('{descriptor_match_rate}', str(sentiment_data.get('descriptor_match_rate', 0)))
    markdown_content = markdown_content.replace('{share_of_voice[\'brand_sov\']}', str(brand_sov))

    # Convert markdown to HTML (simple conversion)
    html_content = markdown_to_html(markdown_content)

    # Prepare chart data as JSON
    sentiment_chart_data = prepare_sentiment_chart_data(sentiment_data)
    positioning_chart_data = prepare_positioning_chart_data(positioning_data)
    sov_chart_data = prepare_sov_chart_data(sov_data)

    # Generate HTML template
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .page-break {{
                page-break-before: always;
            }}
            .no-print {{
                display: none;
            }}
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
        }}

        .header {{
            background: linear-gradient(135deg, #665775 0%, #80a1d4 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}

        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}

        .header .subtitle {{
            margin-top: 10px;
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}

        .metric-card {{
            background: #f8f9fa;
            border-left: 4px solid #665775;
            padding: 20px;
            border-radius: 8px;
        }}

        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #665775;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .metric-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }}

        .metric-card .label {{
            color: #666;
            font-size: 0.9em;
        }}

        .chart-container {{
            margin: 40px 0;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .chart-container h2 {{
            color: #665775;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}

        .chart-wrapper {{
            position: relative;
            height: 400px;
            margin: 20px 0;
        }}

        .report-content {{
            margin: 40px 0;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .report-content h1 {{
            color: #665775;
            border-bottom: 3px solid #75c9c8;
            padding-bottom: 10px;
            margin-top: 30px;
        }}

        .report-content h2 {{
            color: #80a1d4;
            margin-top: 25px;
        }}

        .report-content h3 {{
            color: #665775;
            margin-top: 20px;
        }}

        .report-content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        .report-content table th {{
            background: #665775;
            color: white;
            padding: 12px;
            text-align: left;
        }}

        .report-content table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }}

        .report-content table tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        .footer {{
            margin-top: 50px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}

        .print-button {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #665775;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.3s;
        }}

        .print-button:hover {{
            background: #80a1d4;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <button class="print-button no-print" onclick="window.print()">Print / Save as PDF</button>

    <div class="header">
        <h1>{title}</h1>
        <div class="subtitle">AI Brand Analysis Report with Visual Analytics</div>
    </div>

    <!-- Report Content -->
    <div class="report-content">
        {html_content}
    </div>

    <div class="footer">
        <p>Generated by TALES - AI Brand Analysis Platform</p>
        <p>Report created: {dashboard_data.get('report_date', 'N/A')}</p>
    </div>
</body>
</html>
"""

    return html


def markdown_to_html(markdown_content: str, embed_images: bool = True) -> str:
    """
    Convert markdown to HTML (simple conversion)

    Args:
        markdown_content: Markdown content to convert
        embed_images: If True, embed images as base64 data URLs for standalone HTML
    """
    import re
    import os
    import base64

    html = markdown_content

    # Convert image markdown to HTML img tags
    def convert_image(match):
        alt_text = match.group(1)
        image_path = match.group(2)

        # Convert web path to filesystem path
        if image_path.startswith('report_charts/'):
            full_path = os.path.join('frontend', 'public', image_path)
        elif os.path.exists(image_path):
            full_path = image_path
        else:
            # Try with frontend/public prefix
            full_path = os.path.join('frontend', 'public', image_path)

        # Embed as base64 for standalone HTML
        if embed_images and os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                    return f'<img src="data:image/png;base64,{img_data}" alt="{alt_text}" style="max-width: 100%; height: auto; margin: 20px 0; display: block;">'
            except Exception as e:
                print(f"Warning: Could not embed image {full_path}: {e}")

        # Fallback to web path
        if image_path.startswith('report_charts/'):
            web_path = '/' + image_path
        else:
            web_path = image_path

        return f'<img src="{web_path}" alt="{alt_text}" style="max-width: 100%; height: auto; margin: 20px 0; display: block;">'

    html = re.sub(r'!\[(.*?)\]\((.*?)\)', convert_image, html)

    # Process tables first (before other conversions)
    def convert_tables(text):
        lines = text.split('\n')
        result = []
        in_table = False
        table_rows = []

        for i, line in enumerate(lines):
            if '|' in line and line.strip().startswith('|'):
                # This is a table row
                if not in_table:
                    in_table = True
                    table_rows = []
                table_rows.append(line)
            else:
                # Not a table row
                if in_table:
                    # End of table, convert it
                    if len(table_rows) >= 2:
                        # Parse table
                        header_row = table_rows[0]
                        separator_row = table_rows[1] if len(table_rows) > 1 else None
                        data_rows = table_rows[2:] if len(table_rows) > 2 else []

                        # Build HTML table
                        table_html = '<table style="width:100%; border-collapse: collapse; margin: 20px 0;">\n'

                        # Header
                        if header_row:
                            cells = [cell.strip() for cell in header_row.split('|')[1:-1]]
                            table_html += '<thead><tr>'
                            for cell in cells:
                                table_html += f'<th style="border: 1px solid #ddd; padding: 12px; text-align: left; background-color: #665775; color: white; font-weight: bold;">{cell}</th>'
                            table_html += '</tr></thead>\n'

                        # Data rows
                        if data_rows:
                            table_html += '<tbody>'
                            for row in data_rows:
                                cells = [cell.strip() for cell in row.split('|')[1:-1]]
                                table_html += '<tr>'
                                for cell in cells:
                                    table_html += f'<td style="border: 1px solid #ddd; padding: 12px; text-align: left;">{cell}</td>'
                                table_html += '</tr>\n'
                            table_html += '</tbody>'

                        table_html += '</table>'
                        result.append(table_html)

                    in_table = False
                    table_rows = []

                result.append(line)

        # Handle case where table is at end of content
        if in_table and len(table_rows) >= 2:
            header_row = table_rows[0]
            data_rows = table_rows[2:] if len(table_rows) > 2 else []

            table_html = '<table style="width:100%; border-collapse: collapse; margin: 20px 0;">\n'

            if header_row:
                cells = [cell.strip() for cell in header_row.split('|')[1:-1]]
                table_html += '<thead><tr>'
                for cell in cells:
                    table_html += f'<th style="border: 1px solid #ddd; padding: 12px; text-align: left; background-color: #665775; color: white; font-weight: bold;">{cell}</th>'
                table_html += '</tr></thead>\n'

            if data_rows:
                table_html += '<tbody>'
                for row in data_rows:
                    cells = [cell.strip() for cell in row.split('|')[1:-1]]
                    table_html += '<tr>'
                    for cell in cells:
                        table_html += f'<td style="border: 1px solid #ddd; padding: 12px; text-align: left;">{cell}</td>'
                    table_html += '</tr>\n'
                table_html += '</tbody>'

            table_html += '</table>'
            result.append(table_html)

        return '\n'.join(result)

    html = convert_tables(html)

    # Headers (process from most specific to least specific)
    html = re.sub(r'^#### (.*?)$', r'<strong>\1</strong>', html, flags=re.MULTILINE)  # Convert #### to bold instead
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)

    # Bullet points
    html = re.sub(r'^\- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)

    # Paragraphs
    html = re.sub(r'\n\n', '</p><p>', html)
    html = f'<p>{html}</p>'

    return html


def prepare_sentiment_chart_data(sentiment_data: Dict[str, Any]) -> str:
    """Prepare sentiment data for Chart.js"""
    colors = {
        'Very Positive': '#116C29',  # Bright highlighter green
        'Positive': '#58A13B',       # Extended green (formerly Very Positive)
        'Neutral': '#9FA8DA',
        'Negative': '#E04320',
        'Very Negative': '#EA4A4A',
        'Mixed': '#75C9C8'
    }

    # Build breakdown from flat structure
    breakdown = {}
    if sentiment_data.get('very_positive', 0) > 0:
        breakdown['Very Positive'] = sentiment_data['very_positive']
    if sentiment_data.get('positive', 0) > 0:
        breakdown['Positive'] = sentiment_data['positive']
    if sentiment_data.get('neutral', 0) > 0:
        breakdown['Neutral'] = sentiment_data['neutral']
    if sentiment_data.get('mixed', 0) > 0:
        breakdown['Mixed'] = sentiment_data['mixed']
    if sentiment_data.get('negative', 0) > 0:
        breakdown['Negative'] = sentiment_data['negative']
    if sentiment_data.get('very_negative', 0) > 0:
        breakdown['Very Negative'] = sentiment_data['very_negative']

    data = {
        'labels': list(breakdown.keys()),
        'datasets': [{
            'label': 'Sentiment Distribution',
            'data': list(breakdown.values()),
            'backgroundColor': [colors.get(label, '#999') for label in breakdown.keys()],
            'borderWidth': 2,
            'borderColor': '#fff'
        }]
    }

    return json.dumps(data)


def prepare_positioning_chart_data(positioning_data: Dict[str, Any]) -> str:
    """Prepare positioning data for Chart.js"""
    colors = {
        'Leader': '#116C29',  # Bright highlighter green
        'Top 3': '#44809C',
        'Featured': '#75C9C8',
        'Listed': '#80A1D4',
        'Not Mentioned': '#665775'
    }

    # Build breakdown from flat structure
    breakdown = {}
    if positioning_data.get('leader', 0) > 0:
        breakdown['Leader'] = positioning_data['leader']
    if positioning_data.get('top_3', 0) > 0:
        breakdown['Top 3'] = positioning_data['top_3']
    if positioning_data.get('featured', 0) > 0:
        breakdown['Featured'] = positioning_data['featured']
    if positioning_data.get('listed', 0) > 0:
        breakdown['Listed'] = positioning_data['listed']
    if positioning_data.get('not_mentioned', 0) > 0:
        breakdown['Not Mentioned'] = positioning_data['not_mentioned']

    data = {
        'labels': list(breakdown.keys()),
        'datasets': [{
            'label': 'Number of Mentions',
            'data': list(breakdown.values()),
            'backgroundColor': [colors.get(label, '#999') for label in breakdown.keys()],
            'borderWidth': 1,
            'borderColor': '#fff'
        }]
    }

    return json.dumps(data)


def prepare_sov_chart_data(sov_data: list) -> str:
    """Prepare share of voice data for Chart.js"""
    if not sov_data:
        return json.dumps({'labels': [], 'datasets': []})

    # Sort by mention count
    sorted_data = sorted(sov_data, key=lambda x: x.get('mention_count', 0), reverse=True)

    # Separate brand and competitors
    labels = [item.get('name', 'Unknown') for item in sorted_data]
    values = [item.get('mention_count', 0) for item in sorted_data]
    colors_list = ['#665775' if item.get('is_brand') else '#80a1d4' for item in sorted_data]

    data = {
        'labels': labels,
        'datasets': [{
            'label': 'Mentions',
            'data': values,
            'backgroundColor': colors_list,
            'borderWidth': 1,
            'borderColor': '#fff'
        }]
    }

    return json.dumps(data)
