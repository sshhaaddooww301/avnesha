"""
PDF Report Generation for QDS SIEM.

Generates professional security assessment reports with:
- Threat detection statistics
- Quantum measurement analysis
- Forgery probability calculations
- Confusion matrix (from Test Lab)
- Audit ledger integrity verification

All data sourced dynamically from PostgreSQL - zero hardcoded values.
"""

import io
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.database import get_db
from app.models import SecurityEvent, Threat, AuditLedger, TestRun, TestResult
from app.blockchain.ledger import audit_ledger
from app.engine.statistics import (
    mean, std_deviation, variance, measurement_deviation
)

router = APIRouter(prefix="/api/reports", tags=["Reports"])


# ------------------------------------------------------------------
# Color Palette (matching dashboard obsidian theme)
# ------------------------------------------------------------------
COLOR_BG = colors.HexColor("#0a0a0e")
COLOR_HEADER = colors.HexColor("#18181b")
COLOR_ACCENT = colors.HexColor("#a1a1aa")
COLOR_WHITE = colors.white
COLOR_RED = colors.HexColor("#f87171")
COLOR_GREEN = colors.HexColor("#34d399")
COLOR_AMBER = colors.HexColor("#fbbf24")
COLOR_TABLE_BG = colors.HexColor("#27272a")
COLOR_TABLE_HEADER = colors.HexColor("#3f3f46")
COLOR_BORDER = colors.HexColor("#52525b")


