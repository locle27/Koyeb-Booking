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

# --- Production Mode Only ---
# Development toolbar and debug mode completely removed
# --------------------

# Import các hàm logic
from logic import (
    import_from_gsheet, create_demo_data,
    get_daily_activity, get_overall_calendar_day_info,
    extract_booking_info_from_image_content,
    check_duplicate_guests, analyze_existing_duplicates,
    export_data_to_new_sheet,
    append_multiple_bookings_to_sheet,
    delete_booking_by_id, update_row_in_gsheet,
    prepare_dashboard_data, delete_row_in_gsheet,
    delete_multiple_rows_in_gsheet,
    import_message_templates_from_gsheet,
    export_message_templates_to_gsheet,
    scrape_booking_apartments, format_apartments_display,
    add_expense_to_sheet, get_expenses_from_sheet
)

# Import dashboard logic module
from dashboard_routes import process_dashboard_data, safe_to_dict_records

# Email & Reminder System imports removed per user request

# Cấu hình
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, template_folder=BASE_DIR / "templates", static_folder=BASE_DIR / "static")

# Production configuration
app.config['ENV'] = 'production'
app.config['DEBUG'] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_default_secret_key_for_development")

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
    
    # === AUTO DUPLICATE FILTERING ===
    auto_filter_duplicates = request.args.get('auto_filter', 'true').lower() == 'true'
    duplicate_report = {"duplicate_groups": [], "total_groups": 0, "total_duplicates": 0}
    filtered_booking_ids = set()
    
    if auto_filter_duplicates:
        try:
            # Get duplicate analysis
            duplicate_report = analyze_existing_duplicates()
            
            # Extract all duplicate booking IDs to filter out
            for group in duplicate_report.get("duplicate_groups", []):
                # Keep main booking, filter out similar ones
                for similar_booking in group.get("similar_bookings", []):
                    filtered_booking_ids.add(similar_booking["booking_id"])
            
            # Filter duplicates from the main booking list
            if filtered_booking_ids and not df.empty:
                original_count = len(df)
                df = df[~df['Số đặt phòng'].isin(filtered_booking_ids)]
                print(f"DEBUG: Auto-filtered {original_count - len(df)} duplicate bookings")
        except Exception as e:
            print(f"ERROR: Failed to auto-filter duplicates: {e}")
    
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
                         show_all=show_all,
                         auto_filter_duplicates=auto_filter_duplicates,
                         duplicate_report=duplicate_report,
                         filtered_count=len(filtered_booking_ids))

@app.route('/calendar/')
def calendar_view():
    """Revenue Calendar - shows daily totals"""
    try:
        df, _ = load_data()
        
        # Get daily totals using the function from dashboard_routes
        from dashboard_routes import get_daily_totals
        daily_totals = get_daily_totals(df)
        
        return render_template(
            'calendar.html',
            daily_totals=daily_totals
        )
    except Exception as e:
        print(f"Calendar error: {e}")
        flash(f"Lỗi tải calendar: {e}", "danger")
        return redirect(url_for('dashboard'))

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
    
# Combined with add_booking route for unified experience

@app.route('/bookings/add', methods=['GET', 'POST'])
def add_booking():
    """Add new booking manually with duplicate detection"""
    if request.method == 'GET':
        return render_template('add_booking.html')
    
    try:
        # Get form data
        form_data = request.form.to_dict()
        print(f"[ADD_BOOKING] Received form data: {form_data}")
        
        # Convert form data to booking format for duplicate check
        booking_data = {
            'guest_name': form_data.get('Tên người đặt', '').strip(),
            'check_in_date': form_data.get('Ngày đến', ''),
            'check_out_date': form_data.get('Ngày đi', ''),
            'room_type': form_data.get('Tên chỗ nghỉ', ''),
            'booking_id': form_data.get('Số đặt phòng', ''),
            'total_payment': float(form_data.get('Tổng thanh toán', 0))
        }
        
        # Check for duplicates BEFORE saving
        print(f"[DUPLICATE_CHECK] Checking for duplicates...")
        duplicate_check = check_duplicate_guests([booking_data])
        
        if duplicate_check['has_duplicates']:
            # Format duplicate warning message
            duplicate_guest = duplicate_check['duplicates'][0]
            existing = duplicate_guest['existing_booking']
            
            flash(f'⚠️ CẢNH BÁO: Khách "{booking_data["guest_name"]}" có thể đã tồn tại!\n'
                  f'🔍 Khách hiện tại: ID {existing["booking_id"]}, Check-in: {existing["check_in_date"]}\n'
                  f'❓ Bạn có chắc muốn thêm booking này không?', 'warning')
            
            # Add force parameter to bypass duplicate check if user confirms
            if not request.form.get('force_add'):
                return render_template('add_booking.html', 
                                     form_data=form_data, 
                                     duplicate_warning=duplicate_check)
        
        # Generate auto booking ID and current date
        import random
        current_date = datetime.now().strftime('%Y-%m-%d')
        auto_booking_id = f"MANUAL_{datetime.now().strftime('%Y%m%d')}_{random.randint(1000, 9999)}"
        
        # Prepare data for Google Sheets
        formatted_booking = {
            'Tên người đặt': form_data.get('Tên người đặt', ''),
            'Số đặt phòng': auto_booking_id,
            'Tên chỗ nghỉ': '118 Hang Bac Hostel',
            'Check-in Date': form_data.get('Ngày đến', ''),
            'Check-out Date': form_data.get('Ngày đi', ''),
            'Được đặt vào': current_date,
            'Tổng thanh toán': float(form_data.get('Tổng thanh toán', 0)),
            'Hoa hồng': float(form_data.get('Hoa hồng', 0)),
            'Tình trạng': form_data.get('Tình trạng', 'OK'),
            'Người thu tiền': form_data.get('Người thu tiền', ''),
            'Tiền tệ': 'VND',
            'Vị trí': 'Hà Nội',
            'Thành viên Genius': 'Không'
        }
        
        # Save to Google Sheets
        print(f"[SAVE] Saving single booking to sheets...")
        append_multiple_bookings_to_sheet(
            bookings=[formatted_booking],
            gcp_creds_file_path=GCP_CREDS_FILE_PATH,
            sheet_id=DEFAULT_SHEET_ID,
            worksheet_name=WORKSHEET_NAME
        )
        
        # Clear cache
        load_data.cache_clear()
        
        flash(f'✅ Đã thêm booking thành công: {booking_data["guest_name"]} ({auto_booking_id})', 'success')
        return redirect(url_for('view_bookings'))
        
    except Exception as e:
        print(f"[ERROR] Failed to add booking: {e}")
        flash(f'❌ Lỗi khi thêm booking: {str(e)}', 'danger')
        return render_template('add_booking.html', form_data=request.form.to_dict())

