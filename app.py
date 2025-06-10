import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from dotenv import load_dotenv
import json
from functools import lru_cache
from pathlib import Path
import pandas as pd
import plotly
import plotly.express as px
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
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not start_date_str or not end_date_str:
        # === PHẦN SỬA LỖI QUAN TRỌNG ===
        # Lấy ngày và giờ hiện tại, sau đó chỉ lấy phần ngày
        today_full = datetime.today()
        start_date = today_full.replace(day=1)
        _, last_day = calendar.monthrange(today_full.year, today_full.month)
        end_date = today_full.replace(day=last_day)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    df, _ = load_data()
    
    # Gọi hàm logic với các tham số sắp xếp
    sort_by = request.args.get('sort_by', 'Tháng')
    sort_order = request.args.get('sort_order', 'desc')
    dashboard_data = prepare_dashboard_data(df, start_date, end_date, sort_by, sort_order)

    # Chuẩn bị dữ liệu cho template
    monthly_revenue_list = dashboard_data.get('monthly_revenue_all_time', pd.DataFrame()).to_dict('records')
    genius_stats_list = dashboard_data.get('genius_stats', pd.DataFrame()).to_dict('records')
    monthly_guests_list = dashboard_data.get('monthly_guests_all_time', pd.DataFrame()).to_dict('records')
    weekly_guests_list = dashboard_data.get('weekly_guests_all_time', pd.DataFrame()).to_dict('records')
    monthly_collected_revenue_list = dashboard_data.get('monthly_collected_revenue', pd.DataFrame()).to_dict('records')

    # Tạo biểu đồ doanh thu hàng tháng với thiết kế đẹp hơn
    monthly_revenue_df = pd.DataFrame(monthly_revenue_list)
    monthly_revenue_chart_json = {}
    
    if not monthly_revenue_df.empty:
        print(f"DEBUG: Creating chart with {len(monthly_revenue_df)} data points")
        print(f"DEBUG: Data columns: {monthly_revenue_df.columns.tolist()}")
        print(f"DEBUG: Sample data: {monthly_revenue_df.head()}")
        
        # Sắp xếp lại theo tháng để biểu đồ đường đúng thứ tự
        monthly_revenue_df_sorted = monthly_revenue_df.sort_values('Tháng')
        
        # Tạo biểu đồ combo: line + bar
        fig = px.line(monthly_revenue_df_sorted, x='Tháng', y='Doanh thu', 
                     title='📊 Doanh thu Hàng tháng', markers=True)
        
        # Thêm bar chart cho cùng dữ liệu
        fig.add_bar(x=monthly_revenue_df_sorted['Tháng'], 
                   y=monthly_revenue_df_sorted['Doanh thu'],
                   name='Doanh thu',
                   opacity=0.3,
                   yaxis='y')
        
        # Cải thiện layout
        fig.update_layout(
            title={
                'text': '📊 Doanh thu Hàng tháng (Tất cả thời gian)', 
                'x': 0.5,
                'font': {'size': 18, 'family': 'Arial, sans-serif', 'color': '#2c3e50'}
            },
            xaxis_title='Tháng',
            yaxis_title='Doanh thu (VND)',
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Arial, sans-serif', 'size': 12},
            margin=dict(l=60, r=30, t=80, b=50),
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Cải thiện axes
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            showline=True,
            linewidth=1,
            linecolor='rgba(128,128,128,0.5)'
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            showline=True,
            linewidth=1,
            linecolor='rgba(128,128,128,0.5)',
            tickformat=',.0f'
        )
        
        # Cải thiện line traces
        fig.update_traces(
            line=dict(width=3, color='#3498db'),
            marker=dict(size=8, color='#e74c3c', line=dict(width=2, color='white')),
            selector=dict(type='scatter')
        )
        
        # Cải thiện bar traces  
        fig.update_traces(
            marker=dict(color='#3498db', opacity=0.3),
            selector=dict(type='bar')
        )
        
        monthly_revenue_chart_json = json.loads(fig.to_json())
        print(f"DEBUG: Chart JSON created successfully")
    else:
        print("DEBUG: No monthly revenue data for chart")

    # ===== LOGIC MỚI: TÍNH TOÁN KHÁCH CHƯA THU TIỀN QUÁ HẠN =====
    overdue_unpaid_guests = []
    overdue_total_amount = 0
    monthly_revenue_with_unpaid = []
    
    try:
        if not df.empty and 'Check-in Date' in df.columns:
            today = datetime.today().date()
            
            # Đảm bảo Check-in Date là datetime
            if df['Check-in Date'].dtype == 'object':
                df['Check-in Date'] = pd.to_datetime(df['Check-in Date'], errors='coerce')
            
            # Find overdue unpaid guests (checked-in but not paid)
            try:
                # Safer approach: work with a clean copy and convert dates properly
                df_work = df.copy()
                
                # Ensure datetime conversion with explicit handling
                if 'Check-in Date' in df_work.columns:
                    # Convert to datetime, handle various formats
                    df_work['Check-in Date'] = pd.to_datetime(df_work['Check-in Date'], errors='coerce', dayfirst=True)
                    
                    # Only proceed if we have valid datetime data
                    valid_dates_mask = df_work['Check-in Date'].notna()
                    if valid_dates_mask.any():
                        # Filter to only rows with valid dates first
                        df_valid = df_work[valid_dates_mask].copy()
                        
                        print(f"DEBUG: Total records with valid dates: {len(df_valid)}")
                        print(f"DEBUG: Today's date: {today}")
                        
                        # Debug: Check what collectors exist
                        collectors = df_valid['Người thu tiền'].unique()
                        print(f"DEBUG: Unique collectors: {collectors}")
                        
                        # Now create overdue mask on clean data
                        past_checkin = df_valid['Check-in Date'].dt.date <= today
                        
                        # Handle null collectors better - include nan, N/A, empty string, None
                        collected_values = ['LOC LE', 'THAO LE']
                        collector_series = df_valid['Người thu tiền'].fillna('').astype(str)
                        not_collected = ~collector_series.isin(collected_values)
                        
                        not_cancelled = df_valid['Tình trạng'] != 'Đã hủy'
                        
                        print(f"DEBUG: Past check-in: {past_checkin.sum()} records")
                        print(f"DEBUG: Not collected: {not_collected.sum()} records") 
                        print(f"DEBUG: Not cancelled: {not_cancelled.sum()} records")
                        
                        overdue_mask = past_checkin & not_collected & not_cancelled
                        print(f"DEBUG: Combined overdue mask: {overdue_mask.sum()} records")
                        
                        overdue_df = df_valid[overdue_mask].copy()
                        
                        if not overdue_df.empty:
                            # Calculate overdue days safely - convert date to days manually
                            try:
                                checkin_dates = overdue_df['Check-in Date'].dt.date
                                days_overdue_list = []
                                for date in checkin_dates:
                                    try:
                                        days = (today - date).days
                                        days_overdue_list.append(max(0, days))  # Ensure non-negative
                                    except:
                                        days_overdue_list.append(0)  # Fallback for any date issues
                                        
                                overdue_df['days_overdue'] = days_overdue_list
                                print(f"DEBUG: Days overdue calculated: {days_overdue_list}")
                                
                            except Exception as days_error:
                                print(f"DEBUG: Error calculating days: {days_error}")
                                overdue_df['days_overdue'] = 0  # Fallback
                            
                            # Sort by overdue days descending
                            overdue_df = overdue_df.sort_values('days_overdue', ascending=False)
                            
                            # Safe sum calculation BEFORE converting to dict
                            if 'Tổng thanh toán' in overdue_df.columns:
                                overdue_total_amount = pd.to_numeric(overdue_df['Tổng thanh toán'], errors='coerce').fillna(0).sum()
                            
                            # Convert to list AFTER all calculations
                            overdue_unpaid_guests = overdue_df.to_dict('records')
                            
                            # DEBUG: Print detailed info about overdue guests
                            print(f"DEBUG: Found {len(overdue_unpaid_guests)} overdue unpaid guests, total: {overdue_total_amount:,.0f}d")
                            for i, guest in enumerate(overdue_unpaid_guests[:3]):  # Print first 3
                                print(f"DEBUG Guest {i+1}: {guest.get('Tên người đặt', 'N/A')} - {guest.get('days_overdue', 0)} days - {guest.get('Tổng thanh toán', 0)}d")
                                print(f"  Check-in: {guest.get('Check-in Date')}, Collector: '{guest.get('Người thu tiền', 'N/A')}'")
                        else:
                            print("DEBUG: No overdue guests found after filtering")
                            
                    else:
                        print("DEBUG: No valid dates found in data")
                
            except Exception as overdue_error:
                print(f"WARNING: Error calculating overdue guests: {overdue_error}")
                import traceback
                traceback.print_exc()
                overdue_unpaid_guests = []
                overdue_total_amount = 0
            
            # Tính toán doanh thu theo tháng có bao gồm số khách chưa thu
            try:
                df_period = df[
                    (df['Check-in Date'] >= pd.Timestamp(start_date)) & 
                    (df['Check-in Date'] <= pd.Timestamp(end_date)) &
                    (df['Check-in Date'] <= pd.Timestamp.now()) &
                    (df['Check-in Date'].notna())
                ].copy()
                
                if not df_period.empty:
                    # Tính doanh thu đã thu (LOC LE và THAO LE)
                    collected_df = df_period[
                        df_period['Người thu tiền'].isin(['LOC LE', 'THAO LE'])
                    ].copy()
                    
                    # Tính doanh thu chưa thu (các giá trị khác hoặc rỗng)
                    uncollected_df = df_period[
                        ~df_period['Người thu tiền'].isin(['LOC LE', 'THAO LE'])
                    ].copy()
                    
                    # Nhóm theo tháng - Đã thu
                    if not collected_df.empty:
                        collected_df['Month_Period'] = collected_df['Check-in Date'].dt.to_period('M')
                        collected_monthly = collected_df.groupby('Month_Period').agg({
                            'Tổng thanh toán': 'sum'
                        }).reset_index()
                        collected_monthly['Tháng'] = collected_monthly['Month_Period'].dt.strftime('%Y-%m')
                    else:
                        collected_monthly = pd.DataFrame(columns=['Tháng', 'Tổng thanh toán'])
                    
                    # Nhóm theo tháng - Chưa thu
                    if not uncollected_df.empty:
                        uncollected_df['Month_Period'] = uncollected_df['Check-in Date'].dt.to_period('M')
                        uncollected_monthly = uncollected_df.groupby('Month_Period').agg({
                            'Tổng thanh toán': 'sum',
                            'Số đặt phòng': 'count'  # Đếm số khách chưa thu
                        }).reset_index()
                        uncollected_monthly['Tháng'] = uncollected_monthly['Month_Period'].dt.strftime('%Y-%m')
                        uncollected_monthly = uncollected_monthly.rename(columns={'Số đặt phòng': 'Số khách chưa thu'})
                    else:
                        uncollected_monthly = pd.DataFrame(columns=['Tháng', 'Tổng thanh toán', 'Số khách chưa thu'])
                    
                    # Merge dữ liệu
                    if not collected_monthly.empty and not uncollected_monthly.empty:
                        merged_data = pd.merge(
                            collected_monthly[['Tháng', 'Tổng thanh toán']].rename(columns={'Tổng thanh toán': 'Đã thu'}),
                            uncollected_monthly[['Tháng', 'Tổng thanh toán', 'Số khách chưa thu']].rename(columns={'Tổng thanh toán': 'Chưa thu'}),
                            on='Tháng', how='outer'
                        ).fillna(0)
                    elif not collected_monthly.empty:
                        merged_data = collected_monthly[['Tháng', 'Tổng thanh toán']].rename(columns={'Tổng thanh toán': 'Đã thu'})
                        merged_data['Chưa thu'] = 0
                        merged_data['Số khách chưa thu'] = 0
                    elif not uncollected_monthly.empty:
                        merged_data = uncollected_monthly[['Tháng', 'Tổng thanh toán', 'Số khách chưa thu']].rename(columns={'Tổng thanh toán': 'Chưa thu'})
                        merged_data['Đã thu'] = 0
                    else:
                        merged_data = pd.DataFrame(columns=['Tháng', 'Đã thu', 'Chưa thu', 'Số khách chưa thu'])
                    
                    if not merged_data.empty:
                        # Sắp xếp theo tháng
                        merged_data = merged_data.sort_values('Tháng')
                        monthly_revenue_with_unpaid = merged_data.to_dict('records')
                    
                    print(f"DEBUG: Monthly revenue with unpaid data created: {len(monthly_revenue_with_unpaid)} months")
                    
            except Exception as monthly_error:
                print(f"WARNING: Error calculating monthly revenue with unpaid: {monthly_error}")
                monthly_revenue_with_unpaid = []
                
    except Exception as main_error:
        print(f"ERROR: Main calculation error: {main_error}")
        import traceback
        traceback.print_exc()
        overdue_unpaid_guests = []
        overdue_total_amount = 0
        monthly_revenue_with_unpaid = []

    # Tạo biểu đồ donut chart chuyên nghiệp cho người thu tiền
    collector_revenue_data = dashboard_data.get('collector_revenue_selected', pd.DataFrame()).to_dict('records')
    
    collector_chart_data = {
        'data': [{
            'type': 'pie',
            'labels': [row['Người thu tiền'] for row in collector_revenue_data],
            'values': [row['Tổng thanh toán'] for row in collector_revenue_data],
            'textinfo': 'label+percent',
            'textposition': 'auto',
            'hovertemplate': '<b>%{label}</b><br>' +
                           'Doanh thu: %{value:,.0f}đ<br>' +
                           'Tỷ lệ: %{percent}<br>' +
                           '<extra></extra>',
            'marker': {
                'colors': ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c'],
                'line': {
                    'color': '#ffffff',
                    'width': 3
                }
            },
            'hole': 0.4,
            'textfont': {
                'size': 12,
                'family': 'Arial Bold',
                'color': '#2c3e50'
            },
            'pull': [0.05 if i == 0 else 0 for i in range(len(collector_revenue_data))]  # Nổi bật phần đầu tiên
        }],
        'layout': {
            'title': {
                'text': '💰 Doanh thu theo Người thu',
                'x': 0.5,
                'y': 0.95,
                'font': {
                    'size': 16,
                    'family': 'Arial Bold',
                    'color': '#2c3e50'
                }
            },
            'showlegend': True,
            'legend': {
                'orientation': 'v',
                'x': 1.05,
                'y': 0.5,
                'font': {
                    'size': 12,
                    'family': 'Arial',
                    'color': '#2c3e50'
                },
                'bgcolor': 'rgba(255,255,255,0.9)',
                'bordercolor': 'rgba(0,0,0,0.1)',
                'borderwidth': 1
            },
            'height': 300,
            'margin': {'l': 20, 'r': 120, 't': 40, 'b': 20},
            'plot_bgcolor': 'rgba(248,249,250,0.8)',
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'font': {
                'family': 'Arial, sans-serif',
                'size': 12,
                'color': '#2c3e50'
            },
            'annotations': [{
                'text': f'<b>Tổng</b><br>{sum([row["Tổng thanh toán"] for row in collector_revenue_data]):,.0f}đ',
                'x': 0.5, 'y': 0.5,
                'font': {'size': 14, 'family': 'Arial Bold', 'color': '#2c3e50'},
                'showarrow': False
            }]
        }
    }

    collector_revenue_list = dashboard_data.get('collector_revenue_selected', pd.DataFrame()).to_dict('records')

    # DEBUG: Print what we're sending to template
    print(f"DEBUG: Sending to template - overdue_unpaid_guests count: {len(overdue_unpaid_guests)}")
    print(f"DEBUG: Sending to template - overdue_total_amount: {overdue_total_amount}")
    if overdue_unpaid_guests:
        print(f"DEBUG: First overdue guest: {overdue_unpaid_guests[0].get('Tên người đặt', 'N/A')}")

    return render_template(
        'dashboard.html',
        total_revenue=dashboard_data.get('total_revenue_selected', 0),
        total_guests=dashboard_data.get('total_guests_selected', 0),
        monthly_revenue_list=monthly_revenue_list,
        genius_stats_list=genius_stats_list,
        monthly_guests_list=monthly_guests_list,
        weekly_guests_list=weekly_guests_list,
        monthly_collected_revenue_list=monthly_collected_revenue_list,
        monthly_revenue_chart_json=monthly_revenue_chart_json,
        monthly_revenue_with_unpaid=monthly_revenue_with_unpaid,  # Dữ liệu mới
        overdue_unpaid_guests=overdue_unpaid_guests,  # Khách quá hạn
        overdue_total_amount=overdue_total_amount,  # Tổng tiền quá hạn
        collector_chart_json=collector_chart_data,
        collector_revenue_list=collector_revenue_list,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        current_sort_by=sort_by,
        current_sort_order=sort_order
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
                         available_months=available_months)

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
            formatted_bookings.append({
                'Tên người đặt': booking.get('guest_name'),
                'Số đặt phòng': booking.get('booking_id'),
                'Check-in Date': booking.get('check_in_date'),
                'Check-out Date': booking.get('check_out_date'),
                'Tên chỗ nghỉ': booking.get('room_type'),
                'Tổng thanh toán': booking.get('total_payment'),
                'Tình trạng': 'OK'
            })

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
        
        # Thêm ghi chú nếu có
        if payment_note:
            new_data['Ghi chú thu tiền'] = f"Thu {collected_amount:,.0f}đ - {payment_note}"
        
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
        result = analyze_chat_image_with_ai(image_bytes, templates, selected_template, response_mode)
        
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
def analyze_chat_image_with_ai(image_bytes, templates, selected_template=None, response_mode='auto'):
    """
    Phân tích ảnh đoạn chat và tạo phản hồi AI với vai trò lễ tân khách sạn
    
    Args:
        image_bytes: Dữ liệu ảnh
        templates: Danh sách tất cả templates
        selected_template: Template được chọn cụ thể (nếu có)
        response_mode: 'auto', 'yes', hoặc 'no'
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
        
        # Tạo prompt cho AI với response mode emphasis
        prompt = f"""
