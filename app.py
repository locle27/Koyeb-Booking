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
from dashboard_routes import process_dashboard_data

# Market Price Analyzer - REMOVED per user request
# from market_price_analyzer import (
#     analyze_market_prices, 
#     format_price_analysis_for_display,
#     MarketPriceAnalyzer
# )

# Import AI Pricing Analyst - REMOVED per user request  
# from ai_pricing_analyst import analyze_budget_pricing_with_ai, analyze_price_range_with_ai

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
        collector_revenue_list=dashboard_data.get('collector_revenue_selected', pd.DataFrame()).to_dict('records'),
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
    
    bookings_list = df.to_dict(orient='records')
    
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
            flash('Không có dữ liệu để lưu.', 'warning')
            return redirect(url_for('add_from_image_page'))

        bookings_to_save = json.loads(extracted_json_str)
        
        formatted_bookings = []
        for booking in bookings_to_save:
            if 'error' in booking: continue
            formatted_booking = {
                'Tên người đặt': booking.get('guest_name'),
                'Số đặt phòng': booking.get('booking_id'),
                'Check-in Date': booking.get('check_in_date'),
                'Check-out Date': booking.get('check_out_date'),
                'Tên chỗ nghỉ': booking.get('room_type'),
                'Tổng thanh toán': booking.get('total_payment'),
                'Hoa hồng': booking.get('commission', 0),  # Thêm hoa hồng
                'Tình trạng': 'OK'
            }
            formatted_bookings.append(formatted_booking)

        if formatted_bookings:
            append_multiple_bookings_to_sheet(
                bookings=formatted_bookings,
                gcp_creds_file_path=GCP_CREDS_FILE_PATH,
                sheet_id=DEFAULT_SHEET_ID,
                worksheet_name=WORKSHEET_NAME
            )
            # === SỬA LỖI QUAN TRỌNG: Xóa cache sau khi thêm ===
            load_data.cache_clear()
            flash(f'Đã lưu thành công {len(formatted_bookings)} đặt phòng mới!', 'success')
        else:
            flash('Không có đặt phòng hợp lệ nào để lưu.', 'info')

    except Exception as e:
        flash(f'Lỗi khi lưu các đặt phòng đã trích xuất: {e}', 'danger')
        
    return redirect(url_for('view_bookings'))

