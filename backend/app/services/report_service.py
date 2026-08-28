import os
import io
from datetime import datetime, timezone
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_event_pdf_report(
    event_data: Dict[str, Any],
    prediction_data: Dict[str, Any] = None,
    risk_data: Dict[str, Any] = None,
    facility_data: Dict[str, Any] = None,
    output_filepath: str = None
) -> bytes:
    """
    Generates a professional AGNI-NETRA PDF Intelligence Dossier.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer if not output_filepath else output_filepath,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    header_title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0b1329'),
        alignment=TA_LEFT
    )
    subtitle_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#d97706'),
        alignment=TA_LEFT
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748b')
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("AGNI-NETRA", header_title_style))
    story.append(Paragraph("AI Geospatial Network for Industrial Thermal Risk & Anomaly Analysis", subtitle_style))
    story.append(Paragraph(f"INTELLIGENCE DOSSIER • Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} • DECISION SUPPORT SYSTEM", meta_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#d97706'), spaceAfter=12))

    # 2. Executive Event Summary Box
    event_code = event_data.get("event_code", "EVT-UNKNOWN")
    state = event_data.get("state", "N/A")
    lat = event_data.get("latitude", 0.0)
    lon = event_data.get("longitude", 0.0)
    status = event_data.get("status", "ACTIVE")
    
    pred_class = prediction_data.get("predicted_class", "Uncertain") if prediction_data else "Uncertain"
    confidence = prediction_data.get("confidence", 0.0) if prediction_data else 0.0
    risk_level = risk_data.get("risk_level", "LOW") if risk_data else "LOW"
    risk_score = risk_data.get("risk_score", 0.0) if risk_data else 0.0

    # Risk badge color
    risk_color_map = {
        "CRITICAL": colors.HexColor('#ef4444'),
        "HIGH": colors.HexColor('#f97316'),
        "MODERATE": colors.HexColor('#eab308'),
        "LOW": colors.HexColor('#10b981')
    }
    badge_color = risk_color_map.get(risk_level, colors.HexColor('#64748b'))

    summary_table_data = [
        [
            Paragraph(f"<b>Event Code:</b> {event_code}", body_style),
            Paragraph(f"<b>Classification:</b> {pred_class} ({confidence*100:.1f}%)", body_style),
        ],
        [
            Paragraph(f"<b>Location:</b> {lat:.5f}°N, {lon:.5f}°E ({state})", body_style),
            Paragraph(f"<b>AGNI-NETRA Risk Level:</b> <b>{risk_level}</b> ({risk_score}/100)", body_style),
        ],
        [
            Paragraph(f"<b>Active Detections:</b> {event_data.get('detection_count', 1)} observations", body_style),
            Paragraph(f"<b>Peak Radiative Power (FRP):</b> {event_data.get('max_frp', 0.0):.1f} MW", body_style),
        ],
        [
            Paragraph(f"<b>First Detected:</b> {str(event_data.get('first_seen'))[:19]}", body_style),
            Paragraph(f"<b>Last Detected:</b> {str(event_data.get('last_seen'))[:19]}", body_style),
        ]
    ]

    t_summary = Table(summary_table_data, colWidths=[270, 270])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 14))

    # 3. Explainable AI & SHAP Feature Contribution
    story.append(Paragraph("1. Explainable AI (SHAP) Attribution", section_title_style))
    shap_explanation = prediction_data.get("explanation_summary", "Model attribution calculated via TreeExplainer.") if prediction_data else "No SHAP details."
    story.append(Paragraph(shap_explanation, body_style))
    story.append(Spacer(1, 6))

    top_contributors = []
    if prediction_data and "shap_values" in prediction_data:
        top_contributors = prediction_data["shap_values"].get("top_contributors", [])
    
    if top_contributors:
        shap_table_data = [["Feature Name", "Value", "Shapley Impact", "Direction"]]
        for item in top_contributors[:5]:
            impact_val = item.get("shap_value", 0.0)
            direction = "Supports Class (+)" if impact_val >= 0 else "Opposes Class (-)"
            shap_table_data.append([
                item.get("feature", "Unknown"),
                str(item.get("value", "")),
                f"{impact_val:+.3f}",
                direction
            ])
        t_shap = Table(shap_table_data, colWidths=[160, 110, 110, 160])
        t_shap.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0b1329')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_shap)
    story.append(Spacer(1, 14))

    # 4. Facility Context & Candidate Evidence
    story.append(Paragraph("2. Geospatial Facility Association", section_title_style))
    fac_name = facility_data.get("name", "None (Uncataloged Site)") if facility_data else "None (Uncataloged Site)"
    fac_type = facility_data.get("facility_type", "N/A") if facility_data else "N/A"
    fac_dist = event_data.get("nearest_facility_distance_m", 9999) or 9999
    
    fac_info = [
        [Paragraph(f"<b>Associated Facility:</b> {fac_name}", body_style), Paragraph(f"<b>Facility Type:</b> {fac_type}", body_style)],
        [Paragraph(f"<b>Facility Status:</b> {event_data.get('facility_status', 'UNKNOWN')}", body_style), Paragraph(f"<b>Distance to Boundary:</b> {fac_dist:.1f} m", body_style)],
        [Paragraph(f"<b>Land Cover Context:</b> {event_data.get('landcover_class', 'Unknown')}", body_style), Paragraph(f"<b>Source Provenance:</b> OSM / Satellite Survey", body_style)]
    ]
    t_fac = Table(fac_info, colWidths=[270, 270])
    t_fac.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_fac)
    story.append(Spacer(1, 14))

    # 5. Risk Assessment Breakdown
    story.append(Paragraph("3. Risk Evaluation & Drivers", section_title_style))
    risk_reasons = risk_data.get("risk_reasons", []) if risk_data else ["Standard thermal evaluation."]
    for reason in risk_reasons:
        story.append(Paragraph(f"• {reason}", body_style))
    story.append(Spacer(1, 14))

    # 6. Disclaimer & Verification Notice
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=8))
    disclaimer = (
        "<b>LEGAL & SCIENTIFIC DISCLAIMER:</b> This document contains automated analytical intelligence derived from "
        "satellite remote sensing observations and machine learning models. Predictions reflect statistical probabilities "
        "and do not constitute certified ground truth until verified by authorized domain personnel."
    )
    story.append(Paragraph(disclaimer, meta_style))

    doc.build(story)
    
    if output_filepath:
        return b""
    else:
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
