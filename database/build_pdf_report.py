"""
Generates the publication-quality PDF version of the AGNI-NETRA Comprehensive Research Project Report.
Uses ReportLab to build a formatted PDF document with:
- Numbered Canvas for 'Page X of Y' Page Numbers
- Professional Cover Page
- Running Headers and Footers
- Beautifully Styled Tables with Header Shading & Borders
- Callout Finding / Alert Boxes
- Mathematical Formulations & Full 31 Sections + Abstract, Keywords, References, Appendices
"""

import sys
import html
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PDF = ROOT_DIR / "AGNI_NETRA_COMPLETE_RESEARCH_PROJECT_REPORT.pdf"


def clean_xml(text: str) -> str:
    """Safely cleans text for ReportLab Paragraphs by escaping XML entities."""
    if not text:
        return ""
    # Remove markdown bold/code/math markers
    t = text.replace("**", "").replace("`", "").replace("$", "")
    t = html.escape(t)
    return t


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render 'Page X of Y' page numbers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        if self._pageNumber == 1:
            # Suppress header/footer on cover page
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))

        # Running Header
        self.drawString(
            54, 750, "AGNI-NETRA: Geospatial Intelligence & ML Platform for Thermal Risk Assessment"
        )
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 744, 558, 744)

        # Running Footer
        self.line(54, 48, 558, 48)
        self.drawString(54, 36, "AGNI-NETRA Research Project Report — Production Release v1.0 — Controlled Activation")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_text)
        self.restoreState()


