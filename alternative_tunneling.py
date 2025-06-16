#!/usr/bin/env python3
"""
Alternative Tunneling Solutions
If ngrok requires account setup, use these alternatives
"""

import subprocess
import sys
import time

def try_serveo():
    """Try Serveo - no account needed"""
    print("🔗 Trying Serveo (no account needed)...")
    try:
        print("📍 Starting Serveo tunnel...")
        print("🌐 This will give you a public URL like: https://yourname.serveo.net")
        print()
        
        # Start serveo tunnel
        cmd = ['ssh', '-R', '80:localhost:5000', 'serveo.net']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("✅ Serveo tunnel started!")
        print("🔗 Check the output above for your public URL")
        print("⏹️ Press Ctrl+C to stop")
        
        # Keep the process running
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n⏹️ Serveo tunnel stopped")
            process.terminate()
            
    except FileNotFoundError:
        print("❌ SSH not available")
        return False
    except Exception as e:
        print(f"❌ Serveo failed: {e}")
        return False
    
    return True

def try_localhost_run():
    """Use localhost.run - no account needed"""
    print("🔗 Trying localhost.run (no account needed)...")
    try:
        print("📍 Starting localhost.run tunnel...")
        print("🌐 This will give you a public URL")
        print()
        
        # Start localhost.run tunnel
        cmd = ['ssh', '-R', '80:localhost:5000', 'ssh.localhost.run']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("✅ localhost.run tunnel started!")
        print("🔗 Check the output above for your public URL")
        print("⏹️ Press Ctrl+C to stop")
        
        # Keep the process running
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n⏹️ localhost.run tunnel stopped")
            process.terminate()
            
    except FileNotFoundError:
        print("❌ SSH not available")
        return False
    except Exception as e:
        print(f"❌ localhost.run failed: {e}")
        return False
    
    return True

def show_alternatives():
    """Show all alternative options"""
    print("🌐 PUBLIC ACCESS ALTERNATIVES")
    print("=" * 40)
    print()
    
    print("🎯 RECOMMENDED: Just test locally for now")
    print("📍 Local URL: http://localhost:5000")
    print("✅ Instant changes, full debugging")
    print("✅ Same as public testing but faster")
    print()
    
    print("🔗 FOR PUBLIC ACCESS (if needed):")
    print()
    print("Option 1: ngrok (most reliable)")
    print("  1. Sign up: https://dashboard.ngrok.com/signup")
    print("  2. Get token: https://dashboard.ngrok.com/get-started/your-authtoken")
    print("  3. Run: ngrok config add-authtoken YOUR_TOKEN")
    print("  4. Run: ngrok http 5000")
    print()
    
    print("Option 2: VS Code Port Forwarding")
    print("  1. Open project in VS Code")
    print("  2. Run your local server")
    print("  3. Ports tab → Forward port 5000")
    print("  4. Get public URL automatically")
    print()
    
    print("Option 3: GitHub Codespaces")
    print("  1. Open repository in GitHub")
    print("  2. Code → Create codespace")
    print("  3. Run your app in browser")
    print("  4. Automatic public URL")
    print()
    
    print("Option 4: Replit")
    print("  1. Import GitHub repo to Replit")
    print("  2. Run button → instant public URL")
    print("  3. Real-time collaboration")
    print()

def main():
    """Main function"""
    print("🔧 TUNNELING ALTERNATIVES")
    print("=" * 30)
    print()
    
    print("💡 You have several options:")
    print()
    
    choice = input("What would you like to do?\n1. Test locally only (recommended)\n2. Try alternative tunneling\n3. Show all options\nChoice (1-3): ").strip()
    
    if choice == "1":
        print()
        print("🎯 PERFECT CHOICE!")
        print("✅ Local testing is often better for development")
        print("📍 Run: START_LOCAL_TESTING.bat")
        print("🌐 Open: http://localhost:5000")
        print("⚡ Instant changes, no delays!")
        
    elif choice == "2":
        print()
        print("🔗 Trying alternative tunneling methods...")
        print()
        
        # Try serveo first
        if not try_serveo():
            # Try localhost.run
            if not try_localhost_run():
                print("❌ Alternative tunneling methods not available")
                print("💡 Recommend using local testing or ngrok with account")
    
    else:
        show_alternatives()

if __name__ == '__main__':
    main()