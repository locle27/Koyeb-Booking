# dashboard_routes.py - Dashboard logic module
from flask import render_template, request
from datetime import datetime, timedelta
import calendar
import pandas as pd
import plotly.express as px
import json
import warnings

def safe_to_dict_records(df):
    """
    Safely convert DataFrame to dict records, handling duplicate columns
    """
    if df.empty:
        return []
    
    try:
        # Check for duplicate columns and clean if necessary
        if df.columns.duplicated().any():
            print("WARNING: DataFrame has duplicate columns, cleaning...")
            # Keep only the first occurrence of each column
            df = df.loc[:, ~df.columns.duplicated()]
            
        # Suppress the warning temporarily
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="DataFrame columns are not unique")
            return df.to_dict('records')
    except Exception as e:
        print(f"Error in safe_to_dict_records: {e}")
        return []


def process_dashboard_data(df, start_date, end_date, sort_by, sort_order, dashboard_data):
    """
    Xử lý dữ liệu dashboard phức tạp
    """
    # Chuẩn bị dữ liệu cho template
    monthly_revenue_list = safe_to_dict_records(dashboard_data.get('monthly_revenue_all_time', pd.DataFrame()))
    genius_stats_list = safe_to_dict_records(dashboard_data.get('genius_stats', pd.DataFrame()))
    monthly_guests_list = safe_to_dict_records(dashboard_data.get('monthly_guests_all_time', pd.DataFrame()))
    weekly_guests_list = safe_to_dict_records(dashboard_data.get('weekly_guests_all_time', pd.DataFrame()))
    monthly_collected_revenue_list = safe_to_dict_records(dashboard_data.get('monthly_collected_revenue', pd.DataFrame()))

    # Tạo biểu đồ doanh thu hàng tháng
    monthly_revenue_chart_json = create_revenue_chart(monthly_revenue_list)
    
    # Xử lý khách chưa thu tiền quá hạn
    overdue_unpaid_guests, overdue_total_amount = process_overdue_guests(df)
    
    # Xử lý doanh thu theo tháng có bao gồm số khách chưa thu
    monthly_revenue_with_unpaid = process_monthly_revenue_with_unpaid(df, start_date, end_date)
    
    # Phát hiện ngày có quá nhiều khách
    overcrowded_days = detect_overcrowded_days(df)
    
    # Tính tổng doanh thu theo ngày cho calendar (chia theo số đêm ở)
    daily_revenue_by_stay = get_daily_revenue_by_stay(df)
    
    # Convert to daily_totals format for compatibility
    daily_totals = []
    for date, data in daily_revenue_by_stay.items():
        today = datetime.today().date()
        days_from_today = (date - today).days
        
        daily_totals.append({
            'date': date,
            'guest_count': data['guest_count'],
            'daily_total': data['daily_total'],
            'bookings': data['bookings'],
            'days_from_today': days_from_today,
            'is_today': days_from_today == 0,
            'is_future': days_from_today > 0
        })
    
    # Tạo biểu đồ pie chart cho người thu tiền
    collector_chart_data = create_collector_chart(dashboard_data)
    
    # Xử lý thông báo khách đến và khách đi
    arrival_notifications = process_arrival_notifications(df)
    departure_notifications = process_departure_notifications(df)
    
    return {
        'monthly_revenue_list': monthly_revenue_list,
        'genius_stats_list': genius_stats_list,
        'monthly_guests_list': monthly_guests_list,
        'weekly_guests_list': weekly_guests_list,
        'monthly_collected_revenue_list': monthly_collected_revenue_list,
        'monthly_revenue_chart_json': monthly_revenue_chart_json,
        'monthly_revenue_with_unpaid': monthly_revenue_with_unpaid,
        'overdue_unpaid_guests': overdue_unpaid_guests,
        'overdue_total_amount': overdue_total_amount,
        'overcrowded_days': overcrowded_days,
        'daily_totals': daily_totals,
        'collector_chart_json': collector_chart_data,
        'arrival_notifications': arrival_notifications,
        'departure_notifications': departure_notifications
    }


