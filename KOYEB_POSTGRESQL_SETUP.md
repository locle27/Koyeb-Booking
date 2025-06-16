# 🚀 Koyeb PostgreSQL Setup Guide
**Hotel Booking System - Zero-Risk Migration**

## 📋 Step-by-Step Setup

### 1. **Create PostgreSQL Database on Koyeb**
```bash
# Login to Koyeb CLI
koyeb login

# Create PostgreSQL database
koyeb databases create hotel-booking-db \
  --type postgresql \
  --plan small \
  --region fra

# Get connection details
koyeb databases get hotel-booking-db
```

**Expected Output:**
```
Database: hotel-booking-db
Status: Running
Type: PostgreSQL 15
Plan: Small (2GB RAM, 20GB Storage)
Region: Frankfurt (fra)
Connection: postgresql://user:password@host:5432/database
```

### 2. **Configure Environment Variables**
Add to your `.env` file or Koyeb environment:

```bash
# PostgreSQL Configuration
DATABASE_URL=postgresql://user:password@host:5432/database
USE_POSTGRESQL=false                    # Start with false for safety
USE_HYBRID_MODE=true                   # Enable hybrid mode
FALLBACK_TO_SHEETS=true               # Keep Google Sheets as fallback

# Performance Monitoring
ENABLE_PERFORMANCE_LOGGING=true

# Migration Settings
MIGRATION_BATCH_SIZE=100
VERIFICATION_SAMPLE_SIZE=50

# Existing Google Sheets (keep these)
GCP_CREDS_FILE_PATH=your-credentials.json
DEFAULT_SHEET_ID=your-sheet-id
GOOGLE_API_KEY=your-api-key
```

### 3. **Install PostgreSQL Dependencies**
```bash
pip install psycopg2-binary SQLAlchemy Flask-SQLAlchemy
```

### 4. **Test Database Connection**
```python
# test_connection.py
import os
import psycopg2
from urllib.parse import urlparse

DATABASE_URL = os.getenv('DATABASE_URL')
url = urlparse(DATABASE_URL)

try:
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        database=url.path[1:],
        user=url.username,
        password=url.password
    )
    print("✅ PostgreSQL connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## 🔄 Migration Process

### Phase 1: Foundation (Week 1)
```bash
# 1. Setup database schema
python migrate_to_postgresql.py --create-sample-data

# 2. Test migration (dry run)
python migrate_to_postgresql.py --dry-run

# 3. Run benchmarks
python migrate_to_postgresql.py --benchmark-only
```

### Phase 2: Gradual Migration (Week 2-3)
```bash
# 1. Enable hybrid mode (both backends running)
# Set in environment:
USE_HYBRID_MODE=true
USE_POSTGRESQL=false  # Still use Google Sheets as primary
FALLBACK_TO_SHEETS=true

# 2. Run actual migration
python migrate_to_postgresql.py

# 3. Verify data integrity
python -c "
from database_service import get_database_service
service = get_database_service()
print(service.health_check())
"
```

### Phase 3: Full Switch (Week 4)
```bash
# 1. Switch to PostgreSQL as primary
# Update environment:
USE_POSTGRESQL=true
FALLBACK_TO_SHEETS=true  # Keep fallback for 30 days

# 2. Monitor performance
# Check logs for performance improvements

