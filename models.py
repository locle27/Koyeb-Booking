"""
Hotel Booking System - SQLAlchemy Models
Enterprise PostgreSQL Schema Implementation
"""

from datetime import datetime, date, time
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, Boolean, DECIMAL, Date, Time, DateTime
from sqlalchemy import ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

db = SQLAlchemy()

# =====================================================
# GUESTS TABLE - Master guest information
# =====================================================
class Guest(db.Model):
    __tablename__ = 'guests'
    
    # Primary identification
    guest_id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(50), index=True)
    nationality = Column(String(100))
    passport_number = Column(String(100))
    
    # Audit fields
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    bookings = relationship("Booking", back_populates="guest", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name='email_format'),
    )
    
    def __repr__(self):
        return f"<Guest {self.guest_id}: {self.full_name}>"
    
    def to_dict(self):
        return {
            'guest_id': self.guest_id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'nationality': self.nationality,
            'passport_number': self.passport_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# =====================================================
# BOOKINGS TABLE - Core booking information
# =====================================================
class Booking(db.Model):
    __tablename__ = 'bookings'
    
    # Primary identification
    booking_id = Column(String(50), primary_key=True)
    guest_id = Column(Integer, ForeignKey('guests.guest_id', ondelete='RESTRICT'), nullable=False, index=True)
    
    # Booking details
    checkin_date = Column(Date, nullable=False, index=True)
    checkout_date = Column(Date, nullable=False, index=True)
    
    # Financial information
    room_amount = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    taxi_amount = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    commission = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    
    # Payment tracking
    collector = Column(String(100))
    payment_status = Column(String(50), default='pending', index=True)
    
    # Booking status
    booking_status = Column(String(50), default='confirmed', index=True)
    
    # Additional services
    has_taxi = Column(Boolean, default=False)
    taxi_details = Column(Text)
    
    # Notes and comments
    booking_notes = Column(Text)
    internal_notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    guest = relationship("Guest", back_populates="bookings")
    quick_notes = relationship("QuickNote", back_populates="booking", cascade="all, delete-orphan")
    arrival_time = relationship("ArrivalTime", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('checkout_date > checkin_date', name='valid_dates'),
        CheckConstraint('room_amount >= 0 AND taxi_amount >= 0 AND commission >= 0', name='positive_amounts'),
        CheckConstraint("payment_status IN ('pending', 'partial', 'completed', 'refunded')", name='valid_payment_status'),
        CheckConstraint("booking_status IN ('confirmed', 'checked_in', 'checked_out', 'cancelled', 'no_show')", name='valid_booking_status'),
    )
    
    @hybrid_property
    def nights(self):
        """Calculate number of nights"""
        if self.checkin_date and self.checkout_date:
            return (self.checkout_date - self.checkin_date).days
        return 0
    
    @hybrid_property
    def total_amount(self):
        """Calculate total amount"""
        return (self.room_amount or 0) + (self.taxi_amount or 0)
    
    def __repr__(self):
        return f"<Booking {self.booking_id}: {self.guest.full_name if self.guest else 'N/A'}>"
    
    def to_dict(self):
        return {
            'booking_id': self.booking_id,
            'guest_id': self.guest_id,
            'guest_name': self.guest.full_name if self.guest else None,
            'checkin_date': self.checkin_date.isoformat() if self.checkin_date else None,
            'checkout_date': self.checkout_date.isoformat() if self.checkout_date else None,
            'nights': self.nights,
            'room_amount': float(self.room_amount) if self.room_amount else 0.0,
            'taxi_amount': float(self.taxi_amount) if self.taxi_amount else 0.0,
            'commission': float(self.commission) if self.commission else 0.0,
            'total_amount': float(self.total_amount),
            'collector': self.collector,
            'payment_status': self.payment_status,
            'booking_status': self.booking_status,
            'has_taxi': self.has_taxi,
            'taxi_details': self.taxi_details,
            'booking_notes': self.booking_notes,
            'internal_notes': self.internal_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# =====================================================
# QUICK_NOTES TABLE - Enhanced note system
# =====================================================
class QuickNote(db.Model):
    __tablename__ = 'quick_notes'
    
    note_id = Column(Integer, primary_key=True)
    
    # Note categorization
    note_type = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), default='normal')
    
    # Content
    content = Column(Text, nullable=False)
    
    # Scheduling
    reminder_date = Column(Date, index=True)
    reminder_time = Column(Time)
    
    # Guest association
    guest_name = Column(String(255))
    booking_id = Column(String(50), ForeignKey('bookings.booking_id', ondelete='CASCADE'), index=True)
    
    # Status tracking
    completed = Column(Boolean, default=False, index=True)
    completed_at = Column(DateTime)
    completed_by = Column(String(100))
    
    # Audit fields
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(String(100), default='system')
    
    # Relationships
    booking = relationship("Booking", back_populates="quick_notes")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("note_type IN ('thu-tien', 'huy-phong', 'taxi', 'general')", name='valid_note_type'),
        CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", name='valid_priority'),
    )
    
    def __repr__(self):
        return f"<QuickNote {self.note_id}: {self.note_type}>"
    
    def to_dict(self):
        return {
            'note_id': self.note_id,
            'note_type': self.note_type,
            'priority': self.priority,
            'content': self.content,
            'reminder_date': self.reminder_date.isoformat() if self.reminder_date else None,
            'reminder_time': self.reminder_time.isoformat() if self.reminder_time else None,
            'guest_name': self.guest_name,
            'booking_id': self.booking_id,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by': self.completed_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }

# =====================================================
# EXPENSES TABLE - Financial tracking
# =====================================================
class Expense(db.Model):
    __tablename__ = 'expenses'
    
    expense_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Expense details
    description = Column(Text, nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    expense_date = Column(Date, nullable=False, index=True)
    category = Column(String(100), default='general', index=True)
    
    # Receipt/documentation
    receipt_url = Column(Text)
    receipt_number = Column(String(100))
    
    # Approval workflow
    approved = Column(Boolean, default=False)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    
    # Audit fields
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(String(100), default='system')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount > 0', name='positive_amount'),
    )
    
    def __repr__(self):
        return f"<Expense {self.expense_id}: {self.description[:50]}>"
    
    def to_dict(self):
        return {
            'expense_id': self.expense_id,
            'description': self.description,
            'amount': float(self.amount),
            'expense_date': self.expense_date.isoformat() if self.expense_date else None,
            'category': self.category,
            'receipt_url': self.receipt_url,
            'receipt_number': self.receipt_number,
            'approved': self.approved,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }

# =====================================================
# MESSAGE_TEMPLATES TABLE - Template management
# =====================================================
class MessageTemplate(db.Model):
    __tablename__ = 'message_templates'
    
    template_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Template identification
    category = Column(String(100), nullable=False)
    label = Column(String(100), nullable=False)
    
    # Content
    message_text = Column(Text, nullable=False)
    
    # Metadata
    language = Column(String(10), default='en')
    active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    
    # Audit fields
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('category', 'label', name='unique_category_label'),
    )
    
    def __repr__(self):
        return f"<MessageTemplate {self.template_id}: {self.category}/{self.label}>"
    
    def to_dict(self):
        return {
            'template_id': self.template_id,
            'category': self.category,
            'label': self.label,
            'message_text': self.message_text,
            'language': self.language,
            'active': self.active,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# =====================================================
# ARRIVAL_TIMES TABLE - Guest arrival tracking
# =====================================================
class ArrivalTime(db.Model):
    __tablename__ = 'arrival_times'
    
    arrival_id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(String(50), ForeignKey('bookings.booking_id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Time details
    estimated_arrival = Column(Time)
    actual_arrival = Column(DateTime)
    
    # Status
    arrival_status = Column(String(50), default='pending')
    
    # Notes
    arrival_notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    booking = relationship("Booking", back_populates="arrival_time")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("arrival_status IN ('pending', 'arrived', 'delayed', 'cancelled')", name='valid_arrival_status'),
    )
    
    def __repr__(self):
        return f"<ArrivalTime {self.arrival_id}: {self.booking_id}>"
    
    def to_dict(self):
        return {
            'arrival_id': self.arrival_id,
            'booking_id': self.booking_id,
            'estimated_arrival': self.estimated_arrival.isoformat() if self.estimated_arrival else None,
            'actual_arrival': self.actual_arrival.isoformat() if self.actual_arrival else None,
            'arrival_status': self.arrival_status,
            'arrival_notes': self.arrival_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# =====================================================
# DATABASE UTILITY FUNCTIONS
# =====================================================

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
def create_all_tables(app):
    """Create all tables"""
    with app.app_context():
        db.create_all()
        print("✅ All PostgreSQL tables created successfully!")

def drop_all_tables(app):
    """Drop all tables (use with caution!)"""
    with app.app_context():
        db.drop_all()
        print("⚠️ All PostgreSQL tables dropped!")

def get_db_stats(app):
    """Get database statistics"""
    with app.app_context():
        stats = {}
        stats['guests'] = Guest.query.count()
        stats['bookings'] = Booking.query.count()
        stats['quick_notes'] = QuickNote.query.count()
        stats['expenses'] = Expense.query.count()
        stats['message_templates'] = MessageTemplate.query.count()
        stats['arrival_times'] = ArrivalTime.query.count()
        return stats

# =====================================================
# SAMPLE DATA FUNCTIONS
# =====================================================

def create_sample_data(app):
    """Create sample data for testing"""
    with app.app_context():
        # Clear existing data
        db.session.query(QuickNote).delete()
        db.session.query(ArrivalTime).delete()
        db.session.query(Booking).delete()
        db.session.query(Guest).delete()
        db.session.query(Expense).delete()
        db.session.query(MessageTemplate).delete()
        
        # Create sample guests
        guest1 = Guest(
            full_name="John Smith",
            email="john.smith@email.com",
            phone="+1234567890",
            nationality="USA"
        )
        guest2 = Guest(
            full_name="Alice Johnson", 
            email="alice.j@email.com",
            phone="+1987654321",
            nationality="Canada"
        )
        guest3 = Guest(
            full_name="Nguyen Van A",
            email="nguyenvana@email.com", 
            phone="+84123456789",
            nationality="Vietnam"
        )
        
        db.session.add_all([guest1, guest2, guest3])
        db.session.flush()  # Get IDs
        
        # Create sample bookings
        from datetime import date, timedelta
        today = date.today()
        
        booking1 = Booking(
            booking_id="BK2025001",
            guest_id=guest1.guest_id,
            checkin_date=today,
            checkout_date=today + timedelta(days=3),
            room_amount=350000,
            taxi_amount=50000,
            has_taxi=True,
            booking_status="confirmed",
            payment_status="pending"
        )
        
        booking2 = Booking(
            booking_id="BK2025002", 
            guest_id=guest2.guest_id,
            checkin_date=today + timedelta(days=1),
            checkout_date=today + timedelta(days=5),
            room_amount=400000,
            taxi_amount=0,
            has_taxi=False,
            booking_status="confirmed",
            payment_status="completed"
        )
        
        booking3 = Booking(
            booking_id="BK2025003",
            guest_id=guest3.guest_id, 
            checkin_date=today - timedelta(days=1),
            checkout_date=today + timedelta(days=2),
            room_amount=300000,
            taxi_amount=30000,
            has_taxi=True,
            booking_status="checked_in",
            payment_status="partial"
        )
        
        db.session.add_all([booking1, booking2, booking3])
        
        # Create sample quick notes
        note1 = QuickNote(
            note_id=1750005802934,
            note_type="thu-tien",
            content="Thu tiền từ khách John Smith",
            reminder_date=today,
            guest_name="John Smith",
            booking_id="BK2025001"
        )
        
        note2 = QuickNote(
            note_id=1750005802935,
            note_type="taxi", 
            content="Đặt taxi cho khách Alice Johnson",
            reminder_date=today + timedelta(days=1),
            guest_name="Alice Johnson",
            booking_id="BK2025002"
        )
        
        db.session.add_all([note1, note2])
        
        # Create sample templates
        template1 = MessageTemplate(
            category="WELCOME",
            label="DEFAULT", 
            message_text="Welcome to our hotel! Thank you for your reservation."
        )
        
        template2 = MessageTemplate(
            category="CHECKOUT",
            label="DEFAULT",
            message_text="Thank you for staying with us! We hope you enjoyed your stay."
        )
        
        template3 = MessageTemplate(
            category="TAXI",
            label="AIRPORT",
            message_text="Your taxi to the airport has been arranged. The driver will contact you 30 minutes before pickup."
        )
        
        db.session.add_all([template1, template2, template3])
        
        # Commit all changes
        db.session.commit()
        print("✅ Sample data created successfully!")
        
        return get_db_stats(app)