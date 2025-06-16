# Stage 1: Build stage
FROM python:3.9-slim AS builder

WORKDIR /app
COPY requirements.txt .

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
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true

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

ENTRYPOINT ["streamlit", "run"]
CMD ["app.py", "--server.address=0.0.0.0"]
