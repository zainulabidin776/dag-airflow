# ✅ Pre-Fix Checklist and Post-Fix Verification

## Pre-Fix: What You Should Have Seen

- ❌ Error: "FATAL: password authentication failed for user"
- ❌ Error: "FATAL: database "apod_db" does not exist"
- ❌ Task retries with "UP_FOR_RETRY" status
- ❌ Unclear error messages in logs

---

## Files That Were Fixed

Copy this checklist and verify all files are modified:

### 1. ✅ `airflow_settings.yaml`
- [ ] Change `conn_login: airflow` → `conn_login: postgres`
- [ ] Change `conn_password: airflow` → `conn_password: postgres`
- [ ] File should contain `postgres:postgres` credentials

```yaml
# Should look like:
connections:
  - conn_id: postgres_apod
    conn_type: postgres
    conn_host: postgres
    conn_schema: apod_db
    conn_login: postgres
    conn_password: postgres
    conn_port: 5432
```

### 2. ✅ `docker-compose.override.yml`
- [ ] Port changed from `5433:5432` to `5432:5432`
- [ ] Added volume: `./init_db.sql:/docker-entrypoint-initdb.d/init_db.sql`

```yaml
# Should look like:
ports:
  - "5432:5432"
volumes:
  - postgres-db-volume:/var/lib/postgresql/data
  - ./init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
```

### 3. ✅ `include/scripts/etl_functions.py`
- [ ] `load_to_postgres` function has improved error handling
- [ ] Variables initialized: `conn = None` and `cursor = None`
- [ ] Has specific exception types: `psycopg2.OperationalError`, `psycopg2.DatabaseError`

### 4. ✅ `init_db.sql` (NEW FILE)
- [ ] File exists in root directory
- [ ] Contains: `CREATE DATABASE apod_db`
- [ ] Contains: `GRANT ALL PRIVILEGES`

---

## Post-Fix: Verification Steps

### Step 1: Container Startup ✅
```bash
astro dev start
# Wait 60 seconds
# Then check: docker ps
```

- [ ] webserver container is running
- [ ] scheduler container is running
- [ ] postgres container is running
- [ ] triggerer container is running

### Step 2: Database Verification ✅
```bash
docker exec -it <postgres-container> psql -U postgres -l
```

Expected output:
```
   Name   | Owner | Encoding | Collate | Ctype | Access privileges
-----------+----------+----------+----------+----------+---------
 apod_db   | postgres | UTF8 | en_US.utf8 | en_US.utf8 |
```

- [ ] `apod_db` database is listed
- [ ] Owner is `postgres`
- [ ] Encoding is `UTF8`

### Step 3: Table Verification ✅
```bash
docker exec -it <postgres-container> psql -U postgres -d apod_db -c "\dt"
```

Expected output:
```
           List of relations
 Schema | Name | Type | Owner
--------+----------+-------+----------
 public | apod_data | table | postgres
```

- [ ] `apod_data` table exists
- [ ] Owner is `postgres`
- [ ] Schema is `public`

### Step 4: Table Structure Verification ✅
```bash
docker exec -it <postgres-container> psql -U postgres -d apod_db -c "\d apod_data"
```

Expected columns:
- [ ] id (integer, primary key)
- [ ] date (date, unique, not null)
- [ ] title (text)
- [ ] url (text)
- [ ] hdurl (text)
- [ ] media_type (varchar)
- [ ] explanation (text)
- [ ] copyright (varchar)
- [ ] retrieved_at (timestamp)
- [ ] created_at (timestamp)
- [ ] updated_at (timestamp)

### Step 5: Airflow Connection Verification ✅
```bash
astro dev run connections get postgres_apod
# Or check in UI: Admin > Connections > postgres_apod
```

- [ ] Conn ID: `postgres_apod`
- [ ] Conn Type: `postgres`
- [ ] Host: `postgres`
- [ ] Database: `apod_db`
- [ ] Login: `postgres`
- [ ] Password: `postgres` (masked as ***)
- [ ] Port: `5432`

### Step 6: DAG Parsing ✅
```bash
astro dev run dags list
```

