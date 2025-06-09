#!/usr/bin/env python3
"""Test script to verify imports work correctly"""

try:
    print("Testing imports...")
    
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
    
    print("SUCCESS: All imports successful!")
    print(f"SUCCESS: import_from_gsheet function: {type(import_from_gsheet)}")
    
except ImportError as e:
    print(f"ERROR: Import error: {e}")
    
except Exception as e:
    print(f"ERROR: Other error: {e}")
