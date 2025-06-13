# 🔥 Firecrawl MCP Server Setup Guide

## 📋 Quick Setup (5 minutes)

### **Step 1: Get Your API Key**
1. Visit: https://firecrawl.dev/app/api-keys
2. Sign up/login to get your API key
3. Copy the API key (format: `fc-xxxxxxxxxx`)

### **Step 2: Set Environment Variable**
```bash
# Set your API key (replace with your actual key)
export FIRECRAWL_API_KEY=fc-YOUR_ACTUAL_API_KEY

# Add to your shell profile for persistence
echo 'export FIRECRAWL_API_KEY=fc-YOUR_ACTUAL_API_KEY' >> ~/.bashrc
source ~/.bashrc
```

### **Step 3: Start MCP Server**
```bash
# Quick start (recommended)
./setup-mcp.sh

# Or manually
npx firecrawl-mcp
```

## 🎯 Hotel Business Use Cases

### **Competitor Research**
- Scrape competitor hotel websites for pricing
- Monitor booking availability
- Analyze competitor amenities and services
- Track market rates in your area

### **Market Analysis** 
- Research local tourism trends
- Analyze visitor reviews and feedback
- Monitor local events affecting bookings
- Study seasonal pricing patterns

### **Content Creation**
- Extract hotel descriptions for inspiration
- Research local attractions for guest guides
- Gather restaurant recommendations
- Create comprehensive area guides

### **Business Intelligence**
- Monitor travel booking sites
- Track industry news and trends
- Research new hotel technologies
- Analyze customer sentiment

## 🛠️ Available MCP Tools

Once running, you'll have access to:

- **Web Scraping**: Extract data from any website
- **Batch Processing**: Handle multiple URLs efficiently
- **Web Search**: Search the web for specific information
- **Content Extraction**: Get clean, structured data
- **Deep Research**: Comprehensive research capabilities

## 🔧 Configuration Files

- **`mcp-config.json`**: MCP server configuration
- **`package.json`**: Node.js dependencies
- **`setup-mcp.sh`**: Quick setup script

## 🚨 Troubleshooting

### **API Key Issues**
```bash
# Check if API key is set
echo $FIRECRAWL_API_KEY

# Should show: fc-xxxxxxxxxx
```

### **Permission Issues**
```bash
# Make sure script is executable
chmod +x setup-mcp.sh
```

### **Port Conflicts**
- MCP server runs on default ports
- Check no other MCP servers are running
- Restart if needed

## 🎉 Integration with Hotel Project

The MCP server will enhance your hotel management system with:

- **Real-time market data** for pricing decisions
- **Competitor monitoring** for strategic advantage  
- **Guest research tools** for better service
- **Content generation** for marketing materials
- **Business intelligence** for growth planning

## 📞 Support

- **Firecrawl Docs**: https://docs.firecrawl.dev/
- **MCP Guide**: https://docs.firecrawl.dev/mcp
- **Support**: help@firecrawl.com

---

**Ready to enhance your hotel business with AI-powered web intelligence!** 🚀