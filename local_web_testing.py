#!/usr/bin/env python3
"""
Local Web Testing with Public URL
Run your app locally but make it accessible from anywhere on the web
INSTANT changes, no deployment delays!
"""

import os
import sys
import subprocess
import threading
import time

def setup_environment():
    """Set environment variables for local testing"""
    env_vars = {
        'DATABASE_URL': 'postgres://koyeb-adm:npg_T4hEuUQeDl7A@ep-little-haze-a2133rvc.eu-central-1.pg.koyeb.app:5432/koyebdb',
        'DEFAULT_SHEET_ID': '13kQETOUGCVUwUqZrxeLy-WAj3b17SugI4L8Oq09SX2w',
        'GCP_CREDS_FILE_PATH': 'credentials.json',
        'GOOGLE_API_KEY': 'AIzaSyA-0V4VgrJbnzQWueDVI9pSOoH_V2EMUg4',
        'USE_POSTGRESQL': 'false',
        'USE_HYBRID_MODE': 'true',
        'FALLBACK_TO_SHEETS': 'true',
        'FLASK_ENV': 'development',
        'FLASK_DEBUG': 'true',
        'PORT': '5000'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Environment variables set for local testing")

def install_ngrok():
    """Install ngrok for public URL tunneling"""
    print("🔗 Setting up ngrok for public URL...")
    print("📥 Download ngrok from: https://ngrok.com/download")
    print("   Or install via:")
    print("   • Windows: choco install ngrok")
    print("   • Mac: brew install ngrok")
    print("   • Linux: snap install ngrok")
    print()
    
    # Check if ngrok is available
    try:
        result = subprocess.run(['ngrok', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok is already installed!")
            return True
        else:
            print("❌ ngrok not found")
            return False
    except FileNotFoundError:
        print("❌ ngrok not found")
        return False

def run_flask_app():
    """Run Flask app locally"""
    print("🚀 Starting Flask development server...")
    print("📍 Local URL: http://localhost:5000")
    print("🔄 Auto-reload enabled - changes appear instantly!")
    print()
    
    try:
        # Run Flask app
        subprocess.run([sys.executable, 'app.py'], env=os.environ)
    except KeyboardInterrupt:
        print("\n⏹️ Flask server stopped")

def start_ngrok_tunnel():
    """Start ngrok tunnel in background"""
    try:
        print("🌐 Starting ngrok tunnel...")
        process = subprocess.Popen(['ngrok', 'http', '5000'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait a moment for ngrok to start
        time.sleep(3)
        
        # Get the public URL
        try:
            import requests
            response = requests.get('http://127.0.0.1:4040/api/tunnels')
            data = response.json()
            
            if data['tunnels']:
                public_url = data['tunnels'][0]['public_url']
                print(f"🌍 PUBLIC URL: {public_url}")
                print(f"🔗 Share this URL for real-time testing!")
                print(f"📱 Test on any device, anywhere in the world")
                return public_url
            else:
                print("❌ No tunnels found")
                return None
        except:
            print("⚠️ Could not get ngrok URL automatically")
            print("🔗 Check ngrok dashboard: http://127.0.0.1:4040")
            return None
            
    except Exception as e:
        print(f"❌ ngrok tunnel failed: {e}")
        return None

def main():
    """Main function for local web testing"""
    print("⚡" * 60)
    print("🚀 LOCAL WEB TESTING WITH PUBLIC ACCESS")
    print("⚡" * 60)
    print()
    print("💡 BENEFITS:")
    print("✅ INSTANT changes - no deployment wait")
    print("✅ Real-time debugging")
    print("✅ Public URL for testing from anywhere")
    print("✅ Keep your Koyeb PostgreSQL database")
    print("✅ Live reload on file changes")
    print()
    
    # Setup environment
    setup_environment()
    
    # Check for ngrok
    has_ngrok = install_ngrok()
    
    if has_ngrok:
        print("🎯 RECOMMENDED SETUP:")
        print("1. Run this script to start Flask app")
        print("2. In another terminal: ngrok http 5000")
        print("3. Get public URL for instant web testing")
        print()
        
        choice = input("Start Flask app now? (y/N): ").lower()
        if choice in ['y', 'yes']:
            # Start ngrok in background
            tunnel_thread = threading.Thread(target=start_ngrok_tunnel)
            tunnel_thread.daemon = True
            tunnel_thread.start()
            
            time.sleep(2)
            
            # Start Flask app
            run_flask_app()
    else:
        print("🎯 ALTERNATIVE SETUP:")
        print("1. Install ngrok first")
        print("2. Run: python local_web_testing.py")
        print("3. Get instant public URL")
        print()
        
        choice = input("Start Flask app without ngrok? (y/N): ").lower()
        if choice in ['y', 'yes']:
            print("📍 Local testing only: http://localhost:5000")
            run_flask_app()

if __name__ == '__main__':
    main()