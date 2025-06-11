"""
Quick App Test - Test Flask app hoạt động
Kiểm tra các route chính của app
"""
import requests
import threading
import time
import subprocess
import sys
import os

class QuickAppTester:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.app_process = None
        
    def start_app(self):
        """Start Flask app in background"""
        try:
            print("[START] Starting Flask app...")
            
            # Change to app directory
            app_dir = r"C:\Users\T14\Desktop\hotel_flask_app"
            os.chdir(app_dir)
            
            # Start app
            self.app_process = subprocess.Popen(
                [sys.executable, "app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=app_dir
            )
            
            # Wait for app to start
            print("[WAIT] Waiting for app to start...")
            time.sleep(8)  # Give app time to start
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to start app: {e}")
            return False
    
    def stop_app(self):
        """Stop Flask app"""
        if self.app_process:
            try:
                self.app_process.terminate()
                self.app_process.wait(timeout=5)
                print("[STOP] App stopped")
            except:
                self.app_process.kill()
                print("[KILL] App force killed")
    
    def test_route(self, route, expected_status=200):
        """Test a specific route"""
        try:
            url = f"{self.base_url}{route}"
            print(f"[TEST] Testing {url}...")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == expected_status:
                print(f"[OK] {route} - Status: {response.status_code}")
                return True
            else:
                print(f"[FAIL] {route} - Status: {response.status_code} (expected {expected_status})")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"[FAIL] {route} - Connection failed (app not running?)")
            return False
        except Exception as e:
            print(f"[FAIL] {route} - Error: {e}")
            return False
    
    def test_api_route(self, route, method="GET", data=None):
        """Test API route"""
        try:
            url = f"{self.base_url}{route}"
            print(f"[API] Testing {method} {url}...")
            
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            else:
                print(f"[SKIP] Method {method} not supported in test")
                return False
            
            print(f"[API] {route} - Status: {response.status_code}")
            
            # Try to parse JSON response
            try:
                json_data = response.json()
                print(f"[API] Response type: {type(json_data)}")
                if isinstance(json_data, dict) and "success" in json_data:
                    print(f"[API] Success: {json_data.get('success')}")
            except:
                print(f"[API] Response length: {len(response.text)} chars")
            
            return response.status_code < 500  # Accept any non-server-error
            
        except Exception as e:
            print(f"[API] {route} - Error: {e}")
            return False
    
    def run_tests(self):
        """Run comprehensive app tests"""
        print("=" * 60)
        print("[TEST] QUICK APP FUNCTIONALITY TEST")
        print("=" * 60)
        
        # Start app
        if not self.start_app():
            print("[FAIL] Could not start app")
            return False
        
        try:
            # Test main routes
            routes_to_test = [
                "/",  # Dashboard
                "/bookings",  # Bookings list
                "/calendar",  # Calendar view
                "/ai_assistant",  # AI Assistant
                "/voice_translator",  # Voice Translator
                "/templates",  # Templates
                "/reminder_system"  # Reminder System
            ]
            
            print(f"\n[ROUTES] Testing {len(routes_to_test)} main routes...")
            passed_routes = 0
            
            for route in routes_to_test:
                if self.test_route(route):
                    passed_routes += 1
                time.sleep(1)  # Small delay between requests
            
            print(f"[ROUTES] Passed: {passed_routes}/{len(routes_to_test)}")
            
            # Test API routes
            api_routes = [
                ("/api/reminder_status", "GET", None),
                ("/api/templates", "GET", None),
                ("/api/debug_booking/TEST123", "GET", None)  # Non-existent booking for testing
            ]
            
            print(f"\n[API] Testing {len(api_routes)} API routes...")
            passed_apis = 0
            
            for route, method, data in api_routes:
                if self.test_api_route(route, method, data):
                    passed_apis += 1
                time.sleep(1)
            
            print(f"[API] Passed: {passed_apis}/{len(api_routes)}")
            
            # Summary
            total_tests = len(routes_to_test) + len(api_routes)
            total_passed = passed_routes + passed_apis
            
            print("\n" + "=" * 60)
            print(f"[SUMMARY] Total tests: {total_tests}")
            print(f"[SUMMARY] Passed: {total_passed}")
            print(f"[SUMMARY] Success rate: {(total_passed/total_tests)*100:.1f}%")
            
            if total_passed >= total_tests * 0.8:  # 80% success rate
                print("[SUCCESS] App is working well!")
                return True
            else:
                print("[WARNING] Some issues detected")
                return False
                
        finally:
            self.stop_app()

def main():
    """Run quick app test"""
    tester = QuickAppTester()
    
    print("[INFO] Quick App Test - Check if Flask app is working")
    print("[INFO] This will start the app, test routes, then stop it")
    print("[INFO] Make sure no other instance is running on port 8080")
    
    input("\nPress Enter to start test...")
    
    success = tester.run_tests()
    
    if success:
        print("\n[RESULT] ✓ APP TEST PASSED - Ready for deployment!")
    else:
        print("\n[RESULT] ✗ APP TEST ISSUES - Check logs above")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