@app.route('/bookings/add_from_image')
def add_from_image_page():
    """Route to serve the add from image page for multi-booking extraction"""
    return render_template('add_from_image.html')

@app.route('/api/analyze_duplicates', methods=['GET'])
def api_analyze_duplicates():
    """API endpoint để phân tích duplicate bookings hiện có"""
    try:
        print("[API] 🔍 Analyzing existing duplicates...")
        duplicate_analysis = analyze_existing_duplicates()
        
        return jsonify({
            "success": True,
            "data": duplicate_analysis,
            "message": f"Tìm thấy {duplicate_analysis['total_groups']} nhóm trùng lặp với tổng {duplicate_analysis['total_duplicates']} booking"
        })
        
    except Exception as e:
        print(f"[ERROR] Failed to analyze duplicates: {e}")
        return jsonify({
            "success": False,
            "message": f"Lỗi phân tích: {str(e)}"
        }), 500

@app.route('/api/process_pasted_image', methods=['POST'])
def process_pasted_image():
    data = request.get_json()
    if not data or 'image_b64' not in data:
        return jsonify({"error": "Yêu cầu không chứa dữ liệu ảnh."}), 400
    try:
        image_header, image_b64_data = data['image_b64'].split(',', 1)
        image_bytes = base64.b64decode(image_b64_data)
        extracted_data = extract_booking_info_from_image_content(image_bytes)
        
        # Kiểm tra trùng lặp nếu có dữ liệu hợp lệ
        if extracted_data and isinstance(extracted_data, list) and len(extracted_data) > 0:
            # Lọc bỏ các booking có lỗi
            valid_bookings = [b for b in extracted_data if not b.get('error')]
            if valid_bookings:
                duplicate_check = check_duplicate_guests(valid_bookings)
                return jsonify({
                    "bookings": extracted_data,
                    "duplicate_check": duplicate_check
                })
        
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
        # 🚨 FIXED: Only update amount fields, NOT customer info
        new_data = {}
        
        # Only update payment amounts, never overwrite customer data
        total_amount = request.form.get('Tổng thanh toán')
        if total_amount:
            new_data['Tổng thanh toán'] = total_amount
            
        taxi_amount = request.form.get('Taxi')
        if taxi_amount:
            new_data['Taxi'] = taxi_amount
            
        commission = request.form.get('Hoa hồng')
        if commission:
            new_data['Hoa hồng'] = commission
            
        # Only update collector if provided
        collector = request.form.get('Người thu tiền')
        if collector:
            new_data['Người thu tiền'] = collector
            
        print(f"[EDIT_BOOKING] FIXED - Only updating: {new_data}")
        
        if not new_data:
            flash('Không có dữ liệu nào để cập nhật.', 'warning')
            return redirect(url_for('view_bookings'))
        
        success = update_row_in_gsheet(
            sheet_id=DEFAULT_SHEET_ID,
            gcp_creds_file_path=GCP_CREDS_FILE_PATH,
            worksheet_name=WORKSHEET_NAME,
            booking_id=booking_id,
            new_data=new_data
        )
        
        if success:
            # ⚠️ CRITICAL: Force clear ALL caches for dashboard update
            load_data.cache_clear()
            print(f"[EDIT_TAXI] Cache cleared after updating taxi fare for {booking_id}")
            
            # Verify data is actually updated
            fresh_df, _ = load_data()
            updated_booking = fresh_df[fresh_df['Số đặt phòng'] == booking_id]
            if not updated_booking.empty:
                new_taxi = updated_booking.iloc[0].get('Taxi', '')
                print(f"[EDIT_TAXI] Verified update: booking {booking_id} taxi = {new_taxi}")
            
            flash('✅ Đã cập nhật số tiền thành công! Dashboard sẽ tự động cập nhật.', 'success')
        else:
            flash('❌ Có lỗi xảy ra khi cập nhật đặt phòng trên Google Sheet.', 'danger')
            
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

