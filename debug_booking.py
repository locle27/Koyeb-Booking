#!/usr/bin/env python3
import pandas as pd
import os
from logic import import_from_gsheet
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Get configuration
GCP_CREDS_FILE_PATH = os.getenv("GCP_CREDS_FILE_PATH")
DEFAULT_SHEET_ID = os.getenv("DEFAULT_SHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")

def debug_specific_booking():
    """Debug booking ID 6794271870"""
    try:
        # Load data from Google Sheets
        print("Loading data from Google Sheets...")
        df = import_from_gsheet(DEFAULT_SHEET_ID, GCP_CREDS_FILE_PATH, WORKSHEET_NAME)
        
        if df.empty:
            print("ERROR: No data loaded!")
            return
        
        print(f"Total bookings loaded: {len(df)}")
        
        # Find specific booking
        booking_id = "6794271870"
        booking_df = df[df['Số đặt phòng'] == booking_id]
        
        if booking_df.empty:
            print(f"ERROR: Booking {booking_id} not found!")
            # Show all booking IDs for reference
            print("Available booking IDs:", df['Số đặt phòng'].tolist()[:10])
            return
        
        booking = booking_df.iloc[0]
        
        print(f"\n=== BOOKING DEBUG: {booking_id} ===")
        print(f"Guest Name: {booking.get('Tên người đặt', 'N/A')}")
        print(f"Total Payment: {booking.get('Tổng thanh toán', 'N/A')}")
        
        # Check date columns specifically
        for date_col in ['Check-in Date', 'Check-out Date']:
            if date_col in booking.index:
                raw_value = booking[date_col]
                print(f"\n--- {date_col} DEBUG ---")
                print(f"Raw value: {repr(raw_value)}")
                print(f"Type: {type(raw_value)}")
                print(f"String representation: {str(raw_value)}")
                print(f"Is null (pandas): {pd.isna(raw_value)}")
                print(f"Is None: {raw_value is None}")
                
                # Try to convert to datetime
                try:
                    if pd.isna(raw_value):
                        print("Value is NaT/NaN - will show N/A")
                    elif hasattr(raw_value, 'strftime'):
                        formatted = raw_value.strftime('%d/%m/%y')
                        day_name = raw_value.strftime('%A')
                        print(f"Formatted date: {formatted}")
                        print(f"Day name: {day_name}")
                        print("✅ Should display correctly")
                    else:
                        # Try to parse as datetime
                        parsed_date = pd.to_datetime(raw_value, errors='coerce')
                        if pd.isna(parsed_date):
                            print("❌ Cannot parse as datetime - will show N/A")
                        else:
                            print(f"Parsed date: {parsed_date}")
                            print(f"Formatted: {parsed_date.strftime('%d/%m/%y')}")
                            print("✅ Should display correctly after parsing")
                except Exception as e:
                    print(f"❌ Error processing date: {e}")
        
        # Check all columns and their data types
        print(f"\n--- ALL COLUMNS FOR BOOKING {booking_id} ---")
        for col in df.columns:
            value = booking[col]
            print(f"{col}: {repr(value)} (type: {type(value)})")
        
        # Check data types of entire dataframe
        print(f"\n--- DATAFRAME COLUMN TYPES ---")
        print(df.dtypes)
        
        # Check if there are any datetime conversion issues
        print(f"\n--- DATE COLUMN ANALYSIS ---")
        for date_col in ['Check-in Date', 'Check-out Date']:
            if date_col in df.columns:
                print(f"\n{date_col}:")
                print(f"  dtype: {df[date_col].dtype}")
                print(f"  null count: {df[date_col].isna().sum()}")
                print(f"  unique values (first 5): {df[date_col].unique()[:5]}")
                
                # Check if column has datetime objects
                has_datetime = df[date_col].apply(lambda x: hasattr(x, 'strftime')).sum()
                print(f"  rows with datetime objects: {has_datetime}/{len(df)}")
        
    except Exception as e:
        print(f"ERROR in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_specific_booking()
