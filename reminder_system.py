"""
Hotel Reminder System - Background Scheduler
Tự động check và gửi email reminder cho các sự kiện quan trọng
"""
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
from email_service import send_checkin_reminder, send_checkout_reminder, send_payment_reminder
from logic import import_from_gsheet
import os
from dotenv import load_dotenv

load_dotenv()

class HotelReminderSystem:
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        self.check_interval = 3600  # Check every hour (3600 seconds)
        self.last_check_time = None
        self.enabled = True
        
        # Email settings
        self.gcp_creds_file_path = os.getenv("GCP_CREDS_FILE_PATH")
        self.default_sheet_id = os.getenv("DEFAULT_SHEET_ID")
        self.worksheet_name = os.getenv("WORKSHEET_NAME")
        
        print("[REMINDER] Hotel Reminder System initialized")
    
    def start_scheduler(self):
        """Bắt đầu background scheduler"""
        if self.running:
            print("[WARNING] Scheduler is already running")
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("[SUCCESS] Hotel Reminder Scheduler started")
    
    def stop_scheduler(self):
        """Dừng background scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("[STOP] Hotel Reminder Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop chạy trong background"""
        while self.running:
            try:
                if self.enabled:
                    self.check_and_send_reminders()
                    self.last_check_time = datetime.now()
                
                # Sleep for check_interval seconds, but check every 10 seconds if we should stop
                for _ in range(0, self.check_interval, 10):
                    if not self.running:
                        break
                    time.sleep(10)
                        
            except Exception as e:
                print(f"[ERROR] Error in scheduler loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def check_and_send_reminders(self):
        """
        Kiểm tra và gửi email reminders cho:
        1. Check-in hôm nay
        2. Check-out hôm nay  
        3. Khách chưa thanh toán quá hạn
        """
        try:
            print(f"[CHECK] Checking reminders at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Load booking data
            df = self._load_booking_data()
            if df.empty:
                print("[WARNING] No booking data found")
                return
                
            today = datetime.now().date()
            reminder_count = 0
            
            # 1. CHECK-IN REMINDERS - Khách check-in hôm nay
            checkin_today = self._get_checkin_today(df, today)
            for _, booking in checkin_today.iterrows():
                try:
                    if send_checkin_reminder(booking.to_dict()):
                        reminder_count += 1
                        print(f"[SUCCESS] Sent check-in reminder for {booking.get('Tên người đặt', 'N/A')}")
                except Exception as e:
                    print(f"[ERROR] Error sending check-in reminder: {e}")
            
            # 2. CHECK-OUT REMINDERS - Khách check-out hôm nay
            checkout_today = self._get_checkout_today(df, today)
            for _, booking in checkout_today.iterrows():
                try:
                    if send_checkout_reminder(booking.to_dict()):
                        reminder_count += 1
                        print(f"[SUCCESS] Sent check-out reminder for {booking.get('Tên người đặt', 'N/A')}")
                except Exception as e:
                    print(f"[ERROR] Error sending check-out reminder: {e}")
            
            # 3. PAYMENT REMINDERS - Khách chưa thanh toán quá hạn
            payment_overdue = self._get_payment_overdue(df, today)
            for _, booking in payment_overdue.iterrows():
                try:
                    if send_payment_reminder(booking.to_dict()):
                        reminder_count += 1
                        print(f"[SUCCESS] Sent payment reminder for {booking.get('Tên người đặt', 'N/A')}")
                except Exception as e:
                    print(f"[ERROR] Error sending payment reminder: {e}")
            
            print(f"[SUMMARY] Sent {reminder_count} reminder emails total")
            
        except Exception as e:
            print(f"[ERROR] Error in check_and_send_reminders: {e}")
    
    def _load_booking_data(self) -> pd.DataFrame:
        """Load booking data từ Google Sheets"""
        try:
            df = import_from_gsheet(
                self.default_sheet_id, 
                self.gcp_creds_file_path, 
                self.worksheet_name
            )
            
            if df.empty:
                return df
                
            # Convert date columns
            date_columns = ['Check-in Date', 'Check-out Date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Filter active bookings only
            df = df[df['Tình trạng'] != 'Đã hủy'].copy()
            
            return df
            
        except Exception as e:
            print(f"[ERROR] Error loading booking data: {e}")
            return pd.DataFrame()
    
    def _get_checkin_today(self, df: pd.DataFrame, today: datetime.date) -> pd.DataFrame:
        """Lấy danh sách khách check-in hôm nay"""
        try:
            if 'Check-in Date' not in df.columns:
                return pd.DataFrame()
                
            # Filter check-in today
            checkin_mask = df['Check-in Date'].dt.date == today
            checkin_today = df[checkin_mask].copy()
            
            print(f"[INFO] Found {len(checkin_today)} check-ins today")
            return checkin_today
            
        except Exception as e:
            print(f"[ERROR] Error getting check-in today: {e}")
            return pd.DataFrame()
    
    def _get_checkout_today(self, df: pd.DataFrame, today: datetime.date) -> pd.DataFrame:
        """Lấy danh sách khách check-out hôm nay"""
        try:
            if 'Check-out Date' not in df.columns:
                return pd.DataFrame()
                
            # Filter check-out today
            checkout_mask = df['Check-out Date'].dt.date == today
            checkout_today = df[checkout_mask].copy()
            
            print(f"[INFO] Found {len(checkout_today)} check-outs today")
            return checkout_today
            
        except Exception as e:
            print(f"[ERROR] Error getting check-out today: {e}")
            return pd.DataFrame()
    
    def _get_payment_overdue(self, df: pd.DataFrame, today: datetime.date) -> pd.DataFrame:
        """Lấy danh sách khách chưa thanh toán quá hạn"""
        try:
            if 'Check-in Date' not in df.columns or 'Người thu tiền' not in df.columns:
                return pd.DataFrame()
            
            # Filter criteria:
            # 1. Đã check-in (Check-in Date <= today)
            # 2. Chưa thu tiền (Người thu tiền không phải LOC LE/THAO LE)
            # 3. Không bị hủy
            
            checked_in_mask = df['Check-in Date'].dt.date <= today
            collected_values = ['LOC LE', 'THAO LE']
            collector_series = df['Người thu tiền'].fillna('').astype(str)
            not_collected_mask = ~collector_series.isin(collected_values)
            not_cancelled_mask = df['Tình trạng'] != 'Đã hủy'
            
            # Combine all conditions
            overdue_mask = checked_in_mask & not_collected_mask & not_cancelled_mask
            payment_overdue = df[overdue_mask].copy()
            
            print(f"[INFO] Found {len(payment_overdue)} payment overdue")
            return payment_overdue
            
        except Exception as e:
            print(f"[ERROR] Error getting payment overdue: {e}")
            return pd.DataFrame()
    
    def manual_check_reminders(self) -> Dict:
        """
        Manual trigger để check reminders ngay lập tức
        Returns summary của reminders được gửi
        """
        try:
            start_time = datetime.now()
            
            # Load data
            df = self._load_booking_data()
            if df.empty:
                return {"error": "No booking data found"}
            
            today = datetime.now().date()
            results = {
                "check_time": start_time.strftime('%d/%m/%Y %H:%M:%S'),
                "total_bookings": len(df),
                "checkin_today": 0,
                "checkout_today": 0, 
                "payment_overdue": 0,
                "emails_sent": 0,
                "errors": []
            }
            
            # Check-in reminders
            checkin_today = self._get_checkin_today(df, today)
            results["checkin_today"] = len(checkin_today)
            
            for _, booking in checkin_today.iterrows():
                try:
                    if send_checkin_reminder(booking.to_dict()):
                        results["emails_sent"] += 1
                except Exception as e:
                    results["errors"].append(f"Check-in reminder error: {str(e)}")
            
            # Check-out reminders
            checkout_today = self._get_checkout_today(df, today)
            results["checkout_today"] = len(checkout_today)
            
            for _, booking in checkout_today.iterrows():
                try:
                    if send_checkout_reminder(booking.to_dict()):
                        results["emails_sent"] += 1
                except Exception as e:
                    results["errors"].append(f"Check-out reminder error: {str(e)}")
            
            # Payment reminders
            payment_overdue = self._get_payment_overdue(df, today)
            results["payment_overdue"] = len(payment_overdue)
            
            for _, booking in payment_overdue.iterrows():
                try:
                    if send_payment_reminder(booking.to_dict()):
                        results["emails_sent"] += 1
                except Exception as e:
                    results["errors"].append(f"Payment reminder error: {str(e)}")
            
            end_time = datetime.now()
            results["execution_time"] = str(end_time - start_time)
            
            return results
            
        except Exception as e:
            return {"error": f"Manual check failed: {str(e)}"}
    
    def get_system_status(self) -> Dict:
        """Lấy status của reminder system"""
        return {
            "running": self.running,
            "enabled": self.enabled,
            "check_interval_hours": self.check_interval / 3600,
            "last_check_time": self.last_check_time.strftime('%d/%m/%Y %H:%M:%S') if self.last_check_time else None,
            "next_check_estimate": (datetime.now() + timedelta(seconds=self.check_interval)).strftime('%d/%m/%Y %H:%M:%S') if self.running else None
        }
    
    def enable_reminders(self):
        """Bật reminder system"""
        self.enabled = True
        print("[SUCCESS] Reminder system enabled")
    
    def disable_reminders(self):
        """Tắt reminder system"""
        self.enabled = False
        print("[DISABLED] Reminder system disabled")

# Global instance
reminder_system = HotelReminderSystem()

# Helper functions
def start_reminder_system():
    """Start the reminder system"""
    reminder_system.start_scheduler()

def stop_reminder_system():
    """Stop the reminder system"""
    reminder_system.stop_scheduler()

def get_reminder_status():
    """Get reminder system status"""
    return reminder_system.get_system_status()

def manual_trigger_reminders():
    """Manually trigger reminder check"""
    return reminder_system.manual_check_reminders()

def enable_reminders():
    """Enable reminders"""
    reminder_system.enable_reminders()

def disable_reminders():
    """Disable reminders"""
    reminder_system.disable_reminders()
