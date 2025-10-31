"""
Chart generation service for TALES reports.
Generates PNG charts for inclusion in markdown reports.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server-side rendering
import matplotlib.pyplot as plt
import os
from typing import Dict, List, Any
from datetime import datetime

# Set style for professional-looking charts
plt.style.use('seaborn-v0_8-darkgrid')

# Color palette - professional blues and grays
COLORS = {
    'primary': '#1976d2',
    'secondary': '#42a5f5',
    'success': '#66bb6a',
    'warning': '#ffa726',
    'danger': '#ef5350',
    'neutral': '#78909c',
    'palette': ['#1976d2', '#42a5f5', '#66bb6a', '#ffa726', '#ef5350', '#78909c', '#9575cd', '#4db6ac']
}


def ensure_charts_directory():
    """Ensure the charts output directory exists."""
    charts_dir = "report_charts"
    if not os.path.exists(charts_dir):
        os.makedirs(charts_dir)
    return charts_dir


def generate_mention_rate_pie_chart(mention_metrics: Dict[str, Any], brand_name: str, output_path: str) -> str:
    """
    Generate a pie chart showing brand mention rates.
    Returns the file path of the generated chart.
    """
    labels = ['Explicit Mention', 'Indirect Mention', 'Not Mentioned']
    sizes = [mention_metrics['yes'], mention_metrics['indirect'], mention_metrics['no']]
    colors = [COLORS['success'], COLORS['warning'], COLORS['danger']]
    explode = (0.05, 0, 0)  # Explode the first slice

    fig, ax = plt.subplots(figsize=(10, 7))
    wedges, texts, autotexts = ax.pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 12, 'weight': 'bold'}
    )

    # Make percentage text white and bold
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(14)
        autotext.set_weight('bold')

    ax.set_title(f'{brand_name} Mention Rate in AI Responses', fontsize=16, weight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return output_path


def generate_positioning_bar_chart(positioning_metrics: Dict[str, Any], brand_name: str, output_path: str) -> str:
    """
    Generate a bar chart showing brand positioning distribution.
    Returns the file path of the generated chart.
    """
    positions = ['Leader', 'Top 3', 'Featured', 'Listed', 'Not Mentioned']
    counts = [
        positioning_metrics['leader'],
        positioning_metrics['top_3'],
        positioning_metrics['featured'],
        positioning_metrics['listed'],
        positioning_metrics['not_mentioned']
    ]

    colors_map = [COLORS['success'], COLORS['primary'], COLORS['secondary'], COLORS['warning'], COLORS['danger']]

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(positions, counts, color=colors_map, edgecolor='white', linewidth=2)

    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=12, weight='bold')

    ax.set_ylabel('Number of Responses', fontsize=13, weight='bold')
    ax.set_xlabel('Positioning Category', fontsize=13, weight='bold')
    ax.set_title(f'{brand_name} Positioning in AI Responses', fontsize=16, weight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return output_path


def generate_sentiment_pie_chart(sentiment_metrics: Dict[str, Any], brand_name: str, output_path: str) -> str:
    """
    Generate a compact pie chart showing sentiment distribution with labels inside slices.
    Returns the file path of the generated chart.
    """
    labels = ['Very Positive', 'Positive', 'Neutral', 'Negative', 'Mixed']
    sizes = [
        sentiment_metrics['very_positive'],
        sentiment_metrics['positive'],
        sentiment_metrics['neutral'],
        sentiment_metrics['negative'],
        sentiment_metrics['mixed']
    ]

    # Filter out zero values
    filtered_data = [(label, size) for label, size in zip(labels, sizes) if size > 0]
    if not filtered_data:
        return None

    labels, sizes = zip(*filtered_data)
    colors = [COLORS['success'], COLORS['primary'], COLORS['neutral'], COLORS['danger'], COLORS['warning']][:len(labels)]

    # Calculate percentages
    total = sum(sizes)
    percentages = [(size / total) * 100 for size in sizes]

    # Create compact pie chart
    fig, ax = plt.subplots(figsize=(6, 5))

    # Create pie chart with percentage labels inside
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 9},
        pctdistance=0.85  # Position percentage labels closer to center
    )

    # Style the labels - category names outside
    for text in texts:
        text.set_fontsize(9)
        text.set_weight('bold')

    # Style the percentage labels - white and bold
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_weight('bold')

    ax.set_title(f'Sentiment Distribution\n{brand_name}', fontsize=11, weight='bold', pad=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()

    return output_path


def generate_platform_comparison_chart(platform_metrics: Dict[str, Dict[str, Any]], brand_name: str, output_path: str) -> str:
    """
    Generate a grouped bar chart comparing performance across platforms.
    Returns the file path of the generated chart.
    """
    platforms = [p for p, m in platform_metrics.items() if m['total'] > 0]

    if not platforms:
        return None

    mention_rates = [platform_metrics[p]['mention']['yes_pct'] for p in platforms]
    positive_sentiment = [
        platform_metrics[p]['sentiment']['positive_pct'] + platform_metrics[p]['sentiment']['very_positive_pct']
        for p in platforms
    ]
    leader_positioning = [
        platform_metrics[p]['positioning']['leader_pct'] + platform_metrics[p]['positioning']['top_3_pct']
        for p in platforms
    ]

    x = range(len(platforms))
    width = 0.25

    fig, ax = plt.subplots(figsize=(14, 8))

    bars1 = ax.bar([i - width for i in x], mention_rates, width, label='Mention Rate (%)',
                    color=COLORS['primary'], edgecolor='white', linewidth=1.5)
    bars2 = ax.bar(x, positive_sentiment, width, label='Positive Sentiment (%)',
                    color=COLORS['success'], edgecolor='white', linewidth=1.5)
    bars3 = ax.bar([i + width for i in x], leader_positioning, width, label='Leader/Top 3 (%)',
                    color=COLORS['secondary'], edgecolor='white', linewidth=1.5)

    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%',
                        ha='center', va='bottom', fontsize=10, weight='bold')

    ax.set_ylabel('Percentage (%)', fontsize=13, weight='bold')
    ax.set_xlabel('Platform', fontsize=13, weight='bold')
    ax.set_title(f'{brand_name} Performance by Platform', fontsize=16, weight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(platforms, fontsize=12)
    ax.legend(fontsize=11, loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, min(100, max(mention_rates + positive_sentiment + leader_positioning) * 1.15))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return output_path


def generate_share_of_voice_chart(share_of_voice: Dict[str, Any], brand_name: str, output_path: str) -> str:
    """
    Generate a horizontal bar chart showing share of voice.
    Returns the file path of the generated chart.
    """
    # Prepare data: brand + top 5 competitors
    organizations = [brand_name]
    sov_percentages = [share_of_voice['brand_sov']]

    for comp_name, data in list(share_of_voice['competitor_sov'].items())[:5]:
        organizations.append(comp_name)
        sov_percentages.append(data['sov'])

    # Sort by SOV descending
    sorted_data = sorted(zip(organizations, sov_percentages), key=lambda x: x[1], reverse=True)
    organizations, sov_percentages = zip(*sorted_data)

    # Color brand differently
    colors = [COLORS['primary'] if org == brand_name else COLORS['neutral'] for org in organizations]

    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(organizations, sov_percentages, color=colors, edgecolor='white', linewidth=2)

    # Add value labels
    for i, (bar, sov) in enumerate(zip(bars, sov_percentages)):
        width = bar.get_width()
        ax.text(width + 0.5, bar.get_y() + bar.get_height()/2.,
                f'{sov:.1f}%',
                ha='left', va='center', fontsize=12, weight='bold')

    ax.set_xlabel('Share of Voice (%)', fontsize=13, weight='bold')
    ax.set_title('Share of Voice: Brand vs. Competitors', fontsize=16, weight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # Highlight brand name in bold
    ylabels = [f'**{org}**' if org == brand_name else org for org in organizations]
    ax.set_yticks(range(len(organizations)))
    ax.set_yticklabels(organizations, fontsize=11, weight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return output_path


def generate_descriptor_performance_chart(descriptor_analysis: Dict[str, int], brand_name: str, output_path: str, top_n: int = 10) -> str:
    """
    Generate a horizontal bar chart showing top descriptors associated with the brand.
    Returns the file path of the generated chart.
    """
    if not descriptor_analysis:
        return None

    # Get top N descriptors
    sorted_descriptors = sorted(descriptor_analysis.items(), key=lambda x: x[1], reverse=True)[:top_n]

    if not sorted_descriptors:
        return None

    descriptors, counts = zip(*sorted_descriptors)

    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(range(len(descriptors)), counts, color=COLORS['primary'], edgecolor='white', linewidth=2)

    # Add value labels
    for bar, count in zip(bars, counts):
        width = bar.get_width()
        ax.text(width + 0.3, bar.get_y() + bar.get_height()/2.,
                f'{int(count)}',
                ha='left', va='center', fontsize=11, weight='bold')

    ax.set_yticks(range(len(descriptors)))
    ax.set_yticklabels(descriptors, fontsize=11)
    ax.set_xlabel('Number of Mentions', fontsize=13, weight='bold')
    ax.set_title(f'Top Descriptors Associated with {brand_name}', fontsize=16, weight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.invert_yaxis()  # Highest at top

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return output_path


def generate_all_charts(
    mention_metrics: Dict[str, Any],
    positioning_metrics: Dict[str, Any],
    sentiment_metrics: Dict[str, Any],
    platform_metrics: Dict[str, Dict[str, Any]],
    share_of_voice: Dict[str, Any],
    descriptor_analysis: Dict[str, int],
    brand_name: str,
    timestamp: str = None
) -> Dict[str, str]:
    """
    Generate all charts for the report.
    Returns a dictionary mapping chart names to file paths.
    """
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    charts_dir = ensure_charts_directory()
    brand_slug = brand_name.replace(' ', '_').replace('/', '_')

    chart_paths = {}

    # Generate each chart
    try:
        chart_paths['mention_rate'] = generate_mention_rate_pie_chart(
            mention_metrics, brand_name,
            f"{charts_dir}/{brand_slug}_mention_rate_{timestamp}.png"
        )
    except Exception as e:
        print(f"Warning: Could not generate mention rate chart: {e}")

    try:
        chart_paths['positioning'] = generate_positioning_bar_chart(
            positioning_metrics, brand_name,
            f"{charts_dir}/{brand_slug}_positioning_{timestamp}.png"
        )
    except Exception as e:
        print(f"Warning: Could not generate positioning chart: {e}")

    try:
        chart_paths['sentiment'] = generate_sentiment_pie_chart(
            sentiment_metrics, brand_name,
            f"{charts_dir}/{brand_slug}_sentiment_{timestamp}.png"
        )
    except Exception as e:
        print(f"Warning: Could not generate sentiment chart: {e}")

    try:
        chart_paths['platform_comparison'] = generate_platform_comparison_chart(
            platform_metrics, brand_name,
            f"{charts_dir}/{brand_slug}_platform_comparison_{timestamp}.png"
        )
    except Exception as e:
        print(f"Warning: Could not generate platform comparison chart: {e}")

    try:
        chart_paths['share_of_voice'] = generate_share_of_voice_chart(
            share_of_voice, brand_name,
            f"{charts_dir}/{brand_slug}_share_of_voice_{timestamp}.png"
        )
    except Exception as e:
        print(f"Warning: Could not generate share of voice chart: {e}")

    try:
        chart_paths['descriptor_performance'] = generate_descriptor_performance_chart(
            descriptor_analysis, brand_name,
            f"{charts_dir}/{brand_slug}_descriptor_performance_{timestamp}.png"
        )
    except Exception as e:
        print(f"Warning: Could not generate descriptor performance chart: {e}")

    # Filter out None values (charts that couldn't be generated)
    chart_paths = {k: v for k, v in chart_paths.items() if v is not None}

    print(f"Generated {len(chart_paths)} charts in {charts_dir}/")

    return chart_paths
