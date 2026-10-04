# Multi-arch compatible (x86_64 / ARM64 Ampere A1 on Oracle Cloud)
FROM python:3.12-slim-bookworm

# System dependencies & CA certificates for secure external HTTPS requests
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user for security
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Install dependencies first for Docker layer caching
COPY pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir ".[dev]" || pip install --no-cache-dir .

# Copy application source code
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/
COPY entrypoint.sh /app/

# Set permissions
RUN chmod +x /app/entrypoint.sh && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
