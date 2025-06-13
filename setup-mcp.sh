#!/bin/bash

echo "🔥 Firecrawl MCP Server Setup for Hotel Booking Project"
echo "====================================================="

# Check if API key is set
if [ -z "$FIRECRAWL_API_KEY" ]; then
    echo "❌ FIRECRAWL_API_KEY not found in environment"
    echo ""
    echo "📋 Setup Instructions:"
    echo "1. Get your API key from: https://firecrawl.dev/app/api-keys"
    echo "2. Set the environment variable:"
    echo "   export FIRECRAWL_API_KEY=fc-YOUR_ACTUAL_API_KEY"
    echo "3. Run this script again"
    echo ""
    exit 1
fi

echo "✅ FIRECRAWL_API_KEY found in environment"
echo "🔧 Starting Firecrawl MCP Server..."

# Update the config file with the actual API key
sed -i "s/YOUR_FIRECRAWL_API_KEY_HERE/$FIRECRAWL_API_KEY/g" mcp-config.json

echo "📁 Updated mcp-config.json with your API key"
echo "🚀 Starting MCP server..."

# Start the MCP server
npx firecrawl-mcp

echo "✅ Firecrawl MCP Server is running!"
echo ""
echo "🎯 Available Tools:"
echo "  - Web scraping for hotel research"
echo "  - Competitor analysis"  
echo "  - Market research"
echo "  - Content extraction"
echo "  - Deep research capabilities"