def build_pdf():
    print(f"Generating PDF report: {OUTPUT_PDF}...")
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Typography Hierarchy
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#003366'),
        alignment=1, # Center
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#444444'),
        alignment=1,
        spaceAfter=16
    )

    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#333333'),
        alignment=1,
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'ReportH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor('#003366'),
        spaceBefore=14,
        spaceAfter=5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'ReportH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor('#1A5276'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'ReportH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor('#283747'),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#222222'),
        spaceAfter=5
    )

    abstract_style = ParagraphStyle(
        'ReportAbstract',
        parent=styles['BodyText'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#0B3861')
    )

    tbl_hdr_style = ParagraphStyle(
        'TblHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )

    tbl_cell_style = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#222222')
    )

    eq_style = ParagraphStyle(
        'ReportEq',
        parent=styles['Normal'],
        fontName='Courier-Oblique',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#002244'),
        alignment=1, # Center
        spaceBefore=3,
        spaceAfter=5
    )

    story = []

    # COVER PAGE
    story.append(Spacer(1, 15))
    story.append(Paragraph("AGNI-NETRA:<br/>A Geospatial Intelligence and Machine-Learning Platform for Satellite-Based Thermal Event Detection, Contextualization, Risk Assessment, and Human-in-the-Loop Decision Support in India", title_style))
    story.append(Paragraph("From Raw Satellite Thermal Anomaly Ingestion to Multi-Source Contextualization, Calibrated Risk Scoring, and National Command Center Operations", subtitle_style))
    story.append(Paragraph("<b>AGNI-NETRA Project Core Engineering Team</b><br/>Advanced Geospatial & Thermal Intelligence Initiative, India<br/>September 2026 | Production Go-Live Release (Phase 16)", meta_style))
    story.append(Spacer(1, 10))

    # Executive Summary Table on Cover
    cov_rows = [
        [Paragraph("<b>Core Platform Dimension</b>", tbl_hdr_style), Paragraph("<b>Verified Operational State</b>", tbl_hdr_style)],
        [Paragraph("Database Engine", tbl_cell_style), Paragraph("PostgreSQL 16.1 + PostGIS 3.4.2 (EPSG:4326)", tbl_cell_style)],
        [Paragraph("Authoritative Thermal Records", tbl_cell_style), Paragraph("8,221,825+ Observations (2022–2026 Archive)", tbl_cell_style)],
        [Paragraph("Historical Partition Status", tbl_cell_style), Paragraph("100% Sealed & Immutable (6,448,666 rows, 0 diff)", tbl_cell_style)],
        [Paragraph("Geospatial Knowledge Base", tbl_cell_style), Paragraph("35,684 Facilities | 1,633 CEA Plants | 98,793 Mines", tbl_cell_style)],
        [Paragraph("Champion Model", tbl_cell_style), Paragraph("xgb-v3.0-real-candidate + Balanced Platt Calibrator", tbl_cell_style)],
        [Paragraph("Spatial Validation Accuracy", tbl_cell_style), Paragraph("94.32% Mean Accuracy (Macro F1: 0.9318)", tbl_cell_style)],
        [Paragraph("Probability Calibration", tbl_cell_style), Paragraph("Log-Loss: 0.7124 (55.7% drop) | ECE: 0.1294 (54.3% drop)", tbl_cell_style)],
        [Paragraph("Tri-Tier Decision Safety", tbl_cell_style), Paragraph("Tier 1 Selective Accuracy: 97.18%", tbl_cell_style)],
        [Paragraph("Operational Dispatch Gate", tbl_cell_style), Paragraph("ENABLE_OPERATIONAL_DISPATCH_GATE = False (Secured)", tbl_cell_style)],
        [Paragraph("Platform Operational Status", tbl_cell_style), Paragraph("<b>HEALTHY / PRODUCTION-READY (CONTROLLED ACTIVATION)</b>", tbl_cell_style)],
    ]
    t_cov = Table(cov_rows, colWidths=[2.2 * inch, 4.3 * inch])
    t_cov.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D0D3D4')),
    ]))
    story.append(t_cov)
    story.append(PageBreak())

    # Read Markdown Document
    md_text = (ROOT_DIR / "AGNI_NETRA_COMPLETE_RESEARCH_PROJECT_REPORT.md").read_text(encoding="utf-8")
    lines = md_text.splitlines()

    in_abstract = False
    in_table = False
    table_headers = []
    table_rows = []

    for line in lines:
        sline = line.strip()

        if sline.startswith("# AGNI-NETRA:"):
            continue
        if sline.startswith("**Subtitle**:") or sline.startswith("**Authors") or sline.startswith("**Date") or sline.startswith("**Document") or sline.startswith("**Repository") or sline.startswith("**Software"):
            continue
        if sline == "---":
            continue

        # Headings
        if sline.startswith("## Abstract"):
            in_abstract = True
            story.append(Paragraph("Abstract", h1_style))
            continue
        elif sline.startswith("## Keywords"):
            in_abstract = False
            story.append(Paragraph("Keywords", h1_style))
            continue
        elif sline.startswith("## ") and not sline.startswith("### "):
            title = clean_xml(sline.replace("## ", "").strip())
            story.append(Paragraph(title, h1_style))
            continue
        elif sline.startswith("### "):
            title = clean_xml(sline.replace("### ", "").strip())
            story.append(Paragraph(title, h2_style))
            continue
        elif sline.startswith("#### "):
            title = clean_xml(sline.replace("#### ", "").strip())
            story.append(Paragraph(title, h3_style))
            continue

        # Callouts / Key Results
        if sline.startswith("> **Key Result**:") or sline.startswith("> **Scientific Finding**:") or sline.startswith("> **Safety Significance**:") or sline.startswith("> [!NOTE]"):
            callout_prefix = "KEY FINDING"
            if "Scientific" in sline:
                callout_prefix = "SCIENTIFIC FINDING"
            elif "Safety" in sline:
                callout_prefix = "SAFETY SIGNIFICANCE"
            elif "NOTE" in sline:
                callout_prefix = "NOTE"

            raw_c = sline.replace("> **Key Result**:", "").replace("> **Scientific Finding**:", "").replace("> **Safety Significance**:", "").replace("> [!NOTE]", "").replace(">", "").strip()
            clean_c = f"<b>{callout_prefix}:</b> " + clean_xml(raw_c)
            t_box = Table([[Paragraph(clean_c, callout_style)]], colWidths=[6.5 * inch])
            t_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EBF3FA')),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LINELEFT', (0, 0), (0, -1), 3.5, colors.HexColor('#003366')),
            ]))
            story.append(Spacer(1, 3))
            story.append(t_box)
            story.append(Spacer(1, 5))
            continue

        # Tables
        if sline.startswith("|") and sline.endswith("|"):
            cells = [c.strip() for c in sline.split("|")[1:-1]]
            if not cells:
                continue
            if all(set(c).issubset({'-', ':', ' '}) for c in cells):
                in_table = True
                continue
            if not in_table:
                table_headers = [clean_xml(c) for c in cells]
                table_rows = []
            else:
                table_rows.append([clean_xml(c) for c in cells])
            continue
        elif in_table and not sline.startswith("|"):
            in_table = False
            if table_headers and table_rows:
                num_cols = len(table_headers)
                t_data = []
                t_data.append([Paragraph(f"<b>{h}</b>", tbl_hdr_style) for h in table_headers])
                for r in table_rows:
                    t_data.append([Paragraph(c, tbl_cell_style) for c in r])

                # Width distribution
                total_w = 6.5
                col_w = [total_w / num_cols * inch] * num_cols
                if num_cols == 2:
                    col_w = [2.2 * inch, 4.3 * inch]
                elif num_cols == 3:
                    col_w = [2.0 * inch, 2.25 * inch, 2.25 * inch]
                elif num_cols == 4:
                    col_w = [1.6 * inch, 1.6 * inch, 1.6 * inch, 1.7 * inch]
                elif num_cols == 5:
                    col_w = [1.3 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch]
                elif num_cols == 6:
                    col_w = [1.2 * inch, 1.05 * inch, 1.05 * inch, 1.05 * inch, 1.05 * inch, 1.1 * inch]

                t_elem = Table(t_data, colWidths=col_w)
                t_elem.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5D8DC')),
                ]))
                story.append(Spacer(1, 4))
                story.append(t_elem)
                story.append(Spacer(1, 5))
                table_headers = []
                table_rows = []

        # Equations & Code Blocks
        if sline.startswith("```") or sline.endswith("```"):
            continue
        if sline.startswith("$$") and sline.endswith("$$"):
            clean_eq = clean_xml(sline.replace("$$", "").strip())
            story.append(Paragraph(clean_eq, eq_style))
            continue

        # Body Paragraph
        if sline:
            clean_line = clean_xml(sline)
            if in_abstract:
                story.append(Paragraph(clean_line, abstract_style))
            else:
                story.append(Paragraph(clean_line, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF report: {OUTPUT_PDF}")


if __name__ == "__main__":
    build_pdf()
