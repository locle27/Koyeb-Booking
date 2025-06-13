# Hotel Booking Management System - Project Memory

## 🏨 Project Overview
**Name:** Koyeb Hotel Booking System  
**Type:** Flask web application for hotel management  
**Owner:** locle27  
**Repository:** https://github.com/locle27/Koyeb-Booking  
**Branch:** clean-main  
**Latest Commit:** 129ab1d - PWA Implementation Removed + AI Assistant Hub Fixed

## 🏗️ System Architecture

### **Core Files:**
- **`app.py`** - Main Flask application with all routes (2040 lines)
- **`logic.py`** - Business logic, Google Sheets integration, AI processing
- **`dashboard_routes.py`** - Dashboard data processing functions (enhanced with taxi fee calculations)
- **`email_service.py`** - Email functionality
- **`reminder_system.py`** - Automated reminder system

### **Key Templates:**
- **`base.html`** - Main layout template (enhanced navbar text visibility)
- **`dashboard.html`** - Main dashboard with analytics, quick notes, and overdue guests management
- **`bookings.html`** - Booking management with auto-duplicate filtering
- **`add_booking.html`** - Add new bookings (manual + photo AI, no rounding restrictions)
- **`edit_booking.html`** - Edit existing bookings (step="any" for exact values)
- **`ai_assistant.html`** - AI chat, voice translator, message templates (fixed text colors)
- **`add_from_image.html`** - AI-powered photo booking extraction

## 🚀 Recent Major Features & Fixes (Latest Update)

### **1. PWA Implementation Removed** ⭐ LATEST ⭐
**Location:** Entire project - PWA functionality completely removed
**Commit:** `129ab1d` - 🔄 REVERT: Remove PWA Implementation - Restore to Working State

**🚨 Issue Resolved:**
- **PWA caused application to stop working** after deployment
- Service worker conflicts prevented normal operation
- PWA meta tags and manifest files caused browser issues
- User requested complete removal to restore functionality

**✅ Files Removed:**
- `static/sw.js` - Service worker that caused conflicts
- `static/manifest.json` - Web app manifest
- `static/icons/` - All PWA icons directory (icon.svg, all PNG icons)
- `static/browserconfig.xml` - Browser configuration
- `templates/pwa_debug.html` - PWA debugging template

**✅ Code Cleaned:**
- Removed PWA routes from `app.py` (manifest, service worker endpoints)
- Removed PWA meta tags from `templates/base.html`
- Removed service worker registration JavaScript
- Removed offline/online status handlers

**🎯 Result:**
- ✅ **Application working normally again**
- ✅ **All core hotel management features restored**
- ✅ **No PWA overhead or browser conflicts**
- ✅ **Real-time payment updates preserved**
- ✅ **AI Assistant Hub functionality maintained**

### **2. AI Assistant Hub Tab Functionality Fixed** ⭐ RECENT ⭐
**Location:** `templates/ai_assistant.html`
**Commit:** `0caecd5` - 🔧 FIX: AI Assistant Hub Tab Functionality

**🔧 Issue Fixed:**
- **All 3 AI Assistant Hub tabs were non-functional**
- Multiple conflicting `DOMContentLoaded` event listeners
- Templates tab click events not triggering template loading
- JavaScript timing conflicts prevented tab functionality

**✅ Solution Applied:**
- Consolidated all `DOMContentLoaded` logic into single listener
- Moved templates tab event handlers to main initialization
- Moved modal category handlers to main initialization
- Removed duplicate event listener registrations (lines 2266, 2401)

**🎯 Result:**
- ✅ **AI Chat Assistant tab** - Image analysis and AI responses working
- ✅ **Voice Translator tab** - Speech recognition and translation working  
- ✅ **Message Templates tab** - Template management and usage working

### **3. Enhanced Overdue Unpaid Guests System** ⭐ ESTABLISHED ⭐
**Location:** `dashboard_routes.py` (lines 119-205), `templates/dashboard.html` (lines 112-336)

**💰 Key Features:**
- **Total calculation includes Room + Taxi fees** automatically
- **Smart taxi fee parsing:** Handles "50,000đ", "50000", etc.
- **Visual breakdown:** Shows room fee and taxi fee separately
- **Quick edit functionality:** Modal to update amounts with real-time preview
- **Enhanced display format:**
  ```
  Guest Name: John Doe
  ✅ 550,000đ (Total - bold)
  Phòng: 500,000đ
  Taxi: 50,000đ (only if > 0)
  ID: BOOKING123
  [Thu tiền] [Sửa số tiền]
  ```

