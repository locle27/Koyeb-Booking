#!/usr/bin/env python3
"""
Instant Local Web Server
Run your hotel booking system locally with all optimizations
No deployment delays - instant changes!
"""

import os
import sys
from flask import Flask

def setup_environment():
    """Set up environment for local testing"""
    print("🔧 Setting up environment for local testing...")
    
    env_vars = {
        'DATABASE_URL': 'postgres://koyeb-adm:npg_T4hEuUQeDl7A@ep-little-haze-a2133rvc.eu-central-1.pg.koyeb.app:5432/koyebdb',
        'DEFAULT_SHEET_ID': '13kQETOUGCVUwUqZrxeLy-WAj3b17SugI4L8Oq09SX2w',
        'GCP_CREDS_FILE_PATH': 'credentials.json',
        'GOOGLE_API_KEY': 'AIzaSyA-0V4VgrJbnzQWueDVI9pSOoH_V2EMUg4',
        'USE_POSTGRESQL': 'false',  # Start safe with Google Sheets primary
        'USE_HYBRID_MODE': 'true',
        'FALLBACK_TO_SHEETS': 'true',
        'ENABLE_PERFORMANCE_LOGGING': 'true',
        'FLASK_ENV': 'development',
        'FLASK_DEBUG': 'True',
        'FLASK_APP': 'app.py'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Environment configured")
    return env_vars

def create_development_server():
    """Create optimized development server"""
    print("🚀 Creating development server...")
    
    # Import your main app
    try:
        from app import app
        print("✅ Main app imported successfully")
        
        # Enable debug mode for instant reloading
        app.config['DEBUG'] = True
        app.config['TESTING'] = False
        
        return app
    except ImportError as e:
        print(f"❌ Could not import app: {e}")
        print("💡 Make sure app.py exists and is working")
        return None
    except Exception as e:
        print(f"❌ App setup error: {e}")
        return None

def run_local_server(app, port=5000):
    """Run the local development server"""
    print(f"🌐 Starting server on port {port}...")
    print(f"📍 Local URL: http://localhost:{port}")
    print(f"🔄 Auto-reload enabled - changes appear instantly!")
    print(f"🛡️ Using hybrid database (PostgreSQL + Google Sheets fallback)")
    print()
    print("🎯 TESTING URLS:")
    print(f"   • Dashboard: http://localhost:{port}/")
    print(f"   • Bookings: http://localhost:{port}/bookings")
    print(f"   • API Health: http://localhost:{port}/api/database/health")
    print(f"   • Performance: http://localhost:{port}/api/database/performance")
    print()
    print("💡 NEXT STEPS:")
    print("1. Open http://localhost:5000 in your browser")
    print("2. Test all features locally")
    print("3. Make changes to files - they appear instantly!")
    print("4. When ready, share via ngrok: ngrok http 5000")
    print()
    print("⏹️ Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Run with debug mode for auto-reload
        app.run(
            host='0.0.0.0',  # Allow external connections
            port=port,
            debug=True,
            use_reloader=True,
            use_debugger=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n⏹️ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

def main():
    """Main function"""
    print("⚡" * 60)
    print("🚀 HOTEL BOOKING SYSTEM - INSTANT LOCAL TESTING")
    print("⚡" * 60)
    print()
    print("💡 BENEFITS:")
    print("✅ INSTANT changes - no deployment delays")
    print("✅ Full debugging capabilities")
    print("✅ Connect to your Koyeb PostgreSQL")
    print("✅ Google Sheets fallback safety")
    print("✅ Test all features locally first")
    print()
    
    # Setup environment
    env_vars = setup_environment()
    
    # Create and run server
    app = create_development_server()
    
    if app:
        print("✅ App ready for local testing")
        run_local_server(app, port=5000)
    else:
        print("❌ Could not start app")
        print("🔧 Troubleshooting:")
        print("1. Make sure you're in the virtual environment")
        print("2. Check that app.py exists and works")
        print("3. Verify all dependencies are installed")
        
        # Show current directory and files
        print(f"\n📁 Current directory: {os.getcwd()}")
        if os.path.exists('app.py'):
            print("✅ app.py found")
        else:
            print("❌ app.py not found")

if __name__ == '__main__':
    main()