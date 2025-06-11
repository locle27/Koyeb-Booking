import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from dotenv import load_dotenv
import json
from functools import lru_cache
from pathlib import Path
import pandas as pd
# plotly imports moved to dashboard_routes.py
from datetime import datetime, timedelta
import calendar
import base64
import google.generativeai as genai
from io import BytesIO

# --- Cài đặt Chế độ ---
# Đặt thành True để bật thanh công cụ dev và chế độ debug.
# Đặt thành False để chạy ở chế độ production (tắt thanh công cụ).
DEV_MODE = True  # Bật development mode để tự động reload
# --------------------

# Import các hàm logic
from logic import (
    import_from_gsheet, create_demo_data,
    get_daily_activity, get_overall_calendar_day_info,
    extract_booking_info_from_image_content,
    export_data_to_new_sheet,
    append_multiple_bookings_to_sheet,
    delete_booking_by_id, update_row_in_gsheet,
    prepare_dashboard_data, delete_row_in_gsheet,
    delete_multiple_rows_in_gsheet,
    import_message_templates_from_gsheet,
    export_message_templates_to_gsheet
)

# Import dashboard logic module
from dashboard_routes import process_dashboard_data, safe_to_dict_records

# Import Email & Reminder System
from email_service import send_test_email, email_service
from reminder_system import (
    start_reminder_system, stop_reminder_system, 
    get_reminder_status, manual_trigger_reminders,
    enable_reminders, disable_reminders
)

# Cấu hình
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, template_folder=BASE_DIR / "templates", static_folder=BASE_DIR / "static")

# Sử dụng biến DEV_MODE để cấu hình app
app.config['ENV'] = 'production'  # Luôn sử dụng production mode
app.config['DEBUG'] = False  # Luôn tắt debug mode
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_default_secret_key_for_development")

# Vô hiệu hóa Debug Toolbar - Đã hoàn toàn bị xóa
# KHÔNG import hoặc sử dụng DebugToolbarExtension

@app.context_processor
def inject_dev_mode():
    return dict(dev_mode=DEV_MODE)

@app.context_processor
def inject_pandas():
    return dict(pd=pd)

# Custom Jinja2 filters cho ngày tháng
@app.template_filter('safe_date_format')
def safe_date_format(date_value, format_string='%d/%m/%y'):
    """
    Safely format date values, handling None, NaT, and string values
    """
    try:
        if date_value is None:
            return 'N/A'
        
        # Handle string representations
        if isinstance(date_value, str):
            if date_value.lower() in ['nat', 'none', 'null', '', 'n/a']:
                return 'N/A'
            # Try to parse string as date
            try:
                date_value = pd.to_datetime(date_value)
            except:
                return date_value  # Return original string if can't parse
        
        # Handle pandas NaT
        if pd.isna(date_value):
            return 'N/A'
            
        # Handle datetime objects
        if hasattr(date_value, 'strftime'):
            return date_value.strftime(format_string)
        
        return str(date_value)
        
    except Exception as e:
        print(f"Error formatting date {date_value}: {e}")
        return 'Error'

@app.template_filter('safe_day_name')
def safe_day_name(date_value):
    """
    Safely get day name from date value
    """
    try:
        if date_value is None or pd.isna(date_value):
            return ''
        
        if isinstance(date_value, str):
            if date_value.lower() in ['nat', 'none', 'null', '', 'n/a']:
                return ''
            try:
                date_value = pd.to_datetime(date_value)
            except:
                return ''
        
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%A')
        
        return ''
        
    except Exception as e:
        print(f"Error getting day name for {date_value}: {e}")
        return ''

@app.template_filter('is_valid_date')
def is_valid_date(date_value):
    """
    Check if date value is valid
    """
    try:
        if date_value is None:
            return False
        
        if isinstance(date_value, str):
            if date_value.lower() in ['nat', 'none', 'null', '', 'n/a']:
                return False
            try:
                pd.to_datetime(date_value)
                return True
            except:
                return False
        
        if pd.isna(date_value):
            return False
            
        return hasattr(date_value, 'strftime')
        
    except:
        return False