You are a friendly, casual hotel receptionist at 118 Hang Bac Hostel in Hanoi's Old Quarter. Your job is to analyze the chat conversation in the image and provide a NATURAL, FRIENDLY response to the LAST message from the guest.

HOTEL INFO:
- Name: 118 Hang Bac Hostel
- Location: 118 Hang Bac Street, Hoan Kiem District, Hanoi (Old Quarter)
- Type: Budget hostel/guesthouse in Hanoi's historic center

{response_mode_instruction}

⚠️ IMPORTANT: The response mode above is MANDATORY and must be followed strictly. If the mode is YES, be positive even if normally you'd say no. If the mode is NO, decline even if normally you'd say yes.

AVAILABLE MESSAGE TEMPLATES:
{templates_context}

TEMPLATE USAGE PRIORITY (VERY IMPORTANT):
1. FIRST: Analyze the guest's last message and identify the topic/need
2. {"USE SELECTED TEMPLATE: The user has specifically chosen a template to use as the primary response base" if selected_template else "SEARCH: Look through ALL available templates to find any that relate to the topic"}
3. IF MATCH FOUND: Use the relevant template as your BASE response, then adapt it to sound natural and conversational
4. IF NO MATCH: Create a helpful response based on hotel receptionist experience
5. ALWAYS: Apply the RESPONSE MODE instructions to modify your tone appropriately
6. ALWAYS: List any templates you used in the "matched_templates" section