**📊 Technical Implementation:**
```python
# dashboard_routes.py - Enhanced calculation
def process_overdue_guests(df):
    # Calculates room_total + taxi_total
    # Adds calculated_total_amount, calculated_room_fee, calculated_taxi_fee
    # Smart regex parsing for taxi amounts
```

**🎯 Usage:**
- **Edit amounts:** Click "Sửa số tiền" → Update room/taxi fees → Real-time total preview
- **Collect payment:** Enhanced "Thu tiền" button with full amount visibility
- **Auto-update:** Page refreshes after successful updates

### **2. Critical Bug Fixes** ✅
**Location:** Multiple files

**🔧 Fixed Issues:**
- **Quick Notes Delete:** Fixed JavaScript quotes in `dashboard.html` line 823
- **AI Duplicate Filter Review:** Added missing `/api/delete_booking/<booking_id>` endpoint in `app.py` lines 839-867
- **Voice Translator Text:** Changed from white to black with text-shadow in `ai_assistant.html` lines 243-244
- **Template Import Redirects:** Fixed broken routes to `ai_assistant_hub` in `app.py` line 1573
- **Navbar Text Visibility:** Enhanced with text-shadows in `base.html` lines 52, 62
- **Message Template Category Bug:** Fixed duplicate ID conflict (`templateCategory` → `addTemplateCategory`) in `ai_assistant.html` line 444

### **3. Auto Duplicate Filtering System**
**Location:** `templates/bookings.html`, `app.py` (lines 313-336)
- ✅ Automatically filters duplicate bookings on page load
- ✅ Shows smart filter report with review options  
- ✅ Uses AI logic: same guest ± 3 days ± 100k VND
- **Toggle:** `?auto_filter=true/false` URL parameter
- **Functions:** `analyze_existing_duplicates()` in `logic.py`

### **4. Quick Notes Integration**
**Location:** `templates/dashboard.html` (lines 89-91, 1141-1336)
- ✅ Removed separate page, integrated modal into dashboard
- ✅ 3 note types: Thu tiền, Hủy phòng, Taxi
- ✅ Auto-fills current date/time
- ✅ Saves to localStorage + server API
- ✅ Fixed delete functionality with proper quotes

### **5. Photo Booking AI System**
**Location:** `templates/add_from_image.html`, `logic.py` (lines 1130-1375)
- ✅ AI-powered booking extraction from images
- ✅ Uses Google Gemini API for OCR and data extraction
- ✅ Handles single booking processing issues (fixed duplicate logic)
- **API Route:** `/api/process_pasted_image`

### **6. Price Field Precision Fix**
**Location:** `templates/add_booking.html`, `templates/edit_booking.html`
- ✅ Removed `step="1000"` rounding restrictions
- ✅ Changed to `step="any"` for exact pricing
- **Fields:** "Tổng thanh toán", "Hoa hồng"

## 🎨 UI/UX Improvements

### **Text Visibility Fixes:**
**Location:** `templates/ai_assistant.html`, `templates/base.html`
- ✅ Message Template Management: Enhanced text contrast, colored buttons
- ✅ Voice Translator: Black text with white text-shadow for readability
- ✅ Navbar: Enhanced brand and navigation text with shadows
- ✅ Better contrast across all black bar elements

### **Enhanced Dashboard Display:**
**Location:** `templates/dashboard.html`
- ✅ Overdue guests section with room/taxi breakdown
- ✅ Quick edit modals with real-time calculations
- ✅ Better visual hierarchy and button grouping
- ✅ Responsive design for mobile devices

## 💾 Database & Integration

### **Google Sheets Integration:**
- **Main Sheet:** Stores all booking data
- **Core Columns:** Số đặt phòng, Tên người đặt, Check-in Date, Check-out Date, Tổng thanh toán, Hoa hồng, Taxi, etc.
- **Redundant Columns to Remove:** Ngày đến, Ngày đi, Được đặt vào, Tiền tệ, Người nhận tiền, Vị trí
- **Functions:** `import_from_gsheet()`, `append_multiple_bookings_to_sheet()`, `update_row_in_gsheet()`