def create_revenue_chart(monthly_revenue_list):
    """Tạo biểu đồ doanh thu hàng tháng"""
    monthly_revenue_df = pd.DataFrame(monthly_revenue_list)
    
    if monthly_revenue_df.empty:
        return {}
    
    try:
        # Sắp xếp lại theo tháng
        monthly_revenue_df_sorted = monthly_revenue_df.sort_values('Tháng')
        
        # Tạo biểu đồ combo: line + bar
        fig = px.line(monthly_revenue_df_sorted, x='Tháng', y='Doanh thu', 
                     title='📊 Doanh thu Hàng tháng', markers=True)
        
        # Thêm bar chart
        fig.add_bar(x=monthly_revenue_df_sorted['Tháng'], 
                   y=monthly_revenue_df_sorted['Doanh thu'],
                   name='Doanh thu', opacity=0.3, yaxis='y')
        
        # Cải thiện layout
        fig.update_layout(
            title={'text': '📊 Doanh thu Hàng tháng (Tất cả thời gian)', 'x': 0.5,
                   'font': {'size': 18, 'family': 'Arial, sans-serif', 'color': '#2c3e50'}},
            xaxis_title='Tháng', yaxis_title='Doanh thu (VND)',
            hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)', height=400, showlegend=True,
            font={'family': 'Arial, sans-serif', 'size': 12},
            margin=dict(l=60, r=30, t=80, b=50)
        )
        
        # Cải thiện axes và traces
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)', tickformat=',.0f')
        fig.update_traces(line=dict(width=3, color='#3498db'), 
                         marker=dict(size=8, color='#e74c3c'), selector=dict(type='scatter'))
        fig.update_traces(marker=dict(color='#3498db', opacity=0.3), selector=dict(type='bar'))
        
        return json.loads(fig.to_json())
    
    except Exception as e:
        print(f"Chart creation error: {e}")
        return {}


def process_overdue_guests(df):
    """Xử lý logic khách chưa thu tiền quá hạn"""
    overdue_unpaid_guests = []
    overdue_total_amount = 0
    
    try:
        if df.empty or 'Check-in Date' not in df.columns:
            return overdue_unpaid_guests, overdue_total_amount
            
        today = datetime.today().date()
        df_work = df.copy()
        
        # Convert dates
        df_work['Check-in Date'] = pd.to_datetime(df_work['Check-in Date'], errors='coerce', dayfirst=True)
        valid_dates_mask = df_work['Check-in Date'].notna()
        
        if not valid_dates_mask.any():
            return overdue_unpaid_guests, overdue_total_amount
            
        df_valid = df_work[valid_dates_mask].copy()
        
        # Create filters
        past_checkin = df_valid['Check-in Date'].dt.date <= today
        collected_values = ['LOC LE', 'THAO LE']
        collector_series = df_valid['Người thu tiền'].fillna('').astype(str)
        not_collected = ~collector_series.isin(collected_values)
        not_cancelled = df_valid['Tình trạng'] != 'Đã hủy'
        
        overdue_mask = past_checkin & not_collected & not_cancelled
        overdue_df = df_valid[overdue_mask].copy()
        
        if not overdue_df.empty:
            # Calculate overdue days
            checkin_dates = overdue_df['Check-in Date'].dt.date
            days_overdue_list = [(today - date).days if date else 0 for date in checkin_dates]
            overdue_df['days_overdue'] = [max(0, days) for days in days_overdue_list]
            
            # Calculate total amount including taxi fees
            overdue_df = overdue_df.sort_values('days_overdue', ascending=False)
            
            # Calculate room fees
            room_total = 0
            if 'Tổng thanh toán' in overdue_df.columns:
                room_total = pd.to_numeric(overdue_df['Tổng thanh toán'], errors='coerce').fillna(0).sum()
            
            # Calculate taxi fees
            taxi_total = 0
            if 'Taxi' in overdue_df.columns:
                # Extract numeric values from taxi column (handles formats like "50,000đ", "50000", etc.)
                taxi_series = overdue_df['Taxi'].fillna('').astype(str)
                for taxi_value in taxi_series:
                    if taxi_value and taxi_value.strip():
                        # Remove currency symbols and commas, extract numbers
                        import re
                        numeric_match = re.search(r'[\d,]+', taxi_value.replace('.', ''))
                        if numeric_match:
                            try:
                                taxi_amount = float(numeric_match.group().replace(',', ''))
                                taxi_total += taxi_amount
                            except ValueError:
                                pass
            
            # Total amount = room fees + taxi fees
            overdue_total_amount = room_total + taxi_total
            
            # Add calculated totals to DataFrame BEFORE converting to records
            calculated_room_fees = []
            calculated_taxi_fees = []
            calculated_total_amounts = []
            
            for idx, (_, guest_row) in enumerate(overdue_df.iterrows()):
                # Fix: Better room fee calculation
                guest_room_payment = guest_row.get('Tổng thanh toán', 0)
                if guest_room_payment is not None and guest_room_payment != '':
                    try:
                        guest_room_fee = float(guest_room_payment)
                    except (ValueError, TypeError):
                        guest_room_fee = 0
                else:
                    guest_room_fee = 0
                
                guest_taxi_fee = 0
                
                # Fix: Better taxi fee extraction for this guest
                taxi_value = guest_row.get('Taxi', '')
                if taxi_value and str(taxi_value).strip() and str(taxi_value).strip() not in ['nan', 'None', 'N/A']:
                    import re
                    # More robust regex to handle various formats
                    taxi_str = str(taxi_value).replace('.', '').replace(' ', '')
                    numeric_match = re.search(r'(\d{1,3}(?:,\d{3})*|\d+)', taxi_str)
                    if numeric_match:
                        try:
                            guest_taxi_fee = float(numeric_match.group().replace(',', ''))
                        except ValueError:
                            guest_taxi_fee = 0
                
                calculated_room_fees.append(guest_room_fee)
                calculated_taxi_fees.append(guest_taxi_fee)  
                calculated_total_amounts.append(guest_room_fee + guest_taxi_fee)
            
            # Add calculated columns to DataFrame
            overdue_df['calculated_room_fee'] = calculated_room_fees
            overdue_df['calculated_taxi_fee'] = calculated_taxi_fees
            overdue_df['calculated_total_amount'] = calculated_total_amounts
            
            overdue_unpaid_guests = overdue_df.to_dict('records')
    
    except Exception as e:
        print(f"Process overdue guests error: {e}")
    
    return overdue_unpaid_guests, overdue_total_amount