# --- Lấy thông tin từ .env ---
GCP_CREDS_FILE_PATH = os.getenv("GCP_CREDS_FILE_PATH")
DEFAULT_SHEET_ID = os.getenv("DEFAULT_SHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TOTAL_HOTEL_CAPACITY = 4

# --- Khởi tạo ---
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# --- Hàm chính để tải dữ liệu ---
@lru_cache(maxsize=1)
def load_data():
    print("Loading booking data from source...")
    try:
        df = import_from_gsheet(DEFAULT_SHEET_ID, GCP_CREDS_FILE_PATH, WORKSHEET_NAME)
        if df.empty:
            raise ValueError("Booking sheet is empty or inaccessible.")
        active_bookings = df[df['Tình trạng'] != 'Đã hủy'].copy()
        print("Successfully loaded data from Google Sheet!")
        return df, active_bookings
    except Exception as e:
        print(f"Error loading booking data: {e}. Using demo data.")
        df_demo, active_bookings_demo = create_demo_data()
        return df_demo, active_bookings_demo

# --- CÁC ROUTE CỦA ỨNG DỤNG ---

@app.route('/')
def dashboard():
    """Optimized dashboard route using modular approach"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Set default date range to current month
    if not start_date_str or not end_date_str:
        today_full = datetime.today()
        start_date = today_full.replace(day=1)
        _, last_day = calendar.monthrange(today_full.year, today_full.month)
        end_date = today_full.replace(day=last_day)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    # Load data and prepare dashboard
    df, _ = load_data()
    sort_by = request.args.get('sort_by', 'Tháng')
    sort_order = request.args.get('sort_order', 'desc')
    dashboard_data = prepare_dashboard_data(df, start_date, end_date, sort_by, sort_order)

    # Process all dashboard data using modular approach
    processed_data = process_dashboard_data(df, start_date, end_date, sort_by, sort_order, dashboard_data)

    # Render template with processed data
    return render_template(
        'dashboard.html',
        total_revenue=dashboard_data.get('total_revenue_selected', 0),
        total_guests=dashboard_data.get('total_guests_selected', 0),
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        current_sort_by=sort_by,
        current_sort_order=sort_order,
        collector_revenue_list=safe_to_dict_records(dashboard_data.get('collector_revenue_selected', pd.DataFrame())),
        **processed_data  # Unpack all processed dashboard data
    )

@app.route('/bookings')
def view_bookings():
    df, _ = load_data()
    
    # Lấy tham số từ URL
    search_term = request.args.get('search_term', '').strip().lower()
    sort_by = request.args.get('sort_by', 'Check-in Date') # Mặc định sắp xếp theo Check-in Date
    order = request.args.get('order', 'asc') # Mặc định tăng dần (ascending)
    
    # Thêm filter theo tháng
    filter_month = request.args.get('filter_month', '')
    filter_year = request.args.get('filter_year', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # === FILTER MỚI: CHỈ HIỂN THỊ KHÁCH ACTIVE ===
    show_all = request.args.get('show_all', 'false').lower() == 'true'
    
    # === MẶC ĐỊNH CHỈ HIỂN THỊ THÁNG HIỆN TẠI NẾU KHÔNG CÓ FILTER ===
    if not filter_month and not filter_year and not start_date and not end_date and not show_all:
        # Lọc theo tháng hiện tại
        current_date = datetime.today()
        filter_month = str(current_date.month)
        filter_year = str(current_date.year)
        print(f"DEBUG: Mặc định lọc theo tháng hiện tại: {filter_month}/{filter_year}")
    
    if not show_all:
        # Mặc định: chỉ hiển thị khách active (chưa thu tiền HOẶC chưa check-out)
        today = datetime.today().date()
        
        # Điều kiện active:
        # 1. Chưa thu tiền (Người thu tiền không phải LOC LE/THAO LE)
        # 2. HOẶC chưa check-out (Check-out Date > hôm nay)
        # 3. VÀ không bị hủy
        
        # Ensure datetime conversion
        if 'Check-out Date' in df.columns:
            df['Check-out Date'] = pd.to_datetime(df['Check-out Date'], errors='coerce')
        
        # Create active mask
        not_cancelled = df['Tình trạng'] != 'Đã hủy'
        
        # Chưa thu tiền
        collected_values = ['LOC LE', 'THAO LE']
        collector_series = df['Người thu tiền'].fillna('').astype(str)
        not_collected = ~collector_series.isin(collected_values)
        
        # Chưa check-out (check-out date là hôm nay hoặc trong tương lai)
        not_checked_out = df['Check-out Date'].dt.date >= today
        
        # Combine conditions: (chưa thu tiền HOẶC chưa check-out) VÀ không bị hủy
        active_mask = (not_collected | not_checked_out) & not_cancelled
        
        df = df[active_mask].copy()
        
        print(f"DEBUG: Filtered to {len(df)} active bookings (unpaid OR not checked out)")

    # Lọc theo từ khóa tìm kiếm
    if search_term:
        df = df[df.apply(lambda row: search_term in str(row).lower(), axis=1)]

    # Lọc theo tháng/năm
    if filter_month and filter_year:
        try:
            year = int(filter_year)
            month = int(filter_month)
            df = df[
                (df['Check-in Date'].dt.year == year) & 
                (df['Check-in Date'].dt.month == month)
            ]
            print(f"DEBUG: Filtered by month {month}/{year}, result: {len(df)} bookings")
        except (ValueError, AttributeError):
            pass
    
    # Lọc theo khoảng ngày cụ thể
    elif start_date and end_date:
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[
                (df['Check-in Date'] >= start_dt) & 
                (df['Check-in Date'] <= end_dt)
            ]
        except (ValueError, AttributeError):
            pass

    # Sắp xếp dữ liệu
    if sort_by in df.columns:
        ascending = order == 'asc'
        df = df.sort_values(by=sort_by, ascending=ascending)
    
    bookings_list = safe_to_dict_records(df)
    
    # Tạo danh sách tháng/năm có sẵn để dropdown
    all_df, _ = load_data()
    available_months = []
    if not all_df.empty and 'Check-in Date' in all_df.columns:
        unique_dates = all_df['Check-in Date'].dropna().dt.to_period('M').unique()
        available_months = [(str(period), period.year, period.month) for period in sorted(unique_dates, reverse=True)]
    
    return render_template('bookings.html', 
                         bookings=bookings_list, 
                         search_term=search_term, 
                         booking_count=len(bookings_list),
                         current_sort_by=sort_by,
                         current_order=order,
                         filter_month=filter_month,
                         filter_year=filter_year,
                         start_date=start_date,
                         end_date=end_date,
                         available_months=available_months,
                         show_all=show_all)

@app.route('/calendar/')
@app.route('/calendar/<int:year>/<int:month>')
def calendar_view(year=None, month=None):
    today = datetime.today()
    if year is None or month is None:
        return redirect(url_for('calendar_view', year=today.year, month=today.month))
    
    current_month_start = datetime(year, month, 1)
    prev_month_date = (current_month_start.replace(day=1) - timedelta(days=1)).replace(day=1)
    next_month_date = (current_month_start.replace(day=1) + timedelta(days=32)).replace(day=1)

    df, _ = load_data()
    month_activities = {}
    month_matrix = calendar.monthcalendar(year, month)
    
    calendar_data = []
    for week in month_matrix:
        week_data = []
        for day in week:
            if day != 0:
                current_date = datetime(year, month, day).date()
                date_str = current_date.strftime('%Y-%m-%d')
                day_info = get_overall_calendar_day_info(current_date, df, TOTAL_HOTEL_CAPACITY)
                week_data.append((current_date, date_str, day_info))
            else:
                week_data.append((None, None, None))
        calendar_data.append(week_data)

    return render_template(
        'calendar.html',
        calendar_data=calendar_data,
        current_month=current_month_start,
        prev_month=prev_month_date,
        next_month=next_month_date,
        today=today.date()
    )

@app.route('/calendar/details/<string:date_str>')
def calendar_details(date_str):
    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash("Định dạng ngày không hợp lệ.", "danger")
        return redirect(url_for('calendar_view'))
    df, _ = load_data()
    activities = get_daily_activity(parsed_date, df)
    return render_template('calendar_details.html',
                           date=parsed_date.strftime('%d/%m/%Y'),
                           check_in=activities.get('check_in', []),
                           check_out=activities.get('check_out', []),
                           staying_over=activities.get('staying_over', []),
                           current_date=parsed_date)
    
@app.route('/bookings/add_from_image', methods=['GET'])
def add_from_image_page():
    return render_template('add_from_image.html')

@app.route('/api/process_pasted_image', methods=['POST'])
def process_pasted_image():
    data = request.get_json()
    if not data or 'image_b64' not in data:
        return jsonify({"error": "Yêu cầu không chứa dữ liệu ảnh."}), 400
    try:
        image_header, image_b64_data = data['image_b64'].split(',', 1)
        image_bytes = base64.b64decode(image_b64_data)
        extracted_data = extract_booking_info_from_image_content(image_bytes)
        return jsonify(extracted_data)
    except Exception as e:
        return jsonify({"error": f"Lỗi xử lý phía server: {str(e)}"}), 500

@app.route('/bookings/sync')
def sync_bookings():
    """
    Đây là nơi ĐÚNG và DUY NHẤT để gọi cache_clear.
    """
    try:
        load_data.cache_clear()
        flash('Data has been synced from Google Sheets.', 'info')
        print("Cache cleared successfully via Sync button.")
    except Exception as e:
        flash(f'Error clearing cache: {e}', 'danger')

    return redirect(url_for('view_bookings'))

@app.route('/bookings/export')
def export_bookings():
    try:
        df, _ = load_data()
        if not df.empty:
            worksheet_name = export_data_to_new_sheet(df, GCP_CREDS_FILE_PATH, DEFAULT_SHEET_ID)
            flash(f'Đã export dữ liệu thành công ra sheet mới: "{worksheet_name}"', 'success')
        else:
            flash('Không có dữ liệu để export.', 'warning')
    except Exception as e:
        flash(f'Lỗi khi export dữ liệu: {e}', 'danger')
    return redirect(url_for('view_bookings'))
    
@app.route('/bookings/save_extracted', methods=['POST'])
def save_extracted_bookings():
    try:
        extracted_json_str = request.form.get('extracted_json')
        if not extracted_json_str:
            flash('[ERROR] Không có dữ liệu để lưu.', 'warning')
            return redirect(url_for('add_from_image_page'))

        print(f"📥 Received extracted data: {len(extracted_json_str)} characters")
        bookings_to_save = json.loads(extracted_json_str)
        print(f"[CHART] Parsed {len(bookings_to_save)} bookings from JSON")
        
        formatted_bookings = []
        errors = []
        saved_booking_ids = []  # ✅ Track saved booking IDs
        
        for i, booking in enumerate(bookings_to_save):
            try:
                if 'error' in booking: 
                    continue
                    
                # Debug: Print original booking data
                print(f"🔍 Original booking {i+1}: {booking}")
                    
                # Validate essential fields
                if not booking.get('guest_name', '').strip():
                    errors.append(f"Booking {i+1}: Thiếu tên khách")
                    continue
                    
                if not booking.get('check_in_date', '').strip():
                    errors.append(f"Booking {i+1}: Thiếu ngày check-in")
                    continue
                    
                if not booking.get('check_out_date', '').strip():
                    errors.append(f"Booking {i+1}: Thiếu ngày check-out")
                    continue
                
                # Generate booking ID
                booking_id = booking.get('booking_id', '').strip() or f"IMG_{datetime.now().strftime('%Y%m%d%H%M%S')}{i:02d}"
                saved_booking_ids.append(booking_id)  # ✅ Track this ID
                
                # Enhanced: Format booking data with better mapping and date validation
                check_in_date = booking.get('check_in_date', '').strip()
                check_out_date = booking.get('check_out_date', '').strip()
                
                # Validate and normalize dates
                try:
                    if check_in_date:
                        check_in_parsed = datetime.strptime(check_in_date, '%Y-%m-%d')
                        check_in_date = check_in_parsed.strftime('%Y-%m-%d')
                except ValueError:
                    print(f"⚠️ Invalid check-in date format: {check_in_date}")
                    errors.append(f"Booking {i+1}: Định dạng ngày check-in không hợp lệ")
                    continue
                
                try:
                    if check_out_date:
                        check_out_parsed = datetime.strptime(check_out_date, '%Y-%m-%d')
                        check_out_date = check_out_parsed.strftime('%Y-%m-%d')
                except ValueError:
                    print(f"⚠️ Invalid check-out date format: {check_out_date}")
                    errors.append(f"Booking {i+1}: Định dạng ngày check-out không hợp lệ")
                    continue
                
                # Calculate stay duration
                stay_duration = ''
                if check_in_date and check_out_date:
                    try:
                        checkin_dt = datetime.strptime(check_in_date, '%Y-%m-%d')
                        checkout_dt = datetime.strptime(check_out_date, '%Y-%m-%d')
                        duration = (checkout_dt - checkin_dt).days
                        stay_duration = str(duration)
                    except:
                        stay_duration = ''
                
                # Format Vietnamese dates
                checkin_vn = ''
                checkout_vn = ''
                if check_in_date:
                    try:
                        parts = check_in_date.split('-')
                        checkin_vn = f"ngày {parts[2]} tháng {parts[1]} năm {parts[0]}"
                    except:
                        checkin_vn = ''
                if check_out_date:
                    try:
                        parts = check_out_date.split('-')
                        checkout_vn = f"ngày {parts[2]} tháng {parts[1]} năm {parts[0]}"
                    except:
                        checkout_vn = ''
                
                # Use correct column mapping with proper full names - EXACT MATCH với Google Sheets
                formatted_booking = {
                    'Số đặt phòng': booking_id,
                    'Tên người đặt': booking.get('guest_name', '').strip(),
                    'Tên chỗ nghỉ': booking.get('room_type', '').strip() or 'Chưa xác định',
                    'Check-in Date': check_in_date,
                    'Check-out Date': check_out_date,
                    'Stay Duration': stay_duration,
                    'Tình trạng': 'OK',
                    'Tổng thanh toán': booking.get('total_payment', 0) or 0,
                    'Giá mỗi đêm': booking.get('total_payment', 0) or 0,
                    'Booking Date': datetime.now().strftime('%Y-%m-%d'),
                    'Ngày đến': checkin_vn,
                    'Ngày đi': checkout_vn,
                    'Vị trí': 'N/A (Chưa xác định)',
                    'Thành viên Genius': 'Không',
                    'Được đặt vào': datetime.now().strftime('%d tháng %m, %Y'),
                    'Hoa hồng': booking.get('commission', 0) or 0,
                    'Tiền tệ': 'VND',
                    'Người nhận tiền': '',
                    'Ghi chú thanh toán': f"Thêm từ ảnh lúc {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    'Người thu tiền': '',
                    'Taxi': ''
                }
                
                # Remove keys that don't exist in actual sheet header
                print(f"[DEBUG] Pre-filtering booking keys: {list(formatted_booking.keys())}")
                # This will be filtered during append process based on actual header
                
                # Debug: Print formatted booking
                print(f"✅ Formatted booking {i+1}: {formatted_booking}")
                
                formatted_bookings.append(formatted_booking)
                print(f"[OK] Formatted booking {i+1}: {formatted_booking['Tên người đặt']}")
                
            except Exception as e:
                errors.append(f"Lỗi xử lý booking {i+1}: {str(e)}")
                print(f"[ERROR] Error processing booking {i+1}: {e}")
                import traceback
                traceback.print_exc()

        if formatted_bookings:
            print(f"[SAVE] Attempting to save {len(formatted_bookings)} bookings to Google Sheets...")
            
            # Save to Google Sheets with enhanced error handling
            try:
                print(f"[SAVE] Attempting to save {len(formatted_bookings)} bookings...")
                print(f"[SAVE] Sample booking data: {formatted_bookings[0] if formatted_bookings else 'None'}")
                
                append_multiple_bookings_to_sheet(
                    bookings=formatted_bookings,
                    gcp_creds_file_path=GCP_CREDS_FILE_PATH,
                    sheet_id=DEFAULT_SHEET_ID,
                    worksheet_name=WORKSHEET_NAME
                )
                print("[SAVE] ✅ Successfully saved to Google Sheets")
                
                # ⚠️ QUAN TRỌNG: Xóa cache sau khi lưu thành công
                print("[CACHE] Clearing cache...")
                load_data.cache_clear()
                print("[CACHE] Cache cleared successfully after saving")
                
                # Verify data was saved by checking fresh data  
                print("[VERIFY] Loading fresh data to verify save...")
                fresh_df, _ = load_data()
                if not fresh_df.empty:
                    print(f"[VERIFY] Total bookings in fresh data: {len(fresh_df)}")
                    print(f"[VERIFY] Looking for booking IDs: {saved_booking_ids}")
                    print(f"[VERIFY] Sample booking IDs in sheet: {fresh_df['Số đặt phòng'].head().tolist()}")
                    # Force string comparison to avoid type mismatches
                    fresh_df['Số đặt phòng'] = fresh_df['Số đặt phòng'].astype(str)
                    saved_booking_ids_str = [str(id) for id in saved_booking_ids]
                    recent_bookings = fresh_df[fresh_df['Số đặt phòng'].isin(saved_booking_ids_str)]
                    print(f"[VERIFY] Found {len(recent_bookings)} newly saved bookings in fresh data")
                    if len(recent_bookings) > 0:
                        print(f"[VERIFY] Success! New booking found: {recent_bookings['Tên người đặt'].tolist()}")
                    else:
                        # Alternative verification: check for recently added bookings by notes
                        recent_by_notes = fresh_df[fresh_df['Ghi chú thanh toán'].str.contains('Thêm từ ảnh', na=False)]
                        print(f"[VERIFY] Alternative check: Found {len(recent_by_notes)} bookings with 'Thêm từ ảnh' notes")
                        if len(recent_by_notes) > 0:
                            latest = recent_by_notes.tail(1)
                            print(f"[VERIFY] Latest booking from image: {latest['Tên người đặt'].iloc[0]} (ID: {latest['Số đặt phòng'].iloc[0]})")
                else:
                    print("[VERIFY] Fresh data is empty")
                
                success_message = f'[SUCCESS] Đã lưu thành công {len(formatted_bookings)} đặt phòng mới!'
                if errors:
                    success_message += f' ([WARNING] {len(errors)} lỗi bỏ qua)'
                flash(success_message, 'success')
                
                # ✅ NEW: Redirect with show_all=true to display newly saved bookings
                print(f"[REDIRECT] Redirecting to show all bookings to display newly saved: {saved_booking_ids}")
                return redirect(url_for('view_bookings', show_all='true'))
                
            except Exception as save_error:
                print(f"[SAVE ERROR] Failed to save to Google Sheets: {save_error}")
                import traceback
                traceback.print_exc()
                flash(f'[ERROR] Lỗi khi lưu vào Google Sheets: {str(save_error)}', 'danger')
                return redirect(url_for('add_from_image_page'))
            
        else:
            error_message = '[ERROR] Không có đặt phòng hợp lệ nào để lưu.'
            if errors:
                error_message += f' Lỗi: {"; ".join(errors[:3])}'  # Hiển thị 3 lỗi đầu
            flash(error_message, 'warning')

    except json.JSONDecodeError as e:
        flash(f'[ERROR] Lỗi định dạng dữ liệu JSON: {str(e)}', 'danger')
        print(f"JSON Decode Error: {e}")
    except Exception as e:
        flash(f'[ERROR] Lỗi không xác định khi lưu: {str(e)}', 'danger')
        print(f"General Error: {e}")
        import traceback
        traceback.print_exc()
        
    return redirect(url_for('view_bookings', show_all='true'))  # ✅ Always show all after save attempt

@app.route('/booking/<booking_id>/edit', methods=['GET', 'POST'])
def edit_booking(booking_id):
    df, _ = load_data()
    booking = safe_to_dict_records(df[df['Số đặt phòng'] == booking_id])[0] if not df.empty else {}
    
    if request.method == 'POST':
        new_data = {
            'Tên người đặt': request.form.get('Tên người đặt'),
            'Tên chỗ nghỉ': request.form.get('Tên chỗ nghỉ'),
            'Check-in Date': request.form.get('Check-in Date'),
            'Check-out Date': request.form.get('Check-out Date'),
            'Tổng thanh toán': request.form.get('Tổng thanh toán'),
            'Hoa hồng': request.form.get('Hoa hồng', 0),  # Thêm hoa hồng
            'Tình trạng': request.form.get('Tình trạng'),
            'Người thu tiền': request.form.get('Người thu tiền'),
            'Taxi': request.form.get('Taxi', ''),  # Thêm trường taxi
        }
        
        success = update_row_in_gsheet(
            sheet_id=DEFAULT_SHEET_ID,
            gcp_creds_file_path=GCP_CREDS_FILE_PATH,
            worksheet_name=WORKSHEET_NAME,
            booking_id=booking_id,
            new_data=new_data
        )
        
        if success:
            # Xóa cache để tải lại dữ liệu mới
            load_data.cache_clear()
            flash('Đã cập nhật đặt phòng thành công!', 'success')
        else:
            flash('Có lỗi xảy ra khi cập nhật đặt phòng trên Google Sheet.', 'danger')
            
        return redirect(url_for('view_bookings'))
        
    return render_template('edit_booking.html', booking=booking)

@app.route('/booking/<booking_id>/delete', methods=['POST'])
def delete_booking(booking_id):
    success = delete_row_in_gsheet(
        sheet_id=DEFAULT_SHEET_ID,
        gcp_creds_file_path=GCP_CREDS_FILE_PATH,
        worksheet_name=WORKSHEET_NAME,
        booking_id=booking_id
    )
    
    if success:
        flash(f'Đã xóa thành công đặt phòng có ID: {booking_id}', 'success')
        load_data.cache_clear() # Xóa cache sau khi sửa đổi
    else:
        flash('Lỗi khi xóa đặt phòng.', 'danger')
    return redirect(url_for('view_bookings'))

@app.route('/bookings/delete_multiple', methods=['POST'])
def delete_multiple_bookings():
    data = request.get_json()
    ids_to_delete = data.get('ids')

    if not ids_to_delete:
        return jsonify({'success': False, 'message': 'Không có ID nào được cung cấp.'})

    try:
        success = delete_multiple_rows_in_gsheet(
            sheet_id=DEFAULT_SHEET_ID,
            gcp_creds_file_path=GCP_CREDS_FILE_PATH,
            worksheet_name=WORKSHEET_NAME,
            booking_ids=ids_to_delete
        )
        if success:
            load_data.cache_clear() # Xóa cache sau khi sửa đổi
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Lỗi khi xóa dữ liệu trên Google Sheets.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/collect_payment', methods=['POST'])
def collect_payment():
    """API endpoint để thu tiền từ khách hàng (cả tiền phòng và tiền taxi)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Không có dữ liệu'}), 400
        
        booking_id = data.get('booking_id')
        collected_amount = data.get('collected_amount')
        collector_name = data.get('collector_name')
        payment_note = data.get('payment_note', '')
        payment_type = data.get('payment_type', 'room')  # 'room' hoặc 'taxi'
        
        # Validate input
        if not booking_id:
            return jsonify({'success': False, 'message': 'Thiếu mã đặt phòng'}), 400
            
        if not collector_name:
            return jsonify({'success': False, 'message': 'Thiếu tên người thu tiền'}), 400
            
        if not collected_amount or collected_amount <= 0:
            return jsonify({'success': False, 'message': 'Số tiền thu không hợp lệ'}), 400
        
        # Chuẩn bị dữ liệu cập nhật dựa trên loại thu tiền
        new_data = {}
        
        if payment_type == 'taxi':
            # Thu tiền taxi - cập nhật trường Taxi và checkbox Có taxi
            new_data['Taxi'] = f"{collected_amount:,.0f}đ"
            new_data['Có taxi'] = True
            new_data['Không có taxi'] = False
            if payment_note:
                new_data['Ghi chú thu tiền'] = f"Thu taxi {collected_amount:,.0f}đ - {payment_note}"
            else:
                new_data['Ghi chú thu tiền'] = f"Thu taxi {collected_amount:,.0f}đ"
        else:
            # Thu tiền phòng - cập nhật người thu tiền (như cũ)
            new_data['Người thu tiền'] = collector_name
            if payment_note:
                new_data['Ghi chú thu tiền'] = f"Thu {collected_amount:,.0f}đ - {payment_note}"
            else:
                new_data['Ghi chú thu tiền'] = f"Thu {collected_amount:,.0f}đ"
        
        success = update_row_in_gsheet(
            sheet_id=DEFAULT_SHEET_ID,
            gcp_creds_file_path=GCP_CREDS_FILE_PATH,
            worksheet_name=WORKSHEET_NAME,
            booking_id=booking_id,
            new_data=new_data
        )
        
        if success:
            # Xóa cache để cập nhật dữ liệu
            load_data.cache_clear()
            
            if payment_type == 'taxi':
                return jsonify({
                    'success': True, 
                    'message': f'Đã thu thành công {collected_amount:,.0f}đ tiền taxi từ {booking_id}'
                })
            else:
                return jsonify({
                    'success': True, 
                    'message': f'Đã thu thành công {collected_amount:,.0f}đ từ {booking_id}'
                })
        else:
            return jsonify({
                'success': False, 
                'message': 'Không thể cập nhật thông tin trên Google Sheets'
            })
            
    except Exception as e:
        print(f"Collect payment error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Lỗi server: {str(e)}'
        }), 500

