#!/usr/bin/env python3
# Emergency script to restore Google Sheet header if corrupted
import os
import sys

def restore_google_sheet_header():
    """
    Emergency script to restore correct header to Google Sheet
    if it was overwritten by booking data
    """
    print("=== EMERGENCY GOOGLE SHEET HEADER RESTORATION ===")
    
    try:
        # Import required modules
        from gcp_helper import get_gspread_client_safe
        
        # Configuration
        SHEET_ID = "13kQETOUGCVUwUqZrxeLy-WAj3b17SugI4L8Oq09SX2w"
        WORKSHEET_NAME = "BookingManager"
        GCP_CREDS_FILE = "gcp_credentials.json"
        
        # Correct header that should be in row 1
        CORRECT_HEADER = [
            'Số đặt phòng', 'Tên người đặt', 'Tên chỗ nghỉ', 'Check-in Date', 'Check-out Date',
            'Stay Duration', 'Tình trạng', 'Tổng thanh toán', 'Giá mỗi đêm', 'Booking Date',
            'Ngày đến', 'Ngày đi', 'Vị trí', 'Thành viên Genius', 'Được đặt vào',
            'Hoa hồng', 'Tiền tệ', 'Người nhận tiền', 'Ghi chú thanh toán', 'Người thu tiền', 'Taxi'
        ]
        
        print("Step 1: Connecting to Google Sheets...")
        gc = get_gspread_client_safe(GCP_CREDS_FILE)
        sh = gc.open_by_key(SHEET_ID)
        worksheet = sh.worksheet(WORKSHEET_NAME)
        print("OK: Connected successfully")
        
        print("Step 2: Checking current header...")
        current_row_1 = worksheet.row_values(1)
        try:
            print(f"Current row 1: {current_row_1[:5]}...")  # First 5 values
        except UnicodeEncodeError:
            print(f"Current row 1 (count): {len(current_row_1)} columns")
        
        # Check if header is corrupted (contains booking data instead of column names)
        corrupted_indicators = ['6481690399', 'One-Bedroom Apartment']
        is_corrupted = any(indicator in str(current_row_1) for indicator in corrupted_indicators)
        
        if is_corrupted:
            print("DETECTED: Header is corrupted with booking data!")
            print("Step 3: Restoring correct header...")
            
            # Insert new row at top and shift everything down
            worksheet.insert_row(CORRECT_HEADER, index=1, value_input_option='USER_ENTERED')
            print("OK: Inserted correct header at row 1")
            
            print("Step 4: Verifying restoration...")
            new_row_1 = worksheet.row_values(1)
            if len(new_row_1) >= len(CORRECT_HEADER):
                print("SUCCESS: Header restored correctly!")
                try:
                    print(f"New header (first 3): {new_row_1[:3]}")
                except UnicodeEncodeError:
                    print(f"New header count: {len(new_row_1)} columns")
                return True
            else:
                print(f"ERROR: Header restoration failed. Got {len(new_row_1)} columns")
                return False
        else:
            print("OK: Header appears to be correct already")
            expected_columns = ['So dat phong', 'Ten nguoi dat', 'Check-in Date']
            has_expected = any(any(expected in str(col) for expected in expected_columns) for col in current_row_1)
            
            if has_expected:
                print("VERIFIED: Header contains expected columns")
                return True
            else:
                print("WARNING: Header may still need fixing")
                print("Step 3: Replacing header with correct version...")
                worksheet.update([CORRECT_HEADER], 'A1', value_input_option='USER_ENTERED')
                print("OK: Updated header row")
                return True
    
    except Exception as e:
        print(f"ERROR: Failed to restore header: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = restore_google_sheet_header()
    print(f"\nRestoration result: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