def process_monthly_revenue_with_unpaid(df, start_date, end_date):
    """Xử lý doanh thu theo tháng bao gồm khách chưa thu"""
    monthly_revenue_with_unpaid = []
    
    try:
        if df.empty or 'Check-in Date' not in df.columns:
            return monthly_revenue_with_unpaid
            
        df_period = df[
            (df['Check-in Date'] >= pd.Timestamp(start_date)) & 
            (df['Check-in Date'] <= pd.Timestamp(end_date)) &
            (df['Check-in Date'] <= pd.Timestamp.now()) &
            (df['Check-in Date'].notna())
        ].copy()
        
        if df_period.empty:
            return monthly_revenue_with_unpaid
            
        # Tính doanh thu đã thu và chưa thu
        collected_df = df_period[df_period['Người thu tiền'].isin(['LOC LE', 'THAO LE'])].copy()
        uncollected_df = df_period[~df_period['Người thu tiền'].isin(['LOC LE', 'THAO LE'])].copy()
        
        # Process collected revenue
        if not collected_df.empty:
            collected_df['Month_Period'] = collected_df['Check-in Date'].dt.to_period('M')
            collected_monthly = collected_df.groupby('Month_Period').agg({'Tổng thanh toán': 'sum'}).reset_index()
            collected_monthly['Tháng'] = collected_monthly['Month_Period'].dt.strftime('%Y-%m')
        else:
            collected_monthly = pd.DataFrame(columns=['Tháng', 'Tổng thanh toán'])
        
        # Process uncollected revenue
        if not uncollected_df.empty:
            uncollected_df['Month_Period'] = uncollected_df['Check-in Date'].dt.to_period('M')
            uncollected_monthly = uncollected_df.groupby('Month_Period').agg({
                'Tổng thanh toán': 'sum', 'Số đặt phòng': 'count'
            }).reset_index()
            uncollected_monthly['Tháng'] = uncollected_monthly['Month_Period'].dt.strftime('%Y-%m')
            uncollected_monthly = uncollected_monthly.rename(columns={'Số đặt phòng': 'Số khách chưa thu'})
        else:
            uncollected_monthly = pd.DataFrame(columns=['Tháng', 'Tổng thanh toán', 'Số khách chưa thu'])
        
        # Merge data
        if not collected_monthly.empty and not uncollected_monthly.empty:
            merged_data = pd.merge(
                collected_monthly[['Tháng', 'Tổng thanh toán']].rename(columns={'Tổng thanh toán': 'Đã thu'}),
                uncollected_monthly[['Tháng', 'Tổng thanh toán', 'Số khách chưa thu']].rename(columns={'Tổng thanh toán': 'Chưa thu'}),
                on='Tháng', how='outer'
            ).fillna(0)
        elif not collected_monthly.empty:
            merged_data = collected_monthly.rename(columns={'Tổng thanh toán': 'Đã thu'})
            merged_data[['Chưa thu', 'Số khách chưa thu']] = 0
        elif not uncollected_monthly.empty:
            merged_data = uncollected_monthly.rename(columns={'Tổng thanh toán': 'Chưa thu'})
            merged_data['Đã thu'] = 0
        else:
            merged_data = pd.DataFrame(columns=['Tháng', 'Đã thu', 'Chưa thu', 'Số khách chưa thu'])
        
        if not merged_data.empty:
            merged_data = merged_data.sort_values('Tháng')
            monthly_revenue_with_unpaid = safe_to_dict_records(merged_data)
    
    except Exception as e:
        print(f"Process monthly revenue error: {e}")
    
    return monthly_revenue_with_unpaid