@app.route('/booking/<booking_id>/edit', methods=['GET', 'POST'])
def edit_booking(booking_id):
    df, _ = load_data()
    booking = df[df['Số đặt phòng'] == booking_id].to_dict('records')[0] if not df.empty else {}
    
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
    """API endpoint để thu tiền từ khách hàng"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Không có dữ liệu'}), 400
        
        booking_id = data.get('booking_id')
        collected_amount = data.get('collected_amount')
        collector_name = data.get('collector_name')
        payment_note = data.get('payment_note', '')
        
        # Validate input
        if not booking_id:
            return jsonify({'success': False, 'message': 'Thiếu mã đặt phòng'}), 400
            
        if not collector_name:
            return jsonify({'success': False, 'message': 'Thiếu tên người thu tiền'}), 400
            
        if not collected_amount or collected_amount <= 0:
            return jsonify({'success': False, 'message': 'Số tiền thu không hợp lệ'}), 400
        
        # Cập nhật thông tin trong Google Sheets
        new_data = {
            'Người thu tiền': collector_name,
        }
        
        # Thêm ghi chú nếu có (bao gồm thông tin hoa hồng nếu có)
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

@app.route('/data_health')
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

@app.route('/templates')
def get_templates_page():
    """Trả về trang HTML cho quản lý templates"""
    return render_template('templates.html')

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

# MARKET ANALYSIS ROUTES REMOVED PER USER REQUEST
# @app.route('/market_analysis')
# def market_analysis_page():
#     """Trang Market Price Analysis - Phân tích giá thị trường - REMOVED"""
#     return redirect(url_for('dashboard'))  # Redirect to dashboard instead

# @app.route('/api/analyze_market_prices', methods=['POST'])
# def api_analyze_market_prices():
#     """API endpoint để phân tích giá thị trường từ Booking.com - REMOVED"""
#     return jsonify({"error": "Market analysis feature has been removed", "success": False}), 410

# @app.route('/api/ai_pricing_analysis', methods=['POST'])
# def api_ai_pricing_analysis():
#     """API endpoint để phân tích pricing với AI - REMOVED"""
#     return jsonify({"error": "AI pricing analysis feature has been removed", "success": False}), 410

# @app.route('/api/get_default_booking_url')
# def get_default_booking_url():
#     """API endpoint trả về URL mặc định cho Khu Phố Cổ Hà Nội - REMOVED"""
#     return jsonify({"error": "Default booking URL feature has been removed", "success": False}), 410

# === EMAIL REMINDER SYSTEM ROUTES ===
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
    Phân tích ảnh đoạn chat và tạo phản hồi AI với vai trò lễ tân khách sạn
    
    Args:
        image_bytes: Dữ liệu ảnh
        templates: Danh sách tất cả templates
        selected_template: Template được chọn cụ thể (nếu có)
        response_mode: 'auto', 'yes', hoặc 'no'
        custom_instructions: Hướng dẫn tùy chỉnh từ người dùng
    """
    try:
        if not GOOGLE_API_KEY:
            return {"error": "Google API key chưa được cấu hình"}
        
        # Chuẩn bị context từ templates
        if selected_template:
            # Nếu có template được chọn cụ thể, ưu tiên nó
            templates_context = f"SELECTED TEMPLATE (USE THIS PRIMARILY):\n- {selected_template.get('Category', '')} - {selected_template.get('Label', '')}: {selected_template.get('Message', '')}\n\n"
            templates_context += "OTHER AVAILABLE TEMPLATES:\n" + "\n".join([
                f"- {t.get('Category', '')} - {t.get('Label', '')}: {t.get('Message', '')}"
                for t in templates if isinstance(t, dict) and t != selected_template
            ])
        else:
            # Sử dụng tất cả templates như trước
            templates_context = "\n".join([
                f"- {t.get('Category', '')} - {t.get('Label', '')}: {t.get('Message', '')}"
                for t in templates if isinstance(t, dict)
            ])
        
        # Tạo hướng dẫn cho response mode với emphasis mạnh hơn
        if response_mode == 'yes':
            response_mode_instruction = """
⚠️⚠️⚠️ CRITICAL RESPONSE MODE: POSITIVE/YES MODE ⚠️⚠️⚠️
- YOU MUST respond in a POSITIVE, HELPFUL, and ACCOMMODATING manner
- ALWAYS say YES whenever possible and offer solutions
- Be ENTHUSIASTIC and SUPPORTIVE in your tone
- Example: "Absolutely! We'd be happy to help with that..."
- DO NOT decline requests unless absolutely impossible
- FOCUS on what you CAN do, not what you cannot do
"""
        elif response_mode == 'no':
            response_mode_instruction = """
⚠️⚠️⚠️ CRITICAL RESPONSE MODE: NEGATIVE/NO MODE ⚠️⚠️⚠️
- YOU MUST politely DECLINE or explain why something ISN'T AVAILABLE
- Say NO to requests, but be APOLOGETIC and PROFESSIONAL
- Be REGRETFUL but maintain professional standards
- Example: "I'm very sorry, but unfortunately we don't have that available right now. However, we can offer..."
- ALWAYS explain why something cannot be done
- FOCUS on limitations and constraints, then offer alternatives
- Even if you would normally say yes, you MUST say no in this mode
"""
        else:
            response_mode_instruction = """
RESPONSE MODE: AUTO MODE
- Respond naturally based on the guest's request and available services
- Be honest about what's available or not available
- Use your best judgment for the most helpful response
"""
        
        # Tạo custom instructions section
        custom_instructions_section = ""
        if custom_instructions.strip():
            custom_instructions_section = f"""
⭐⭐⭐ HƯỚNG DẪN TÙY CHỈNH TỪ NGƯỜI DÙNG (ƯU TIÊN CAO) ⭐⭐⭐
QUAN TRỌNG: Người dùng đã cung cấp hướng dẫn cụ thể sau đây. BẠN PHẢI tuân thủ hướng dẫn này khi tạo phản hồi:

"{custom_instructions.strip()}"

Hãy đảm bảo phản hồi của bạn phù hợp với hướng dẫn này trong khi vẫn giữ tính chuyên nghiệp và bối cảnh cuộc hội thoại.
⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
"""
        
        # Tạo prompt cho AI với response mode emphasis
        prompt = f"""
You are a professional hotel receptionist at 118 Hang Bac Hostel in Hanoi's Old Quarter. Your job is to analyze the ENTIRE conversation in the image and provide a NATURAL, CONTEXTUAL response.

HOTEL INFO:
- Name: 118 Hang Bac Hostel
- Location: 118 Hang Bac Street, Hoan Kiem District, Hanoi (Old Quarter)
- Type: Budget hostel/guesthouse in Hanoi's historic center

{custom_instructions_section}

{response_mode_instruction}

⚠️ IMPORTANT: The response mode above is MANDATORY and must be followed strictly.

CONVERSATION ANALYSIS PROCESS (VERY IMPORTANT):
1. FIRST: Read and understand the ENTIRE conversation from beginning to end
2. ANALYZE: Identify key context including:
   - Guest's original request/need
   - Previous responses given
   - Any unresolved issues
   - Guest's emotional state (frustrated, happy, confused, etc.)
   - Timeline of events discussed
   - Any specific details mentioned (dates, room numbers, services, etc.)
3. UNDERSTAND: The relationship between messages and how the conversation has evolved
4. IDENTIFY: What the guest's LATEST message is asking for in context of the full conversation
5. RESPOND: Provide appropriate response based on FULL CONTEXT, not just the last message

AVAILABLE MESSAGE TEMPLATES:
{templates_context}

TEMPLATE USAGE PRIORITY:
1. ANALYZE FULL CONVERSATION CONTEXT FIRST
2. {"USE SELECTED TEMPLATE: The user has specifically chosen a template - use this as base but adapt to conversation context" if selected_template else "SEARCH: Look through ALL available templates to find any that relate to the overall conversation topic"}
3. IF MATCH FOUND: Use the relevant template as your BASE response, then adapt it to:
   - Match the conversation's tone and context
   - Address any previous concerns mentioned
   - Reference specific details from earlier messages
   - Show that you understand the full situation
4. IF NO MATCH: Create a helpful response based on the full conversation context
5. ALWAYS: Apply the RESPONSE MODE instructions while maintaining contextual awareness

CONTEXTUAL RESPONSE REQUIREMENTS:
- Reference previous parts of the conversation when relevant
- Address any ongoing concerns or unresolved issues
- Show understanding of the guest's journey/experience
- Be consistent with any previous information provided
- Acknowledge any time-sensitive elements mentioned earlier

RESPONSE STYLE:
- Natural, conversational English
- Show that you've read and understood the FULL conversation
- Reference specific details from earlier messages when appropriate
- Be empathetic to the guest's situation based on the full context
- MOST IMPORTANT: FOLLOW THE RESPONSE MODE while being contextually aware

CRITICAL: Your response should show clear understanding of the ENTIRE conversation and provide a contextually appropriate reply to the latest message that takes into account everything discussed previously.

Return your analysis in this JSON format:
{{
    "conversation_context": "Detailed analysis of the ENTIRE conversation - what happened from start to finish, key points discussed, guest's journey, and current situation",
    "previous_interactions": "Summary of important details from earlier messages that are relevant to the current response",
    "latest_message_analysis": "Analysis of what the guest's latest message is asking for in context of the full conversation",
    "matched_templates": [
        {{"category": "Template category if used", "label": "Template label if used", "message": "Original template content if used"}}
    ],
    "ai_response": "Your contextually-aware response that shows understanding of the full conversation and addresses the latest message appropriately",
    "context_rationale": "Brief explanation of how the full conversation context influenced your response",
    "custom_instructions_applied": {"true if custom instructions were used and how" if custom_instructions.strip() else "false"},
    "used_config": {{
        "selected_template": {"true" if selected_template else "false"},
        "response_mode": "{response_mode}",
        "custom_instructions": "{custom_instructions.strip() if custom_instructions.strip() else 'none'}"
    }}
}}
"""
        
        # Gọi Gemini API
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Chuyển đổi image bytes thành format phù hợp
        image_data = {
            'mime_type': 'image/jpeg',
            'data': image_bytes
        }
        
        response = model.generate_content([prompt, image_data])
        ai_text = response.text.strip()
        
        # Parse JSON response
        try:
            # Tìm và extract JSON từ response
            json_start = ai_text.find('{')
            json_end = ai_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_text[json_start:json_end]
                result = json.loads(json_str)
                
                # Validate và clean result
                if not isinstance(result, dict):
                    raise ValueError("Invalid JSON structure")
                
                # Ensure required fields
                result.setdefault('analysis_info', 'Đã phân tích nội dung chat')
                result.setdefault('matched_templates', [])
                result.setdefault('ai_response', ai_text)
                result.setdefault('used_config', {
                    'selected_template': bool(selected_template),
                    'response_mode': response_mode
                })
                
                return result
            else:
                # Fallback nếu không parse được JSON
                return {
                    "analysis_info": "Đã phân tích nội dung chat từ ảnh",
                    "matched_templates": [],
                    "ai_response": ai_text,
                    "used_config": {
                        'selected_template': bool(selected_template),
                        'response_mode': response_mode
                    }
                }
                
        except json.JSONDecodeError:
            # Fallback nếu response không phải JSON
            return {
                "analysis_info": "Đã phân tích nội dung chat từ ảnh",
                "matched_templates": [],
                "ai_response": ai_text,
                "used_config": {
                    'selected_template': bool(selected_template),
                    'response_mode': response_mode
                }
            }
        
    except Exception as e:
        print(f"AI analysis error: {e}")
        return {
            "error": f"Lỗi khi phân tích với AI: {str(e)}",
            "analysis_info": "",
            "matched_templates": [],
            "ai_response": "",
            "used_config": {
                'selected_template': bool(selected_template) if selected_template else False,
                'response_mode': response_mode
            }
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
        print("🤖 Starting Hotel Reminder System...")
        start_reminder_system()
        print("✅ Reminder System started successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not start reminder system: {e}")
        print("   Email reminders will be available for manual triggering only")
    
    # Chạy trên cổng từ environment variable hoặc mặc định 8080 cho Koyeb
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
