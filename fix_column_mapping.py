"""
Fixed Column Mapping - Micro Step 2
Sửa lỗi mapping columns trong save_extracted_bookings function
"""

# EXACT HEADER MAPPING từ Google Sheets analysis
GOOGLE_SHEETS_COLUMN_MAPPING = {
    # Core booking info
    'booking_id': 'Số đặt phòng',           # Position 1
    'guest_name': 'Tên người đặt',          # Position 2  
    'room_type': 'Tên chỗ nghỉ',            # Position 3
    'check_in_date': 'Check-in Date',       # Position 4
    'check_out_date': 'Check-out Date',     # Position 5
    'stay_duration': 'Stay Duration',       # Position 6
    'status': 'Tình trạng',                 # Position 7
    'total_payment': 'Tổng thanh toán',     # Position 8
    'price_per_night': 'Giá mỗi đêm',       # Position 9
    'booking_date': 'Booking Date',         # Position 10
    
    # Vietnamese formatted dates
    'checkin_vn': 'Ngày đến',               # Position 11
    'checkout_vn': 'Ngày đi',               # Position 12
    
    # Additional info
    'location': 'Vị trí',                   # Position 13
    'genius_member': 'Thành viên Genius',   # Position 14
    'booked_on': 'Được đặt vào',            # Position 15
    'commission': 'Hoa hồng',               # Position 16
    'currency': 'Tiền tệ',                  # Position 17
    'money_receiver': 'Người nhận tiền',    # Position 18
    'payment_note': 'Ghi chú thanh toán',   # Position 19
    'money_collector': 'Người thu tiền',    # Position 20
    'taxi': 'Taxi'                          # Position 21
}

def create_formatted_booking_fixed(booking, i):
    """
    Tạo formatted booking với mapping chính xác
    """
    import datetime
    
    # Generate booking ID
    booking_id = booking.get('booking_id', '').strip() or f"IMG_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{i:02d}"
    
    # Validate and normalize dates
    check_in_date = booking.get('check_in_date', '').strip()
    check_out_date = booking.get('check_out_date', '').strip()
    
    # Validate dates
    try:
        if check_in_date:
            check_in_parsed = datetime.datetime.strptime(check_in_date, '%Y-%m-%d')
            check_in_date = check_in_parsed.strftime('%Y-%m-%d')
    except ValueError:
        print(f"WARNING: Invalid check-in date format: {check_in_date}")
        check_in_date = ''
    
    try:
        if check_out_date:
            check_out_parsed = datetime.datetime.strptime(check_out_date, '%Y-%m-%d')
            check_out_date = check_out_parsed.strftime('%Y-%m-%d')
    except ValueError:
        print(f"WARNING: Invalid check-out date format: {check_out_date}")
        check_out_date = ''
    
    # Calculate stay duration
    stay_duration = ''
    if check_in_date and check_out_date:
        try:
            checkin_dt = datetime.datetime.strptime(check_in_date, '%Y-%m-%d')
            checkout_dt = datetime.datetime.strptime(check_out_date, '%Y-%m-%d')
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
    
    # Create formatted booking using EXACT column names
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
        'Booking Date': datetime.datetime.now().strftime('%Y-%m-%d'),
        'Ngày đến': checkin_vn,
        'Ngày đi': checkout_vn,
        'Vị trí': 'N/A (Chưa xác định)',
        'Thành viên Genius': 'Không',
        'Được đặt vào': datetime.datetime.now().strftime('%d tháng %m, %Y'),
        'Hoa hồng': booking.get('commission', 0) or 0,
        'Tiền tệ': 'VND',
        'Người nhận tiền': '',
        'Ghi chú thanh toán': f"Thêm từ ảnh lúc {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
        'Người thu tiền': '',
        'Taxi': ''
    }
    
    return formatted_booking

# Test the function
if __name__ == "__main__":
    # Test with sample booking data
    sample_booking = {
        'guest_name': 'Test User',
        'booking_id': '12345',
        'check_in_date': '2025-06-15',
        'check_out_date': '2025-06-17', 
        'room_type': 'Standard Room',
        'total_payment': 500000,
        'commission': 50000
    }
    
    result = create_formatted_booking_fixed(sample_booking, 1)
    print("FORMATTED BOOKING TEST:")
    print("=" * 50)
    for key, value in result.items():
        print(f"'{key}': '{value}'")
    
    print(f"\nTotal fields: {len(result)}")
    print("Column mapping completed successfully!")
