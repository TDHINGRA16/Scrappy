FROM mcr.microsoft.com/playwright/python:v1.47.0-noble

# Use Playwright official image (has Chromium + deps preinstalled)
WORKDIR /app

# Install only Python dependencies from requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Use existing pwuser from Playwright image (UID 1000 already exists)
RUN chown -R pwuser:pwuser /app
USER pwuser

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
