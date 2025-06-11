# 📧 Email Reminder System - Setup Guide

## 🚨 URGENT FIX: "❌ Email test failed. Check SMTP configuration."

**Problem**: Email environment variables not set in Koyeb deployment.

**Quick Solution**: 
1. Go to **Koyeb Dashboard** → Your App → **Settings** → **Environment Variables**
2. Add missing variables (see section below)
3. **Redeploy** your app

## 🔧 KOYEB DEPLOYMENT SETUP

### Required Environment Variables for Koyeb:

| Variable | Value | Required |
|----------|-------|----------|
| `EMAIL_USER` | `your-gmail@gmail.com` | ✅ **YES** |
| `EMAIL_PASSWORD` | `your-16-char-app-password` | ✅ **YES** |
| `SMTP_SERVER` | `smtp.gmail.com` | Optional (default) |
| `SMTP_PORT` | `587` | Optional (default) |
| `REMINDER_EMAIL` | `loc22100302@gmail.com` | Optional (default) |
| `EMAIL_REMINDERS_ENABLED` | `true` | Optional (default) |

### Koyeb Setup Steps:
1. **Get Gmail App Password** (see steps below)
2. **Add to Koyeb Environment Variables**:
   ```
   EMAIL_USER=youremail@gmail.com
   EMAIL_PASSWORD=abcd efgh ijkl mnop
   ```
3. **Redeploy** your Koyeb app
4. **Test** via app UI `/reminder_system` page

## 🤔 TẠI SAO CẦN EMAIL PASSWORD?

**Email Reminder System** tự động gửi email khi:
- ✅ Khách check-in hôm nay → Nhắc nhở chuẩn bị phòng
- ✅ Khách check-out hôm nay → Nhắc nhở dọn phòng  
- ✅ Khách chưa thanh toán → Nhắc nhở thu tiền

**Để gửi email tự động, system cần:**
1. Login vào Gmail SMTP server
2. Authenticate bằng email + password
3. Gửi email thay mặt bạn

## 🛡️ BẢO MẬT: DÙNG APP PASSWORD, KHÔNG PHẢI PASSWORD THẬT!

### ✅ CÁCH SETUP AN TOÀN:

#### Bước 1: Tạo Gmail account riêng (recommended)
```
hotel.notifications@gmail.com  ← Account riêng cho hotel system
```

#### Bước 2: Enable 2-Factor Authentication
1. Go to: https://myaccount.google.com/security
2. Turn on "2-Step Verification"

#### Bước 3: Generate App Password  
1. Go to: https://myaccount.google.com/apppasswords
2. Select app: "Mail" 
3. Generate → Copy 16-character password

#### Bước 4: Configure .env
```bash
EMAIL_USER=hotel.notifications@gmail.com
EMAIL_PASSWORD=abcd-efgh-ijkl-mnop  # ← 16-char App Password
REMINDER_EMAIL=your-main-email@gmail.com
```

## 🚫 KHÔNG MUỐN DÙNG EMAIL? 

### Option 1: Disable Email Reminders
```bash
# Trong .env file:
EMAIL_REMINDERS_ENABLED=false
```

### Option 2: Để trống email config
```bash
# Comment out hoặc để trống:
# EMAIL_USER=""
# EMAIL_PASSWORD=""
```

**→ System sẽ chỉ log reminders trong console, không gửi email**

## 🔒 BẢO MẬT TỐI ƯU:

### ✅ DO:
- ✅ Dùng Gmail account riêng cho hotel system
- ✅ Dùng App Password (16 characters) 
- ✅ Enable 2-Factor Authentication
- ✅ Giữ .env file secret (never commit to GitHub)

### ❌ DON'T:
- ❌ NEVER dùng password Gmail thật
- ❌ NEVER dùng main business email account  
- ❌ NEVER commit .env file to GitHub
- ❌ NEVER share email credentials

## 🧪 TEST EMAIL SETUP:

### Trong app, go to `/reminder_system` page:
1. Click "Test Email Connection"
2. Check inbox của REMINDER_EMAIL
3. Nếu nhận được email → Setup thành công!

## ❓ TROUBLESHOOTING:

### "Authentication failed" error:
- ✅ Check EMAIL_USER và EMAIL_PASSWORD đúng chưa
- ✅ Đảm bảo dùng App Password, không phải password thật
- ✅ Enable 2-Factor Authentication trước khi generate App Password

### "Less secure app access" error:
- ✅ Dùng App Password thay vì "Allow less secure apps"
- ✅ App Password an toàn hơn và recommended bởi Google

### Không nhận được email:
- ✅ Check Spam folder
- ✅ Verify REMINDER_EMAIL address đúng
- ✅ Check email quotas (Gmail: 500 emails/day for free accounts)

## 🎯 RECOMMENDED SETUP:

```bash
# .env file - RECOMMENDED CONFIG
EMAIL_USER=hotel.system@gmail.com      # ← Dedicated Gmail account  
EMAIL_PASSWORD=your-app-password       # ← 16-char App Password
REMINDER_EMAIL=manager@yourhotel.com   # ← Your notification email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

**→ Secure, professional, và easy to manage!**
