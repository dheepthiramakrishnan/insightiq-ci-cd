"""
analytics.py
-------------
Handles all data cleaning, transformation, and analytical computations
using Pandas and NumPy.
"""

from typing import Optional

import numpy as np
import pandas as pd


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a raw uploaded sales DataFrame:
    - Remove duplicate rows
    - Handle missing values (drop rows missing critical fields)
    - Convert 'Order Date' to datetime
    - Ensure numeric fields (Quantity, Sales, Profit) are numeric
    """
    df = df.copy()

    # Remove exact duplicate rows
    df.drop_duplicates(inplace=True)

    # Convert date column
    if "Order Date" in df.columns:
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

    # Ensure numeric fields are numeric, coercing bad values to NaN
    for col in ["Quantity", "Sales", "Profit"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows missing any critical field required for analysis
    critical_cols = [c for c in ["Order Date", "Sales", "Profit", "Region", "Category"] if c in df.columns]
    df.dropna(subset=critical_cols, inplace=True)

    # Reset index after cleaning
    df.reset_index(drop=True, inplace=True)

    return df


def apply_filters(
    df: pd.DataFrame,
    year: Optional[int] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
) -> pd.DataFrame:
    """Apply optional Year / Region / Category filters to the DataFrame."""
    filtered = df.copy()

    if year:
        filtered = filtered[filtered["Order Date"].dt.year == year]
    if region and region.lower() != "all":
        filtered = filtered[filtered["Region"] == region]
    if category and category.lower() != "all":
        filtered = filtered[filtered["Category"] == category]

    return filtered


def calculate_kpis(df: pd.DataFrame) -> dict:
    """Compute dashboard KPI values from a cleaned DataFrame."""
    if df.empty:
        return {
            "total_sales": 0,
            "total_profit": 0,
            "total_orders": 0,
            "total_customers": 0,
            "best_selling_category": "N/A",
            "highest_revenue_region": "N/A",
        }

    total_sales = float(df["Sales"].sum())
    total_profit = float(df["Profit"].sum())
    total_orders = int(df["Order ID"].nunique())
    total_customers = int(df["Customer Name"].nunique())

    best_selling_category = (
        df.groupby("Category")["Sales"].sum().idxmax() if "Category" in df.columns else "N/A"
    )
    highest_revenue_region = (
        df.groupby("Region")["Sales"].sum().idxmax() if "Region" in df.columns else "N/A"
    )

    return {
        "total_sales": round(total_sales, 2),
        "total_profit": round(total_profit, 2),
        "total_orders": total_orders,
        "total_customers": total_customers,
        "best_selling_category": best_selling_category,
        "highest_revenue_region": highest_revenue_region,
    }


def get_monthly_sales_trend(df: pd.DataFrame) -> dict:
    """Return month-wise total sales for a line chart."""
    if df.empty:
        return {"months": [], "sales": []}

    monthly = (
        df.set_index("Order Date")
        .resample("ME")["Sales"]
        .sum()
        .reset_index()
    )
    monthly["month"] = monthly["Order Date"].dt.strftime("%b %Y")

    return {
        "months": monthly["month"].tolist(),
        "sales": monthly["Sales"].round(2).tolist(),
    }


def get_sales_by_region(df: pd.DataFrame) -> dict:
    """Return total sales grouped by region for a bar/pie chart."""
    if df.empty:
        return {"regions": [], "sales": []}

    grouped = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
    return {"regions": grouped.index.tolist(), "sales": grouped.round(2).tolist()}


def get_sales_by_category(df: pd.DataFrame) -> dict:
    """Return total sales grouped by category for a bar/pie chart."""
    if df.empty:
        return {"categories": [], "sales": []}

    grouped = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
    return {"categories": grouped.index.tolist(), "sales": grouped.round(2).tolist()}


def get_top_products(df: pd.DataFrame, top_n: int = 10) -> dict:
    """Return the top N products by total sales."""
    if df.empty:
        return {"products": [], "sales": []}

    grouped = (
        df.groupby("Product Name")["Sales"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
    )
    return {"products": grouped.index.tolist(), "sales": grouped.round(2).tolist()}


def get_profit_by_category(df: pd.DataFrame) -> dict:
    """Return total profit grouped by category."""
    if df.empty:
        return {"categories": [], "profit": []}

    grouped = df.groupby("Category")["Profit"].sum().sort_values(ascending=False)
    return {"categories": grouped.index.tolist(), "profit": grouped.round(2).tolist()}
