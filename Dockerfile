FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

WORKDIR /app

# Install system dependencies (minimal for faster build)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements files
COPY requirements*.txt ./

# Multi-step installation strategy with specific error handling
RUN echo "🚀 Trying installation strategy..." && \
    (echo "Step 1: Trying latest crawl4ai version..." && \
     pip install --no-cache-dir --timeout=300 -r requirements-latest.txt && \
     echo "✅ Latest version installed successfully!" && \
     export MARKET_ANALYSIS_MODE=latest) || \
    (echo "Step 2: Trying stable crawl4ai version..." && \
     pip install --no-cache-dir --timeout=300 -r requirements.txt && \
     echo "✅ Stable version installed successfully!" && \
     export MARKET_ANALYSIS_MODE=stable) || \
    (echo "Step 3: Trying production mode (no crawl4ai)..." && \
     pip install --no-cache-dir --timeout=300 -r requirements-production.txt && \
     echo "✅ Production mode installed successfully!" && \
     export MARKET_ANALYSIS_MODE=demo) || \
    (echo "Step 4: Using minimal requirements..." && \
     pip install --no-cache-dir --timeout=300 -r requirements-minimal.txt && \
     echo "✅ Minimal install completed!" && \
     export MARKET_ANALYSIS_MODE=disabled)

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p static templates

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run the application directly
CMD ["python", "app.py"]
