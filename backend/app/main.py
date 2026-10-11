"""
main.py
--------
Entry point for the InsightIQ FastAPI backend.

Responsibilities:
- Initialize the FastAPI application
- Configure CORS so the frontend (served separately) can call the API
- Create database tables on startup
- Register all API routes from routes.py
- Serve the frontend static files (CSS/JS/images) and HTML templates

NOTE: This is a Module 2 skeleton. Route wiring and DB table creation
will be completed once database.py (Module 3) and routes.py (Module 6)
are implemented.

to run:
cd backend
uvicorn app.main:app --reload
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base
from app import models  # noqa: F401 - ensures models are registered with Base
from app.routes import router as api_router

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")

app = FastAPI(
    title="InsightIQ - AI-Powered Business Intelligence Dashboard",
    description="Upload sales data, explore analytics, and generate AI-powered business insights.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
# Allows the frontend (HTML/JS served on a different port during development)
# to communicate with this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Database Table Creation
# ---------------------------------------------------------------------------
# Creates all tables defined in models.py if they don't already exist.
# For a student project this is simpler than running Alembic migrations.
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Static Files (CSS / JS / images)
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["Health Check"])
async def health_check():
    """Simple health check endpoint to verify the API is running."""
    return {"status": "ok", "service": "InsightIQ API"}


# ---------------------------------------------------------------------------
# Frontend Pages
# ---------------------------------------------------------------------------
# Plain HTML pages (no templating engine needed) that call the /api
# endpoints via JavaScript fetch(). Serving them directly from FastAPI
# keeps the whole app running from a single "uvicorn app.main:app" command.

@app.get("/", tags=["Frontend"])
async def serve_dashboard():
    """Dashboard Home page."""
    return FileResponse(os.path.join(TEMPLATES_DIR, "dashboard.html"))


@app.get("/upload", tags=["Frontend"])
async def serve_upload_page():
    """Upload Dataset page."""
    return FileResponse(os.path.join(TEMPLATES_DIR, "upload.html"))


@app.get("/analytics", tags=["Frontend"])
async def serve_analytics_page():
    """Analytics page."""
    return FileResponse(os.path.join(TEMPLATES_DIR, "analytics.html"))


@app.get("/insights", tags=["Frontend"])
async def serve_insights_page():
    """AI Insights page."""
    return FileResponse(os.path.join(TEMPLATES_DIR, "insights.html"))
