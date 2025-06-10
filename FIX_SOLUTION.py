"""
FIX DATA SOLUTION - Hotel Booking System

PROBLEM DETECTED:
Booking ID: 6794271870 (Amaury Garde)
- Check-in Date: NaT (Not a Time) - NULL/Empty in Google Sheets
- Check-out Date: NaT (Not a Time) - NULL/Empty in Google Sheets
- This causes "N/A" display in bookings table

SOLUTION 1: FIX DATA IN GOOGLE SHEETS (RECOMMENDED)
============================================
1. Open Google Sheets booking data
2. Find row with booking ID: 6794271870
3. Add proper dates in format: YYYY-MM-DD or DD/MM/YYYY
   Example: 2024-12-15 or 15/12/2024
4. Save and sync data in app

SOLUTION 2: ENHANCED ERROR HANDLING IN APP
=========================================
Add better error handling and data validation
"""

# Enhanced template for bookings.html to show better error information
booking_debug_template = """
<!-- Enhanced date display with debug info -->
<td style="padding: 4px 8px; min-width: 90px;">
    <div class="text-center">
        {% set checkin_date = booking.get('Check-in Date') %}
        {% if checkin_date|is_valid_date %}
            <div class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1" style="font-size: 0.8rem;">
                <i class="fas fa-calendar-check fa-xs me-1"></i>
                <strong>{{ checkin_date|safe_date_format('%d/%m/%y') }}</strong>
            </div>
            {% set day_name = checkin_date|safe_day_name %}
            {% if day_name %}
            <small class="text-muted d-block">{{ day_name }}</small>
            {% endif %}
        {% else %}
            <div class="badge bg-warning-subtle text-warning border border-warning-subtle px-2 py-1" style="font-size: 0.8rem;">
                <i class="fas fa-calendar-question fa-xs me-1"></i>
                <strong>N/A</strong>
            </div>
            <!-- DEBUG INFO FOR ADMIN -->
            {% if dev_mode %}
            <small class="text-muted d-block" title="Debug: Raw value = {{ checkin_date|string }}">
                Debug: {{ checkin_date|string|truncate(10) }}
            </small>
            {% endif %}
        {% endif %}
    </div>
</td>
"""

print("SOLUTION SUMMARY:")
print("1. Go to Google Sheets")
print("2. Find booking ID: 6794271870")
print("3. Add proper check-in and check-out dates")
print("4. Save and sync in app")
