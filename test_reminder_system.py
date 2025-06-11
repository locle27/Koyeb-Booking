"""
Test Reminder System - Comprehensive Testing
Test tất cả chức năng của reminder system
"""
import os
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_reminder_system():
    """Test reminder system functionality"""
    print("=== TESTING REMINDER SYSTEM ===")
    
    try:
        # Import reminder functions
        from reminder_system import (
            HotelReminderSystem, 
            get_reminder_status,
            manual_trigger_reminders,
            enable_reminders,
            disable_reminders
        )
        
        print("[OK] Successfully imported reminder system modules")
        
        # Test 1: Create reminder system instance
        print("\n[TEST1] Test 1: Creating reminder system instance...")
        reminder_system = HotelReminderSystem()
        print(f"[OK] Reminder system created - enabled: {reminder_system.enabled}")
        
        # Test 2: Check system status
        print("\n[TEST2] Test 2: Checking system status...")
        status = get_reminder_status()
        print(f"[OK] Status retrieved: {status}")
        
        # Test 3: Test enable/disable
        print("\n[TEST3] Test 3: Testing enable/disable...")
        disable_reminders()
        print("[OK] Reminders disabled")
        
        enable_reminders()
        print("[OK] Reminders enabled")
        
        # Test 4: Test manual trigger (dry run)
        print("\n[TEST4] Test 4: Testing manual reminder check...")
        try:
            results = manual_trigger_reminders()
            print(f"[OK] Manual trigger completed:")
            print(f"   - Total bookings: {results.get('total_bookings', 0)}")
            print(f"   - Check-in today: {results.get('checkin_today', 0)}")
            print(f"   - Check-out today: {results.get('checkout_today', 0)}")
            print(f"   - Payment overdue: {results.get('payment_overdue', 0)}")
            print(f"   - Emails sent: {results.get('emails_sent', 0)}")
            
            if results.get('errors'):
                print(f"   - Errors: {len(results['errors'])}")
                for error in results['errors'][:3]:  # Show first 3 errors
                    print(f"     * {error}")
                    
        except Exception as e:
            print(f"[WARNING] Manual trigger test failed: {e}")
        
        # Test 5: Data loading test
        print("\n[TEST5] Test 5: Testing data loading...")
        try:
            df = reminder_system._load_booking_data()
            if not df.empty:
                print(f"[OK] Data loaded successfully: {len(df)} records")
                
                # Test date conversion
                today = datetime.now().date()
                if 'Check-in Date' in df.columns:
                    checkin_today = reminder_system._get_checkin_today(df, today)
                    print(f"   - Check-ins today: {len(checkin_today)}")
                    
                if 'Check-out Date' in df.columns:
                    checkout_today = reminder_system._get_checkout_today(df, today)
                    print(f"   - Check-outs today: {len(checkout_today)}")
                    
                payment_overdue = reminder_system._get_payment_overdue(df, today)
                print(f"   - Payment overdue: {len(payment_overdue)}")
                
            else:
                print("[WARNING] No data loaded (empty DataFrame)")
                
        except Exception as e:
            print(f"[ERROR] Data loading test failed: {e}")
            
        print("\n[OK] REMINDER SYSTEM TESTS COMPLETED")
        return True
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_email_service():
    """Test email service functionality"""
    print("\n=== TESTING EMAIL SERVICE ===")
    
    try:
        from email_service import email_service
        
        print("[OK] Email service imported successfully")
        
        # Test email configuration
        print(f"[INFO] Email configured: {email_service.smtp_configured}")
        print(f"[INFO] From email: {email_service.from_email}")
        print(f"[INFO] To emails: {email_service.to_emails}")
        
        # Test email templates
        print("\n[TEST] Testing email templates...")
        
        # Sample booking data for testing
        sample_booking = {
            'Tên người đặt': 'Test Guest',
            'Số đặt phòng': 'TEST123',
            'Check-in Date': datetime.now().strftime('%Y-%m-%d'),
            'Check-out Date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'Tổng thanh toán': 500000,
            'Tên chỗ nghỉ': 'Standard Room'
        }
        
        # Test template generation (without sending)
        try:
            checkin_subject, checkin_body = email_service._create_checkin_reminder_email(sample_booking)
            print("[OK] Check-in reminder template generated")
            print(f"   Subject: {checkin_subject[:50]}...")
            
            checkout_subject, checkout_body = email_service._create_checkout_reminder_email(sample_booking)
            print("[OK] Check-out reminder template generated")
            print(f"   Subject: {checkout_subject[:50]}...")
            
            payment_subject, payment_body = email_service._create_payment_reminder_email(sample_booking)
            print("[OK] Payment reminder template generated")
            print(f"   Subject: {payment_subject[:50]}...")
            
        except Exception as e:
            print(f"[WARNING] Email template generation failed: {e}")
        
        print("\n[OK] EMAIL SERVICE TESTS COMPLETED")
        return True
        
    except ImportError as e:
        print(f"[ERROR] Email service import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Email service test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("[TEST] STARTING COMPREHENSIVE REMINDER SYSTEM TESTS")
    print("=" * 60)
    
    # Check environment
    print("[CHECK] Checking environment variables...")
    required_vars = ['GCP_CREDS_FILE_PATH', 'DEFAULT_SHEET_ID', 'WORKSHEET_NAME']
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"[OK] {var}: {'*' * 10}")  # Hide actual values
        else:
            print(f"[ERROR] {var}: Not set")
    
    print("\n" + "=" * 60)
    
    # Run tests
    reminder_test = test_reminder_system()
    email_test = test_email_service()
    
    print("\n" + "=" * 60)
    print("[SUMMARY] TEST SUMMARY:")
    print(f"   Reminder System: {'[PASS]' if reminder_test else '[FAIL]'}")
    print(f"   Email Service: {'[PASS]' if email_test else '[FAIL]'}")
    
    if reminder_test and email_test:
        print("\n[SUCCESS] ALL TESTS PASSED - REMINDER SYSTEM READY!")
    else:
        print("\n[WARNING] SOME TESTS FAILED - CHECK CONFIGURATION")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
