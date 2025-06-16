-- =====================================================
-- Hotel Booking System - Enterprise PostgreSQL Schema
-- =====================================================

-- Enable UUID extension for unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- GUESTS TABLE - Master guest information
-- =====================================================
CREATE TABLE guests (
    guest_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    nationality VARCHAR(100),
    passport_number VARCHAR(100),
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- =====================================================
-- BOOKINGS TABLE - Core booking information
-- =====================================================
CREATE TABLE bookings (
    -- Primary identification
    booking_id VARCHAR(50) PRIMARY KEY,
    guest_id INTEGER REFERENCES guests(guest_id) ON DELETE RESTRICT,
    
    -- Booking details
    checkin_date DATE NOT NULL,
    checkout_date DATE NOT NULL,
    nights INTEGER GENERATED ALWAYS AS (checkout_date - checkin_date) STORED,
    
    -- Financial information
    room_amount DECIMAL(12,2) DEFAULT 0.00,
    taxi_amount DECIMAL(12,2) DEFAULT 0.00,
    commission DECIMAL(12,2) DEFAULT 0.00,
    total_amount DECIMAL(12,2) GENERATED ALWAYS AS (room_amount + taxi_amount) STORED,
    
    -- Payment tracking
    collector VARCHAR(100),
    payment_status VARCHAR(50) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'partial', 'completed', 'refunded')),
    
    -- Booking status
    booking_status VARCHAR(50) DEFAULT 'confirmed' CHECK (booking_status IN ('confirmed', 'checked_in', 'checked_out', 'cancelled', 'no_show')),
    
    -- Additional services
    has_taxi BOOLEAN DEFAULT FALSE,
    taxi_details TEXT,
    
    -- Notes and comments
    booking_notes TEXT,
    internal_notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_dates CHECK (checkout_date > checkin_date),
    CONSTRAINT positive_amounts CHECK (room_amount >= 0 AND taxi_amount >= 0 AND commission >= 0)
);

-- =====================================================
-- QUICK_NOTES TABLE - Enhanced note system
-- =====================================================
CREATE TABLE quick_notes (
    note_id BIGINT PRIMARY KEY,
    
    -- Note categorization
    note_type VARCHAR(50) NOT NULL CHECK (note_type IN ('thu-tien', 'huy-phong', 'taxi', 'general')),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    
    -- Content
    content TEXT NOT NULL,
    
    -- Scheduling
    reminder_date DATE,
    reminder_time TIME,
    
    -- Guest association
    guest_name VARCHAR(255),
    booking_id VARCHAR(50) REFERENCES bookings(booking_id) ON DELETE CASCADE,
    
    -- Status tracking
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    completed_by VARCHAR(100),
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system'
);

-- =====================================================
-- EXPENSES TABLE - Financial tracking
-- =====================================================
CREATE TABLE expenses (
    expense_id SERIAL PRIMARY KEY,
    
    -- Expense details
    description TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    expense_date DATE NOT NULL,
    category VARCHAR(100) DEFAULT 'general',
    
    -- Receipt/documentation
    receipt_url TEXT,
    receipt_number VARCHAR(100),
    
    -- Approval workflow
    approved BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system'
);

-- =====================================================
-- MESSAGE_TEMPLATES TABLE - Template management
-- =====================================================
CREATE TABLE message_templates (
    template_id SERIAL PRIMARY KEY,
    
    -- Template identification
    category VARCHAR(100) NOT NULL,
    label VARCHAR(100) NOT NULL,
    
    -- Content
    message_text TEXT NOT NULL,
    
    -- Metadata
    language VARCHAR(10) DEFAULT 'en',
    active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(category, label)
);

-- =====================================================
-- ARRIVAL_TIMES TABLE - Guest arrival tracking
-- =====================================================
CREATE TABLE arrival_times (
    arrival_id SERIAL PRIMARY KEY,
    booking_id VARCHAR(50) REFERENCES bookings(booking_id) ON DELETE CASCADE,
    
    -- Time details
    estimated_arrival TIME,
    actual_arrival TIMESTAMP,
    
    -- Status
    arrival_status VARCHAR(50) DEFAULT 'pending' CHECK (arrival_status IN ('pending', 'arrived', 'delayed', 'cancelled')),
    
    -- Notes
    arrival_notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(booking_id)
);

-- =====================================================
-- INDEXES for Performance
-- =====================================================

-- Booking indexes
CREATE INDEX idx_bookings_checkin_date ON bookings(checkin_date);
CREATE INDEX idx_bookings_checkout_date ON bookings(checkout_date);
CREATE INDEX idx_bookings_guest_id ON bookings(guest_id);
CREATE INDEX idx_bookings_status ON bookings(booking_status);
CREATE INDEX idx_bookings_payment_status ON bookings(payment_status);

-- Guest indexes
CREATE INDEX idx_guests_email ON guests(email);
CREATE INDEX idx_guests_phone ON guests(phone);
CREATE INDEX idx_guests_name ON guests(full_name);

