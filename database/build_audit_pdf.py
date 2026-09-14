import os
import sys
import html
import re
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
INPUT_MD = ROOT_DIR / "FINAL_PROJECT_AUDIT_REPORT.md"
OUTPUT_PDF = ROOT_DIR / "FINAL_PROJECT_AUDIT_REPORT.pdf"


def clean_xml(text: str) -> str:
    """Safely cleans text for ReportLab Paragraphs by escaping XML entities and handling basic markdown."""
    if not text:
        return ""
    
    # Pre-process markdown tags
    # Replace math $...$ with plain text
    t = re.sub(r'\$([^\$]+)\$', r'\1', text)
    
    # Convert markdown bold **word** to temporary tokens
    t = re.sub(r'\*\*(.+?)\*\*', r'{{B_START}}\1{{B_END}}', t)
    # Convert markdown italic *word* to temporary tokens
    t = re.sub(r'\*([^\*]+?)\*', r'{{I_START}}\1{{I_END}}', t)
    # Convert markdown code `word` to temporary tokens
    t = re.sub(r'`([^`]+?)`', r'{{C_START}}\1{{C_END}}', t)
    
    # Escape HTML special chars
    t = html.escape(t)
    
    # Restore tags
    t = t.replace('{{B_START}}', '<b>').replace('{{B_END}}', '</b>')
    t = t.replace('{{I_START}}', '<i>').replace('{{I_END}}', '</i>')
    t = t.replace('{{C_START}}', '<font face="Courier"><b>').replace('{{C_END}}', '</b></font>')
    
    # Remove unsupported HTML breaks or tags if any
    t = t.replace('&lt;br/&gt;', '<br/>').replace('&lt;br&gt;', '<br/>').replace('&lt;br /&gt;', '<br/>')
    
    return t


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render 'Page X of Y' page numbers and headers."""
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
            # Suppress running header/footer on cover page
            return

        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#555555"))

        # Running Header
        self.drawString(
            45, 752, "AGNI-NETRA — Sovereign Space-Borne Thermal Intelligence & Mission Platform (Phase 24 Final Release)"
        )
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(45, 746, 567, 746)

        # Running Footer
        self.line(45, 42, 567, 42)
        self.drawString(45, 30, "CONFIDENTIAL & PROPRIETARY — FINAL AUDIT & ACCEPTANCE VERIFICATION REPORT")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(567, 30, page_text)
        self.restoreState()


def build_pdf():
    print(f"Reading markdown source from: {INPUT_MD}")
    md_text = INPUT_MD.read_text(encoding="utf-8")
    
    print(f"Generating publication-grade PDF: {OUTPUT_PDF}...")
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Custom Typography Palette
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#002B49'),
        alignment=1, # Center
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4A607A'),
        alignment=1,
        spaceAfter=12
    )

    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#333333'),
        alignment=1,
        spaceAfter=16
    )

    h1_style = ParagraphStyle(
        'AuditH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#002B49'),
        spaceBefore=14,
        spaceAfter=5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'AuditH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#134B70'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'AuditH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#201E43'),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'AuditBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#222222'),
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'AuditBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#222222'),
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor('#002B49')
    )

    tbl_hdr_style = ParagraphStyle(
        'TblHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=colors.white
    )

    tbl_cell_style = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.5,
        leading=8.5,
        textColor=colors.HexColor('#1A1A1A')
    )

    eq_style = ParagraphStyle(
        'AuditEq',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#002B49'),
        alignment=1, # Center
        spaceBefore=4,
        spaceAfter=5
    )

    code_block_style = ParagraphStyle(
        'CodeBlock',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=6.5,
        leading=8.5,
        textColor=colors.HexColor('#1A3636'),
        spaceBefore=2,
        spaceAfter=4
    )

    story = []

    # 1. COVER PAGE
    story.append(Spacer(1, 20))
    story.append(Paragraph("AGNI-NETRA (अग्नि-नेत्र)", title_style))
    story.append(Paragraph("Sovereign Space-Borne Thermal Intelligence, Industrial Anomaly Detection & Mission Platform", subtitle_style))
    story.append(Paragraph("<b>Final System Audit, Technical Verification & Acceptance Report</b><br/>Autonomous Dual-Path Pipeline • Calibrated Machine Learning • JARVIS Mission Orchestrator<br/><b>Phase 24 Final Sovereign Release Freeze | September 2026</b>", meta_style))
    story.append(Spacer(1, 10))

    # Executive Cover Table
    cov_rows = [
        [Paragraph("<b>Evaluation Dimension</b>", tbl_hdr_style), Paragraph("<b>Verified System Reality & Evidence</b>", tbl_hdr_style)],
        [Paragraph("Operational Architecture", tbl_cell_style), Paragraph("Dual-Path Decoupled: Path A (Autonomous Ingestion) + Path B (JARVIS Orchestrator)", tbl_cell_style)],
        [Paragraph("Operating Scope", tbl_cell_style), Paragraph("Sovereign Territory of India (Lat 6.0°N–38.0°N, Lon 68.0°E–98.0°E; Survey of India / LGD)", tbl_cell_style)],
        [Paragraph("Data Storage & Schemas", tbl_cell_style), Paragraph("48 Relational Tables (PostgreSQL 16 / PostGIS 3.4 & SQLite 3 Geodetic Engine)", tbl_cell_style)],
        [Paragraph("Governed Datasets Registered", tbl_cell_style), Paragraph("18 Datasets (FIRMS, OSM 35.6k, CEA 1,633, IBM 414, FSI Forests, Bhuvan LULC, PARIVESH)", tbl_cell_style)],
        [Paragraph("Machine Learning Engine", tbl_cell_style), Paragraph("Calibrated XGBoost (v3.2 Real Telemetry, N=1,674) + Balanced Platt Scaling + SHAP Waterfall", tbl_cell_style)],
        [Paragraph("Calibration & Uncertainty", tbl_cell_style), Paragraph("Expected Calibration Error (ECE): 0.1045 | Tier 1 Selective Accuracy: 94.87%", tbl_cell_style)],
        [Paragraph("Epistemic Framework", tbl_cell_style), Paragraph("5-Way Separation: KNOWN (Sensor) | INFERRED (Model) | UNCERTAIN | MISSING | CONFLICTING", tbl_cell_style)],
        [Paragraph("JARVIS Mission Orchestration", tbl_cell_style), Paragraph("Single Master Agent, 32 Controlled Tools, Richards Heuer ACH, Dynamic Conditions A–E", tbl_cell_style)],
        [Paragraph("Voice & Situational Awareness", tbl_cell_style), Paragraph("Web Audio STT/TTS (< 1.4s Latency) with Graceful Fallback & In-Memory World-State Cache", tbl_cell_style)],
        [Paragraph("Safety & Governance Gates", tbl_cell_style), Paragraph("ENABLE_OPERATIONAL_DISPATCH_GATE = False (HARD-LOCKED) | Model Weights Frozen", tbl_cell_style)],
        [Paragraph("Automated Test Suite Execution", tbl_cell_style), Paragraph("144 / 144 Pytest Tests Passed (100% Clean) | 8,576 Joblib Warnings Audited & Resolved", tbl_cell_style)],
        [Paragraph("Frontend & UI Build Quality", tbl_cell_style), Paragraph("Next.js Production Build Passed (30 Routes Compiled) | 0 TypeScript Errors", tbl_cell_style)],
        [Paragraph("Interactive E2E Demonstration", tbl_cell_style), Paragraph("Browser Subagent Executed 15-Step Live Flow with Recorded Session WebP Artifact", tbl_cell_style)],
        [Paragraph("Official System Verdict", tbl_cell_style), Paragraph("<b>VERIFIED — JARVIS AUTONOMOUS INTELLIGENCE READY (PHASE 24 ACCEPTED)</b>", tbl_cell_style)],
    ]
    t_cov = Table(cov_rows, colWidths=[2.2 * inch, 5.0 * inch])
    t_cov.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002B49')),
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

    # 2. PARSE MARKDOWN DOCUMENT
    lines = md_text.splitlines()

    in_table = False
    table_headers = []
    table_rows = []
    in_code_block = False
    code_lines = []

    for line in lines:
        sline = line.strip()

        # Skip main title (already rendered on cover)
        if sline.startswith("# AGNI-NETRA:"):
            continue
        if sline == "---":
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CCCCCC'), spaceBefore=2, spaceAfter=4))
            continue

        # Code block handling
        if sline.startswith("```"):
            if in_code_block:
                in_code_block = False
                if code_lines:
                    block_text = "<br/>".join([clean_xml(cl) for cl in code_lines])
                    t_code = Table([[Paragraph(block_text, code_block_style)]], colWidths=[7.2 * inch])
                    t_code.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F6F7')),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
                    ]))
                    story.append(Spacer(1, 3))
                    story.append(t_code)
                    story.append(Spacer(1, 4))
                code_lines = []
            else:
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # Headings
        if sline.startswith("## ") and not sline.startswith("### "):
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

        # Callouts / Alerts (> ...)
        if sline.startswith(">"):
            raw_c = sline.replace(">", "").strip()
            # Clean alert headers
            raw_c = raw_c.replace("[!IMPORTANT]", "<b>IMPORTANT NOTICE:</b>")
            raw_c = raw_c.replace("[!NOTE]", "<b>NOTE:</b>")
            raw_c = raw_c.replace("[!WARNING]", "<b>WARNING:</b>")
            clean_c = clean_xml(raw_c)
            t_box = Table([[Paragraph(clean_c, callout_style)]], colWidths=[7.2 * inch])
            t_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EBF3FA')),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINELEFT', (0, 0), (0, -1), 3.0, colors.HexColor('#002B49')),
            ]))
            story.append(Spacer(1, 2))
            story.append(t_box)
            story.append(Spacer(1, 4))
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

                # Col widths calculation
                total_w = 7.2
                if num_cols == 2:
                    col_w = [2.2 * inch, 5.0 * inch]
                elif num_cols == 3:
                    col_w = [2.2 * inch, 2.5 * inch, 2.5 * inch]
                elif num_cols == 4:
                    col_w = [1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch]
                elif num_cols == 5:
                    col_w = [1.44 * inch] * 5
                elif num_cols == 6:
                    col_w = [1.5 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 1.2 * inch, 1.2 * inch]
                elif num_cols == 7:
                    col_w = [0.5 * inch, 1.4 * inch, 0.9 * inch, 1.0 * inch, 1.3 * inch, 1.1 * inch, 1.0 * inch]
                else:
                    col_w = [total_w / num_cols * inch] * num_cols

                t_elem = Table(t_data, colWidths=col_w)
                t_elem.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002B49')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 2.5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5D8DC')),
                ]))
                story.append(Spacer(1, 3))
                story.append(t_elem)
                story.append(Spacer(1, 4))
                table_headers = []
                table_rows = []

        # Mathematical Equations ($$ ... $$)
        if sline.startswith("$$") and sline.endswith("$$"):
            clean_eq = clean_xml(sline.replace("$$", "").strip())
            story.append(Paragraph(f"<b>[FORMULA]</b>: {clean_eq}", eq_style))
            continue

        # Bullet items
        if sline.startswith("* ") or sline.startswith("- "):
            clean_b = clean_xml(sline[2:].strip())
            story.append(Paragraph(f"• &nbsp; {clean_b}", bullet_style))
            continue

        # Numbered items (e.g. 1. , 2. )
        m_num = re.match(r'^(\d+)\.\s+(.*)$', sline)
        if m_num:
            num = m_num.group(1)
            rest = clean_xml(m_num.group(2))
            story.append(Paragraph(f"<b>{num}.</b> &nbsp; {rest}", bullet_style))
            continue

        # Regular Body Paragraph
        if sline:
            clean_line = clean_xml(sline)
            story.append(Paragraph(clean_line, body_style))

    print(f"Building PDF document with {len(story)} flowable elements...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated updated PDF report: {OUTPUT_PDF}!")


if __name__ == "__main__":
    build_pdf()