# 3. After 30 days, disable fallback:
FALLBACK_TO_SHEETS=false
```

## ⚡ Expected Performance Gains

| Operation | Google Sheets | PostgreSQL | Improvement |
|-----------|---------------|------------|-------------|
| **Dashboard Load** | 3-5 seconds | 50-100ms | **30-100x faster** |
| **Search Bookings** | 2-3 seconds | 20-50ms | **40-150x faster** |
| **Add Booking** | 1-2 seconds | 10-30ms | **33-200x faster** |
| **Duplicate Detection** | 5-10 seconds | 100ms | **50-100x faster** |
| **RAG Queries** | 1-2 seconds | 50ms | **20-40x faster** |

## 🛡️ Safety Features

### **Zero-Downtime Migration**
- Hybrid mode runs both backends simultaneously
- Automatic fallback to Google Sheets if PostgreSQL fails
- Real-time health monitoring

### **Data Verification**
- Complete data integrity checks
- Sample verification of random records
- Automated rollback on failure

### **Performance Monitoring**
- Real-time performance comparison
- Detailed operation logging
- Performance benchmarks

## 📊 Monitoring Commands

### **Health Check**
```python
from database_service import get_database_service
service = get_database_service()
health = service.health_check()
print(f"PostgreSQL: {health['postgresql']['status']} ({health['postgresql']['response_time']})")
print(f"Google Sheets: {health['google_sheets']['status']} ({health['google_sheets']['response_time']})")
```

### **Performance Stats**
```python
from database_service import get_database_service
service = get_database_service()
stats = service.get_performance_stats()
print(f"Primary Backend: {stats['config']['primary_backend']}")
print(f"PostgreSQL Status: {stats['health_check']['postgresql']['status']}")
```

### **Database Statistics**
```python
from models import get_db_stats
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
with app.app_context():
    stats = get_db_stats(app)
    print(f"Guests: {stats['guests']}")
    print(f"Bookings: {stats['bookings']}")
    print(f"Quick Notes: {stats['quick_notes']}")
```

## 🔧 Integration with Existing App

### **1. Update app.py**
```python
# Add at the top of app.py
from database_service import init_database_service, get_database_service
from models import db

# Initialize hybrid database service
db_service = init_database_service(app)

# Example route using hybrid service
@app.route('/api/bookings')
def get_bookings():
    try:
        bookings = db_service.get_all_bookings()
        return jsonify(bookings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### **2. Update Dashboard Routes**
```python
# In dashboard_routes.py, add:
from database_service import get_database_service

def get_dashboard_data():
    db_service = get_database_service()
    return db_service.get_dashboard_data()
```

### **3. Health Check Endpoint**
```python
@app.route('/api/database/health')
def database_health():
    db_service = get_database_service()
    return jsonify(db_service.health_check())

@app.route('/api/database/performance')
def database_performance():
    db_service = get_database_service()
    return jsonify(db_service.get_performance_stats())
```

## 🚨 Troubleshooting

### **Connection Issues**
```bash
# Test connection manually
python -c "
import psycopg2
from urllib.parse import urlparse
DATABASE_URL = 'your-database-url'
url = urlparse(DATABASE_URL)
conn = psycopg2.connect(host=url.hostname,port=url.port,database=url.path[1:],user=url.username,password=url.password)
print('Connected successfully!')
conn.close()
"
```

### **Migration Errors**
```bash
# Check migration logs
cat migration_reports/migration_report_*.json

# Rollback if needed
python migrate_to_postgresql.py --drop-tables
# Restore from backup in migration_backups/
```

### **Performance Issues**
```bash
# Check slow queries
# Add to PostgreSQL config:
log_min_duration_statement = 1000  # Log queries > 1 second

# Monitor connection pool
pip install psycopg2[pool]
```

## 📈 Success Metrics

### **Week 1 Goals**
- [ ] PostgreSQL database created and accessible
- [ ] Schema deployed successfully
- [ ] Migration dry-run passes verification
- [ ] Performance benchmarks show expected improvements

### **Week 2-3 Goals**
- [ ] Hybrid mode running smoothly
- [ ] Data migration completed with 100% verification
- [ ] Zero downtime during migration
- [ ] Performance monitoring shows improvements

### **Week 4 Goals**
- [ ] Primary backend switched to PostgreSQL
- [ ] Google Sheets fallback working
- [ ] All features working with new backend
- [ ] Performance gains realized (30-100x faster)

## 🎯 Next Steps

1. **Create Koyeb PostgreSQL Database** ✅
2. **Set Environment Variables** ✅
3. **Run Migration Script** ⏳
4. **Enable Hybrid Mode** ⏳
5. **Monitor Performance** ⏳
6. **Switch to Primary** ⏳

**Estimated Total Time:** 2-4 weeks
**Risk Level:** Minimal (Zero-downtime hybrid approach)
**Expected ROI:** 30-100x performance improvement

---

*This guide ensures a smooth, zero-risk migration from Google Sheets to PostgreSQL while maintaining full functionality and providing significant performance improvements.*