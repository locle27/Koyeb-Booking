#!/usr/bin/env python3
"""
Quick Test Script - Hotel Booking PostgreSQL Migration
Fast 30-second test to verify everything is working

This script quickly checks:
✅ Environment setup
✅ Dependencies
✅ Google Sheets connection
✅ Basic imports
✅ Ready for migration
"""

import os
import sys
import time
from datetime import datetime

def print_status(message, status="info"):
    """Print colored status messages"""
    colors = {
        "success": "\033[92m✅",
        "error": "\033[91m❌", 
        "warning": "\033[93m⚠️",
        "info": "\033[94m🔍",
        "reset": "\033[0m"
    }
    print(f"{colors.get(status, colors['info'])} {message}{colors['reset']}")

def quick_test():
    """Run quick 30-second test"""
    print("\n" + "⚡" * 50)
    print("🚀 QUICK MIGRATION TEST - 30 Second Verification")
    print("⚡" * 50 + "\n")
    
    start_time = time.time()
    
    # Test 1: Environment Variables
    print("🔧 Checking Environment...")
    required_vars = ['GCP_CREDS_FILE_PATH', 'DEFAULT_SHEET_ID', 'GOOGLE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print_status(f"Missing environment variables: {', '.join(missing_vars)}", "error")
        print("   Set these in your .env file or export them")
        return False
    else:
        print_status("Environment variables OK", "success")
    
    # Test 2: Basic Dependencies
    print("\n📦 Checking Dependencies...")
    try:
        import pandas
        import flask
        import gspread
        print_status("Core dependencies installed", "success")
    except ImportError as e:
        print_status(f"Missing dependency: {e}", "error")
        print("   Run: pip install pandas flask gspread")
        return False
    
    # Test 3: PostgreSQL Dependencies (optional)
    try:
        import psycopg2
        import sqlalchemy
        import flask_sqlalchemy
        print_status("PostgreSQL dependencies installed", "success")
        postgres_ready = True
    except ImportError:
        print_status("PostgreSQL dependencies not installed (optional for testing)", "warning")
        print("   For full migration, run: pip install psycopg2-binary SQLAlchemy Flask-SQLAlchemy")
        postgres_ready = False
    
    # Test 4: Google Sheets Connection
    print("\n📊 Testing Google Sheets...")
    try:
        from logic import import_from_gsheet
        
        sheet_id = os.getenv('DEFAULT_SHEET_ID')
        creds_path = os.getenv('GCP_CREDS_FILE_PATH')
        
        df = import_from_gsheet(sheet_id, creds_path)
        print_status(f"Google Sheets connected - {len(df)} records loaded", "success")
        sheets_working = True
        
    except Exception as e:
        print_status(f"Google Sheets error: {str(e)[:100]}...", "error")
        sheets_working = False
    
    # Test 5: Migration Files
    print("\n📋 Checking Migration Files...")
    required_files = [
        'models.py',
        'database_service.py', 
        'migrate_to_postgresql.py',
        'database_schema.sql'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print_status(f"Missing files: {', '.join(missing_files)}", "error")
        return False
    else:
        print_status("All migration files present", "success")
    
    # Test 6: Import Migration Components
    print("\n🔄 Testing Migration Components...")
    try:
        from models import Guest, Booking, db
        from database_service import HybridDatabaseService, DatabaseConfig
        print_status("Migration components import successfully", "success")
        migration_ready = True
    except Exception as e:
        print_status(f"Migration import error: {str(e)[:100]}...", "error")
        migration_ready = False
    
    # Test 7: Database URL (if provided)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print("\n🗄️ Testing PostgreSQL Connection...")
        if postgres_ready:
            try:
                import psycopg2
                from urllib.parse import urlparse
                
                url = urlparse(database_url)
                conn = psycopg2.connect(
                    host=url.hostname,
                    port=url.port,
                    database=url.path[1:],
                    user=url.username,
                    password=url.password
                )
                conn.close()
                print_status(f"PostgreSQL connected to {url.hostname}", "success")
                postgres_connected = True
            except Exception as e:
                print_status(f"PostgreSQL connection failed: {str(e)[:100]}...", "error")
                postgres_connected = False
        else:
            print_status("PostgreSQL dependencies missing - cannot test connection", "warning")
            postgres_connected = False
    else:
        print_status("DATABASE_URL not set - PostgreSQL not configured", "warning")
        postgres_connected = False
    
    # Summary
    duration = time.time() - start_time
    print("\n" + "=" * 50)
    print("📊 QUICK TEST SUMMARY")
    print("=" * 50)
    
    print(f"⏱️ Test Duration: {duration:.1f} seconds")
    
    if sheets_working and migration_ready:
        print_status("🎉 READY FOR MIGRATION!", "success")
        print("\n🔗 Next Steps:")
        
        if postgres_connected:
            print("   1. ✅ PostgreSQL ready - run full migration")
            print("   2. 🚀 python migrate_to_postgresql.py --dry-run")
            print("   3. 🚀 python migrate_to_postgresql.py")
        else:
            print("   1. 🔧 Setup PostgreSQL database on Koyeb")
            print("   2. 🔧 Set DATABASE_URL environment variable")
            print("   3. 📦 pip install psycopg2-binary SQLAlchemy Flask-SQLAlchemy")
            print("   4. 🚀 python migrate_to_postgresql.py")
        
        print("\n📚 Documentation:")
        print("   📄 KOYEB_POSTGRESQL_SETUP.md - Setup guide")
        print("   🧪 python test_migration_system.py - Full test suite")
        
        return True
    else:
        print_status("❌ SETUP INCOMPLETE", "error")
        print("\n🔧 Issues to fix:")
        if not sheets_working:
            print("   • Fix Google Sheets connection")
        if not migration_ready:
            print("   • Fix migration component imports")
        
        return False

if __name__ == '__main__':
    success = quick_test()
    sys.exit(0 if success else 1)