### **Key Environment Variables:**
```bash
GCP_CREDS_FILE_PATH=gcp_credentials.json
DEFAULT_SHEET_ID=your_sheet_id
WORKSHEET_NAME=your_worksheet
GOOGLE_API_KEY=your_gemini_api_key
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

## 🛠️ Common Debugging & Maintenance

### **Quick Issue Resolution:**

#### **Overdue Guests System Not Working:**
1. Check `dashboard_routes.py` line 119: `process_overdue_guests()` function
2. Verify taxi fee parsing in lines 166-179 (regex pattern)
3. Check calculated fields in template: `calculated_total_amount`, `calculated_room_fee`, `calculated_taxi_fee`
4. Debug edit modal in `dashboard.html` lines 598-651

#### **Quick Edit Modal Issues:**
1. Check JavaScript function `openEditAmountModal()` in `dashboard.html` line 1232
2. Verify API call to `/booking/<id>/edit` endpoint
3. Test real-time calculation in `updateTotalPreview()` function
4. Check form validation in `updateBookingAmounts()` function

#### **Photo Booking Not Working:**
1. Check Google API key in environment
2. Verify `logic.py` line 1177: `genai.configure(api_key=api_key)`
3. Look for duplicate logic interference in `add_from_image.html` line 116

#### **Duplicate Filter Issues:**
1. Check `analyze_existing_duplicates()` function in `logic.py`
2. Verify URL parameter: `?auto_filter=true`
3. Debug filter logic in `app.py` lines 320-333
4. Test delete functionality with `/api/delete_booking/<id>` endpoint

#### **Text Visibility Problems:**
1. Check `base.html` CSS for text-shadow properties
2. Verify `ai_assistant.html` color classes (text-dark, text-white)
3. Look for contrast issues in black bar elements

#### **Quick Notes Not Saving:**
1. Check localStorage in browser console
2. Verify API route: `/api/quick_notes`
3. Modal functions in `dashboard.html` lines 1056-1336
4. Test delete function with proper quotes

### **Development Commands:**
```bash
# Run locally
python app.py

# Test import syntax
python -m py_compile app.py

# Check template syntax
grep -n "{% endblock %}" templates/filename.html

# Search for specific functionality
grep -rn "search_term" templates/

# Test API endpoints
curl -X POST http://localhost:5000/api/collect_payment

# Check overdue guests calculation
python -c "from dashboard_routes import process_overdue_guests; print('Function loaded')"
```

### **File Structure Quick Reference:**
```
hotel_flask_app/
├── app.py                    # Main application (2040 lines)
├── logic.py                  # Business logic + AI processing
├── dashboard_routes.py       # Dashboard + overdue guests processing
├── email_service.py          # Email functionality
├── reminder_system.py        # Automated reminders
├── gcp_helper.py            # Google Cloud integration
├── templates/
│   ├── base.html            # Main layout (enhanced navbar)
│   ├── dashboard.html       # Dashboard + overdue guests + quick notes
│   ├── bookings.html        # Booking list + auto-duplicate filter
│   ├── add_booking.html     # Add booking form (no rounding)
│   ├── edit_booking.html    # Edit booking form (step="any")
│   ├── ai_assistant.html    # AI tools hub (fixed text colors)
│   └── add_from_image.html  # Photo AI extraction
├── static/
│   ├── css/style.css        # Main styles
│   └── js/dashboard.js      # Dashboard JavaScript
├── requirements.txt         # Dependencies
└── CLAUDE.md               # This memory bank
```

## 🚀 API Endpoints Reference

### **Payment & Booking Management:**
- `POST /api/collect_payment` - Collect payment from guests
- `DELETE /api/delete_booking/<id>` - Delete specific booking (JSON response)
- `POST /booking/<id>/edit` - Update booking details (including amounts)
- `POST /bookings/delete_multiple` - Delete multiple bookings

### **AI & Analysis:**
- `POST /api/process_pasted_image` - AI photo booking extraction
- `GET /api/analyze_duplicates` - AI duplicate detection
- `POST /api/ai_chat_analyze` - AI chat assistant
- `POST /api/translate` - Voice translation

### **Quick Notes:**
- `GET /api/quick_notes` - Get quick notes
- `POST /api/quick_notes` - Save quick note

## 🎯 Deployment Notes

### **GitHub Workflow:**
- **Repository:** https://github.com/locle27/Koyeb-Booking
- **Branch:** clean-main
- **Latest Commit:** 129ab1d (PWA Removed + AI Assistant Hub Fixed)

### **Deployment Commands:**
```bash
# Commit and push workflow
git add .
git commit -m "🎯 Feature: Description"
git push origin clean-main

