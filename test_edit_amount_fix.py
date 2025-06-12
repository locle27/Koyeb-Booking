#!/usr/bin/env python3
"""
Test script for the edit amount functionality fix
"""

import requests
import json

def test_edit_amount_api():
    """Test the new /api/update_guest_amounts endpoint"""
    
    # Test data
    test_data = {
        "booking_id": "TEST123",  # Use a test booking ID
        "room_amount": 500000,
        "taxi_amount": 50000,
        "edit_note": "Test update from fix verification"
    }
    
    # Local test URL (adjust if needed)
    url = "http://localhost:8080/api/update_guest_amounts"
    
    try:
        print("🧪 Testing new edit amount API endpoint...")
        print(f"URL: {url}")
        print(f"Data: {test_data}")
        
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ API endpoint working correctly!")
                return True
            else:
                print(f"❌ API returned error: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Cannot connect to server. Make sure the Flask app is running.")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def print_fix_summary():
    """Print summary of the fixes applied"""
    print("\n" + "="*60)
    print("🔧 EDIT AMOUNT BUG FIX SUMMARY")
    print("="*60)
    print()
    print("🐛 PROBLEM IDENTIFIED:")
    print("   - Edit amount functionality was using wrong API endpoint")
    print("   - '/booking/{id}/edit' expects full booking data")
    print("   - Sending only partial data caused corruption (None values)")
    print("   - Data from previous guest was getting affected")
    print()
    print("✅ FIXES APPLIED:")
    print("   1. Created new API endpoint: /api/update_guest_amounts")
    print("   2. Updated frontend JavaScript to use correct endpoint") 
    print("   3. Enhanced error handling and logging in update function")
    print("   4. Added data verification after updates")
    print()
    print("📝 FILES MODIFIED:")
    print("   - app.py: Added new API endpoint")
    print("   - templates/dashboard.html: Updated JavaScript function")
    print("   - logic.py: Enhanced update_row_in_gsheet function")
    print()
    print("🎯 RESULT:")
    print("   - Edit amount now only updates specified fields")
    print("   - No more data corruption in other bookings")
    print("   - Better error tracking and debugging")
    print("="*60)

if __name__ == "__main__":
    print_fix_summary()
    print("\n🧪 Running API test...")
    test_edit_amount_api()
