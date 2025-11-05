"""
PowerPoint Slideshow Export Service
Generates PowerPoint presentations with embedded PNG charts
"""

import os
import io
import re
from typing import Optional
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from sqlalchemy.orm import Session


def generate_slideshow(
    markdown_content: str,
    title: str,
    db: Session,
    user_id: int,
    brand_id: Optional[int] = None
) -> io.BytesIO:
    """
    Generate a PowerPoint slideshow with embedded charts.

    Args:
        markdown_content: The markdown report content
        title: Report title
        db: Database session
        user_id: User ID
        brand_id: Brand ID

    Returns:
        BytesIO object containing the PowerPoint file
    """
    from app import models

    # Create presentation
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Get brand name
    brand_name = "Your Brand"
    if brand_id:
        brand = db.query(models.BrandInfo).filter(models.BrandInfo.id == brand_id).first()
        if brand:
            brand_name = brand.brand_name

    # TALES brand colors
    TALES_PURPLE = RGBColor(102, 87, 117)  # #665775
    TALES_BLUE = RGBColor(128, 161, 212)   # #80a1d4
    TALES_TEAL = RGBColor(117, 201, 200)   # #75c9c8

    # === Slide 1: Title Slide ===
    title_slide_layout = prs.slide_layouts[6]  # Blank layout
    slide = prs.slides.add_slide(title_slide_layout)

    # Add purple background
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = TALES_PURPLE

    # Add title
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(9), Inches(2)
    )
    title_frame = title_box.text_frame
    title_frame.text = title
    title_para = title_frame.paragraphs[0]
    title_para.font.size = Pt(44)
    title_para.font.bold = True
    title_para.font.color.rgb = RGBColor(255, 255, 255)
    title_para.alignment = PP_ALIGN.CENTER

    # Add subtitle
    subtitle_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(4.5), Inches(9), Inches(1)
    )
    subtitle_frame = subtitle_box.text_frame
    subtitle_frame.text = f"AI Reputation Analysis for {brand_name}"
    subtitle_para = subtitle_frame.paragraphs[0]
    subtitle_para.font.size = Pt(24)
    subtitle_para.font.color.rgb = RGBColor(255, 255, 255)
    subtitle_para.alignment = PP_ALIGN.CENTER

    # === Extract Executive Summary ===
    exec_summary_match = re.search(r'## Executive Summary\n\n(.*?)(?=\n\n!|\n\n##|\Z)', markdown_content, re.DOTALL)
    if exec_summary_match:
        exec_summary = exec_summary_match.group(1).strip()

        # Create Executive Summary slide
        blank_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_layout)

        # Add title
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(0.8))
        title_frame = title_box.text_frame
        title_frame.text = "Executive Summary"
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(32)
        title_para.font.bold = True
        title_para.font.color.rgb = TALES_PURPLE

        # Add summary text
        text_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9), Inches(5.5))
        text_frame = text_box.text_frame
        text_frame.word_wrap = True

        # Remove markdown formatting
        clean_summary = re.sub(r'\*\*(.*?)\*\*', r'\1', exec_summary)
        text_frame.text = clean_summary

        for paragraph in text_frame.paragraphs:
            paragraph.font.size = Pt(14)
            paragraph.font.color.rgb = RGBColor(51, 51, 51)
            paragraph.space_before = Pt(6)
            paragraph.space_after = Pt(6)

    # === Extract and add chart images ===
    images = re.findall(r'!\[(.*?)\]\((.*?)\)', markdown_content)

    chart_titles = {
        'mention_rate': 'Brand Mention Rate',
        'share_of_voice': 'Share of Voice',
        'positioning': 'Brand Positioning',
        'sentiment': 'Sentiment Distribution',
        'descriptor_performance': 'Top Descriptors',
        'platform_comparison': 'Platform Performance',
        'competitor_threats': 'Competitive Threats',
        'brand_mentions_trend': 'Mention Rate Trend',
        'positioning_trend': 'Positioning Trend',
        'sentiment_trend': 'Sentiment Trend',
        'share_of_voice_trend': 'Share of Voice Trend'
    }

    for alt_text, image_path in images:
        # Convert web path to filesystem path
        if image_path.startswith('report_charts/'):
            full_path = os.path.join('frontend', 'public', image_path)
        elif os.path.exists(image_path):
            full_path = image_path
        else:
            continue

        if not os.path.exists(full_path):
            print(f"Warning: Chart not found at {full_path}")
            continue

        # Determine chart title
        chart_title = alt_text
        for key, title in chart_titles.items():
            if key in image_path.lower():
                chart_title = title
                break

        # Create slide for this chart
        blank_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_layout)

        # Add title
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.7))
        title_frame = title_box.text_frame
        title_frame.text = chart_title
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(32)
        title_para.font.bold = True
        title_para.font.color.rgb = TALES_PURPLE

        # Add chart image (centered, large)
        try:
            left = Inches(1)
            top = Inches(1.2)
            width = Inches(8)
            slide.shapes.add_picture(full_path, left, top, width=width)
        except Exception as e:
            print(f"Error adding image {full_path}: {e}")

    # === Final Slide: Thank You ===
    final_slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(final_slide_layout)

    # Add teal background
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = TALES_TEAL

    # Add thank you text
    thank_you_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(3), Inches(9), Inches(2)
    )
    thank_you_frame = thank_you_box.text_frame
    thank_you_frame.text = "Questions?"
    thank_you_para = thank_you_frame.paragraphs[0]
    thank_you_para.font.size = Pt(48)
    thank_you_para.font.bold = True
    thank_you_para.font.color.rgb = RGBColor(255, 255, 255)
    thank_you_para.alignment = PP_ALIGN.CENTER

    # Save to BytesIO
    output = io.BytesIO()
    prs.save(output)
    output.seek(0)

    return output