@app.route('/api/delete_booking/<booking_id>', methods=['DELETE'])
def api_delete_booking(booking_id):
    """API endpoint for deleting bookings (returns JSON)"""
    try:
        success = delete_row_in_gsheet(
            sheet_id=DEFAULT_SHEET_ID,
            gcp_creds_file_path=GCP_CREDS_FILE_PATH,
            worksheet_name=WORKSHEET_NAME,
            booking_id=booking_id
        )
        
        if success:
            load_data.cache_clear() # Clear cache after modification
            return jsonify({
                'success': True, 
                'message': f'Successfully deleted booking ID: {booking_id}'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Failed to delete booking'
            }), 400
            
    except Exception as e:
        print(f"[ERROR] API delete booking failed: {e}")
        return jsonify({
            'success': False, 
            'message': f'Error deleting booking: {str(e)}'
        }), 500

@app.route('/bookings/delete_multiple', methods=['POST'])
def delete_multiple_bookings():
    try:
        print(f"[DELETE_MULTIPLE] Received request")
        data = request.get_json()
        print(f"[DELETE_MULTIPLE] Request data: {data}")
        
        if not data:
            print("[DELETE_MULTIPLE] No JSON data received")
            return jsonify({'success': False, 'message': 'Không có dữ liệu JSON.'}), 400
            
        ids_to_delete = data.get('ids')
        print(f"[DELETE_MULTIPLE] IDs to delete: {ids_to_delete}")

        if not ids_to_delete:
            print("[DELETE_MULTIPLE] No IDs provided")
            return jsonify({'success': False, 'message': 'Không có ID nào được cung cấp.'}), 400

        print(f"[DELETE_MULTIPLE] Attempting to delete {len(ids_to_delete)} bookings")
        success = delete_multiple_rows_in_gsheet(
            sheet_id=DEFAULT_SHEET_ID,
            gcp_creds_file_path=GCP_CREDS_FILE_PATH,
            worksheet_name=WORKSHEET_NAME,
            booking_ids=ids_to_delete
        )
        
        if success:
            print("[DELETE_MULTIPLE] Delete successful, clearing cache")
            load_data.cache_clear() # Xóa cache sau khi sửa đổi
            return jsonify({'success': True, 'message': f'Đã xóa thành công {len(ids_to_delete)} booking(s)'})
        else:
            print("[DELETE_MULTIPLE] Delete failed in Google Sheets")
            return jsonify({'success': False, 'message': 'Lỗi khi xóa dữ liệu trên Google Sheets.'})
            
    except Exception as e:
        print(f"[DELETE_MULTIPLE] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/test_delete', methods=['POST'])
def test_delete():
    """Test endpoint for debugging delete functionality"""
    try:
        data = request.get_json()
        return jsonify({
            'success': True, 
            'message': 'Test endpoint working',
            'received_data': data
        })
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

@app.route('/api/update_guest_amounts', methods=['POST'])
def update_guest_amounts():
    """API endpoint để cập nhật số tiền phòng và taxi cho khách hàng"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Không có dữ liệu'}), 400
        
        booking_id = data.get('booking_id')
        room_amount = data.get('room_amount', 0)
        taxi_amount = data.get('taxi_amount', 0)
        edit_note = data.get('edit_note', '')
        
        # Validate input
        if not booking_id:
            return jsonify({'success': False, 'message': 'Thiếu mã đặt phòng'}), 400
            
        if room_amount < 0 or taxi_amount < 0:
            return jsonify({'success': False, 'message': 'Số tiền không thể âm'}), 400
            
        if room_amount == 0 and taxi_amount == 0:
            return jsonify({'success': False, 'message': 'Vui lòng nhập ít nhất một khoản tiền'}), 400
        
        # Log the original data for debugging
        print(f"[UPDATE_AMOUNTS] Updating booking {booking_id}: room={room_amount}, taxi={taxi_amount}")
        
        # Prepare update data - ONLY update the amount fields
        new_data = {
            'Tổng thanh toán': float(room_amount),
        }
        
        # Handle taxi amount - format properly
        if taxi_amount > 0:
            new_data['Taxi'] = f"{taxi_amount:,.0f}đ"
        else:
            new_data['Taxi'] = ''  # Clear taxi field if amount is 0
        
        # Add edit note with timestamp if provided
        if edit_note:
            timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
            new_data['Ghi chú thanh toán'] = f"dữ liệu trước khi sửa số tiền : {edit_note} (Cập nhật {timestamp})"
        
        print(f"[UPDATE_AMOUNTS] Prepared data: {new_data}")
        
        # Update Google Sheets - use the existing update function
        success = update_row_in_gsheet(
            sheet_id=DEFAULT_SHEET_ID,
            gcp_creds_file_path=GCP_CREDS_FILE_PATH,
            worksheet_name=WORKSHEET_NAME,
            booking_id=booking_id,
            new_data=new_data
        )
        
        if success:
            # Clear cache to get fresh data
            load_data.cache_clear()
            print(f"[UPDATE_AMOUNTS] Successfully updated booking {booking_id}")
            
            return jsonify({
                'success': True, 
                'message': f'Đã cập nhật số tiền thành công cho booking {booking_id}',
                'refresh_dashboard': True,  # ✅ Signal frontend to refresh dashboard
                'updated_booking_id': booking_id
            })
        else:
            print(f"[UPDATE_AMOUNTS] Failed to update booking {booking_id}")
            return jsonify({
                'success': False, 
                'message': 'Không thể cập nhật thông tin trên Google Sheets'
            })
            
    except Exception as e:
        print(f"[UPDATE_AMOUNTS] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Lỗi server: {str(e)}'
        }), 500

@app.route('/api/expenses', methods=['GET', 'POST'])
def manage_expenses():
    """API endpoint for expense management"""
    if request.method == 'GET':
        # Get expenses from Google Sheets
        try:
            from logic import get_expenses_from_sheet
            expenses = get_expenses_from_sheet()
            return jsonify({
                'success': True,
                'data': expenses
            })
        except Exception as e:
            print(f"[GET_EXPENSES] Error: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'data': []
            })
    
    elif request.method == 'POST':
        # Add new expense to Google Sheets
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            # Validate required fields
            required_fields = ['description', 'amount', 'date']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            # Prepare expense data
            expense_data = {
                'date': data['date'],
                'description': data['description'],
                'amount': float(data['amount']),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Save to Google Sheets
            from logic import add_expense_to_sheet
            success = add_expense_to_sheet(expense_data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Expense added successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to save expense to Google Sheets'
                }), 500
                
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid data format: {str(e)}'
            }), 400
        except Exception as e:
            print(f"[ADD_EXPENSE] Error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
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
    """API endpoint trả về JSON data của templates với enhanced debugging"""
    # Try multiple possible paths for production compatibility
    possible_paths = [
        BASE_DIR / 'message_templates.json',  # Local development
        Path('/workspace/message_templates.json'),  # Koyeb production
        Path('/app/message_templates.json'),  # Docker container
        Path('./message_templates.json'),  # Current directory fallback
        Path(os.getcwd()) / 'message_templates.json',  # Working directory
    ]
    
    templates_path = None
    for path in possible_paths:
        if path.exists():
            templates_path = path
            break
    
    try:
        print(f"[TEMPLATES_API] Starting API call...")
        print(f"[TEMPLATES_API] BASE_DIR: {BASE_DIR}")
        print(f"[TEMPLATES_API] Current working directory: {os.getcwd()}")
        print(f"[TEMPLATES_API] Checking paths:")
        for i, path in enumerate(possible_paths):
            exists = path.exists()
            print(f"[TEMPLATES_API]   {i+1}. {path} - {'✅ EXISTS' if exists else '❌ NOT FOUND'}")
        
        if templates_path is None:
            print("[TEMPLATES_API] Templates file not found in any location")
            
            # Try to copy from backup or create default
            backup_locations = [
                BASE_DIR / 'message_templates.json.backup',
                Path('/workspace/message_templates.json.backup'),
                Path('/app/message_templates.json.backup'),
            ]
            
            templates_created = False
            for backup_path in backup_locations:
                if backup_path.exists():
                    try:
                        # Copy backup to main location
                        target_path = Path('/workspace/message_templates.json')
                        import shutil
                        shutil.copy2(backup_path, target_path)
                        print(f"[TEMPLATES_API] Copied backup from {backup_path} to {target_path}")
                        templates_path = target_path
                        templates_created = True
                        break
                    except Exception as copy_error:
                        print(f"[TEMPLATES_API] Failed to copy backup: {copy_error}")
            
            if not templates_created:
                # Create default templates file
                default_path = Path('/workspace/message_templates.json')  # Use workspace for production
                try:
                    default_templates = [
                        {"Category": "WELCOME", "Label": "DEFAULT", "Message": "Welcome! Thank you for your reservation."},
                        {"Category": "CHECK IN", "Label": "DEFAULT", "Message": "Welcome! Please follow the check-in instructions."},
                        {"Category": "THANK YOU", "Label": "DEFAULT", "Message": "Thank you for staying with us!"}
                    ]
                    default_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(default_path, 'w', encoding='utf-8') as f:
                        json.dump(default_templates, f, ensure_ascii=False, indent=2)
                    print(f"[TEMPLATES_API] Created default templates file at: {default_path}")
                    templates_path = default_path
                except Exception as create_error:
                    print(f"[TEMPLATES_API] Failed to create default templates: {create_error}")
                    return jsonify({"success": False, "templates": [], "error": "Templates file not found"})
        
        print(f"[TEMPLATES_API] Using templates file at: {templates_path}")
        print(f"[TEMPLATES_API] File exists: {templates_path.exists()}")
        
        with open(templates_path, 'r', encoding='utf-8') as f:
            templates = json.load(f)
            
        print(f"[TEMPLATES_API] Successfully loaded {len(templates)} templates from file")
        print(f"[TEMPLATES_API] Raw template data type: {type(templates)}")
        
        # Validate templates data
        if not isinstance(templates, list):
            print(f"[TEMPLATES_API] Templates data is not a list: {type(templates)}")
            return jsonify({"success": False, "templates": [], "error": "Invalid templates format"})
            
        # Ensure each template has required fields
        valid_templates = []
        for i, template in enumerate(templates):
            if isinstance(template, dict) and 'Category' in template:
                valid_templates.append(template)
                print(f"[TEMPLATES_API] Template {i}: Category='{template.get('Category')}', Label='{template.get('Label')}'")
            else:
                print(f"[TEMPLATES_API] Skipping invalid template at index {i}: {template}")
        
        print(f"[TEMPLATES_API] Returning {len(valid_templates)} valid templates")
        return jsonify(valid_templates)
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[TEMPLATES_API] Error loading templates: {e}")
        return jsonify({"success": False, "templates": [], "error": str(e)})
    except Exception as e:
        print(f"[TEMPLATES_API] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "templates": [], "error": f"Server error: {str(e)}"})

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

@app.route('/api/ai_chat_rag', methods=['POST'])
def ai_chat_rag():
    """🧠 Enhanced AI Chat with RAG (Simple RAG implementation)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get query and guest information
        user_query = data.get('message', '').strip()
        guest_name = data.get('guest_name', '').strip()
        
        if not user_query:
            return jsonify({"error": "No message provided"}), 400
        
        print(f"🧠 RAG Query: '{user_query}' from guest: '{guest_name}'")
        
        # Initialize RAG system
        try:
            from simple_rag import get_simple_rag
            rag_system = get_simple_rag()
        except ImportError as e:
            print(f"RAG system not available: {e}")
            return jsonify({
                "error": "RAG system not available",
                "fallback_response": "Please contact reception for assistance."
            }), 500
        
        # Generate RAG response
        rag_response = rag_system.generate_rag_response(user_query, guest_name)
        
        # Enhanced response with booking context
        booking_context = {}
        if guest_name:
            try:
                # Get guest booking information from Google Sheets
                booking_context = get_guest_booking_context(guest_name)
            except Exception as e:
                print(f"Error getting booking context: {e}")
        
        # Build enhanced response
        enhanced_response = {
            "success": True,
            "query": user_query,
            "answer": rag_response['answer'],
            "confidence": rag_response['confidence'],
            "sources": rag_response['sources'],
            "suggestions": rag_response['suggestions'],
            "guest_personalized": rag_response['guest_personalized'],
            "booking_context": booking_context,
            "rag_enabled": True,
            "gemini_enhanced": False,
            "timestamp": rag_response['timestamp']
        }
        
        # Add contextual enhancements
        if booking_context:
            enhanced_response["contextual_info"] = generate_contextual_info(booking_context)
        
        print(f"✅ RAG Response generated with confidence: {rag_response['confidence']:.2f}")
        return jsonify(enhanced_response)
        
    except Exception as e:
        print(f"AI Chat RAG error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Server error: {str(e)}",
            "fallback_response": "I apologize, but I'm having technical difficulties. Please contact our reception for immediate assistance."
        }), 500

