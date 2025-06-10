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

# Emergency install with minimal dependencies
RUN echo "🚨 Emergency deployment mode..." && \
    (echo "Trying emergency minimal requirements..." && \
     pip install --no-cache-dir --timeout=300 -r requirements-emergency.txt && \
     echo "✅ Emergency install successful!" && \
     export MARKET_ANALYSIS_MODE=demo_only) || \
    (echo "Trying production requirements..." && \
     pip install --no-cache-dir --timeout=300 -r requirements-production.txt) || \
    (echo "Final fallback to minimal..." && \
     pip install --no-cache-dir --timeout=300 -r requirements-minimal.txt)

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
