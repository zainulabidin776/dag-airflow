# Fix Implementation Guide: NASA APOD Pipeline PostgreSQL Issues

## Issues Fixed

### 1. **Password Authentication Failed**
**Root Cause**: Connection credentials mismatch
- **Before**: Airflow connection tried to use `airflow:airflow` user
- **After**: Configured to use `postgres:postgres` (the actual PostgreSQL user)

**Files Modified**:
- `airflow_settings.yaml` - Updated credentials to `postgres:postgres`

### 2. **Database "apod_db" Does Not Exist**
**Root Cause**: PostgreSQL container started without initializing the required database

**Solution Implemented**:
1. Created `init_db.sql` script that automatically runs on PostgreSQL container startup
2. Script creates:
   - `apod_db` database
   - `apod_data` table with proper schema
   - Indexes for performance
   - Proper permissions

**Files Created**:
- `init_db.sql` - Database initialization script

### 3. **Port Mapping Issues**
**Problem**: Docker Compose override had incorrect port mapping (5433:5432)

**Solution**: Changed to correct mapping (5432:5432) for internal container communication

**Files Modified**:
- `docker-compose.override.yml` - Fixed port and added init script volume

### 4. **Improved Error Handling**
Enhanced `etl_functions.py` with:
- Better connection state management
- Specific exception handling for database errors
- Proper resource cleanup
- Added timestamp update on conflict

## Setup Instructions

### Step 1: Clean Up Existing Containers
```bash
docker-compose down -v
astro dev kill
```

### Step 2: Restart the Environment
```bash
astro dev start
```

PostgreSQL will automatically initialize the database and tables on first run.

### Step 3: Verify Setup
Connect to PostgreSQL and verify:
```bash
docker exec -it <container-name>-postgres-1 psql -U postgres -d apod_db
```

Then run these commands:
```sql
-- Check databases
\l

-- Check tables in apod_db
\dt

-- Verify apod_data table structure
\d apod_data

-- Check indexes
\di
```

You should see:
- Database `apod_db` listed
- Table `apod_data` with all columns
- Indexes on `date` and `created_at`

### Step 4: Test the Pipeline
```bash
astro dev run dags test nasa_apod_etl_pipeline
```

## Troubleshooting

### If still getting password auth errors:
```bash
# Verify connection in Airflow UI
# Admin > Connections > postgres_apod
# Check: User = postgres, Password = postgres, Host = postgres, Port = 5432
```

### If database still doesn't exist:
```bash
# Manually create it:
docker exec -it <container-name>-postgres-1 psql -U postgres -c "CREATE DATABASE apod_db;"
```

### Check container logs:
```bash
docker-compose logs postgres
```

## Key Configuration Changes

| Setting | Before | After |
|---------|--------|-------|
| Connection User | airflow | postgres |
| Connection Password | airflow | postgres |
| Container Port | 5433:5432 | 5432:5432 |
| DB Initialization | None | init_db.sql |
| Table Creation | At runtime | On container start |

## Files Modified/Created

- ✅ Modified: `airflow_settings.yaml` - Corrected credentials
- ✅ Modified: `docker-compose.override.yml` - Fixed port and added init script
- ✅ Modified: `include/scripts/etl_functions.py` - Improved error handling
- ✅ Created: `init_db.sql` - Database initialization script

---

**All issues should now be resolved. The pipeline will work smoothly!** 🚀