def detect_overcrowded_days(df):
    """Phát hiện ngày có quá 4 khách check-in"""
    overcrowded_days = []
    
    try:
        if df.empty or 'Check-in Date' not in df.columns:
            return overcrowded_days
            
        today = datetime.today()
        check_start = today - timedelta(days=30)
        check_end = today + timedelta(days=30)
        
        df_check = df.copy()
        df_check['Check-in Date'] = pd.to_datetime(df_check['Check-in Date'], errors='coerce', dayfirst=True)
        
        valid_checkins = df_check[
            (df_check['Check-in Date'].notna()) &
            (df_check['Check-in Date'] >= pd.Timestamp(check_start)) &
            (df_check['Check-in Date'] <= pd.Timestamp(check_end)) &
            (df_check['Tình trạng'] != 'Đã hủy')
        ].copy()
        
        if valid_checkins.empty:
            return overcrowded_days
            
        # Group by date and count guests + calculate daily totals
        daily_checkins = valid_checkins.groupby(valid_checkins['Check-in Date'].dt.date).agg({
            'Số đặt phòng': ['count', lambda x: list(x)],
            'Tên người đặt': lambda x: list(x),
            'Tổng thanh toán': ['sum', lambda x: list(x)]
        })
        daily_checkins.columns = ['guest_count', 'booking_ids', 'guest_names', 'daily_total', 'individual_amounts']
        
        # Find overcrowded dates (>4 guests)
        overcrowded_dates = daily_checkins[daily_checkins['guest_count'] > 4]
        
        for date, row in overcrowded_dates.iterrows():
            days_from_today = (date - today.date()).days
            
            # Classify alert level
            if days_from_today < 0:
                alert_level, alert_color = 'past', 'secondary'
            elif days_from_today <= 3:
                alert_level, alert_color = 'urgent', 'danger'
            elif days_from_today <= 7:
                alert_level, alert_color = 'warning', 'warning'
            else:
                alert_level, alert_color = 'info', 'info'
            
            overcrowded_days.append({
                'date': date, 'guest_count': row['guest_count'],
                'booking_ids': row['booking_ids'], 'guest_names': row['guest_names'],
                'daily_total': row['daily_total'], 'individual_amounts': row['individual_amounts'],
                'days_from_today': days_from_today, 'alert_level': alert_level,
                'alert_color': alert_color, 'is_today': days_from_today == 0,
                'is_future': days_from_today > 0
            })
        
        # Sort by proximity to today
        overcrowded_days.sort(key=lambda x: abs(x['days_from_today']))
    
    except Exception as e:
        print(f"Detect overcrowded days error: {e}")
    
    return overcrowded_days


