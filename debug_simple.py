#!/usr/bin/env python3
"""
Debug Script - Simplified version to check sheet header without Unicode issues
"""

import os
from dotenv import load_dotenv
from gcp_helper import get_gspread_client_safe

def debug_sheet_header_simple():
    """Debug Google Sheets header - simplified version"""
    
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
        print(f"\nHEADER INFO: {len(header)} columns found")
        print("-" * 60)
        
        # Count empty columns
        empty_count = 0
        for i, col in enumerate(header):
            col_clean = str(col).strip()
            if not col_clean:
                empty_count += 1
                print(f"  Position {i+1}: EMPTY")
            else:
                try:
                    # Try to print safely
                    col_safe = col_clean.encode('ascii', 'ignore').decode('ascii')
                    print(f"  Position {i+1}: '{col_safe}' (len={len(col_clean)})")
                except:
                    print(f"  Position {i+1}: [UNICODE_COLUMN] (len={len(col_clean)})")
        
        print(f"\nSUMMARY:")
        print(f"Total columns: {len(header)}")
        print(f"Empty columns: {empty_count}")
        print(f"Used columns: {len(header) - empty_count}")
        
        # Check specific key columns by searching
        key_columns = [
            'So dat phong', 'Ten nguoi dat', 'Check-in Date', 'Check-out Date', 
            'Tong thanh toan', 'Tinh trang', 'Nguoi thu tien'
        ]
        
        print(f"\nKEY COLUMN SEARCH (ASCII safe):")
        for key_col in key_columns:
            found = False
            for i, col in enumerate(header):
                col_ascii = str(col).encode('ascii', 'ignore').decode('ascii').strip()
                if key_col.lower() in col_ascii.lower():
                    print(f"  FOUND: '{key_col}' at position {i+1}")
                    found = True
                    break
            if not found:
                print(f"  MISSING: '{key_col}'")
        
        # Save header to file for detailed analysis
        with open('header_analysis.txt', 'w', encoding='utf-8') as f:
            f.write("Google Sheets Header Analysis\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total columns: {len(header)}\n")
            f.write(f"Empty columns: {empty_count}\n\n")
            f.write("Column Details:\n")
            for i, col in enumerate(header):
                f.write(f"{i+1:2d}: '{col}' (len={len(str(col).strip())})\n")
        
        print(f"\nDETAILS SAVED TO: header_analysis.txt")
        
        return {
            'total_columns': len(header),
            'empty_columns': empty_count,
            'header_saved': True
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_sheet_header_simple()
