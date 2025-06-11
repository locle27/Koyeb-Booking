#!/usr/bin/env python3
"""
Debug Script - Kiểm tra Header Structure của Google Sheets
Mục tiêu: Hiểu chính xác structure của sheet để fix column mapping
"""

import os
from dotenv import load_dotenv
from gcp_helper import get_gspread_client_safe

def debug_sheet_header():
    """Debug Google Sheets header để hiểu structure chính xác"""
    
    # Load environment variables
    load_dotenv()
    GCP_CREDS_FILE_PATH = os.getenv("GCP_CREDS_FILE_PATH")
    DEFAULT_SHEET_ID = os.getenv("DEFAULT_SHEET_ID") 
    WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")
    
    print("DEBUG: GOOGLE SHEETS HEADER STRUCTURE")
    print("=" * 60)
    
    try:
        # Connect to Google Sheets
        gc = get_gspread_client_safe(GCP_CREDS_FILE_PATH)
        spreadsheet = gc.open_by_key(DEFAULT_SHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        print(f"Connected to worksheet: {worksheet.title}")
        print(f"Total rows: {worksheet.row_count}")
        print(f"Total cols: {worksheet.col_count}")
        
        # Get header row
        header = worksheet.row_values(1)
        print(f"\nRAW HEADER ({len(header)} columns):")
        print("-" * 60)
        
        # Analyze each column in detail
        for i, col in enumerate(header):
            col_clean = str(col).strip()
            print(f"  {i+1:2d}: '{col}' (len={len(col)}) -> Clean: '{col_clean}'")
            
            # Check for potential issues
            if not col_clean:
                print(f"      WARNING: EMPTY COLUMN detected at position {i+1}")
            elif col_clean != col:
                print(f"      FIX: Needs cleaning: '{col}' -> '{col_clean}'")
        
        # Check for missing key columns
        print(f"\nKEY COLUMN CHECK:")
        print("-" * 40)
        key_columns = [
            'Số đặt phòng', 'Tên người đặt', 'Check-in Date', 'Check-out Date', 
            'Tổng thanh toán', 'Tình trạng', 'Người thu tiền'
        ]
        
        missing_columns = []
        for key_col in key_columns:
            if key_col in header:
                print(f"  OK: '{key_col}' - FOUND")
            else:
                print(f"  MISSING: '{key_col}' - NOT FOUND")
                missing_columns.append(key_col)
        
        if missing_columns:
            print(f"\nMISSING KEY COLUMNS: {missing_columns}")
        
        # Get sample data from last 3 rows to understand data structure
        print(f"\nSAMPLE DATA (Last 3 rows):")
        print("-" * 60)
        
        try:
            all_data = worksheet.get_all_values()
            if len(all_data) > 1:
                sample_rows = all_data[-3:] if len(all_data) > 3 else all_data[1:]
                
                for row_idx, row in enumerate(sample_rows, start=len(all_data)-len(sample_rows)+1):
                    print(f"\nRow {row_idx}: {len(row)} cells")
                    for col_idx, cell_value in enumerate(row[:min(len(header), 10)]):  # First 10 columns
                        col_name = header[col_idx] if col_idx < len(header) else f"Col_{col_idx}"
                        print(f"  {col_name}: '{cell_value}'")
                    if len(row) > 10:
                        print(f"  ... (+{len(row)-10} more columns)")
        except Exception as e:
            print(f"  ERROR: Error getting sample data: {e}")
        
        # Summary and recommendations
        print(f"\nSUMMARY & RECOMMENDATIONS:")
        print("=" * 60)
        print(f"Total columns found: {len(header)}")
        print(f"Empty columns: {sum(1 for col in header if not str(col).strip())}")
        print(f"Key columns missing: {len(missing_columns)}")
        
        if missing_columns:
            print(f"\nACTION NEEDED:")
            print(f"   Add these columns to Google Sheets: {missing_columns}")
            
        print(f"\nNEXT STEPS:")
        print(f"   1. Fix any missing key columns in Google Sheets")
        print(f"   2. Update logic.py column mapping to match exact header")
        print(f"   3. Test with a sample booking")
        
        return {
            'header': header,
            'missing_columns': missing_columns,
            'total_columns': len(header),
            'empty_columns': sum(1 for col in header if not str(col).strip())
        }
        
    except Exception as e:
        print(f"ERROR: Error debugging sheet header: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_sheet_header()
