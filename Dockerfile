# Stage 1: Build stage
FROM python:3.9-slim AS builder

WORKDIR /app
COPY requirements-flask.txt ./requirements.txt

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.9-slim

WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Create non-root user
RUN useradd -m appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser
EXPOSE 8501

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8501", "--workers", "2", "--timeout", "60", "app:app"]
