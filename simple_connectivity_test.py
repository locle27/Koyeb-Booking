#!/usr/bin/env python3
"""
Simple Connectivity Test
Test basic connections without heavy dependencies
"""

import os
import sys
import time

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

def test_basic_connectivity():
    """Test basic connectivity without complex imports"""
    
    print("🔌 BASIC CONNECTIVITY TEST")
    print("=" * 30)
    print()
    
    # Test 1: Environment
    print("1. Environment Variables:")
    db_url = os.getenv('DATABASE_URL', '')
    sheet_id = os.getenv('DEFAULT_SHEET_ID', '')
    
    if 'postgres' in db_url and 'koyeb' in db_url:
        print_status("PostgreSQL URL configured", "success")
    else:
        print_status("PostgreSQL URL missing", "error")
        return False
    
    if sheet_id:
        print_status("Google Sheets ID configured", "success")
    else:
        print_status("Google Sheets ID missing", "error")
        return False
    
    print()
    
    # Test 2: Network connectivity to PostgreSQL
    print("2. Network Connectivity:")
    try:
        from urllib.parse import urlparse
        import socket
        
        url = urlparse(db_url)
        host = url.hostname
        port = url.port or 5432
        
        print_status(f"Testing connection to {host}:{port}...", "info")
        
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        duration = time.time() - start_time
        
        if result == 0:
            print_status(f"Network connection successful ({duration*1000:.0f}ms)", "success")
        else:
            print_status(f"Network connection failed", "error")
            return False
            
    except Exception as e:
        print_status(f"Network test error: {str(e)}", "error")
        return False
    
    print()
    
    # Test 3: File accessibility
    print("3. File Access:")
    creds_file = os.getenv('GCP_CREDS_FILE_PATH', 'credentials.json')
    
    if os.path.exists(creds_file):
        print_status(f"Credentials file found: {creds_file}", "success")
        
        # Try to read it
        try:
            with open(creds_file, 'r') as f:
                import json
                creds = json.load(f)
                if 'type' in creds and creds['type'] == 'service_account':
                    print_status("Credentials file valid", "success")
                else:
                    print_status("Credentials file invalid format", "error")
                    return False
        except Exception as e:
            print_status(f"Credentials file read error: {str(e)}", "error")
            return False
    else:
        print_status(f"Credentials file not found: {creds_file}", "error")
        return False
    
    print()
    
    # Test 4: Required files
    print("4. Migration Files:")
    required_files = [
        'models.py',
        'database_service.py', 
        'migrate_to_postgresql.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print_status(f"{file} exists", "success")
        else:
            print_status(f"{file} missing", "error")
            return False
    
    print()
    
    # Summary
    print("=" * 30)
    print_status("🎉 BASIC CONNECTIVITY: ALL GOOD!", "success")
    print()
    print("✅ Network can reach PostgreSQL database")
    print("✅ Credentials file is valid") 
    print("✅ Migration files are present")
    print("✅ Environment variables configured")
    print()
    print("🔗 Next step: Install dependencies and run full test")
    print("   Option 1: Use your virtual environment")
    print("   Option 2: Install globally: pip install pandas flask gspread psycopg2-binary")
    
    return True

def test_with_venv():
    """Test if we can use the existing virtual environment"""
    
    print("\n🐍 VIRTUAL ENVIRONMENT TEST")
    print("=" * 30)
    
    venv_path = os.path.join('.', 'venv')
    if os.path.exists(venv_path):
        print_status("Virtual environment found", "success")
        
        # Check for key packages in venv
        site_packages = None
        for root, dirs, files in os.walk(venv_path):
            if 'site-packages' in root:
                site_packages = root
                break
        
        if site_packages:
            print_status(f"Site-packages: {site_packages}", "info")
            
            # Check for key packages
            packages = ['flask', 'pandas', 'psycopg2', 'sqlalchemy']
            found_packages = []
            
            for package in packages:
                package_dirs = [d for d in os.listdir(site_packages) if package in d.lower()]
                if package_dirs:
                    found_packages.append(package)
                    print_status(f"{package} found in venv", "success")
                else:
                    print_status(f"{package} not found in venv", "warning")
            
            if len(found_packages) >= 2:
                print_status(f"Virtual environment has {len(found_packages)}/4 key packages", "success")
                print()
                print("💡 To use virtual environment:")
                print("   Windows: .\\venv\\Scripts\\activate")
                print("   Linux/Mac: source venv/bin/activate")
                print("   Then run: python comprehensive_test.py")
                return True
            else:
                print_status("Virtual environment missing key packages", "warning")
        
    else:
        print_status("No virtual environment found", "info")
        print("💡 Install dependencies globally:")
        print("   pip install pandas flask gspread psycopg2-binary SQLAlchemy Flask-SQLAlchemy")
    
    return False

if __name__ == '__main__':
    # Load environment
    try:
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip('"').strip("'")
                        os.environ[key] = value
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")
    
    success = test_basic_connectivity()
    
    if success:
        test_with_venv()
    
    sys.exit(0 if success else 1)