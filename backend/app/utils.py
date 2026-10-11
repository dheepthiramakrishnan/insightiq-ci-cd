"""
utils.py
---------
Reusable helper functions shared across the backend.
"""

import os
import uuid
from datetime import datetime

import pandas as pd
from fastapi import UploadFile

# Required columns every uploaded sales CSV must contain.
REQUIRED_COLUMNS = [
    "Order ID",
    "Customer Name",
    "Region",
    "Category",
    "Product Name",
    "Quantity",
    "Sales",
    "Profit",
    "Order Date",
]

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_csv_file(file: UploadFile, df: pd.DataFrame) -> tuple[bool, str]:
    """
    Validate an uploaded CSV file.

    Checks:
    - File has a .csv extension
    - File is not empty (has at least one data row)
    - All required columns are present

    Returns:
        (is_valid, error_message). error_message is "" when valid.
    """
    if not file.filename.lower().endswith(".csv"):
        return False, "Only .csv files are supported."

    if df.empty:
        return False, "The uploaded CSV file is empty."

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"

    return True, ""


def save_uploaded_file(file_bytes: bytes, original_filename: str) -> str:
    """
    Save the raw uploaded CSV bytes to disk under a unique filename so
    multiple uploads don't overwrite each other. Returns the saved path.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    safe_name = f"{timestamp}_{unique_id}_{original_filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    return file_path


def format_currency(value: float) -> str:
    """Format a number as a currency string, e.g. 12345.6 -> '$12,345.60'."""
    try:
        return f"${value:,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def generate_pdf_report(dataset_name: str, kpis: dict, insights, format_currency):
    """
    Build a downloadable PDF report containing the KPI summary and
    (if available) AI-generated business insights, using ReportLab.
    Returns an in-memory BytesIO buffer ready to stream to the client.
    """
    import io as _io

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    buffer = _io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.7 * inch, bottomMargin=0.7 * inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleBlue", parent=styles["Title"], textColor=colors.HexColor("#1a56db")
    )
    heading_style = ParagraphStyle(
        "HeadingBlue", parent=styles["Heading2"], textColor=colors.HexColor("#1a56db"), spaceBefore=14
    )

    elements = [
        Paragraph("InsightIQ - Business Intelligence Report", title_style),
        Paragraph(f"Dataset: {dataset_name}", styles["Normal"]),
        Spacer(1, 16),
        Paragraph("Key Performance Indicators", heading_style),
    ]

    kpi_rows = [
        ["Total Sales", format_currency(kpis.get("total_sales", 0))],
        ["Total Profit", format_currency(kpis.get("total_profit", 0))],
        ["Total Orders", str(kpis.get("total_orders", 0))],
        ["Total Customers", str(kpis.get("total_customers", 0))],
        ["Best Selling Category", str(kpis.get("best_selling_category", "N/A"))],
        ["Highest Revenue Region", str(kpis.get("highest_revenue_region", "N/A"))],
    ]
    kpi_table = Table(kpi_rows, colWidths=[220, 220])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf1fd")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1e293b")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(kpi_table)

    if insights:
        elements.append(Paragraph("AI-Generated Business Insights", heading_style))
        elements.append(Paragraph(insights.get("executive_summary", ""), styles["Normal"]))

        for section_title, key in [
            ("Key Trends", "key_trends"),
            ("Best Performing Products", "best_performing_products"),
            ("Weak Performing Regions", "weak_performing_regions"),
            ("Recommendations", "recommendations"),
        ]:
            items = insights.get(key, [])
            if items:
                elements.append(Paragraph(section_title, heading_style))
                for item in items:
                    elements.append(Paragraph(f"&bull; {item}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer
