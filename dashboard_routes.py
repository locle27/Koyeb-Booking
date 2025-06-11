# dashboard_routes.py - Dashboard logic module
from flask import render_template, request
from datetime import datetime, timedelta
import calendar
import pandas as pd
import plotly.express as px
import json


def process_dashboard_data(df, start_date, end_date, sort_by, sort_order, dashboard_data):
    """
    Xử lý dữ liệu dashboard phức tạp
    """
    # Chuẩn bị dữ liệu cho template
    monthly_revenue_list = dashboard_data.get('monthly_revenue_all_time', pd.DataFrame()).to_dict('records')
    genius_stats_list = dashboard_data.get('genius_stats', pd.DataFrame()).to_dict('records')
    monthly_guests_list = dashboard_data.get('monthly_guests_all_time', pd.DataFrame()).to_dict('records')
    weekly_guests_list = dashboard_data.get('weekly_guests_all_time', pd.DataFrame()).to_dict('records')
    monthly_collected_revenue_list = dashboard_data.get('monthly_collected_revenue', pd.DataFrame()).to_dict('records')

    # Tạo biểu đồ doanh thu hàng tháng
    monthly_revenue_chart_json = create_revenue_chart(monthly_revenue_list)
    
    # Xử lý khách chưa thu tiền quá hạn
    overdue_unpaid_guests, overdue_total_amount = process_overdue_guests(df)
    
    # Xử lý doanh thu theo tháng có bao gồm số khách chưa thu
    monthly_revenue_with_unpaid = process_monthly_revenue_with_unpaid(df, start_date, end_date)
    
    # Phát hiện ngày có quá nhiều khách
    overcrowded_days = detect_overcrowded_days(df)
    
    # Tạo biểu đồ pie chart cho người thu tiền
    collector_chart_data = create_collector_chart(dashboard_data)
    
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
        'collector_chart_json': collector_chart_data
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
            
            # Sort and calculate total
            overdue_df = overdue_df.sort_values('days_overdue', ascending=False)
            if 'Tổng thanh toán' in overdue_df.columns:
                overdue_total_amount = pd.to_numeric(overdue_df['Tổng thanh toán'], errors='coerce').fillna(0).sum()
            
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
            monthly_revenue_with_unpaid = merged_data.to_dict('records')
    
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
            
        # Group by date and count guests
        daily_checkins = valid_checkins.groupby(valid_checkins['Check-in Date'].dt.date).agg({
            'Số đặt phòng': ['count', lambda x: list(x)],
            'Tên người đặt': lambda x: list(x)
        })
        daily_checkins.columns = ['guest_count', 'booking_ids', 'guest_names']
        
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
                'days_from_today': days_from_today, 'alert_level': alert_level,
                'alert_color': alert_color, 'is_today': days_from_today == 0,
                'is_future': days_from_today > 0
            })
        
        # Sort by proximity to today
        overcrowded_days.sort(key=lambda x: abs(x['days_from_today']))
    
    except Exception as e:
        print(f"Detect overcrowded days error: {e}")
    
    return overcrowded_days


def create_collector_chart(dashboard_data):
    """Tạo biểu đồ donut chart cho người thu tiền"""
    collector_revenue_data = dashboard_data.get('collector_revenue_selected', pd.DataFrame()).to_dict('records')
    
    return {
        'data': [{
            'type': 'pie',
            'labels': [row['Người thu tiền'] for row in collector_revenue_data],
            'values': [row['Tổng thanh toán'] for row in collector_revenue_data],
            'textinfo': 'label+percent', 'textposition': 'auto',
            'hovertemplate': '<b>%{label}</b><br>Doanh thu: %{value:,.0f}đ<br>Tỷ lệ: %{percent}<br><extra></extra>',
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
