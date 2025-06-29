FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security (but don't switch to it yet)
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

# Create data directory with flexible permissions
RUN mkdir -p /app/data && \
    chmod 777 /app/data

# Note: USER will be set by Railway based on RAILWAY_RUN_UID
# If RAILWAY_RUN_UID=0, runs as root (needed for volume access)
# If not set, will run as root by default

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]