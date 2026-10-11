# ---- Stage 1: run the test-suite (Jenkins builds this with --target test) ----
FROM python:3.12-slim AS test
ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt -r requirements-dev.txt
COPY . .
ENV DATABASE_URL=sqlite:////tmp/ci_test.db
RUN python -m pytest -q

# ---- Stage 2: production image ----
FROM python:3.12-slim
ARG BUILD_NUMBER=local
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    APP_VERSION=${BUILD_NUMBER} APP_ENV=production
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY backend ./backend
COPY frontend ./frontend
RUN useradd -m appuser && mkdir -p backend/app/uploads && chown -R appuser /app
USER appuser
WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
