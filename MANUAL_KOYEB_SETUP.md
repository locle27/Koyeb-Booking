# 🗄️ Manual Koyeb PostgreSQL Database Setup

Since CLI login requires interactive mode, here's how to create your database manually:

## **Step 1: Create Database via Web Interface**

1. **Go to Koyeb Dashboard:** https://app.koyeb.com
2. **Login to your account**
3. **Click "Databases" in the left sidebar**
4. **Click "Create Database"**
5. **Configure Database:**
   - **Name:** `hotel-booking-db`
   - **Engine:** PostgreSQL
   - **Version:** 15 (latest)
   - **Plan:** Small (2GB RAM, 20GB Storage)
   - **Region:** Frankfurt (fra) or closest to your app
6. **Click "Create Database"**

## **Step 2: Get Connection Details**

1. **Wait 2-3 minutes for database to be ready**
2. **Click on your database name**
3. **Go to "Connection" tab**
4. **Copy the DATABASE_URL** (looks like: `postgresql://user:password@host:5432/database`)

## **Step 3: Configure Your Environment**

```bash
# Add to your .env file:
DATABASE_URL=postgresql://user:password@host:5432/database

# Also set these for hybrid mode:
USE_POSTGRESQL=false        # Start safely
USE_HYBRID_MODE=true       # Enable dual backend
FALLBACK_TO_SHEETS=true    # Safety fallback
```

## **Step 4: Test Connection**

```bash
# Test connection
python quick_test.py

# Should show: ✅ PostgreSQL connected to your-host
```

## **Step 5: Run Migration**

```bash
# Safe dry run first
python migrate_to_postgresql.py --dry-run

# If successful, run actual migration
python migrate_to_postgresql.py
```

## **Alternative: Using API Token**

If you can get an API token from Koyeb:

1. **Go to:** https://app.koyeb.com/settings/api
2. **Create new token**
3. **Copy token**
4. **Use CLI:**

```bash
export PATH="/home/locle/.koyeb/bin:$PATH"
export KOYEB_TOKEN="your-api-token-here"

# Create database via CLI
koyeb --token $KOYEB_TOKEN databases create hotel-booking-db \
  --type postgresql \
  --plan small \
  --region fra

# Get connection details
koyeb --token $KOYEB_TOKEN databases get hotel-booking-db
```

## **🎯 What You'll Get**

Once created, you'll have:
- **PostgreSQL 15 database**
- **2GB RAM, 20GB storage** 
- **Frankfurt region** (low latency)
- **Connection string** for your app

**Expected setup time:** 5 minutes
**Expected migration time:** 5 minutes
**Total time to 50-100x faster system:** 10 minutes

---

**Choose the method that works best for you and let me know when you have the DATABASE_URL!**