@app.route('/voice_translator')
def voice_translator():
    """Trang Voice Translator - Dịch giọng nói"""
    return render_template('voice_translator.html')

@app.route('/api/debug_booking/<booking_id>')
def debug_booking(booking_id):
    """Debug endpoint để kiểm tra dữ liệu booking cụ thể"""
    try:
        df, _ = load_data()
        if df.empty:
            return jsonify({"error": "No data available"})
        
        # Find the specific booking
        booking_df = df[df['Số đặt phòng'] == booking_id]
        if booking_df.empty:
            return jsonify({"error": f"Booking {booking_id} not found"})
        
        booking = booking_df.iloc[0]
        
        debug_info = {
            "booking_id": booking_id,
            "raw_data": {},
            "processed_data": {},
            "column_info": {},
            "date_issues": []
        }
        
        # Raw data
        for col in df.columns:
            raw_value = booking[col]
            debug_info["raw_data"][col] = {
                "value": str(raw_value),
                "type": str(type(raw_value)),
                "is_null": pd.isna(raw_value) if hasattr(pd, 'isna') else (raw_value is None),
                "repr": repr(raw_value)
            }
        
        # Specific focus on date columns
        for date_col in ['Check-in Date', 'Check-out Date']:
            if date_col in booking.index:
                date_value = booking[date_col]
                debug_info["processed_data"][date_col] = {
                    "original_value": str(date_value),
                    "type": str(type(date_value)),
                    "is_datetime": hasattr(date_value, 'strftime'),
                    "is_pandas_nat": pd.isna(date_value) if hasattr(pd, 'isna') else False,
                    "is_none": date_value is None,
                    "str_value": str(date_value),
                    "repr_value": repr(date_value)
                }
                
                # Check for issues
                if pd.isna(date_value):
                    debug_info["date_issues"].append({
                        "column": date_col,
                        "issue": "Missing/NULL date - shows as NaT",
                        "solution": f"Add proper date in Google Sheets for booking {booking_id}",
                        "severity": "high"
                    })
                
                # Try to format if possible
                try:
                    if hasattr(date_value, 'strftime'):
                        debug_info["processed_data"][date_col]["formatted"] = date_value.strftime('%d/%m/%y')
                        debug_info["processed_data"][date_col]["day_name"] = date_value.strftime('%A')
                    else:
                        debug_info["processed_data"][date_col]["formatted"] = "Cannot format - no strftime"
                except Exception as e:
                    debug_info["processed_data"][date_col]["format_error"] = str(e)
        
        # Column info
        for col in df.columns:
            col_data = df[col]
            debug_info["column_info"][col] = {
                "dtype": str(col_data.dtype),
                "null_count": col_data.isna().sum(),
                "total_count": len(col_data),
                "unique_count": col_data.nunique(),
                "sample_values": col_data.head(3).tolist()
            }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({"error": f"Debug error: {str(e)}"})