@app.route('/api/ai_chat_gemini_rag', methods=['POST'])
def ai_chat_gemini_rag():
    """🚀 NEW: Gemini-Enhanced RAG with Advanced AI Reasoning"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get query and conversation information
        user_query = data.get('message', '').strip()
        guest_name = data.get('guest_name', '').strip()
        conversation_id = data.get('conversation_id', '')
        
        if not user_query:
            return jsonify({"error": "No message provided"}), 400
        
        print(f"🚀 Gemini RAG Query: '{user_query}' from guest: '{guest_name}'")
        
        # Initialize Gemini RAG system
        try:
            from gemini_rag import get_gemini_rag, initialize_gemini_rag
            
            gemini_rag_system = get_gemini_rag()
            if not gemini_rag_system:
                # Initialize with API key from environment
                gemini_rag_system = initialize_gemini_rag(GOOGLE_API_KEY)
                
        except ImportError as e:
            print(f"Gemini RAG system not available: {e}")
            # Fallback to simple RAG
            return ai_chat_rag()
        
        # Generate enhanced response
        enhanced_response = gemini_rag_system.generate_enhanced_response(
            user_query, guest_name, conversation_id
        )
        
        # Enhanced response with booking context
        booking_context = {}
        if guest_name:
            try:
                booking_context = get_guest_booking_context(guest_name)
            except Exception as e:
                print(f"Error getting booking context: {e}")
        
        # Build complete response
        complete_response = {
            "success": True,
            "query": user_query,
            "answer": enhanced_response['answer'],
            "confidence": enhanced_response.get('confidence', 0.9),
            "sources": enhanced_response.get('sources', []),
            "suggestions": enhanced_response.get('suggestions', []),
            "guest_personalized": enhanced_response.get('guest_personalized', False),
            "booking_context": booking_context,
            "rag_enabled": True,
            "gemini_enhanced": enhanced_response.get('gemini_enhanced', False),
            "model_used": enhanced_response.get('model_used', 'simple_rag'),
            "reasoning_type": enhanced_response.get('reasoning_type', 'keyword_matching'),
            "conversation_id": enhanced_response.get('conversation_id', conversation_id),
            "timestamp": enhanced_response.get('timestamp', datetime.now().isoformat())
        }
        
        # Add contextual enhancements
        if booking_context:
            complete_response["contextual_info"] = generate_contextual_info(booking_context)
        
        # Add conversation management
        if enhanced_response.get('gemini_enhanced'):
            print(f"✅ Gemini-Enhanced Response generated (model: {enhanced_response.get('model_used')})")
        else:
            print(f"✅ Fallback RAG Response generated")
            
        return jsonify(complete_response)
        
    except Exception as e:
        print(f"Gemini RAG error: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to simple RAG on any error
        return ai_chat_rag()

def get_guest_booking_context(guest_name: str) -> dict:
    """Get guest booking information for RAG context"""
    try:
        from logic import import_from_gsheet
        
        # Import current bookings
        df = import_from_gsheet(
            sheet_id=DEFAULT_SHEET_ID,
            worksheet_name=WORKSHEET_NAME,
            gcp_creds_file_path=GCP_CREDS_FILE_PATH
        )
        
        if df is None or df.empty:
            return {}
        
        # Find guest bookings (case insensitive)
        guest_bookings = df[df['Tên người đặt'].str.contains(guest_name, case=False, na=False)]
        
        if guest_bookings.empty:
            return {}
        
        # Get latest booking
        latest_booking = guest_bookings.iloc[-1]
        
        booking_context = {
            'guest_name': guest_name,
            'booking_id': latest_booking.get('Số đặt phòng', ''),
            'checkin_date': str(latest_booking.get('Check-in Date', '')),
            'checkout_date': str(latest_booking.get('Check-out Date', '')),
            'total_amount': latest_booking.get('Tổng thanh toán', 0),
            'payment_status': latest_booking.get('Đã thanh toán', ''),
            'room_type': latest_booking.get('Loại phòng', ''),
            'special_requests': latest_booking.get('Ghi chú', ''),
            'booking_count': len(guest_bookings)
        }
        
        return booking_context
        
    except Exception as e:
        print(f"Error getting guest booking context: {e}")
        return {}

def generate_contextual_info(booking_context: dict) -> dict:
    """Generate contextual information based on booking"""
    
    from datetime import datetime, timedelta
    
    contextual_info = {}
    
    try:
        # Parse dates
        checkin_str = booking_context.get('checkin_date', '')
        checkout_str = booking_context.get('checkout_date', '')
        
        if checkin_str and checkout_str:
            checkin_date = datetime.strptime(checkin_str, '%Y-%m-%d')
            checkout_date = datetime.strptime(checkout_str, '%Y-%m-%d')
            today = datetime.now()
            
            # Determine guest status
            if today < checkin_date:
                days_until_checkin = (checkin_date - today).days
                contextual_info['guest_status'] = 'upcoming'
                contextual_info['status_message'] = f"Arriving in {days_until_checkin} days"
            elif checkin_date <= today <= checkout_date:
                days_remaining = (checkout_date - today).days
                contextual_info['guest_status'] = 'current'
                contextual_info['status_message'] = f"{days_remaining} days remaining"
            else:
                contextual_info['guest_status'] = 'past'
                contextual_info['status_message'] = "Previous guest"
            
            # Add relevant suggestions based on status
            if contextual_info['guest_status'] == 'upcoming':
                contextual_info['suggestions'] = [
                    "Check-in starts at 14:00",
                    "Airport taxi available for 280,000 VND",
                    "Let us know your arrival time"
                ]
            elif contextual_info['guest_status'] == 'current':
                contextual_info['suggestions'] = [
                    "Need restaurant recommendations?",
                    "Ask about tourist attractions nearby",
                    "Late checkout available until 15:00"
                ]
        
        # Payment status context
        payment_status = booking_context.get('payment_status', '').lower()
        if 'chưa' in payment_status or 'no' in payment_status:
            contextual_info['payment_reminder'] = "Payment pending - please settle at reception"
        
        # VIP status for repeat guests
        if booking_context.get('booking_count', 0) > 1:
            contextual_info['vip_status'] = True
            contextual_info['vip_message'] = f"Welcome back! This is your {booking_context['booking_count']} booking with us."
        
    except Exception as e:
        print(f"Error generating contextual info: {e}")
    
    return contextual_info

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
        return redirect(url_for('ai_assistant_hub'))
    except Exception as e:
        flash(f'❌ Lỗi khi import: {str(e)}', 'danger')
        return redirect(url_for('ai_assistant_hub'))

# === QUICK NOTES SYSTEM ===

@app.route('/api/quick_notes', methods=['GET'])
def get_quick_notes():
    """API để lấy danh sách quick notes từ Google Sheets"""
    try:
        # Sử dụng logic tương tự như templates
        from logic import _get_gspread_client
        
        gc = _get_gspread_client(GCP_CREDS_FILE_PATH)
        sh = gc.open_by_key(DEFAULT_SHEET_ID)
        
        # Tìm hoặc tạo worksheet QuickNotes
        try:
            worksheet = sh.worksheet('QuickNotes')
        except:
            # Tạo worksheet mới nếu chưa có
            worksheet = sh.add_worksheet(title='QuickNotes', rows=100, cols=8)
            # Thêm header
            headers = ['ID', 'Type', 'Content', 'Date', 'Time', 'GuestName', 'CreatedAt', 'Completed']
            worksheet.update([headers], 'A1')
            print("✅ Created new QuickNotes worksheet")
        
        # Đọc dữ liệu
        data = worksheet.get_all_values()
        if len(data) <= 1:  # Chỉ có header hoặc trống
            return jsonify({'success': True, 'notes': []})
        
        # Chuyển đổi dữ liệu
        headers = data[0]
        notes = []
        for row in data[1:]:
            if len(row) >= len(headers) and row[0]:  # Có ID
                note = {}
                for i, header in enumerate(headers):
                    note[header.lower()] = row[i] if i < len(row) else ''
                notes.append(note)
        
        return jsonify({'success': True, 'notes': notes})
        
    except Exception as e:
        print(f"❌ Error getting quick notes: {e}")
        return jsonify({'success': False, 'message': str(e), 'notes': []})

@app.route('/api/quick_notes', methods=['POST'])
def save_quick_note():
    """API để lưu quick note vào Google Sheets"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Không có dữ liệu'}), 400
        
        # Validate required fields
        required_fields = ['type', 'content', 'date', 'time']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Thiếu field: {field}'}), 400
        
        # Lưu vào Google Sheets
        from logic import _get_gspread_client
        
        gc = _get_gspread_client(GCP_CREDS_FILE_PATH)
        sh = gc.open_by_key(DEFAULT_SHEET_ID)
        
        # Tìm hoặc tạo worksheet QuickNotes
        try:
            worksheet = sh.worksheet('QuickNotes')
        except:
            # Tạo worksheet mới nếu chưa có
            worksheet = sh.add_worksheet(title='QuickNotes', rows=100, cols=8)
            headers = ['ID', 'Type', 'Content', 'Date', 'Time', 'GuestName', 'CreatedAt', 'Completed']
            worksheet.update([headers], 'A1')
        
        # Chuẩn bị dữ liệu để lưu
        note_id = data.get('id', str(int(datetime.now().timestamp() * 1000)))
        guest_name = data.get('guestName', '')
        created_at = datetime.now().isoformat()
        completed = data.get('completed', 'false')
        
        new_row = [
            note_id,
            data['type'],
            data['content'],
            data['date'],
            data['time'],
            guest_name,
            created_at,
            completed
        ]
        
        # Thêm hàng mới
        worksheet.append_row(new_row)
        
        print(f"✅ Quick Note saved to Sheets: {data['type']} - {data['content'][:50]}...")
        
        return jsonify({
            'success': True, 
            'message': 'Đã lưu quick note vào Google Sheets!',
            'note_id': note_id
        })
        
    except Exception as e:
        print(f"Error saving quick note: {e}")
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/quick_notes/<note_id>/complete', methods=['POST'])
def complete_quick_note(note_id):
    """API để đánh dấu hoàn thành quick note"""
    try:
        from logic import _get_gspread_client
        
        gc = _get_gspread_client(GCP_CREDS_FILE_PATH)
        sh = gc.open_by_key(DEFAULT_SHEET_ID)
        worksheet = sh.worksheet('QuickNotes')
        
        # Tìm hàng có ID tương ứng
        data = worksheet.get_all_values()
        headers = data[0]
        id_col_index = headers.index('ID') + 1  # gspread uses 1-based indexing
        completed_col_index = headers.index('Completed') + 1
        
        # Tìm cell chứa note_id
        cell = worksheet.find(note_id, in_column=id_col_index)
        if cell:
            # Cập nhật trạng thái completed
            worksheet.update_cell(cell.row, completed_col_index, 'true')
            return jsonify({'success': True, 'message': 'Đã đánh dấu hoàn thành!'})
        else:
            return jsonify({'success': False, 'message': 'Không tìm thấy note'}), 404
            
    except Exception as e:
        print(f"Error completing quick note: {e}")
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/quick_notes/<note_id>', methods=['DELETE'])
def delete_quick_note(note_id):
    """API để xóa quick note"""
    try:
        from logic import _get_gspread_client
        
        gc = _get_gspread_client(GCP_CREDS_FILE_PATH)
        sh = gc.open_by_key(DEFAULT_SHEET_ID)
        worksheet = sh.worksheet('QuickNotes')
        
        # Tìm hàng có ID tương ứng
        data = worksheet.get_all_values()
        headers = data[0]
        id_col_index = headers.index('ID') + 1
        
        # Tìm cell chứa note_id
        cell = worksheet.find(note_id, in_column=id_col_index)
        if cell:
            # Xóa hàng
            worksheet.delete_rows(cell.row)
            return jsonify({'success': True, 'message': 'Đã xóa note!'})
        else:
            return jsonify({'success': False, 'message': 'Không tìm thấy note'}), 404
            
    except Exception as e:
        print(f"Error deleting quick note: {e}")
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

