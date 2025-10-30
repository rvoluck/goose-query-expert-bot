# Multi-stage Docker build for Goose Slackbot
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directory
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN mkdir -p /app && chown appuser:appuser /app
WORKDIR /app

# ================================
# Development stage
# ================================
FROM base as development

# Install development dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    vim \
    htop \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements-db.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-db.txt

# Install development tools
RUN pip install --no-cache-dir \
    pytest-cov \
    pytest-xdist \
    ipython \
    jupyter

# Copy source code
COPY --chown=appuser:appuser . .

# Switch to app user
USER appuser

# Expose ports
EXPOSE 3000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3000/health', timeout=5)"

# Default command for development
CMD ["python", "-m", "uvicorn", "slack_bot:app", "--host", "0.0.0.0", "--port", "3000", "--reload"]

# ================================
# Production build stage
# ================================
FROM base as builder

# Copy requirements
COPY requirements.txt requirements-db.txt ./

# Install dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt -r requirements-db.txt

# ================================
# Production runtime stage
# ================================
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directory
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN mkdir -p /app && chown appuser:appuser /app
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data && chown -R appuser:appuser /app/logs /app/data

# Switch to app user
USER appuser

# Expose ports
EXPOSE 3000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python health_check.py || exit 1

# Production command
CMD ["gunicorn", "--config", "gunicorn.conf.py", "slack_bot:app"]