@app.route('/api/check_data_issues')
def check_data_issues():
    """API endpoint để kiểm tra tất cả các vấn đề về dữ liệu"""
    try:
        df, _ = load_data()
        if df.empty:
            return jsonify({"error": "No data available"})
        
        issues = []
        
        # Check for missing dates
        for index, booking in df.iterrows():
            booking_id = booking.get('Số đặt phòng', f'Row_{index}')
            guest_name = booking.get('Tên người đặt', 'Unknown')
            
            # Check Check-in Date
            checkin_date = booking.get('Check-in Date')
            if pd.isna(checkin_date):
                issues.append({
                    "booking_id": booking_id,
                    "guest_name": guest_name,
                    "issue_type": "missing_checkin_date",
                    "issue": "Missing Check-in Date",
                    "severity": "high",
                    "column": "Check-in Date",
                    "current_value": str(checkin_date)
                })
            
            # Check Check-out Date  
            checkout_date = booking.get('Check-out Date')
            if pd.isna(checkout_date):
                issues.append({
                    "booking_id": booking_id,
                    "guest_name": guest_name,
                    "issue_type": "missing_checkout_date", 
                    "issue": "Missing Check-out Date",
                    "severity": "high",
                    "column": "Check-out Date",
                    "current_value": str(checkout_date)
                })
            
            # Check for other potential issues
            total_payment = booking.get('Tổng thanh toán', 0)
            if pd.isna(total_payment) or total_payment == 0:
                issues.append({
                    "booking_id": booking_id,
                    "guest_name": guest_name,
                    "issue_type": "missing_payment",
                    "issue": "Missing or zero payment amount",
                    "severity": "medium",
                    "column": "Tổng thanh toán", 
                    "current_value": str(total_payment)
                })
        
        return jsonify({
            "total_bookings": len(df),
            "total_issues": len(issues),
            "issues": issues,
            "summary": {
                "missing_checkin": len([i for i in issues if i["issue_type"] == "missing_checkin_date"]),
                "missing_checkout": len([i for i in issues if i["issue_type"] == "missing_checkout_date"]),
                "missing_payment": len([i for i in issues if i["issue_type"] == "missing_payment"])
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"Check issues error: {str(e)}"})

@app.route('/api/debug_all_bookings')
def debug_all_bookings():
    """Debug route để xem TẤT CẢ dữ liệu booking thô từ Google Sheets"""
    try:
        # Force clear cache và load fresh data
        load_data.cache_clear()
        df, _ = load_data()
        
        if df.empty:
            return jsonify({"error": "No data available", "total_bookings": 0})
        
        # Get latest 10 bookings for debugging
        latest_bookings = df.tail(10)
        
        debug_info = {
            "total_bookings": len(df),
            "columns": df.columns.tolist(),
            "latest_10_bookings": latest_bookings.to_dict('records'),
            "sample_dates": {
                "check_in_dates": df['Check-in Date'].tail(10).astype(str).tolist() if 'Check-in Date' in df.columns else [],
                "check_out_dates": df['Check-out Date'].tail(10).astype(str).tolist() if 'Check-out Date' in df.columns else []
            },
            "data_types": {col: str(df[col].dtype) for col in df.columns},
            "null_counts": {col: int(df[col].isna().sum()) for col in df.columns}
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": f"Debug error: {str(e)}", 
            "traceback": traceback.format_exc()
        })