RESPONSE STYLE:
- Use natural, casual English (avoid overly formal language)
- Be friendly and conversational 
- Keep it simple and easy to understand
- Show genuine care and helpfulness
- When using templates, make them sound natural and personal
- MOST IMPORTANT: FOLLOW THE RESPONSE MODE INSTRUCTIONS ABOVE STRICTLY

TOPIC MATCHING EXAMPLES:
- Guest asks about check-in → Use CHECK IN or EARLY CHECK IN templates
- Guest asks about arrival/directions → Use ARRIVAL template  
- Guest asks about parking → Use PARK template
- Guest asks about laundry → Use LAUNDRY template
- Guest asks about taxi/transport → Use TAXI templates
- Guest says thanks for cleaning → Use DON PHONG template
- Guest asks about room availability → Use HET PHONG if no rooms
- Guest asks about payment options → Use NOT BOOKING template

CRITICAL: Your response should be what YOU (the receptionist) would say NEXT to continue the conversation, based on available templates when possible, BUT MODIFIED ACCORDING TO THE RESPONSE MODE.

Return your analysis in this JSON format:
{{
    "analysis_info": "Brief description of what the guest needs and which topic it relates to",
    "matched_templates": [
        {{"category": "Template category if used", "label": "Template label if used", "message": "Original template content if used"}}
    ],
    "ai_response": "Your friendly, natural response based on templates when available, or original helpful response, STRICTLY following the specified response mode",
    "used_config": {{
        "selected_template": {"true" if selected_template else "false"},
        "response_mode": "{response_mode}"
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
    # Chạy trên cổng từ environment variable hoặc mặc định 8080 cho Koyeb
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