# Email reminder system routes removed per user request


@app.route('/api/arrival_times', methods=['GET', 'POST'])
def manage_arrival_times():
    """API để quản lý thời gian check-in (sync across devices)"""
    try:
        from logic import _get_gspread_client
        
        gc = _get_gspread_client(GCP_CREDS_FILE_PATH)
        sh = gc.open_by_key(DEFAULT_SHEET_ID)
        
        # Tìm hoặc tạo worksheet ArrivalTimes
        try:
            worksheet = sh.worksheet('ArrivalTimes')
        except:
            worksheet = sh.add_worksheet(title='ArrivalTimes', rows=100, cols=4)
            headers = ['Type', 'BookingID', 'Time', 'UpdatedAt']
            worksheet.update([headers], 'A1')
        
        if request.method == 'GET':
            # Lấy tất cả thời gian đã lưu
            all_times = worksheet.get_all_records()
            
            result = {
                'default_time': '14:00',  # fallback
                'guest_times': {}
            }
            
            for record in all_times:
                if record['Type'] == 'default':
                    result['default_time'] = record['Time']
                elif record['Type'] == 'guest' and record['BookingID']:
                    result['guest_times'][record['BookingID']] = record['Time']
            
            return jsonify({
                'success': True,
                'data': result
            })
        
        elif request.method == 'POST':
            # Lưu thời gian mới
            data = request.get_json()
            time_type = data.get('type')  # 'default' or 'guest'
            booking_id = data.get('booking_id', '')
            new_time = data.get('time')
            
            if not new_time or not time_type:
                return jsonify({'success': False, 'message': 'Missing time or type'}), 400
            
            # Tìm và cập nhật hoặc thêm mới
            all_records = worksheet.get_all_records()
            updated = False
            
            for i, record in enumerate(all_records):
                if record['Type'] == time_type and record['BookingID'] == booking_id:
                    # Cập nhật existing record
                    worksheet.update_cell(i + 2, 3, new_time)  # Column C (Time)
                    worksheet.update_cell(i + 2, 4, datetime.now().isoformat())  # Column D (UpdatedAt)
                    updated = True
                    break
            
            if not updated:
                # Thêm record mới
                new_row = [
                    time_type,
                    booking_id,
                    new_time,
                    datetime.now().isoformat()
                ]
                worksheet.append_row(new_row)
            
            return jsonify({
                'success': True,
                'message': f'Đã lưu thời gian {time_type}: {new_time}'
            })
            
    except Exception as e:
        print(f"Error managing arrival times: {e}")
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500