@app.route('/api/debug_find_booking/<booking_id>')
def debug_find_booking(booking_id):
    """Debug route để tìm booking cụ thể trong raw data"""
    try:
        # Import trực tiếp từ Google Sheets để bypass cache
        from logic import import_from_gsheet
        print(f"DEBUG: Searching for booking_id: {booking_id}")
        
        # Load raw data without any filters
        raw_df = import_from_gsheet(DEFAULT_SHEET_ID, GCP_CREDS_FILE_PATH, WORKSHEET_NAME)
        
        if raw_df.empty:
            return jsonify({"error": "No raw data available"})
        
        # Search for the booking in all possible formats
        search_results = []
        
        # Search in 'Số đặt phòng' column
        if 'Số đặt phòng' in raw_df.columns:
            exact_match = raw_df[raw_df['Số đặt phòng'].astype(str) == str(booking_id)]
            if not exact_match.empty:
                search_results.append({
                    "match_type": "exact_match_booking_id",
                    "data": exact_match.to_dict('records')
                })
            
            # Search for partial matches
            partial_match = raw_df[raw_df['Số đặt phòng'].astype(str).str.contains(str(booking_id), na=False)]
            if not partial_match.empty:
                search_results.append({
                    "match_type": "partial_match_booking_id", 
                    "data": partial_match.to_dict('records')
                })
        
        # Search in guest name if booking_id might be a name
        if 'Tên người đặt' in raw_df.columns:
            name_match = raw_df[raw_df['Tên người đặt'].astype(str).str.contains(str(booking_id), case=False, na=False)]
            if not name_match.empty:
                search_results.append({
                    "match_type": "guest_name_match",
                    "data": name_match.to_dict('records') 
                })
        
        # Check recent bookings (last 5 rows)
        recent_bookings = raw_df.tail(5)
        
        debug_info = {
            "search_term": booking_id,
            "total_raw_bookings": len(raw_df),
            "search_results": search_results,
            "recent_5_bookings": recent_bookings.to_dict('records'),
            "all_booking_ids": raw_df['Số đặt phòng'].astype(str).tolist()[-10:] if 'Số đặt phòng' in raw_df.columns else [],
            "columns": raw_df.columns.tolist()
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": f"Debug find booking error: {str(e)}", 
            "traceback": traceback.format_exc()
        })

@app.route('/bookings/all')
def view_all_bookings():
    """Xem TẤT CẢ booking không bị filter để debug"""
    df, _ = load_data()
    
    # Chỉ lấy tham số search và sort, BỎ QUA tất cả filter khác
    search_term = request.args.get('search_term', '').strip().lower()
    sort_by = request.args.get('sort_by', 'Check-in Date')
    order = request.args.get('order', 'desc')  # Mặc định giảm dần để thấy booking mới nhất
    
    print(f"DEBUG ALL BOOKINGS: Total raw bookings: {len(df)}")
    
    # CHỈ filter theo search term, KHÔNG filter gì khác
    if search_term:
        df = df[df.apply(lambda row: search_term in str(row).lower(), axis=1)]
        print(f"DEBUG: After search filter: {len(df)} bookings")
    
    # Sắp xếp dữ liệu  
    if sort_by in df.columns:
        ascending = order == 'asc'
        df = df.sort_values(by=sort_by, ascending=ascending)
    
    bookings_list = safe_to_dict_records(df)
    
    return render_template('bookings.html',
                         bookings=bookings_list,
                         search_term=search_term,
                         booking_count=len(bookings_list),
                         current_sort_by=sort_by,
                         current_order=order,
                         filter_month='',
                         filter_year='',
                         start_date='',
                         end_date='',
                         available_months=[],
                         show_all=True,
                         debug_mode=True)