def get_daily_totals(df):
    """Tính tổng doanh thu theo ngày cho calendar"""
    daily_totals = []
    
    try:
        if df.empty or 'Check-in Date' not in df.columns:
            return daily_totals
            
        today = datetime.today()
        check_start = today - timedelta(days=7)  # 7 days ago
        check_end = today + timedelta(days=14)   # 14 days ahead
        
        df_check = df.copy()
        df_check['Check-in Date'] = pd.to_datetime(df_check['Check-in Date'], errors='coerce', dayfirst=True)
        
        valid_checkins = df_check[
            (df_check['Check-in Date'].notna()) &
            (df_check['Check-in Date'] >= pd.Timestamp(check_start)) &
            (df_check['Check-in Date'] <= pd.Timestamp(check_end)) &
            (df_check['Tình trạng'] != 'Đã hủy')
        ].copy()
        
        if valid_checkins.empty:
            return daily_totals
            
        # Group by date and calculate totals
        daily_checkins = valid_checkins.groupby(valid_checkins['Check-in Date'].dt.date).agg({
            'Số đặt phòng': ['count', lambda x: list(x)],
            'Tên người đặt': lambda x: list(x),
            'Tổng thanh toán': ['sum', lambda x: list(x)]
        })
        daily_checkins.columns = ['guest_count', 'booking_ids', 'guest_names', 'daily_total', 'individual_amounts']
        
        for date, row in daily_checkins.iterrows():
            days_from_today = (date - today.date()).days
            
            daily_totals.append({
                'date': date,
                'guest_count': row['guest_count'],
                'booking_ids': row['booking_ids'],
                'guest_names': row['guest_names'],
                'daily_total': row['daily_total'],
                'individual_amounts': row['individual_amounts'],
                'days_from_today': days_from_today,
                'is_today': days_from_today == 0,
                'is_future': days_from_today > 0
            })
        
        # Sort by date
        daily_totals.sort(key=lambda x: x['date'])
    
    except Exception as e:
        print(f"Get daily totals error: {e}")
    
    return daily_totals


def get_daily_revenue_by_stay(df):
    """Calculate daily revenue by dividing total booking amount by stay duration"""
    daily_revenue = {}
    
    try:
        if df.empty:
            return daily_revenue
            
        today = datetime.today()
        check_start = today - timedelta(days=30)  # 30 days ago
        check_end = today + timedelta(days=60)    # 60 days ahead
        
        df_clean = df.copy()
        
        # Parse dates
        df_clean['Check-in Date'] = pd.to_datetime(df_clean['Check-in Date'], errors='coerce', dayfirst=True)
        df_clean['Check-out Date'] = pd.to_datetime(df_clean['Check-out Date'], errors='coerce', dayfirst=True)
        
        # Filter valid bookings
        valid_bookings = df_clean[
            (df_clean['Check-in Date'].notna()) &
            (df_clean['Check-out Date'].notna()) &
            (df_clean['Check-in Date'] >= pd.Timestamp(check_start)) &
            (df_clean['Check-in Date'] <= pd.Timestamp(check_end)) &
            (df_clean['Tình trạng'] != 'Đã hủy') &
            (df_clean['Tổng thanh toán'].notna()) &
            (df_clean['Tổng thanh toán'] > 0)
        ].copy()
        
        if valid_bookings.empty:
            return daily_revenue
        
        for _, booking in valid_bookings.iterrows():
            checkin_date = booking['Check-in Date'].date()
            checkout_date = booking['Check-out Date'].date()
            total_amount = float(booking['Tổng thanh toán'])
            
            # Calculate number of nights
            nights = (checkout_date - checkin_date).days
            if nights <= 0:
                nights = 1  # Minimum 1 night
            
            # Calculate daily rate
            daily_rate = total_amount / nights
            
            # Add daily rate to each date in the stay
            current_date = checkin_date
            while current_date < checkout_date:
                if current_date not in daily_revenue:
                    daily_revenue[current_date] = {
                        'daily_total': 0,
                        'guest_count': 0,
                        'bookings': []
                    }
                
                daily_revenue[current_date]['daily_total'] += daily_rate
                daily_revenue[current_date]['guest_count'] += 1
                daily_revenue[current_date]['bookings'].append({
                    'guest_name': booking.get('Tên người đặt', 'N/A'),
                    'booking_id': booking.get('Số đặt phòng', 'N/A'),
                    'daily_amount': daily_rate,
                    'total_amount': total_amount,
                    'nights': nights,
                    'checkin': checkin_date,
                    'checkout': checkout_date
                })
                
                current_date += timedelta(days=1)
        
        print(f"✅ Calculated daily revenue for {len(daily_revenue)} dates")
        
    except Exception as e:
        print(f"Error calculating daily revenue by stay: {e}")
        import traceback
        traceback.print_exc()
    
    return daily_revenue


