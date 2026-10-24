# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm AS base

# Install OS libraries for Tesseract OCR, Spanish language pack, and zbar QR decoder
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    libzbar0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy uv binary directly from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install python dependencies first (cached layer)
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-install-project --frozen --no-cache --no-dev

# Copy application source
COPY src/ src/
COPY ruff.toml .

# Sync the root project into venv
RUN uv sync --frozen --no-cache --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENV DATABASE_URL="sqlite+aiosqlite:////data/verifact.db"
ENV PYTHONUNBUFFERED=1

# Persistent storage volume for SQLite WAL database
VOLUME ["/data"]

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
