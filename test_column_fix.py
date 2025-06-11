#!/usr/bin/env python3
"""
Test Script để validate toàn bộ booking save flow
Kiểm tra xem fix có hoạt động không
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic import append_multiple_bookings_to_sheet

def test_booking_save():
    """Test save booking với dữ liệu mẫu"""
    
    load_dotenv()
    GCP_CREDS_FILE_PATH = os.getenv("GCP_CREDS_FILE_PATH")
    DEFAULT_SHEET_ID = os.getenv("DEFAULT_SHEET_ID") 
    WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")
    
    print("TESTING BOOKING SAVE FLOW")
    print("=" * 50)
    
    # Tạo dữ liệu test booking với exact column mapping
    test_booking = {
        'Số đặt phòng': f'TEST_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'Tên người đặt': 'Test User - Column Fix',
        'Tên chỗ nghỉ': 'Test Room Type',
        'Check-in Date': '2025-06-20',
        'Check-out Date': '2025-06-22',
        'Stay Duration': '2',
        'Tình trạng': 'OK',
        'Tổng thanh toán': 300000,
        'Giá mỗi đêm': 150000,
        'Booking Date': datetime.now().strftime('%Y-%m-%d'),
        'Ngày đến': 'ngày 20 tháng 6 năm 2025',
        'Ngày đi': 'ngày 22 tháng 6 năm 2025',
        'Vị trí': 'Test Location',
        'Thành viên Genius': 'Không',
        'Được đặt vào': datetime.now().strftime('%d tháng %m, %Y'),
        'Hoa hồng': 30000,
        'Tiền tệ': 'VND',
        'Người nhận tiền': '',
        'Ghi chú thanh toán': f'TEST BOOKING - Column Fix Test {datetime.now().strftime("%H:%M")}',
        'Người thu tiền': '',
        'Taxi': ''
    }
    
    bookings_to_test = [test_booking]
    
    print(f"📝 Test booking created:")
    print(f"   ID: {test_booking['Số đặt phòng']}")
    print(f"   Guest: {test_booking['Tên người đặt']}")
    print(f"   Check-in: {test_booking['Check-in Date']}")
    print(f"   Total fields: {len(test_booking)}")
    
    try:
        print(f"\n🔄 Attempting to save to Google Sheets...")
        
        append_multiple_bookings_to_sheet(
            bookings=bookings_to_test,
            gcp_creds_file_path=GCP_CREDS_FILE_PATH,
            sheet_id=DEFAULT_SHEET_ID,
            worksheet_name=WORKSHEET_NAME
        )
        
        print(f"✅ SUCCESS: Test booking saved!")
        print(f"📋 Check Google Sheets for booking ID: {test_booking['Số đặt phòng']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_booking_in_sheet():
    """Verify rằng test booking có trong sheet"""
    
    try:
        from logic import import_from_gsheet
        
        load_dotenv()
        GCP_CREDS_FILE_PATH = os.getenv("GCP_CREDS_FILE_PATH")
        DEFAULT_SHEET_ID = os.getenv("DEFAULT_SHEET_ID") 
        WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")
        
        print(f"\n🔍 Verifying booking in sheet...")
        
        df = import_from_gsheet(DEFAULT_SHEET_ID, GCP_CREDS_FILE_PATH, WORKSHEET_NAME)
        
        if df.empty:
            print(f"❌ Sheet is empty or couldn't load")
            return False
        
        print(f"📊 Sheet loaded: {len(df)} total bookings")
        
        # Look for test bookings
        test_bookings = df[df['Ghi chú thanh toán'].str.contains('TEST BOOKING', na=False)]
        
        if not test_bookings.empty:
            print(f"✅ Found {len(test_bookings)} test booking(s):")
            for _, booking in test_bookings.iterrows():
                print(f"   - ID: {booking.get('Số đặt phòng', 'N/A')}")
                print(f"   - Guest: {booking.get('Tên người đặt', 'N/A')}")
                print(f"   - Note: {booking.get('Ghi chú thanh toán', 'N/A')}")
            return True
        else:
            print(f"⚠️ No test bookings found")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    print("Column Fix Validation Test")
    print("=" * 50)
    
    # Test 1: Save booking
    save_success = test_booking_save()
    
    if save_success:
        # Test 2: Verify booking appears in sheet
        import time
        print(f"\n⏳ Waiting 3 seconds for Google Sheets sync...")
        time.sleep(3)
        
        verify_success = verify_booking_in_sheet()
        
        if verify_success:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"✅ Column mapping fix is working correctly")
            print(f"📋 Check your Google Sheets to see the new test booking")
        else:
            print(f"\n⚠️ Save succeeded but verification failed")
            print(f"   Check Google Sheets manually for the test booking")
    else:
        print(f"\n❌ TESTS FAILED")
        print(f"   Column mapping fix needs more work")
    
    print(f"\n" + "=" * 50)
