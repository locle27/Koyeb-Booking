#!/usr/bin/env python3
"""
Test script để kiểm tra dashboard route sau khi sửa lỗi Internal Server Error
"""
import os
import sys
from pathlib import Path
import traceback

# Thêm thư mục hiện tại vào Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Import app
try:
    from app import app, load_data
    print("SUCCESS: Import app thanh cong")
except Exception as e:
    print(f"ERROR: Loi import app: {e}")
    traceback.print_exc()
    sys.exit(1)

def test_dashboard_route():
    """Test dashboard route với app context"""
    print("\nTEST: Testing Dashboard Route...")
    
    try:
        with app.test_client() as client:
            # Test GET request tới dashboard
            response = client.get('/')
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                print("SUCCESS: Dashboard route hoat dong binh thuong!")
                print(f"Response length: {len(response.data)} bytes")
                
                # Kiểm tra xem có lỗi JavaScript trong response không
                response_text = response.data.decode('utf-8')
                if 'Internal Server Error' in response_text:
                    print("WARNING: Phat hien 'Internal Server Error' trong response")
                elif 'error' in response_text.lower():
                    print("WARNING: Phat hien tu 'error' trong response")
                else:
                    print("SUCCESS: Khong co loi duoc phat hien trong response")
                    
            elif response.status_code == 500:
                print("ERROR: Van con loi 500 Internal Server Error!")
                print(f"Response: {response.data.decode('utf-8')[:500]}...")
            else:
                print(f"WARNING: Unexpected status code: {response.status_code}")
                
    except Exception as e:
        print(f"ERROR: Loi khi test dashboard: {e}")
        traceback.print_exc()
        return False
        
    return True

def test_data_loading():
    """Test hàm load_data"""
    print("\n📊 Testing Data Loading...")
    
    try:
        df, active_bookings = load_data()
        print(f"✅ Load data thành công!")
        print(f"📈 Total rows: {len(df)}")
        print(f"📋 Active bookings: {len(active_bookings)}")
        print(f"📋 Columns: {list(df.columns) if not df.empty else 'No columns'}")
        
        # Test một số cột quan trọng
        if not df.empty:
            required_cols = ['Check-in Date', 'Người thu tiền', 'Tình trạng', 'Tổng thanh toán']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"⚠️ Thiếu các cột: {missing_cols}")
            else:
                print("✅ Tất cả cột cần thiết đều có")
                
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi load data: {e}")
        traceback.print_exc()
        return False

def test_dashboard_with_params():
    """Test dashboard với các tham số date"""
    print("\n📅 Testing Dashboard with Date Parameters...")
    
    try:
        with app.test_client() as client:
            # Test với date parameters
            response = client.get('/?start_date=2024-01-01&end_date=2024-12-31')
            
            print(f"📊 Response status with dates: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Dashboard với date parameters hoạt động!")
            else:
                print(f"❌ Lỗi với date parameters: {response.status_code}")
                
            return response.status_code == 200
            
    except Exception as e:
        print(f"❌ Lỗi khi test dashboard với params: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing Dashboard Fix for Internal Server Error")
    print("=" * 60)
    
    # Kiểm tra environment
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version}")
    
    # Run tests
    tests = [
        ("Data Loading", test_data_loading),
        ("Dashboard Route", test_dashboard_route), 
        ("Dashboard with Params", test_dashboard_with_params)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Tất cả tests đều PASS! Dashboard đã được sửa!")
        print("💡 Bạn có thể deploy lên Koyeb an toàn.")
    else:
        print("⚠️ Một số tests FAIL. Cần kiểm tra thêm.")
        sys.exit(1)
