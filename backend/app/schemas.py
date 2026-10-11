"""
schemas.py
-----------
Pydantic schemas used for request validation and response serialization.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DatasetUploadResponse(BaseModel):
    """Response returned after a successful CSV upload."""

    dataset_id: int
    filename: str
    row_count: int
    total_sales: float
    total_profit: float
    uploaded_at: datetime
    message: str = "File uploaded and processed successfully."

    class Config:
        from_attributes = True


class DatasetHistoryItem(BaseModel):
    """A single row in the upload history list."""

    dataset_id: int
    filename: str
    row_count: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class KPIResponse(BaseModel):
    """Response schema for dashboard KPI cards."""

    total_sales: float
    total_profit: float
    total_orders: int
    total_customers: int
    best_selling_category: str
    highest_revenue_region: str


class ChartDataResponse(BaseModel):
    """Generic response wrapper for chart data (keys vary by chart type)."""

    chart_name: str
    data: dict


class AIInsightResponse(BaseModel):
    """Response schema for Gemini-generated business insights."""

    executive_summary: str
    key_trends: List[str]
    best_performing_products: List[str]
    weak_performing_regions: List[str]
    recommendations: List[str]