# ==============================================================================
# APARTMENT MARKET ANALYSIS API - BOOKING.COM SCRAPER
# ==============================================================================

@app.route('/api/market_intelligence', methods=['GET', 'POST'])
def market_intelligence_api():
    """
    Complete hotel market intelligence API endpoint
    Provides comprehensive market analysis with multiple data sources
    """
    try:
        # Import the complete market intelligence system
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        
        from market_intelligence_complete import HotelMarketIntelligence, MarketAnalyzer, format_complete_analysis
        
        # Get parameters
        if request.method == 'POST':
            data = request.get_json() or {}
            location = data.get('location', 'Hanoi')
            max_price = data.get('max_price', 500000)
            custom_url = data.get('custom_url')
        else:
            location = request.args.get('location', 'Hanoi')
            max_price = int(request.args.get('max_price', 500000))
            custom_url = request.args.get('custom_url')
        
        if custom_url:
            print(f"🔍 Starting market intelligence for custom URL: {custom_url[:100]}...")
        else:
            print(f"🔍 Starting market intelligence for {location} (under {int(max_price):,} VND)")
        
        # Initialize systems
        intel = HotelMarketIntelligence()
        analyzer = MarketAnalyzer()
        
        # Get market data with custom URL support
        market_data = intel.get_market_data(location, max_price, custom_url)
        
        if "error" in market_data:
            return jsonify({
                "success": False,
                "error": market_data["error"]
            }), 500
        
        # Perform comprehensive analysis
        analysis = analyzer.analyze_market(market_data)
        
        # Generate formatted report
        formatted_report = format_complete_analysis(market_data, analysis)
        
        # Create summary for API response
        apartments = market_data.get("apartments", [])
        prices = [apt.get("price_num", 0) for apt in apartments if apt.get("price_num")]
        
        summary = {
            "total_properties": len(apartments),
            "average_price": sum(prices) // len(prices) if prices else 0,
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0
            },
            "data_source": market_data.get("source", "Unknown"),
            "location": location,
            "max_price_filter": max_price
        }
        
        return jsonify({
            "success": True,
            "summary": summary,
            "market_data": market_data,
            "analysis": analysis,
            "formatted_report": formatted_report,
            "timestamp": datetime.now().isoformat(),
            "intelligence_level": "complete"
        })
        
    except ImportError as e:
        return jsonify({
            "success": False,
            "error": f"Market intelligence system not available: {str(e)}"
        }), 500
    except Exception as e:
        print(f"❌ Market intelligence API error: {e}")
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500

