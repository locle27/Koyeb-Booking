"""
Quick Auto App Test - Automatic test without input
"""
import requests
import threading
import time
import subprocess
import sys
import os

def test_app_automatically():
    """Run automatic app test"""
    print("=" * 60)
    print("[AUTO-TEST] QUICK APP FUNCTIONALITY TEST")
    print("=" * 60)
    
    app_process = None
    
    try:
        # Start app
        print("[START] Starting Flask app...")
        
        app_dir = r"C:\Users\T14\Desktop\hotel_flask_app"
        os.chdir(app_dir)
        
        app_process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=app_dir
        )
        
        print("[WAIT] Waiting 10 seconds for app to start...")
        time.sleep(10)
        
        # Test basic connectivity
        base_url = "http://localhost:8080"
        
        # Simple tests
        test_routes = [
            "/",
            "/bookings", 
            "/calendar",
            "/api/reminder_status"
        ]
        
        passed = 0
        total = len(test_routes)
        
        for route in test_routes:
            try:
                url = f"{base_url}{route}"
                print(f"[TEST] Testing {url}...")
                
                response = requests.get(url, timeout=8)
                
                if response.status_code < 500:
                    print(f"[OK] {route} - Status: {response.status_code}")
                    passed += 1
                else:
                    print(f"[FAIL] {route} - Status: {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                print(f"[FAIL] {route} - Connection failed")
            except Exception as e:
                print(f"[FAIL] {route} - Error: {e}")
            
            time.sleep(1)
        
        print("\n" + "=" * 60)
        print(f"[SUMMARY] Tests passed: {passed}/{total}")
        print(f"[SUMMARY] Success rate: {(passed/total)*100:.1f}%")
        
        if passed >= total * 0.75:  # 75% success rate
            print("[SUCCESS] ✓ APP IS WORKING!")
            return True
        else:
            print("[WARNING] ✗ Some issues detected")
            return False
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False
        
    finally:
        # Stop app
        if app_process:
            try:
                print("[STOP] Stopping app...")
                app_process.terminate()
                app_process.wait(timeout=5)
                print("[STOP] App stopped")
            except:
                app_process.kill()
                print("[KILL] App force killed")

if __name__ == "__main__":
    success = test_app_automatically()
    print(f"\n[FINAL] Test result: {'PASS' if success else 'FAIL'}")