# Check status
git status
git log --oneline -5
```

### **Current Status:**
- ✅ **PWA Implementation Removed** - Application restored to working state
- ✅ **AI Assistant Hub Fixed** - All 3 tabs now functional
- ✅ **All major features implemented and tested**
- ✅ **Overdue guests system with taxi fee integration**
- ✅ **Real-time payment updates preserved**
- ✅ **No PWA conflicts or browser issues**
- ✅ **Ready for production deployment (non-PWA)**

## 🔮 Future Enhancement Ideas

### **Potential Improvements:**
- [ ] Database migration from Google Sheets to PostgreSQL
- [ ] Real-time notifications for new bookings
- [ ] Advanced analytics dashboard with profit margins
- [ ] Mobile app integration
- [ ] Multi-property support
- [ ] Automated pricing suggestions
- [ ] Integration with booking platforms (Booking.com, Agoda)
- [ ] SMS notifications for guests
- [ ] QR code check-in system

## 🆘 Troubleshooting Checklist

### **If something breaks:**
1. **Check recent commits:** `git log --oneline -n 10`
2. **Verify environment variables:** Especially Google APIs
3. **Test basic functionality:** Add booking manually first
4. **Check browser console:** For JavaScript errors
5. **Review server logs:** For Python exceptions
6. **Test Google Sheets connection:** Import/export functions
7. **Verify API endpoints:** Use curl or Postman for testing

### **Performance Optimization:**
- Monitor Google Sheets API quota usage
- Consider caching for frequent data access
- Optimize image processing for large photos
- Review database query efficiency
- Monitor overdue calculation performance

#### **Message Template Category Selection Issues:**
1. Check duplicate IDs in `ai_assistant.html`: Search for `id="templateCategory"`
2. Verify JavaScript function `addNewTemplate()` finds correct element 
3. Look for duplicate element IDs causing form confusion
4. Test category dropdown and "OTHER" custom category functionality

### **Critical System Dependencies:**
- **Google Sheets API:** For data storage
- **Google Gemini API:** For AI photo processing
- **Flask Framework:** Web application
- **Bootstrap 5:** UI components
- **Plotly.js:** Charts and analytics

---

**Last Updated:** June 2025  
**Latest Features:** PWA Removed + AI Assistant Hub Fixed + Overdue Guests System  
**Status:** Production Ready (Non-PWA)  
**Next Review:** Q3 2025

## 📞 Quick Support Commands

### **Emergency Fixes:**
```bash
# Restart application
python app.py

# Clear cache and reload
rm -rf __pycache__
python app.py

# Reset to last working commit
git reset --hard HEAD~1

# Check logs for errors
tail -f app.log
```

### **Common Issues & Solutions:**
| Issue | Location | Solution |
|-------|----------|----------|
| App not working after PWA | `Entire project` | **SOLVED:** PWA removed in commit 129ab1d |
| AI Assistant tabs not working | `ai_assistant.html` | **SOLVED:** Event listeners fixed in commit 0caecd5 |
| Overdue amounts wrong | `dashboard_routes.py:159` | Check taxi fee parsing |
| Quick edit not working | `dashboard.html:1232` | Verify modal JavaScript |
| Delete buttons broken | `dashboard.html:823` | Check function quotes |
| Text not visible | `base.html:52,62` | Add text-shadow CSS |
| API endpoints failing | `app.py:839-867` | Verify route exists |

### **Critical Issue History:**
- **PWA Implementation (Removed):** Commits ec31c9e → 65a43e4 caused app failures, completely removed in 129ab1d
- **AI Assistant Hub Tabs:** Fixed JavaScript conflicts in 0caecd5  
- **Real-time Payment Updates:** Working properly (commit b22cf31)

This memory bank is now your complete reference for maintaining and extending the system. Keep it updated with any future changes! 🚀