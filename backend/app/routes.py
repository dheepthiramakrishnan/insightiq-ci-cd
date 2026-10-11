"""
routes.py
----------
Defines all REST API endpoints for InsightIQ and wires them into a
single APIRouter that main.py mounts under the /api prefix.
"""

import io
import json
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import analytics, utils
from app.ai_service import generate_business_insights
from app.database import get_db
from app.models import UploadedDataset
from app.schemas import (
    AIInsightResponse,
    ChartDataResponse,
    DatasetHistoryItem,
    DatasetUploadResponse,
    KPIResponse,
)
from app.utils import format_currency

router = APIRouter()


@router.get("/ping", tags=["Health Check"])
async def ping():
    """Simple endpoint to confirm the API router is wired up correctly."""
    return {"message": "InsightIQ API router is active"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_dataset_or_404(dataset_id: Optional[int], db: Session) -> UploadedDataset:
    """
    Fetch a specific dataset by ID, or fall back to the most recently
    uploaded dataset if no ID is given. Raises 404 if none exist.
    """
    query = db.query(UploadedDataset)
    if dataset_id is not None:
        dataset = query.filter(UploadedDataset.id == dataset_id).first()
    else:
        dataset = query.order_by(UploadedDataset.uploaded_at.desc()).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="No uploaded dataset found. Please upload a CSV first.")

    return dataset


def _load_clean_dataframe(dataset: UploadedDataset) -> pd.DataFrame:
    """Load the raw CSV from disk for a dataset and return it cleaned."""
    try:
        df = pd.read_csv(dataset.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Stored dataset file could not be found on disk.")
    return analytics.clean_dataset(df)


# ---------------------------------------------------------------------------
# 1. CSV Upload
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=DatasetUploadResponse, tags=["Upload"])
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a sales CSV file. Validates the file, cleans it, stores the
    raw file on disk, and records metadata (row count, totals) in MySQL.
    """
    raw_bytes = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid CSV.")

    is_valid, error_message = utils.validate_csv_file(file, df)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    cleaned_df = analytics.clean_dataset(df)
    kpis = analytics.calculate_kpis(cleaned_df)

    file_path = utils.save_uploaded_file(raw_bytes, file.filename)

    dataset = UploadedDataset(
        filename=file.filename,
        file_path=file_path,
        row_count=len(cleaned_df),
        total_sales=kpis["total_sales"],
        total_profit=kpis["total_profit"],
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return DatasetUploadResponse(
        dataset_id=dataset.id,
        filename=dataset.filename,
        row_count=dataset.row_count,
        total_sales=dataset.total_sales,
        total_profit=dataset.total_profit,
        uploaded_at=dataset.uploaded_at,
    )


@router.get("/uploads", response_model=list[DatasetHistoryItem], tags=["Upload"])
async def get_upload_history(db: Session = Depends(get_db)):
    """Return upload history, most recent first."""
    datasets = db.query(UploadedDataset).order_by(UploadedDataset.uploaded_at.desc()).all()
    return [
        DatasetHistoryItem(
            dataset_id=d.id, filename=d.filename, row_count=d.row_count, uploaded_at=d.uploaded_at
        )
        for d in datasets
    ]


# ---------------------------------------------------------------------------
# Filter Options
# ---------------------------------------------------------------------------

@router.get("/filters/options", tags=["Analytics"])
async def get_filter_options(dataset_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Return available Year / Region / Category values for filter dropdowns."""
    dataset = _get_dataset_or_404(dataset_id, db)
    df = _load_clean_dataframe(dataset)

    return {
        "years": sorted(df["Order Date"].dt.year.unique().tolist()) if not df.empty else [],
        "regions": sorted(df["Region"].unique().tolist()) if not df.empty else [],
        "categories": sorted(df["Category"].unique().tolist()) if not df.empty else [],
    }


# ---------------------------------------------------------------------------
# Dashboard KPIs
# ---------------------------------------------------------------------------

@router.get("/kpis", response_model=KPIResponse, tags=["Analytics"])
async def get_kpis(
    dataset_id: Optional[int] = None,
    year: Optional[int] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return dashboard KPI summary, optionally filtered by year/region/category."""
    dataset = _get_dataset_or_404(dataset_id, db)
    df = _load_clean_dataframe(dataset)
    filtered = analytics.apply_filters(df, year=year, region=region, category=category)
    return analytics.calculate_kpis(filtered)


# ---------------------------------------------------------------------------
# Chart Data
# ---------------------------------------------------------------------------

CHART_FUNCTIONS = {
    "monthly-sales-trend": analytics.get_monthly_sales_trend,
    "sales-by-region": analytics.get_sales_by_region,
    "sales-by-category": analytics.get_sales_by_category,
    "top-products": analytics.get_top_products,
    "profit-by-category": analytics.get_profit_by_category,
}


@router.get("/charts/{chart_name}", response_model=ChartDataResponse, tags=["Analytics"])
async def get_chart_data(
    chart_name: str,
    dataset_id: Optional[int] = None,
    year: Optional[int] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Return data for a specific chart. Valid chart_name values:
    monthly-sales-trend, sales-by-region, sales-by-category,
    top-products, profit-by-category.
    """
    if chart_name not in CHART_FUNCTIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown chart '{chart_name}'. Valid options: {list(CHART_FUNCTIONS.keys())}",
        )

    dataset = _get_dataset_or_404(dataset_id, db)
    df = _load_clean_dataframe(dataset)
    filtered = analytics.apply_filters(df, year=year, region=region, category=category)

    data = CHART_FUNCTIONS[chart_name](filtered)
    return ChartDataResponse(chart_name=chart_name, data=data)


# ---------------------------------------------------------------------------
# AI Insights
# ---------------------------------------------------------------------------

@router.get("/insights", response_model=AIInsightResponse, tags=["AI Insights"])
async def get_ai_insights(dataset_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Generate (or return cached) AI business insights for a dataset using
    the Gemini API.
    """
    dataset = _get_dataset_or_404(dataset_id, db)

    # Return cached insights if we've already generated them for this dataset.
    if dataset.ai_insights:
        return AIInsightResponse(**json.loads(dataset.ai_insights))

    df = _load_clean_dataframe(dataset)
    kpis = analytics.calculate_kpis(df)
    chart_data = {
        "monthly_sales_trend": analytics.get_monthly_sales_trend(df),
        "sales_by_region": analytics.get_sales_by_region(df),
        "sales_by_category": analytics.get_sales_by_category(df),
        "top_products": analytics.get_top_products(df),
        "profit_by_category": analytics.get_profit_by_category(df),
    }

    insights = generate_business_insights(kpis, chart_data)

    dataset.ai_insights = json.dumps(insights)
    db.commit()

    return AIInsightResponse(**insights)


# ---------------------------------------------------------------------------
# PDF Reports
# ---------------------------------------------------------------------------

@router.get("/reports/pdf", tags=["Reports"])
async def download_pdf_report(dataset_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Generate and download a PDF report containing KPIs and AI insights."""
    dataset = _get_dataset_or_404(dataset_id, db)
    df = _load_clean_dataframe(dataset)
    kpis = analytics.calculate_kpis(df)

    insights = json.loads(dataset.ai_insights) if dataset.ai_insights else None

    pdf_buffer = utils.generate_pdf_report(
        dataset_name=dataset.filename, kpis=kpis, insights=insights, format_currency=format_currency
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=InsightIQ_Report_{dataset.id}.pdf"},
    )