def _build_styles():
    """Create custom paragraph styles for the PDF report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        textColor=COLOR_WHITE,
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=COLOR_ACCENT,
        alignment=TA_CENTER,
        spaceAfter=8 * mm,
    ))
    styles.add(ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=COLOR_GREEN,
        spaceBefore=8 * mm,
        spaceAfter=3 * mm,
        borderPadding=2,
    ))
    styles.add(ParagraphStyle(
        "SubSectionHeader",
        parent=styles["Heading3"],
        fontSize=11,
        leading=14,
        textColor=COLOR_AMBER,
        spaceBefore=5 * mm,
        spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        "BodyText2",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=COLOR_ACCENT,
        spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        "Formula",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=COLOR_WHITE,
        alignment=TA_CENTER,
        fontName="Courier",
        spaceBefore=3 * mm,
        spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        "MetricValue",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        textColor=COLOR_WHITE,
        fontName="Courier-Bold",
    ))
    styles.add(ParagraphStyle(
        "FooterStyle",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        textColor=COLOR_ACCENT,
        alignment=TA_CENTER,
    ))
    return styles


def _make_table(data, col_widths=None, header_row=True):
    """Build a styled table matching the obsidian theme."""
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_TABLE_BG),
        ("TEXTCOLOR", (0, 0), (-1, -1), COLOR_WHITE),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, -1), "Courier"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    if header_row:
        style_commands += [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_GREEN),
            ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
        ]

    # Alternate row striping
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_commands.append(
                ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#1f1f23"))
            )

    t = Table(data, colWidths=col_widths, repeatRows=1 if header_row else 0)
    t.setStyle(TableStyle(style_commands))
    return t


def _add_page_bg(canvas, doc):
    """Draw dark background and footer on each page."""
    canvas.saveState()
    canvas.setFillColor(COLOR_BG)
    canvas.rect(0, 0, A4[0], A4[1], fill=1)
    # Footer
    canvas.setFont("Courier", 7)
    canvas.setFillColor(COLOR_ACCENT)
    canvas.drawCentredString(
        A4[0] / 2, 10 * mm,
        f"QDS SIEM  •  Quantum-Inspired Cyber Threat Detection  •  Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  •  Page {doc.page}"
    )
    canvas.restoreState()


@router.get("/pdf")
async def generate_pdf_report(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a comprehensive PDF Security Assessment Report.
    All data is sourced dynamically from PostgreSQL.
    """
    styles = _build_styles()
    start_time = datetime.utcnow() - timedelta(days=days)

    # ------------------------------------------------------------------
    # 1. Collect data from DB
    # ------------------------------------------------------------------

    # Total events + verification stats
    ev_result = await db.execute(
        select(
            func.count(SecurityEvent.id),
            func.count(SecurityEvent.id).filter(SecurityEvent.verification_result == True),
            func.count(SecurityEvent.id).filter(SecurityEvent.verification_result == False),
        ).where(SecurityEvent.timestamp >= start_time)
    )
    ev_row = ev_result.one()
    total_events = ev_row[0] or 0
    ver_success = ev_row[1] or 0
    ver_failure = ev_row[2] or 0
    total_verified = ver_success + ver_failure
    success_rate = round(ver_success / total_verified * 100, 2) if total_verified > 0 else 0

    # Threats
    th_count = await db.execute(
        select(func.count(Threat.id)).where(Threat.detected_at >= start_time)
    )
    total_threats = th_count.scalar() or 0

    # Severity distribution
    sev_result = await db.execute(
        select(Threat.severity, func.count(Threat.id))
        .where(Threat.detected_at >= start_time)
        .group_by(Threat.severity)
    )
    sev_rows = sev_result.all()

    # Threat type distribution
    type_result = await db.execute(
        select(Threat.threat_type, func.count(Threat.id))
        .where(Threat.detected_at >= start_time)
        .group_by(Threat.threat_type)
        .order_by(func.count(Threat.id).desc())
    )
    type_rows = type_result.all()

    # Quantum measurement statistics
    dev_result = await db.execute(
        select(SecurityEvent.observed_measurement, SecurityEvent.expected_measurement)
        .where(
            and_(
                SecurityEvent.timestamp >= start_time,
                SecurityEvent.observed_measurement != None,
                SecurityEvent.expected_measurement != None,
            )
        )
    )
    dev_records = dev_result.all()
    deviations = [
        measurement_deviation(r[0], r[1])
        for r in dev_records
        if r[0] is not None and r[1] is not None
    ]

    # Ledger status
    ledger_status = await audit_ledger.get_status(db)

    # Latest test run metrics (for confusion matrix / forgery probability)
    test_run_result = await db.execute(
        select(TestRun)
        .where(TestRun.status == "completed")
        .order_by(TestRun.created_at.desc())
        .limit(1)
    )
    latest_test = test_run_result.scalar_one_or_none()

    test_metrics = None
    if latest_test and latest_test.metrics:
        test_metrics = latest_test.metrics

    # ------------------------------------------------------------------
    # 2. Build PDF document
    # ------------------------------------------------------------------
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    story = []

    # ---- Title Page ----
    story.append(Spacer(1, 30 * mm))
    story.append(Paragraph(
        "QUANTUM-INSPIRED CYBER THREAT<br/>DETECTION ASSESSMENT REPORT",
        styles["ReportTitle"]
    ))
    story.append(Paragraph(
        "Teleportation-Based Quantum Digital Signature (QDS) Security Framework",
        styles["ReportSubtitle"]
    ))
    story.append(Spacer(1, 5 * mm))
    story.append(HRFlowable(width="80%", thickness=0.5, color=COLOR_BORDER, spaceAfter=5 * mm))
    story.append(Paragraph(
        f"Report Period: Last {days} Days  •  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        styles["ReportSubtitle"]
    ))
    story.append(Paragraph(
        "Framework: No AI/ML — Deterministic Rules, Statistical Thresholds, Quantum Measurement Analysis",
        styles["ReportSubtitle"]
    ))
    story.append(Spacer(1, 5 * mm))

    # Key metrics summary box
    summary_data = [
        ["METRIC", "VALUE"],
        ["Total QDS Events Ingested", str(total_events)],
        ["Total Threats Detected", str(total_threats)],
        ["Verification Success Rate", f"{success_rate}%"],
        ["Alert Rate", f"{round(total_threats / total_events * 100, 2) if total_events > 0 else 0}%"],
        ["Audit Ledger Integrity", ledger_status.get("integrity", "UNKNOWN")],
        ["Ledger Verified Blocks", str(ledger_status.get("total_blocks", 0))],
    ]
    story.append(_make_table(summary_data, col_widths=[90 * mm, 80 * mm]))

    story.append(PageBreak())

    # ---- Section 1: Teleportation-Based QDS Protocol Overview ----
    story.append(Paragraph("1. TELEPORTATION-BASED QDS PROTOCOL", styles["SectionHeader"]))
    story.append(Paragraph(
        "This framework implements quantum-inspired threat detection for a Teleportation-Based Quantum Digital "
        "Signature (QDS) protocol. The QDS protocol leverages Bell-state entanglement and quantum teleportation "
        "to distribute quantum public keys and verify digital signatures with information-theoretic security.",
        styles["BodyText2"]
    ))

    story.append(Paragraph("Protocol Flow:", styles["SubSectionHeader"]))
    protocol_steps = [
        ["STEP", "OPERATION", "QUANTUM PRINCIPLE"],
        ["1", "Bell State Preparation |Φ+⟩ = (|00⟩+|11⟩)/√2", "Entanglement Generation"],
        ["2", "Quantum Public Key Distribution via Teleportation", "Bell-State Measurement + Classical Channel"],
        ["3", "Pauli Correction Operations (X, Z gates)", "Pauli Eigenstates"],
        ["4", "Projective Measurement on Computational Basis", "Projective Measurement"],
        ["5", "Statistical Verification of Measurement Outcomes", "Threshold-Based Decision Rules"],
        ["6", "Threat Detection via Deviation Analysis", "Z-Score & Standard Deviation"],
    ]
    story.append(_make_table(protocol_steps, col_widths=[15 * mm, 90 * mm, 65 * mm]))

    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(
        "Detection Method: Pure deterministic statistical analysis — NO Artificial Intelligence or "
        "Machine Learning techniques are used. All threat identification is performed using z-score "
        "thresholds, measurement deviation analysis, hash integrity verification, and sliding-window "
        "temporal correlation.",
        styles["BodyText2"]
    ))

    # ---- Section 2: Threat Detection Statistics ----
    story.append(Paragraph("2. THREAT DETECTION STATISTICS", styles["SectionHeader"]))

    # Severity distribution
    story.append(Paragraph("Severity Distribution:", styles["SubSectionHeader"]))
    if sev_rows:
        sev_data = [["SEVERITY", "COUNT", "PERCENTAGE"]]
        for row in sev_rows:
            pct = round(row[1] / total_threats * 100, 2) if total_threats > 0 else 0
            sev_data.append([str(row[0]).upper(), str(row[1]), f"{pct}%"])
        story.append(_make_table(sev_data, col_widths=[55 * mm, 55 * mm, 55 * mm]))
    else:
        story.append(Paragraph("No threats recorded in this time period.", styles["BodyText2"]))

    # Threat type distribution
    story.append(Paragraph("Attack Type Distribution:", styles["SubSectionHeader"]))
    if type_rows:
        type_data = [["ATTACK TYPE", "COUNT", "PERCENTAGE"]]
        for row in type_rows:
            pct = round(row[1] / total_threats * 100, 2) if total_threats > 0 else 0
            type_data.append([str(row[0]), str(row[1]), f"{pct}%"])
        story.append(_make_table(type_data, col_widths=[70 * mm, 45 * mm, 50 * mm]))

    # ---- Section 3: Quantum Measurement Statistical Analysis ----
    story.append(Paragraph("3. QUANTUM MEASUREMENT STATISTICAL ANALYSIS", styles["SectionHeader"]))

    if deviations:
        m = mean(deviations)
        v = variance(deviations)
        std = std_deviation(deviations)

        meas_data = [
            ["STATISTIC", "VALUE"],
            ["Sample Count (n)", str(len(deviations))],
            ["Mean Deviation (μ)", f"{round(m * 100, 4)}%"],
            ["Standard Deviation (σ)", f"{round(std * 100, 4)}%"],
            ["Variance (σ²)", str(round(v, 8))],
            ["Max Deviation", f"{round(max(deviations) * 100, 4)}%"],
            ["Min Deviation", f"{round(min(deviations) * 100, 4)}%"],
        ]
        story.append(_make_table(meas_data, col_widths=[90 * mm, 80 * mm]))

        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("Detection Formula:", styles["SubSectionHeader"]))
        story.append(Paragraph(
            "Z-Score = (x - μ) / σ     where x = observed measurement deviation",
            styles["Formula"]
        ))
        story.append(Paragraph(
            "Threat triggered when: |Z-Score| > threshold  (default: 2.0)",
            styles["Formula"]
        ))
    else:
        story.append(Paragraph("No quantum measurement data available.", styles["BodyText2"]))

    # ---- Section 4: Forgery Probability Analysis ----
    story.append(Paragraph("4. FORGERY PROBABILITY ANALYSIS", styles["SectionHeader"]))

    story.append(Paragraph(
        "The forgery probability P_forge represents the likelihood that an adversary can successfully forge "
        "a quantum digital signature without detection. This is calculated from the False Negative rate of "
        "the detection framework:",
        styles["BodyText2"]
    ))

    story.append(Paragraph(
        "P_forge = FN / (TP + FN) = 1 - Recall",
        styles["Formula"]
    ))

    if test_metrics:
        tp = test_metrics.get("true_positives", 0)
        fp = test_metrics.get("false_positives", 0)
        fn = test_metrics.get("false_negatives", 0)
        tn = test_metrics.get("true_negatives", 0)
        precision = test_metrics.get("precision", 0)
        recall = test_metrics.get("recall", 0)
        f1 = test_metrics.get("f1_score", 0)
        detection_rate = test_metrics.get("detection_rate", 0)
        accuracy = test_metrics.get("accuracy", 0)

        forgery_prob = round(1 - (recall / 100), 4) if recall else 1.0
        false_alarm_rate = round(fp / (fp + tn) * 100, 2) if (fp + tn) > 0 else 0

        story.append(Paragraph("Latest Test Lab Results:", styles["SubSectionHeader"]))
        forgery_data = [
            ["METRIC", "VALUE", "INTERPRETATION"],
            ["True Positives (TP)", str(tp), "Correctly detected attacks"],
            ["False Positives (FP)", str(fp), "Benign flagged as threats (Type I error)"],
            ["False Negatives (FN)", str(fn), "Attacks missed by rules (Type II error)"],
            ["True Negatives (TN)", str(tn), "Benign correctly passed"],
            ["Precision (PPV)", f"{precision}%", "TP / (TP + FP)"],
            ["Recall (TPR)", f"{recall}%", "TP / (TP + FN)"],
            ["F1 Score", f"{f1}%", "2 × (Precision × Recall) / (Precision + Recall)"],
            ["Detection Rate", f"{detection_rate}%", "Attacks detected / Attacks injected"],
            ["Accuracy", f"{accuracy}%", "(TP + TN) / Total"],
            ["Forgery Probability", f"{forgery_prob * 100}%", "P_forge = 1 - Recall"],
            ["False Alarm Rate", f"{false_alarm_rate}%", "FP / (FP + TN)"],
        ]
        story.append(_make_table(forgery_data, col_widths=[50 * mm, 35 * mm, 80 * mm]))

        story.append(Spacer(1, 4 * mm))

        # Security guarantees
        story.append(Paragraph("Security Assessment:", styles["SubSectionHeader"]))
        if forgery_prob == 0:
            assessment = "STRONG — Zero forgery probability. All injected attacks were detected. The framework provides deterministic rejection of forged signatures."
        elif forgery_prob < 0.05:
            assessment = f"HIGH — Forgery probability is {forgery_prob*100:.2f}%, well below the 5% threshold. The framework demonstrates robust threat detection."
        elif forgery_prob < 0.15:
            assessment = f"MODERATE — Forgery probability is {forgery_prob*100:.2f}%. Consider tuning detection thresholds to improve recall."
        else:
            assessment = f"NEEDS IMPROVEMENT — Forgery probability is {forgery_prob*100:.2f}%. Detection rules require recalibration."

        story.append(Paragraph(assessment, styles["BodyText2"]))

    else:
        story.append(Paragraph(
            "No Test Lab results available. Run an attack simulation in the Test Lab to generate "
            "forgery probability metrics with real TP/FP/FN/TN confusion matrix data.",
            styles["BodyText2"]
        ))

    # ---- Section 5: Risk Score Mathematical Model ----
    story.append(Paragraph("5. RISK SCORE MATHEMATICAL MODEL", styles["SectionHeader"]))
    story.append(Paragraph(
        "The composite risk score for each detected threat is computed using a weighted multi-factor formula:",
        styles["BodyText2"]
    ))
    story.append(Paragraph(
        "RiskScore = w1×DeviationFactor + w2×VerificationPenalty + w3×ZScoreFactor + w4×ConfidenceWeight + w5×SeverityBase",
        styles["Formula"]
    ))
    story.append(Paragraph(
        "Where: w1=0.25, w2=0.20, w3=0.20, w4=0.15, w5=0.20  •  Range: [0, 100]",
        styles["Formula"]
    ))

    risk_formula = [
        ["FACTOR", "WEIGHT", "DESCRIPTION"],
        ["Deviation Factor", "25%", "Quantum measurement deviation magnitude vs expected baseline"],
        ["Verification Penalty", "20%", "Binary penalty: 100 if verification fails, 0 if passes"],
        ["Z-Score Factor", "20%", "Statistical outlier severity (capped at |z| = 5.0)"],
        ["Confidence Weight", "15%", "Rule-specific confidence score from detection engine"],
        ["Severity Base", "20%", "Categorical severity: Critical=100, High=75, Medium=50, Low=25"],
    ]
    story.append(_make_table(risk_formula, col_widths=[45 * mm, 20 * mm, 100 * mm]))

    # ---- Section 6: Audit Ledger Integrity ----
    story.append(Paragraph("6. TAMPER-EVIDENT AUDIT LEDGER", styles["SectionHeader"]))
    story.append(Paragraph(
        "All security events are recorded in a SHA-256 blockchain-style hash chain for immutable forensic evidence. "
        "Each block contains: event_hash, payload_hash, previous_hash, and block_hash = SHA-256(index || previous_hash || event_hash || payload_hash || timestamp).",
        styles["BodyText2"]
    ))

    ledger_data = [
        ["PROPERTY", "VALUE"],
        ["Total Blocks", str(ledger_status.get("total_blocks", 0))],
        ["Integrity Status", ledger_status.get("integrity", "UNKNOWN")],
        ["Last Block Hash", str(ledger_status.get("last_block_hash", "N/A"))[:40] + "..."],
        ["Hash Algorithm", "SHA-256 (Cryptographic)"],
        ["Chain Structure", "Sequential block_index with prev_hash linkage"],
    ]
    story.append(_make_table(ledger_data, col_widths=[55 * mm, 110 * mm]))

    # ---- Section 7: Detection Rules ----
    story.append(Paragraph("7. DETECTION RULE REGISTRY", styles["SectionHeader"]))
    rules_data = [
        ["RULE ID", "ATTACK TYPE", "DETECTION METHOD"],
        ["QDS-MITM-001", "MITM / Channel Manipulation", "Measurement deviation > threshold AND verification failure"],
        ["QDS-RPL-001", "Replay Attack", "Signature hash reuse within temporal sliding window"],
        ["QDS-FRG-001", "Forgery", "Signature hash integrity mismatch on payload"],
        ["QDS-IMP-001", "Impersonation", "Source node / session inconsistency in verification chain"],
        ["QDS-ANM-001", "Quantum Anomaly", "Statistical z-score outlier on measurement deviation"],
    ]
    story.append(_make_table(rules_data, col_widths=[35 * mm, 55 * mm, 75 * mm]))

    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceAfter=5 * mm))
    story.append(Paragraph(
        "End of Report — QDS SIEM Quantum-Inspired Cyber Threat Detection Framework",
        styles["FooterStyle"]
    ))

    # Build PDF
    doc.build(story, onFirstPage=_add_page_bg, onLaterPages=_add_page_bg)
    buffer.seek(0)

    filename = f"QDS_SIEM_Security_Report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
