#!/bin/bash
# Koyeb PostgreSQL Database Setup Script
# Hotel Booking System - Zero-Risk Migration

echo "🚀 Creating Koyeb PostgreSQL Database..."
echo "======================================="

# Check if koyeb CLI is installed
if ! command -v koyeb &> /dev/null; then
    echo "❌ Koyeb CLI not found. Installing..."
    echo "📥 Download from: https://github.com/koyeb/koyeb-cli/releases"
    echo "Or run: curl https://www.koyeb.com/install.sh | sh"
    exit 1
fi

# Login check
echo "🔐 Checking Koyeb authentication..."
if ! koyeb auth status &> /dev/null; then
    echo "🔑 Please login to Koyeb first:"
    echo "   koyeb login"
    exit 1
fi

echo "✅ Koyeb CLI ready!"

# Create PostgreSQL database
echo ""
echo "🗄️ Creating PostgreSQL database..."
echo "Database name: hotel-booking-db"
echo "Type: PostgreSQL 15"
echo "Plan: Small (2GB RAM, 20GB Storage)"
echo "Region: Frankfurt (fra)"
echo ""

# Create the database
koyeb databases create hotel-booking-db \
  --type postgresql \
  --plan small \
  --region fra

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Database creation initiated!"
    echo "⏳ Waiting for database to be ready..."
    
    # Wait for database to be ready
    sleep 30
    
    echo ""
    echo "📊 Getting database connection details..."
    koyeb databases get hotel-booking-db
    
    echo ""
    echo "🎉 SUCCESS! Your PostgreSQL database is ready!"
    echo ""
    echo "🔗 Next steps:"
    echo "1. Copy the DATABASE_URL from above"
    echo "2. Add it to your .env file:"
    echo "   DATABASE_URL=postgresql://user:password@host:5432/database"
    echo "3. Run: python quick_test.py"
    echo "4. Run: python migrate_to_postgresql.py"
    echo ""
    
else
    echo "❌ Database creation failed!"
    echo "Please check your Koyeb account and try again."
    exit 1
fi