def create_collector_chart(dashboard_data):
    """Tạo biểu đồ donut chart cho người thu tiền"""
    collector_revenue_data = safe_to_dict_records(dashboard_data.get('collector_revenue_selected', pd.DataFrame()))
    
    return {
        'data': [{
            'type': 'pie',
            'labels': [row['Người thu tiền'] for row in collector_revenue_data],
            'values': [row['Tổng thanh toán'] for row in collector_revenue_data],
            'textinfo': 'label+value', 'textposition': 'auto',
            'hovertemplate': '<b>%{label}</b><br>Doanh thu: %{value:,.0f}đ<br>Tỷ lệ: %{percent}<br><extra></extra>',
            'texttemplate': '%{label}<br>%{value:,.0f}đ',
            'marker': {
                'colors': ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c'],
                'line': {'color': '#ffffff', 'width': 3}
            },
            'hole': 0.4,
            'textfont': {'size': 12, 'family': 'Arial Bold', 'color': '#2c3e50'},
            'pull': [0.05 if i == 0 else 0 for i in range(len(collector_revenue_data))]
        }],
        'layout': {
            'title': {'text': '💰 Doanh thu theo Người thu', 'x': 0.5, 'y': 0.95,
                     'font': {'size': 16, 'family': 'Arial Bold', 'color': '#2c3e50'}},
            'showlegend': True, 'height': 300,
            'legend': {'orientation': 'v', 'x': 1.05, 'y': 0.5,
                      'font': {'size': 12, 'family': 'Arial', 'color': '#2c3e50'}},
            'margin': {'l': 20, 'r': 120, 't': 40, 'b': 20},
            'plot_bgcolor': 'rgba(248,249,250,0.8)', 'paper_bgcolor': 'rgba(0,0,0,0)',
            'font': {'family': 'Arial, sans-serif', 'size': 12, 'color': '#2c3e50'},
            'annotations': [{
                'text': f'<b>Tổng</b><br>{sum([row["Tổng thanh toán"] for row in collector_revenue_data]):,.0f}đ',
                'x': 0.5, 'y': 0.5,
                'font': {'size': 14, 'family': 'Arial Bold', 'color': '#2c3e50'},
                'showarrow': False
            }]
        }
    }


