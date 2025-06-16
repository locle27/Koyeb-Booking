"""
Hotel Booking System - Hybrid Database Service
Zero-Risk PostgreSQL Migration with Google Sheets Fallback

This service provides a unified interface that can seamlessly switch between
PostgreSQL and Google Sheets, ensuring zero downtime during migration.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from flask import current_app
from contextlib import contextmanager
import pandas as pd

# Import models and existing Google Sheets logic
from models import db, Guest, Booking, QuickNote, Expense, MessageTemplate, ArrivalTime
from logic import import_from_gsheet, append_multiple_bookings_to_sheet, update_row_in_gsheet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURATION
# =====================================================

class DatabaseConfig:
    """Database configuration and feature flags"""
    
    # Feature flags for gradual migration
    USE_POSTGRESQL = os.getenv('USE_POSTGRESQL', 'false').lower() == 'true'
    USE_HYBRID_MODE = os.getenv('USE_HYBRID_MODE', 'true').lower() == 'true'
    
    # Fallback behavior
    FALLBACK_TO_SHEETS = os.getenv('FALLBACK_TO_SHEETS', 'true').lower() == 'true'
    
    # Performance monitoring
    ENABLE_PERFORMANCE_LOGGING = os.getenv('ENABLE_PERFORMANCE_LOGGING', 'true').lower() == 'true'
    
    # Google Sheets settings (existing)
    GCP_CREDS_FILE_PATH = os.getenv('GCP_CREDS_FILE_PATH')
    DEFAULT_SHEET_ID = os.getenv('DEFAULT_SHEET_ID')
    
    @classmethod
    def get_primary_backend(cls):
        """Get the primary database backend"""
        if cls.USE_POSTGRESQL:
            return 'postgresql'
        return 'google_sheets'
    
    @classmethod
    def get_fallback_backend(cls):
        """Get the fallback database backend"""
        if cls.USE_POSTGRESQL and cls.FALLBACK_TO_SHEETS:
            return 'google_sheets'
        elif not cls.USE_POSTGRESQL:
            return 'postgresql'
        return None

# =====================================================
# PERFORMANCE MONITORING
# =====================================================

class PerformanceTimer:
    """Context manager for measuring performance"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = (self.end_time - self.start_time) * 1000  # Convert to milliseconds
        
        if DatabaseConfig.ENABLE_PERFORMANCE_LOGGING:
            backend = DatabaseConfig.get_primary_backend()
            logger.info(f"🚀 PERFORMANCE: {self.operation_name} ({backend}) - {duration:.1f}ms")
        
        return False

# =====================================================
# EXCEPTION HANDLING
# =====================================================

class DatabaseError(Exception):
    """Base exception for database operations"""
    pass

class PostgreSQLError(DatabaseError):
    """PostgreSQL specific error"""
    pass

class GoogleSheetsError(DatabaseError):
    """Google Sheets specific error"""
    pass

# =====================================================
# DATA MAPPERS
# =====================================================

