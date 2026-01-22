FROM python:3.11-slim

WORKDIR /app
# Keep environment variables minimal in image; set secrets at runtime in Coolify
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
# Install build and runtime deps (Cairo/WeasyPrint and common libs)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libcairo2-dev \
    pkg-config \
    libffi-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libxml2 \
        libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Copy app
COPY . .

# Create non-root user
RUN useradd --create-home appuser || true && chown -R appuser /app

# Add start script (controls app server)
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh
USER appuser

# Start script will either run gunicorn or python run.py depending on USE_PYTHON_RUN
CMD ["/app/start.sh"]
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    build-essential \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN pip install --no-cache-dir playwright && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY . .

# Create directories for logs and temp files
RUN mkdir -p /app/logs /app/temp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
