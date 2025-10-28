"""
Report Export Service
Provides Word and PDF export functionality with proper table formatting.
"""

import io
import re
from typing import Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import markdown2


def export_to_word(markdown_content: str, title: str) -> io.BytesIO:
    """
    Convert markdown report to Word document with proper formatting.

    Args:
        markdown_content: The markdown content to convert
        title: The report title

    Returns:
        BytesIO object containing the Word document
    """
    doc = Document()

    # Set document margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Parse markdown line by line
    lines = markdown_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # H1 Headers
        if line.startswith('# '):
            text = line[2:].strip()
            heading = doc.add_heading(text, level=1)
            heading.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # H2 Headers
        elif line.startswith('## '):
            text = line[3:].strip()
            heading = doc.add_heading(text, level=2)
            heading.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # H3 Headers
        elif line.startswith('### '):
            text = line[4:].strip()
            heading = doc.add_heading(text, level=3)
            heading.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Horizontal rules
        elif line.startswith('---') or line.startswith('***'):
            doc.add_paragraph('_' * 80)

        # Tables
        elif line.startswith('|'):
            # Collect all table lines
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            i -= 1  # Back up one since we'll increment at the end

            # Parse table
            if len(table_lines) >= 2:  # Header + separator minimum
                # Parse header
                header = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]

                # Skip separator line
                # Parse data rows (skip separator)
                data_rows = []
                for row_line in table_lines[2:]:  # Skip header and separator
                    cells = [cell.strip() for cell in row_line.split('|')[1:-1]]
                    data_rows.append(cells)

                # Create Word table
                if data_rows:
                    table = doc.add_table(rows=1 + len(data_rows), cols=len(header))
                    table.style = 'Light Grid Accent 1'

                    # Add header
                    header_cells = table.rows[0].cells
                    for idx, header_text in enumerate(header):
                        header_cells[idx].text = header_text
                        # Make header bold
                        for paragraph in header_cells[idx].paragraphs:
                            for run in paragraph.runs:
                                run.font.bold = True

                    # Add data rows
                    for row_idx, row_data in enumerate(data_rows, start=1):
                        cells = table.rows[row_idx].cells
                        for col_idx, cell_data in enumerate(row_data):
                            # Remove markdown formatting from cell content
                            clean_text = cell_data.replace('**', '')
                            cells[col_idx].text = clean_text

        # Bullet points
        elif line.startswith('- ') or line.startswith('* '):
            text = line[2:].strip()
            # Remove markdown formatting
            text = text.replace('**', '')
            doc.add_paragraph(text, style='List Bullet')

        # Numbered lists
        elif re.match(r'^\d+\.\s', line):
            text = re.sub(r'^\d+\.\s+', '', line)
            # Remove markdown formatting
            text = text.replace('**', '')
            doc.add_paragraph(text, style='List Number')

        # Regular paragraphs
        else:
            # Remove markdown formatting
            text = line.replace('**', '')
            if text:
                para = doc.add_paragraph(text)
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT

        i += 1

    # Save to BytesIO
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)

    return output


def export_to_pdf(markdown_content: str, title: str) -> io.BytesIO:
    """
    Convert markdown report to PDF document with proper formatting.

    Args:
        markdown_content: The markdown content to convert
        title: The report title

    Returns:
        BytesIO object containing the PDF document
    """
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_LEFT,
    )

    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=12,
    )

    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=10,
        spaceBefore=10,
    )

    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=8,
        spaceBefore=8,
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )

    # Parse markdown
    lines = markdown_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # H1 Headers
        if line.startswith('# '):
            text = line[2:].strip()
            elements.append(Paragraph(text, h1_style))
            elements.append(Spacer(1, 12))

        # H2 Headers
        elif line.startswith('## '):
            text = line[3:].strip()
            elements.append(Paragraph(text, h2_style))
            elements.append(Spacer(1, 10))

        # H3 Headers
        elif line.startswith('### '):
            text = line[4:].strip()
            elements.append(Paragraph(text, h3_style))
            elements.append(Spacer(1, 8))

        # Horizontal rules
        elif line.startswith('---') or line.startswith('***'):
            elements.append(Spacer(1, 12))

        # Tables
        elif line.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            i -= 1

            if len(table_lines) >= 2:
                # Parse header
                header = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]

                # Parse data rows
                data_rows = [[cell.strip().replace('**', '') for cell in row.split('|')[1:-1]]
                            for row in table_lines[2:]]

                if data_rows:
                    # Create table data
                    table_data = [header] + data_rows

                    # Create table
                    t = Table(table_data, repeatRows=1)

                    # Style the table
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
                    ]))

                    elements.append(t)
                    elements.append(Spacer(1, 12))

        # Bullet points or regular text
        else:
            text = line.replace('**', '<b>').replace('**', '</b>')
            text = text.replace('- ', '• ')
            if text:
                elements.append(Paragraph(text, body_style))
                elements.append(Spacer(1, 6))

        i += 1

    # Build PDF
    doc.build(elements)
    output.seek(0)

    return output
