#!/bin/bash

# Koyeb Deployment Script with Conditional Dependencies
# This script tries to install full requirements, falls back to minimal if needed

echo "🚀 Starting Koyeb deployment..."

# Try installing full requirements with crawl4ai
echo "📦 Attempting full installation with Market Analysis features..."
pip install -r requirements.txt --timeout 300 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Full installation successful - Market Analysis enabled"
    export MARKET_ANALYSIS_ENABLED=true
else
    echo "⚠️ Full installation failed, trying production requirements..."
    
    # Fall back to production requirements
    pip install -r requirements-production.txt --timeout 300 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ Production installation successful - Market Analysis in demo mode"
        export MARKET_ANALYSIS_ENABLED=false
    else
        echo "❌ Both installations failed, trying minimal..."
        pip install -r requirements-minimal.txt --timeout 300 2>&1
        export MARKET_ANALYSIS_ENABLED=false
    fi
fi

# Start the application
echo "🎯 Starting Flask application..."
exec python app.py
