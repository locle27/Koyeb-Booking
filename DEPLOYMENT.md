# 🚀 Koyeb Deployment Guide

## Environment Variables cần setup trong Koyeb Dashboard:

### Basic Variables:
```
FLASK_SECRET_KEY = your_secret_key_here
DEFAULT_SHEET_ID = your_google_sheet_id
WORKSHEET_NAME = BookingManager
MESSAGE_TEMPLATE_WORKSHEET = MessageTemplate
GOOGLE_API_KEY = your_google_ai_api_key
PORT = 8080
FLASK_ENV = production
```

### Google Credentials:
**Variable Name:** `GCP_CREDENTIALS_JSON`
**Value:** Copy từ file gcp_credentials.json local (format JSON)

## 📋 Setup Steps:

1. **Clone repository**
2. **Create Koyeb service** từ GitHub repo
3. **Add environment variables** theo list trên
4. **Deploy**

## ⚠️ Security Notes:
- Không bao giờ commit credentials vào git
- Sử dụng Environment Variables cho sensitive data
- Files chứa credentials đã được thêm vào .gitignore

## 🔧 Local Development:
- Copy `.env.example` thành `.env`
- Điền thông tin thực vào `.env`
- Đặt file `gcp_credentials.json` trong thư mục gốc
