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
    brand_id: Optional[int] = None
) -> str:
    """
    Generate an HTML report with embedded charts from analytics data.

    Args:
        markdown_content: The markdown report content
        title: Report title
        db: Database session
        brand_id: Brand ID for filtering analytics data

    Returns:
        HTML string with embedded charts
    """

    # Fetch analytics data
    sentiment_data = analytics.get_sentiment_breakdown(db, brand_id=brand_id)
    positioning_data = analytics.get_positioning_breakdown(db, brand_id=brand_id)
    sov_data = analytics.get_share_of_voice(db, brand_id=brand_id)
    dashboard_data = analytics.get_dashboard_metrics(db, brand_id=brand_id)

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

    <div class="metrics-grid">
        <div class="metric-card">
            <h3>Total Responses</h3>
            <div class="value">{dashboard_data.get('total_responses', 0)}</div>
            <div class="label">AI responses analyzed</div>
        </div>
        <div class="metric-card">
            <h3>Mention Rate</h3>
            <div class="value">{dashboard_data.get('mention_rate', 0):.1f}%</div>
            <div class="label">Brand visibility</div>
        </div>
        <div class="metric-card">
            <h3>Positioning Score</h3>
            <div class="value">{positioning_data.get('average_score', 0):.2f}</div>
            <div class="label">Out of 5.0</div>
        </div>
    </div>

    <!-- Sentiment Analysis Chart -->
    <div class="chart-container page-break">
        <h2>Sentiment Distribution</h2>
        <div class="chart-wrapper">
            <canvas id="sentimentChart"></canvas>
        </div>
    </div>

    <!-- Positioning Analysis Chart -->
    <div class="chart-container">
        <h2>Brand Positioning Breakdown</h2>
        <div class="chart-wrapper">
            <canvas id="positioningChart"></canvas>
        </div>
    </div>

    <!-- Share of Voice Chart -->
    <div class="chart-container page-break">
        <h2>Share of Voice Analysis</h2>
        <div class="chart-wrapper">
            <canvas id="sovChart"></canvas>
        </div>
    </div>

    <!-- Report Content -->
    <div class="report-content page-break">
        {html_content}
    </div>

    <div class="footer">
        <p>Generated by TALES - AI Brand Analysis Platform</p>
        <p>Report created: {dashboard_data.get('report_date', 'N/A')}</p>
    </div>

    <script>
        // Sentiment Chart
        const sentimentCtx = document.getElementById('sentimentChart').getContext('2d');
        new Chart(sentimentCtx, {{
            type: 'pie',
            data: {sentiment_chart_data},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                    }},
                    title: {{
                        display: false
                    }}
                }}
            }}
        }});

        // Positioning Chart
        const positioningCtx = document.getElementById('positioningChart').getContext('2d');
        new Chart(positioningCtx, {{
            type: 'bar',
            data: {positioning_chart_data},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Mentions'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Positioning Category'
                        }}
                    }}
                }}
            }}
        }});

        // Share of Voice Chart
        const sovCtx = document.getElementById('sovChart').getContext('2d');
        new Chart(sovCtx, {{
            type: 'bar',
            data: {sov_chart_data},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Mentions'
                        }}
                    }},
                    y: {{
                        title: {{
                            display: true,
                            text: 'Brand / Competitor'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    return html


def markdown_to_html(markdown_content: str) -> str:
    """Convert markdown to HTML (simple conversion)"""
    import re

    html = markdown_content

    # Headers
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

    # Tables (simple markdown tables)
    html = html.replace('|', '</td><td>')

    return html


def prepare_sentiment_chart_data(sentiment_data: Dict[str, Any]) -> str:
    """Prepare sentiment data for Chart.js"""
    breakdown = sentiment_data.get('breakdown', {})

    colors = {
        'Very Positive': '#4caf50',
        'Positive': '#8bc34a',
        'Neutral': '#9e9e9e',
        'Negative': '#ff9800',
        'Very Negative': '#f44336',
        'Mixed': '#2196f3'
    }

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
    breakdown = positioning_data.get('breakdown', {})

    colors = {
        'Leader': '#4caf50',
        'Top 3': '#8bc34a',
        'Featured': '#2196f3',
        'Listed': '#ff9800',
        'Not Mentioned': '#f44336'
    }

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
