#!/usr/bin/env python3
"""
Simple test script without emoji to validate column fix
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic import append_multiple_bookings_to_sheet

def test_simple():
    """Simple test for column fix"""
    
    load_dotenv()
    GCP_CREDS_FILE_PATH = os.getenv("GCP_CREDS_FILE_PATH")
    DEFAULT_SHEET_ID = os.getenv("DEFAULT_SHEET_ID") 
    WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")
    
    print("Testing Column Fix")
    print("=" * 30)
    
    # Create test booking
    test_booking = {
        'Số đặt phòng': f'TEST_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'Tên người đặt': 'Test User - Column Fix',
        'Tên chỗ nghỉ': 'Test Room',
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
        'Ghi chú thanh toán': f'COLUMN FIX TEST {datetime.now().strftime("%H:%M")}',
        'Người thu tiền': '',
        'Taxi': ''
    }
    
    print(f"Test booking ID: {test_booking['Số đặt phòng']}")
    print(f"Guest name: {test_booking['Tên người đặt']}")
    print(f"Total fields: {len(test_booking)}")
    
    try:
        print("\nSaving to Google Sheets...")
        
        append_multiple_bookings_to_sheet(
            bookings=[test_booking],
            gcp_creds_file_path=GCP_CREDS_FILE_PATH,
            sheet_id=DEFAULT_SHEET_ID,
            worksheet_name=WORKSHEET_NAME
        )
        
        print("SUCCESS: Test booking saved!")
        print(f"Check Google Sheets for: {test_booking['Số đặt phòng']}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple()
    if success:
        print("\nColumn fix validation PASSED!")
    else:
        print("\nColumn fix validation FAILED!")