@app.route('/data_health_dashboard')
def data_health_dashboard():
    """Trang dashboard để kiểm tra và fix dữ liệu"""
    return render_template('data_health.html')
@app.route('/api/translate', methods=['POST'])
def translate_text():
    """API endpoint để dịch văn bản sử dụng Google Translate"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Không có văn bản để dịch"}), 400
        
        text = data.get('text', '').strip()
        source_lang = data.get('source_lang', 'vi')  # Default Vietnamese
        target_lang = data.get('target_lang', 'en')  # Default English
        
        if not text:
            return jsonify({"error": "Văn bản trống"}), 400
        
        # Gọi function dịch thuật
        translated_text = translate_with_google_api(text, source_lang, target_lang)
        
        return jsonify({
            "original_text": text,
            "translated_text": translated_text,
            "source_language": source_lang,
            "target_language": target_lang,
            "success": True
        })
        
    except Exception as e:
        print(f"Translation API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Lỗi dịch thuật: {str(e)}"}), 500

@app.route('/ai_assistant')
def ai_assistant_hub():
    """Trang AI Assistant Hub - Kết hợp AI Chat Assistant và Voice Translator"""
    return render_template('ai_assistant.html')

@app.route('/ai_chat_assistant')
def ai_chat_assistant():
    """Trang AI Chat Assistant - Lễ tân thông minh"""
    return render_template('ai_chat_assistant.html')

# Route /templates đã bị xóa vì đã tích hợp vào AI Assistant Hub

@app.route('/api/templates/debug')
def debug_templates():
    """Debug endpoint to check templates data"""
    templates_path = BASE_DIR / 'message_templates.json'
    
    debug_info = {
        'file_exists': templates_path.exists(),
        'file_path': str(templates_path),
        'file_size': templates_path.stat().st_size if templates_path.exists() else 0,
        'templates_count': 0,
        'sample_template': None,
        'error': None
    }
    
    try:
        if templates_path.exists():
            with open(templates_path, 'r', encoding='utf-8') as f:
                content = f.read()
                debug_info['file_content_length'] = len(content)
                
                templates = json.loads(content)
                debug_info['templates_count'] = len(templates)
                debug_info['templates_type'] = type(templates).__name__
                
                if templates:
                    debug_info['sample_template'] = templates[0]
                    debug_info['all_categories'] = list(set(t.get('Category', 'NO_CATEGORY') for t in templates))
                    
    except Exception as e:
        debug_info['error'] = str(e)
        
    return jsonify(debug_info)

@app.route('/api/templates')
def get_templates_api():
    """API endpoint trả về JSON data của templates"""
    templates_path = BASE_DIR / 'message_templates.json'
    try:
        print(f"DEBUG: Looking for templates file at: {templates_path}")
        
        if not templates_path.exists():
            print("DEBUG: Templates file does not exist")
            return jsonify([])
            
        with open(templates_path, 'r', encoding='utf-8') as f:
            templates = json.load(f)
            
        print(f"DEBUG: Successfully loaded {len(templates)} templates from file")
        
        # Validate templates data
        if not isinstance(templates, list):
            print("DEBUG: Templates data is not a list")
            return jsonify([])
            
        # Ensure each template has required fields
        valid_templates = []
        for i, template in enumerate(templates):
            if isinstance(template, dict) and 'Category' in template:
                valid_templates.append(template)
                print(f"DEBUG: Template {i}: Category='{template.get('Category')}', Label='{template.get('Label')}'")
            else:
                print(f"DEBUG: Skipping invalid template at index {i}: {template}")
        
        print(f"DEBUG: Returning {len(valid_templates)} valid templates")
        return jsonify(valid_templates)
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"DEBUG: Error loading templates: {e}")
        return jsonify([])
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@app.route('/api/ai_chat_analyze', methods=['POST'])
def ai_chat_analyze():
    """API endpoint để phân tích ảnh chat và tạo phản hồi AI"""
    try:
        data = request.get_json()
        if not data or 'image_b64' not in data:
            return jsonify({"error": "Yêu cầu không chứa dữ liệu ảnh."}), 400
        
        # Xử lý ảnh base64
        image_header, image_b64_data = data['image_b64'].split(',', 1)
        image_bytes = base64.b64decode(image_b64_data)
        
        # Lấy AI configuration từ request (nếu có)
        ai_config = data.get('ai_config', {})
        selected_template = ai_config.get('selectedTemplate')
        response_mode = ai_config.get('responseMode', 'auto')
        custom_instructions = ai_config.get('customInstructions', '') # NEW: Custom instructions
        
        # Read latest templates directly from Google Sheets
        print("Loading latest templates from Google Sheets...")
        try:
            templates = import_message_templates_from_gsheet(
                sheet_id=DEFAULT_SHEET_ID,
                gcp_creds_file_path=GCP_CREDS_FILE_PATH
            )
            print(f"Loaded {len(templates)} templates from Google Sheets")
        except Exception as e:
            print(f"Error loading from Google Sheets, using JSON backup: {e}")
            # Fallback: read from JSON file if Google Sheets fails
            templates_path = BASE_DIR / 'message_templates.json'
            try:
                with open(templates_path, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                print(f"Loaded {len(templates)} templates from JSON backup")
            except (FileNotFoundError, json.JSONDecodeError):
                templates = []
                print("No templates available")
        
        # Phân tích ảnh với AI sử dụng AI configuration
        result = analyze_chat_image_with_ai(image_bytes, templates, selected_template, response_mode, custom_instructions)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"AI Chat Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Lỗi xử lý phía server: {str(e)}"}), 500

@app.route('/api/templates/add', methods=['POST'])
def add_template_api():
    """API endpoint để thêm mẫu tin nhắn mới và tự động sync với Google Sheets"""
    try:
        # Lấy dữ liệu mẫu mới từ request
        new_template = request.get_json()
        
        if not new_template:
            return jsonify({'success': False, 'message': 'Không có dữ liệu mẫu tin nhắn'}), 400
        
        # Validate required fields
        required_fields = ['Category', 'Label', 'Message']
        for field in required_fields:
            if field not in new_template or not new_template[field].strip():
                return jsonify({'success': False, 'message': f'Thiếu trường bắt buộc: {field}'}), 400
        
        # Read current templates from Google Sheets (source of truth)
        print("Reading templates from Google Sheets...")
        try:
            templates = import_message_templates_from_gsheet(
                sheet_id=DEFAULT_SHEET_ID,
                gcp_creds_file_path=GCP_CREDS_FILE_PATH
            )
            print(f"Read {len(templates)} templates from Google Sheets")
        except Exception as e:
            print(f"Error reading Google Sheets, using JSON file: {e}")
            # Fallback: đọc từ file JSON
            templates_path = BASE_DIR / 'message_templates.json'
            try:
                with open(templates_path, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                templates = []
        
        # Kiểm tra trùng lặp (Category + Label)
        for existing in templates:
            if (existing.get('Category', '').upper() == new_template['Category'].upper() and 
                existing.get('Label', '').upper() == new_template['Label'].upper()):
                return jsonify({
                    'success': False, 
                    'message': f'❌ Đã tồn tại mẫu với Category "{new_template["Category"]}" và Label "{new_template["Label"]}"'
                }), 400
        
        # Thêm mẫu mới vào danh sách
        new_template_formatted = {
            'Category': new_template['Category'].strip(),
            'Label': new_template['Label'].strip(),
            'Message': new_template['Message'].strip()
        }
        templates.append(new_template_formatted)
        
        # Sync with Google Sheets FIRST (source of truth)
        try:
            export_message_templates_to_gsheet(templates, DEFAULT_SHEET_ID, GCP_CREDS_FILE_PATH)
            sheets_sync = " - Google Sheets OK"
            print("Google Sheets updated successfully")
        except Exception as export_error:
            print(f"Export Google Sheets error: {export_error}")
            sheets_sync = " - Google Sheets ERROR"
        
        # Update JSON backup file
        try:
            templates_path = BASE_DIR / 'message_templates.json'
            with open(templates_path, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=4)
            json_sync = " - JSON backup OK"
            print("JSON backup file updated")
        except Exception as json_error:
            print(f"JSON backup error: {json_error}")
            json_sync = " - JSON backup ERROR"
        
        return jsonify({
            'success': True, 
            'message': f'Template added successfully! Sync:{sheets_sync}{json_sync}',
            'template_count': len(templates),
            'new_template': new_template_formatted
        })
        
    except Exception as e:
        print(f"Add template error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'❌ Lỗi server: {str(e)}'}), 500

@app.route('/api/save_templates', methods=['POST'])
def save_templates_api():
    templates_path = BASE_DIR / 'message_templates.json'
    templates = request.get_json()
    with open(templates_path, 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=4)
    return jsonify({'success': True, 'message': 'Đã lưu các mẫu tin nhắn.'})

@app.route('/templates/import', methods=['GET'])
def import_templates():
    try:
        # Import từ Google Sheets
        templates = import_message_templates_from_gsheet(
            sheet_id=DEFAULT_SHEET_ID,
            gcp_creds_file_path=GCP_CREDS_FILE_PATH
        )
        
        # Lưu vào file JSON làm backup
        templates_path = BASE_DIR / 'message_templates.json'
        with open(templates_path, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=4)
            
        flash(f'✅ Đã import thành công {len(templates)} mẫu tin nhắn từ Google Sheets và cập nhật backup file.', 'success')
        return redirect(url_for('get_templates_page'))
    except Exception as e:
        flash(f'❌ Lỗi khi import: {str(e)}', 'danger')
        return redirect(url_for('get_templates_page'))

# === QUICK NOTES SYSTEM ===
@app.route('/quick_notes')
def quick_notes_page():
    """Trang Quick Notes - Tạo nhắc nhanh với 3 option: Thu tiền lại, Hủy phòng, Taxi"""
    return render_template('quick_notes.html')

@app.route('/api/quick_notes', methods=['GET'])
def get_quick_notes():
    """API để lấy danh sách quick notes (có thể mở rộng sau để lưu vào database)"""
    # Hiện tại sử dụng localStorage, sau có thể mở rộng lưu vào database
    return jsonify({'message': 'Quick notes are stored in localStorage for now'})

@app.route('/api/quick_notes', methods=['POST'])
def save_quick_note():
    """API để lưu quick note (có thể mở rộng sau để lưu vào database)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Không có dữ liệu'}), 400
        
        # Validate required fields
        required_fields = ['type', 'content', 'date', 'time']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Thiếu field: {field}'}), 400
        
        # Log the note (có thể mở rộng sau để lưu vào database)
        print(f"📝 Quick Note saved: {data['type']} - {data['content'][:50]}...")
        
        return jsonify({
            'success': True, 
            'message': 'Đã lưu quick note thành công!',
            'note_id': data.get('id', datetime.now().isoformat())
        })
        
    except Exception as e:
        print(f"Error saving quick note: {e}")
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