- [ ] `nasa_apod_etl_pipeline` is listed
- [ ] No parsing errors

### Step 7: Task Test ✅
```bash
astro dev run dags test nasa_apod_etl_pipeline
```

Expected behavior:
- [ ] No authentication errors
- [ ] No "database does not exist" errors
- [ ] All tasks complete (or fail for other reasons, not DB connection)

### Step 8: Extract Task Test ✅
```bash
astro dev run tasks test nasa_apod_etl_pipeline extract_data
```

- [ ] Task completes successfully
- [ ] No API errors (may fail if DEMO_KEY has limits, but not DB errors)

### Step 9: Transform Task Test ✅
```bash
astro dev run tasks test nasa_apod_etl_pipeline transform_data
```

- [ ] Task completes successfully
- [ ] No XCom errors

### Step 10: Load Task Test ✅
```bash
astro dev run tasks test nasa_apod_etl_pipeline load_to_postgres
```

- [ ] Task completes successfully
- [ ] No authentication errors
- [ ] No "database does not exist" errors
- [ ] Log shows: "✅ Successfully loaded data to PostgreSQL"

### Step 11: Data Verification ✅
```bash
docker exec -it <postgres-container> psql -U postgres -d apod_db -c "SELECT COUNT(*) FROM apod_data;"
```

- [ ] Query returns a count (should be ≥ 1)
- [ ] No permission errors
- [ ] Data is actually inserted

---

## Success Criteria

You can mark the fix as **COMPLETE** when:

✅ All 11 verification steps pass
✅ No authentication errors in logs
✅ No "database does not exist" errors
✅ PostgreSQL container shows healthy status
✅ Airflow UI shows correct connection config
✅ Tasks execute without DB-related errors
✅ Data appears in apod_data table

---

## Troubleshooting If Something Fails

### Issue: "database apod_db does not exist"
**Solution**: The init script didn't run. Check:
1. Is `init_db.sql` in the root directory?
2. Is the volume mount in `docker-compose.override.yml` correct?
3. Try manual creation:
   ```bash
   docker exec -it <postgres> psql -U postgres -c "CREATE DATABASE apod_db;"
   ```

### Issue: "password authentication failed"
**Solution**: Check credentials in `airflow_settings.yaml`:
1. Verify `conn_login: postgres` (not `airflow`)
2. Verify `conn_password: postgres` (not `airflow`)
3. Restart containers: `astro dev kill && astro dev start`
4. Verify in Airflow UI: Admin > Connections > postgres_apod

### Issue: "Connection refused"
**Solution**: PostgreSQL container not ready. 
1. Wait 60+ seconds after `astro dev start`
2. Check container is running: `docker ps | grep postgres`
3. Check health: `docker exec -it <postgres> pg_isready -U postgres`

### Issue: Table structure missing columns
**Solution**: The init script created DB but not table. The table is created on first `load_to_postgres` task. Either:
1. Run the full DAG to create table
2. Or manually create:
   ```bash
   docker exec -it <postgres> psql -U postgres -d apod_db -f init_db.sql
   ```

---

## Performance Check

After everything works, verify performance:

```bash
# Check query performance
docker exec -it <postgres> psql -U postgres -d apod_db -c "
EXPLAIN ANALYZE SELECT * FROM apod_data WHERE date = CURRENT_DATE;
"
```

Expected: Uses index `idx_apod_date` for efficient lookups

---

## Documentation Check

- [ ] Read `IMPLEMENTATION_SUMMARY.md` for technical details
- [ ] Read `POSTGRES_FIX_GUIDE.md` for setup steps
- [ ] Read `QUICK_COMMANDS.md` for common commands
- [ ] Bookmark these for team reference

---

## Team Handoff

When sharing with team, provide:
1. ✅ `IMPLEMENTATION_SUMMARY.md` - Technical explanation
2. ✅ `QUICK_COMMANDS.md` - Daily reference commands
3. ✅ This checklist - Verification steps
4. ✅ All modified files in git commit

---

**Status**: ⏳ In Progress → ✅ Complete

Last verified: [Your date here]
Verified by: [Your name]