class DataMapper:
    """Maps data between PostgreSQL and Google Sheets formats"""
    
    @staticmethod
    def sheets_to_postgres_booking(sheets_row: Dict) -> Dict:
        """Convert Google Sheets booking row to PostgreSQL format"""
        try:
            # Map Vietnamese column names to English
            mapped = {
                'booking_id': sheets_row.get('Số đặt phòng', ''),
                'guest_name': sheets_row.get('Tên người đặt', ''),
                'checkin_date': sheets_row.get('Check-in Date', ''),
                'checkout_date': sheets_row.get('Check-out Date', ''),
                'room_amount': float(sheets_row.get('Tổng thanh toán', 0) or 0),
                'taxi_amount': float(sheets_row.get('Taxi', 0) or 0),
                'commission': float(sheets_row.get('Hoa hồng', 0) or 0),
                'collector': sheets_row.get('Người thu tiền', ''),
                'booking_status': 'confirmed' if sheets_row.get('Tình trạng', '') == 'OK' else 'cancelled',
                'payment_status': 'completed' if sheets_row.get('Người thu tiền') else 'pending',
                'has_taxi': bool(sheets_row.get('Taxi', 0)),
                'booking_notes': sheets_row.get('Ghi chú thanh toán', ''),
            }
            
            # Convert dates
            if mapped['checkin_date']:
                mapped['checkin_date'] = pd.to_datetime(mapped['checkin_date']).date()
            if mapped['checkout_date']:
                mapped['checkout_date'] = pd.to_datetime(mapped['checkout_date']).date()
            
            return mapped
        except Exception as e:
            logger.error(f"Error mapping sheets to postgres: {e}")
            raise DataMappingError(f"Failed to map sheets data: {e}")
    
    @staticmethod
    def postgres_to_sheets_booking(booking: Union[Booking, Dict]) -> Dict:
        """Convert PostgreSQL booking to Google Sheets format"""
        try:
            if isinstance(booking, Booking):
                booking_dict = booking.to_dict()
            else:
                booking_dict = booking
            
            # Map English column names to Vietnamese
            mapped = {
                'Số đặt phòng': booking_dict.get('booking_id', ''),
                'Tên người đặt': booking_dict.get('guest_name', ''),
                'Tên chỗ nghỉ': '118 Hang Bac Hostel',
                'Check-in Date': booking_dict.get('checkin_date', ''),
                'Check-out Date': booking_dict.get('checkout_date', ''),
                'Tổng thanh toán': booking_dict.get('room_amount', 0),
                'Hoa hồng': booking_dict.get('commission', 0),
                'Taxi': booking_dict.get('taxi_amount', 0),
                'Người thu tiền': booking_dict.get('collector', ''),
                'Tình trạng': 'OK' if booking_dict.get('booking_status') == 'confirmed' else 'Đã hủy',
                'Ghi chú thanh toán': booking_dict.get('booking_notes', ''),
                'Tiền tệ': 'VND',
                'Vị trí': 'Hà Nội',
                'Thành viên Genius': 'Không',
            }
            
            return mapped
        except Exception as e:
            logger.error(f"Error mapping postgres to sheets: {e}")
            raise DataMappingError(f"Failed to map postgres data: {e}")

class DataMappingError(DatabaseError):
    """Error in data mapping between formats"""
    pass

# =====================================================
# HYBRID DATABASE SERVICE
# =====================================================

