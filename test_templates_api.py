#!/usr/bin/env python3
"""
Test script để debug Templates API
"""

import requests
import json
from pathlib import Path

# Test API endpoints
BASE_URL = "http://localhost:8080"  # Change to your actual URL

def test_templates_api():
    """Test /api/templates endpoint"""
    print("=" * 60)
    print("🧪 Testing Templates API")
    print("=" * 60)
    
    try:
        # Test 1: Check if templates file exists locally
        print("\n1️⃣ Checking local templates file...")
        templates_file = Path("message_templates.json")
        
        if templates_file.exists():
            print(f"✅ File exists: {templates_file}")
            with open(templates_file, 'r', encoding='utf-8') as f:
                local_data = json.load(f)
            print(f"📊 Local templates count: {len(local_data)}")
            print(f"📋 Sample template: {local_data[0] if local_data else 'None'}")
        else:
            print("❌ Templates file not found locally")
            return
        
        # Test 2: Test API endpoint
        print("\n2️⃣ Testing API endpoint...")
        try:
            response = requests.get(f"{BASE_URL}/api/templates", timeout=10)
            print(f"📡 Response status: {response.status_code}")
            print(f"📋 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    api_data = response.json()
                    print(f"✅ API response successful")
                    print(f"📊 API data type: {type(api_data)}")
                    print(f"📊 API data count: {len(api_data) if isinstance(api_data, list) else 'Not a list'}")
                    
                    if isinstance(api_data, list) and len(api_data) > 0:
                        print(f"📋 Sample API template: {api_data[0]}")
                    elif isinstance(api_data, dict):
                        print(f"📋 API response dict: {api_data}")
                    else:
                        print("⚠️ API returned unexpected format")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    print(f"📄 Raw response: {response.text[:500]}...")
            else:
                print(f"❌ API request failed: {response.status_code}")
                print(f"📄 Error response: {response.text}")
                
        except requests.RequestException as e:
            print(f"❌ Request error: {e}")
            print("💡 Make sure your Flask app is running!")
        
        # Test 3: Test debug endpoint
        print("\n3️⃣ Testing debug endpoint...")
        try:
            response = requests.get(f"{BASE_URL}/api/templates/debug", timeout=10)
            if response.status_code == 200:
                debug_data = response.json()
                print(f"🔍 Debug info: {json.dumps(debug_data, indent=2)}")
            else:
                print(f"❌ Debug endpoint failed: {response.status_code}")
        except requests.RequestException as e:
            print(f"❌ Debug request error: {e}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_import_route():
    """Test import route"""
    print("\n4️⃣ Testing import route...")
    try:
        response = requests.get(f"{BASE_URL}/templates/import", timeout=15)
        print(f"📡 Import response status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Import successful")
        else:
            print(f"❌ Import failed: {response.text}")
    except requests.RequestException as e:
        print(f"❌ Import request error: {e}")

def generate_test_html():
    """Generate test HTML page"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Templates API Test</title>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h2>Templates API Test</h2>
        <div class="row">
            <div class="col-md-6">
                <button class="btn btn-primary" onclick="testAPI()">Test API</button>
                <button class="btn btn-success" onclick="testImport()">Test Import</button>
                <button class="btn btn-info" onclick="testDebug()">Test Debug</button>
            </div>
        </div>
        <div id="results" class="mt-4"></div>
    </div>

    <script>
        async function testAPI() {
            const results = document.getElementById('results');
            results.innerHTML = '<div class="alert alert-info">Testing API...</div>';
            
            try {
                const response = await fetch('/api/templates');
                const data = await response.json();
                
                results.innerHTML = `
                    <div class="alert alert-success">
                        <h5>API Test Result</h5>
                        <p><strong>Status:</strong> ${response.status}</p>
                        <p><strong>Data Type:</strong> ${typeof data}</p>
                        <p><strong>Count:</strong> ${Array.isArray(data) ? data.length : 'Not an array'}</p>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    </div>
                `;
            } catch (error) {
                results.innerHTML = `
                    <div class="alert alert-danger">
                        <h5>API Test Error</h5>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }

        async function testImport() {
            const results = document.getElementById('results');
            results.innerHTML = '<div class="alert alert-info">Testing Import...</div>';
            
            try {
                const response = await fetch('/templates/import');
                results.innerHTML = `
                    <div class="alert alert-success">
                        <h5>Import Test Result</h5>
                        <p><strong>Status:</strong> ${response.status}</p>
                        <p><strong>Redirected:</strong> ${response.redirected}</p>
                        <p><strong>URL:</strong> ${response.url}</p>
                    </div>
                `;
            } catch (error) {
                results.innerHTML = `
                    <div class="alert alert-danger">
                        <h5>Import Test Error</h5>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }

        async function testDebug() {
            const results = document.getElementById('results');
            results.innerHTML = '<div class="alert alert-info">Testing Debug...</div>';
            
            try {
                const response = await fetch('/api/templates/debug');
                const data = await response.json();
                
                results.innerHTML = `
                    <div class="alert alert-info">
                        <h5>Debug Test Result</h5>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    </div>
                `;
            } catch (error) {
                results.innerHTML = `
                    <div class="alert alert-danger">
                        <h5>Debug Test Error</h5>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
    </script>
</body>
</html>
"""
    
    with open("templates_test.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("📄 Generated templates_test.html for browser testing")

if __name__ == "__main__":
    test_templates_api()
    test_import_route()
    generate_test_html()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("💡 Open templates_test.html in your browser to test frontend")
    print("=" * 60)