-- Quick notes indexes
CREATE INDEX idx_quick_notes_type ON quick_notes(note_type);
CREATE INDEX idx_quick_notes_date ON quick_notes(reminder_date);
CREATE INDEX idx_quick_notes_completed ON quick_notes(completed);
CREATE INDEX idx_quick_notes_booking ON quick_notes(booking_id);

-- Expense indexes
CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_expenses_category ON expenses(category);

-- =====================================================
-- TRIGGERS for automatic timestamp updates
-- =====================================================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all tables with updated_at
CREATE TRIGGER update_guests_updated_at BEFORE UPDATE ON guests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bookings_updated_at BEFORE UPDATE ON bookings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_quick_notes_updated_at BEFORE UPDATE ON quick_notes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_expenses_updated_at BEFORE UPDATE ON expenses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON message_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_arrival_times_updated_at BEFORE UPDATE ON arrival_times FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- VIEWS for Common Queries
-- =====================================================

-- Active bookings with guest information
CREATE VIEW v_active_bookings AS
SELECT 
    b.booking_id,
    g.full_name,
    g.email,
    g.phone,
    b.checkin_date,
    b.checkout_date,
    b.nights,
    b.room_amount,
    b.taxi_amount,
    b.total_amount,
    b.booking_status,
    b.payment_status,
    b.collector,
    b.has_taxi
FROM bookings b
JOIN guests g ON b.guest_id = g.guest_id
WHERE b.booking_status NOT IN ('cancelled', 'checked_out');

-- Overdue payments view
CREATE VIEW v_overdue_payments AS
SELECT 
    b.booking_id,
    g.full_name,
    b.checkin_date,
    b.total_amount,
    b.collector,
    (CURRENT_DATE - b.checkin_date) as days_overdue
FROM bookings b
JOIN guests g ON b.guest_id = g.guest_id
WHERE b.checkin_date <= CURRENT_DATE 
    AND b.payment_status != 'completed'
    AND b.booking_status != 'cancelled';

-- Today's arrivals
CREATE VIEW v_todays_arrivals AS
SELECT 
    b.booking_id,
    g.full_name,
    g.phone,
    b.room_amount,
    b.has_taxi,
    at.estimated_arrival,
    at.arrival_status
FROM bookings b
JOIN guests g ON b.guest_id = g.guest_id
LEFT JOIN arrival_times at ON b.booking_id = at.booking_id
WHERE b.checkin_date = CURRENT_DATE
    AND b.booking_status = 'confirmed';

-- =====================================================
-- SAMPLE DATA for Testing
-- =====================================================

-- Insert sample guest
INSERT INTO guests (full_name, email, phone, nationality) VALUES
('John Smith', 'john.smith@email.com', '+1234567890', 'USA'),
('Alice Johnson', 'alice.j@email.com', '+1987654321', 'Canada'),
('Nguyen Van A', 'nguyenvana@email.com', '+84123456789', 'Vietnam');

-- Insert sample booking
INSERT INTO bookings (booking_id, guest_id, checkin_date, checkout_date, room_amount, taxi_amount, has_taxi, booking_status, payment_status) VALUES
('BK2025001', 1, CURRENT_DATE, CURRENT_DATE + INTERVAL '3 days', 350000, 50000, true, 'confirmed', 'pending'),
('BK2025002', 2, CURRENT_DATE + INTERVAL '1 day', CURRENT_DATE + INTERVAL '5 days', 400000, 0, false, 'confirmed', 'completed'),
('BK2025003', 3, CURRENT_DATE - INTERVAL '1 day', CURRENT_DATE + INTERVAL '2 days', 300000, 30000, true, 'checked_in', 'partial');

-- Insert sample quick note
INSERT INTO quick_notes (note_id, note_type, content, reminder_date, reminder_time, guest_name, booking_id) VALUES
(1750005802934, 'thu-tien', 'Thu tiền từ khách John Smith', CURRENT_DATE, '14:00', 'John Smith', 'BK2025001'),
(1750005802935, 'taxi', 'Đặt taxi cho khách Alice Johnson', CURRENT_DATE + INTERVAL '1 day', '10:00', 'Alice Johnson', 'BK2025002');

-- Insert sample templates
INSERT INTO message_templates (category, label, message_text) VALUES
('WELCOME', 'DEFAULT', 'Welcome to our hotel! Thank you for your reservation.'),
('CHECKOUT', 'DEFAULT', 'Thank you for staying with us! We hope you enjoyed your stay.'),
('TAXI', 'AIRPORT', 'Your taxi to the airport has been arranged. The driver will contact you 30 minutes before pickup.');

-- =====================================================
-- SUCCESS MESSAGE
-- =====================================================
SELECT 'Hotel Booking Database Schema Created Successfully!' as status,
       'Tables: ' || count(*) as table_count
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';