@app.route('/api/scrape_apartments', methods=['GET', 'POST'])
def scrape_apartments_api():
    """
    Legacy API endpoint - redirects to new market intelligence system
    """
    try:
        print("🔄 Redirecting to optimized market intelligence system...")
        return market_intelligence_api()
    except Exception as e:
        print(f"❌ Legacy API error: {e}")
        return jsonify({
            "success": False,
            "error": f"Legacy endpoint error: {str(e)}",
            "recommendation": "Use /api/market_intelligence for better results"
        }), 500

# ==============================================================================
# MARKET INTELLIGENCE FRONTEND ROUTE
# ==============================================================================

@app.route('/market_intelligence')
def market_intelligence():
    """
    Market Intelligence frontend page
    """
    return render_template('market_intelligence.html')

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
            return redirect(url_for('ai_assistant_hub'))
        export_message_templates_to_gsheet(templates, DEFAULT_SHEET_ID, GCP_CREDS_FILE_PATH)
        flash('Đã export thành công tất cả các mẫu tin nhắn!', 'success')
    except Exception as e:
        flash(f'Lỗi khi export: {e}', 'danger')
    return redirect(url_for('ai_assistant_hub'))

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
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        
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
        
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
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
    # Email reminder system initialization removed per user request
    
    # Chạy trên cổng từ environment variable hoặc mặc định 8080 cho Koyeb
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
