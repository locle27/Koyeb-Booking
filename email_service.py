"""
Email Reminder Service
Tự động gửi email nhắc hẹn cho các sự kiện quan trọng của khách sạn
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailReminderService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER", "")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")
        self.reminder_email = os.getenv("REMINDER_EMAIL", "loc22100302@gmail.com")
        
        # Check if email reminders are explicitly disabled
        self.enabled = os.getenv("EMAIL_REMINDERS_ENABLED", "true").lower() != "false"
        
        # Add properties for test compatibility
        self.from_email = self.email_user
        self.to_emails = [self.reminder_email]
        self.smtp_configured = bool(self.email_user and self.email_password and self.enabled)
        
        if not self.enabled:
            print("[EMAIL] Email reminders DISABLED via EMAIL_REMINDERS_ENABLED=false")
        elif not self.smtp_configured:
            print("[EMAIL] Email service initialized - SMTP NOT configured (missing EMAIL_USER/PASSWORD)")
        else:
            print(f"[EMAIL] Email service initialized - SMTP configured: {self.smtp_configured}")
        
    def _create_checkin_reminder_email(self, booking_data: Dict):
        """Create check-in reminder email content for testing"""
        guest_name = booking_data.get('Tên người đặt', 'Khách hàng')
        checkin_date = booking_data.get('Check-in Date', 'N/A')
        
        subject = f"🏨 Nhắc nhở Check-in - {guest_name}"
        body = f"Check-in reminder for {guest_name} on {checkin_date}"
        
        return subject, body
    
    def _create_checkout_reminder_email(self, booking_data: Dict):
        """Create check-out reminder email content for testing"""
        guest_name = booking_data.get('Tên người đặt', 'Khách hàng')
        checkout_date = booking_data.get('Check-out Date', 'N/A')
        
        subject = f"🚪 Nhắc nhở Check-out - {guest_name}"
        body = f"Check-out reminder for {guest_name} on {checkout_date}"
        
        return subject, body
    
    def _create_payment_reminder_email(self, booking_data: Dict):
        """Create payment reminder email content for testing"""
        guest_name = booking_data.get('Tên người đặt', 'Khách hàng')
        total_payment = booking_data.get('Tổng thanh toán', 0)
        
        subject = f"💰 Nhắc nhở Thu tiền - {guest_name}"
        body = f"Payment reminder for {guest_name}: {total_payment:,}₫"
        
        return subject, body
        
    def send_email(self, subject: str, body: str, to_email: str = None) -> bool:
    def send_email(self, subject: str, body: str, to_email: str = None) -> bool:
        """
        Gửi email với subject và body được chỉ định
        
        Args:
            subject: Tiêu đề email
            body: Nội dung email (HTML format)
            to_email: Email người nhận (mặc định dùng REMINDER_EMAIL)
            
        Returns:
            bool: True nếu gửi thành công, False nếu có lỗi
        """
        try:
            # Check if email is disabled
            if not self.enabled:
                print(f"[EMAIL] SKIPPED (disabled): {subject}")
                return True  # Return True to not break the flow
            
            if not to_email:
                to_email = self.reminder_email
                
            # Kiểm tra cấu hình email
            if not self.email_user or not self.email_password:
                print(f"[EMAIL] SKIPPED (no config): {subject}")
                print("   💡 To enable emails: Set EMAIL_USER and EMAIL_PASSWORD in .env")
                print("   📝 Guide: Use Gmail App Password, not real password!")
                return False
            
            # Tạo message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Thêm nội dung HTML
            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Kết nối SMTP và gửi email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
                
            print(f"[EMAIL] ✅ Sent successfully to {to_email}: {subject}")
            return True
            
        except Exception as e:
            print(f"[EMAIL] ❌ Error sending: {str(e)}")
            print(f"   Subject: {subject}")
            print("   💡 Check EMAIL_USER and EMAIL_PASSWORD in .env")
            return False
    
    def send_checkin_reminder(self, booking_data: Dict) -> bool:
        """
        Gửi email nhắc nhở check-in
        
        Args:
            booking_data: Dictionary chứa thông tin booking
            
        Returns:
            bool: True nếu gửi thành công
        """
        guest_name = booking_data.get('Tên người đặt', 'Khách hàng')
        checkin_date = booking_data.get('Check-in Date', 'N/A')
        checkout_date = booking_data.get('Check-out Date', 'N/A')
        room_type = booking_data.get('Tên chỗ nghỉ', 'N/A')
        booking_id = booking_data.get('Số đặt phòng', 'N/A')
        total_payment = booking_data.get('Tổng thanh toán', 0)
        
        # Format ngày tháng
        try:
            if isinstance(checkin_date, str):
                checkin_date_obj = pd.to_datetime(checkin_date)
            else:
                checkin_date_obj = checkin_date
            checkin_formatted = checkin_date_obj.strftime('%d/%m/%Y')
            checkin_day = checkin_date_obj.strftime('%A')
        except:
            checkin_formatted = str(checkin_date)
            checkin_day = ''
            
        try:
            if isinstance(checkout_date, str):
                checkout_date_obj = pd.to_datetime(checkout_date)
            else:
                checkout_date_obj = checkout_date
            checkout_formatted = checkout_date_obj.strftime('%d/%m/%Y')
        except:
            checkout_formatted = str(checkout_date)
        
        subject = f"🏨 Nhắc nhở Check-in - {guest_name} - {checkin_formatted}"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f8f9fa; }}
                .booking-card {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .booking-info {{ display: flex; justify-content: space-between; margin: 10px 0; }}
                .label {{ font-weight: bold; color: #2563eb; }}
                .value {{ color: #1e293b; }}
                .footer {{ background: #e2e8f0; padding: 15px; text-align: center; font-size: 12px; color: #64748b; }}
                .urgent {{ background: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏨 118 Hang Bac Hostel</h1>
                <h2>Nhắc nhở Check-in</h2>
            </div>
            
            <div class="content">
                <div class="urgent">
                    <strong>⏰ NHẮC NHỞ CHECK-IN HÔM NAY!</strong><br>
                    Khách <strong>{guest_name}</strong> sẽ check-in vào hôm nay ({checkin_day}).
                </div>
                
                <div class="booking-card">
                    <h3>📋 Thông tin đặt phòng:</h3>
                    
                    <div class="booking-info">
                        <span class="label">👤 Tên khách:</span>
                        <span class="value">{guest_name}</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">🆔 Mã đặt phòng:</span>
                        <span class="value">{booking_id}</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">🏠 Loại phòng:</span>
                        <span class="value">{room_type}</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">📅 Check-in:</span>
                        <span class="value">{checkin_formatted} ({checkin_day})</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">📅 Check-out:</span>
                        <span class="value">{checkout_formatted}</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">💰 Tổng thanh toán:</span>
                        <span class="value">{total_payment:,}₫</span>
                    </div>
                </div>
                
                <div class="booking-card">
                    <h3>📝 Checklist Check-in:</h3>
                    <ul>
                        <li>✅ Chuẩn bị phòng sạch sẽ</li>
                        <li>✅ Kiểm tra tiện nghi trong phòng</li>
                        <li>✅ Chuẩn bị chìa khóa/thẻ từ</li>
                        <li>✅ Xác nhận thông tin thanh toán</li>
                        <li>✅ Giải thích quy định khách sạn</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>📧 Email tự động từ Hotel Management System</p>
                <p>🕐 Gửi lúc: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(subject, body)
    
    def send_checkout_reminder(self, booking_data: Dict) -> bool:
        """
        Gửi email nhắc nhở check-out
        """
        guest_name = booking_data.get('Tên người đặt', 'Khách hàng')
        checkout_date = booking_data.get('Check-out Date', 'N/A')
        room_type = booking_data.get('Tên chỗ nghỉ', 'N/A')
        booking_id = booking_data.get('Số đặt phòng', 'N/A')
        
        # Format ngày tháng
        try:
            if isinstance(checkout_date, str):
                checkout_date_obj = pd.to_datetime(checkout_date)
            else:
                checkout_date_obj = checkout_date
            checkout_formatted = checkout_date_obj.strftime('%d/%m/%Y')
            checkout_day = checkout_date_obj.strftime('%A')
        except:
            checkout_formatted = str(checkout_date)
            checkout_day = ''
        
        subject = f"🚪 Nhắc nhở Check-out - {guest_name} - {checkout_formatted}"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #f39c12 0%, #e74c3c 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f8f9fa; }}
                .booking-card {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .booking-info {{ display: flex; justify-content: space-between; margin: 10px 0; }}
                .label {{ font-weight: bold; color: #f39c12; }}
                .value {{ color: #1e293b; }}
                .footer {{ background: #e2e8f0; padding: 15px; text-align: center; font-size: 12px; color: #64748b; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #f39c12; padding: 15px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏨 118 Hang Bac Hostel</h1>
                <h2>Nhắc nhở Check-out</h2>
            </div>
            
            <div class="content">
                <div class="warning">
                    <strong>⏰ NHẮC NHỞ CHECK-OUT HÔM NAY!</strong><br>
                    Khách <strong>{guest_name}</strong> sẽ check-out vào hôm nay ({checkout_day}).
                </div>
                
                <div class="booking-card">
                    <h3>📋 Thông tin đặt phòng:</h3>
                    
                    <div class="booking-info">
                        <span class="label">👤 Tên khách:</span>
                        <span class="value">{guest_name}</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">🆔 Mã đặt phòng:</span>
                        <span class="value">{booking_id}</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">🏠 Loại phòng:</span>
                        <span class="value">{room_type}</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">📅 Check-out:</span>
                        <span class="value">{checkout_formatted} ({checkout_day})</span>
                    </div>
                </div>
                
                <div class="booking-card">
                    <h3>📝 Checklist Check-out:</h3>
                    <ul>
                        <li>✅ Kiểm tra tình trạng phòng</li>
                        <li>✅ Thu hồi chìa khóa/thẻ từ</li>
                        <li>✅ Xác nhận không có đồ bỏ quên</li>
                        <li>✅ Thanh toán các chi phí phát sinh (nếu có)</li>
                        <li>✅ Chúc tạm biệt và mời quay lại</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>📧 Email tự động từ Hotel Management System</p>
                <p>🕐 Gửi lúc: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(subject, body)
    
    def send_payment_reminder(self, booking_data: Dict) -> bool:
        """
        Gửi email nhắc nhở thanh toán
        """
        guest_name = booking_data.get('Tên người đặt', 'Khách hàng')
        total_payment = booking_data.get('Tổng thanh toán', 0)
        booking_id = booking_data.get('Số đặt phòng', 'N/A')
        checkin_date = booking_data.get('Check-in Date', 'N/A')
        collector = booking_data.get('Người thu tiền', '')
        
        # Kiểm tra nếu đã thu tiền
        if collector in ['LOC LE', 'THAO LE']:
            return False  # Đã thu tiền rồi, không cần nhắc
        
        # Format ngày tháng
        try:
            if isinstance(checkin_date, str):
                checkin_date_obj = pd.to_datetime(checkin_date)
            else:
                checkin_date_obj = checkin_date
            checkin_formatted = checkin_date_obj.strftime('%d/%m/%Y')
        except:
            checkin_formatted = str(checkin_date)
        
        subject = f"💰 Nhắc nhở Thu tiền - {guest_name} - {total_payment:,}₫"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f8f9fa; }}
                .booking-card {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .booking-info {{ display: flex; justify-content: space-between; margin: 10px 0; }}
                .label {{ font-weight: bold; color: #e74c3c; }}
                .value {{ color: #1e293b; }}
                .footer {{ background: #e2e8f0; padding: 15px; text-align: center; font-size: 12px; color: #64748b; }}
                .urgent {{ background: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin: 15px 0; }}
                .amount {{ font-size: 24px; font-weight: bold; color: #e74c3c; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏨 118 Hang Bac Hostel</h1>
                <h2>Nhắc nhở Thu tiền</h2>
            </div>
            
            <div class="content">
                <div class="urgent">
                    <strong>💰 CẦN THU TIỀN KHÁCH!</strong><br>
                    Khách <strong>{guest_name}</strong> chưa thanh toán.
                </div>
                
                <div class="booking-card">
                    <h3>📋 Thông tin thanh toán:</h3>
                    
                    <div class="booking-info">
                        <span class="label">👤 Tên khách:</span>
                        <span class="value">{guest_name}</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">🆔 Mã đặt phòng:</span>
                        <span class="value">{booking_id}</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">📅 Ngày check-in:</span>
                        <span class="value">{checkin_formatted}</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">💰 Số tiền cần thu:</span>
                        <span class="value amount">{total_payment:,}₫</span>
                    </div>
                    
                    <div class="booking-info">
                        <span class="label">👨‍💼 Người thu tiền:</span>
                        <span class="value">{collector if collector else 'Chưa có'}</span>
                    </div>
                </div>
                
                <div class="booking-card">
                    <h3>📝 Hướng dẫn thu tiền:</h3>
                    <ul>
                        <li>✅ Xác nhận số tiền cần thu: <strong>{total_payment:,}₫</strong></li>
                        <li>✅ Thu tiền mặt hoặc chuyển khoản</li>
                        <li>✅ Cập nhật "Người thu tiền" trong hệ thống</li>
                        <li>✅ In hóa đơn cho khách (nếu có)</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>📧 Email tự động từ Hotel Management System</p>
                <p>🕐 Gửi lúc: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(subject, body)
    
    def test_email_connection(self) -> bool:
        """
        Test kết nối email để đảm bảo cấu hình đúng
        """
        test_subject = "🧪 Test Email Connection - Hotel Management System"
        test_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>✅ Email Connection Test Successful!</h2>
            <p>Hệ thống email reminder đã được cấu hình thành công.</p>
            <p><strong>Thời gian test:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            <p><strong>SMTP Server:</strong> {self.smtp_server}:{self.smtp_port}</p>
            <p><strong>Email gửi từ:</strong> {self.email_user}</p>
            <p><strong>Email nhận:</strong> {self.reminder_email}</p>
        </body>
        </html>
        """
        
        return self.send_email(test_subject, test_body)

# Khởi tạo service
email_service = EmailReminderService()

# Helper functions để sử dụng trong app
def send_test_email() -> bool:
    """Test email connection"""
    return email_service.test_email_connection()

def send_checkin_reminder(booking_data: Dict) -> bool:
    """Gửi nhắc nhở check-in"""
    return email_service.send_checkin_reminder(booking_data)

def send_checkout_reminder(booking_data: Dict) -> bool:
    """Gửi nhắc nhở check-out"""
    return email_service.send_checkout_reminder(booking_data)

def send_payment_reminder(booking_data: Dict) -> bool:
    """Gửi nhắc nhở thanh toán"""
    return email_service.send_payment_reminder(booking_data)
