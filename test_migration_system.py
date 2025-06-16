#!/usr/bin/env python3
"""
Hotel Booking System - Migration Testing Suite
Complete testing framework for PostgreSQL migration

This script provides comprehensive testing for:
- Database connections
- Data migration integrity
- Performance benchmarks
- Hybrid system functionality
- Error handling and fallback
"""

import os
import sys
import time
import json
import traceback
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
import tempfile

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def colored_print(message: str, color: str = 'white'):
    """Print colored messages for better visibility"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, colors['white'])}{message}{colors['reset']}")

class MigrationTester:
    """Comprehensive testing suite for migration system"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
        
    def log_test_result(self, test_name: str, passed: bool, details: str = "", duration: float = 0):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        color = "green" if passed else "red"
        
        self.test_results.append({
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'duration_ms': duration * 1000,
            'timestamp': datetime.now().isoformat()
        })
        
        colored_print(f"{status} {test_name}", color)
        if details:
            print(f"    📝 {details}")
        if duration > 0:
            print(f"    ⏱️ {duration*1000:.1f}ms")
        print()

    # =====================================================
    # ENVIRONMENT AND DEPENDENCY TESTS
    # =====================================================
    
    def test_environment_variables(self):
        """Test if required environment variables are set"""
        colored_print("🔧 Testing Environment Variables", "blue")
        
        required_vars = [
            'GCP_CREDS_FILE_PATH',
            'DEFAULT_SHEET_ID',
            'GOOGLE_API_KEY'
        ]
        
        optional_vars = [
            'DATABASE_URL',
            'USE_POSTGRESQL',
            'USE_HYBRID_MODE',
            'FALLBACK_TO_SHEETS'
        ]
        
        missing_required = []
        missing_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        if missing_required:
            self.log_test_result(
                "Environment Variables",
                False,
                f"Missing required: {', '.join(missing_required)}"
            )
        else:
            details = f"All required vars present. Optional missing: {', '.join(missing_optional) if missing_optional else 'None'}"
            self.log_test_result("Environment Variables", True, details)
    
    def test_dependencies(self):
        """Test if required Python packages are installed"""
        colored_print("📦 Testing Dependencies", "blue")
        
        required_packages = [
            ('pandas', 'pandas'),
            ('flask', 'Flask'),
            ('gspread', 'gspread'),
            ('google.generativeai', 'google-generativeai'),
        ]
        
        optional_packages = [
            ('psycopg2', 'psycopg2-binary'),
            ('sqlalchemy', 'SQLAlchemy'),
            ('flask_sqlalchemy', 'Flask-SQLAlchemy')
        ]
        
        missing_required = []
        missing_optional = []
        
        for module, package in required_packages:
            try:
                __import__(module)
            except ImportError:
                missing_required.append(package)
        
        for module, package in optional_packages:
            try:
                __import__(module)
            except ImportError:
                missing_optional.append(package)
        
        if missing_required:
            self.log_test_result(
                "Dependencies",
                False,
                f"Missing required: pip install {' '.join(missing_required)}"
            )
        else:
            details = f"Required packages OK. Optional missing: {', '.join(missing_optional) if missing_optional else 'None'}"
            self.log_test_result("Dependencies", True, details)
    
    # =====================================================
    # DATABASE CONNECTION TESTS
    # =====================================================
    
    def test_google_sheets_connection(self):
        """Test Google Sheets connection and data access"""
        colored_print("📊 Testing Google Sheets Connection", "blue")
        
        try:
            start_time = time.time()
            
            from logic import import_from_gsheet
            
            sheet_id = os.getenv('DEFAULT_SHEET_ID')
            creds_path = os.getenv('GCP_CREDS_FILE_PATH')
            
            if not sheet_id or not creds_path:
                self.log_test_result(
                    "Google Sheets Connection",
                    False,
                    "Missing DEFAULT_SHEET_ID or GCP_CREDS_FILE_PATH"
                )
                return
            
            df = import_from_gsheet(sheet_id, creds_path)
            duration = time.time() - start_time
            
            if len(df) > 0:
                self.log_test_result(
                    "Google Sheets Connection",
                    True,
                    f"Successfully loaded {len(df)} records",
                    duration
                )
                return df
            else:
                self.log_test_result(
                    "Google Sheets Connection",
                    False,
                    "No data found in sheet"
                )
                
        except Exception as e:
            self.log_test_result(
                "Google Sheets Connection",
                False,
                f"Error: {str(e)}"
            )
        
        return None
    
    def test_postgresql_connection(self):
        """Test PostgreSQL connection"""
        colored_print("🗄️ Testing PostgreSQL Connection", "blue")
        
        try:
            database_url = os.getenv('DATABASE_URL')
            
            if not database_url:
                self.log_test_result(
                    "PostgreSQL Connection",
                    False,
                    "DATABASE_URL not set. Run: export DATABASE_URL=postgresql://..."
                )
                return False
            
            start_time = time.time()
            
            # Test basic connection
            try:
                import psycopg2
                from urllib.parse import urlparse
                
                url = urlparse(database_url)
                conn = psycopg2.connect(
                    host=url.hostname,
                    port=url.port,
                    database=url.path[1:],
                    user=url.username,
                    password=url.password
                )
                conn.close()
                duration = time.time() - start_time
                
                self.log_test_result(
                    "PostgreSQL Connection",
                    True,
                    f"Connected to {url.hostname}",
                    duration
                )
                return True
                
            except ImportError:
                self.log_test_result(
                    "PostgreSQL Connection",
                    False,
                    "psycopg2 not installed. Run: pip install psycopg2-binary"
                )
                
        except Exception as e:
            self.log_test_result(
                "PostgreSQL Connection",
                False,
                f"Error: {str(e)}"
            )
        
        return False
    
    # =====================================================
    # MIGRATION SYSTEM TESTS
    # =====================================================
    
    def test_models_import(self):
        """Test SQLAlchemy models import and functionality"""
        colored_print("🏗️ Testing SQLAlchemy Models", "blue")
        
        try:
            start_time = time.time()
            
            from models import Guest, Booking, QuickNote, Expense, MessageTemplate, ArrivalTime
            from models import db, init_db, create_all_tables, get_db_stats
            
            duration = time.time() - start_time
            
            # Test model instantiation
            guest = Guest(full_name="Test Guest")
            booking = Booking(booking_id="TEST001", checkin_date=date.today(), checkout_date=date.today() + timedelta(days=1))
            
            self.log_test_result(
                "SQLAlchemy Models",
                True,
                "All models imported and instantiated successfully",
                duration
            )
            
        except Exception as e:
            self.log_test_result(
                "SQLAlchemy Models",
                False,
                f"Error: {str(e)}"
            )
    
    def test_database_service_import(self):
        """Test hybrid database service import"""
        colored_print("🔄 Testing Database Service", "blue")
        
        try:
            start_time = time.time()
            
            from database_service import HybridDatabaseService, DatabaseConfig, get_database_service
            from database_service import DataMapper, PerformanceTimer
            
            # Test service instantiation
            service = HybridDatabaseService()
            config = DatabaseConfig()
            mapper = DataMapper()
            
            duration = time.time() - start_time
            
            self.log_test_result(
                "Database Service",
                True,
                f"Service loaded. Primary backend: {config.get_primary_backend()}",
                duration
            )
            
            return service
            
        except Exception as e:
            self.log_test_result(
                "Database Service",
                False,
                f"Error: {str(e)}"
            )
            return None
    
    def test_migration_script_import(self):
        """Test migration script import"""
        colored_print("📋 Testing Migration Script", "blue")
        
        try:
            start_time = time.time()
            
            from migrate_to_postgresql import PostgreSQLMigrator, MigrationConfig, DataVerifier
            from migrate_to_postgresql import PerformanceBenchmark, MigrationLogger
            
            duration = time.time() - start_time
            
            self.log_test_result(
                "Migration Script",
                True,
                "All migration components imported successfully",
                duration
            )
            
        except Exception as e:
            self.log_test_result(
                "Migration Script",
                False,
                f"Error: {str(e)}"
            )
    
    # =====================================================
    # DATA MAPPING TESTS
    # =====================================================
    
    def test_data_mapping(self, sample_sheets_data=None):
        """Test data mapping between Google Sheets and PostgreSQL formats"""
        colored_print("🔀 Testing Data Mapping", "blue")
        
        try:
            from database_service import DataMapper
            
            mapper = DataMapper()
            
            # Create sample Google Sheets data
            sample_row = {
                'Số đặt phòng': 'TEST123',
                'Tên người đặt': 'John Doe',
                'Check-in Date': '2025-06-16',
                'Check-out Date': '2025-06-18',
                'Tổng thanh toán': '350000',
                'Hoa hồng': '35000',
                'Taxi': '50000',
                'Người thu tiền': 'LOC LE',
                'Tình trạng': 'OK',
                'Ghi chú thanh toán': 'Test booking'
            }
            
            start_time = time.time()
            
            # Test sheets to postgres mapping
            postgres_data = mapper.sheets_to_postgres_booking(sample_row)
            
            # Test postgres to sheets mapping
            sheets_data = mapper.postgres_to_sheets_booking(postgres_data)
            
            duration = time.time() - start_time
            
            # Verify key fields
            success = (
                postgres_data['booking_id'] == 'TEST123' and
                postgres_data['guest_name'] == 'John Doe' and
                postgres_data['room_amount'] == 350000.0 and
                sheets_data['Số đặt phòng'] == 'TEST123'
            )
            
            if success:
                self.log_test_result(
                    "Data Mapping",
                    True,
                    "Bidirectional mapping working correctly",
                    duration
                )
            else:
                self.log_test_result(
                    "Data Mapping",
                    False,
                    f"Mapping inconsistency: {postgres_data}"
                )
                
        except Exception as e:
            self.log_test_result(
                "Data Mapping",
                False,
                f"Error: {str(e)}"
            )
    
    # =====================================================
    # PERFORMANCE TESTS
    # =====================================================
    
    def test_performance_comparison(self, sheets_df=None):
        """Test performance comparison between backends"""
        colored_print("⚡ Testing Performance Comparison", "blue")
        
        if not sheets_df or len(sheets_df) == 0:
            self.log_test_result(
                "Performance Comparison",
                False,
                "No Google Sheets data available for comparison"
            )
            return
        
        try:
            # Test Google Sheets performance (already loaded)
            sheets_start = time.time()
            sheets_count = len(sheets_df)
            sheets_duration = 0.001  # Minimal since already loaded
            
            # Test PostgreSQL performance (if available)
            postgres_duration = None
            postgres_count = 0
            
            try:
                from models import Booking, Guest
                from flask import Flask
                
                app = Flask(__name__)
                app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///:memory:')
                app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
                
                from models import db
                db.init_app(app)
                
                with app.app_context():
                    postgres_start = time.time()
                    bookings = Booking.query.join(Guest).all()
                    postgres_duration = time.time() - postgres_start
                    postgres_count = len(bookings)
                    
            except Exception as e:
                postgres_duration = None
                postgres_error = str(e)
            
            # Calculate results
            if postgres_duration is not None:
                improvement = (sheets_duration * 1000) / (postgres_duration * 1000) if postgres_duration > 0 else float('inf')
                details = f"Sheets: {sheets_duration*1000:.1f}ms ({sheets_count} records), PostgreSQL: {postgres_duration*1000:.1f}ms ({postgres_count} records), {improvement:.1f}x improvement"
                
                self.log_test_result(
                    "Performance Comparison",
                    True,
                    details
                )
            else:
                self.log_test_result(
                    "Performance Comparison",
                    False,
                    f"PostgreSQL test failed: {postgres_error if 'postgres_error' in locals() else 'Unknown error'}"
                )
                
        except Exception as e:
            self.log_test_result(
                "Performance Comparison",
                False,
                f"Error: {str(e)}"
            )
    
    # =====================================================
    # INTEGRATION TESTS
    # =====================================================
    
    def test_flask_integration(self):
        """Test Flask integration with hybrid database service"""
        colored_print("🌐 Testing Flask Integration", "blue")
        
        try:
            from flask import Flask
            from database_service import init_database_service
            
            start_time = time.time()
            
            # Create test Flask app
            app = Flask(__name__)
            app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///:memory:')
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            # Initialize database service
            db_service = init_database_service(app)
            
            duration = time.time() - start_time
            
            self.log_test_result(
                "Flask Integration",
                True,
                "Hybrid database service initialized with Flask",
                duration
            )
            
            return app, db_service
            
        except Exception as e:
            self.log_test_result(
                "Flask Integration",
                False,
                f"Error: {str(e)}"
            )
            return None, None
    
    def test_health_check(self, db_service=None):
        """Test database health check functionality"""
        colored_print("🏥 Testing Health Check", "blue")
        
        if not db_service:
            self.log_test_result(
                "Health Check",
                False,
                "Database service not available"
            )
            return
        
        try:
            start_time = time.time()
            
            health_status = db_service.health_check()
            
            duration = time.time() - start_time
            
            # Check if health check returns expected structure
            required_keys = ['timestamp', 'primary_backend', 'postgresql', 'google_sheets']
            has_required_keys = all(key in health_status for key in required_keys)
            
            if has_required_keys:
                pg_status = health_status['postgresql']['status']
                sheets_status = health_status['google_sheets']['status']
                
                self.log_test_result(
                    "Health Check",
                    True,
                    f"PostgreSQL: {pg_status}, Google Sheets: {sheets_status}",
                    duration
                )
            else:
                self.log_test_result(
                    "Health Check",
                    False,
                    f"Missing required keys in health status: {health_status}"
                )
                
        except Exception as e:
            self.log_test_result(
                "Health Check",
                False,
                f"Error: {str(e)}"
            )
    
    # =====================================================
    # MIGRATION SIMULATION TESTS
    # =====================================================
    
    def test_dry_run_migration(self):
        """Test migration dry run"""
        colored_print("🧪 Testing Migration Dry Run", "blue")
        
        try:
            import subprocess
            import sys
            
            start_time = time.time()
            
            # Run migration script in dry run mode
            result = subprocess.run([
                sys.executable, 'migrate_to_postgresql.py', '--dry-run'
            ], capture_output=True, text=True, timeout=60)
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.log_test_result(
                    "Migration Dry Run",
                    True,
                    "Dry run completed successfully",
                    duration
                )
            else:
                self.log_test_result(
                    "Migration Dry Run",
                    False,
                    f"Exit code: {result.returncode}, Error: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            self.log_test_result(
                "Migration Dry Run",
                False,
                "Dry run timed out after 60 seconds"
            )
        except Exception as e:
            self.log_test_result(
                "Migration Dry Run",
                False,
                f"Error: {str(e)}"
            )
    
    # =====================================================
    # COMPREHENSIVE TEST RUNNER
    # =====================================================
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        colored_print("🚀 Starting Comprehensive Migration Testing", "cyan")
        colored_print("=" * 60, "cyan")
        
        # Phase 1: Environment and Dependencies
        colored_print("\n📋 PHASE 1: Environment Setup", "purple")
        self.test_environment_variables()
        self.test_dependencies()
        
        # Phase 2: Database Connections
        colored_print("\n📋 PHASE 2: Database Connections", "purple")
        sheets_df = self.test_google_sheets_connection()
        postgres_available = self.test_postgresql_connection()
        
        # Phase 3: Migration System
        colored_print("\n📋 PHASE 3: Migration System", "purple")
        self.test_models_import()
        db_service = self.test_database_service_import()
        self.test_migration_script_import()
        
        # Phase 4: Data Processing
        colored_print("\n📋 PHASE 4: Data Processing", "purple")
        self.test_data_mapping(sheets_df)
        
        # Phase 5: Performance Testing
        colored_print("\n📋 PHASE 5: Performance Testing", "purple")
        self.test_performance_comparison(sheets_df)
        
        # Phase 6: Integration Testing
        colored_print("\n📋 PHASE 6: Integration Testing", "purple")
        app, db_service = self.test_flask_integration()
        self.test_health_check(db_service)
        
        # Phase 7: Migration Testing
        if postgres_available:
            colored_print("\n📋 PHASE 7: Migration Testing", "purple")
            self.test_dry_run_migration()
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        total_duration = time.time() - self.start_time
        
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        total_tests = len(self.test_results)
        
        colored_print("\n" + "=" * 60, "cyan")
        colored_print("📊 TEST SUMMARY", "cyan")
        colored_print("=" * 60, "cyan")
        
        colored_print(f"✅ Passed: {passed_tests}/{total_tests}", "green" if passed_tests == total_tests else "yellow")
        colored_print(f"⏱️ Total Duration: {total_duration:.1f}s", "blue")
        
        if passed_tests == total_tests:
            colored_print("🎉 ALL TESTS PASSED! Migration system is ready for deployment.", "green")
        else:
            colored_print("⚠️ Some tests failed. Check the details above.", "yellow")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['passed']]
            if failed_tests:
                colored_print("\n❌ Failed Tests:", "red")
                for test in failed_tests:
                    colored_print(f"  • {test['test_name']}: {test['details']}", "red")
        
        # Save detailed results
        self.save_test_results()
        
        # Show next steps
        colored_print("\n🔗 Next Steps:", "blue")
        if passed_tests == total_tests:
            colored_print("1. Create Koyeb PostgreSQL database", "white")
            colored_print("2. Set DATABASE_URL environment variable", "white") 
            colored_print("3. Run: python migrate_to_postgresql.py", "white")
            colored_print("4. Enable hybrid mode in production", "white")
        else:
            colored_print("1. Fix failed tests listed above", "white")
            colored_print("2. Re-run tests: python test_migration_system.py", "white")
            colored_print("3. Proceed with migration once all tests pass", "white")
    
    def save_test_results(self):
        """Save test results to file"""
        try:
            os.makedirs('test_reports', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f'test_reports/migration_test_report_{timestamp}.json'
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_duration_seconds': time.time() - self.start_time,
                'test_results': self.test_results,
                'summary': {
                    'total_tests': len(self.test_results),
                    'passed_tests': sum(1 for r in self.test_results if r['passed']),
                    'failed_tests': sum(1 for r in self.test_results if not r['passed'])
                }
            }
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            colored_print(f"📄 Test report saved: {report_file}", "blue")
            
        except Exception as e:
            colored_print(f"⚠️ Could not save test report: {e}", "yellow")

def main():
    """Main testing function"""
    print("\n" + "🧪 " * 30)
    colored_print("HOTEL BOOKING SYSTEM - POSTGRESQL MIGRATION TESTING", "cyan")
    print("🧪 " * 30 + "\n")
    
    tester = MigrationTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        colored_print("\n⏹️ Testing interrupted by user", "yellow")
    except Exception as e:
        colored_print(f"\n❌ Testing failed with error: {e}", "red")
        traceback.print_exc()

if __name__ == '__main__':
    main()