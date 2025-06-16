@echo off
REM Hotel Booking System - Instant Local Testing
REM Run this to start local web server with instant changes

echo ⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
echo 🚀 HOTEL BOOKING - INSTANT LOCAL TESTING
echo ⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
echo.

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .\venv\Scripts\activate
if %errorlevel% neq 0 (
    echo ❌ Could not activate virtual environment
    echo 💡 Make sure venv folder exists
    pause
    exit /b 1
)
echo ✅ Virtual environment activated
echo.

REM Set environment variables
echo 🔧 Setting environment variables...
set DATABASE_URL=postgres://koyeb-adm:npg_T4hEuUQeDl7A@ep-little-haze-a2133rvc.eu-central-1.pg.koyeb.app:5432/koyebdb
set DEFAULT_SHEET_ID=13kQETOUGCVUwUqZrxeLy-WAj3b17SugI4L8Oq09SX2w
set GCP_CREDS_FILE_PATH=credentials.json
set GOOGLE_API_KEY=AIzaSyA-0V4VgrJbnzQWueDVI9pSOoH_V2EMUg4
set USE_POSTGRESQL=false
set USE_HYBRID_MODE=true
set FALLBACK_TO_SHEETS=true
set FLASK_ENV=development
set FLASK_DEBUG=True
set FLASK_APP=app.py

echo ✅ Environment variables set
echo.

REM Start the server
echo 🚀 Starting instant local server...
echo 📍 Local URL: http://localhost:5000
echo 🔄 Auto-reload enabled - changes appear instantly!
echo.
echo 💡 TESTING URLS:
echo    • Dashboard: http://localhost:5000/
echo    • Bookings: http://localhost:5000/bookings
echo    • API Health: http://localhost:5000/api/database/health
echo.
echo 🌐 TO SHARE PUBLICLY:
echo    1. Download ngrok: https://ngrok.com/download
echo    2. Run: ngrok http 5000
echo    3. Get public URL like: https://abc123.ngrok.io
echo.
echo ⏹️ Press Ctrl+C to stop the server
echo ================================================================
echo.

REM Run the server
python instant_local_server.py

echo.
echo 👋 Server stopped
pause