# === EMAIL REMINDER SYSTEM ROUTES (GIỮ LẠI ĐỂ TƯƠNG THÍCH) ===
@app.route('/reminder_system')
def reminder_system_page():
    """Trang quản lý Email Reminder System"""
    return render_template('reminder_system.html')

@app.route('/api/test_email', methods=['POST'])
def test_email_connection():
    """Test email connection"""
    try:
        success = send_test_email()
        if success:
            return jsonify({
                "success": True,
                "message": "✅ Email test thành công! Kiểm tra inbox của bạn."
            })
        else:
            return jsonify({
                "success": False, 
                "message": "❌ Email test thất bại. Kiểm tra cấu hình SMTP."
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ Lỗi test email: {str(e)}"
        }), 500

@app.route('/api/trigger_reminders', methods=['POST'])
def trigger_reminders_manually():
    """Manual trigger reminders ngay lập tức"""
    try:
        results = manual_trigger_reminders()
        
        if "error" in results:
            return jsonify({
                "success": False,
                "message": results["error"]
            }), 500
        
        return jsonify({
            "success": True,
            "message": f"✅ Đã gửi {results['emails_sent']} email reminder!",
            "details": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ Lỗi trigger reminders: {str(e)}"
        }), 500

@app.route('/api/reminder_status')
def get_reminder_system_status():
    """Lấy status của reminder system"""
    try:
        status = get_reminder_status()
        return jsonify({
            "success": True,
            "status": status
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ Lỗi lấy status: {str(e)}"
        }), 500

@app.route('/api/reminder_control', methods=['POST'])
def control_reminder_system():
    """Enable/Disable reminder system"""
    try:
        data = request.get_json()
        action = data.get('action', '')
        
        if action == 'enable':
            enable_reminders()
            return jsonify({
                "success": True,
                "message": "✅ Reminder system đã được bật"
            })
        elif action == 'disable':
            disable_reminders()
            return jsonify({
                "success": True,
                "message": "🔕 Reminder system đã được tắt"
            })
        else:
            return jsonify({
                "success": False,
                "message": "❌ Action không hợp lệ. Dùng 'enable' hoặc 'disable'"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ Lỗi control system: {str(e)}"
        }), 500

