import sys
sys.stdout.reconfigure(encoding='utf-8')

# Simple test to check data directly from app
import pandas as pd
from datetime import datetime

# Create sample data to test the filters
test_data = {
    'Số đặt phòng': ['6794271870'],
    'Tên người đặt': ['Amaury Garde'],
    'Check-in Date': [pd.NaT],  # This simulates the issue
    'Check-out Date': [pd.NaT],
    'Tổng thanh toán': [837900]
}

df = pd.DataFrame(test_data)

print("=== TESTING DATE FILTERS ===")
print(f"Original data:")
print(df.dtypes)
print(df)

# Test the filters like in app.py
def safe_date_format(date_value, format_string='%d/%m/%y'):
    """Test safe_date_format filter"""
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

def is_valid_date(date_value):
    """Test is_valid_date filter"""
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

# Test both functions
for index, row in df.iterrows():
    booking_id = row['Số đặt phòng']
    checkin_date = row['Check-in Date']
    checkout_date = row['Check-out Date']
    
    print(f"\n=== BOOKING {booking_id} ===")
    print(f"Check-in Date:")
    print(f"  Raw value: {repr(checkin_date)}")
    print(f"  Type: {type(checkin_date)}")
    print(f"  pd.isna(): {pd.isna(checkin_date)}")
    print(f"  is_valid_date(): {is_valid_date(checkin_date)}")
    print(f"  safe_date_format(): {safe_date_format(checkin_date)}")
    
    print(f"Check-out Date:")
    print(f"  Raw value: {repr(checkout_date)}")
    print(f"  Type: {type(checkout_date)}")
    print(f"  pd.isna(): {pd.isna(checkout_date)}")
    print(f"  is_valid_date(): {is_valid_date(checkout_date)}")
    print(f"  safe_date_format(): {safe_date_format(checkout_date)}")

print("\n=== TESTING WITH REAL DATE ===")
# Test with real date
real_date = pd.to_datetime('2024-12-15')
print(f"Real date: {real_date}")
print(f"is_valid_date(): {is_valid_date(real_date)}")
print(f"safe_date_format(): {safe_date_format(real_date)}")