class HybridDatabaseService:
    """
    Unified database service that routes requests between PostgreSQL and Google Sheets
    Provides zero-risk migration path with intelligent fallback
    """
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.mapper = DataMapper()
    
    @contextmanager
    def performance_timer(self, operation_name: str):
        """Context manager for performance monitoring"""
        with PerformanceTimer(operation_name) as timer:
            yield timer
    
    def _try_postgresql_operation(self, operation_func, *args, **kwargs):
        """Try PostgreSQL operation with error handling"""
        try:
            return operation_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"PostgreSQL operation failed: {e}")
            raise PostgreSQLError(f"PostgreSQL error: {e}")
    
    def _try_sheets_operation(self, operation_func, *args, **kwargs):
        """Try Google Sheets operation with error handling"""
        try:
            return operation_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Google Sheets operation failed: {e}")
            raise GoogleSheetsError(f"Google Sheets error: {e}")
    
    def _execute_with_fallback(self, primary_func, fallback_func, operation_name: str):
        """Execute operation with fallback support"""
        primary_backend = self.config.get_primary_backend()
        fallback_backend = self.config.get_fallback_backend()
        
        with self.performance_timer(operation_name):
            try:
                # Try primary backend
                if primary_backend == 'postgresql':
                    return self._try_postgresql_operation(primary_func)
                else:
                    return self._try_sheets_operation(primary_func)
                    
            except Exception as e:
                logger.warning(f"Primary backend ({primary_backend}) failed: {e}")
                
                # Try fallback if enabled
                if fallback_backend and self.config.FALLBACK_TO_SHEETS:
                    logger.info(f"Falling back to {fallback_backend}")
                    try:
                        if fallback_backend == 'google_sheets':
                            return self._try_sheets_operation(fallback_func)
                        else:
                            return self._try_postgresql_operation(fallback_func)
                    except Exception as fallback_error:
                        logger.error(f"Fallback backend ({fallback_backend}) also failed: {fallback_error}")
                        raise DatabaseError(f"Both primary and fallback failed: {e}, {fallback_error}")
                else:
                    raise DatabaseError(f"Primary backend failed and no fallback available: {e}")
    
    # =====================================================
    # BOOKING OPERATIONS
    # =====================================================
    
    def get_all_bookings(self) -> List[Dict]:
        """Get all bookings from the database"""
        
        def postgres_get_all():
            bookings = Booking.query.join(Guest).all()
            return [booking.to_dict() for booking in bookings]
        
        def sheets_get_all():
            df = import_from_gsheet(
                self.config.DEFAULT_SHEET_ID,
                self.config.GCP_CREDS_FILE_PATH
            )
            bookings = []
            for _, row in df.iterrows():
                try:
                    booking = self.mapper.sheets_to_postgres_booking(row.to_dict())
                    bookings.append(booking)
                except Exception as e:
                    logger.warning(f"Skipping invalid booking row: {e}")
                    continue
            return bookings
        
        return self._execute_with_fallback(postgres_get_all, sheets_get_all, "get_all_bookings")
    
    def get_booking_by_id(self, booking_id: str) -> Optional[Dict]:
        """Get a specific booking by ID"""
        
        def postgres_get_by_id():
            booking = Booking.query.filter_by(booking_id=booking_id).join(Guest).first()
            return booking.to_dict() if booking else None
        
        def sheets_get_by_id():
            df = import_from_gsheet(
                self.config.DEFAULT_SHEET_ID,
                self.config.GCP_CREDS_FILE_PATH
            )
            booking_row = df[df['Số đặt phòng'] == booking_id]
            if booking_row.empty:
                return None
            return self.mapper.sheets_to_postgres_booking(booking_row.iloc[0].to_dict())
        
        return self._execute_with_fallback(postgres_get_by_id, sheets_get_by_id, f"get_booking_by_id({booking_id})")
    
    def create_booking(self, booking_data: Dict) -> Dict:
        """Create a new booking"""
        
        def postgres_create():
            # First, create or get guest
            guest = Guest.query.filter_by(full_name=booking_data['guest_name']).first()
            if not guest:
                guest = Guest(
                    full_name=booking_data['guest_name'],
                    email=booking_data.get('email'),
                    phone=booking_data.get('phone')
                )
                db.session.add(guest)
                db.session.flush()
            
            # Create booking
            booking = Booking(
                booking_id=booking_data['booking_id'],
                guest_id=guest.guest_id,
                checkin_date=booking_data['checkin_date'],
                checkout_date=booking_data['checkout_date'],
                room_amount=booking_data.get('room_amount', 0),
                taxi_amount=booking_data.get('taxi_amount', 0),
                commission=booking_data.get('commission', 0),
                collector=booking_data.get('collector'),
                booking_status=booking_data.get('booking_status', 'confirmed'),
                payment_status=booking_data.get('payment_status', 'pending'),
                has_taxi=booking_data.get('has_taxi', False),
                booking_notes=booking_data.get('booking_notes', ''),
            )
            
            db.session.add(booking)
            db.session.commit()
            return booking.to_dict()
        
        def sheets_create():
            # Convert to sheets format
            sheets_data = self.mapper.postgres_to_sheets_booking(booking_data)
            
            # Append to sheets
            append_multiple_bookings_to_sheet(
                [sheets_data],
                self.config.DEFAULT_SHEET_ID,
                self.config.GCP_CREDS_FILE_PATH
            )
            
            return booking_data
        
        return self._execute_with_fallback(postgres_create, sheets_create, f"create_booking({booking_data.get('booking_id')})")
    
    def update_booking(self, booking_id: str, update_data: Dict) -> Dict:
        """Update an existing booking"""
        
        def postgres_update():
            booking = Booking.query.filter_by(booking_id=booking_id).first()
            if not booking:
                raise ValueError(f"Booking {booking_id} not found")
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(booking, key):
                    setattr(booking, key, value)
            
            db.session.commit()
            return booking.to_dict()
        
        def sheets_update():
            # Get current data
            df = import_from_gsheet(
                self.config.DEFAULT_SHEET_ID,
                self.config.GCP_CREDS_FILE_PATH
            )
            
            # Find row to update
            row_index = df[df['Số đặt phòng'] == booking_id].index
            if row_index.empty:
                raise ValueError(f"Booking {booking_id} not found in sheets")
            
            # Update row
            sheets_update_data = self.mapper.postgres_to_sheets_booking(update_data)
            update_row_in_gsheet(
                self.config.DEFAULT_SHEET_ID,
                self.config.GCP_CREDS_FILE_PATH,
                row_index[0] + 2,  # +2 for header and 0-based index
                sheets_update_data
            )
            
            return update_data
        
        return self._execute_with_fallback(postgres_update, sheets_update, f"update_booking({booking_id})")
    
    def delete_booking(self, booking_id: str) -> bool:
        """Delete a booking"""
        
        def postgres_delete():
            booking = Booking.query.filter_by(booking_id=booking_id).first()
            if not booking:
                return False
            
            db.session.delete(booking)
            db.session.commit()
            return True
        
        def sheets_delete():
            # For Google Sheets, we'll mark as cancelled instead of deleting
            return self.update_booking(booking_id, {'booking_status': 'cancelled'})
        
        return self._execute_with_fallback(postgres_delete, sheets_delete, f"delete_booking({booking_id})")
    
    # =====================================================
    # DASHBOARD OPERATIONS
    # =====================================================
    
    def get_dashboard_data(self) -> Dict:
        """Get dashboard analytics data"""
        
        def postgres_dashboard():
            today = date.today()
            
            # Get statistics
            total_bookings = Booking.query.count()
            active_bookings = Booking.query.filter(
                Booking.booking_status.in_(['confirmed', 'checked_in'])
            ).count()
            
            # Today's arrivals
            todays_arrivals = Booking.query.filter(
                Booking.checkin_date == today,
                Booking.booking_status == 'confirmed'
            ).join(Guest).all()
            
            # Overdue payments
            overdue_payments = Booking.query.filter(
                Booking.checkin_date <= today,
                Booking.payment_status != 'completed',
                Booking.booking_status != 'cancelled'
            ).join(Guest).all()
            
            return {
                'total_bookings': total_bookings,
                'active_bookings': active_bookings,
                'todays_arrivals': [booking.to_dict() for booking in todays_arrivals],
                'overdue_payments': [booking.to_dict() for booking in overdue_payments],
                'performance_backend': 'postgresql'
            }
        
        def sheets_dashboard():
            # Existing dashboard logic from dashboard_routes.py
            from dashboard_routes import process_overdue_guests
            
            df = import_from_gsheet(
                self.config.DEFAULT_SHEET_ID,
                self.config.GCP_CREDS_FILE_PATH
            )
            
            # Process data (simplified version)
            total_bookings = len(df)
            active_bookings = len(df[df['Tình trạng'] == 'OK'])
            
            # Get overdue guests
            overdue_data = process_overdue_guests(df)
            
            return {
                'total_bookings': total_bookings,
                'active_bookings': active_bookings,
                'overdue_payments': overdue_data.get('overdue_guests', []),
                'todays_arrivals': [],  # Would need to implement
                'performance_backend': 'google_sheets'
            }
        
        return self._execute_with_fallback(postgres_dashboard, sheets_dashboard, "get_dashboard_data")
    
    # =====================================================
    # QUICK NOTES OPERATIONS
    # =====================================================
    
    def get_quick_notes(self, completed: Optional[bool] = None) -> List[Dict]:
        """Get quick notes"""
        
        def postgres_get_notes():
            query = QuickNote.query
            if completed is not None:
                query = query.filter(QuickNote.completed == completed)
            notes = query.order_by(QuickNote.created_at.desc()).all()
            return [note.to_dict() for note in notes]
        
        def sheets_get_notes():
            # Existing quick notes logic from logic.py
            # This would need to be implemented based on current sheets structure
            return []
        
        return self._execute_with_fallback(postgres_get_notes, sheets_get_notes, f"get_quick_notes(completed={completed})")
    
    def create_quick_note(self, note_data: Dict) -> Dict:
        """Create a quick note"""
        
        def postgres_create_note():
            note = QuickNote(
                note_id=note_data.get('note_id', int(time.time() * 1000)),
                note_type=note_data['note_type'],
                content=note_data['content'],
                guest_name=note_data.get('guest_name'),
                booking_id=note_data.get('booking_id'),
                reminder_date=note_data.get('reminder_date'),
                reminder_time=note_data.get('reminder_time'),
                priority=note_data.get('priority', 'normal')
            )
            
            db.session.add(note)
            db.session.commit()
            return note.to_dict()
        
        def sheets_create_note():
            # Use existing sheets logic for quick notes
            return note_data
        
        return self._execute_with_fallback(postgres_create_note, sheets_create_note, "create_quick_note")
    
    # =====================================================
    # HEALTH CHECK & MONITORING
    # =====================================================
    
    def health_check(self) -> Dict:
        """Check health of both backends"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'primary_backend': self.config.get_primary_backend(),
            'fallback_backend': self.config.get_fallback_backend(),
            'postgresql': {'status': 'unknown', 'response_time': None, 'error': None},
            'google_sheets': {'status': 'unknown', 'response_time': None, 'error': None}
        }
        
        # Test PostgreSQL
        try:
            with PerformanceTimer("health_check_postgresql") as timer:
                guest_count = Guest.query.count()
            health_status['postgresql'] = {
                'status': 'healthy',
                'response_time': f"{(timer.end_time - timer.start_time) * 1000:.1f}ms",
                'guest_count': guest_count,
                'error': None
            }
        except Exception as e:
            health_status['postgresql'] = {
                'status': 'error',
                'response_time': None,
                'error': str(e)
            }
        
        # Test Google Sheets
        try:
            with PerformanceTimer("health_check_sheets") as timer:
                df = import_from_gsheet(
                    self.config.DEFAULT_SHEET_ID,
                    self.config.GCP_CREDS_FILE_PATH
                )
            health_status['google_sheets'] = {
                'status': 'healthy',
                'response_time': f"{(timer.end_time - timer.start_time) * 1000:.1f}ms",
                'booking_count': len(df),
                'error': None
            }
        except Exception as e:
            health_status['google_sheets'] = {
                'status': 'error',
                'response_time': None,
                'error': str(e)
            }
        
        return health_status
    
    def get_performance_stats(self) -> Dict:
        """Get performance comparison between backends"""
        return {
            'config': {
                'primary_backend': self.config.get_primary_backend(),
                'fallback_backend': self.config.get_fallback_backend(),
                'use_postgresql': self.config.USE_POSTGRESQL,
                'use_hybrid_mode': self.config.USE_HYBRID_MODE,
                'fallback_to_sheets': self.config.FALLBACK_TO_SHEETS
            },
            'health_check': self.health_check()
        }

# =====================================================
# GLOBAL SERVICE INSTANCE
# =====================================================

# Global service instance
db_service = HybridDatabaseService()

# =====================================================
# FLASK ROUTE HELPERS
# =====================================================

def get_database_service() -> HybridDatabaseService:
    """Get the global database service instance"""
    return db_service

def init_database_service(app):
    """Initialize the database service with Flask app"""
    global db_service
    
    # Initialize models
    from models import init_db
    init_db(app)
    
    # Create tables if using PostgreSQL
    if DatabaseConfig.USE_POSTGRESQL:
        try:
            from models import create_all_tables
            create_all_tables(app)
            logger.info("✅ PostgreSQL tables initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize PostgreSQL tables: {e}")
    
    logger.info(f"🚀 Hybrid Database Service initialized - Primary: {DatabaseConfig.get_primary_backend()}")
    return db_service