def process_arrival_notifications(df):
    """
    Xử lý thông báo khách đến - chỉ hiển thị khách đến hôm nay và ngày mai
    """
    try:
        if df.empty:
            return []
        
        # Ngày hôm nay và ngày mai
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        notifications = []
        
        # Lọc khách check-in - chỉ xử lý khách đến từ hôm nay trở đi
        for index, row in df.iterrows():
            try:
                checkin_date = row.get('Check-in Date')
                if checkin_date:
                    # Xử lý nhiều định dạng ngày
                    if isinstance(checkin_date, str):
                        try:
                            checkin_date = datetime.strptime(checkin_date, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                checkin_date = datetime.strptime(checkin_date, '%d/%m/%Y').date()
                            except ValueError:
                                continue
                    elif hasattr(checkin_date, 'date'):
                        checkin_date = checkin_date.date()
                    
                    # Bỏ qua khách đã check-in trước hôm nay
                    if checkin_date < today:
                        continue
                    
                    # Khách đến ngày mai
                    if checkin_date == tomorrow:
                        guest_name = row.get('Tên người đặt', 'Không có tên')
                        booking_id = row.get('Số đặt phòng', 'N/A')
                        total_amount = row.get('Tổng thanh toán', 0)
                        hoa_hong = row.get('Hoa hồng', 0)
                        
                        notifications.append({
                            'type': 'arrival',
                            'priority': 'high',
                            'guest_name': guest_name,
                            'booking_id': booking_id,
                            'checkin_date': checkin_date.strftime('%d/%m/%Y'),
                            'total_amount': total_amount,
                            'Hoa hồng': hoa_hong,
                            'days_until': 1,
                            'message': f'Khách {guest_name} sẽ đến vào ngày mai ({checkin_date.strftime("%d/%m/%Y")})'
                        })
                    
                    # Khách đến hôm nay
                    elif checkin_date == today:
                        guest_name = row.get('Tên người đặt', 'Không có tên')
                        booking_id = row.get('Số đặt phòng', 'N/A')
                        total_amount = row.get('Tổng thanh toán', 0)
                        hoa_hong = row.get('Hoa hồng', 0)
                        
                        notifications.append({
                            'type': 'arrival',
                            'priority': 'urgent',
                            'guest_name': guest_name,
                            'booking_id': booking_id,
                            'checkin_date': checkin_date.strftime('%d/%m/%Y'),
                            'total_amount': total_amount,
                            'Hoa hồng': hoa_hong,
                            'days_until': 0,
                            'message': f'Khách {guest_name} đến HÔM NAY ({checkin_date.strftime("%d/%m/%Y")})'
                        })
                        
            except Exception as e:
                print(f"Error processing arrival for row {index}: {e}")
                continue
        
        # Sắp xếp theo độ ưu tiên
        notifications.sort(key=lambda x: (x['days_until'], x['guest_name']))
        
        return notifications
        
    except Exception as e:
        print(f"Error in process_arrival_notifications: {e}")
        return []


def process_departure_notifications(df):
    """
    Xử lý thông báo khách đi - hiển thị 1 ngày trước để chuẩn bị taxi/dịch vụ
    """
    try:
        if df.empty:
            return []
        
        # Ngày hôm nay và ngày mai
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        notifications = []
        
        # Lọc khách check-out ngày mai (để chuẩn bị dịch vụ)
        for index, row in df.iterrows():
            try:
                checkout_date = row.get('Check-out Date')
                if checkout_date:
                    # Xử lý nhiều định dạng ngày
                    if isinstance(checkout_date, str):
                        try:
                            checkout_date = datetime.strptime(checkout_date, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                checkout_date = datetime.strptime(checkout_date, '%d/%m/%Y').date()
                            except ValueError:
                                continue
                    elif hasattr(checkout_date, 'date'):
                        checkout_date = checkout_date.date()
                    
                    # Khách đi ngày mai
                    if checkout_date == tomorrow:
                        guest_name = row.get('Tên người đặt', 'Không có tên')
                        booking_id = row.get('Số đặt phòng', 'N/A')
                        total_amount = row.get('Tổng thanh toán', 0)
                        
                        notifications.append({
                            'type': 'departure',
                            'priority': 'high',
                            'guest_name': guest_name,
                            'booking_id': booking_id,
                            'checkout_date': checkout_date.strftime('%d/%m/%Y'),
                            'total_amount': total_amount,
                            'days_until': 1,
                            'message': f'Khách {guest_name} sẽ đi vào ngày mai ({checkout_date.strftime("%d/%m/%Y")}) - Chuẩn bị taxi/dịch vụ'
                        })
                    
                    # Khách đi hôm nay
                    elif checkout_date == today:
                        guest_name = row.get('Tên người đặt', 'Không có tên')
                        booking_id = row.get('Số đặt phòng', 'N/A')
                        total_amount = row.get('Tổng thanh toán', 0)
                        
                        notifications.append({
                            'type': 'departure',
                            'priority': 'urgent',
                            'guest_name': guest_name,
                            'booking_id': booking_id,
                            'checkout_date': checkout_date.strftime('%d/%m/%Y'),
                            'total_amount': total_amount,
                            'days_until': 0,
                            'message': f'Khách {guest_name} đi HÔM NAY ({checkout_date.strftime("%d/%m/%Y")}) - Hỗ trợ taxi ngay'
                        })
                        
            except Exception as e:
                print(f"Error processing departure for row {index}: {e}")
                continue
        
        # Sắp xếp theo độ ưu tiên
        notifications.sort(key=lambda x: (x['days_until'], x['guest_name']))
        
        return notifications
        
    except Exception as e:
        print(f"Error in process_departure_notifications: {e}")
        return []
