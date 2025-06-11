import pandas as pd
import numpy as np
import datetime
import re
import csv
from typing import Dict, List, Optional, Tuple, Any
import json
import calendar
from io import BytesIO

# Import các thư viện có thể không có sẵn
try:
    import gspread
except ImportError:
    gspread = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import plotly.express as px
    import plotly.io as p_json
    import plotly
except ImportError:
    px = None
    p_json = None
    plotly = None

try:
    from gcp_helper import get_gspread_client_safe
except ImportError:
    def get_gspread_client_safe(gcp_creds_file_path):
        raise ImportError("gcp_helper module not available")

# ==============================================================================
# GOOGLE SHEETS HELPER
# ==============================================================================

def _get_gspread_client(gcp_creds_file_path: str):
    if gspread is None:
        raise ImportError("gspread library not installed. Please install it with: pip install gspread")
    
    try:
        return get_gspread_client_safe(gcp_creds_file_path)
    except Exception as e:
        print(f"ERROR: Authentication failed with credentials file '{gcp_creds_file_path}': {e}")
        raise

def import_from_gsheet(sheet_id: str, gcp_creds_file_path: str, worksheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Hàm này sẽ đọc dữ liệu từ Google Sheet và thực hiện việc chuyển đổi kiểu dữ liệu
    một lần duy nhất và chính xác tại đây.
    """
    try:
        gc = _get_gspread_client(gcp_creds_file_path)
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.worksheet(worksheet_name) if worksheet_name else sh.sheet1
        data = worksheet.get_all_values()
        if not data or len(data) < 2:
            return pd.DataFrame()
        
        # === FIX: HANDLE DUPLICATE COLUMN NAMES ===
        original_columns = data[0]
        print(f"DEBUG: Original columns: {original_columns}")
        
        # Detect and fix duplicate columns
        seen_columns = {}
        clean_columns = []
        for col in original_columns:
            if col in seen_columns:
                seen_columns[col] += 1
                clean_columns.append(f"{col}_{seen_columns[col]}")
                print(f"WARNING: Duplicate column '{col}' renamed to '{col}_{seen_columns[col]}'")
            else:
                seen_columns[col] = 0
                clean_columns.append(col)
        
        df = pd.DataFrame(data[1:], columns=clean_columns)
        print(f"DEBUG: Cleaned columns: {clean_columns}")
        
        # === SỬA LỖI: LỌC BỎ HÀNG TRỐNG ===
        print(f"DEBUG: Original data has {len(df)} rows")
        
        # Loại bỏ hàng hoàn toàn trống
        df = df.dropna(how='all')
        print(f"DEBUG: After removing completely empty rows: {len(df)} rows")
        
        # Loại bỏ hàng không có Số đặt phòng hoặc Tên người đặt (hai trường quan trọng nhất)
        if 'Số đặt phòng' in df.columns and 'Tên người đặt' in df.columns:
            # Store original count for debugging
            original_count = len(df)
            
            # Convert to string first to avoid errors with numeric values or NaN
            df_booking_id_valid = (df['Số đặt phòng'].notna()) & (df['Số đặt phòng'].astype(str).str.strip() != '') & (df['Số đặt phòng'].astype(str).str.strip() != 'nan')
            df_guest_name_valid = (df['Tên người đặt'].notna()) & (df['Tên người đặt'].astype(str).str.strip() != '') & (df['Tên người đặt'].astype(str).str.strip() != 'nan')
            
            # Show invalid bookings before removing them
            invalid_mask = ~(df_booking_id_valid & df_guest_name_valid)
            if invalid_mask.any():
                invalid_bookings = df[invalid_mask][['Số đặt phòng', 'Tên người đặt']].head(3)
                print(f"DEBUG: Sample invalid bookings to be removed: {invalid_bookings.to_dict('records')}")
                
                # CRITICAL DEBUG: Check if our target booking is being filtered out
                target_id = '6481690399'
                target_booking = df[df['Số đặt phòng'].astype(str) == target_id]
                if not target_booking.empty:
                    booking_data = target_booking[['Số đặt phòng', 'Tên người đặt']].iloc[0]
                    print(f"DEBUG: Target booking {target_id} found - ID: '{booking_data['Số đặt phòng']}', Name: '{booking_data['Tên người đặt']}'")
                    if target_booking.index[0] in df[invalid_mask].index:
                        print(f"ERROR: Target booking {target_id} is being INCORRECTLY filtered out!")
                        print(f"ERROR: ID valid: {df_booking_id_valid.iloc[target_booking.index[0]]}")
                        print(f"ERROR: Name valid: {df_guest_name_valid.iloc[target_booking.index[0]]}")
            
            df = df[df_booking_id_valid & df_guest_name_valid]
            final_count = len(df)
            print(f"DEBUG: After removing rows with missing critical info: {final_count} rows")
            
            if final_count < original_count:
                removed_count = original_count - final_count
                print(f"DEBUG: Removed {removed_count} rows with missing info")
        
        # CRITICAL DEBUG: Check for target booking in RAW data before filtering
        target_id = '6481690399'
        raw_target_check = df[df['Số đặt phòng'].astype(str) == target_id]
        if not raw_target_check.empty:
            print(f"DEBUG RAW: Target booking {target_id} FOUND in raw data at row {raw_target_check.index[0]}")
            print(f"DEBUG RAW: Data: {raw_target_check[['Số đặt phòng', 'Tên người đặt']].iloc[0].to_dict()}")
        else:
            print(f"DEBUG RAW: Target booking {target_id} NOT FOUND in raw data!")
            print(f"DEBUG RAW: Sample booking IDs in raw data: {df['Số đặt phòng'].head(10).tolist()}")
        
        # Reset index sau khi loại bỏ hàng
        df = df.reset_index(drop=True)
        
        if 'Tổng thanh toán' in df.columns:
            df['Tổng thanh toán'] = pd.to_numeric(df['Tổng thanh toán'].astype(str).str.replace('[^\\d.]', '', regex=True), errors='coerce').fillna(0)
        
        # Xử lý cột Hoa hồng
        if 'Hoa hồng' in df.columns:
            df['Hoa hồng'] = pd.to_numeric(df['Hoa hồng'].astype(str).str.replace('[^\\d.]', '', regex=True), errors='coerce').fillna(0)
        else:
            # Nếu chưa có cột Hoa hồng, tạo mặc định = 0
            df['Hoa hồng'] = 0
        
        # === SỬA LỖI QUAN TRỌNG NHẤT ===
        # Ép Pandas đọc ngày tháng theo đúng định dạng YYYY-MM-DD từ sheet của bạn.
        # Điều này loại bỏ mọi sự mơ hồ và sửa lỗi "dừng ở ngày 13".
        # Chúng ta sẽ sử dụng các cột này trong toàn bộ ứng dụng.
        if 'Check-in Date' in df.columns:
            print(f"DEBUG: Processing Check-in Date column. Sample values: {df['Check-in Date'].head().tolist()}")
            df['Check-in Date'] = pd.to_datetime(df['Check-in Date'], format='%Y-%m-%d', errors='coerce')
            # Debug: Check for any NaT values after conversion
            nat_count = df['Check-in Date'].isna().sum()
            if nat_count > 0:
                print(f"WARNING: {nat_count} Check-in Date values could not be parsed")
                # Print problematic values
                problematic = df[df['Check-in Date'].isna()]['Số đặt phòng'].tolist()[:5]
                print(f"DEBUG: Problematic booking IDs: {problematic}")
                
        if 'Check-out Date' in df.columns:
            print(f"DEBUG: Processing Check-out Date column. Sample values: {df['Check-out Date'].head().tolist()}")
            df['Check-out Date'] = pd.to_datetime(df['Check-out Date'], format='%Y-%m-%d', errors='coerce')
            # Debug: Check for any NaT values after conversion
            nat_count = df['Check-out Date'].isna().sum()
            if nat_count > 0:
                print(f"WARNING: {nat_count} Check-out Date values could not be parsed")
                # Print problematic values
                problematic = df[df['Check-out Date'].isna()]['Số đặt phòng'].tolist()[:5]
                print(f"DEBUG: Problematic booking IDs: {problematic}")
            
        return df
    except Exception as e:
        print(f"ERROR importing from Google Sheet: {e}")
        raise

def export_data_to_new_sheet(df: pd.DataFrame, gcp_creds_file_path: str, sheet_id: str) -> str:
    gc = _get_gspread_client(gcp_creds_file_path)
    spreadsheet = gc.open_by_key(sheet_id)
    worksheet_name = f"Export_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    df_str = df.astype(str)
    new_worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=len(df_str) + 1, cols=df_str.shape[1])
    new_worksheet.update([df_str.columns.values.tolist()] + df_str.values.tolist(), 'A1')
    return worksheet_name

def append_multiple_bookings_to_sheet(bookings: List[Dict[str, Any]], gcp_creds_file_path: str, sheet_id: str, worksheet_name: str):
    """
    Enhanced version với debug chi tiết để fix vấn đề mapping columns
    """
    try:
        print(f"🔄 Starting append {len(bookings)} bookings to Google Sheet")
        
        gc = _get_gspread_client(gcp_creds_file_path)
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Debug: Verify worksheet details
        print(f"📋 Worksheet Info: Name='{worksheet.title}', ID={worksheet.id}")
        print(f"📋 Worksheet Row Count: {worksheet.row_count}")
        
        # Debug: Print first booking structure
        if bookings:
            print(f"📝 Sample booking data keys: {list(bookings[0].keys())}")
        
        # Get header from Google Sheet
        header = worksheet.row_values(1)
        print(f"📊 Google Sheet header: {header}")
        
        # Debug: Print EXACT header structure for diagnosis
        print(f"📊 RAW Google Sheet header ({len(header)} columns):")
        for i, col in enumerate(header):
            print(f"  {i+1:2d}: '{col}' (len={len(col)})")
        
        # Debug: Check for missing columns
        missing_columns = []
        for booking in bookings:
            for key in booking.keys():
                if key not in header:
                    missing_columns.append(key)
        
        if missing_columns:
            print(f"⚠️ WARNING: Keys in booking data not found in sheet header: {set(missing_columns)}")
            print(f"📝 Available header columns: {header}")
            print(f"🔍 Booking data keys: {list(bookings[0].keys()) if bookings else 'None'}")
        
        # CRITICAL FIX: Clean and normalize header to prevent column drift
        clean_header = []
        empty_count = 0
        
        for i, col in enumerate(header):
            col_clean = str(col).strip() if col else ''
            if col_clean and col_clean != '':
                # Fix common truncated column names
                if col_clean == 'ên người đặt':  # Missing "T"
                    col_clean = 'Tên người đặt'
                    print(f"🔧 Fixed truncated column: '{col}' → '{col_clean}'")
                elif col_clean.endswith('ười') or col_clean.endswith('tiền'):  # Truncated endings
                    if 'thu' in col_clean.lower():
                        col_clean = 'Người thu tiền'
                        print(f"🔧 Fixed truncated column: '{col}' → '{col_clean}'")
                
                clean_header.append(col_clean)
                print(f"✅ Column {i+1}: '{col_clean}'")
            else:
                empty_count += 1
                print(f"⚠️ Skipping empty column at position {i+1}")
        
        print(f"📊 FINAL Clean header ({len(clean_header)} columns, {empty_count} empty skipped)")
        print(f"📋 Clean columns: {clean_header}")
        
        # Also get the EXACT range for writing to avoid column drift
        if clean_header:
            last_col_letter = chr(ord('A') + len(clean_header) - 1)  # Convert to Excel column letter
            write_range = f"A{worksheet.row_count + 1}:{last_col_letter}{worksheet.row_count + 1}"
            print(f"🎯 Target write range: {write_range}")
        
        # Create rows with proper mapping using clean header
        rows_to_append = []
        for i, booking in enumerate(bookings):
            row = []
            for col in clean_header:
                value = booking.get(col, '')
                # Special handling for dates - ensure proper format
                if 'Date' in col and value:
                    # Ensure date is in YYYY-MM-DD format
                    try:
                        if isinstance(value, str) and value.strip():
                            # Validate date format
                            from datetime import datetime
                            parsed_date = datetime.strptime(value.strip(), '%Y-%m-%d')
                            value = parsed_date.strftime('%Y-%m-%d')
                    except (ValueError, AttributeError):
                        print(f"⚠️ Invalid date format for {col}: {value} in booking {i+1}")
                        value = ''  # Set empty if invalid
                
                row.append(str(value) if value is not None else '')
            
            # Ensure row has exactly the same length as clean header
            while len(row) < len(clean_header):
                row.append('')
                
            rows_to_append.append(row)
            print(f"✅ Mapped booking {i+1}: {booking.get('Tên người đặt', 'Unknown')} ({len(row)} fields)")
        
        if rows_to_append:
            print(f"💾 Writing {len(rows_to_append)} rows to Google Sheet...")
            pre_save_count = worksheet.row_count
            print(f"📊 Pre-save row count: {pre_save_count}")
            
            # CRITICAL FIX: Use exact range update instead of append_rows to prevent column drift
            if clean_header and len(clean_header) <= 26:  # Only for A-Z columns
                start_row = pre_save_count + 1
                end_row = start_row + len(rows_to_append) - 1
                last_col_letter = chr(ord('A') + len(clean_header) - 1)
                exact_range = f"A{start_row}:{last_col_letter}{end_row}"
                
                print(f"🎯 Using EXACT range update: {exact_range}")
                print(f"📏 Data dimensions: {len(rows_to_append)} rows × {len(clean_header)} columns")
                
                # Ensure all rows have exactly the right number of columns
                normalized_rows = []
                for row in rows_to_append:
                    normalized_row = row[:len(clean_header)]  # Truncate if too long
                    while len(normalized_row) < len(clean_header):  # Pad if too short
                        normalized_row.append('')
                    normalized_rows.append(normalized_row)
                    
                worksheet.update(normalized_rows, exact_range, value_input_option='USER_ENTERED')
            else:
                # Fallback to original method for complex cases
                worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
            
            # CRITICAL: Verify save was successful
            post_save_count = worksheet.row_count  
            print(f"📊 Post-save row count: {post_save_count}")
            
            if post_save_count > pre_save_count:
                print(f"🎉 Successfully appended {len(rows_to_append)} bookings to sheet!")
                
                # Verify last row contains our data
                if bookings and 'Số đặt phòng' in bookings[0]:
                    target_id = bookings[0]['Số đặt phòng']
                    try:
                        last_row_data = worksheet.row_values(post_save_count)
                        if last_row_data and len(last_row_data) > 0:
                            print(f"✅ Last row data preview: {last_row_data[:3]}")  # First 3 cells
                            if target_id in str(last_row_data):
                                print(f"✅ CONFIRMED: Target ID {target_id} found in saved row!")
                            else:
                                print(f"⚠️ WARNING: Target ID {target_id} NOT found in saved row!")
                    except Exception as verify_error:
                        print(f"⚠️ Could not verify saved data: {verify_error}")
            else:
                print(f"❌ ERROR: Row count did not increase! Expected increase but got {post_save_count} (was {pre_save_count})")
        else:
            print("❌ No valid rows to append")
            
    except Exception as e:
        print(f"💥 Error in append_multiple_bookings_to_sheet: {e}")
        import traceback
        traceback.print_exc()
        raise

def update_row_in_gsheet(sheet_id: str, gcp_creds_file_path: str, worksheet_name: str, booking_id: str, new_data: dict) -> bool:
    """
    Tìm một hàng trong Google Sheet dựa trên booking_id và cập nhật nó.
    """
    try:
        print(f"Starting update Google Sheet for ID: {booking_id}")
        gc = _get_gspread_client(gcp_creds_file_path)
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.worksheet(worksheet_name)
        
        # Lấy toàn bộ dữ liệu để tìm đúng hàng và cột
        data = worksheet.get_all_values()
        if not data:
            print("Error: Empty sheet.")
            return False
            
        header = data[0]
        
        # Tìm cột chứa 'Số đặt phòng'
        try:
            id_col_index = header.index('Số đặt phòng') + 1  # gspread dùng index từ 1
        except ValueError:
            print("Error: Cannot find 'Số đặt phòng' column in header.")
            return False

        # Tìm hàng có booking_id tương ứng
        cell = worksheet.find(booking_id, in_column=id_col_index)
        if not cell:
            print(f"Error: Cannot find row with ID {booking_id} in column {id_col_index}.")
            return False
            
        row_index = cell.row
        print(f"Found ID {booking_id} at row {row_index}.")

        # Tạo một danh sách các ô cần cập nhật
        cells_to_update = []
        for key, value in new_data.items():
            if key in header:
                col_index = header.index(key) + 1
                # Thêm ô vào danh sách để cập nhật hàng loạt
                cells_to_update.append(gspread.Cell(row=row_index, col=col_index, value=str(value)))

        if cells_to_update:
            worksheet.update_cells(cells_to_update, value_input_option='USER_ENTERED')
            print(f"Successfully updated {len(cells_to_update)} cells for ID {booking_id}.")
            return True
        else:
            print("No valid data to update.")
            return False

    except Exception as e:
        print(f"Critical error when updating Google Sheet: {e}")
        return False

def delete_row_in_gsheet(sheet_id: str, gcp_creds_file_path: str, worksheet_name: str, booking_id: str) -> bool:
    """
    Tìm một hàng trong Google Sheet dựa trên booking_id và xóa nó.
    """
    try:
        print(f"Starting deletion on Google Sheet for ID: {booking_id}")
        gc = _get_gspread_client(gcp_creds_file_path)
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.worksheet(worksheet_name)
        
        header = worksheet.row_values(1)
        try:
            id_col_index = header.index('Số đặt phòng') + 1
        except ValueError:
            print("Error: Cannot find 'Số đặt phòng' column.")
            return False

        cell = worksheet.find(booking_id, in_column=id_col_index)
        if not cell:
            print(f"Error: Cannot find row with ID {booking_id} to delete.")
            return False
            
        worksheet.delete_rows(cell.row)
        print(f"Successfully deleted row containing ID {booking_id}.")
        return True

    except Exception as e:
        print(f"Critical error when deleting from Google Sheet: {e}")
        return False

def delete_multiple_rows_in_gsheet(sheet_id: str, gcp_creds_file_path: str, worksheet_name: str, booking_ids: List[str]) -> bool:
    """
    Xóa nhiều hàng trong Google Sheet dựa trên danh sách các booking_id.
    Phiên bản này hiệu quả và đáng tin cậy hơn.
    """
    if not booking_ids:
        return True
    try:
        print(f"Starting batch deletion on Google Sheet for IDs: {booking_ids}")
        gc = _get_gspread_client(gcp_creds_file_path)
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.worksheet(worksheet_name)
        
        # 1. Đọc tất cả dữ liệu một lần duy nhất
        all_data = worksheet.get_all_values()
        if not all_data:
            print("Sheet is empty, nothing to delete.")
            return True

        header = all_data[0]
        try:
            # Tìm chỉ số của cột 'Số đặt phòng'
            id_col_index = header.index('Số đặt phòng')
        except ValueError:
            print("Error: Cannot find 'Số đặt phòng' column in header.")
            return False

        # 2. Tạo một set các ID cần xóa để tra cứu nhanh
        ids_to_delete_set = set(booking_ids)
        rows_to_delete_indices = []

        # 3. Tìm tất cả các chỉ số hàng cần xóa
        # Duyệt từ hàng thứ 2 (bỏ qua header)
        for i, row in enumerate(all_data[1:]):
            # i bắt đầu từ 0, tương ứng với hàng 2 trong sheet
            row_index_in_sheet = i + 2 
            if len(row) > id_col_index:
                booking_id_in_row = row[id_col_index]
                if booking_id_in_row in ids_to_delete_set:
                    rows_to_delete_indices.append(row_index_in_sheet)

        # 4. Xóa các hàng từ dưới lên trên để tránh lỗi sai chỉ số
        if rows_to_delete_indices:
            # Sắp xếp các chỉ số theo thứ tự giảm dần
            sorted_rows_to_delete = sorted(rows_to_delete_indices, reverse=True)
            print(f"Found {len(sorted_rows_to_delete)} rows to delete. Starting deletion...")
            
            for row_index in sorted_rows_to_delete:
                worksheet.delete_rows(row_index)
            
            print(f"Successfully deleted {len(sorted_rows_to_delete)} rows.")
        else:
            print("No rows found matching the provided IDs.")
        
        return True

    except Exception as e:
        # In ra lỗi chi tiết hơn để debug
        import traceback
        print(f"Critical error when batch deleting on Google Sheet: {e}")
        traceback.print_exc()
        return False

# ==============================================================================
# LOGIC CHO MẪU TIN NHẮN (VỚI DEBUG VÀ XỬ LÝ LỖI NÂNG CAP)
# ==============================================================================

def import_message_templates_from_gsheet(sheet_id: str, gcp_creds_file_path: str) -> List[dict]:
    """
    Đọc mẫu tin nhắn từ tab 'MessageTemplate' trong Google Sheet.
    Phiên bản có debug chi tiết và xử lý lỗi tốt hơn.
    """
    print("=== STARTING IMPORT MESSAGE TEMPLATES ===")
    
    if gspread is None:
        print("❌ gspread library not installed")
        return get_fallback_templates()
    
    try:
        # Bước 1: Kết nối với Google Sheets
        print("Step 1: Connecting to Google Sheets...")
        gc = _get_gspread_client(gcp_creds_file_path)
        print("✓ Connection successful")
        
        # Bước 2: Mở spreadsheet
        print(f"Step 2: Opening spreadsheet with ID: {sheet_id}")
        sh = gc.open_by_key(sheet_id)
        print("✓ Spreadsheet opened successfully")
        
        # Bước 3: Tìm worksheet 'MessageTemplate'
        print("Step 3: Looking for worksheet 'MessageTemplate'...")
        try:
            worksheet = sh.worksheet('MessageTemplate')
            print("✓ Found worksheet 'MessageTemplate'")
        except gspread.exceptions.WorksheetNotFound:
            print("❌ Cannot find worksheet 'MessageTemplate'")
            print("Creating new worksheet with sample data...")
            
            # Tạo worksheet mới với dữ liệu mẫu
            worksheet = sh.add_worksheet(title='MessageTemplate', rows=10, cols=5)
            sample_data = [
                ['Category', 'Label', 'Message'],
                ['Welcome', 'Chào mừng cơ bản', 'Xin chào {guest_name}! Chúng tôi rất vui được đón tiếp bạn.'],
                ['Reminder', 'Nhắc nhở check-out', 'Kính chào {guest_name}, hôm nay là ngày check-out của bạn.'],
                ['Thank You', 'Cảm ơn', 'Cảm ơn {guest_name} đã lựa chọn chúng tôi!']
            ]
            worksheet.update(sample_data, 'A1')
            print("✓ Created new worksheet with sample data")
        
        # Bước 4: Đọc dữ liệu
        print("Step 4: Reading data from worksheet...")
        try:
            all_values = worksheet.get_all_values()
            print(f"✓ Read {len(all_values)} data rows")
        except Exception as e:
            print(f"❌ Error reading data: {e}")
            return []
        
        # Bước 5: Kiểm tra dữ liệu
        if not all_values:
            print("❌ No data in worksheet")
            return []
            
        if len(all_values) < 1:
            print("❌ Worksheet has no header")
            return []
            
        print(f"Headers: {all_values[0]}")
        print(f"Number of data rows (excluding header): {len(all_values) - 1}")
        
        # Bước 6: Xử lý dữ liệu
        headers = all_values[0]
        templates = []
        
        for row_index, row in enumerate(all_values[1:], start=2):  # Bắt đầu từ dòng 2
            try:
                # Tạo dictionary cho mỗi row
                template = {}
                for col_index, header in enumerate(headers):
                    value = row[col_index] if col_index < len(row) else ""
                    template[header] = value.strip() if isinstance(value, str) else str(value).strip()
                
                # Kiểm tra Category có hợp lệ không
                category = template.get('Category', '').strip()
                if category:  # Chỉ thêm nếu có Category
                    templates.append(template)
                    print(f"✓ Row {row_index}: Category='{category}', Label='{template.get('Label', '')}' - VALID")
                else:
                    print(f"⚠ Row {row_index}: Category empty - SKIPPED")
                    
            except Exception as e:
                print(f"❌ Error processing row {row_index}: {e}")
                continue
        
        print(f"=== RESULT: {len(templates)} valid templates ===")
        
        # Debug: In ra templates đầu tiên
        for i, template in enumerate(templates[:2]):
            print(f"Template {i+1}: {template}")
            
        return templates
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Trả về dữ liệu mẫu nếu có lỗi
        print("Returning sample data due to error...")
        return get_fallback_templates()

def get_fallback_templates() -> List[dict]:
    """
    Trả về dữ liệu mẫu khi không thể đọc từ Google Sheets.
    """
    return [
        {
            'Category': 'Welcome',
            'Label': 'Chào mừng cơ bản',
            'Message': 'Xin chào {guest_name}! Chúng tôi rất vui được đón tiếp bạn tại {property_name}.'
        },
        {
            'Category': 'Reminder', 
            'Label': 'Nhắc nhở check-out',
            'Message': 'Kính chào {guest_name}, hôm nay là ngày check-out của bạn ({check_out_date}).'
        },
        {
            'Category': 'Thank You',
            'Label': 'Cảm ơn',
            'Message': 'Cảm ơn {guest_name} đã lựa chọn {property_name}! Hy vọng được phục vụ bạn lần sau.'
        }
    ]

def export_message_templates_to_gsheet(templates: List[dict], sheet_id: str, gcp_creds_file_path: str):
    """
    Export templates với xử lý lỗi tốt hơn.
    """
    print("=== STARTING EXPORT MESSAGE TEMPLATES ===")
    
    if not templates:
        print("❌ No templates to export")
        return False
        
    try:
        print(f"Exporting {len(templates)} templates...")
        gc = _get_gspread_client(gcp_creds_file_path)
        sh = gc.open_by_key(sheet_id)
        
        # Tìm hoặc tạo worksheet
        try:
            worksheet = sh.worksheet('MessageTemplate')
            worksheet.clear()
            print("✓ Cleared old data")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title='MessageTemplate', rows=50, cols=5)
            print("✓ Created new worksheet")
        
        # Chuẩn bị dữ liệu
        headers = ['Category', 'Label', 'Message']
        rows = [headers]
        
        for template in templates:
            row = []
            for header in headers:
                value = template.get(header, '')
                row.append(str(value))
            rows.append(row)
        
        # Ghi dữ liệu
        worksheet.update(rows, 'A1', value_input_option='USER_ENTERED')
        print(f"✓ Successfully exported {len(templates)} templates")
        return True
        
    except Exception as e:
        print(f"❌ Error when exporting: {e}")
        import traceback
        traceback.print_exc()
        return False

def safe_import_message_templates(sheet_id: str, gcp_creds_file_path: str) -> List[dict]:
    """
    Hàm wrapper an toàn để import templates.
    Luôn trả về list, không bao giờ raise exception.
    """
    try:
        result = import_message_templates_from_gsheet(sheet_id, gcp_creds_file_path)
        if isinstance(result, list):
            return result
        else:
            print("❌ Result is not a list, returning fallback")
            return get_fallback_templates()
    except Exception as e:
        print(f"❌ Exception in safe_import: {e}")
        return get_fallback_templates()

# ==============================================================================
# HÀM DEBUG CHO STREAMLIT
# ==============================================================================

def debug_message_templates_connection(sheet_id: str, gcp_creds_file_path: str):
    """
    Hàm debug để kiểm tra kết nối và dữ liệu.
    Sử dụng trong Streamlit để troubleshoot.
    """
    debug_info = {
        'status': 'unknown',
        'error': None,
        'data_preview': None,
        'sheet_structure': None
    }
    
    try:
        print("=== DEBUG MESSAGE TEMPLATES ===")
        
        # Test kết nối
        gc = _get_gspread_client(gcp_creds_file_path)
        sh = gc.open_by_key(sheet_id)
        debug_info['status'] = 'connected'
        
        # Kiểm tra worksheets
        worksheets = [ws.title for ws in sh.worksheets()]
        debug_info['sheet_structure'] = worksheets
        
        if 'MessageTemplate' in worksheets:
            ws = sh.worksheet('MessageTemplate')
            data = ws.get_all_values()
            debug_info['data_preview'] = data[:5]  # 5 dòng đầu
            debug_info['status'] = 'success'
        else:
            debug_info['error'] = 'MessageTemplate worksheet not found'
            debug_info['status'] = 'missing_worksheet'
            
    except Exception as e:
        debug_info['error'] = str(e)
        debug_info['status'] = 'error'
    
    return debug_info

# ==============================================================================
# CÁC HÀM LOGIC (ĐÃ ĐƯỢC ĐƠN GIẢN HÓA VÀ SỬA LỖI)
# ==============================================================================

def create_demo_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    print("Creating demo data because cannot load from Google Sheet.")
    demo_data = {
        'Tên chỗ nghỉ': ['Home in Old Quarter', 'Old Quarter Home', 'Home in Old Quarter', 'Riverside Apartment'],
        'Tên người đặt': ['Demo User Alpha', 'Demo User Beta', 'Demo User Gamma', 'Demo User Delta'],
        'Ngày đến': ['2025-05-22', '2025-05-23', '2025-05-26', '2025-06-01'],
        'Ngày đi': ['2025-05-23', '2025-05-24', '2025-05-28', '2025-06-05'],
        'Tình trạng': ['OK', 'OK', 'OK', 'OK'],
        'Tổng thanh toán': [300000, 450000, 600000, 1200000],
        'Số đặt phòng': [f'DEMO{i+1:09d}' for i in range(4)],
        'Người thu tiền': ['LOC LE', 'THAO LE', 'THAO LE', 'LOC LE']
    }
    df_demo = pd.DataFrame(demo_data)
    df_demo['Check-in Date'] = pd.to_datetime(df_demo['Ngày đến'], errors='coerce')
    df_demo['Check-out Date'] = pd.to_datetime(df_demo['Ngày đi'], errors='coerce')
    df_demo['Tổng thanh toán'] = pd.to_numeric(df_demo['Tổng thanh toán'], errors='coerce').fillna(0)
    active_bookings_demo = df_demo[df_demo['Tình trạng'] != 'Đã hủy'].copy()
    return df_demo, active_bookings_demo

def prepare_dashboard_data(df: pd.DataFrame, start_date, end_date, sort_by=None, sort_order='asc') -> dict:
    """
    Chuẩn bị tất cả dữ liệu cho Dashboard với bộ lọc và sắp xếp động.
    """
    if df.empty:
        return {
            'total_revenue_selected': 0,
            'total_guests_selected': 0,
            'collector_revenue_selected': pd.DataFrame(),
            'monthly_revenue_all_time': pd.DataFrame(),
            'monthly_collected_revenue': pd.DataFrame(),
            'genius_stats': pd.DataFrame(),
            'monthly_guests_all_time': pd.DataFrame(),
            'weekly_guests_all_time': pd.DataFrame()
        }

    # Đảm bảo cột ngày tháng đúng định dạng
    df = df.copy()
    df['Check-in Date'] = pd.to_datetime(df['Check-in Date'])

    # --- TÍNH TOÁN TRƯỚC KHI LỌC (ALL TIME DATA) ---
    
    # 1. Doanh thu hàng tháng trên toàn bộ dữ liệu
    df_with_period = df.copy()
    df_with_period['Month_Period'] = df_with_period['Check-in Date'].dt.to_period('M')
    monthly_revenue = df_with_period.groupby('Month_Period')['Tổng thanh toán'].sum().reset_index()
    monthly_revenue['Tháng'] = monthly_revenue['Month_Period'].dt.strftime('%Y-%m')
    monthly_revenue = monthly_revenue[['Tháng', 'Tổng thanh toán']].rename(columns={'Tổng thanh toán': 'Doanh thu'})

    # 2. Doanh thu đã thu hàng tháng
    collected_df = df[df['Người thu tiền'].notna() & (df['Người thu tiền'] != '') & (df['Người thu tiền'] != 'N/A')].copy()
    if not collected_df.empty:
        collected_df['Month_Period'] = collected_df['Check-in Date'].dt.to_period('M')
        monthly_collected_revenue = collected_df.groupby('Month_Period')['Tổng thanh toán'].sum().reset_index()
        monthly_collected_revenue['Tháng'] = monthly_collected_revenue['Month_Period'].dt.strftime('%Y-%m')
        monthly_collected_revenue = monthly_collected_revenue[['Tháng', 'Tổng thanh toán']].rename(columns={'Tổng thanh toán': 'Doanh thu đã thu'})
    else:
        monthly_collected_revenue = pd.DataFrame(columns=['Tháng', 'Doanh thu đã thu'])

    # 3. Thống kê Genius
    genius_stats = df.groupby('Thành viên Genius').agg({
        'Tổng thanh toán': 'sum',
        'Số đặt phòng': 'count'
    }).reset_index()
    genius_stats.columns = ['Thành viên Genius', 'Tổng doanh thu', 'Số lượng booking']

    # 4. Khách hàng hàng tháng (all time)
    monthly_guests = df_with_period.groupby('Month_Period').size().reset_index(name='Số khách')
    monthly_guests['Tháng'] = monthly_guests['Month_Period'].dt.strftime('%Y-%m')
    monthly_guests = monthly_guests[['Tháng', 'Số khách']]

    # 5. Khách hàng hàng tuần (all time)
    df_with_week = df.copy()
    df_with_week['Week_Period'] = df_with_week['Check-in Date'].dt.to_period('W')
    weekly_guests = df_with_week.groupby('Week_Period').size().reset_index(name='Số khách')
    weekly_guests['Tuần'] = weekly_guests['Week_Period'].astype(str)
    weekly_guests = weekly_guests[['Tuần', 'Số khách']]

    # --- LỌC DỮ LIỆU THEO THỜI GIAN NGƯỜI DÙNG CHỌN ---
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    
    # Lọc theo khoảng thời gian và loại bỏ booking tương lai
    df_filtered = df[
        (df['Check-in Date'] >= start_ts) & 
        (df['Check-in Date'] <= end_ts) &
        (df['Check-in Date'] <= pd.Timestamp.now())
    ].copy()

    # --- TÍNH TOÁN CÁC CHỈ SỐ THEO THỜI GIAN ĐÃ CHỌN ---
    total_revenue_selected = df_filtered['Tổng thanh toán'].sum()
    total_guests_selected = len(df_filtered)
    
    # Doanh thu theo người thu tiền (trong khoảng thời gian đã chọn)
    collector_revenue_selected = df_filtered.groupby('Người thu tiền')['Tổng thanh toán'].sum().reset_index()
    collector_revenue_selected = collector_revenue_selected[
        collector_revenue_selected['Người thu tiền'].notna() & 
        (collector_revenue_selected['Người thu tiền'] != '') & 
        (collector_revenue_selected['Người thu tiền'] != 'N/A')
    ]

    # --- SẮP XẾP ĐỘNG ---
    is_ascending = sort_order == 'asc'
    if sort_by and sort_by in monthly_revenue.columns:
        monthly_revenue = monthly_revenue.sort_values(by=sort_by, ascending=is_ascending)
    else:
        monthly_revenue = monthly_revenue.sort_values(by='Tháng', ascending=False)
        
    # Sắp xếp các dataframe khác
    monthly_collected_revenue = monthly_collected_revenue.sort_values('Tháng', ascending=False)
    monthly_guests = monthly_guests.sort_values('Tháng', ascending=False)
    weekly_guests = weekly_guests.sort_values('Tuần', ascending=False)

    return {
        'total_revenue_selected': total_revenue_selected,
        'total_guests_selected': total_guests_selected,
        'collector_revenue_selected': collector_revenue_selected,
        'monthly_revenue_all_time': monthly_revenue,
        'monthly_collected_revenue': monthly_collected_revenue,
        'genius_stats': genius_stats,
        'monthly_guests_all_time': monthly_guests,
        'weekly_guests_all_time': weekly_guests,
    }

def extract_booking_info_from_image_content(image_bytes: bytes) -> List[Dict[str, Any]]:
    """
    ✅ PHIÊN BẢN NÂNG CẤP: Trích xuất thông tin đặt phòng từ ảnh bằng Google Gemini API
    Với error handling tốt hơn và prompt được tối ưu.
    """
    print("\n🔍 STARTING AI IMAGE PROCESSING (UPGRADED VERSION)")
    
    # Kiểm tra dependencies
    if Image is None:
        error_msg = "❌ PIL library chưa được cài đặt. Hãy cài: pip install Pillow"
        print(error_msg)
        return [{"error": error_msg}]
    
    if genai is None:
        error_msg = "❌ google-generativeai library chưa được cài đặt. Hãy cài: pip install google-generativeai"
        print(error_msg)
        return [{"error": error_msg}]
    
    try:
        # 1. Cấu hình API Key với nhiều nguồn
        api_key = None
        try:
            # Thử từ .env file trước
            import os
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                print("✅ Found API Key from environment variable")
            else:
                # Thử từ secrets.toml (cho Streamlit)
                try:
                    import toml
                    secrets_path = ".streamlit/secrets.toml"
                    secrets = toml.load(secrets_path)
                    api_key = secrets.get("GOOGLE_API_KEY")
                    if api_key:
                        print("✅ Found API Key from secrets.toml")
                except:
                    pass
        except Exception as e:
            print(f"⚠️ Error reading API key: {e}")
        
        if not api_key:
            error_msg = "❌ Cannot find GOOGLE_API_KEY. Please configure in .env file."
            print(error_msg)
            return [{"error": error_msg}]

        # Cấu hình Gemini
        genai.configure(api_key=api_key)
        print("✅ Successfully configured Google AI API")

        # 2. Optimize image size to reduce tokens while maintaining quality
        try:
            img = Image.open(BytesIO(image_bytes))
            original_size = img.size
            print(f"✅ Successfully loaded image. Original size: {original_size}")
            
            # Resize if image is too large (limit to 1024px on longest side)
            max_size = 1024
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                print(f"📏 Resized image from {original_size} to {img.size} for token efficiency")
            
        except Exception as e:
            error_msg = f"❌ Error processing image: {str(e)}"
            print(error_msg)
            return [{"error": error_msg}]

        # 3. Khởi tạo model với model chính xác
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("✅ Successfully initialized Gemini model")
        except Exception as e:
            print(f"⚠️ Error with gemini-2.0-flash-exp, trying other model...")
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                print("✅ Successfully initialized Gemini 1.5 Flash")
            except Exception as e2:
                error_msg = f"❌ Cannot initialize Gemini model: {str(e2)}"
                print(error_msg)
                return [{"error": error_msg}]
        
        # 4. OPTIMIZED PROMPT - Shorter but precise for token efficiency
        enhanced_prompt = """Extract hotel booking info from image. Return JSON array only.

Required fields:
- guest_name: Customer name
- booking_id: Confirmation/booking number
- check_in_date: YYYY-MM-DD format
- check_out_date: YYYY-MM-DD format  
- room_type: Accommodation type
- total_payment: Total amount (number)
- commission: Commission amount (number)

Output format (no markdown):
[{"guest_name":"Name","booking_id":"ID","check_in_date":"2025-01-15","check_out_date":"2025-01-16","room_type":"Room","total_payment":100,"commission":10}]

Return [] if no booking info found."""

        # 5. Gọi API với retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🤖 Sending request to Gemini AI (attempt {attempt + 1}/{max_retries})...")
                
                response = model.generate_content([enhanced_prompt, img], stream=False)
                response.resolve()
                
                ai_response_text = response.text.strip()
                print(f"✅ Received response from AI ({len(ai_response_text)} characters)")
                
                if not ai_response_text:
                    raise ValueError("AI returned empty response")
                
                break  # Thành công, thoát khỏi retry loop
                
            except Exception as api_error:
                print(f"❌ API error attempt {attempt + 1}: {str(api_error)}")
                if attempt == max_retries - 1:  # Lần thử cuối cùng
                    error_msg = f"❌ Gemini API error after {max_retries} attempts: {str(api_error)}"
                    print(error_msg)
                    return [{"error": error_msg}]
                import time
                time.sleep(2)  # Đợi 2 giây trước khi thử lại

        # 6. Xử lý và parse kết quả
        print("\n📝 RAW RESULT FROM AI:")
        print("-" * 50)
        print(ai_response_text[:500] + ("..." if len(ai_response_text) > 500 else ""))
        print("-" * 50)

        # Clean response (remove markdown if present)
        cleaned_response = ai_response_text.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        # Parse JSON với error handling
        try:
            parsed_result = json.loads(cleaned_response)
            print(f"✅ JSON parsing successful")
            
            # Validate result structure
            if not isinstance(parsed_result, list):
                if isinstance(parsed_result, dict):
                    parsed_result = [parsed_result]  # Convert single object to array
                else:
                    raise ValueError("Result is not array or object")
            
            # Validate và clean từng booking
            validated_bookings = []
            for i, booking in enumerate(parsed_result):
                if not isinstance(booking, dict):
                    print(f"⚠️ Booking {i+1} is not dict, skipping")
                    continue
                
                # Ensure all required fields exist and validate dates
                check_in_date = str(booking.get("check_in_date", "")).strip() or None
                check_out_date = str(booking.get("check_out_date", "")).strip() or None
                
                # Normalize date formats to YYYY-MM-DD
                if check_in_date:
                    check_in_date = normalize_date_format(check_in_date)
                if check_out_date:
                    check_out_date = normalize_date_format(check_out_date)
                
                validated_booking = {
                    "guest_name": str(booking.get("guest_name", "")).strip() or None,
                    "booking_id": str(booking.get("booking_id", "")).strip() or None,
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "room_type": str(booking.get("room_type", "")).strip() or None,
                    "total_payment": booking.get("total_payment", 0),
                    "commission": booking.get("commission", 0)
                }
                
                # Convert numeric fields
                try:
                    if validated_booking["total_payment"]:
                        validated_booking["total_payment"] = float(validated_booking["total_payment"])
                    else:
                        validated_booking["total_payment"] = 0
                        
                    if validated_booking["commission"]:
                        validated_booking["commission"] = float(validated_booking["commission"])
                    else:
                        validated_booking["commission"] = 0
                except (ValueError, TypeError):
                    validated_booking["total_payment"] = 0
                    validated_booking["commission"] = 0
                
                validated_bookings.append(validated_booking)
                print(f"✅ Validated booking {i+1}: {validated_booking['guest_name']}")
            
            if not validated_bookings:
                print("⚠️ No valid bookings found")
                return [{"error": "No valid booking information found in image"}]
            
            print(f"🎉 Successfully extracted {len(validated_bookings)} bookings!")
            return validated_bookings
            
        except json.JSONDecodeError as json_error:
            error_msg = f"❌ JSON parsing error: {str(json_error)}\nResponse: {cleaned_response[:200]}..."
            print(error_msg)
            return [{"error": "AI returned invalid format. Please try with clearer image."}]

    except Exception as main_error:
        error_msg = f"❌ General error: {str(main_error)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return [{"error": f"Image processing error: {str(main_error)}"}]

def normalize_date_format(date_str: str) -> str:
    """
    Normalize various date formats to YYYY-MM-DD
    """
    if not date_str or date_str.strip() == '':
        return None
    
    date_str = date_str.strip()
    
    # Common date formats to try
    formats_to_try = [
        '%Y-%m-%d',      # 2025-01-15
        '%d/%m/%Y',      # 15/01/2025
        '%m/%d/%Y',      # 01/15/2025
        '%d-%m-%Y',      # 15-01-2025
        '%m-%d-%Y',      # 01-15-2025
        '%Y/%m/%d',      # 2025/01/15
        '%d.%m.%Y',      # 15.01.2025
        '%Y.%m.%d',      # 2025.01.15
    ]
    
    for fmt in formats_to_try:
        try:
            parsed_date = datetime.datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # If no format matches, return original string
    print(f"⚠️ Could not normalize date format: {date_str}")
    return date_str

def parse_app_standard_date(date_input: Any) -> Optional[datetime.date]:
    """
    Hàm này chuyển đổi ngày tháng từ nhiều định dạng khác nhau sang datetime.date
    """
    if pd.isna(date_input):
        return None
    if isinstance(date_input, (datetime.datetime, datetime.date)):
        return date_input.date() if isinstance(date_input, datetime.datetime) else date_input
    if isinstance(date_input, pd.Timestamp):
        return date_input.date()

    date_str = str(date_input).strip().lower()
    
    # Thử parse định dạng "ngày DD tháng MM năm YYYY"
    try:
        if "ngày" in date_str and "tháng" in date_str and "năm" in date_str:
            parts = date_str.replace("ngày", "").replace("tháng", "").replace("năm", "").split()
            if len(parts) >= 3:
                day = int(parts[0])
                month = int(parts[1])
                year = int(parts[2])
                return datetime.date(year, month, day)
    except:
        pass

    # Thử parse các định dạng khác
    try:
        return pd.to_datetime(date_str).date()
    except:
        pass

    return None

def get_daily_activity(date_to_check: datetime.date, df: pd.DataFrame) -> dict:
    """
    Hàm này tính toán các hoạt động cho một ngày cụ thể, bao gồm:
    - Khách check-in hôm nay.
    - Khách check-out hôm nay.
    - Khách đang ở (đã check-in trước đó và chưa check-out).
    """
    if df is None or df.empty:
        return {'check_in': [], 'check_out': [], 'staying_over': []}

    df_local = df.copy()

    # Chuyển đổi cột datetime sang date để so sánh chính xác ngày.
    df_local['Check-in Date'] = pd.to_datetime(df_local['Check-in Date'], errors='coerce').dt.date
    df_local['Check-out Date'] = pd.to_datetime(df_local['Check-out Date'], errors='coerce').dt.date

    # Lọc các booking có tình trạng OK
    active_bookings = df_local[df_local['Tình trạng'] != 'Đã hủy'].copy()
    if active_bookings.empty:
        return {'check_in': [], 'check_out': [], 'staying_over': []}

    # 1. Lấy khách CHECK-IN hôm nay
    check_ins_df = active_bookings[active_bookings['Check-in Date'] == date_to_check]

    # 2. Lấy khách CHECK-OUT hôm nay
    check_outs_df = active_bookings[active_bookings['Check-out Date'] == date_to_check]

    # 3. Lấy khách ĐANG Ở (không check-in và cũng không check-out hôm nay)
    staying_over_df = active_bookings[
        (active_bookings['Check-in Date'] < date_to_check) &
        (active_bookings['Check-out Date'] > date_to_check)
    ]
    
    # Trả về toàn bộ thông tin của các booking này dưới dạng dictionary
    return {
        'check_in': check_ins_df.to_dict(orient='records'),
        'check_out': check_outs_df.to_dict(orient='records'),
        'staying_over': staying_over_df.to_dict(orient='records')
    }

def get_overall_calendar_day_info(date_to_check: datetime.date, df: pd.DataFrame, total_capacity: int) -> dict:
    """
    Hàm này tính toán công suất phòng và trả về cả thông tin trạng thái và màu sắc.
    """
    if df is None or df.empty or total_capacity == 0:
        return {
            'occupied_units': 0, 'available_units': total_capacity,
            'status_text': "Trống", 'status_color': 'empty' # Màu cho ngày trống
        }

    df_local = df.copy()

    df_local['Check-in Date'] = pd.to_datetime(df_local['Check-in Date'], errors='coerce').dt.date
    df_local['Check-out Date'] = pd.to_datetime(df_local['Check-out Date'], errors='coerce').dt.date

    active_on_date = df_local[
        (df_local['Check-in Date'].notna()) &
        (df_local['Check-out Date'].notna()) &
        (df_local['Check-in Date'] <= date_to_check) & 
        (df_local['Check-out Date'] > date_to_check) &
        (df_local['Tình trạng'] != 'Đã hủy')
    ]
    
    occupied_units = len(active_on_date)
    available_units = max(0, total_capacity - occupied_units)
    
    # Quyết định văn bản và màu sắc dựa trên tình trạng
    if occupied_units == 0:
        status_text = "Trống"
        status_color = "empty"  # Sẽ tương ứng với màu vàng
    elif available_units == 0:
        status_text = "Hết phòng"
        status_color = "full"   # Sẽ tương ứng với màu đỏ
    else:
        status_text = f"{available_units}/{total_capacity} trống"
        status_color = "occupied" # Sẽ tương ứng với màu xanh

    return {
        'occupied_units': occupied_units,
        'available_units': available_units,
        'status_text': status_text,
        'status_color': status_color  # Trả về thêm thông tin màu sắc
    }

def delete_booking_by_id(df: pd.DataFrame, booking_id: str) -> pd.DataFrame:
    """
    Tìm và xóa một đặt phòng dựa trên Số đặt phòng.
    """
    if df is None or 'Số đặt phòng' not in df.columns:
        return df
    
    # Tìm index của dòng cần xóa
    index_to_delete = df[df['Số đặt phòng'] == booking_id].index
    
    if not index_to_delete.empty:
        df = df.drop(index_to_delete)
        print(f"Deleted booking with ID: {booking_id}")
    else:
        print(f"Cannot find booking with ID: {booking_id} to delete.")
        
    return df.reset_index(drop=True)


def update_booking_by_id(df: pd.DataFrame, booking_id: str, new_data: dict) -> pd.DataFrame:
    """
    Tìm và cập nhật thông tin cho một đặt phòng.
    """
    if df is None or 'Số đặt phòng' not in df.columns:
        return df

    index_to_update = df[df['Số đặt phòng'] == booking_id].index
    
    if not index_to_update.empty:
        idx = index_to_update[0]
        for key, value in new_data.items():
            if key in df.columns:
                # Chuyển đổi kiểu dữ liệu trước khi gán
                if 'Date' in key and value:
                    df.loc[idx, key] = pd.to_datetime(value)
                elif 'thanh toán' in key.lower() and value:
                    df.loc[idx, key] = float(value)
                else:
                    df.loc[idx, key] = value
        
        print(f"Updated booking with ID: {booking_id}")
    else:
        print(f"Cannot find booking with ID: {booking_id} to update.")

    return df