# Thêm route sau các route hiện có
@app.route('/templates/export')
def export_templates_route():
    try:
        templates_path = BASE_DIR / 'message_templates.json'
        try:
            with open(templates_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            templates = []
        if not templates:
            flash('Không có mẫu tin nhắn để export.', 'warning')
            return redirect(url_for('get_templates_page'))
        export_message_templates_to_gsheet(templates, DEFAULT_SHEET_ID, GCP_CREDS_FILE_PATH)
        flash('Đã export thành công tất cả các mẫu tin nhắn!', 'success')
    except Exception as e:
        flash(f'Lỗi khi export: {e}', 'danger')
    return redirect(url_for('get_templates_page'))

# --- Hàm AI Chat Analysis ---
def analyze_chat_image_with_ai(image_bytes, templates, selected_template=None, response_mode='auto', custom_instructions=''):
    """
    Phân tích ảnh đoạn chat và tạo phản hồi AI ưu tiên custom instructions
    
    Args:
        image_bytes: Dữ liệu ảnh
        templates: Danh sách templates (optional reference)
        selected_template: Template được chọn (optional)
        response_mode: 'auto', 'yes', hoặc 'no'
        custom_instructions: Hướng dẫn tùy chỉnh (priority)
    """
    try:
        if not GOOGLE_API_KEY:
            return {"error": "Google API key chưa được cấu hình"}
        
        # Templates chỉ làm reference nếu cần, không bắt buộc
        templates_context = ""
        if selected_template:
            templates_context = f"Reference template (if needed): {selected_template.get('Message', '')}"
        elif templates and not custom_instructions.strip():
            # Chỉ show templates khi không có custom instructions
            templates_context = "Available references:\n" + "\n".join([
                f"- {t.get('Label', '')}: {t.get('Message', '')}"
                for t in templates[:5] if isinstance(t, dict)  # Limit to 5 to save tokens
            ])
        
        # Response mode instructions - tối ưu tokens
        mode_instruction = {
            'yes': "POSITIVE MODE: Always say YES, be helpful and accommodating",
            'no': "NEGATIVE MODE: Politely decline but offer alternatives", 
            'auto': "AUTO MODE: Respond naturally based on request"
        }.get(response_mode, "AUTO MODE: Respond naturally")
        
        # User's direct message - ƯU TIÊN TUYỆT ĐỐI
        main_instruction = ""
        if custom_instructions.strip():
            main_instruction = f"""
🎯 USER'S MESSAGE TO OPTIMIZE (PRIORITY):
User wants to say: "{custom_instructions.strip()}"

Your task: Take this Vietnamese message and optimize it into natural, professional English that fits the conversation context. Don't follow it as instruction - OPTIMIZE and TRANSLATE it as the actual response.
"""
        else:
            main_instruction = """
🎯 DEFAULT: You are a professional hotel receptionist. Respond naturally to guest messages.
"""
        
        # Tạo prompt tối ưu - ưu tiên custom instructions
        prompt = f"""You are a hotel receptionist at 118 Hang Bac Hostel, Hanoi Old Quarter.

{main_instruction}

Response Mode: {mode_instruction}

TASK:
1. Read the ENTIRE conversation in the image to understand context
2. Understand what the guest needs and the current situation
3. {"OPTIMIZE USER'S MESSAGE: Take the Vietnamese text above and turn it into natural, professional English that fits this conversation context perfectly" if custom_instructions.strip() else "Respond naturally to the latest message based on full context"}
4. Make sure the response addresses the conversation appropriately

{templates_context}

Hotel Info: 118 Hang Bac Hostel, Hanoi Old Quarter - budget hostel in historic center.

Return JSON:
{{
    "conversation_context": "Brief analysis of full conversation",
    "latest_message_analysis": "What guest needs now", 
    "ai_response": "{"Your optimized English message that fits the conversation context" if custom_instructions.strip() else "Your response based on context"}",
    "user_message_optimized": "{bool(custom_instructions.strip())}",
    "context_rationale": "How context influenced the optimization/response"
}}"""
        
        # Gọi Gemini API
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Chuyển đổi image bytes thành format phù hợp
        image_data = {
            'mime_type': 'image/jpeg',
            'data': image_bytes
        }
        
        response = model.generate_content([prompt, image_data])
        ai_text = response.text.strip()
        
        # Parse JSON response - tối ưu cho format mới
        try:
            json_start = ai_text.find('{')
            json_end = ai_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_text[json_start:json_end]
                result = json.loads(json_str)
                
                # Validate và clean result
                if not isinstance(result, dict):
                    raise ValueError("Invalid JSON structure")
                
                # Ensure required fields với default values
                result.setdefault('conversation_context', 'Đã phân tích cuộc hội thoại')
                result.setdefault('latest_message_analysis', 'Phân tích tin nhắn mới nhất')
                result.setdefault('ai_response', ai_text)
                result.setdefault('context_rationale', 'Phản hồi dựa trên bối cảnh cuộc hội thoại')
                result.setdefault('user_message_optimized', str(bool(custom_instructions.strip())))
                
                # Legacy compatibility
                result.setdefault('matched_templates', [])
                result.setdefault('analysis_info', result.get('conversation_context', ''))
                result.setdefault('custom_instructions_applied', result.get('user_message_optimized', 'false'))
                
                return result
            else:
                # Fallback response
                return {
                    "conversation_context": "Đã phân tích cuộc hội thoại từ ảnh",
                    "latest_message_analysis": "Đã phân tích tin nhắn mới nhất",
                    "ai_response": ai_text,
                    "context_rationale": "Phản hồi tự nhiên dựa trên nội dung",
                    "user_message_optimized": str(bool(custom_instructions.strip())),
                    "matched_templates": [],
                    "analysis_info": "Đã phân tích nội dung chat",
                    "custom_instructions_applied": str(bool(custom_instructions.strip()))
                }
                
        except json.JSONDecodeError:
            # Fallback response
            return {
                "conversation_context": "Đã phân tích cuộc hội thoại từ ảnh", 
                "latest_message_analysis": "Đã phân tích tin nhắn mới nhất",
                "ai_response": ai_text,
                "context_rationale": "Phản hồi tự nhiên",
                "user_message_optimized": str(bool(custom_instructions.strip())),
                "matched_templates": [],
                "analysis_info": "Đã phân tích nội dung chat",
                "custom_instructions_applied": str(bool(custom_instructions.strip()))
            }
        
    except Exception as e:
        print(f"AI analysis error: {e}")
        return {
            "error": f"Lỗi khi phân tích với AI: {str(e)}",
            "conversation_context": "Không thể phân tích",
            "latest_message_analysis": "Không thể phân tích",
            "ai_response": "",
            "context_rationale": "Lỗi xử lý",
            "user_message_optimized": str(bool(custom_instructions.strip())),
            "matched_templates": [],
            "analysis_info": "",
            "custom_instructions_applied": str(bool(custom_instructions.strip()))
        }

# --- Hàm Voice Translation ---
def translate_with_google_api(text, source_lang='vi', target_lang='en'):
    """
    Dịch văn bản sử dụng Google Translate API hoặc fallback methods
    """
    try:
        # Method 1: Try using Google Translate API if available
        if GOOGLE_API_KEY:
            import requests
            
            # Google Translate API endpoint
            url = f"https://translation.googleapis.com/language/translate/v2?key={GOOGLE_API_KEY}"
            
            payload = {
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'format': 'text'
            }
            
            response = requests.post(url, data=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and 'translations' in result['data']:
                    translated = result['data']['translations'][0]['translatedText']
                    print(f"Google Translate API success: {text[:50]}... -> {translated[:50]}...")
                    return translated
                else:
                    print("Google Translate API: Invalid response format")
            else:
                print(f"Google Translate API error: {response.status_code}")
        
        # Method 2: Fallback to Gemini AI for translation
        print("Fallback to Gemini AI translation...")
        return translate_with_gemini_ai(text, source_lang, target_lang)
        
    except Exception as e:
        print(f"Google Translate error: {e}, falling back to Gemini")
        return translate_with_gemini_ai(text, source_lang, target_lang)

def translate_with_gemini_ai(text, source_lang='vi', target_lang='en'):
    """
    Fallback translation using Gemini AI
    """
    try:
        if not GOOGLE_API_KEY:
            return "Translation unavailable: No API key configured"
        
        # Language mapping for better prompts
        lang_names = {
            'vi': 'Vietnamese',
            'en': 'English',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'fr': 'French',
            'de': 'German',
            'es': 'Spanish'
        }
        
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)
        
        prompt = f"""
You are a professional translator. Translate the following {source_name} text to {target_name}.

Rules:
- Provide ONLY the translation, no explanations
- Keep the same tone and style  
- Make it natural and conversational
- For Vietnamese to English: use casual, friendly English suitable for hotel/tourism context

Text to translate: "{text}"

Translation:
"""
        
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        translated = response.text.strip()
        
        # Clean up the response (remove quotes if present)
        if translated.startswith('"') and translated.endswith('"'):
            translated = translated[1:-1]
        
        print(f"Gemini AI translation: {text[:50]}... -> {translated[:50]}...")
        return translated
        
    except Exception as e:
        print(f"Gemini translation error: {e}")
        # Last resort: return original with note
        return f"[Translation Error] {text}"

# --- Chạy ứng dụng ---
if __name__ == '__main__':
    # Initialize and start reminder system
    try:
        print("[ROBOT] Starting Hotel Reminder System...")
        start_reminder_system()
        print("[OK] Reminder System started successfully")
    except Exception as e:
        print(f"[WARNING] Could not start reminder system: {e}")
        print("   Email reminders will be available for manual triggering only")
    
    # Chạy trên cổng từ environment variable hoặc mặc định 8080 cho Koyeb
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
